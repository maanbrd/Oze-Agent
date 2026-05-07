"""Insights API routes — read-only analytics for /dashboard.

Endpoints:

  GET /api/insights/activity-week  — 4-metric "Mój tydzień" card

This module is intentionally separate from api/routes/dashboard.py so it
can be developed without touching the file other agents (Codex/Maan) are
modifying. It owns its own Calendar fetch window and its own Sheets row
mapper, both tuned to the analytics use case rather than the live
dashboard one.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends
from zoneinfo import ZoneInfo

from api.auth import AuthUser, get_current_auth_user
from shared.database import get_supabase_client
from shared.google_calendar import get_events_for_range
from shared.google_sheets import get_all_clients

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Constants ─────────────────────────────────────────────────────────────────

WARSAW_TZ = ZoneInfo("Europe/Warsaw")

# How far back the streak loop is allowed to look. Past this, a salesperson
# either had a real long streak or we hit a Calendar fetch boundary — either
# way 30 days is a reasonable cap so the loop is bounded.
STREAK_MAX_DAYS = 30


# ── Helpers ───────────────────────────────────────────────────────────────────


def _now_warsaw() -> datetime:
    return datetime.now(tz=WARSAW_TZ)


def _today_warsaw() -> date:
    return _now_warsaw().date()


def _resolve_user_record(auth_user: AuthUser) -> dict[str, Any]:
    """Fetch the internal users-table row (returns {} on 'not onboarded yet')."""
    result = (
        get_supabase_client()
        .table("users")
        .select("id, auth_user_id, google_sheets_id, google_calendar_id")
        .eq("auth_user_id", auth_user.user_id)
        .limit(1)
        .execute()
    )
    if not result.data:
        return {}
    return result.data[0]


def _parse_iso_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _parse_event_start_warsaw(value: Optional[str]) -> Optional[datetime]:
    """Calendar 'start' may be RFC3339 datetime or all-day 'YYYY-MM-DD'.

    Always returns a Warsaw-aware datetime so date math is timezone-safe.
    """
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=WARSAW_TZ)
        return dt.astimezone(WARSAW_TZ)
    except ValueError:
        pass
    parsed = _parse_iso_date(value)
    if parsed is None:
        return None
    return datetime(parsed.year, parsed.month, parsed.day, 0, 0, tzinfo=WARSAW_TZ)


def _empty_activity_week_payload(today: date) -> dict[str, Any]:
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return {
        "fetchedAt": datetime.now(tz=timezone.utc).isoformat(),
        "today": today.isoformat(),
        "weekStart": monday.isoformat(),
        "weekEnd": sunday.isoformat(),
        "newClients": 0,
        "meetingsDone": 0,
        "offersSent": 0,
        "streak": 0,
        "source": "unavailable",
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get("/insights/activity-week")
async def get_activity_week(
    auth_user: AuthUser = Depends(get_current_auth_user),
) -> dict[str, Any]:
    """Return 4 personal-activity counters for the current Warsaw week.

    Fields:
      newClients    — Sheets rows whose 'Data pierwszego kontaktu' (col I)
                      falls within Mon..Sun of the current Warsaw week.
      meetingsDone  — Calendar past events (start <= now) within the same
                      week range. No event_type filter — the salesperson
                      decides what counts as a meeting in their Calendar.
      offersSent    — Calendar past events with event_type="offer_email"
                      within the same week range. (Subset of meetingsDone.)
      streak        — Consecutive days with at least one movement, looking
                      back from today (or yesterday if today has nothing
                      yet — grace period so a 9am check doesn't reset the
                      counter). Movement = a row's 'Data ostatniego
                      kontaktu' on that day OR a Calendar event on that
                      day. Capped at STREAK_MAX_DAYS.
    """
    record = _resolve_user_record(auth_user)
    today = _today_warsaw()

    if not record or not record.get("google_sheets_id"):
        return _empty_activity_week_payload(today)

    user_id = record["id"]
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    now_warsaw = _now_warsaw()

    range_start = datetime.combine(
        today - timedelta(days=STREAK_MAX_DAYS), time.min, tzinfo=WARSAW_TZ
    )
    range_end = datetime.combine(today, time.max, tzinfo=WARSAW_TZ)

    rows, events = await asyncio.gather(
        get_all_clients(user_id),
        get_events_for_range(user_id, range_start, range_end),
    )

    new_clients = 0
    contact_days: set[date] = set()
    for row in rows:
        first = _parse_iso_date(row.get("Data pierwszego kontaktu"))
        if first is not None and monday <= first <= sunday:
            new_clients += 1
        last = _parse_iso_date(row.get("Data ostatniego kontaktu"))
        if last is not None:
            contact_days.add(last)

    meetings_done = 0
    offers_sent = 0
    event_days: set[date] = set()
    for ev in events:
        ev_dt = _parse_event_start_warsaw(ev.get("start"))
        if ev_dt is None:
            continue
        if ev_dt > now_warsaw:
            continue
        ev_day = ev_dt.date()
        event_days.add(ev_day)
        if monday <= ev_day <= today:
            meetings_done += 1
            if (ev.get("event_type") or "") == "offer_email":
                offers_sent += 1

    streak = _compute_streak(today, contact_days, event_days)

    return {
        "fetchedAt": datetime.now(tz=timezone.utc).isoformat(),
        "today": today.isoformat(),
        "weekStart": monday.isoformat(),
        "weekEnd": sunday.isoformat(),
        "newClients": new_clients,
        "meetingsDone": meetings_done,
        "offersSent": offers_sent,
        "streak": streak,
        "source": "live",
    }


def _compute_streak(
    today: date,
    contact_days: set[date],
    event_days: set[date],
) -> int:
    """Consecutive-days counter ending today (or yesterday, with grace).

    A day "has movement" if it appears in either set. We look back from
    today; if today has no movement, we let the count start from yesterday
    so a salesperson checking the dashboard at 9am doesn't see streak=0
    until they touch something. Capped at STREAK_MAX_DAYS so the loop is
    bounded.
    """

    def has_movement(day: date) -> bool:
        return day in contact_days or day in event_days

    streak = 0
    start_offset = 0 if has_movement(today) else 1

    for i in range(start_offset, STREAK_MAX_DAYS + 1):
        day = today - timedelta(days=i)
        if has_movement(day):
            streak += 1
        else:
            break
    return streak
