"""Admin-only debug commands for controlled manual smoke tests."""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.config import Config
from bot.utils.conversation_reply import reply_text
from shared.proactive.morning_brief import run_morning_brief

logger = logging.getLogger(__name__)


def _admin_telegram_id() -> int | None:
    raw = (Config.ADMIN_TELEGRAM_ID or "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        logger.error("Invalid ADMIN_TELEGRAM_ID: %r", raw)
        return None


async def debug_brief_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Run the morning brief immediately, restricted to the configured admin."""
    message = update.effective_message
    user = update.effective_user
    admin_id = _admin_telegram_id()

    if not message or not user or not admin_id or user.id != admin_id:
        if message:
            await reply_text(update, "Brak dostępu.")
        return

    await reply_text(update, "Uruchamiam morning brief debug...")
    result = await run_morning_brief(context.bot)
    await reply_text(update, f"Debug brief zakończony: {result}")
