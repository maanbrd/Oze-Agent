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
    assert args[3]["source_client_data"]["Telefon"] == "746938764"
    assert args[4] == "Spotkanie w piątek o 14 746938764 z Anna Testowa Zatory"


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
