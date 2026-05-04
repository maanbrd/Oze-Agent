"""Read-only Google Sheets verification helpers for E2E scenarios.

Wraps the existing `shared.google_sheets` API in test-friendly helpers
that scenarios can call after a write to verify the row actually landed.
NEVER writes via these helpers — only reads. The single delete helper
(`delete_synthetic_rows`) is for cleanup of E2E-Beta-* test data and is
strictly opt-in via the `e2e_cleanup_run` MCP tool.

User-id resolution: scenarios know the test user's Telegram ID
(via `harness.authenticated_user_id`); these helpers translate it to
the Supabase user UUID needed by the wrapper API.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional

from shared.database import get_user_by_telegram_id
from shared.google_sheets import delete_client, get_all_clients

logger = logging.getLogger(__name__)


# ── User-id resolution ──────────────────────────────────────────────────────


def _supabase_user_id_override() -> Optional[str]:
    """Return an explicit Supabase user UUID for local/MCP verifier runs."""
    for name in (
        "TELEGRAM_E2E_SUPABASE_USER_ID",
        "TELEGRAM_E2E_USER_ID",
        "OZE_E2E_USER_ID",
    ):
        value = os.getenv(name, "").strip()
        if value:
            return value
    return None


async def resolve_user_id(telegram_id: int) -> Optional[str]:
    """Resolve Supabase user UUID from a Telegram numeric id. None if no match."""
    override = _supabase_user_id_override()
    if override:
        return override

    user = await asyncio.to_thread(get_user_by_telegram_id, telegram_id)
    if not user:
        logger.warning(
            "resolve_user_id: no user for telegram_id=%s; set "
            "TELEGRAM_E2E_SUPABASE_USER_ID for local verifier runs",
            telegram_id,
        )
        return None
    return user.get("id")


# ── Client row read ─────────────────────────────────────────────────────────


async def find_client_row(
    user_id: str, name: str, city: Optional[str] = None,
) -> Optional[dict]:
    """Return the first row whose `Imię i nazwisko` matches `name` exactly.

    If `city` is given, also requires `Miasto` to match. Comparison is
    case-insensitive. Returns the row dict (with `_row` key) or None.
    """
    clients = await get_all_clients(user_id)
    name_lo = name.lower()
    city_lo = city.lower() if city else None
    for c in clients:
        if c.get("Imię i nazwisko", "").lower() != name_lo:
            continue
        if city_lo is not None and c.get("Miasto", "").lower() != city_lo:
            continue
        return c
    return None


def assert_row_field(
    row: dict, field: str, expected_substring: str,
) -> tuple[bool, str]:
    """Verify a row's `field` value contains `expected_substring` (case-insensitive)."""
    actual = row.get(field, "")
    if expected_substring.lower() in actual.lower():
        return True, f"row[{field!r}]={actual!r} contains {expected_substring!r}"
    return False, (
        f"row[{field!r}]={actual!r} does NOT contain {expected_substring!r}"
    )


def assert_row_field_equals(row: dict, field: str, expected: str) -> tuple[bool, str]:
    """Verify a row's `field` equals `expected` exactly (case-insensitive trimmed)."""
    actual = row.get(field, "")
    if actual.strip().lower() == expected.strip().lower():
        return True, f"row[{field!r}]={actual!r} matches"
    return False, f"row[{field!r}]={actual!r}, expected {expected!r}"


# ── Synthetic data discovery + cleanup ──────────────────────────────────────


_SYNTHETIC_PREFIX = "E2E-Beta-"
_FIXTURE_PREFIX = "E2E-Beta-Fixture-"


async def find_synthetic_rows(
    user_id: str,
    *,
    run_id: Optional[str] = None,
    include_fixtures: bool = False,
) -> list[dict]:
    """Return all rows whose `Imię i nazwisko` starts with `E2E-Beta-`.

    `run_id` filters by substring in name (run_id is embedded in synthetic
    names like `E2E-Beta-Tester-{run_id}-B01`). `include_fixtures=False`
    excludes rows starting with `E2E-Beta-Fixture-`.
    """
    clients = await get_all_clients(user_id)
    out: list[dict] = []
    for c in clients:
        name = c.get("Imię i nazwisko", "")
        if not name.startswith(_SYNTHETIC_PREFIX):
            continue
        if not include_fixtures and name.startswith(_FIXTURE_PREFIX):
            continue
        if run_id is not None and run_id not in name:
            continue
        out.append(c)
    return out


async def delete_synthetic_rows(user_id: str, rows: list[dict]) -> int:
    """Hard-delete the given rows. Returns count of successful deletes.

    Sorts by `_row` descending so deleting earlier rows doesn't shift
    later row indices (Sheets row numbers are absolute and shift on
    delete-from-middle).
    """
    rows_sorted = sorted(rows, key=lambda r: r.get("_row", 0), reverse=True)
    n = 0
    for row in rows_sorted:
        rn = row.get("_row")
        if rn is None:
            continue
        if await delete_client(user_id, rn):
            n += 1
        else:
            logger.warning("delete_synthetic_rows: failed to delete row %s", rn)
    return n
