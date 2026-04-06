"""Google Calendar operations for OZE-Agent.

All public functions are async and use asyncio.to_thread() for sync Google API calls.
Returns None / False / empty list on failure — never raises.
"""

import asyncio
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from googleapiclient.discovery import build

from shared.database import get_user_by_id
from shared.google_auth import get_google_credentials

logger = logging.getLogger(__name__)

WORKING_HOURS_START = 9   # 09:00
WORKING_HOURS_END = 18    # 18:00


# ── Internal helpers ──────────────────────────────────────────────────────────


def _get_calendar_service_sync(user_id: str):
    """Build and return a Google Calendar API service (sync)."""
    creds = get_google_credentials(user_id)
    if not creds:
        return None
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def _to_rfc3339(dt: datetime) -> str:
    """Convert datetime to RFC3339 string required by Google Calendar API."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _event_to_dict(event: dict) -> dict:
    """Normalize a Google Calendar event to a clean dict."""
    start = event.get("start", {})
    end = event.get("end", {})
    return {
        "id": event.get("id"),
        "title": event.get("summary", ""),
        "description": event.get("description", ""),
        "location": event.get("location", ""),
        "start": start.get("dateTime") or start.get("date"),
        "end": end.get("dateTime") or end.get("date"),
        "status": event.get("status", "confirmed"),
    }


# ── Public async API ──────────────────────────────────────────────────────────


async def get_calendar_service(user_id: str):
    """Return a Calendar API service for this user, or None."""
    return await asyncio.to_thread(_get_calendar_service_sync, user_id)


async def create_calendar(user_id: str, name: str) -> Optional[str]:
    """Create a new OZE calendar for this user. Returns calendar ID or None."""
    try:
        def _create():
            service = _get_calendar_service_sync(user_id)
            if not service:
                return None
            cal = service.calendars().insert(
                body={"summary": name, "timeZone": "Europe/Warsaw"}
            ).execute()
            return cal.get("id")

        calendar_id = await asyncio.to_thread(_create)
        return calendar_id
    except Exception as e:
        logger.error("create_calendar(%s): %s", user_id, e)
        return None


async def get_events_for_date(user_id: str, day: date) -> list[dict]:
    """Return all events on a specific day, sorted by start time."""
    try:
        user = get_user_by_id(user_id)
        if not user or not user.get("google_calendar_id"):
            return []
        calendar_id = user["google_calendar_id"]

        day_start = datetime(day.year, day.month, day.day, 0, 0, 0, tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)

        def _fetch():
            service = _get_calendar_service_sync(user_id)
            if not service:
                return []
            result = service.events().list(
                calendarId=calendar_id,
                timeMin=_to_rfc3339(day_start),
                timeMax=_to_rfc3339(day_end),
                singleEvents=True,
                orderBy="startTime",
            ).execute()
            return [_event_to_dict(e) for e in result.get("items", [])]

        return await asyncio.to_thread(_fetch)
    except Exception as e:
        logger.error("get_events_for_date(%s, %s): %s", user_id, day, e)
        return []


async def get_events_for_range(
    user_id: str, start: datetime, end: datetime
) -> list[dict]:
    """Return events in a date range, sorted by start time."""
    try:
        user = get_user_by_id(user_id)
        if not user or not user.get("google_calendar_id"):
            return []
        calendar_id = user["google_calendar_id"]

        def _fetch():
            service = _get_calendar_service_sync(user_id)
            if not service:
                return []
            result = service.events().list(
                calendarId=calendar_id,
                timeMin=_to_rfc3339(start),
                timeMax=_to_rfc3339(end),
                singleEvents=True,
                orderBy="startTime",
            ).execute()
            return [_event_to_dict(e) for e in result.get("items", [])]

        return await asyncio.to_thread(_fetch)
    except Exception as e:
        logger.error("get_events_for_range(%s): %s", user_id, e)
        return []


async def get_upcoming_events(user_id: str, hours: int = 24) -> list[dict]:
    """Return events in the next `hours` hours."""
    now = datetime.now(tz=timezone.utc)
    return await get_events_for_range(user_id, now, now + timedelta(hours=hours))


async def create_event(
    user_id: str,
    title: str,
    start: datetime,
    end: datetime,
    location: Optional[str] = None,
    description: Optional[str] = None,
) -> Optional[dict]:
    """Create a calendar event. Returns event dict with ID or None."""
    try:
        user = get_user_by_id(user_id)
        if not user or not user.get("google_calendar_id"):
            return None
        calendar_id = user["google_calendar_id"]

        body: dict = {
            "summary": title,
            "start": {"dateTime": _to_rfc3339(start), "timeZone": "Europe/Warsaw"},
            "end": {"dateTime": _to_rfc3339(end), "timeZone": "Europe/Warsaw"},
        }
        if location:
            body["location"] = location
        if description:
            body["description"] = description

        def _create():
            service = _get_calendar_service_sync(user_id)
            if not service:
                return None
            event = service.events().insert(
                calendarId=calendar_id, body=body
            ).execute()
            return _event_to_dict(event)

        return await asyncio.to_thread(_create)
    except Exception as e:
        logger.error("create_event(%s): %s", user_id, e)
        return None


async def update_event(
    user_id: str, event_id: str, updates: dict
) -> Optional[dict]:
    """Update event fields (title, start, end, location, description)."""
    try:
        user = get_user_by_id(user_id)
        if not user or not user.get("google_calendar_id"):
            return None
        calendar_id = user["google_calendar_id"]

        def _update():
            service = _get_calendar_service_sync(user_id)
            if not service:
                return None
            event = service.events().get(
                calendarId=calendar_id, eventId=event_id
            ).execute()

            if "title" in updates:
                event["summary"] = updates["title"]
            if "start" in updates:
                event["start"] = {
                    "dateTime": _to_rfc3339(updates["start"]),
                    "timeZone": "Europe/Warsaw",
                }
            if "end" in updates:
                event["end"] = {
                    "dateTime": _to_rfc3339(updates["end"]),
                    "timeZone": "Europe/Warsaw",
                }
            if "location" in updates:
                event["location"] = updates["location"]
            if "description" in updates:
                event["description"] = updates["description"]

            updated = service.events().update(
                calendarId=calendar_id, eventId=event_id, body=event
            ).execute()
            return _event_to_dict(updated)

        return await asyncio.to_thread(_update)
    except Exception as e:
        logger.error("update_event(%s, %s): %s", user_id, event_id, e)
        return None


async def delete_event(user_id: str, event_id: str) -> bool:
    """Delete a calendar event. Returns True on success."""
    try:
        user = get_user_by_id(user_id)
        if not user or not user.get("google_calendar_id"):
            return False
        calendar_id = user["google_calendar_id"]

        def _delete():
            service = _get_calendar_service_sync(user_id)
            if not service:
                return False
            service.events().delete(
                calendarId=calendar_id, eventId=event_id
            ).execute()
            return True

        return await asyncio.to_thread(_delete)
    except Exception as e:
        logger.error("delete_event(%s, %s): %s", user_id, event_id, e)
        return False


async def check_conflicts(
    user_id: str, start: datetime, end: datetime
) -> list[dict]:
    """Return events that overlap with the given time range."""
    return await get_events_for_range(user_id, start, end)


async def get_free_slots(
    user_id: str, day: date, slot_duration: int = 60
) -> list[tuple[datetime, datetime]]:
    """Return available time slots on `day` within working hours (9:00–18:00).

    Returns list of (slot_start, slot_end) tuples in UTC.
    slot_duration is in minutes.
    """
    try:
        events = await get_events_for_date(user_id, day)

        # Build busy intervals (in minutes from midnight)
        busy: list[tuple[int, int]] = []
        for event in events:
            start_str = event.get("start")
            end_str = event.get("end")
            if not start_str or not end_str:
                continue
            try:
                ev_start = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                ev_end = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                busy.append((ev_start.hour * 60 + ev_start.minute,
                              ev_end.hour * 60 + ev_end.minute))
            except Exception:
                continue

        # Generate slots
        slots = []
        current = WORKING_HOURS_START * 60  # minutes from midnight
        end_of_day = WORKING_HOURS_END * 60

        while current + slot_duration <= end_of_day:
            slot_end = current + slot_duration
            overlaps = any(
                not (slot_end <= b_start or current >= b_end)
                for b_start, b_end in busy
            )
            if not overlaps:
                slot_start_dt = datetime(
                    day.year, day.month, day.day,
                    current // 60, current % 60,
                    tzinfo=timezone.utc,
                )
                slot_end_dt = datetime(
                    day.year, day.month, day.day,
                    slot_end // 60, slot_end % 60,
                    tzinfo=timezone.utc,
                )
                slots.append((slot_start_dt, slot_end_dt))
            current += slot_duration

        return slots
    except Exception as e:
        logger.error("get_free_slots(%s, %s): %s", user_id, day, e)
        return []


async def get_todays_last_event(user_id: str) -> Optional[dict]:
    """Return the last event ending today (for follow-up scheduling). None if no events."""
    try:
        events = await get_events_for_date(user_id, date.today())
        if not events:
            return None
        # Events are sorted by start time; return the one with the latest end
        return max(events, key=lambda e: e.get("end") or "")
    except Exception as e:
        logger.error("get_todays_last_event(%s): %s", user_id, e)
        return None
