"""Tests for change_status matching and pending confirmation behavior."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.handlers.text import handle_change_status
from shared.pending import PendingFlowType


def _update(telegram_id: int = 123) -> MagicMock:
    upd = MagicMock()
    upd.effective_user.id = telegram_id
    upd.effective_message.reply_text = AsyncMock()
    upd.effective_message.reply_markdown_v2 = AsyncMock()
    return upd


@pytest.mark.asyncio
async def test_change_status_uses_entities_name_for_matching_not_whole_message():
    upd = _update()
    search = AsyncMock(return_value=[
        {
            "_row": 7,
            "Imię i nazwisko": "Jan Kowalski",
            "Miasto": "Warszawa",
            "Status": "Nowy lead",
        }
    ])

    with patch("bot.handlers.text.search_clients", new=search), patch(
        "bot.handlers.text.save_pending"
    ) as mock_save:
        await handle_change_status(
            upd,
            MagicMock(),
            {"id": 1},
            {"entities": {"name": "Jan Kowalski", "status": "Podpisane"}},
            "Jan Kowalski podpisał umowę, zmień status na Podpisane",
        )

    search.assert_awaited_once_with(1, "Jan Kowalski")
    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_type is PendingFlowType.CHANGE_STATUS
    assert saved_flow.flow_data["row"] == 7
    assert saved_flow.flow_data["new_value"] == "Podpisane"
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
        "bot.handlers.text.save_pending_flow"
    ) as mock_save_flow, patch("bot.handlers.text.save_pending") as mock_save:
        await handle_change_status(
            upd,
            MagicMock(),
            {"id": 1},
            {"entities": {"status": "Podpisane"}},
            "Anna zmień status na Podpisane",
        )

    mock_save.assert_not_called()
    mock_save_flow.assert_called_once_with(
        123,
        "disambiguation",
        {"intent": "change_status", "new_status": "Podpisane"},
    )
    response = upd.effective_message.reply_text.call_args.args[0]
    assert "Mam 2 klientów:" in response
    assert "Którego?" in response


@pytest.mark.asyncio
async def test_change_status_single_name_token_disambiguates_many_results():
    upd = _update()
    search = AsyncMock(return_value=[
        {"_row": 8, "Imię i nazwisko": "Jan Mazur", "Miasto": "Kraków", "Status": ""},
        {"_row": 9, "Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa", "Status": ""},
    ])

    with patch("bot.handlers.text.search_clients", new=search), patch(
        "bot.handlers.text.save_pending_flow"
    ) as mock_save_flow, patch("bot.handlers.text.save_pending") as mock_save:
        await handle_change_status(
            upd,
            MagicMock(),
            {"id": 1},
            {"entities": {"name": "Jan", "status": "Podpisane"}},
            "Jan podpisał",
        )

    search.assert_awaited_once_with(1, "Jan")
    mock_save.assert_not_called()
    mock_save_flow.assert_called_once_with(
        123,
        "disambiguation",
        {"intent": "change_status", "new_status": "Podpisane"},
    )
    response = upd.effective_message.reply_text.call_args.args[0]
    assert "Jan Mazur" in response
    assert "Jan Kowalski" in response
