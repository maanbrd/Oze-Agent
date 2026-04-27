"""Global `/cancel` slash-command handler.

Closes ANY active pending flow for the user (add_client, add_meeting,
add_note, change_status, voice_transcription, etc.). Added as part of
the voice transcription post-MVP slice — voice correction UX assumes
`/cancel` always works as an escape hatch, but the repo previously had
no global cancel command.

Useful beyond voice: any user stuck in a pending state can `/cancel`
and start fresh.
"""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.conversation_reply import reply_text
from shared.database import delete_pending_flow, get_pending_flow

logger = logging.getLogger(__name__)


async def handle_cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancel any active pending flow for the calling user."""
    if update.effective_user is None or update.effective_message is None:
        return  # defensive — should not happen for a CommandHandler match

    telegram_id = update.effective_user.id
    flow = get_pending_flow(telegram_id)

    if flow:
        flow_type = flow.get("flow_type", "unknown")
        delete_pending_flow(telegram_id)
        logger.info(
            "handle_cancel_command: cancelled flow_type=%s for user %s",
            flow_type, telegram_id,
        )
        await reply_text(update, "❌ Anulowane.")
    else:
        await reply_text(update,
            "Nie ma żadnej aktywnej operacji do anulowania."
        )
