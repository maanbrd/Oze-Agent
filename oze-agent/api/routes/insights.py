"""Insights API routes — read-only analytics for /dashboard.

Endpoints:

  GET /api/insights/activity-week  — 4-metric "Mój tydzień" card
  GET /api/insights/trend-6mo      — 6-month sparkline data (4 series)
  GET /api/insights/sources        — top lead-source bars (count + conversion)

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


# ── 6-month trend ─────────────────────────────────────────────────────────────

# Series we expose. Keep keys camelCase to match the web client.
TREND_SERIES_KEYS = ("newClients", "meetingsDone", "offersSent", "signed")


def _ym(year: int, month: int) -> str:
    return f"{year:04d}-{month:02d}"


def _last_six_month_keys(today: date) -> list[str]:
    """Return the last 6 calendar-month keys including the current month, oldest first."""
    keys: list[str] = []
    year, month = today.year, today.month
    for _ in range(6):
        keys.append(_ym(year, month))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return list(reversed(keys))


def _months_window(month_keys: list[str]) -> tuple[date, date]:
    """Return (firstDayOfFirstMonth, lastDayOfLastMonth) covering the given month keys."""
    first_y, first_m = (int(p) for p in month_keys[0].split("-"))
    last_y, last_m = (int(p) for p in month_keys[-1].split("-"))
    start = date(first_y, first_m, 1)
    if last_m == 12:
        end = date(last_y + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(last_y, last_m + 1, 1) - timedelta(days=1)
    return start, end


def _empty_trend_payload(today: date) -> dict[str, Any]:
    months = _last_six_month_keys(today)
    return {
        "fetchedAt": datetime.now(tz=timezone.utc).isoformat(),
        "today": today.isoformat(),
        "months": months,
        "series": {key: [0] * len(months) for key in TREND_SERIES_KEYS},
        "source": "unavailable",
    }


@router.get("/insights/trend-6mo")
async def get_trend_6mo(
    auth_user: AuthUser = Depends(get_current_auth_user),
) -> dict[str, Any]:
    """Return 4 monthly series over the last 6 calendar months.

    Series:
      newClients    — Sheets rows whose 'Data pierwszego kontaktu' falls
                      in that month.
      meetingsDone  — Calendar past events grouped by month (no
                      event_type filter; any past event = "spotkanie odbyte").
      offersSent    — Calendar past events with event_type=offer_email.
      signed        — Sheets rows with status="Podpisane" whose 'Data
                      ostatniego kontaktu' falls in that month (heuristic
                      proxy for the missing signing-date column).

    Months array is oldest-first, so series[i] aligns with months[i].
    """
    record = _resolve_user_record(auth_user)
    today = _today_warsaw()

    if not record or not record.get("google_sheets_id"):
        return _empty_trend_payload(today)

    user_id = record["id"]
    months = _last_six_month_keys(today)
    window_start, window_end = _months_window(months)

    range_start = datetime.combine(window_start, time.min, tzinfo=WARSAW_TZ)
    # Cap the calendar fetch at "end of today" — months past today haven't
    # happened yet, so future events would dilute "meetingsDone" totals.
    range_end_cap = min(window_end, today)
    range_end = datetime.combine(range_end_cap, time.max, tzinfo=WARSAW_TZ)

    rows, events = await asyncio.gather(
        get_all_clients(user_id),
        get_events_for_range(user_id, range_start, range_end),
    )

    series: dict[str, list[int]] = {key: [0] * len(months) for key in TREND_SERIES_KEYS}
    month_index = {ym: i for i, ym in enumerate(months)}
    now_warsaw = _now_warsaw()

    for row in rows:
        first = _parse_iso_date(row.get("Data pierwszego kontaktu"))
        if first is not None:
            key = _ym(first.year, first.month)
            idx = month_index.get(key)
            if idx is not None:
                series["newClients"][idx] += 1

        status_value = (row.get("Status") or "").strip()
        if status_value == "Podpisane":
            last = _parse_iso_date(row.get("Data ostatniego kontaktu"))
            if last is not None:
                key = _ym(last.year, last.month)
                idx = month_index.get(key)
                if idx is not None:
                    series["signed"][idx] += 1

    for ev in events:
        ev_dt = _parse_event_start_warsaw(ev.get("start"))
        if ev_dt is None:
            continue
        if ev_dt > now_warsaw:
            continue
        key = _ym(ev_dt.year, ev_dt.month)
        idx = month_index.get(key)
        if idx is None:
            continue
        series["meetingsDone"][idx] += 1
        if (ev.get("event_type") or "") == "offer_email":
            series["offersSent"][idx] += 1

    return {
        "fetchedAt": datetime.now(tz=timezone.utc).isoformat(),
        "today": today.isoformat(),
        "months": months,
        "series": series,
        "source": "live",
    }


# ── Top lead sources ──────────────────────────────────────────────────────────

# Cap returned rows so a noisy free-text Źródło column doesn't render 50 bars.
SOURCES_TOP_N = 3


def _normalize_source(value: str) -> str:
    """Trim whitespace; preserve case (handlowiec sees their own typing)."""
    return (value or "").strip()


def _empty_sources_payload(today: date) -> dict[str, Any]:
    return {
        "fetchedAt": datetime.now(tz=timezone.utc).isoformat(),
        "today": today.isoformat(),
        "totalClients": 0,
        "totalSigned": 0,
        "rows": [],
        "source": "unavailable",
    }


@router.get("/insights/sources")
async def get_lead_sources(
    auth_user: AuthUser = Depends(get_current_auth_user),
) -> dict[str, Any]:
    """Top lead-source bars: count + conversion rate to "Podpisane".

    Reads column M ("Źródło pozyskania") raw — no dictionary validation
    (free-text in Sheets stays free-text in UI). Empty/blank sources are
    skipped from the bars but counted in totalClients so the overall
    rate matches what the salesperson sees on the funnel.

    Each row:
        {
          source: str,          # e.g. "Polecenie"
          totalCount: int,      # clients with this source
          signedCount: int,     # subset whose status == "Podpisane"
          conversionRate: float # signedCount / totalCount, rounded to 4dp
        }

    Sorted by totalCount desc, capped at SOURCES_TOP_N.
    """
    record = _resolve_user_record(auth_user)
    today = _today_warsaw()

    if not record or not record.get("google_sheets_id"):
        return _empty_sources_payload(today)

    user_id = record["id"]
    rows = await get_all_clients(user_id)

    by_source_total: dict[str, int] = {}
    by_source_signed: dict[str, int] = {}
    total_clients = 0
    total_signed = 0

    for row in rows:
        total_clients += 1
        is_signed = (row.get("Status") or "").strip() == "Podpisane"
        if is_signed:
            total_signed += 1

        source = _normalize_source(row.get("Źródło pozyskania") or "")
        if not source:
            continue

        by_source_total[source] = by_source_total.get(source, 0) + 1
        if is_signed:
            by_source_signed[source] = by_source_signed.get(source, 0) + 1

    sorted_sources = sorted(
        by_source_total.items(),
        key=lambda pair: (-pair[1], pair[0]),
    )[:SOURCES_TOP_N]

    result_rows = []
    for source, total in sorted_sources:
        signed = by_source_signed.get(source, 0)
        rate = round(signed / total, 4) if total > 0 else 0.0
        result_rows.append(
            {
                "source": source,
                "totalCount": total,
                "signedCount": signed,
                "conversionRate": rate,
            }
        )

    return {
        "fetchedAt": datetime.now(tz=timezone.utc).isoformat(),
        "today": today.isoformat(),
        "totalClients": total_clients,
        "totalSigned": total_signed,
        "rows": result_rows,
        "source": "live",
    }
