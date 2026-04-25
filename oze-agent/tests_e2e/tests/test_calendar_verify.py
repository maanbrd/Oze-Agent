"""Pure unit tests for tests_e2e.calendar_verify.

Mocks `shared.google_calendar` so tests run without Supabase / Google.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

from tests_e2e.calendar_verify import (
    VALID_EVENT_TYPES,
    assert_event_at_time,
    assert_event_duration,
    assert_event_type,
    delete_synthetic_events,
    find_event_by_summary_in_window,
    find_synthetic_events,
)


def _make_event(
    summary: str = "evt",
    event_type: str = "in_person",
    start: datetime | None = None,
    duration_min: int = 60,
    eid: str = "id-1",
) -> dict:
    if start is None:
        start = datetime(2026, 4, 26, 14, 0, tzinfo=timezone.utc)
    end = start + timedelta(minutes=duration_min)
    return {
        "id": eid,
        "title": summary,
        "description": "",
        "location": "",
        "start": start.isoformat(),
        "end": end.isoformat(),
        "status": "confirmed",
        "event_type": event_type,
    }


# ── find_event_by_summary_in_window ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_find_event_by_summary_returns_first_match():
    events = [
        _make_event(summary="Random A", eid="a"),
        _make_event(summary="E2E-Beta-Tester-X", eid="b"),
    ]
    with patch(
        "tests_e2e.calendar_verify.get_events_for_range",
        new=AsyncMock(return_value=events),
    ):
        e = await find_event_by_summary_in_window(
            "uid", "E2E-Beta-Tester",
            datetime(2026, 4, 26, tzinfo=timezone.utc),
            datetime(2026, 4, 27, tzinfo=timezone.utc),
        )
    assert e is not None
    assert e["id"] == "b"


@pytest.mark.asyncio
async def test_find_event_by_summary_no_match_returns_none():
    with patch(
        "tests_e2e.calendar_verify.get_events_for_range",
        new=AsyncMock(return_value=[]),
    ):
        e = await find_event_by_summary_in_window(
            "uid", "X",
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            datetime(2026, 1, 2, tzinfo=timezone.utc),
        )
    assert e is None


# ── assert_event_type ───────────────────────────────────────────────────────


def test_assert_event_type_match():
    e = _make_event(event_type="phone_call")
    ok, _ = assert_event_type(e, "phone_call")
    assert ok is True


def test_assert_event_type_mismatch():
    e = _make_event(event_type="in_person")
    ok, detail = assert_event_type(e, "phone_call")
    assert ok is False
    assert "phone_call" in detail and "in_person" in detail


def test_assert_event_type_rejects_invalid_expected():
    e = _make_event()
    ok, detail = assert_event_type(e, "not_a_real_type")
    assert ok is False
    assert "invalid expected" in detail


def test_valid_event_types_constant():
    """Sanity: VALID_EVENT_TYPES matches INTENCJE_MVP §4 spec."""
    assert set(VALID_EVENT_TYPES) == {
        "in_person", "phone_call", "offer_email", "doc_followup",
    }


# ── assert_event_at_time ────────────────────────────────────────────────────


def test_assert_event_at_time_exact_match():
    expected = datetime(2026, 4, 26, 14, 0, tzinfo=timezone.utc)
    e = _make_event(start=expected)
    ok, _ = assert_event_at_time(e, expected)
    assert ok is True


def test_assert_event_at_time_within_tolerance():
    expected = datetime(2026, 4, 26, 14, 0, tzinfo=timezone.utc)
    actual = datetime(2026, 4, 26, 14, 3, tzinfo=timezone.utc)  # +3 min
    e = _make_event(start=actual)
    ok, _ = assert_event_at_time(e, expected, tolerance_min=5)
    assert ok is True


def test_assert_event_at_time_beyond_tolerance():
    expected = datetime(2026, 4, 26, 14, 0, tzinfo=timezone.utc)
    actual = datetime(2026, 4, 26, 14, 10, tzinfo=timezone.utc)  # +10 min
    e = _make_event(start=actual)
    ok, _ = assert_event_at_time(e, expected, tolerance_min=5)
    assert ok is False


def test_assert_event_at_time_handles_unparseable():
    e = {"start": "not-a-date"}
    ok, detail = assert_event_at_time(e, datetime(2026, 4, 26, tzinfo=timezone.utc))
    assert ok is False
    assert "could not parse" in detail


def test_assert_event_at_time_requires_tz_aware_expected():
    e = _make_event()
    ok, detail = assert_event_at_time(e, datetime(2026, 4, 26, 14, 0))  # naive
    assert ok is False
    assert "timezone" in detail.lower()


# ── assert_event_duration ───────────────────────────────────────────────────


def test_assert_event_duration_exact():
    e = _make_event(duration_min=15)
    ok, _ = assert_event_duration(e, 15)
    assert ok is True


def test_assert_event_duration_within_tolerance():
    e = _make_event(duration_min=16)
    ok, _ = assert_event_duration(e, 15, tolerance_min=1)
    assert ok is True


def test_assert_event_duration_outside_tolerance():
    e = _make_event(duration_min=20)
    ok, _ = assert_event_duration(e, 15, tolerance_min=1)
    assert ok is False


# ── find_synthetic_events ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_find_synthetic_events_excludes_non_e2e():
    events = [
        _make_event(summary="E2E-Beta-Tester-143052-B06"),
        _make_event(summary="Real meeting", eid="real"),
        _make_event(summary="E2E-Beta-Fixture-Conflict-Slot", eid="fixture"),
    ]
    with patch(
        "tests_e2e.calendar_verify.get_events_for_range",
        new=AsyncMock(return_value=events),
    ):
        out = await find_synthetic_events("uid")
    titles = [e["title"] for e in out]
    assert "Real meeting" not in titles
    assert any("143052" in t for t in titles)
    # Fixture excluded by default
    assert not any("Fixture" in t for t in titles)


@pytest.mark.asyncio
async def test_find_synthetic_events_run_id_filter():
    events = [
        _make_event(summary="E2E-Beta-Tester-143052-B06", eid="a"),
        _make_event(summary="E2E-Beta-Tester-150000-B07", eid="b"),
    ]
    with patch(
        "tests_e2e.calendar_verify.get_events_for_range",
        new=AsyncMock(return_value=events),
    ):
        out = await find_synthetic_events("uid", run_id="143052")
    assert len(out) == 1
    assert out[0]["id"] == "a"


# ── delete_synthetic_events ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_synthetic_events_counts_successes():
    events = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
    results = {"a": True, "b": False, "c": True}

    async def fake_delete(uid, eid):
        return results[eid]

    with patch("tests_e2e.calendar_verify.delete_event", new=fake_delete):
        n = await delete_synthetic_events("uid", events)
    assert n == 2


@pytest.mark.asyncio
async def test_delete_synthetic_events_skips_events_without_id():
    events = [{"title": "no id"}, {"id": "a"}]
    with patch("tests_e2e.calendar_verify.delete_event", new=AsyncMock(return_value=True)):
        n = await delete_synthetic_events("uid", events)
    assert n == 1
