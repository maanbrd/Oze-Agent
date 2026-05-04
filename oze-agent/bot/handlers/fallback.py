"""Catch-all handler for unsupported message types."""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.conversation_reply import reply_text
from bot.utils.telegram_helpers import is_private_chat

logger = logging.getLogger(__name__)


async def handle_fallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle any message not caught by other handlers.

    - Groups: ignore silently.
    - Stickers / animations / documents: inform user of supported types.
    - Forwarded messages: treat as regular content (re-route by type).
    """
    if not await is_private_chat(update):
        return

    message = update.effective_message
    if not message:
        return

    # Forwarded messages — route by actual content type
    if message.forward_date:
        if message.text:
            from bot.handlers.text import handle_text
            await handle_text(update, context)
        elif message.voice or message.audio:
            from bot.handlers.voice import handle_voice
            await handle_voice(update, context)
        elif message.photo:
            from bot.handlers.photo import handle_photo
            await handle_photo(update, context)
        elif message.document and (message.document.mime_type or "").startswith("image/"):
            from bot.handlers.photo import handle_photo
            await handle_photo(update, context)
        return

    # Unsupported types
    await reply_text(
        update,
        "Obsługuję wiadomości tekstowe, głosówki i zdjęcia. "
        "Wyślij jedną z tych form, żeby zacząć."
    )
