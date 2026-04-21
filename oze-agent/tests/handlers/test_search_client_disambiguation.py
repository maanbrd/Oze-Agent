"""Tests for handle_search_client unique-match vs multi-match routing.

Regression guard for silent-pick bug: when search_clients returns 2+ rows with
identical full names (different cities), bot must ask which one, not silently
pick the first.

Post-Slice-5.1b: handler delegates to shared.clients.lookup_client; tests
patch lookup_client directly to pin down handler dispatch behavior.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.handlers.text import handle_search_client
from shared.clients import ClientLookupResult


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


def _patched_lookup(result: ClientLookupResult):
    return patch(
        "bot.handlers.text.lookup_client",
        new=AsyncMock(return_value=result),
    )


def _patched_suggest_fuzzy(value):
    return patch(
        "bot.handlers.text.suggest_fuzzy_client",
        new=AsyncMock(return_value=value),
    )


@pytest.mark.asyncio
async def test_search_client_unique_exact_match_shows_card():
    """lookup_client=unique → card directly."""
    upd = _update()
    client = {"_row": 7, "Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa"}
    result = ClientLookupResult(status="unique", clients=[client], normalized_query="jan kowalski")

    with _patched_lookup(result):
        await handle_search_client(
            upd,
            MagicMock(),
            {"id": 1},
            {"entities": {"name": "Jan Kowalski"}},
            "Jan Kowalski",
        )

    upd.effective_message.reply_markdown_v2.assert_awaited_once()
    for call in upd.effective_message.reply_text.call_args_list:
        assert "Mam " not in call.args[0]


@pytest.mark.asyncio
async def test_search_client_multi_exact_match_asks_which_one():
    """lookup_client=multi → disambiguation list, NOT silent pick."""
    upd = _update()
    clients = [
        {"_row": 7, "Imię i nazwisko": "Mariusz Krzywinski", "Miasto": "Marki"},
        {"_row": 11, "Imię i nazwisko": "Mariusz Krzywinski", "Miasto": "Wołomin"},
    ]
    result = ClientLookupResult(status="multi", clients=clients, normalized_query="mariusz krzywinski")

    with _patched_lookup(result):
        await handle_search_client(
            upd,
            MagicMock(),
            {"id": 1},
            {"entities": {"name": "Mariusz Krzywinski"}},
            "Mariusz Krzywinski",
        )

    upd.effective_message.reply_markdown_v2.assert_not_called()
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
    """lookup_client=unique via first_name_ok (typo tolerance) → card."""
    upd = _update()
    client = {"_row": 7, "Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa"}
    result = ClientLookupResult(status="unique", clients=[client], normalized_query="jan kowalsky")

    with _patched_lookup(result):
        await handle_search_client(
            upd,
            MagicMock(),
            {"id": 1},
            {"entities": {"name": "Jan Kowalsky"}},
            "Jan Kowalsky",
        )

    upd.effective_message.reply_markdown_v2.assert_awaited_once()
    for call in upd.effective_message.reply_text.call_args_list:
        assert "Mam " not in call.args[0]


@pytest.mark.asyncio
async def test_search_client_multi_first_name_ok_match_asks_which_one():
    """lookup_client=multi for two first_name_ok candidates → disambiguation."""
    upd = _update()
    clients = [
        {"_row": 7, "Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa"},
        {"_row": 9, "Imię i nazwisko": "Jan Kowalski", "Miasto": "Kraków"},
    ]
    result = ClientLookupResult(status="multi", clients=clients, normalized_query="jan kowalsky")

    with _patched_lookup(result):
        await handle_search_client(
            upd,
            MagicMock(),
            {"id": 1},
            {"entities": {"name": "Jan Kowalsky"}},
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
async def test_search_client_not_found_triggers_fuzzy_suggestion():
    """lookup_client=not_found (name) → suggest_fuzzy_client → 'Chodziło o...?' prompt."""
    upd = _update()
    result = ClientLookupResult(status="not_found", clients=[], normalized_query="kowalsky")
    candidate = {"_row": 7, "Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa"}

    from shared.clients import FuzzySuggestion

    with (
        _patched_lookup(result),
        _patched_suggest_fuzzy(FuzzySuggestion(candidate=candidate, distance=1)),
        patch("bot.handlers.text.save_pending_flow") as mock_save,
    ):
        await handle_search_client(
            upd,
            MagicMock(),
            {"id": 1},
            {"entities": {"name": "Kowalsky"}},
            "Kowalsky",
        )

    reply = upd.effective_message.reply_text.call_args
    assert "Chodziło o Jan Kowalski z Warszawa?" in reply.args[0]
    markup = reply.kwargs["reply_markup"]
    assert _button_callbacks(markup) == ["confirm:yes", "cancel:search"]
    mock_save.assert_called_once()
    args = mock_save.call_args.args
    assert args[0] == 123
    assert args[1] == "confirm_search"
    assert args[2] == {"row": 7}


@pytest.mark.asyncio
async def test_search_client_not_found_phone_skips_fuzzy():
    """Phone not_found → bare 'Nie mam ... w bazie', no fuzzy suggestion."""
    upd = _update()
    result = ClientLookupResult(
        status="not_found",
        clients=[],
        normalized_query="+48601123456",
        is_phone_query=True,
    )

    with (
        _patched_lookup(result),
        _patched_suggest_fuzzy(None) as mock_suggest,
    ):
        await handle_search_client(
            upd,
            MagicMock(),
            {"id": 1},
            {"entities": {"phone": "+48601123456"}},
            "+48601123456",
        )

    mock_suggest.assert_not_called()
    reply = upd.effective_message.reply_text.call_args
    assert "Nie mam \"+48601123456\" w bazie." in reply.args[0]


@pytest.mark.asyncio
async def test_search_client_multi_50_plus_sends_sheets_link():
    """lookup_client=multi with 50+ rows → link do arkusza, NOT button list (text.py:1197 regression guard)."""
    upd = _update()
    many = [
        {"_row": i, "Imię i nazwisko": "Jan Kowalski", "Miasto": f"Miasto{i}"}
        for i in range(2, 55)
    ]
    result = ClientLookupResult(status="multi", clients=many, normalized_query="jan")

    with _patched_lookup(result):
        await handle_search_client(
            upd,
            MagicMock(),
            {"id": 1, "google_sheets_id": "abc123"},
            {"entities": {"name": "Jan"}},
            "Jan",
        )

    reply = upd.effective_message.reply_text.call_args
    text = reply.args[0]
    assert "Otwórz arkusz" in text
    assert "docs.google.com/spreadsheets/d/abc123" in text
    assert "reply_markup" not in reply.kwargs or reply.kwargs.get("reply_markup") is None
