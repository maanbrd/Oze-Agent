"""Confirmation tests for add_meeting with carried client data."""

from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest

from bot.handlers.text import handle_confirm
from shared.pending import PendingFlowType


def _update(telegram_id: int = 123) -> MagicMock:
    upd = MagicMock()
    upd.effective_user.id = telegram_id
    upd.effective_message.reply_text = AsyncMock()
    upd.effective_message.reply_markdown_v2 = AsyncMock()
    return upd


@pytest.mark.asyncio
async def test_add_meeting_confirm_offers_add_client_with_carried_client_data():
    flow_data = {
        "title": "Spotkanie - Jurek Jurecki",
        "start": "2026-04-17T11:00:00+02:00",
        "end": "2026-04-17T12:00:00+02:00",
        "client_name": "Jurek Jurecki",
        "location": "Warszawa",
        "description": "",
        "event_type": "in_person",
        "client_data": {
            "Imię i nazwisko": "Jurek Jurecki",
            "Telefon": "746938764",
            "Produkt": "Magazyn energii",
            "Notatki": "Zużycie 4500kw, magazyn 10kw",
        },
    }
    upd = _update()

    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value={"flow_type": "add_meeting", "flow_data": flow_data},
    ), patch(
        "bot.handlers.text.create_event",
        new=AsyncMock(return_value={"id": "event-1"}),
    ) as mock_create, patch(
        "bot.handlers.text.search_clients",
        new=AsyncMock(return_value=[]),
    ), patch("bot.handlers.text.save_pending") as mock_save, patch(
        "bot.handlers.text.delete_pending_flow"
    ) as mock_delete:
        await handle_confirm(
            upd,
            MagicMock(),
            {"id": 1, "sheet_columns": ["Imię i nazwisko", "Telefon", "Produkt", "Notatki"]},
            {},
            "",
        )

    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_type is PendingFlowType.ADD_CLIENT
    assert saved_flow.flow_data["client_data"]["Status"] == "Spotkanie umówione"
    assert saved_flow.flow_data["client_data"]["Telefon"] == "746938764"
    assert saved_flow.flow_data["client_data"]["Produkt"] == "Magazyn energii"
    assert saved_flow.flow_data["client_data"]["Notatki"] == "Zużycie 4500kw, magazyn 10kw"
    create_kwargs = mock_create.await_args.kwargs
    assert "Telefon: 746938764" in create_kwargs["description"]
    assert "Produkt: Magazyn energii" in create_kwargs["description"]
    assert "Notatki: Zużycie 4500kw, magazyn 10kw" in create_kwargs["description"]
    assert create_kwargs["event_type"] == "in_person"
    mock_delete.assert_not_called()
    response = upd.effective_message.reply_text.call_args.args[0]
    assert "Spotkanie dodane" in response
    assert "Tel. 746 938 764" in response
    assert "Magazyn energii" in response
    assert "Zużycie 4500kw, magazyn 10kw" in response


@pytest.mark.asyncio
async def test_add_meeting_confirm_recovers_client_name_from_client_data():
    flow_data = {
        "title": "Spotkanie",
        "start": "2026-04-17T14:00:00+02:00",
        "end": "2026-04-17T15:00:00+02:00",
        "client_name": "",
        "location": "ul. Paderewskiego 14/2, Strzeszew",
        "description": "",
        "event_type": "in_person",
        "client_data": {
            "Imię i nazwisko": "Andrzej Andrzejowski",
            "Miasto": "Strzeszew",
            "Adres": "ul. Paderewskiego 14/2",
            "Telefon": "449558338",
            "Produkt": "PV + Magazyn energii",
        },
    }
    upd = _update()

    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value={"flow_type": "add_meeting", "flow_data": flow_data},
    ), patch(
        "bot.handlers.text.create_event",
        new=AsyncMock(return_value={"id": "event-1"}),
    ) as mock_create, patch(
        "bot.handlers.text.search_clients",
        new=AsyncMock(return_value=[]),
    ), patch("bot.handlers.text.save_pending") as mock_save, patch(
        "bot.handlers.text.delete_pending_flow"
    ) as mock_delete:
        await handle_confirm(
            upd,
            MagicMock(),
            {"id": 1, "sheet_columns": ["Imię i nazwisko", "Telefon", "Produkt", "Status"]},
            {},
            "",
        )

    create_kwargs = mock_create.await_args.kwargs
    assert create_kwargs["title"] == "Spotkanie — Andrzej Andrzejowski"
    assert create_kwargs["event_type"] == "in_person"
    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_type is PendingFlowType.ADD_CLIENT
    assert saved_flow.flow_data["client_data"]["Imię i nazwisko"] == "Andrzej Andrzejowski"
    assert saved_flow.flow_data["client_data"]["Telefon"] == "449558338"
    assert saved_flow.flow_data["client_data"]["Produkt"] == "PV + Magazyn energii"
    assert saved_flow.flow_data["client_data"]["Status"] == "Spotkanie umówione"
    mock_delete.assert_not_called()


@pytest.mark.asyncio
async def test_add_meeting_confirm_updates_existing_new_lead_status():
    flow_data = {
        "title": "Spotkanie - Jurek Jurecki",
        "start": "2026-04-17T11:00:00+02:00",
        "end": "2026-04-17T12:00:00+02:00",
        "client_name": "Jurek Jurecki",
        "location": "Warszawa",
        "description": "",
        "event_type": "in_person",
    }
    upd = _update()

    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value={"flow_type": "add_meeting", "flow_data": flow_data},
    ), patch(
        "bot.handlers.text.create_event",
        new=AsyncMock(return_value={"id": "event-1"}),
    ), patch(
        "bot.handlers.text.search_clients",
        new=AsyncMock(return_value=[
            {"_row": 7, "Imię i nazwisko": "Jurek Jurecki", "Status": "Nowy lead"}
        ]),
    ), patch(
        "bot.handlers.text.update_client",
        new=AsyncMock(return_value=True),
    ) as mock_update, patch("bot.handlers.text.save_pending") as mock_save, patch(
        "bot.handlers.text.delete_pending_flow"
    ):
        await handle_confirm(upd, MagicMock(), {"id": 1}, {}, "")

    mock_update.assert_awaited_once_with(
        1,
        7,
        {
            "Następny krok": "Spotkanie",
            "Data następnego kroku": "2026-04-17T11:00:00+02:00",
            "Data ostatniego kontaktu": ANY,
            "ID wydarzenia Kalendarz": "event-1",
            "Status": "Spotkanie umówione",
        },
    )
    mock_save.assert_not_called()
    upd.effective_message.reply_text.assert_awaited_once_with(
        "✅ Spotkanie dodane do kalendarza. Status klienta: Spotkanie umówione."
    )


@pytest.mark.asyncio
async def test_add_meeting_confirm_does_not_downgrade_advanced_status():
    flow_data = {
        "title": "Spotkanie - Jurek Jurecki",
        "start": "2026-04-17T11:00:00+02:00",
        "end": "2026-04-17T12:00:00+02:00",
        "client_name": "Jurek Jurecki",
        "location": "Warszawa",
        "description": "",
        "event_type": "in_person",
    }
    upd = _update()

    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value={"flow_type": "add_meeting", "flow_data": flow_data},
    ), patch(
        "bot.handlers.text.create_event",
        new=AsyncMock(return_value={"id": "event-1"}),
    ), patch(
        "bot.handlers.text.search_clients",
        new=AsyncMock(return_value=[
            {"_row": 7, "Imię i nazwisko": "Jurek Jurecki", "Status": "Oferta wysłana"}
        ]),
    ), patch(
        "bot.handlers.text.update_client",
        new=AsyncMock(return_value=True),
    ) as mock_update, patch("bot.handlers.text.delete_pending_flow"):
        await handle_confirm(upd, MagicMock(), {"id": 1}, {}, "")

    mock_update.assert_awaited_once_with(
        1,
        7,
        {
            "Następny krok": "Spotkanie",
            "Data następnego kroku": "2026-04-17T11:00:00+02:00",
            "Data ostatniego kontaktu": ANY,
            "ID wydarzenia Kalendarz": "event-1",
        },
    )
    upd.effective_message.reply_text.assert_awaited_once_with("✅ Spotkanie dodane do kalendarza.")


@pytest.mark.asyncio
@pytest.mark.parametrize("event_type", ["phone_call", "offer_email", "doc_followup"])
async def test_add_meeting_confirm_skips_status_for_non_in_person_event_types(event_type):
    flow_data = {
        "title": "Spotkanie - Jurek Jurecki",
        "start": "2026-04-17T11:00:00+02:00",
        "end": "2026-04-17T12:00:00+02:00",
        "client_name": "Jurek Jurecki",
        "location": "Warszawa",
        "description": "",
        "event_type": event_type,
    }
    upd = _update()

    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value={"flow_type": "add_meeting", "flow_data": flow_data},
    ), patch(
        "bot.handlers.text.create_event",
        new=AsyncMock(return_value={"id": "event-1"}),
    ) as mock_create, patch(
        "bot.handlers.text.search_clients",
        new=AsyncMock(return_value=[
            {"_row": 7, "Imię i nazwisko": "Jurek Jurecki", "Status": "Nowy lead"}
        ]),
    ), patch(
        "bot.handlers.text.update_client",
        new=AsyncMock(return_value=True),
    ) as mock_update, patch("bot.handlers.text.delete_pending_flow"):
        await handle_confirm(upd, MagicMock(), {"id": 1}, {}, "")

    expected_label = {
        "phone_call": "Telefon",
        "offer_email": "Wysłać ofertę",
        "doc_followup": "Follow-up dokumentowy",
    }[event_type]
    assert mock_create.await_args.kwargs["event_type"] == event_type
    mock_update.assert_awaited_once_with(
        1,
        7,
        {
            "Następny krok": expected_label,
            "Data następnego kroku": "2026-04-17T11:00:00+02:00",
            "Data ostatniego kontaktu": ANY,
            "ID wydarzenia Kalendarz": "event-1",
        },
    )
    upd.effective_message.reply_text.assert_awaited_once_with("✅ Spotkanie dodane do kalendarza.")


@pytest.mark.asyncio
async def test_add_meeting_confirm_updates_only_first_name_safe_match():
    flow_data = {
        "title": "Spotkanie - Jurek Jurecki",
        "start": "2026-04-17T11:00:00+02:00",
        "end": "2026-04-17T12:00:00+02:00",
        "client_name": "Jurek Jurecki",
        "location": "Warszawa",
        "description": "",
        "event_type": "in_person",
    }
    upd = _update()

    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value={"flow_type": "add_meeting", "flow_data": flow_data},
    ), patch(
        "bot.handlers.text.create_event",
        new=AsyncMock(return_value={"id": "event-1"}),
    ), patch(
        "bot.handlers.text.search_clients",
        new=AsyncMock(return_value=[
            {"_row": 3, "Imię i nazwisko": "Zbigniew Jurecki", "Status": "Nowy lead"},
            {"_row": 7, "Imię i nazwisko": "Jurek Jurecki", "Status": "Nowy lead"},
            {"_row": 9, "Imię i nazwisko": "Anna Jurecka", "Status": "Nowy lead"},
        ]),
    ), patch(
        "bot.handlers.text.update_client",
        new=AsyncMock(return_value=True),
    ) as mock_update, patch("bot.handlers.text.save_pending") as mock_save, patch(
        "bot.handlers.text.delete_pending_flow"
    ):
        await handle_confirm(upd, MagicMock(), {"id": 1}, {}, "")

    mock_update.assert_awaited_once_with(
        1,
        7,
        {
            "Następny krok": "Spotkanie",
            "Data następnego kroku": "2026-04-17T11:00:00+02:00",
            "Data ostatniego kontaktu": ANY,
            "ID wydarzenia Kalendarz": "event-1",
            "Status": "Spotkanie umówione",
        },
    )
    mock_save.assert_not_called()


@pytest.mark.asyncio
async def test_add_meeting_confirm_no_first_name_match_creates_add_client_draft():
    flow_data = {
        "title": "Spotkanie - Jurek Jurecki",
        "start": "2026-04-17T11:00:00+02:00",
        "end": "2026-04-17T12:00:00+02:00",
        "client_name": "Jurek Jurecki",
        "location": "Warszawa",
        "description": "",
        "event_type": "in_person",
        "client_data": {"Telefon": "746938764"},
    }
    upd = _update()

    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value={"flow_type": "add_meeting", "flow_data": flow_data},
    ), patch(
        "bot.handlers.text.create_event",
        new=AsyncMock(return_value={"id": "event-1"}),
    ), patch(
        "bot.handlers.text.search_clients",
        new=AsyncMock(return_value=[
            {"_row": 3, "Imię i nazwisko": "Zbigniew Jurecki", "Status": "Nowy lead"},
            {"_row": 9, "Imię i nazwisko": "Anna Jurecka", "Status": "Nowy lead"},
        ]),
    ), patch(
        "bot.handlers.text.update_client",
        new=AsyncMock(return_value=True),
    ) as mock_update, patch("bot.handlers.text.save_pending") as mock_save, patch(
        "bot.handlers.text.delete_pending_flow"
    ) as mock_delete:
        await handle_confirm(
            upd,
            MagicMock(),
            {"id": 1, "sheet_columns": ["Imię i nazwisko", "Telefon", "Status"]},
            {},
            "",
        )

    mock_update.assert_not_awaited()
    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_type is PendingFlowType.ADD_CLIENT
    assert saved_flow.flow_data["client_data"]["Imię i nazwisko"] == "Jurek Jurecki"
    assert saved_flow.flow_data["client_data"]["Telefon"] == "746938764"
    assert saved_flow.flow_data["client_data"]["Status"] == "Spotkanie umówione"
    mock_delete.assert_not_called()


@pytest.mark.asyncio
async def test_add_meeting_confirm_rejects_first_name_collision():
    flow_data = {
        "title": "Spotkanie - Krzysztof Krzysztofiński",
        "start": "2026-04-17T08:00:00+02:00",
        "end": "2026-04-17T09:00:00+02:00",
        "client_name": "Krzysztof Krzysztofiński",
        "location": "Marki",
        "description": "weź jego fakturę",
        "event_type": "in_person",
        "client_data": {
            "Imię i nazwisko": "Krzysztof Krzysztofiński",
            "Miasto": "Marki",
            "Adres": "ul. Duża 5",
            "Produkt": "Magazyn energii",
        },
    }
    upd = _update()

    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value={"flow_type": "add_meeting", "flow_data": flow_data},
    ), patch(
        "bot.handlers.text.create_event",
        new=AsyncMock(return_value={"id": "event-1"}),
    ), patch(
        "bot.handlers.text.search_clients",
        new=AsyncMock(return_value=[
            {"_row": 33, "Imię i nazwisko": "Krzysztof Wojcik", "Status": "Nowy lead"}
        ]),
    ), patch(
        "bot.handlers.text.update_client",
        new=AsyncMock(return_value=True),
    ) as mock_update, patch("bot.handlers.text.save_pending") as mock_save, patch(
        "bot.handlers.text.delete_pending_flow"
    ) as mock_delete:
        await handle_confirm(
            upd,
            MagicMock(),
            {"id": 1, "sheet_columns": ["Imię i nazwisko", "Miasto", "Adres", "Produkt", "Status"]},
            {},
            "",
        )

    mock_update.assert_not_awaited()
    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_type is PendingFlowType.ADD_CLIENT
    assert saved_flow.flow_data["client_data"]["Imię i nazwisko"] == "Krzysztof Krzysztofiński"
    assert saved_flow.flow_data["client_data"]["Miasto"] == "Marki"
    assert saved_flow.flow_data["client_data"]["Status"] == "Spotkanie umówione"
    mock_delete.assert_not_called()


@pytest.mark.asyncio
async def test_add_meeting_confirm_update_client_fails_reports_failure():
    flow_data = {
        "title": "Spotkanie - Jurek Jurecki",
        "start": "2026-04-17T11:00:00+02:00",
        "end": "2026-04-17T12:00:00+02:00",
        "client_name": "Jurek Jurecki",
        "location": "Warszawa",
        "description": "",
        "event_type": "in_person",
    }
    upd = _update()

    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value={"flow_type": "add_meeting", "flow_data": flow_data},
    ), patch(
        "bot.handlers.text.create_event",
        new=AsyncMock(return_value={"id": "event-1"}),
    ), patch(
        "bot.handlers.text.search_clients",
        new=AsyncMock(return_value=[
            {"_row": 7, "Imię i nazwisko": "Jurek Jurecki", "Status": "Nowy lead"}
        ]),
    ), patch(
        "bot.handlers.text.update_client",
        new=AsyncMock(return_value=False),
    ), patch("bot.handlers.text.delete_pending_flow"):
        await handle_confirm(upd, MagicMock(), {"id": 1}, {}, "")

    upd.effective_message.reply_text.assert_awaited_once_with(
        "✅ Spotkanie dodane do kalendarza. Nie udało się zaktualizować arkusza."
    )


@pytest.mark.asyncio
async def test_add_meetings_confirm_passes_event_type_to_calendar():
    flow_data = {
        "meetings": [
            {
                "title": "Telefon — Anna Nowak",
                "start": "2026-04-17T11:00:00+02:00",
                "end": "2026-04-17T11:30:00+02:00",
                "client_name": "Anna Nowak",
                "event_type": "phone_call",
            },
            {
                "title": "Spotkanie — Jan Kowalski",
                "start": "2026-04-18T12:00:00+02:00",
                "end": "2026-04-18T13:00:00+02:00",
                "client_name": "Jan Kowalski",
            },
        ]
    }
    upd = _update()

    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value={"flow_type": "add_meetings", "flow_data": flow_data},
    ), patch(
        "bot.handlers.text.create_event",
        new=AsyncMock(side_effect=[{"id": "event-1"}, {"id": "event-2"}]),
    ) as mock_create, patch(
        "bot.handlers.text.search_clients",
        new=AsyncMock(return_value=[{"_row": 7, "Imię i nazwisko": "Anna Nowak"}]),
    ), patch("bot.handlers.text.delete_pending_flow"):
        await handle_confirm(upd, MagicMock(), {"id": 1}, {}, "")

    assert mock_create.await_args_list[0].kwargs["event_type"] == "phone_call"
    assert mock_create.await_args_list[1].kwargs["event_type"] is None
