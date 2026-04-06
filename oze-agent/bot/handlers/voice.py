"""Voice message handler — transcribe with Whisper then route as text."""

import asyncio
import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.handlers.text import _run_guards, handle_general, handle_text
from bot.utils.telegram_helpers import (
    build_confirm_buttons,
    increment_interaction,
    is_private_chat,
    send_processing_stage,
    send_typing,
)
from shared.database import save_conversation_message, save_pending_flow
from shared.formatting import format_error
from shared.whisper_stt import transcribe_voice

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.85
WHISPER_TIMEOUT_SECONDS = 60


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle voice (and audio) messages.

    Flow:
    1. Standard guards.
    2. Download voice file.
    3. Transcribe with Whisper (60s timeout).
    4. If confidence ≥ 0.85: process directly.
    5. If confidence < 0.85: show transcription, ask for confirmation.
    6. Log whisper + claude costs.
    """
    if not await is_private_chat(update):
        return

    user = await _run_guards(update)
    if not user:
        return

    telegram_id = update.effective_user.id
    await send_processing_stage(context, telegram_id, "transcribing")

    # Download voice file
    try:
        voice = update.message.voice or update.message.audio
        file = await context.bot.get_file(voice.file_id)
        audio_bytes = await file.download_as_bytearray()
    except Exception as e:
        logger.error("handle_voice: download failed for %s: %s", telegram_id, e)
        await update.message.reply_text("❌ Nie udało się pobrać pliku. Spróbuj ponownie.")
        return

    # Transcribe with timeout
    try:
        result = await asyncio.wait_for(
            transcribe_voice(bytes(audio_bytes), filename="voice.ogg"),
            timeout=WHISPER_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        logger.warning("handle_voice: Whisper timeout for %s", telegram_id)
        await update.message.reply_markdown_v2(format_error("timeout"))
        return
    except RuntimeError as e:
        logger.error("handle_voice: transcription failed for %s: %s", telegram_id, e)
        await update.message.reply_text(
            "❌ Nie udało się przetworzyć nagrania. Spróbuj wysłać wiadomość tekstową."
        )
        return

    transcription = result["text"].strip()
    confidence = result["confidence"]
    duration = result.get("duration_seconds", 0)

    # Estimate Whisper cost: $0.006 per minute
    whisper_cost = (duration / 60) * 0.006

    if not transcription:
        await update.message.reply_text("❌ Nie rozpoznano żadnych słów w nagraniu.")
        return

    if confidence >= CONFIDENCE_THRESHOLD:
        # High confidence — process directly
        await send_processing_stage(context, telegram_id, "analyzing")
        save_conversation_message(telegram_id, "user", f"[głosówka] {transcription}")

        # Inject transcription as text and route through text handler
        update.message.text = transcription
        await handle_text(update, context)
    else:
        # Low confidence — show transcription, ask for confirmation
        save_pending_flow(telegram_id, "voice_transcription", {
            "transcription": transcription,
            "whisper_cost": whisper_cost,
        })
        escaped = transcription.replace("_", "\\_").replace("*", "\\*").replace("`", "\\`")
        await update.message.reply_markdown_v2(
            f"🎙 Transkrypcja \\(niska pewność\\):\n\n_{escaped}_\n\nCzy to poprawne?",
            reply_markup=build_confirm_buttons("voice_confirm"),
        )

    # Log whisper usage
    await increment_interaction(
        telegram_id, "voice_transcription", "whisper-1", 0, 0, whisper_cost
    )
