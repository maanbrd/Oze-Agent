"""Read-only Google health check for the E2E test user."""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from shared.database import get_user_by_id
from shared.google_auth import get_google_credentials
from shared.google_calendar import _get_calendar_service_sync, _to_rfc3339
from shared.google_drive import _get_drive_service_sync
from shared.google_sheets import _get_sheets_service_sync

from tests_e2e.config import E2EConfig
from tests_e2e.sheets_verify import resolve_user_id


@dataclass(frozen=True)
class HealthCheck:
    name: str
    tag: str
    detail: str

    @property
    def ok(self) -> bool:
        return self.tag == "pass"


@dataclass
class HealthResult:
    checks: list[HealthCheck] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return bool(self.checks) and all(check.ok for check in self.checks)

    def add_pass(self, name: str, detail: str) -> None:
        self.checks.append(HealthCheck(name=name, tag="pass", detail=detail))

    def add_blocker(self, name: str, detail: str) -> None:
        self.checks.append(HealthCheck(name=name, tag="blocker", detail=detail))


async def _to_thread(fn):
    return await asyncio.to_thread(fn)


async def _check_sheets(result: HealthResult, user: dict, user_id: str) -> None:
    spreadsheet_id = user.get("google_sheets_id")
    if not spreadsheet_id:
        result.add_blocker("sheets_read", "user missing google_sheets_id")
        return

    def _read_headers():
        service = _get_sheets_service_sync(user_id)
        if not service:
            raise RuntimeError("sheets_no_credentials")
        response = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range="A1:ZZ1",
        ).execute()
        return response.get("values", [[]])[0]

    try:
        headers = await _to_thread(_read_headers)
    except Exception as exc:
        result.add_blocker("sheets_read", f"{type(exc).__name__}: {exc}")
        return
    result.add_pass("sheets_read", f"headers={len(headers)} spreadsheet_id={spreadsheet_id}")


async def _check_calendar(result: HealthResult, user: dict, user_id: str) -> None:
    calendar_id = user.get("google_calendar_id")
    if not calendar_id:
        result.add_blocker("calendar_read", "user missing google_calendar_id")
        return

    now = datetime.now(tz=timezone.utc)
    end = now + timedelta(days=1)

    def _read_events():
        service = _get_calendar_service_sync(user_id)
        if not service:
            raise RuntimeError("calendar_no_credentials")
        response = service.events().list(
            calendarId=calendar_id,
            timeMin=_to_rfc3339(now),
            timeMax=_to_rfc3339(end),
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        return response.get("items", [])

    try:
        events = await _to_thread(_read_events)
    except Exception as exc:
        result.add_blocker("calendar_read", f"{type(exc).__name__}: {exc}")
        return
    result.add_pass("calendar_read", f"events_next_24h={len(events)} calendar_id={calendar_id}")


async def _check_drive(result: HealthResult, user_id: str) -> None:
    def _read_about():
        service = _get_drive_service_sync(user_id)
        if not service:
            raise RuntimeError("drive_no_credentials")
        return service.about().get(fields="user").execute()

    try:
        about = await _to_thread(_read_about)
    except Exception as exc:
        result.add_blocker("drive_read", f"{type(exc).__name__}: {exc}")
        return
    email = about.get("user", {}).get("emailAddress", "")
    result.add_pass("drive_read", f"drive user visible={bool(email)}")


async def run_google_health(telegram_id: int) -> HealthResult:
    """Run read-only Supabase + Google checks for the E2E test user."""
    result = HealthResult()
    user_id = await resolve_user_id(telegram_id)
    if not user_id:
        result.add_blocker(
            "supabase_user",
            f"no Supabase user found for telegram_id={telegram_id}",
        )
        return result
    result.add_pass("supabase_user", f"user_id={user_id}")

    user = get_user_by_id(user_id) or {}
    credentials = get_google_credentials(user_id)
    if not credentials:
        result.add_blocker("google_credentials", "Google OAuth credentials unavailable")
        return result
    result.add_pass("google_credentials", "Google OAuth credentials available")

    await _check_sheets(result, user, user_id)
    await _check_calendar(result, user, user_id)
    await _check_drive(result, user_id)
    return result


def render_markdown(result: HealthResult) -> str:
    status = "PASS" if result.ok else "BLOCKER"
    lines = ["# OZE-Agent Google Health", "", f"**Overall:** {status}", ""]
    lines.append("| Check | Tag | Detail |")
    lines.append("|---|---|---|")
    for check in result.checks:
        detail = check.detail.replace("|", "\\|")
        lines.append(f"| `{check.name}` | `{check.tag}` | {detail} |")
    lines.append("")
    return "\n".join(lines)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m tests_e2e.google_health",
        description="Run read-only Google health checks for the E2E user.",
    )
    parser.add_argument("--report", help="Optional markdown report path.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        config = E2EConfig.from_env()
    except RuntimeError as exc:
        print(f"MISCONFIG: {exc}")
        return 2
    result = asyncio.run(run_google_health(config.admin_telegram_id))
    rendered = render_markdown(result)
    if args.report:
        path = Path(args.report)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8")
        print(f"Google health report written to {path}")
    else:
        print(rendered)
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
