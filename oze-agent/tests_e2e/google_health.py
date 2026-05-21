"""Read-only Google health checks for live E2E smoke runs."""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from shared.database import get_user_by_id
from shared.google_auth import get_google_credentials
from shared.google_calendar import _get_calendar_service_sync, _to_rfc3339
from shared.google_drive import _get_drive_service_sync
from shared.google_sheets import _get_sheets_service_sync
from tests_e2e.config import E2EConfig
from tests_e2e.sheets_verify import resolve_user_id


@dataclass(frozen=True)
class GoogleHealthCheck:
    name: str
    tag: str
    detail: str


@dataclass(frozen=True)
class GoogleHealthReport:
    telegram_id: int
    user_id: str | None
    checks: list[GoogleHealthCheck]

    @property
    def ok(self) -> bool:
        return all(check.tag == "pass" for check in self.checks)

    def to_markdown(self) -> str:
        status = "PASS" if self.ok else "BLOCKER"
        lines = [
            "# Google Health Check",
            "",
            f"**Overall:** {status}",
            f"**Telegram ID:** `{self.telegram_id}`",
            f"**User ID:** `{self.user_id or ''}`",
            "",
            "| Check | Tag | Detail |",
            "|---|---:|---|",
        ]
        for check in self.checks:
            lines.append(f"| `{check.name}` | `{check.tag}` | {check.detail} |")
        return "\n".join(lines)


def _check(name: str, tag: str, detail: str) -> GoogleHealthCheck:
    clean_detail = " ".join(str(detail or "").split())
    return GoogleHealthCheck(name=name, tag=tag, detail=clean_detail[:500])


def _read_sheets_headers(user_id: str, spreadsheet_id: str) -> str:
    service = _get_sheets_service_sync(user_id)
    if service is None:
        raise RuntimeError("sheets_no_service")
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range="A1:1",
    ).execute()
    headers = result.get("values", [[]])[0]
    if not headers:
        raise RuntimeError("sheets_empty_header_row")
    return f"{len(headers)} headers"


def _read_calendar(user_id: str, calendar_id: str) -> str:
    service = _get_calendar_service_sync(user_id)
    if service is None:
        raise RuntimeError("calendar_no_service")
    now = datetime.now(tz=timezone.utc)
    result = service.events().list(
        calendarId=calendar_id,
        timeMin=_to_rfc3339(now),
        timeMax=_to_rfc3339(now + timedelta(days=7)),
        maxResults=1,
        singleEvents=True,
        orderBy="startTime",
    ).execute()
    return f"{len(result.get('items', []))} upcoming events sampled"


def _read_drive_folder(user_id: str, folder_id: str) -> str:
    service = _get_drive_service_sync(user_id)
    if service is None:
        raise RuntimeError("drive_no_service")
    result = service.files().get(
        fileId=folder_id,
        fields="id,name,mimeType,trashed",
        supportsAllDrives=True,
    ).execute()
    if result.get("trashed"):
        raise RuntimeError("drive_folder_trashed")
    return f"folder {result.get('id')} {result.get('name')!r}"


def _safe_read(name: str, fn, *args) -> GoogleHealthCheck:
    try:
        detail = fn(*args)
    except Exception as exc:
        text = str(exc)
        tag = "blocker"
        if "invalid_scope" in text:
            text = f"invalid_scope; reauthorization required: {text}"
        return _check(name, tag, text)
    return _check(name, "pass", detail)


async def check_google_health(telegram_id: int) -> GoogleHealthReport:
    checks: list[GoogleHealthCheck] = []
    user_id = await resolve_user_id(telegram_id)
    if not user_id:
        return GoogleHealthReport(
            telegram_id=telegram_id,
            user_id=None,
            checks=[_check("resolve_user_id", "blocker", f"no Supabase user for telegram_id={telegram_id}")],
        )
    checks.append(_check("resolve_user_id", "pass", user_id))

    user = get_user_by_id(user_id) or {}
    creds = get_google_credentials(user_id)
    if creds is None:
        checks.append(_check("google_credentials_refresh", "blocker", "credentials unavailable; reauthorization required"))
        return GoogleHealthReport(telegram_id=telegram_id, user_id=user_id, checks=checks)
    checks.append(_check("google_credentials_refresh", "pass", "credentials available"))

    spreadsheet_id = str(user.get("google_sheets_id") or "").strip()
    calendar_id = str(user.get("google_calendar_id") or "").strip()
    folder_id = str(user.get("google_drive_folder_id") or "").strip()

    if spreadsheet_id:
        checks.append(await asyncio.to_thread(_safe_read, "sheets_header_read", _read_sheets_headers, user_id, spreadsheet_id))
    else:
        checks.append(_check("sheets_header_read", "blocker", "missing users.google_sheets_id"))

    if calendar_id:
        checks.append(await asyncio.to_thread(_safe_read, "calendar_read", _read_calendar, user_id, calendar_id))
    else:
        checks.append(_check("calendar_read", "blocker", "missing users.google_calendar_id"))

    if folder_id:
        checks.append(await asyncio.to_thread(_safe_read, "drive_folder_read", _read_drive_folder, user_id, folder_id))
    else:
        checks.append(_check("drive_folder_read", "blocker", "missing users.google_drive_folder_id"))

    return GoogleHealthReport(telegram_id=telegram_id, user_id=user_id, checks=checks)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m tests_e2e.google_health")
    parser.add_argument("--telegram-id", type=int)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    telegram_id = args.telegram_id
    if telegram_id is None:
        telegram_id = E2EConfig.from_env().admin_telegram_id
    report = asyncio.run(check_google_health(telegram_id))
    print(report.to_markdown())
    return 0 if report.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
