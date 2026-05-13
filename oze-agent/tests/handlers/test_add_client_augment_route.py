"""Routing tests for add_client augment replies after tapping Dopisać."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.handlers.text import _route_pending_flow


def _flow() -> dict:
    return {
        "flow_type": "add_client",
        "flow_data": {
            "client_data": {
                "Imię i nazwisko": "Anna Testowa",
                "Miasto": "Zatory",
            }
        },
    }


def _update(telegram_id: int = 123) -> MagicMock:
    upd = MagicMock()
    upd.effective_user.id = telegram_id
    upd.effective_message.reply_text = AsyncMock()
    upd.effective_message.reply_markdown_v2 = AsyncMock()
    return upd


def _duplicate_flow() -> dict:
    return {
        "flow_type": "add_client_duplicate",
        "flow_data": {
            "duplicate_row": 7,
            "client_name": "Jan Kowalski",
            "city": "Warszawa",
            "client_data": {
                "Imię i nazwisko": "Jan Kowalski",
                "Miasto": "Warszawa",
            },
        },
    }


@pytest.mark.asyncio
async def test_add_client_duplicate_augment_extracts_inline_email_without_llm():
    upd = _update()
    with patch("bot.handlers.text.extract_client_data", new=AsyncMock()) as mock_extract, \
         patch("bot.handlers.text.save_pending") as mock_save:
        consumed = await _route_pending_flow(
            upd,
            MagicMock(),
            {"id": "u1"},
            _duplicate_flow(),
            "email: updated@example.pl",
        )

    assert consumed is True
    mock_extract.assert_not_awaited()
    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_type.value == "add_client_duplicate"
    assert saved_flow.flow_data["duplicate_row"] == 7
    assert saved_flow.flow_data["client_data"]["Email"] == "updated@example.pl"


@pytest.mark.asyncio
async def test_add_client_augment_spotkanie_routes_before_client_extraction():
    upd = _update()
    with patch("bot.handlers.text.extract_client_data", new=AsyncMock()) as mock_extract, \
         patch("bot.handlers.text.handle_add_meeting", new=AsyncMock()) as mock_meeting:
        consumed = await _route_pending_flow(
            upd,
            MagicMock(),
            {"id": 1},
            _flow(),
            "spotkanie w piątek o 14",
        )

    assert consumed is True
    mock_extract.assert_not_called()
    mock_meeting.assert_awaited_once()
    args, _ = mock_meeting.call_args
    assert args[3]["source_client_data"] == {
        "Imię i nazwisko": "Anna Testowa",
        "Miasto": "Zatory",
    }
    assert args[3]["entities"]["event_type"] == "in_person"
    assert args[4] == "spotkanie w piątek o 14 z Anna Testowa Zatory"


@pytest.mark.asyncio
async def test_add_client_augment_meeting_phone_is_carried_to_meeting_flow():
    upd = _update()
    with patch("bot.handlers.text.extract_client_data", new=AsyncMock()) as mock_extract, \
         patch("bot.handlers.text.handle_add_meeting", new=AsyncMock()) as mock_meeting:
        consumed = await _route_pending_flow(
            upd,
            MagicMock(),
            {"id": 1},
            _flow(),
            "Spotkanie w piątek o 14 746938764",
        )

    assert consumed is True
    mock_extract.assert_not_called()
    args, _ = mock_meeting.call_args
    assert args[3]["entities"]["event_type"] == "in_person"
    assert args[3]["source_client_data"]["Telefon"] == "746938764"
    assert args[4] == "Spotkanie w piątek o 14 746938764 z Anna Testowa Zatory"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "message_text, expected_event_type",
    [
        ("spotkanie, zadzwoń wcześniej", "phone_call"),
        ("zadzwonić w piątek o 10", "phone_call"),
        ("wysłać ofertę w środę", "offer_email"),
        # Slice 5.4.2: follow-up / przypomnij fold into phone_call.
        ("follow-up dokumentowy w poniedziałek", "phone_call"),
        ("przypomnij o fakturze jutro", "phone_call"),
    ],
)
async def test_add_client_augment_infers_event_type_for_action_replies(
    message_text, expected_event_type
):
    upd = _update()
    with patch("bot.handlers.text.extract_client_data", new=AsyncMock()) as mock_extract, \
         patch("bot.handlers.text.handle_add_meeting", new=AsyncMock()) as mock_meeting:
        consumed = await _route_pending_flow(
            upd,
            MagicMock(),
            {"id": 1},
            _flow(),
            message_text,
        )

    assert consumed is True
    mock_extract.assert_not_called()
    args, _ = mock_meeting.call_args
    assert args[3]["entities"]["event_type"] == expected_event_type


@pytest.mark.asyncio
async def test_add_client_augment_phone_stays_client_data_path():
    upd = _update()
    with patch("bot.handlers.text.get_sheet_headers", new=AsyncMock(return_value=["Telefon"])), \
         patch(
             "bot.handlers.text.extract_client_data",
             new=AsyncMock(return_value={"client_data": {"Telefon": "123456789"}}),
         ) as mock_extract, \
         patch("bot.handlers.text.save_pending"), \
         patch("bot.handlers.text.handle_add_meeting", new=AsyncMock()) as mock_meeting:
        consumed = await _route_pending_flow(
            upd,
            MagicMock(),
            {"id": 1, "sheet_columns": ["Telefon", "Email"]},
            _flow(),
            "telefon 123456789",
        )

    assert consumed is True
    mock_extract.assert_awaited_once()
    mock_meeting.assert_not_called()


@pytest.mark.asyncio
async def test_add_client_augment_preserves_meeting_seeded_closed_context():
    upd = _update()
    flow = {
        "flow_type": "add_client",
        "flow_data": {
            "suppress_r7_after_save": True,
            "client_data": {
                "Imię i nazwisko": "Zbigniew Ziomek",
                "Miasto": "Marki",
                "Telefon": "725235242",
                "Status": "Spotkanie umówione",
                "Następny krok": "Spotkanie",
                "Data następnego kroku": "2026-05-14",
                "ID wydarzenia Kalendarz": "event-1",
            },
        },
    }
    with patch("bot.handlers.text.get_sheet_headers", new=AsyncMock(return_value=["Email"])), \
         patch(
             "bot.handlers.text.extract_client_data",
             new=AsyncMock(return_value={"client_data": {"Email": "zbigniewziomek@gmail.com"}}),
         ), \
         patch("bot.handlers.text.save_pending") as mock_save:
        consumed = await _route_pending_flow(
            upd,
            MagicMock(),
            {"id": 1, "sheet_columns": ["Email", "Źródło pozyskania"]},
            flow,
            "email zbigniewziomek@gmail.com",
        )

    assert consumed is True
    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_data["client_data"]["Email"] == "zbigniewziomek@gmail.com"
    assert saved_flow.flow_data["client_data"]["Następny krok"] == "Spotkanie"
    assert saved_flow.flow_data["client_data"]["Data następnego kroku"] == "2026-05-14"
    assert saved_flow.flow_data["suppress_r7_after_save"] is True
