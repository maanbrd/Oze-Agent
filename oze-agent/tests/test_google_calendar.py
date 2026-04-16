"""Unit tests for shared/google_calendar.py — Google API and DB calls are mocked."""

import logging
import pytest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch


class _Execute:
    def __init__(self, value):
        self.value = value

    def execute(self):
        return self.value


class _InsertExecute:
    def __init__(self, events):
        self.events = events

    def execute(self):
        body = self.events.insert_kwargs["body"]
        return {"id": "event-1", "status": "confirmed", **body}


class _UpdateExecute:
    def __init__(self, events):
        self.events = events

    def execute(self):
        return self.events.update_kwargs["body"]


class _EventsService:
    def __init__(self, existing_event: dict | None = None):
        self.existing_event = existing_event or {}
        self.insert_kwargs = None
        self.get_kwargs = None
        self.update_kwargs = None

    def insert(self, **kwargs):
        self.insert_kwargs = kwargs
        return _InsertExecute(self)

    def get(self, **kwargs):
        self.get_kwargs = kwargs
        return _Execute(self.existing_event)

    def update(self, **kwargs):
        self.update_kwargs = kwargs
        return _UpdateExecute(self)


class _CalendarService:
    def __init__(self, events: _EventsService):
        self._events = events

    def events(self):
        return self._events


def _calendar_patches(events: _EventsService):
    return (
        patch("shared.google_calendar.get_user_by_id", return_value={"google_calendar_id": "cal-1"}),
        patch("shared.google_calendar._get_calendar_service_sync", return_value=_CalendarService(events)),
    )


# ── check_conflicts ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_check_conflicts_detects_overlap():
    """Event 10:00-11:00 should conflict with slot 10:30-11:30."""
    existing = [
        {
            "id": "evt1",
            "title": "Spotkanie Kowalski",
            "start": "2026-04-10T10:00:00+00:00",
            "end": "2026-04-10T11:00:00+00:00",
            "location": "",
            "description": "",
            "status": "confirmed",
        }
    ]
    with patch("shared.google_calendar.get_events_for_range", new=AsyncMock(return_value=existing)):
        from shared.google_calendar import check_conflicts
        start = datetime(2026, 4, 10, 10, 30, tzinfo=timezone.utc)
        end = datetime(2026, 4, 10, 11, 30, tzinfo=timezone.utc)
        conflicts = await check_conflicts("user-1", start, end)
    assert len(conflicts) == 1
    assert conflicts[0]["title"] == "Spotkanie Kowalski"


@pytest.mark.asyncio
async def test_check_conflicts_no_overlap():
    """Event 09:00-10:00 should NOT conflict with 10:00-11:00."""
    with patch("shared.google_calendar.get_events_for_range", new=AsyncMock(return_value=[])):
        from shared.google_calendar import check_conflicts
        start = datetime(2026, 4, 10, 10, 0, tzinfo=timezone.utc)
        end = datetime(2026, 4, 10, 11, 0, tzinfo=timezone.utc)
        conflicts = await check_conflicts("user-1", start, end)
    assert conflicts == []


# ── get_free_slots ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_free_slots_full_day_no_events():
    """No events → all 60-min slots from 09:00 to 18:00 are free (9 slots)."""
    with patch("shared.google_calendar.get_events_for_date", new=AsyncMock(return_value=[])):
        from shared.google_calendar import get_free_slots
        slots = await get_free_slots("user-1", date(2026, 4, 10), slot_duration=60)
    assert len(slots) == 9
    assert slots[0][0].hour == 9
    assert slots[-1][1].hour == 18


@pytest.mark.asyncio
async def test_get_free_slots_blocks_occupied_hour():
    """Event 10:00-11:00 → 10:00 slot should be blocked."""
    events = [
        {
            "id": "e1",
            "title": "Busy",
            "start": "2026-04-10T10:00:00+00:00",
            "end": "2026-04-10T11:00:00+00:00",
            "location": "", "description": "", "status": "confirmed",
        }
    ]
    with patch("shared.google_calendar.get_events_for_date", new=AsyncMock(return_value=events)):
        from shared.google_calendar import get_free_slots
        slots = await get_free_slots("user-1", date(2026, 4, 10), slot_duration=60)
    slot_starts = [s[0].hour for s in slots]
    assert 10 not in slot_starts
    assert len(slots) == 8  # 9 total - 1 blocked


@pytest.mark.asyncio
async def test_get_free_slots_returns_empty_on_error():
    """DB error → returns empty list without raising."""
    with patch("shared.google_calendar.get_events_for_date", new=AsyncMock(side_effect=Exception("DB down"))):
        from shared.google_calendar import get_free_slots
        slots = await get_free_slots("user-1", date(2026, 4, 10))
    assert slots == []


# ── D8 event_type metadata ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_event_writes_minimal_private_event_type():
    from shared.google_calendar import create_event

    events = _EventsService()
    start = datetime(2026, 4, 10, 10, 0, tzinfo=timezone.utc)
    end = datetime(2026, 4, 10, 11, 0, tzinfo=timezone.utc)

    user_patch, service_patch = _calendar_patches(events)
    with user_patch, service_patch:
        result = await create_event(
            "user-1",
            "Spotkanie",
            start,
            end,
            event_type="in_person",
        )

    private = events.insert_kwargs["body"]["extendedProperties"]["private"]
    assert private == {"event_type": "in_person"}
    assert not {"client_name", "client_row", "oze_agent"} & set(private)
    assert result["event_type"] == "in_person"


@pytest.mark.asyncio
async def test_create_event_ignores_unknown_event_type(caplog):
    from shared.google_calendar import create_event

    caplog.set_level(logging.WARNING, logger="shared.google_calendar")
    events = _EventsService()
    start = datetime(2026, 4, 10, 10, 0, tzinfo=timezone.utc)
    end = datetime(2026, 4, 10, 11, 0, tzinfo=timezone.utc)

    user_patch, service_patch = _calendar_patches(events)
    with user_patch, service_patch:
        result = await create_event(
            "user-1",
            "Spotkanie",
            start,
            end,
            event_type="unsupported",
        )

    assert "extendedProperties" not in events.insert_kwargs["body"]
    assert result["event_type"] == ""
    assert "Ignoring unknown Calendar event_type: unsupported" in caplog.text


def test_event_to_dict_returns_event_type():
    from shared.google_calendar import _event_to_dict

    event = {
        "id": "event-1",
        "summary": "Spotkanie",
        "start": {"dateTime": "2026-04-10T10:00:00+00:00"},
        "end": {"dateTime": "2026-04-10T11:00:00+00:00"},
        "extendedProperties": {"private": {"event_type": "phone_call"}},
    }

    assert _event_to_dict(event)["event_type"] == "phone_call"


@pytest.mark.asyncio
async def test_update_event_without_event_type_preserves_existing_metadata():
    from shared.google_calendar import update_event

    events = _EventsService(existing_event={
        "id": "event-1",
        "summary": "Old",
        "start": {"dateTime": "2026-04-10T10:00:00+00:00"},
        "end": {"dateTime": "2026-04-10T11:00:00+00:00"},
        "extendedProperties": {"private": {"event_type": "in_person"}},
    })

    user_patch, service_patch = _calendar_patches(events)
    with user_patch, service_patch:
        result = await update_event("user-1", "event-1", {"title": "New"})

    body = events.update_kwargs["body"]
    assert body["summary"] == "New"
    assert body["extendedProperties"]["private"] == {"event_type": "in_person"}
    assert result["event_type"] == "in_person"


@pytest.mark.asyncio
async def test_update_event_sets_event_type():
    from shared.google_calendar import update_event

    events = _EventsService(existing_event={
        "id": "event-1",
        "summary": "Spotkanie",
        "start": {"dateTime": "2026-04-10T10:00:00+00:00"},
        "end": {"dateTime": "2026-04-10T11:00:00+00:00"},
    })

    user_patch, service_patch = _calendar_patches(events)
    with user_patch, service_patch:
        result = await update_event("user-1", "event-1", {"event_type": "doc_followup"})

    body = events.update_kwargs["body"]
    assert body["extendedProperties"]["private"] == {"event_type": "doc_followup"}
    assert result["event_type"] == "doc_followup"


@pytest.mark.asyncio
@pytest.mark.parametrize("event_type", [None, ""])
async def test_update_event_removes_event_type(event_type):
    from shared.google_calendar import update_event

    events = _EventsService(existing_event={
        "id": "event-1",
        "summary": "Spotkanie",
        "start": {"dateTime": "2026-04-10T10:00:00+00:00"},
        "end": {"dateTime": "2026-04-10T11:00:00+00:00"},
        "extendedProperties": {"private": {"event_type": "in_person"}},
    })

    user_patch, service_patch = _calendar_patches(events)
    with user_patch, service_patch:
        result = await update_event("user-1", "event-1", {"event_type": event_type})

    private = events.update_kwargs["body"]["extendedProperties"]["private"]
    assert "event_type" not in private
    assert result["event_type"] == ""


@pytest.mark.asyncio
async def test_update_event_ignores_unknown_event_type(caplog):
    from shared.google_calendar import update_event

    caplog.set_level(logging.WARNING, logger="shared.google_calendar")
    events = _EventsService(existing_event={
        "id": "event-1",
        "summary": "Spotkanie",
        "start": {"dateTime": "2026-04-10T10:00:00+00:00"},
        "end": {"dateTime": "2026-04-10T11:00:00+00:00"},
        "extendedProperties": {"private": {"event_type": "in_person"}},
    })

    user_patch, service_patch = _calendar_patches(events)
    with user_patch, service_patch:
        result = await update_event("user-1", "event-1", {"event_type": "unsupported"})

    private = events.update_kwargs["body"]["extendedProperties"]["private"]
    assert private == {"event_type": "in_person"}
    assert result["event_type"] == "in_person"
    assert "Ignoring unknown Calendar event_type: unsupported" in caplog.text


# ── get_todays_last_event ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_todays_last_event_returns_latest():
    events = [
        {"id": "e1", "title": "First", "start": "2026-04-10T09:00:00+00:00", "end": "2026-04-10T10:00:00+00:00", "location": "", "description": "", "status": "confirmed"},
        {"id": "e2", "title": "Last",  "start": "2026-04-10T15:00:00+00:00", "end": "2026-04-10T16:00:00+00:00", "location": "", "description": "", "status": "confirmed"},
    ]
    with patch("shared.google_calendar.get_events_for_date", new=AsyncMock(return_value=events)):
        from shared.google_calendar import get_todays_last_event
        result = await get_todays_last_event("user-1")
    assert result["title"] == "Last"


@pytest.mark.asyncio
async def test_get_todays_last_event_none_when_no_events():
    with patch("shared.google_calendar.get_events_for_date", new=AsyncMock(return_value=[])):
        from shared.google_calendar import get_todays_last_event
        result = await get_todays_last_event("user-1")
    assert result is None
