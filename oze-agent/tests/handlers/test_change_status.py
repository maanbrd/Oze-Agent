"""Tests for change_status matching and pending confirmation behavior."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.handlers.text import _route_pending_flow, handle_change_status
from shared.clients import ClientLookupResult
from shared.pending import PendingFlowType


def _patched_lookup(result: ClientLookupResult):
    return patch(
        "bot.handlers.text.lookup_client",
        new=AsyncMock(return_value=result),
    )


def _update(telegram_id: int = 123) -> MagicMock:
    upd = MagicMock()
    upd.effective_user.id = telegram_id
    upd.effective_message.reply_text = AsyncMock()
    upd.effective_message.reply_markdown_v2 = AsyncMock()
    return upd


def _button_labels(reply_markup) -> list[str]:
    return [button.text for row in reply_markup.inline_keyboard for button in row]


@pytest.mark.asyncio
async def test_change_status_uses_entities_name_for_matching_not_whole_message():
    upd = _update()
    client = {
        "_row": 7,
        "Imię i nazwisko": "Jan Kowalski",
        "Miasto": "Warszawa",
        "Status": "Nowy lead",
    }
    result = ClientLookupResult(status="unique", clients=[client], normalized_query="jan kowalski")
    lookup = AsyncMock(return_value=result)

    with patch("bot.handlers.text.lookup_client", new=lookup), patch(
        "bot.handlers.text.save_pending"
    ) as mock_save:
        await handle_change_status(
            upd,
            MagicMock(),
            {"id": 1},
            {"entities": {"name": "Jan Kowalski", "status": "Podpisane"}},
            "Jan Kowalski podpisał umowę, zmień status na Podpisane",
        )

    lookup.assert_awaited_once_with(1, "Jan Kowalski", "")
    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_type is PendingFlowType.CHANGE_STATUS
    assert saved_flow.flow_data["row"] == 7
    assert saved_flow.flow_data["new_value"] == "Podpisane"
    labels = _button_labels(upd.effective_message.reply_markdown_v2.await_args.kwargs["reply_markup"])
    assert labels == ["✅ Zapisać", "➕ Dopisać", "❌ Anulować"]
    upd.effective_message.reply_markdown_v2.assert_awaited_once()


@pytest.mark.asyncio
async def test_change_status_without_entities_name_accepts_single_search_result_for_r1():
    upd = _update()
    search = AsyncMock(return_value=[
        {
            "_row": 8,
            "Imię i nazwisko": "Anna Nowak",
            "Miasto": "Kraków",
            "Status": "Oferta wysłana",
        }
    ])

    with patch("bot.handlers.text.search_clients", new=search), patch(
        "bot.handlers.text.save_pending"
    ) as mock_save:
        await handle_change_status(
            upd,
            MagicMock(),
            {"id": 1},
            {"entities": {"status": "Podpisane"}},
            "Anna Nowak podpisane, zmień status klienta",
        )

    search.assert_awaited_once_with(1, "Anna Nowak podpisane, zmień status klienta")
    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_type is PendingFlowType.CHANGE_STATUS
    assert saved_flow.flow_data["row"] == 8
    assert saved_flow.flow_data["client_name"] == "Anna Nowak"
    assert saved_flow.flow_data["new_value"] == "Podpisane"
    upd.effective_message.reply_markdown_v2.assert_awaited_once()


@pytest.mark.asyncio
async def test_change_status_without_entities_name_disambiguates_many_results():
    upd = _update()
    search = AsyncMock(return_value=[
        {"_row": 8, "Imię i nazwisko": "Anna Nowak", "Miasto": "Kraków", "Status": ""},
        {"_row": 9, "Imię i nazwisko": "Anna Nowicka", "Miasto": "Gdańsk", "Status": ""},
    ])

    with patch("bot.handlers.text.search_clients", new=search), patch(
        "bot.handlers.text.save_pending"
    ) as mock_save:
        await handle_change_status(
            upd,
            MagicMock(),
            {"id": 1},
            {"entities": {"status": "Podpisane"}},
            "Anna zmień status na Podpisane",
        )

    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_type is PendingFlowType.DISAMBIGUATION
    assert saved_flow.flow_data == {
        "intent": "change_status",
        "new_status": "Podpisane",
    }
    response = upd.effective_message.reply_text.call_args.args[0]
    assert "Mam 2 klientów:" in response
    assert "Którego?" in response


@pytest.mark.asyncio
async def test_change_status_single_name_token_disambiguates_many_results():
    upd = _update()
    clients = [
        {"_row": 8, "Imię i nazwisko": "Jan Mazur", "Miasto": "Kraków", "Status": ""},
        {"_row": 9, "Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa", "Status": ""},
    ]
    result = ClientLookupResult(status="multi", clients=clients, normalized_query="jan")
    lookup = AsyncMock(return_value=result)

    with patch("bot.handlers.text.lookup_client", new=lookup), patch(
        "bot.handlers.text.save_pending"
    ) as mock_save:
        await handle_change_status(
            upd,
            MagicMock(),
            {"id": 1},
            {"entities": {"name": "Jan", "status": "Podpisane"}},
            "Jan podpisał",
        )

    lookup.assert_awaited_once_with(1, "Jan", "")
    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_type is PendingFlowType.DISAMBIGUATION
    assert saved_flow.flow_data == {
        "intent": "change_status",
        "new_status": "Podpisane",
    }
    response = upd.effective_message.reply_text.call_args.args[0]
    assert "Jan Mazur" in response
    assert "Jan Kowalski" in response


@pytest.mark.asyncio
async def test_change_status_append_routes_next_action_with_status_context():
    upd = _update()
    flow = {
        "flow_type": "change_status",
        "flow_data": {
            "row": 7,
            "field": "Status",
            "old_value": "Oferta wysłana",
            "new_value": "Podpisane",
            "client_name": "Jan Kowalski",
            "city": "Warszawa",
        },
    }

    with patch("bot.handlers.text.handle_add_meeting", new=AsyncMock()) as mock_meeting:
        consumed = await _route_pending_flow(
            upd,
            MagicMock(),
            {"id": 1},
            flow,
            "telefon jutro o 14",
        )

    assert consumed is True
    mock_meeting.assert_awaited_once()
    _, _, _, intent_data, routed_text = mock_meeting.await_args.args
    assert intent_data["entities"]["event_type"] == "phone_call"
    assert intent_data["status_update"] == {
        "row": 7,
        "field": "Status",
        "old_value": "Oferta wysłana",
        "new_value": "Podpisane",
        "client_name": "Jan Kowalski",
        "city": "Warszawa",
    }
    assert "Jan Kowalski" in routed_text
    assert "Warszawa" in routed_text


@pytest.mark.asyncio
async def test_change_status_append_without_action_keeps_status_pending():
    upd = _update()
    flow = {
        "flow_type": "change_status",
        "flow_data": {
            "row": 7,
            "old_value": "Oferta wysłana",
            "new_value": "Podpisane",
            "client_name": "Jan Kowalski",
        },
    }

    with patch("bot.handlers.text.handle_add_meeting", new=AsyncMock()) as mock_meeting:
        consumed = await _route_pending_flow(
            upd,
            MagicMock(),
            {"id": 1},
            flow,
            "dopisz coś tam",
        )

    assert consumed is True
    mock_meeting.assert_not_awaited()
    response = upd.effective_message.reply_text.call_args.args[0]
    assert "Dopisz następny krok" in response


# ── phase5-followup-ux (I2/I3): intent-switch prefix auto-cancel ─────────────


@pytest.mark.asyncio
async def test_change_status_auto_cancels_on_pokaz_prefix():
    """I2 fix: 'pokaż X' during pending change_status → auto-cancel + False,
    reply '⚠️ Anulowane.', let caller re-process as fresh intent.
    Regression guard: handle_add_meeting MUST NOT fire."""
    upd = _update()
    flow = {
        "flow_type": "change_status",
        "flow_data": {"row": 7, "old_value": "X", "new_value": "Y", "client_name": "N"},
    }
    with patch("bot.handlers.text.handle_add_meeting", new=AsyncMock()) as mock_meeting, patch(
        "bot.handlers.text.delete_pending_flow"
    ):
        consumed = await _route_pending_flow(
            upd, MagicMock(), {"id": 1}, flow, "pokaż Jana Kowalskiego",
        )
    assert consumed is False
    upd.effective_message.reply_text.assert_awaited_once_with("⚠️ Anulowane.")
    mock_meeting.assert_not_called()


@pytest.mark.asyncio
async def test_change_status_auto_cancels_on_co_mam_prefix():
    """I3 fix: 'co mam dziś' during pending change_status → auto-cancel
    BEFORE text_has_action check. Key regression guard: handle_add_meeting
    MUST NOT fire (pre-fix bug: temporal 'dziś' routed here, parser failed)."""
    upd = _update()
    flow = {
        "flow_type": "change_status",
        "flow_data": {"row": 7, "old_value": "X", "new_value": "Y", "client_name": "N"},
    }
    with patch("bot.handlers.text.handle_add_meeting", new=AsyncMock()) as mock_meeting, patch(
        "bot.handlers.text.delete_pending_flow"
    ):
        consumed = await _route_pending_flow(
            upd, MagicMock(), {"id": 1}, flow, "co mam dziś",
        )
    assert consumed is False
    upd.effective_message.reply_text.assert_awaited_once_with("⚠️ Anulowane.")
    mock_meeting.assert_not_called()


@pytest.mark.asyncio
async def test_change_status_auto_cancels_on_dodaj_klienta_prefix():
    """Smoke-observed trigger: 'dodaj klienta X' during pending change_status."""
    upd = _update()
    flow = {
        "flow_type": "change_status",
        "flow_data": {"row": 7, "old_value": "X", "new_value": "Y", "client_name": "N"},
    }
    with patch("bot.handlers.text.handle_add_meeting", new=AsyncMock()) as mock_meeting, patch(
        "bot.handlers.text.delete_pending_flow"
    ):
        consumed = await _route_pending_flow(
            upd, MagicMock(), {"id": 1}, flow, "dodaj klienta Tadek Sprawdzony, Marki",
        )
    assert consumed is False
    upd.effective_message.reply_text.assert_awaited_once_with("⚠️ Anulowane.")
    mock_meeting.assert_not_called()


@pytest.mark.asyncio
async def test_change_status_spotkanie_z_still_routes_to_add_meeting():
    """Regression guard: 'spotkanie z X jutro' po change_status nadal
    wchodzi w compound/R7 path (handle_add_meeting z status_update carried).
    Fix I2/I3 NIE może tego zepsuć — meeting-related prefixes celowo
    POMINIĘTE w _search_prefixes (wąższa lista niż add_note)."""
    upd = _update()
    flow = {
        "flow_type": "change_status",
        "flow_data": {
            "row": 7, "old_value": "Oferta wysłana", "new_value": "Podpisane",
            "client_name": "Jan Kowalski", "city": "Warszawa",
        },
    }
    with patch("bot.handlers.text.handle_add_meeting", new=AsyncMock()) as mock_meeting:
        consumed = await _route_pending_flow(
            upd, MagicMock(), {"id": 1}, flow, "spotkanie z Janem jutro o 14",
        )
    assert consumed is True
    mock_meeting.assert_awaited_once()
    _, _, _, intent_data, _ = mock_meeting.await_args.args
    assert intent_data["status_update"]["new_value"] == "Podpisane"


@pytest.mark.asyncio
async def test_change_status_multi_exact_match_asks_which_one():
    """lookup_client=multi → disambiguation, NOT silent pick."""
    upd = _update()
    clients = [
        {"_row": 7, "Imię i nazwisko": "Mariusz Krzywinski", "Miasto": "Marki", "Status": ""},
        {"_row": 11, "Imię i nazwisko": "Mariusz Krzywinski", "Miasto": "Wołomin", "Status": ""},
    ]
    result = ClientLookupResult(status="multi", clients=clients, normalized_query="mariusz krzywinski")

    with _patched_lookup(result), patch(
        "bot.handlers.text.save_pending"
    ) as mock_save:
        await handle_change_status(
            upd,
            MagicMock(),
            {"id": 1},
            {"entities": {"name": "Mariusz Krzywinski", "status": "Podpisane"}},
            "Mariusz Krzywinski podpisał",
        )

    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_type is PendingFlowType.DISAMBIGUATION
    assert saved_flow.flow_data == {
        "intent": "change_status",
        "new_status": "Podpisane",
    }
    response = upd.effective_message.reply_text.call_args.args[0]
    assert "Mam 2 klientów:" in response
    assert "Mariusz Krzywinski — Marki" in response
    assert "Mariusz Krzywinski — Wołomin" in response
    assert "Którego?" in response


@pytest.mark.asyncio
async def test_change_status_entities_name_with_city_narrows_by_city():
    """entities.city is passed to lookup_client so same-name rows can narrow."""
    upd = _update()
    client = {"_row": 7, "Imię i nazwisko": "Mariusz Krzywinski", "Miasto": "Marki", "Status": ""}
    result = ClientLookupResult(status="unique", clients=[client], normalized_query="mariusz krzywinski marki")
    lookup = AsyncMock(return_value=result)

    with patch("bot.handlers.text.lookup_client", new=lookup), patch(
        "bot.handlers.text.save_pending_flow"
    ) as mock_save_flow, patch("bot.handlers.text.save_pending") as mock_save:
        await handle_change_status(
            upd,
            MagicMock(),
            {"id": 1},
            {"entities": {
                "name": "Mariusz Krzywinski",
                "city": "Marki",
                "status": "Podpisane",
            }},
            "Mariusz Krzywinski Marki podpisał",
        )

    # lookup_client narrowed to single row → auto-pick, no disambiguation
    lookup.assert_awaited_once_with(1, "Mariusz Krzywinski", "Marki")
    mock_save_flow.assert_not_called()
    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_type is PendingFlowType.CHANGE_STATUS
    assert saved_flow.flow_data["row"] == 7
    assert saved_flow.flow_data["new_value"] == "Podpisane"


@pytest.mark.asyncio
async def test_change_status_after_disambiguation_uses_three_mutation_buttons():
    from bot.handlers.buttons import _handle_select_client

    query = MagicMock()
    query.from_user.id = 123
    query.edit_message_text = AsyncMock()

    with patch(
        "bot.handlers.buttons.get_all_clients",
        new=AsyncMock(return_value=[
            {
                "_row": 7,
                "Imię i nazwisko": "Jan Kowalski",
                "Miasto": "Warszawa",
                "Status": "Oferta wysłana",
            }
        ]),
    ), patch(
        "bot.handlers.buttons.get_pending_flow",
        return_value={
            "flow_type": "disambiguation",
            "flow_data": {"intent": "change_status", "new_status": "Podpisane"},
        },
    ), patch("bot.handlers.buttons.delete_pending_flow"), patch(
        "bot.handlers.buttons.save_pending"
    ):
        await _handle_select_client(query, MagicMock(), {"id": 1}, "7")

    labels = _button_labels(query.edit_message_text.await_args.kwargs["reply_markup"])
    assert labels == ["✅ Zapisać", "➕ Dopisać", "❌ Anulować"]
