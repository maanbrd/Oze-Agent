"""Unit tests for bot/handlers/cancel.py — global /cancel slash-command.

Verifies:
- Pending exists → flow deleted + "Anulowane" reply
- No pending → polite "no active operation" reply
- Each flow_type is cancelable (add_client / voice_transcription / etc.)
- voice_transcription with awaiting_text_correction flag — moved here
  from voice handler tests because /cancel routes through CommandHandler,
  not through handle_text/_route_pending_flow.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.handlers.cancel import handle_cancel_command


def _make_update(telegram_id: int = 12345):
    """Construct a minimal mocked Telegram Update."""
    update = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = telegram_id
    update.effective_message = MagicMock()
    update.effective_message.reply_text = AsyncMock()
    return update


# ── 1. Pending exists → cancel ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cancel_with_active_add_client_pending():
    update = _make_update()
    fake_flow = {"flow_type": "add_client", "flow_data": {"client_data": {"name": "Jan"}}}
    with patch("bot.handlers.cancel.get_pending_flow", return_value=fake_flow), \
         patch("bot.handlers.cancel.delete_pending_flow") as mock_delete, \
         patch("bot.handlers.cancel.delete_active_photo_session", create=True) as mock_delete_session:
        await handle_cancel_command(update, MagicMock())
    mock_delete.assert_called_once_with(12345)
    mock_delete_session.assert_called_once_with(12345)
    update.effective_message.reply_text.assert_awaited_once_with("❌ Anulowane.")


# ── 2. No pending ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cancel_without_pending():
    update = _make_update()
    with patch("bot.handlers.cancel.get_pending_flow", return_value=None), \
         patch("bot.handlers.cancel.delete_pending_flow") as mock_delete, \
         patch("bot.handlers.cancel.delete_active_photo_session", create=True) as mock_delete_session:
        await handle_cancel_command(update, MagicMock())
    mock_delete.assert_not_called()
    mock_delete_session.assert_called_once_with(12345)
    update.effective_message.reply_text.assert_awaited_once_with(
        "Nie ma żadnej aktywnej operacji do anulowania."
    )


# ── 3. add_client pending (re-asserted explicitly per plan) ─────────────────


@pytest.mark.asyncio
async def test_cancel_add_client_flow_type():
    """Generic 'Anulowane' reply regardless of flow_type — no per-type
    customisation in current spec."""
    update = _make_update()
    flow = {"flow_type": "add_client", "flow_data": {"foo": "bar"}}
    with patch("bot.handlers.cancel.get_pending_flow", return_value=flow), \
         patch("bot.handlers.cancel.delete_pending_flow") as mock_delete:
        await handle_cancel_command(update, MagicMock())
    mock_delete.assert_called_once()
    update.effective_message.reply_text.assert_awaited_once_with("❌ Anulowane.")


# ── 4. voice_transcription with awaiting_text_correction ─────────────────────
#       (MOVED here from voice handler tests per plan v5 — /cancel routes
#       through CommandHandler, NOT through handle_text/_route_pending_flow)


@pytest.mark.asyncio
async def test_cancel_voice_transcription_awaiting_correction():
    """Voice handler in 'awaiting_text_correction' state must yield to /cancel.

    Slash-commands bypass `handle_text` entirely (filter `filters.TEXT &
    ~filters.COMMAND`), so the global /cancel handler is the only escape
    hatch from a stuck voice correction state.
    """
    update = _make_update()
    flow = {
        "flow_type": "voice_transcription",
        "flow_data": {
            "transcription": "Jan Kowalski",
            "awaiting_text_correction": True,
            "whisper_cost": 0.0001,
        },
    }
    with patch("bot.handlers.cancel.get_pending_flow", return_value=flow), \
         patch("bot.handlers.cancel.delete_pending_flow") as mock_delete:
        await handle_cancel_command(update, MagicMock())
    mock_delete.assert_called_once_with(12345)
    update.effective_message.reply_text.assert_awaited_once_with("❌ Anulowane.")


# ── 5. add_meeting_disambiguation pending ───────────────────────────────────


@pytest.mark.asyncio
async def test_cancel_add_meeting_disambiguation():
    update = _make_update()
    flow = {
        "flow_type": "add_meeting_disambiguation",
        "flow_data": {"candidates": ["Jan", "Marek"]},
    }
    with patch("bot.handlers.cancel.get_pending_flow", return_value=flow), \
         patch("bot.handlers.cancel.delete_pending_flow") as mock_delete:
        await handle_cancel_command(update, MagicMock())
    mock_delete.assert_called_once()
    update.effective_message.reply_text.assert_awaited_once_with("❌ Anulowane.")


# ── 6. Defensive: missing user / message ────────────────────────────────────


@pytest.mark.asyncio
async def test_cancel_silent_when_no_effective_user():
    """Defensive guard — if update has no user (shouldn't happen for
    a real CommandHandler match), handler returns silently."""
    update = MagicMock()
    update.effective_user = None
    update.effective_message = MagicMock()
    update.effective_message.reply_text = AsyncMock()

    with patch("bot.handlers.cancel.get_pending_flow") as mock_get:
        await handle_cancel_command(update, MagicMock())
    # Defensive guard returned early — no flow lookup, no reply.
    mock_get.assert_not_called()
    update.effective_message.reply_text.assert_not_awaited()
