"""Tests for handle_search_client unique-match vs multi-match routing.

Regression guard for silent-pick bug: when search_clients returns 2+ rows with
identical full names (different cities), bot must ask which one, not silently
pick the first.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.handlers.text import handle_search_client


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
async def test_search_client_unique_exact_match_shows_card():
    """Query matches exactly 1 row → show card directly."""
    upd = _update()
    results = [
        {"_row": 7, "Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa"},
        {"_row": 9, "Imię i nazwisko": "Anna Nowak", "Miasto": "Kraków"},
    ]

    with patch("bot.handlers.text.search_clients", new=AsyncMock(return_value=results)):
        await handle_search_client(
            upd,
            MagicMock(),
            {"id": 1},
            {"entities": {"name": "Jan Kowalski"}},
            "Jan Kowalski",
        )

    # Card rendered via markdown_v2, NOT disambiguation list
    upd.effective_message.reply_markdown_v2.assert_awaited_once()
    # Should not have called reply_text with "Mam N klientów:"
    reply_text_calls = upd.effective_message.reply_text.call_args_list
    for call in reply_text_calls:
        assert "Mam " not in call.args[0]


@pytest.mark.asyncio
async def test_search_client_multi_exact_match_asks_which_one():
    """2+ rows with identical full name → disambiguation list, NOT silent pick."""
    upd = _update()
    results = [
        {"_row": 7, "Imię i nazwisko": "Mariusz Krzywinski", "Miasto": "Marki"},
        {"_row": 11, "Imię i nazwisko": "Mariusz Krzywinski", "Miasto": "Wołomin"},
    ]

    with patch("bot.handlers.text.search_clients", new=AsyncMock(return_value=results)):
        await handle_search_client(
            upd,
            MagicMock(),
            {"id": 1},
            {"entities": {"name": "Mariusz Krzywinski"}},
            "Mariusz Krzywinski",
        )

    # Should NOT have shown a card (no silent pick)
    upd.effective_message.reply_markdown_v2.assert_not_called()

    # Should have shown disambiguation list
    reply = upd.effective_message.reply_text.call_args
    text = reply.args[0]
    assert "Mam 2 klientów:" in text
    assert "Mariusz Krzywinski — Marki" in text
    assert "Mariusz Krzywinski — Wołomin" in text
    assert "Którego?" in text

    markup = reply.kwargs["reply_markup"]
    assert _button_callbacks(markup) == ["select_client:7", "select_client:11"]


@pytest.mark.asyncio
async def test_search_client_unique_first_name_match_shows_card():
    """0 exact matches + 1 _first_name_ok match → show card."""
    upd = _update()
    # Query "Jan Kowalsky" (typo) — no exact match, but _first_name_ok matches
    # exactly one client after Levenshtein tolerance.
    results = [
        {"_row": 7, "Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa"},
        {"_row": 9, "Imię i nazwisko": "Anna Nowak", "Miasto": "Kraków"},
    ]

    with patch("bot.handlers.text.search_clients", new=AsyncMock(return_value=results)):
        await handle_search_client(
            upd,
            MagicMock(),
            {"id": 1},
            {"entities": {"name": "Jan Kowalsky"}},
            "Jan Kowalsky",
        )

    upd.effective_message.reply_markdown_v2.assert_awaited_once()
    reply_text_calls = upd.effective_message.reply_text.call_args_list
    for call in reply_text_calls:
        assert "Mam " not in call.args[0]


@pytest.mark.asyncio
async def test_search_client_multi_first_name_ok_match_asks_which_one():
    """0 exact matches + 2+ _first_name_ok matches → disambiguation list."""
    upd = _update()
    # Query matches both identically — _first_name_ok True for both.
    results = [
        {"_row": 7, "Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa"},
        {"_row": 9, "Imię i nazwisko": "Jan Kowalski", "Miasto": "Kraków"},
    ]

    with patch("bot.handlers.text.search_clients", new=AsyncMock(return_value=results)):
        await handle_search_client(
            upd,
            MagicMock(),
            {"id": 1},
            {"entities": {"name": "Jan Kowalsky"}},  # typo → no exact match
            "Jan Kowalsky",
        )

    upd.effective_message.reply_markdown_v2.assert_not_called()
    reply = upd.effective_message.reply_text.call_args
    text = reply.args[0]
    assert "Mam 2 klientów:" in text
    assert "Którego?" in text

    markup = reply.kwargs["reply_markup"]
    assert _button_callbacks(markup) == ["select_client:7", "select_client:9"]


@pytest.mark.asyncio
async def test_search_client_single_result_unchanged():
    """1 result from search_clients → existing single-result path (card or confirm-typo)."""
    upd = _update()
    results = [
        {"_row": 7, "Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa"},
    ]

    with patch("bot.handlers.text.search_clients", new=AsyncMock(return_value=results)):
        await handle_search_client(
            upd,
            MagicMock(),
            {"id": 1},
            {"entities": {"name": "Jan Kowalski"}},
            "Jan Kowalski",
        )

    # Exact substring match → card path, not confirm-typo
    upd.effective_message.reply_markdown_v2.assert_awaited_once()
