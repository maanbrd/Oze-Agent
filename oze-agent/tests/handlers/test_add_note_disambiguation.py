"""Tests for handle_add_note unique-match vs multi-match routing.

Regression guard for silent-pick bug: when search_clients returns 2+ rows with
identical full names (different cities), bot must ask which one, not silently
pick the first.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.handlers.text import handle_add_note
from shared.pending import PendingFlowType


def _update(telegram_id: int = 123) -> MagicMock:
    upd = MagicMock()
    upd.effective_user.id = telegram_id
    upd.effective_message.reply_text = AsyncMock()
    upd.effective_message.reply_markdown_v2 = AsyncMock()
    return upd


def _button_callbacks(reply_markup) -> list[str]:
    return [
        button.callback_data
        for row in reply_markup.inline_keyboard
        for button in row
    ]


@pytest.mark.asyncio
async def test_add_note_multi_exact_match_asks_which_one():
    """2+ rows with identical full name + no city → disambiguation, NOT silent pick."""
    upd = _update()
    extract = AsyncMock(return_value={
        "client_name": "Mariusz Krzywinski",
        "city": "",
        "note": "dzwonił wczoraj",
    })
    search = AsyncMock(return_value=[
        {"_row": 7, "Imię i nazwisko": "Mariusz Krzywinski", "Miasto": "Marki"},
        {"_row": 11, "Imię i nazwisko": "Mariusz Krzywinski", "Miasto": "Wołomin"},
    ])

    with patch("bot.handlers.text.extract_note_data", new=extract), \
         patch("bot.handlers.text.search_clients", new=search), \
         patch("bot.handlers.text.save_pending") as mock_save:
        await handle_add_note(
            upd,
            MagicMock(),
            {"id": 1},
            {"entities": {}},
            "dodaj notatkę do Mariusz Krzywinski: dzwonił wczoraj",
        )

    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_type is PendingFlowType.DISAMBIGUATION
    assert saved_flow.flow_data == {
        "intent": "add_note",
        "note_text": "dzwonił wczoraj",
    }
    reply = upd.effective_message.reply_text.call_args
    text = reply.args[0]
    assert "Mam 2 klientów:" in text
    assert "Mariusz Krzywinski — Marki" in text
    assert "Mariusz Krzywinski — Wołomin" in text
    assert "Którego?" in text

    markup = reply.kwargs["reply_markup"]
    assert _button_callbacks(markup) == ["select_client:7", "select_client:11"]


@pytest.mark.asyncio
async def test_add_note_multi_same_name_narrows_by_city():
    """2+ same-name rows + city in query → _first_name_ok narrows to 1 → auto-pick."""
    upd = _update()
    extract = AsyncMock(return_value={
        "client_name": "Mariusz Krzywinski",
        "city": "Marki",
        "note": "test",
    })
    search = AsyncMock(return_value=[
        {"_row": 7, "Imię i nazwisko": "Mariusz Krzywinski", "Miasto": "Marki", "Notatki": ""},
        {"_row": 11, "Imię i nazwisko": "Mariusz Krzywinski", "Miasto": "Wołomin", "Notatki": ""},
    ])

    with patch("bot.handlers.text.extract_note_data", new=extract), \
         patch("bot.handlers.text.search_clients", new=search), \
         patch("bot.handlers.text.save_pending") as mock_save:
        await handle_add_note(
            upd,
            MagicMock(),
            {"id": 1},
            {"entities": {}},
            "dodaj notatkę do Mariusz Krzywinski Marki: test",
        )

    # City narrowed to Marki → auto-pick, no disambiguation
    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_type is PendingFlowType.ADD_NOTE
    assert saved_flow.flow_data["row"] == 7


@pytest.mark.asyncio
async def test_add_note_unique_exact_match_shows_card():
    """2 different surnames, query exact-matches 1 → auto-pick."""
    upd = _update()
    extract = AsyncMock(return_value={
        "client_name": "Jan Kowalski",
        "city": "",
        "note": "test",
    })
    search = AsyncMock(return_value=[
        {"_row": 5, "Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa", "Notatki": ""},
        {"_row": 9, "Imię i nazwisko": "Anna Nowak", "Miasto": "Kraków", "Notatki": ""},
    ])

    with patch("bot.handlers.text.extract_note_data", new=extract), \
         patch("bot.handlers.text.search_clients", new=search), \
         patch("bot.handlers.text.save_pending") as mock_save:
        await handle_add_note(
            upd,
            MagicMock(),
            {"id": 1},
            {"entities": {}},
            "dodaj notatkę do Jan Kowalski: test",
        )

    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_type is PendingFlowType.ADD_NOTE
    assert saved_flow.flow_data["row"] == 5


@pytest.mark.asyncio
async def test_add_note_single_result_unchanged():
    """1 row from search_clients → existing single-result path (no silent-pick branch)."""
    upd = _update()
    extract = AsyncMock(return_value={
        "client_name": "Jan Mazur",
        "city": "",
        "note": "test",
    })
    search = AsyncMock(return_value=[
        {"_row": 4, "Imię i nazwisko": "Jan Mazur", "Miasto": "Radom", "Notatki": ""},
    ])

    with patch("bot.handlers.text.extract_note_data", new=extract), \
         patch("bot.handlers.text.search_clients", new=search), \
         patch("bot.handlers.text.save_pending") as mock_save:
        await handle_add_note(
            upd,
            MagicMock(),
            {"id": 1},
            {"entities": {}},
            "dodaj notatkę do Jan Mazur: test",
        )

    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_type is PendingFlowType.ADD_NOTE
    assert saved_flow.flow_data["row"] == 4
