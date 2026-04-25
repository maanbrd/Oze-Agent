"""Read-only Google Calendar verification helpers for E2E scenarios.

Wraps `shared.google_calendar` so scenarios can verify a `create_event`
side-effect actually landed in the calendar with the right type and
time. NEVER creates events via these helpers (the bot does that under
test). The delete helper is strictly for cleanup of E2E-Beta-* synthetic
events.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from shared.google_calendar import (
    delete_event,
    get_events_for_range,
)

logger = logging.getLogger(__name__)


_SYNTHETIC_PREFIX = "E2E-Beta-"
_FIXTURE_PREFIX = "E2E-Beta-Fixture-"

VALID_EVENT_TYPES = ("in_person", "phone_call", "offer_email", "doc_followup")


# ── Read by summary / window ────────────────────────────────────────────────


async def find_event_by_summary_in_window(
    user_id: str,
    summary_substring: str,
    start: datetime,
    end: datetime,
) -> Optional[dict]:
    """Return the first event in [start, end) whose title contains the substring."""
    events = await get_events_for_range(user_id, start, end)
    for e in events:
        if summary_substring in e.get("title", ""):
            return e
    return None


async def find_events_in_window(
    user_id: str, start: datetime, end: datetime,
) -> list[dict]:
    """Pass-through to `get_events_for_range` — kept here for symmetry."""
    return await get_events_for_range(user_id, start, end)


# ── Field assertions on event dict ──────────────────────────────────────────


def assert_event_type(event: dict, expected: str) -> tuple[bool, str]:
    """Verify event's `event_type` (from extendedProperties) matches expected."""
    if expected not in VALID_EVENT_TYPES:
        return False, f"invalid expected event_type {expected!r}; valid: {VALID_EVENT_TYPES}"
    actual = event.get("event_type", "")
    if actual == expected:
        return True, f"event_type={actual!r} matches"
    return False, f"event_type={actual!r}, expected {expected!r}"


def assert_event_at_time(
    event: dict, expected_dt: datetime, *, tolerance_min: int = 5,
) -> tuple[bool, str]:
    """Verify event start matches expected datetime within `tolerance_min` minutes."""
    start_str = event.get("start", "")
    try:
        actual = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return False, f"could not parse event start={start_str!r}"

    if actual.tzinfo is None:
        # Date-only events shouldn't be the case for our writes, but guard.
        return False, f"event start={start_str!r} has no timezone"
    if expected_dt.tzinfo is None:
        return False, "expected_dt missing timezone — pass a tz-aware datetime"

    diff_min = abs((actual - expected_dt).total_seconds()) / 60
    if diff_min <= tolerance_min:
        return True, (
            f"event start={start_str!r} matches expected "
            f"{expected_dt.isoformat()!r} (diff {diff_min:.1f} min)"
        )
    return False, (
        f"event start={start_str!r} differs by {diff_min:.1f} min from expected "
        f"{expected_dt.isoformat()!r} (tolerance {tolerance_min} min)"
    )


def assert_event_duration(
    event: dict, expected_minutes: int, *, tolerance_min: int = 1,
) -> tuple[bool, str]:
    """Verify event end-start duration matches expected_minutes within tolerance."""
    start_str = event.get("start", "")
    end_str = event.get("end", "")
    try:
        start = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
        end = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return False, f"could not parse start/end {start_str!r}/{end_str!r}"
    actual_min = (end - start).total_seconds() / 60
    if abs(actual_min - expected_minutes) <= tolerance_min:
        return True, f"duration={actual_min:.0f}min matches"
    return False, (
        f"duration={actual_min:.1f}min, expected {expected_minutes}min "
        f"(±{tolerance_min}min tolerance)"
    )


# ── Synthetic data discovery + cleanup ──────────────────────────────────────


async def find_synthetic_events(
    user_id: str,
    *,
    days_forward: int = 60,
    run_id: Optional[str] = None,
    include_fixtures: bool = False,
) -> list[dict]:
    """Return all events in the next `days_forward` days whose title starts
    with `E2E-Beta-`. Filters by `run_id` substring; excludes fixtures by
    default."""
    now = datetime.now(tz=timezone.utc)
    end = now + timedelta(days=days_forward)
    events = await get_events_for_range(user_id, now, end)
    out: list[dict] = []
    for e in events:
        title = e.get("title", "")
        if not title.startswith(_SYNTHETIC_PREFIX):
            continue
        if not include_fixtures and title.startswith(_FIXTURE_PREFIX):
            continue
        if run_id is not None and run_id not in title:
            continue
        out.append(e)
    return out


async def delete_synthetic_events(user_id: str, events: list[dict]) -> int:
    """Hard-delete the given events. Returns count of successful deletes."""
    n = 0
    for e in events:
        eid = e.get("id")
        if not eid:
            continue
        if await delete_event(user_id, eid):
            n += 1
        else:
            logger.warning("delete_synthetic_events: failed eid=%s", eid)
    return n
