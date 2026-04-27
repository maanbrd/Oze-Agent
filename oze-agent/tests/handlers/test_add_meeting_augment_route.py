"""Routing tests for add_meeting replies after tapping Dopisać."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.handlers.text import _route_pending_flow, handle_add_meeting
from shared.pending import PendingFlowType


_MISSING = object()


def _flow(description: str = "", event_type: str | None = None) -> dict:
    flow_data = {
        "title": "Spotkanie — Anna Testowa",
        "start": "2027-04-17T14:00:00+02:00",
        "end": "2027-04-17T15:00:00+02:00",
        "client_name": "Anna Testowa",
        "location": "Zatory",
        "description": description,
        "client_data": {
            "Imię i nazwisko": "Anna Testowa",
            "Miasto": "Zatory",
        },
    }
    if event_type is not None:
        flow_data["event_type"] = event_type
    return {
        "flow_type": "add_meeting",
        "flow_data": flow_data,
    }


def _empty_meeting_flow(description: str = "") -> dict:
    return {
        "flow_type": "add_meeting",
        "flow_data": {
            "title": "Spotkanie",
            "start": "2027-04-17T14:00:00+02:00",
            "end": "2027-04-17T15:00:00+02:00",
            "client_name": "",
            "location": "",
            "description": description,
        },
    }


def _update(telegram_id: int = 123) -> MagicMock:
    upd = MagicMock()
    upd.effective_user.id = telegram_id
    upd.effective_message.reply_text = AsyncMock()
    upd.effective_message.reply_markdown_v2 = AsyncMock()
    return upd


def _duration_minutes(flow_data: dict) -> int:
    start = datetime.fromisoformat(flow_data["start"])
    end = datetime.fromisoformat(flow_data["end"])
    return int((end - start).total_seconds() // 60)


async def _single_meeting_flow_for_duration(
    event_type: str,
    duration_minutes: int | object = _MISSING,
) -> dict:
    upd = _update()
    meeting = {
        "date": "2027-04-20",
        "time": "14:00",
        "client_name": "Jan Kowalski",
        "location": "",
    }
    if duration_minutes is not _MISSING:
        meeting["duration_minutes"] = duration_minutes

    with patch(
        "bot.handlers.text.extract_meeting_data",
        new=AsyncMock(return_value={"meetings": [meeting]}),
    ), patch(
        "bot.handlers.text._enrich_meeting",
        new=AsyncMock(return_value={
            "title": "Spotkanie — Jan Kowalski",
            "location": "",
            "description": "",
            "full_name": "Jan Kowalski",
            "client_found": True,
            "client_row": 5,
            "current_status": "Oferta wysłana",
            "client_city": "Warszawa",
        }),
    ), patch("bot.handlers.text.check_conflicts", new=AsyncMock(return_value=[])), \
         patch("bot.handlers.text.save_pending") as mock_save:
        await handle_add_meeting(
            upd,
            MagicMock(),
            {"id": 1, "default_meeting_duration": 60},
            {"entities": {"event_type": event_type}},
            "w poniedziałek o 14 z Kowalskim",
        )

    return mock_save.call_args.args[0].flow_data


@pytest.mark.asyncio
async def test_add_meeting_augment_product_details_go_to_client_data_not_description():
    upd = _update()
    with patch("bot.handlers.text.save_pending") as mock_save:
        consumed = await _route_pending_flow(
            upd,
            MagicMock(),
            {"id": 1},
            _flow(),
            "Zużycie 4500kw, magazyn 10kw",
        )

    assert consumed is True
    mock_save.assert_called_once()
    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_type is PendingFlowType.ADD_MEETING
    assert saved_flow.flow_data["description"] == ""
    assert saved_flow.flow_data["client_data"]["Produkt"] == "Magazyn energii"
    assert saved_flow.flow_data["client_data"]["Notatki"] == "Zużycie 4500kw, magazyn 10kw"
    upd.effective_message.reply_markdown_v2.assert_awaited_once()
    assert "Anna Testowa" in upd.effective_message.reply_markdown_v2.call_args.args[0]
    assert "Dane klienta do zapisu" in upd.effective_message.reply_markdown_v2.call_args.args[0]


@pytest.mark.asyncio
async def test_handle_add_meeting_extracts_client_data_from_same_message():
    upd = _update()
    message = (
        "Zapisz spotkanie na jutro o 14 z Markiem Markowym, który mieszka "
        "w miejscowości Marki na ulicy Markowej 25. Numer telefonu 736-326-756. "
        "Jest zainteresowany fotowoltaiką i magazynem energii."
    )
    with patch(
        "bot.handlers.text.extract_meeting_data",
        new=AsyncMock(return_value={
            "meetings": [{
                "date": "2027-04-20",
                "time": "14:00",
                "client_name": "Marek Markowy",
                "location": "Marki, ul. Markowa 25",
                "event_type": "in_person",
            }]
        }),
    ), patch(
        "bot.handlers.text.extract_client_data",
        new=AsyncMock(return_value={"client_data": {}}),
    ) as mock_extract_client, patch(
        "bot.handlers.text._enrich_meeting",
        new=AsyncMock(return_value={
            "title": "Spotkanie — Marek Markowy",
            "location": "Marki, ul. Markowa 25",
            "description": "",
            "full_name": "Marek Markowy",
            "client_found": False,
            "client_row": None,
            "current_status": "",
            "client_city": "",
            "ambiguous_client": False,
            "ambiguous_candidates": [],
        }),
    ), patch("bot.handlers.text.check_conflicts", new=AsyncMock(return_value=[])), \
         patch("bot.handlers.text.save_pending") as mock_save:
        await handle_add_meeting(
            upd,
            MagicMock(),
            {
                "id": 1,
                "default_meeting_duration": 60,
                "sheet_columns": ["Imię i nazwisko", "Miasto", "Adres", "Telefon", "Produkt"],
            },
            {"entities": {"event_type": "in_person"}},
            message,
        )

    mock_extract_client.assert_awaited_once()
    saved_flow = mock_save.call_args.args[0]
    client_data = saved_flow.flow_data["client_data"]
    assert client_data["Imię i nazwisko"] == "Marek Markowy"
    assert client_data["Telefon"] == "736326756"
    assert client_data["Miasto"] == "Marki"
    assert client_data["Adres"] == "ul. Markowa 25"
    assert client_data["Produkt"] == "PV + Magazyn energii"
    card = upd.effective_message.reply_markdown_v2.call_args.args[0]
    assert "Dane klienta do zapisu" in card
    assert "736326756" in card
    assert "PV \\+ Magazyn energii" in card


@pytest.mark.asyncio
async def test_handle_add_meeting_existing_client_updates_only_empty_fields():
    upd = _update()
    with patch(
        "bot.handlers.text.extract_meeting_data",
        new=AsyncMock(return_value={
            "meetings": [{
                "date": "2027-04-20",
                "time": "14:00",
                "client_name": "Marek Markowy",
                "location": "",
                "event_type": "in_person",
            }]
        }),
    ), patch(
        "bot.handlers.text.extract_client_data",
        new=AsyncMock(return_value={
            "client_data": {
                "Telefon": "736326756",
                "Produkt": "PV + Magazyn energii",
                "Adres": "ul. Markowa 25",
            }
        }),
    ), patch(
        "bot.handlers.text._enrich_meeting",
        new=AsyncMock(return_value={
            "title": "Spotkanie — Marek Markowy",
            "location": "Marki",
            "description": "",
            "full_name": "Marek Markowy",
            "client_found": True,
            "client_row": 7,
            "current_status": "Oferta wysłana",
            "client_city": "Marki",
            "existing_client_data": {
                "_row": 7,
                "Imię i nazwisko": "Marek Markowy",
                "Telefon": "",
                "Produkt": "PV",
                "Adres": "",
                "Miasto": "Marki",
            },
            "ambiguous_client": False,
            "ambiguous_candidates": [],
        }),
    ), patch("bot.handlers.text.check_conflicts", new=AsyncMock(return_value=[])), \
         patch("bot.handlers.text.save_pending") as mock_save:
        await handle_add_meeting(
            upd,
            MagicMock(),
            {
                "id": 1,
                "default_meeting_duration": 60,
                "sheet_columns": ["Imię i nazwisko", "Telefon", "Miasto", "Adres", "Produkt"],
            },
            {"entities": {"event_type": "in_person"}},
            "Spotkanie z Markiem jutro o 14, telefon 736326756, ul. Markowa 25, fotowoltaika i magazyn",
        )

    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_data["client_updates"] == {
        "Telefon": "736326756",
        "Adres": "ul. Markowa 25",
    }


@pytest.mark.asyncio
async def test_add_meeting_augment_preserves_existing_description():
    upd = _update()
    with patch("bot.handlers.text.save_pending") as mock_save:
        consumed = await _route_pending_flow(
            upd,
            MagicMock(),
            {"id": 1},
            _flow("Tel: 123456789"),
            "parking pod bramą",
        )

    assert consumed is True
    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_data["description"] == (
        "Tel: 123456789\nparking pod bramą"
    )


@pytest.mark.asyncio
async def test_add_meeting_augment_preserves_event_type():
    upd = _update()
    with patch("bot.handlers.text.save_pending") as mock_save:
        consumed = await _route_pending_flow(
            upd,
            MagicMock(),
            {"id": 1},
            _flow(event_type="in_person"),
            "parking pod bramą",
        )

    assert consumed is True
    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_data["event_type"] == "in_person"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "message_text",
    [
        "Zadzwoń do Tomasza Nowickiego jutro o 12",
        "dodaj notatkę do Jana Kowalskiego: oddzwonił",
        "pokaż plan na jutro",
    ],
)
async def test_add_meeting_pending_intent_switch_auto_cancels(message_text):
    upd = _update()
    with patch("bot.handlers.text.delete_pending_flow") as mock_delete, \
         patch("bot.handlers.text.save_pending") as mock_save:
        consumed = await _route_pending_flow(
            upd,
            MagicMock(),
            {"id": 1},
            _flow(),
            message_text,
        )

    assert consumed is False
    mock_delete.assert_called_once_with(123)
    mock_save.assert_not_called()
    upd.effective_message.reply_text.assert_awaited_once_with("⚠️ Anulowane.")


@pytest.mark.asyncio
async def test_add_meeting_pending_phone_fact_stays_augment():
    upd = _update()
    with patch("bot.handlers.text.delete_pending_flow") as mock_delete, \
         patch("bot.handlers.text.save_pending") as mock_save:
        consumed = await _route_pending_flow(
            upd,
            MagicMock(),
            {"id": 1},
            _flow(),
            "tel 600123456",
        )

    assert consumed is True
    mock_delete.assert_not_called()
    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_data["client_data"]["Telefon"] == "600123456"


@pytest.mark.asyncio
async def test_add_meeting_augment_empty_meeting_accepts_full_client_data():
    upd = _update()
    extracted = {
        "client_data": {
            "Imię i nazwisko": "Andrzej Andrzejowski",
            "Miasto": "Strzeszew",
            "Adres": "ul. Paderewskiego 14/2",
            "Telefon": "449558338",
            "Produkt": "PV + Magazyn energii",
        }
    }
    with patch("bot.handlers.text.get_sheet_headers", new=AsyncMock(return_value=[
        "Imię i nazwisko", "Miasto", "Adres", "Telefon", "Produkt", "Notatki",
    ])), patch(
        "bot.handlers.text.extract_client_data",
        new=AsyncMock(return_value=extracted),
    ) as mock_extract, patch(
        "bot.handlers.text._enrich_meeting",
        new=AsyncMock(return_value={
            "title": "Spotkanie — Andrzej Andrzejowski",
            "location": "ul. Paderewskiego 14/2, Strzeszew",
            "description": "",
            "full_name": "Andrzej Andrzejowski",
            "client_found": False,
        }),
    ) as mock_enrich, patch("bot.handlers.text.save_pending") as mock_save:
        consumed = await _route_pending_flow(
            upd,
            MagicMock(),
            {"id": 1},
            _empty_meeting_flow(),
            "Andrzej Andrzejowski, Strzeszew, ul. Paderewskiego 14/2, telefon 449558338, zainteresowany pv i magazynem",
        )

    assert consumed is True
    mock_extract.assert_awaited_once()
    mock_enrich.assert_awaited_once_with(
        1,
        "Andrzej Andrzejowski",
        "ul. Paderewskiego 14/2, Strzeszew",
        event_type=None,
    )
    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_type is PendingFlowType.ADD_MEETING
    assert saved_flow.flow_data["title"] == "Spotkanie — Andrzej Andrzejowski"
    assert saved_flow.flow_data["client_name"] == "Andrzej Andrzejowski"
    assert saved_flow.flow_data["location"] == "ul. Paderewskiego 14/2, Strzeszew"
    assert saved_flow.flow_data["description"] == ""
    assert saved_flow.flow_data["client_data"]["Telefon"] == "449558338"
    assert saved_flow.flow_data["client_data"]["Produkt"] == "PV + Magazyn energii"


@pytest.mark.asyncio
async def test_add_meeting_augment_empty_meeting_plain_description_stays_description():
    upd = _update()
    with patch("bot.handlers.text.get_sheet_headers", new=AsyncMock(return_value=[
        "Imię i nazwisko", "Miasto", "Adres", "Telefon", "Produkt", "Notatki",
    ])), patch(
        "bot.handlers.text.extract_client_data",
        new=AsyncMock(return_value={"client_data": {}}),
    ), patch("bot.handlers.text.save_pending") as mock_save:
        consumed = await _route_pending_flow(
            upd,
            MagicMock(),
            {"id": 1},
            _empty_meeting_flow(),
            "parking pod bramą",
        )

    assert consumed is True
    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_type is PendingFlowType.ADD_MEETING
    assert saved_flow.flow_data["title"] == "Spotkanie"
    assert saved_flow.flow_data["client_name"] == ""
    assert saved_flow.flow_data["description"] == "parking pod bramą"
    assert "client_data" not in saved_flow.flow_data


@pytest.mark.asyncio
async def test_add_meeting_augment_empty_meeting_name_only_stays_description():
    upd = _update()
    with patch("bot.handlers.text.get_sheet_headers", new=AsyncMock(return_value=[
        "Imię i nazwisko", "Miasto", "Adres", "Telefon", "Produkt", "Notatki",
    ])), patch(
        "bot.handlers.text.extract_client_data",
        new=AsyncMock(return_value={"client_data": {"Imię i nazwisko": "Jan Kowalski"}}),
    ), patch(
        "bot.handlers.text._enrich_meeting",
        new=AsyncMock(side_effect=AssertionError("_enrich_meeting must not be called for name-only input")),
    ), patch("bot.handlers.text.save_pending") as mock_save:
        consumed = await _route_pending_flow(
            upd,
            MagicMock(),
            {"id": 1},
            _empty_meeting_flow(),
            "Jan Kowalski",
        )

    assert consumed is True
    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_type is PendingFlowType.ADD_MEETING
    assert saved_flow.flow_data["title"] == "Spotkanie"
    assert saved_flow.flow_data["client_name"] == ""
    assert (saved_flow.flow_data.get("client_data") or {}).get("Imię i nazwisko", "") != "Jan Kowalski"


@pytest.mark.asyncio
async def test_add_meeting_augment_empty_meeting_product_only_stays_description():
    upd = _update()
    with patch("bot.handlers.text.get_sheet_headers", new=AsyncMock(return_value=[
        "Imię i nazwisko", "Miasto", "Adres", "Telefon", "Produkt", "Notatki",
    ])), patch(
        "bot.handlers.text.extract_client_data",
        new=AsyncMock(return_value={"client_data": {"Produkt": "PV", "Notatki": "zainteresowany"}}),
    ), patch(
        "bot.handlers.text._enrich_meeting",
        new=AsyncMock(side_effect=AssertionError("_enrich_meeting must not be called for product-only input")),
    ), patch("bot.handlers.text.save_pending") as mock_save:
        consumed = await _route_pending_flow(
            upd,
            MagicMock(),
            {"id": 1},
            _empty_meeting_flow(),
            "zainteresowany PV",
        )

    assert consumed is True
    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_type is PendingFlowType.ADD_MEETING
    assert saved_flow.flow_data["title"] == "Spotkanie"
    assert saved_flow.flow_data["client_name"] == ""
    assert "Imię i nazwisko" not in saved_flow.flow_data.get("client_data", {})


@pytest.mark.asyncio
async def test_handle_add_meeting_preserves_router_event_type():
    upd = _update()
    with patch(
        "bot.handlers.text.extract_meeting_data",
        new=AsyncMock(return_value={
            "meetings": [{
                "date": "2027-04-20",
                "time": "14:00",
                "client_name": "Anna Testowa",
                "location": "Zatory",
            }]
        }),
    ), patch(
        "bot.handlers.text._enrich_meeting",
        new=AsyncMock(return_value={
            "title": "Spotkanie — Anna Testowa",
            "location": "Zatory",
            "description": "",
            "full_name": "Anna Testowa",
            "client_found": True,
        }),
    ), patch("bot.handlers.text.check_conflicts", new=AsyncMock(return_value=[])), \
         patch("bot.handlers.text.save_pending") as mock_save:
        await handle_add_meeting(
            upd,
            MagicMock(),
            {"id": 1, "default_meeting_duration": 60},
            {"entities": {"event_type": "in_person"}},
            "spotkanie z Anną w poniedziałek o 14",
        )

    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_type is PendingFlowType.ADD_MEETING
    assert saved_flow.flow_data["event_type"] == "in_person"


@pytest.mark.asyncio
async def test_add_meeting_phone_call_default_15_min():
    flow_data = await _single_meeting_flow_for_duration("phone_call")

    assert _duration_minutes(flow_data) == 15


@pytest.mark.asyncio
async def test_add_meeting_offer_email_default_15_min():
    flow_data = await _single_meeting_flow_for_duration("offer_email")

    assert _duration_minutes(flow_data) == 15


@pytest.mark.asyncio
async def test_add_meeting_doc_followup_default_15_min():
    flow_data = await _single_meeting_flow_for_duration("doc_followup")

    assert _duration_minutes(flow_data) == 15


@pytest.mark.asyncio
async def test_add_meeting_in_person_default_60_min():
    flow_data = await _single_meeting_flow_for_duration("in_person")

    assert _duration_minutes(flow_data) == 60


@pytest.mark.asyncio
async def test_add_meeting_explicit_duration_wins_over_default():
    flow_data = await _single_meeting_flow_for_duration("phone_call", duration_minutes=30)

    assert _duration_minutes(flow_data) == 30


@pytest.mark.asyncio
async def test_add_meeting_explicit_zero_duration_preserved():
    flow_data = await _single_meeting_flow_for_duration("offer_email", duration_minutes=0)

    assert _duration_minutes(flow_data) == 0


@pytest.mark.asyncio
async def test_add_meeting_text_event_type_overrides_wrong_router_in_person_for_phone_call():
    upd = _update()
    with patch(
        "bot.handlers.text.extract_meeting_data",
        new=AsyncMock(return_value={
            "meetings": [{
                "date": "2027-04-20",
                "time": "12:00",
                "client_name": "Tomasz Nowicki",
                "location": "telefonicznie",
            }]
        }),
    ), patch(
        "bot.handlers.text._enrich_meeting",
        new=AsyncMock(return_value={
            "title": "Spotkanie — Tomasz Nowicki",
            "location": "telefonicznie",
            "description": "",
            "full_name": "Tomasz Nowicki",
            "client_found": True,
            "current_status": "Oferta wysłana",
        }),
    ), patch("bot.handlers.text.check_conflicts", new=AsyncMock(return_value=[])), \
         patch("bot.handlers.text.save_pending") as mock_save:
        await handle_add_meeting(
            upd,
            MagicMock(),
            {"id": 1, "default_meeting_duration": 60},
            {"entities": {"event_type": "in_person"}},
            "Zadzwoń do Tomasza Nowickiego w sobotę o 12",
        )

    flow_data = mock_save.call_args.args[0].flow_data
    assert flow_data["event_type"] == "phone_call"
    assert _duration_minutes(flow_data) == 15


@pytest.mark.asyncio
async def test_add_meeting_text_event_type_overrides_wrong_router_in_person_for_offer_email():
    upd = _update()
    with patch(
        "bot.handlers.text.extract_meeting_data",
        new=AsyncMock(return_value={
            "meetings": [{
                "date": "2027-04-20",
                "time": "23:00",
                "client_name": "Jan Kowalski",
                "location": "",
            }]
        }),
    ), patch(
        "bot.handlers.text._enrich_meeting",
        new=AsyncMock(return_value={
            "title": "Spotkanie — Jan Kowalski",
            "location": "",
            "description": "",
            "full_name": "Jan Kowalski",
            "client_found": True,
            "current_status": "Oferta wysłana",
        }),
    ), patch("bot.handlers.text.check_conflicts", new=AsyncMock(return_value=[])), \
         patch("bot.handlers.text.save_pending") as mock_save:
        await handle_add_meeting(
            upd,
            MagicMock(),
            {"id": 1, "default_meeting_duration": 60},
            {"entities": {"event_type": "in_person"}},
            "Wyślij ofertę Janowi Kowalskiemu dzisiaj o godzinie 23",
        )

    flow_data = mock_save.call_args.args[0].flow_data
    assert flow_data["event_type"] == "offer_email"
    assert _duration_minutes(flow_data) == 15


@pytest.mark.asyncio
async def test_add_meetings_batch_mixed_event_types_preserve_durations_and_event_types():
    upd = _update()
    meetings = [
        {
            "date": "2027-04-20",
            "time": "10:00",
            "client_name": "Jan Kowalski",
            "location": "Warszawa",
            "event_type": "in_person",
        },
        {
            "date": "2027-04-20",
            "time": "12:00",
            "client_name": "Anna Testowa",
            "location": "",
            "event_type": "phone_call",
        },
        {
            "date": "2027-04-20",
            "time": "15:00",
            "client_name": "Adam Ofertowy",
            "location": "",
            "event_type": "offer_email",
        },
    ]

    _EVENT_TYPE_LABEL = {
        "in_person": "Spotkanie",
        "phone_call": "Telefon",
        "offer_email": "Wysłać ofertę",
        "doc_followup": "Follow-up dokumentowy",
    }

    def enrich_side_effect(_user_id: int, client_name: str, location: str, *, event_type=None) -> dict:
        label = _EVENT_TYPE_LABEL.get(event_type, "Spotkanie")
        return {
            "title": f"{label} — {client_name}",
            "location": location,
            "description": "",
            "full_name": client_name,
            "client_found": True,
        }

    with patch(
        "bot.handlers.text.extract_meeting_data",
        new=AsyncMock(return_value={"meetings": meetings}),
    ), patch(
        "bot.handlers.text._enrich_meeting",
        new=AsyncMock(side_effect=enrich_side_effect),
    ) as mock_enrich, patch(
        "bot.handlers.text.check_conflicts", new=AsyncMock(return_value=[]),
    ), patch("bot.handlers.text.save_pending_flow") as mock_save_flow:
        await handle_add_meeting(
            upd,
            MagicMock(),
            {"id": 1, "default_meeting_duration": 60},
            {"entities": {"event_type": "in_person"}},
            "dodaj kilka spotkań",
        )

    flow_meetings = mock_save_flow.call_args.args[2]["meetings"]
    assert [_duration_minutes(item) for item in flow_meetings] == [60, 15, 15]
    assert [item["event_type"] for item in flow_meetings] == [
        "in_person",
        "phone_call",
        "offer_email",
    ]
    # Slice 5.4.1: per-meeting event_type is plumbed into _enrich_meeting so
    # Calendar titles are built with the correct label per event type.
    assert [call.kwargs.get("event_type") for call in mock_enrich.await_args_list] == [
        "in_person",
        "phone_call",
        "offer_email",
    ]
    assert [item["title"] for item in flow_meetings] == [
        "Spotkanie — Jan Kowalski",
        "Telefon — Anna Testowa",
        "Wysłać ofertę — Adam Ofertowy",
    ]


@pytest.mark.asyncio
async def test_add_meetings_batch_falls_back_to_text_event_type():
    """Parser event_type is per item. Without it, batch uses raw-message
    fallback, which can intentionally flatten a same-action batch."""
    upd = _update()
    meetings = [
        {"date": "2027-04-20", "time": "10:00", "client_name": "Jan Kowalski", "location": ""},
        {"date": "2027-04-20", "time": "11:00", "client_name": "Anna Testowa", "location": ""},
    ]

    def enrich_side_effect(_user_id: int, client_name: str, location: str, *, event_type=None) -> dict:
        return {
            "title": f"Spotkanie — {client_name}",
            "location": location,
            "description": "",
            "full_name": client_name,
            "client_found": True,
        }

    with patch(
        "bot.handlers.text.extract_meeting_data",
        new=AsyncMock(return_value={"meetings": meetings}),
    ), patch(
        "bot.handlers.text._enrich_meeting",
        new=AsyncMock(side_effect=enrich_side_effect),
    ), patch("bot.handlers.text.check_conflicts", new=AsyncMock(return_value=[])), \
         patch("bot.handlers.text.save_pending_flow") as mock_save_flow:
        await handle_add_meeting(
            upd,
            MagicMock(),
            {"id": 1, "default_meeting_duration": 60},
            {"entities": {"event_type": "in_person"}},
            "zadzwoń do obu jutro",
        )

    flow_meetings = mock_save_flow.call_args.args[2]["meetings"]
    assert [_duration_minutes(item) for item in flow_meetings] == [15, 15]
    assert [item["event_type"] for item in flow_meetings] == ["phone_call", "phone_call"]


@pytest.mark.asyncio
async def test_handle_add_meeting_auto_status_preview_for_new_lead():
    upd = _update()
    with patch(
        "bot.handlers.text.extract_meeting_data",
        new=AsyncMock(return_value={
            "meetings": [{
                "date": "2027-04-20",
                "time": "14:00",
                "client_name": "Jan Kowalski",
                "location": "Warszawa",
            }]
        }),
    ), patch(
        "bot.handlers.text._enrich_meeting",
        new=AsyncMock(return_value={
            "title": "Spotkanie — Jan Kowalski",
            "location": "ul. Prosta 1, Warszawa",
            "description": "",
            "full_name": "Jan Kowalski",
            "client_found": True,
            "client_row": 5,
            "current_status": "Nowy lead",
            "client_city": "Warszawa",
        }),
    ), patch("bot.handlers.text.check_conflicts", new=AsyncMock(return_value=[])), \
         patch("bot.handlers.text.save_pending") as mock_save:
        await handle_add_meeting(
            upd,
            MagicMock(),
            {"id": 1, "default_meeting_duration": 60},
            {"entities": {"event_type": "in_person"}},
            "spotkanie z Kowalskim w poniedziałek o 14",
        )

    saved_flow = mock_save.call_args.args[0]
    status_update = saved_flow.flow_data.get("status_update") or {}
    assert status_update.get("old_value") == "Nowy lead"
    assert status_update.get("new_value") == "Spotkanie umówione"
    assert status_update.get("row") == 5
    card_text = upd.effective_message.reply_markdown_v2.call_args.args[0]
    assert "Nowy lead" in card_text
    assert "Spotkanie umówione" in card_text


@pytest.mark.asyncio
async def test_handle_add_meeting_no_auto_status_for_phone_call():
    upd = _update()
    with patch(
        "bot.handlers.text.extract_meeting_data",
        new=AsyncMock(return_value={
            "meetings": [{
                "date": "2027-04-20",
                "time": "14:00",
                "client_name": "Jan Kowalski",
                "location": "",
            }]
        }),
    ), patch(
        "bot.handlers.text._enrich_meeting",
        new=AsyncMock(return_value={
            "title": "Spotkanie — Jan Kowalski",
            "location": "",
            "description": "",
            "full_name": "Jan Kowalski",
            "client_found": True,
            "client_row": 5,
            "current_status": "Nowy lead",
            "client_city": "Warszawa",
        }),
    ), patch("bot.handlers.text.check_conflicts", new=AsyncMock(return_value=[])), \
         patch("bot.handlers.text.save_pending") as mock_save:
        await handle_add_meeting(
            upd,
            MagicMock(),
            {"id": 1, "default_meeting_duration": 60},
            {"entities": {"event_type": "phone_call"}},
            "zadzwonić do Kowalskiego w poniedziałek o 14",
        )

    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_data.get("status_update") in (None, {})


@pytest.mark.asyncio
async def test_handle_add_meeting_no_auto_status_for_advanced_status():
    upd = _update()
    with patch(
        "bot.handlers.text.extract_meeting_data",
        new=AsyncMock(return_value={
            "meetings": [{
                "date": "2027-04-20",
                "time": "14:00",
                "client_name": "Jan Kowalski",
                "location": "Warszawa",
            }]
        }),
    ), patch(
        "bot.handlers.text._enrich_meeting",
        new=AsyncMock(return_value={
            "title": "Spotkanie — Jan Kowalski",
            "location": "Warszawa",
            "description": "",
            "full_name": "Jan Kowalski",
            "client_found": True,
            "client_row": 5,
            "current_status": "Oferta wysłana",
            "client_city": "Warszawa",
        }),
    ), patch("bot.handlers.text.check_conflicts", new=AsyncMock(return_value=[])), \
         patch("bot.handlers.text.save_pending") as mock_save:
        await handle_add_meeting(
            upd,
            MagicMock(),
            {"id": 1, "default_meeting_duration": 60},
            {"entities": {"event_type": "in_person"}},
            "spotkanie z Kowalskim w poniedziałek o 14",
        )

    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_data.get("status_update") in (None, {})
