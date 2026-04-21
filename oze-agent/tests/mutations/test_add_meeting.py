"""Slice 5.4 — commit_add_meeting pipeline.

Covers the ordered Calendar → Sheets contract with explicit
partial-success semantics. Sub-paths:

  A — client_row set, no compound / no auto-upgrade → K/L/P (auto J)
  B — client_row set, auto-upgrade (in_person + Nowy lead OR empty)
  C — compound status_update.row present, wins over client_row
  D — no sync_row → Calendar-only, sheets_attempted=False

Plus guards: Calendar fail short-circuits before Sheets, Sheets fail
after Calendar OK produces partial (success=True, sheets_error set),
compound.new_value wins over auto-upgrade, pipeline never reaches
lookup_client / search_clients.
"""

from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from shared.mutations import AddMeetingResult, commit_add_meeting


# ── Helpers ──────────────────────────────────────────────────────────────────


def _start() -> datetime:
    return datetime(2027, 5, 10, 14, 0, tzinfo=timezone.utc)


def _end() -> datetime:
    return datetime(2027, 5, 10, 15, 0, tzinfo=timezone.utc)


def _patched(event_return=None, sheets_return=True):
    """Convenience patcher for the two external dependencies."""
    return (
        patch(
            "shared.mutations.add_meeting.create_event",
            new=AsyncMock(return_value=event_return if event_return is not None else {"id": "ev-1"}),
        ),
        patch(
            "shared.mutations.add_meeting.update_client_row_touching_contact",
            new=AsyncMock(return_value=sheets_return),
        ),
    )


_MISSING = object()


async def _call(
    client_row,
    *,
    event_type="in_person",
    client_current_status=None,
    status_update=None,
    sheets_return=True,
    event_return=_MISSING,
) -> tuple[AddMeetingResult, AsyncMock, AsyncMock]:
    effective_event = {"id": "ev-1"} if event_return is _MISSING else event_return
    mock_create_patch = patch(
        "shared.mutations.add_meeting.create_event",
        new=AsyncMock(return_value=effective_event),
    )
    mock_sheets_patch = patch(
        "shared.mutations.add_meeting.update_client_row_touching_contact",
        new=AsyncMock(return_value=sheets_return),
    )
    with mock_create_patch as mock_create, mock_sheets_patch as mock_sheets:
        result = await commit_add_meeting(
            "u1",
            title="Spotkanie — X",
            start=_start(),
            end=_end(),
            event_type=event_type,
            location="loc",
            description="desc",
            client_row=client_row,
            today=date(2027, 5, 10),
            client_current_status=client_current_status,
            status_update=status_update,
        )
    return result, mock_create, mock_sheets


# ── Path A: client_row, no status_update, not Nowy lead ──────────────────────


@pytest.mark.asyncio
async def test_path_a_client_row_without_autoupgrade_syncs_klp():
    result, mock_create, mock_sheets = await _call(
        client_row=7,
        event_type="phone_call",
        client_current_status="Oferta wysłana",
    )
    assert result.success is True
    assert result.sheets_attempted is True
    assert result.sheets_synced is True
    assert result.status_updated is False
    mock_create.assert_awaited_once()
    mock_sheets.assert_awaited_once()
    _, row, updates = mock_sheets.await_args.args
    assert row == 7
    assert updates == {
        "Następny krok": "Telefon",
        "Data następnego kroku": _start().isoformat(),
        "ID wydarzenia Kalendarz": "ev-1",
    }


# ── Path B: auto-upgrade (in_person + Nowy lead OR empty) ────────────────────


@pytest.mark.asyncio
async def test_path_b_autoupgrade_from_nowy_lead():
    result, _, mock_sheets = await _call(
        client_row=7,
        event_type="in_person",
        client_current_status="Nowy lead",
    )
    assert result.status_updated is True
    assert result.status_new_value == "Spotkanie umówione"
    _, _, updates = mock_sheets.await_args.args
    assert updates["Status"] == "Spotkanie umówione"
    assert updates["Następny krok"] == "Spotkanie"


@pytest.mark.asyncio
async def test_path_b_autoupgrade_from_empty_status():
    """Auto-upgrade contract includes "" — a row created via ADD_CLIENT
    pre-seed without explicit status still qualifies."""
    result, _, mock_sheets = await _call(
        client_row=7,
        event_type="in_person",
        client_current_status="",
    )
    assert result.status_updated is True
    assert result.status_new_value == "Spotkanie umówione"
    _, _, updates = mock_sheets.await_args.args
    assert updates["Status"] == "Spotkanie umówione"


@pytest.mark.asyncio
async def test_autoupgrade_skipped_for_phone_call_event_type():
    result, _, mock_sheets = await _call(
        client_row=7,
        event_type="phone_call",
        client_current_status="Nowy lead",
    )
    assert result.status_updated is False
    _, _, updates = mock_sheets.await_args.args
    assert "Status" not in updates


@pytest.mark.asyncio
async def test_autoupgrade_skipped_for_advanced_status():
    result, _, mock_sheets = await _call(
        client_row=7,
        event_type="in_person",
        client_current_status="Oferta wysłana",
    )
    assert result.status_updated is False
    _, _, updates = mock_sheets.await_args.args
    assert "Status" not in updates


# ── Path C: compound row wins over client_row ────────────────────────────────


@pytest.mark.asyncio
async def test_path_c_compound_row_wins_over_client_row():
    """client_row=7 but status_update.row=42 → full sync on row 42."""
    result, _, mock_sheets = await _call(
        client_row=7,
        event_type="phone_call",
        status_update={
            "row": 42,
            "field": "Status",
            "old_value": "Oferta wysłana",
            "new_value": "Podpisane",
            "client_name": "X",
            "city": "",
        },
    )
    assert result.success is True
    assert result.status_updated is True
    assert result.status_new_value == "Podpisane"
    _, row, updates = mock_sheets.await_args.args
    assert row == 42
    assert updates["Status"] == "Podpisane"
    assert updates["Następny krok"] == "Telefon"


@pytest.mark.asyncio
async def test_compound_wins_over_autoupgrade():
    """in_person + Nowy lead would trigger auto-upgrade, but a compound
    status_update.new_value explicitly sets the target status."""
    result, _, mock_sheets = await _call(
        client_row=7,
        event_type="in_person",
        client_current_status="Nowy lead",
        status_update={"row": 7, "field": "Status", "new_value": "Podpisane"},
    )
    assert result.status_new_value == "Podpisane"
    _, _, updates = mock_sheets.await_args.args
    assert updates["Status"] == "Podpisane"


@pytest.mark.asyncio
async def test_compound_empty_row_falls_back_to_client_row():
    """status_update present but row=None → sync_row = client_row.
    Pipeline still applies new_value to that row."""
    result, _, mock_sheets = await _call(
        client_row=7,
        event_type="in_person",
        status_update={"row": None, "field": "Status", "new_value": "Podpisane"},
    )
    _, row, updates = mock_sheets.await_args.args
    assert row == 7
    assert updates["Status"] == "Podpisane"
    assert result.status_new_value == "Podpisane"


# ── Path D: no sync_row → Calendar-only ──────────────────────────────────────


@pytest.mark.asyncio
async def test_path_d_no_client_row_is_calendar_only():
    result, mock_create, mock_sheets = await _call(client_row=None)
    assert result.success is True
    assert result.sheets_attempted is False
    assert result.sheets_synced is False
    assert result.sheets_error is None
    mock_create.assert_awaited_once()
    mock_sheets.assert_not_awaited()


# ── Calendar failure ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_calendar_fail_returns_calendar_down_and_skips_sheets():
    result, _, mock_sheets = await _call(
        client_row=7,
        event_return=None,   # create_event returns falsy
    )
    assert result.success is False
    assert result.error_message == "calendar_down"
    assert result.sheets_attempted is False
    mock_sheets.assert_not_awaited()


# ── Sheets failure after Calendar OK (partial) ───────────────────────────────


@pytest.mark.asyncio
async def test_sheets_fail_after_calendar_ok_is_partial_success():
    result, _, _ = await _call(
        client_row=7,
        event_type="in_person",
        client_current_status="Nowy lead",
        sheets_return=False,
    )
    assert result.success is True                      # Calendar ok
    assert result.sheets_attempted is True
    assert result.sheets_synced is False
    assert result.sheets_error == "google_down"
    assert result.calendar_event_id == "ev-1"
    # Status did NOT actually land — handler contract: partial copy trumps
    # "Status klienta: X." copy, so status_updated stays False.
    assert result.status_updated is False


# ── event_type plumbs through to Calendar ────────────────────────────────────


@pytest.mark.asyncio
async def test_event_type_forwarded_to_create_event_kwarg():
    _, mock_create, _ = await _call(client_row=7, event_type="offer_email")
    assert mock_create.await_args.kwargs["event_type"] == "offer_email"


# ── Guard: pipeline never calls search_clients / lookup_client ───────────────


@pytest.mark.asyncio
async def test_pipeline_never_calls_search_or_lookup():
    """Slice 5.4 must not regress the second silent-pick fix — the pipeline
    relies entirely on the client_row the caller passed in."""
    with patch(
        "shared.mutations.add_meeting.create_event",
        new=AsyncMock(return_value={"id": "ev-1"}),
    ), patch(
        "shared.mutations.add_meeting.update_client_row_touching_contact",
        new=AsyncMock(return_value=True),
    ), patch(
        "shared.google_sheets.search_clients",
        new=AsyncMock(),
    ) as mock_search, patch(
        "shared.clients.find.lookup_client",
        new=AsyncMock(),
    ) as mock_lookup:
        await commit_add_meeting(
            "u1",
            title="Spotkanie",
            start=_start(),
            end=_end(),
            event_type="in_person",
            location="",
            description="",
            client_row=7,
            today=date(2027, 5, 10),
            client_current_status="Nowy lead",
        )
    mock_search.assert_not_called()
    mock_lookup.assert_not_called()
