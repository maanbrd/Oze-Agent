"""Read-only Supabase schema verifier for post-MVP app smoke tests."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import Iterable

from shared.database import get_supabase_client

from tests_e2e.config import E2EConfig
from tests_e2e.report import CheckResult

logger = logging.getLogger(__name__)

REQUIRED_TABLES = (
    "photo_upload_sessions",
    "offer_templates",
    "offer_seller_profiles",
    "offer_send_attempts",
)
REQUIRED_BUCKETS = ("offer-logos",)
REQUIRED_USER_GOOGLE_FIELDS = (
    "google_sheets_id",
    "google_calendar_id",
    "google_drive_folder_id",
)


def _error_detail(exc: Exception) -> str:
    payload = getattr(exc, "_raw_error", None)
    if isinstance(payload, dict):
        return repr(payload)
    return repr(exc)


def _is_pgrst205(exc: Exception) -> bool:
    payload = getattr(exc, "_raw_error", None)
    if isinstance(payload, dict) and payload.get("code") == "PGRST205":
        return True
    if getattr(exc, "code", None) == "PGRST205":
        return True
    return "PGRST205" in repr(exc)


def check_table_visible(client, table_name: str) -> CheckResult:
    try:
        client.table(table_name).select("*").limit(1).execute()
    except Exception as exc:
        detail = _error_detail(exc)
        if _is_pgrst205(exc):
            detail = f"PGRST205 schema-cache miss: {detail}"
        return CheckResult(
            name=f"table_{table_name}_visible",
            passed=False,
            detail=detail,
            tag="blocker",
        )
    return CheckResult(name=f"table_{table_name}_visible", passed=True)


def _bucket_name(bucket) -> str:
    if isinstance(bucket, dict):
        return str(bucket.get("name") or bucket.get("id") or "")
    return str(getattr(bucket, "name", "") or getattr(bucket, "id", ""))


def check_bucket_present(client, bucket_name: str) -> CheckResult:
    try:
        buckets = client.storage.list_buckets()
    except Exception as exc:
        return CheckResult(
            name=f"bucket_{bucket_name}_present",
            passed=False,
            detail=_error_detail(exc),
            tag="blocker",
        )
    names = {_bucket_name(bucket) for bucket in buckets}
    return CheckResult(
        name=f"bucket_{bucket_name}_present",
        passed=bucket_name in names,
        detail=f"buckets={sorted(names)}",
        tag="blocker" if bucket_name not in names else "pass",
    )


def _fetch_user_row(client, telegram_id: int) -> dict | None:
    result = (
        client.table("users")
        .select(", ".join(REQUIRED_USER_GOOGLE_FIELDS))
        .eq("telegram_id", telegram_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def check_user_google_resources(client, telegram_id: int) -> list[CheckResult]:
    try:
        row = _fetch_user_row(client, telegram_id)
    except Exception as exc:
        return [
            CheckResult(
                name="user_google_resources_readable",
                passed=False,
                detail=_error_detail(exc),
                tag="blocker",
            )
        ]
    if not row:
        return [
            CheckResult(
                name="user_google_resources_readable",
                passed=False,
                detail=f"telegram_id={telegram_id} not found",
                tag="blocker",
            )
        ]
    return [
        CheckResult(
            name=f"user_{field}_present",
            passed=bool(row.get(field)),
            detail=str(row.get(field) or ""),
            tag="blocker" if not row.get(field) else "pass",
        )
        for field in REQUIRED_USER_GOOGLE_FIELDS
    ]


def run_checks(client, telegram_id: int) -> list[CheckResult]:
    checks: list[CheckResult] = []
    checks.extend(check_table_visible(client, table) for table in REQUIRED_TABLES)
    checks.extend(check_bucket_present(client, bucket) for bucket in REQUIRED_BUCKETS)
    checks.extend(check_user_google_resources(client, telegram_id))
    return checks


def render_checks(checks: Iterable[CheckResult]) -> str:
    lines = ["Supabase post-MVP app schema check"]
    for check in checks:
        marker = "PASS" if check.tag == "pass" else check.tag.upper()
        suffix = f" — {check.detail}" if check.detail else ""
        lines.append(f"- {marker}: {check.name}{suffix}")
    return "\n".join(lines)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m tests_e2e.supabase_app_schema_check"
    )
    parser.add_argument("--telegram-id", type=int, default=None)
    parser.add_argument("--verbose", "-v", action="store_true")
    return parser.parse_args(argv)


def _env_int(name: str) -> int | None:
    value = os.getenv(name, "").strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer, got {value!r}") from exc


def resolve_telegram_id(args: argparse.Namespace) -> int:
    if args.telegram_id is not None:
        return args.telegram_id
    return (
        _env_int("TELEGRAM_E2E_ADMIN_ID")
        or _env_int("ADMIN_TELEGRAM_ID")
        or E2EConfig.from_env().admin_telegram_id
    )


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    telegram_id = resolve_telegram_id(args)
    checks = run_checks(get_supabase_client(), telegram_id)
    print(render_checks(checks))
    return 0 if all(check.tag == "pass" for check in checks) else 2


if __name__ == "__main__":
    raise SystemExit(main())
