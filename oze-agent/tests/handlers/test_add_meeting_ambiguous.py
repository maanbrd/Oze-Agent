"""Slice 5.1d tests — ambiguous_client flag propagated via AddMeetingPayload.

Covers _enrich_meeting multi-match behavior (no silent-pick) and the new
handle_confirm dispatch paths:
  * compound status_update.row wins (full K/L/P+F sync)
  * ambiguous_client=True → Calendar only, no Sheets sync, no ADD_CLIENT pre-seed
  * enriched client_row present → Sheets sync using current_status from payload
  * legacy pending without new fields → safe not_found path (no second lookup)
"""

from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest

from bot.handlers.text import _auto_status_update_from_enriched, _enrich_meeting, handle_confirm
from shared.clients import ClientLookupResult
from shared.pending import PendingFlowType


def _update(telegram_id: int = 123) -> MagicMock:
    upd = MagicMock()
    upd.effective_user.id = telegram_id
    upd.effective_message.reply_text = AsyncMock()
    upd.effective_message.reply_markdown_v2 = AsyncMock()
    return upd


def _patched_lookup(result: ClientLookupResult):
    return patch(
        "bot.handlers.text.lookup_client",
        new=AsyncMock(return_value=result),
    )


# ── _enrich_meeting ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_enrich_meeting_multi_sets_ambiguous_client_true():
    """lookup_client=multi → ambiguous_client=True, client_found=False, client_row=None."""
    clients = [
        {"_row": 7, "Imię i nazwisko": "Mariusz Krzywinski", "Miasto": "Marki"},
        {"_row": 11, "Imię i nazwisko": "Mariusz Krzywinski", "Miasto": "Wołomin"},
    ]
    result = ClientLookupResult(status="multi", clients=clients, normalized_query="mariusz krzywinski")

    with _patched_lookup(result):
        enriched = await _enrich_meeting("u1", "Mariusz Krzywinski", "")

    assert enriched["ambiguous_client"] is True
    assert enriched["client_found"] is False
    assert enriched["client_row"] is None
    assert enriched["current_status"] == ""


@pytest.mark.asyncio
async def test_enrich_meeting_unique_keeps_existing_behavior():
    """unique → client_found=True, client_row resolved, ambiguous_client=False."""
    client = {
        "_row": 7,
        "Imię i nazwisko": "Jan Kowalski",
        "Miasto": "Warszawa",
        "Status": "Oferta wysłana",
        "Telefon": "600123456",
    }
    result = ClientLookupResult(status="unique", clients=[client], normalized_query="jan kowalski")

    with _patched_lookup(result):
        enriched = await _enrich_meeting("u1", "Jan Kowalski", "")

    assert enriched["ambiguous_client"] is False
    assert enriched["client_found"] is True
    assert enriched["client_row"] == 7
    assert enriched["current_status"] == "Oferta wysłana"
    assert enriched["client_city"] == "Warszawa"


@pytest.mark.asyncio
async def test_enrich_meeting_not_found_sets_ambiguous_false():
    """not_found → ambiguous_client=False (distinguishes from multi-match)."""
    result = ClientLookupResult(status="not_found", clients=[], normalized_query="piotr nowy")

    with _patched_lookup(result):
        enriched = await _enrich_meeting("u1", "Piotr Nowy", "")

    assert enriched["ambiguous_client"] is False
    assert enriched["client_found"] is False
    assert enriched["client_row"] is None


def test_auto_status_update_skipped_when_ambiguous():
    """Auto-upgrade must not fire when ambiguous_client=True (no current_status is trusted)."""
    enriched = {
        "client_found": False,
        "ambiguous_client": True,
        "client_row": None,
        "current_status": "",
    }
    assert _auto_status_update_from_enriched(enriched, "in_person") is None


# ── handle_confirm dispatch ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_handle_confirm_ambiguous_skips_sheets_sync():
    """ambiguous_client=True → Calendar event created, update_client NOT called,
    ADD_CLIENT pre-seed NOT triggered, reply carries the 'uściślij' prompt."""
    flow_data = {
        "title": "Spotkanie - Mariusz Krzywinski",
        "start": "2027-04-17T11:00:00+02:00",
        "end": "2027-04-17T12:00:00+02:00",
        "client_name": "Mariusz Krzywinski",
        "location": "",
        "description": "",
        "event_type": "in_person",
        "client_row": None,
        "current_status": "",
        "ambiguous_client": True,
    }
    upd = _update()

    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value={"flow_type": "add_meeting", "flow_data": flow_data},
    ), patch(
        "bot.handlers.text.create_event",
        new=AsyncMock(return_value={"id": "event-1"}),
    ) as mock_create, patch(
        "bot.handlers.text.update_client",
        new=AsyncMock(return_value=True),
    ) as mock_update, patch("bot.handlers.text.save_pending") as mock_save, patch(
        "bot.handlers.text.delete_pending_flow"
    ):
        await handle_confirm(upd, MagicMock(), {"id": 1}, {}, "")

    mock_create.assert_awaited_once()
    mock_update.assert_not_awaited()
    mock_save.assert_not_called()
    reply = upd.effective_message.reply_text.call_args.args[0]
    assert "✅ Spotkanie dodane do kalendarza." in reply
    assert "Mariusz Krzywinski" in reply
    assert "≥2 wpisy w arkuszu" in reply
    assert "uściślij" in reply


@pytest.mark.asyncio
async def test_handle_confirm_ambiguous_with_compound_status_update_syncs_on_explicit_row():
    """Compound status_update.row wins over ambiguous — full K/L/P+F sync on that row."""
    flow_data = {
        "title": "Telefon - Mariusz Krzywinski",
        "start": "2027-04-17T11:00:00+02:00",
        "end": "2027-04-17T11:30:00+02:00",
        "client_name": "Mariusz Krzywinski",
        "location": "telefonicznie",
        "description": "",
        "event_type": "phone_call",
        "client_row": None,
        "current_status": "",
        "ambiguous_client": True,
        "status_update": {
            "row": 11,
            "field": "Status",
            "old_value": "Oferta wysłana",
            "new_value": "Podpisane",
            "client_name": "Mariusz Krzywinski",
            "city": "Wołomin",
        },
    }
    upd = _update()

    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value={"flow_type": "add_meeting", "flow_data": flow_data},
    ), patch(
        "bot.handlers.text.create_event",
        new=AsyncMock(return_value={"id": "event-2"}),
    ), patch(
        "bot.handlers.text.update_client",
        new=AsyncMock(return_value=True),
    ) as mock_update, patch("bot.handlers.text.delete_pending_flow"):
        await handle_confirm(upd, MagicMock(), {"id": 1}, {}, "")

    mock_update.assert_awaited_once_with(
        1,
        11,
        {
            "Następny krok": "Telefon",
            "Data następnego kroku": "2027-04-17T11:00:00+02:00",
            "Data ostatniego kontaktu": ANY,
            "ID wydarzenia Kalendarz": "event-2",
            "Status": "Podpisane",
        },
    )
    upd.effective_message.reply_text.assert_awaited_once_with(
        "✅ Spotkanie dodane do kalendarza. Status klienta: Podpisane."
    )


@pytest.mark.asyncio
async def test_handle_confirm_legacy_pending_without_new_fields_goes_not_found_path():
    """Pending saved before Slice 5.1d deploy lacks client_row/ambiguous_client/current_status.
    Handler must fall to the safe not_found path (pre-seed ADD_CLIENT) WITHOUT
    ever calling search_clients again."""
    flow_data = {
        "title": "Spotkanie - Jurek Jurecki",
        "start": "2027-04-17T11:00:00+02:00",
        "end": "2027-04-17T12:00:00+02:00",
        "client_name": "Jurek Jurecki",
        "location": "Warszawa",
        "description": "",
        "event_type": "in_person",
        # NO client_row, current_status, ambiguous_client — legacy payload
    }
    upd = _update()

    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value={"flow_type": "add_meeting", "flow_data": flow_data},
    ), patch(
        "bot.handlers.text.create_event",
        new=AsyncMock(return_value={"id": "event-1"}),
    ), patch(
        "bot.handlers.text.update_client",
        new=AsyncMock(return_value=True),
    ) as mock_update, patch(
        "bot.handlers.text.search_clients",
        new=AsyncMock(return_value=[]),
    ) as mock_search, patch(
        "bot.handlers.text.save_pending"
    ) as mock_save, patch("bot.handlers.text.delete_pending_flow"):
        await handle_confirm(
            upd,
            MagicMock(),
            {"id": 1, "sheet_columns": ["Imię i nazwisko", "Telefon", "Status"]},
            {},
            "",
        )

    # Deploy safety: no second search_clients lookup, no sheet sync
    mock_search.assert_not_called()
    mock_update.assert_not_awaited()
    # Legacy not_found path: pre-seed ADD_CLIENT draft
    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_type is PendingFlowType.ADD_CLIENT
    assert saved_flow.flow_data["client_data"]["Imię i nazwisko"] == "Jurek Jurecki"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "scenario_flow_data",
    [
        # unique path
        {
            "title": "Spotkanie - X",
            "start": "2027-04-17T11:00:00+02:00",
            "end": "2027-04-17T12:00:00+02:00",
            "client_name": "X",
            "location": "",
            "description": "",
            "event_type": "in_person",
            "client_row": 7,
            "current_status": "Nowy lead",
            "ambiguous_client": False,
        },
        # ambiguous path
        {
            "title": "Spotkanie - Y",
            "start": "2027-04-17T11:00:00+02:00",
            "end": "2027-04-17T12:00:00+02:00",
            "client_name": "Y",
            "location": "",
            "description": "",
            "event_type": "in_person",
            "client_row": None,
            "current_status": "",
            "ambiguous_client": True,
        },
        # not_found explicit (new payload)
        {
            "title": "Spotkanie - Z",
            "start": "2027-04-17T11:00:00+02:00",
            "end": "2027-04-17T12:00:00+02:00",
            "client_name": "Z",
            "location": "",
            "description": "",
            "event_type": "in_person",
            "client_row": None,
            "current_status": "",
            "ambiguous_client": False,
        },
        # legacy pending (no new fields)
        {
            "title": "Spotkanie - W",
            "start": "2027-04-17T11:00:00+02:00",
            "end": "2027-04-17T12:00:00+02:00",
            "client_name": "W",
            "location": "",
            "description": "",
            "event_type": "in_person",
        },
    ],
    ids=["unique", "ambiguous", "not_found_new", "legacy"],
)
async def test_handle_confirm_add_meeting_branch_does_not_call_search_clients(scenario_flow_data):
    """Scoped guard — for every add_meeting dispatch path in handle_confirm,
    search_clients must NOT be called (second silent-pick site removed).
    Batch add_meetings is explicitly out of scope (POST-MVP legacy) and may
    still call search_clients."""
    upd = _update()

    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value={"flow_type": "add_meeting", "flow_data": scenario_flow_data},
    ), patch(
        "bot.handlers.text.create_event",
        new=AsyncMock(return_value={"id": "event-1"}),
    ), patch(
        "bot.handlers.text.update_client",
        new=AsyncMock(return_value=True),
    ), patch(
        "bot.handlers.text.search_clients",
        new=AsyncMock(return_value=[]),
    ) as mock_search, patch("bot.handlers.text.save_pending"), patch(
        "bot.handlers.text.delete_pending_flow"
    ):
        await handle_confirm(
            upd,
            MagicMock(),
            {"id": 1, "sheet_columns": ["Imię i nazwisko", "Status"]},
            {},
            "",
        )

    mock_search.assert_not_called()
