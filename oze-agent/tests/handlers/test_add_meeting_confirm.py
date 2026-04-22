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
        "shared.mutations.add_meeting.create_event",
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
        "shared.mutations.add_meeting.create_event",
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
    # Slice 5.1d: pre-resolved by _enrich_meeting, propagated via payload.
    flow_data = {
        "title": "Spotkanie - Jurek Jurecki",
        "start": "2026-04-17T11:00:00+02:00",
        "end": "2026-04-17T12:00:00+02:00",
        "client_name": "Jurek Jurecki",
        "location": "Warszawa",
        "description": "",
        "event_type": "in_person",
        "client_row": 7,
        "current_status": "Nowy lead",
        "ambiguous_client": False,
    }
    upd = _update()

    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value={"flow_type": "add_meeting", "flow_data": flow_data},
    ), patch(
        "shared.mutations.add_meeting.create_event",
        new=AsyncMock(return_value={"id": "event-1"}),
    ), patch(
        "shared.mutations.add_meeting.update_client_row_touching_contact",
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
        "client_row": 7,
        "current_status": "Oferta wysłana",
        "ambiguous_client": False,
    }
    upd = _update()

    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value={"flow_type": "add_meeting", "flow_data": flow_data},
    ), patch(
        "shared.mutations.add_meeting.create_event",
        new=AsyncMock(return_value={"id": "event-1"}),
    ), patch(
        "shared.mutations.add_meeting.update_client_row_touching_contact",
        new=AsyncMock(return_value=True),
    ) as mock_update, patch("bot.handlers.text.delete_pending_flow"):
        await handle_confirm(upd, MagicMock(), {"id": 1}, {}, "")

    mock_update.assert_awaited_once_with(
        1,
        7,
        {
            "Następny krok": "Spotkanie",
            "Data następnego kroku": "2026-04-17T11:00:00+02:00",
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
        "client_row": 7,
        "current_status": "Nowy lead",
        "ambiguous_client": False,
    }
    upd = _update()

    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value={"flow_type": "add_meeting", "flow_data": flow_data},
    ), patch(
        "shared.mutations.add_meeting.create_event",
        new=AsyncMock(return_value={"id": "event-1"}),
    ) as mock_create, patch(
        "shared.mutations.add_meeting.update_client_row_touching_contact",
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
            "ID wydarzenia Kalendarz": "event-1",
        },
    )
    upd.effective_message.reply_text.assert_awaited_once_with("✅ Spotkanie dodane do kalendarza.")


@pytest.mark.asyncio
async def test_add_meeting_confirm_applies_compound_status_update():
    flow_data = {
        "title": "Telefon - Jurek Jurecki",
        "start": "2026-04-17T11:00:00+02:00",
        "end": "2026-04-17T12:00:00+02:00",
        "client_name": "Jurek Jurecki",
        "location": "telefonicznie",
        "description": "",
        "event_type": "phone_call",
        "status_update": {
            "row": 7,
            "field": "Status",
            "old_value": "Oferta wysłana",
            "new_value": "Podpisane",
            "client_name": "Jurek Jurecki",
            "city": "Warszawa",
        },
    }
    upd = _update()

    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value={"flow_type": "add_meeting", "flow_data": flow_data},
    ), patch(
        "shared.mutations.add_meeting.create_event",
        new=AsyncMock(return_value={"id": "event-1"}),
    ), patch(
        "bot.handlers.text.search_clients",
        new=AsyncMock(return_value=[
            {"_row": 7, "Imię i nazwisko": "Jurek Jurecki", "Status": "Oferta wysłana"}
        ]),
    ), patch(
        "shared.mutations.add_meeting.update_client_row_touching_contact",
        new=AsyncMock(return_value=True),
    ) as mock_update, patch("bot.handlers.text.delete_pending_flow"):
        await handle_confirm(upd, MagicMock(), {"id": 1}, {}, "")

    mock_update.assert_awaited_once_with(
        1,
        7,
        {
            "Następny krok": "Telefon",
            "Data następnego kroku": "2026-04-17T11:00:00+02:00",
            "ID wydarzenia Kalendarz": "event-1",
            "Status": "Podpisane",
        },
    )
    upd.effective_message.reply_text.assert_awaited_once_with(
        "✅ Spotkanie dodane do kalendarza. Status klienta: Podpisane."
    )


@pytest.mark.asyncio
async def test_add_meeting_confirm_syncs_to_enriched_client_row():
    """Slice 5.1d: handle_confirm uses pre-resolved client_row from flow_data
    (no second search_clients lookup). Row/current_status are propagated by
    _enrich_meeting at the preview stage."""
    flow_data = {
        "title": "Spotkanie - Jurek Jurecki",
        "start": "2026-04-17T11:00:00+02:00",
        "end": "2026-04-17T12:00:00+02:00",
        "client_name": "Jurek Jurecki",
        "location": "Warszawa",
        "description": "",
        "event_type": "in_person",
        "client_row": 7,
        "current_status": "Nowy lead",
        "ambiguous_client": False,
    }
    upd = _update()

    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value={"flow_type": "add_meeting", "flow_data": flow_data},
    ), patch(
        "shared.mutations.add_meeting.create_event",
        new=AsyncMock(return_value={"id": "event-1"}),
    ), patch(
        "shared.mutations.add_meeting.update_client_row_touching_contact",
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
        "shared.mutations.add_meeting.create_event",
        new=AsyncMock(return_value={"id": "event-1"}),
    ), patch(
        "bot.handlers.text.search_clients",
        new=AsyncMock(return_value=[
            {"_row": 3, "Imię i nazwisko": "Zbigniew Jurecki", "Status": "Nowy lead"},
            {"_row": 9, "Imię i nazwisko": "Anna Jurecka", "Status": "Nowy lead"},
        ]),
    ), patch(
        "shared.mutations.add_meeting.update_client_row_touching_contact",
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
        "shared.mutations.add_meeting.create_event",
        new=AsyncMock(return_value={"id": "event-1"}),
    ), patch(
        "bot.handlers.text.search_clients",
        new=AsyncMock(return_value=[
            {"_row": 33, "Imię i nazwisko": "Krzysztof Wojcik", "Status": "Nowy lead"}
        ]),
    ), patch(
        "shared.mutations.add_meeting.update_client_row_touching_contact",
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
        "client_row": 7,
        "current_status": "Nowy lead",
        "ambiguous_client": False,
    }
    upd = _update()

    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value={"flow_type": "add_meeting", "flow_data": flow_data},
    ), patch(
        "shared.mutations.add_meeting.create_event",
        new=AsyncMock(return_value={"id": "event-1"}),
    ), patch(
        "shared.mutations.add_meeting.update_client_row_touching_contact",
        new=AsyncMock(return_value=False),
    ), patch("bot.handlers.text.delete_pending_flow"):
        await handle_confirm(upd, MagicMock(), {"id": 1}, {}, "")

    upd.effective_message.reply_text.assert_awaited_once_with(
        "✅ Spotkanie dodane do kalendarza. Nie udało się zaktualizować arkusza."
    )


@pytest.mark.asyncio
async def test_add_meeting_confirm_calendar_fail_uses_calendar_down_error_key():
    """Slice 5.4: Calendar create failure → format_error("calendar_down"),
    NO Sheets write attempted."""
    flow_data = {
        "title": "Spotkanie - Jurek",
        "start": "2027-04-17T11:00:00+02:00",
        "end": "2027-04-17T12:00:00+02:00",
        "client_name": "Jurek",
        "location": "",
        "description": "",
        "event_type": "in_person",
        "client_row": 7,
        "current_status": "Nowy lead",
        "ambiguous_client": False,
    }
    upd = _update()
    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value={"flow_type": "add_meeting", "flow_data": flow_data},
    ), patch(
        "shared.mutations.add_meeting.create_event",
        new=AsyncMock(return_value=None),
    ), patch(
        "shared.mutations.add_meeting.update_client_row_touching_contact",
        new=AsyncMock(return_value=True),
    ) as mock_sheets, patch(
        "bot.handlers.text.format_error",
        return_value="ESCAPED_CALENDAR_DOWN",
    ) as mock_err, patch("bot.handlers.text.delete_pending_flow"):
        await handle_confirm(upd, MagicMock(), {"id": 1}, {}, "")

    mock_err.assert_called_once_with("calendar_down")
    upd.effective_message.reply_markdown_v2.assert_awaited_once_with("ESCAPED_CALENDAR_DOWN")
    upd.effective_message.reply_text.assert_not_called()
    mock_sheets.assert_not_awaited()


@pytest.mark.asyncio
async def test_add_meeting_confirm_forwards_flow_data_to_pipeline():
    """Regression guard: handler passes flow_data fields to commit_add_meeting
    including today as a keyword arg + the compound status_update dict."""
    from datetime import date, datetime
    flow_data = {
        "title": "Spotkanie - X",
        "start": "2027-05-10T14:00:00+02:00",
        "end": "2027-05-10T15:00:00+02:00",
        "client_name": "X",
        "location": "ul. Testowa 1",
        "description": "desc",
        "event_type": "phone_call",
        "client_row": 11,
        "current_status": "Oferta wysłana",
        "ambiguous_client": False,
    }
    upd = _update()
    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value={"flow_type": "add_meeting", "flow_data": flow_data},
    ), patch(
        "bot.handlers.text.commit_add_meeting",
        new=AsyncMock(return_value=MagicMock(
            success=True, error_message=None, calendar_event_id="ev-1",
            sheets_attempted=True, sheets_synced=True, sheets_error=None,
            status_updated=False, status_new_value=None,
        )),
    ) as mock_pipeline, patch("bot.handlers.text.delete_pending_flow"):
        await handle_confirm(upd, MagicMock(), {"id": "u1"}, {}, "")

    mock_pipeline.assert_awaited_once()
    args = mock_pipeline.await_args.args
    kwargs = mock_pipeline.await_args.kwargs
    assert args[0] == "u1"                                    # user_id
    # Slice 5.4.1c: flow_data title "Spotkanie - X" + event_type=phone_call
    # matches the legacy-ASCII-dash override pattern → rewritten with em-dash
    # and the correct label for phone_call.
    assert kwargs["title"] == "Telefon — X"
    assert isinstance(kwargs["start"], datetime)
    assert kwargs["start"].isoformat() == "2027-05-10T14:00:00+02:00"
    assert kwargs["event_type"] == "phone_call"
    assert kwargs["location"] == "ul. Testowa 1"
    assert kwargs["client_row"] == 11
    assert kwargs["today"] == date.today()
    assert kwargs["client_current_status"] == "Oferta wysłana"
    assert kwargs["status_update"] is None


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


# ── Slice 5.4.1 — Calendar title per event_type ──────────────────────────────


def _title_override_flow(*, title: str, event_type: str, client_name: str) -> dict:
    return {
        "title": title,
        "start": "2027-05-10T14:00:00+02:00",
        "end": "2027-05-10T15:00:00+02:00",
        "client_name": client_name,
        "location": "",
        "description": "",
        "event_type": event_type,
        "client_row": 11,
        "current_status": "Oferta wysłana",
        "ambiguous_client": False,
    }


def _mock_pipeline_ok() -> AsyncMock:
    return AsyncMock(return_value=MagicMock(
        success=True, error_message=None, calendar_event_id="ev-1",
        sheets_attempted=True, sheets_synced=True, sheets_error=None,
        status_updated=False, status_new_value=None,
    ))


async def _confirm_and_return_title(flow_data: dict) -> str:
    upd = _update()
    pipeline = _mock_pipeline_ok()
    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value={"flow_type": "add_meeting", "flow_data": flow_data},
    ), patch(
        "bot.handlers.text.commit_add_meeting",
        new=pipeline,
    ), patch("bot.handlers.text.delete_pending_flow"):
        await handle_confirm(upd, MagicMock(), {"id": "u1"}, {}, "")
    return pipeline.await_args.kwargs["title"]


@pytest.mark.asyncio
async def test_add_meeting_confirm_passes_event_type_aware_title_unchanged():
    """New pendings (post-5.4.1) already carry an event_type-aware title;
    override is a no-op because `Telefon — X` is a valid generic+name shape
    and matches correct_label for phone_call."""
    title = await _confirm_and_return_title(
        _title_override_flow(title="Telefon — Zbigniew Nowak", event_type="phone_call", client_name="Zbigniew Nowak")
    )
    assert title == "Telefon — Zbigniew Nowak"


@pytest.mark.asyncio
async def test_add_meeting_confirm_legacy_bare_label_override():
    """Legacy pending with bare title="Spotkanie" + event_type=phone_call
    → override to "Telefon — X"."""
    title = await _confirm_and_return_title(
        _title_override_flow(title="Spotkanie", event_type="phone_call", client_name="Zbigniew Nowak")
    )
    assert title == "Telefon — Zbigniew Nowak"


@pytest.mark.asyncio
async def test_add_meeting_confirm_legacy_label_with_name_override():
    """Legacy pending with title="Spotkanie — Jan" + event_type=phone_call
    → override to "Telefon — Jan" (pattern match on stale generic prefix)."""
    title = await _confirm_and_return_title(
        _title_override_flow(title="Spotkanie — Jan", event_type="phone_call", client_name="Jan")
    )
    assert title == "Telefon — Jan"


@pytest.mark.asyncio
async def test_add_meeting_confirm_custom_title_not_overridden():
    """A user-supplied custom title is preserved verbatim even when it starts
    with a generic label — the full string is not one of the overridable shapes."""
    custom = "Spotkanie podpisujące umowę z architektem Markowskim"
    title = await _confirm_and_return_title(
        _title_override_flow(title=custom, event_type="in_person", client_name="Markowski")
    )
    assert title == custom


@pytest.mark.asyncio
async def test_add_meeting_confirm_wrong_label_with_name_override():
    """Legacy pending with title="Telefon — Anna" but event_type flipped to
    in_person (stale title from a previous extraction) → override to
    "Spotkanie — Anna" on the basis of the current event_type."""
    title = await _confirm_and_return_title(
        _title_override_flow(title="Telefon — Anna", event_type="in_person", client_name="Anna")
    )
    assert title == "Spotkanie — Anna"


@pytest.mark.asyncio
async def test_add_meeting_confirm_legacy_ascii_dash_override():
    """Slice 5.4.1c: legacy pending with ASCII dash ("Spotkanie - Jan") also
    enters the override — pre-5.4.1 flows and several test fixtures in this
    repo use a plain hyphen instead of em-dash. Output still uses em-dash."""
    title = await _confirm_and_return_title(
        _title_override_flow(title="Spotkanie - Jan", event_type="phone_call", client_name="Jan")
    )
    assert title == "Telefon — Jan"
