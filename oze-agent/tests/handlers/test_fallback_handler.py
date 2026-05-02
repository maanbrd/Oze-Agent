"""Regression tests for unsupported/forwarded message fallback routing."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_update():
    update = MagicMock()
    update.effective_message = MagicMock()
    update.effective_message.text = None
    update.effective_message.voice = None
    update.effective_message.audio = None
    update.effective_message.photo = None
    update.effective_message.document = None
    update.effective_message.reply_text = AsyncMock()
    return update


@pytest.mark.asyncio
async def test_fallback_without_forward_date_attribute_does_not_crash():
    update = _make_update()
    del update.effective_message.forward_date

    with patch("bot.handlers.fallback.is_private_chat", new=AsyncMock(return_value=True)), \
         patch("bot.handlers.fallback.reply_text", new=AsyncMock()) as mock_reply:
        from bot.handlers.fallback import handle_fallback

        await handle_fallback(update, MagicMock())

    mock_reply.assert_awaited_once()
    assert "tekstowe" in mock_reply.call_args.args[1]


@pytest.mark.asyncio
async def test_forwarded_image_document_routes_to_photo_handler():
    update = _make_update()
    context = MagicMock()
    update.effective_message.forward_origin = object()
    del update.effective_message.forward_date
    update.effective_message.document = MagicMock()
    update.effective_message.document.mime_type = "image/png"

    with patch("bot.handlers.fallback.is_private_chat", new=AsyncMock(return_value=True)), \
         patch("bot.handlers.photo.handle_photo", new=AsyncMock()) as mock_photo:
        from bot.handlers.fallback import handle_fallback

        await handle_fallback(update, context)

    mock_photo.assert_awaited_once_with(update, context)
