"""Handler integration for confirm → commit_add_note delegation.

Pipeline-surface tests live in tests/mutations/test_add_note.py. Here we
verify the handler layer wiring only:

* commit_add_note is awaited with the flow_data fields the branch sees
  (row / note_text / old_notes) plus today
* success → reply_text("✅ Notatka dodana.") — plain text, exact copy
* error_message="google_down" → reply_markdown_v2 with format_error key
"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.handlers.text import handle_confirm
from shared.mutations import AddNoteResult


def _update(telegram_id: int = 123) -> MagicMock:
    upd = MagicMock()
    upd.effective_user.id = telegram_id
    upd.effective_message.reply_text = AsyncMock()
    upd.effective_message.reply_markdown_v2 = AsyncMock()
    return upd


def _pending_add_note() -> dict:
    return {
        "flow_type": "add_note",
        "flow_data": {
            "row": 7,
            "note_text": "oddzwonił w sprawie oferty",
            "client_name": "Mariusz Krzywinski",
            "city": "Marki",
            "old_notes": "[15.04.2026]: pierwsza rozmowa",
        },
    }


@pytest.mark.asyncio
async def test_success_sends_exact_polish_copy():
    upd = _update()
    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value=_pending_add_note(),
    ), patch(
        "bot.handlers.text.commit_add_note",
        new=AsyncMock(return_value=AddNoteResult(success=True, final_notes="...")),
    ), patch("bot.handlers.text.delete_pending_flow"):
        await handle_confirm(upd, MagicMock(), {"id": "u1"}, {}, "")

    upd.effective_message.reply_text.assert_awaited_once_with("✅ Notatka dodana.")
    upd.effective_message.reply_markdown_v2.assert_not_called()


@pytest.mark.asyncio
async def test_handler_forwards_flow_data_to_pipeline():
    upd = _update()
    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value=_pending_add_note(),
    ), patch(
        "bot.handlers.text.commit_add_note",
        new=AsyncMock(return_value=AddNoteResult(success=True, final_notes="x")),
    ) as mock_pipeline, patch("bot.handlers.text.delete_pending_flow"):
        await handle_confirm(upd, MagicMock(), {"id": "u1"}, {}, "")

    mock_pipeline.assert_awaited_once()
    args = mock_pipeline.await_args.args
    assert args[0] == "u1"                                   # user_id
    assert args[1] == 7                                      # row
    assert args[2] == "oddzwonił w sprawie oferty"           # note_text
    assert args[3] == "[15.04.2026]: pierwsza rozmowa"       # old_notes
    assert args[4] == date.today()                           # today


@pytest.mark.asyncio
async def test_failure_replies_with_google_down_error_key():
    """error_message="google_down" must map to format_error("google_down"),
    not to a new error key — the taxonomy is frozen for Phase 5.
    """
    upd = _update()
    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value=_pending_add_note(),
    ), patch(
        "bot.handlers.text.commit_add_note",
        new=AsyncMock(return_value=AddNoteResult(success=False, error_message="google_down")),
    ), patch(
        "bot.handlers.text.format_error",
        return_value="ESCAPED_ERROR_MESSAGE",
    ) as mock_err, patch("bot.handlers.text.delete_pending_flow"):
        await handle_confirm(upd, MagicMock(), {"id": "u1"}, {}, "")

    mock_err.assert_called_once_with("google_down")
    upd.effective_message.reply_markdown_v2.assert_awaited_once_with("ESCAPED_ERROR_MESSAGE")
    upd.effective_message.reply_text.assert_not_called()
