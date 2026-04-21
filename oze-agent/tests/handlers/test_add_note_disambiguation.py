"""Tests for handle_add_note unique-match vs multi-match routing.

Regression guard for silent-pick bug: when search_clients returns 2+ rows with
identical full names (different cities), bot must ask which one, not silently
pick the first.

Post-Slice-5.1c: handler delegates to shared.clients.lookup_client; tests
patch lookup_client directly with pre-built ClientLookupResult objects.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.handlers.text import handle_add_note
from shared.clients import ClientLookupResult
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


def _patched_lookup(result: ClientLookupResult):
    return patch(
        "bot.handlers.text.lookup_client",
        new=AsyncMock(return_value=result),
    )


@pytest.mark.asyncio
async def test_add_note_multi_exact_match_asks_which_one():
    """lookup_client=multi → disambiguation list, NOT silent pick."""
    upd = _update()
    extract = AsyncMock(return_value={
        "client_name": "Mariusz Krzywinski",
        "city": "",
        "note": "dzwonił wczoraj",
    })
    clients = [
        {"_row": 7, "Imię i nazwisko": "Mariusz Krzywinski", "Miasto": "Marki"},
        {"_row": 11, "Imię i nazwisko": "Mariusz Krzywinski", "Miasto": "Wołomin"},
    ]
    result = ClientLookupResult(status="multi", clients=clients, normalized_query="mariusz krzywinski")

    with patch("bot.handlers.text.extract_note_data", new=extract), \
         _patched_lookup(result), \
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
async def test_add_note_unique_via_city_narrows():
    """lookup_client=unique (city narrowed) → auto-pick, save ADD_NOTE pending."""
    upd = _update()
    extract = AsyncMock(return_value={
        "client_name": "Mariusz Krzywinski",
        "city": "Marki",
        "note": "test",
    })
    client = {"_row": 7, "Imię i nazwisko": "Mariusz Krzywinski", "Miasto": "Marki", "Notatki": ""}
    result = ClientLookupResult(status="unique", clients=[client], normalized_query="mariusz krzywinski")

    with patch("bot.handlers.text.extract_note_data", new=extract), \
         _patched_lookup(result), \
         patch("bot.handlers.text.save_pending") as mock_save:
        await handle_add_note(
            upd,
            MagicMock(),
            {"id": 1},
            {"entities": {}},
            "dodaj notatkę do Mariusz Krzywinski Marki: test",
        )

    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_type is PendingFlowType.ADD_NOTE
    assert saved_flow.flow_data["row"] == 7


@pytest.mark.asyncio
async def test_add_note_unique_exact_match_shows_card():
    """lookup_client=unique → ADD_NOTE pending flow."""
    upd = _update()
    extract = AsyncMock(return_value={
        "client_name": "Jan Kowalski",
        "city": "",
        "note": "test",
    })
    client = {"_row": 5, "Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa", "Notatki": ""}
    result = ClientLookupResult(status="unique", clients=[client], normalized_query="jan kowalski")

    with patch("bot.handlers.text.extract_note_data", new=extract), \
         _patched_lookup(result), \
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
    """lookup_client=unique (single row) → ADD_NOTE pending flow."""
    upd = _update()
    extract = AsyncMock(return_value={
        "client_name": "Jan Mazur",
        "city": "",
        "note": "test",
    })
    client = {"_row": 4, "Imię i nazwisko": "Jan Mazur", "Miasto": "Radom", "Notatki": ""}
    result = ClientLookupResult(status="unique", clients=[client], normalized_query="jan mazur")

    with patch("bot.handlers.text.extract_note_data", new=extract), \
         _patched_lookup(result), \
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


@pytest.mark.asyncio
async def test_add_note_not_found_shows_polish_error():
    """lookup_client=not_found → 'Nie znalazłem klienta' message (no fuzzy suggestion)."""
    upd = _update()
    extract = AsyncMock(return_value={
        "client_name": "Piotr Wiśniewski",
        "city": "Gdańsk",
        "note": "test",
    })
    result = ClientLookupResult(status="not_found", clients=[], normalized_query="piotr wisniewski")

    with patch("bot.handlers.text.extract_note_data", new=extract), \
         _patched_lookup(result), \
         patch("bot.handlers.text.save_pending") as mock_save:
        await handle_add_note(
            upd,
            MagicMock(),
            {"id": 1},
            {"entities": {}},
            "dodaj notatkę do Piotr Wiśniewski Gdańsk: test",
        )

    mock_save.assert_not_called()
    reply = upd.effective_message.reply_text.call_args.args[0]
    assert "Nie znalazłem klienta: 'Piotr Wiśniewski (Gdańsk)'" in reply
