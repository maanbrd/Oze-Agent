"""Unit tests for shared/google_calendar.py — Google API and DB calls are mocked."""

import pytest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch


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
