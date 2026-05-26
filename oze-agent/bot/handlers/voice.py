"""Voice message handler — transcribe with OpenAI STT, normalize Polish names,
always-show transcript with 2-button confirmation (Zapisz/Anuluj). After
"Zapisz" the transcription is fed into handle_text via text_override and
flows through the normal text path."""

import asyncio
import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.handlers.text import _run_guards
from bot.utils.telegram_helpers import (
    build_choice_buttons,
    increment_interaction,
    is_private_chat,
    send_processing_stage,
)
from bot.utils.conversation_reply import reply_markdown_v2, reply_text
from shared.database import save_pending_flow
from shared.formatting import escape_markdown_v2, format_error
from shared.voice_postproc import _redacted_postproc_summary, normalize_polish_names
from shared.whisper_stt import estimate_transcription_cost, transcribe_voice

logger = logging.getLogger(__name__)

WHISPER_TIMEOUT_SECONDS = 60


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle voice (and audio) messages.

    Flow (revised, post-MVP voice slice 25.04.2026):
      1. Standard guards.
      2. Download voice file.
      3. Transcribe with OpenAI STT (60s timeout).
      4. Normalize Polish names via Claude haiku post-pass (defensive — never
         raises, falls back to raw Whisper output on any guard trip).
      5. Log STT + Claude cost ZARAZ — independent of subsequent user
         action (vision: cost is committed once we paid for the call).
      6. ALWAYS save pending + show 2-button transcript card (Zapisz/Anuluj).
         No "fast path" for high-confidence — vision requires explicit user
         confirmation before any downstream processing. After "Zapisz" the
         transcription is fed via `handle_text(text_override=...)` and flows
         through the normal text path.
    """
    if not await is_private_chat(update):
        return

    user = await _run_guards(update)
    if not user:
        return

    telegram_id = update.effective_user.id
    await send_processing_stage(context, telegram_id, "transcribing")

    # ── 1. Download voice file ─────────────────────────────────────────────
    try:
        voice = update.message.voice or update.message.audio
        file = await context.bot.get_file(voice.file_id)
        audio_bytes = await file.download_as_bytearray()
    except Exception as e:
        logger.error("handle_voice: download failed for %s: %s", telegram_id, e)
        await reply_text(update, "❌ Nie udało się pobrać pliku. Spróbuj ponownie.")
        return

    # ── 2. Transcribe with timeout ─────────────────────────────────────────
    try:
        result = await asyncio.wait_for(
            transcribe_voice(bytes(audio_bytes), filename="voice.ogg"),
            timeout=WHISPER_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        logger.warning("handle_voice: STT timeout for %s", telegram_id)
        await reply_markdown_v2(update, format_error("timeout"))
        return
    except RuntimeError as e:
        logger.error("handle_voice: transcription failed for %s: %s", telegram_id, e)
        await reply_text(update,
            "❌ Nie udało się przetworzyć nagrania. Spróbuj wysłać wiadomość tekstową."
        )
        return

    raw_transcription = result["text"].strip()
    raw_confidence = result.get("confidence")
    confidence = (
        float(raw_confidence)
        if isinstance(raw_confidence, (int, float))
        else None
    )
    duration = _coerce_duration(result.get("duration_seconds"))
    voice_duration = getattr(voice, "duration", None)
    if duration <= 0:
        duration = _coerce_duration(voice_duration)
    stt_model = str(result.get("model") or "unknown")
    stt_fallback_used = bool(result.get("fallback_used", False))
    transcription_cost = estimate_transcription_cost(stt_model, duration)

    if not raw_transcription:
        await reply_text(update, "❌ Nie rozpoznano żadnych słów w nagraniu.")
        return

    # ── 3. Polish name post-processing (Claude haiku) ─────────────────────
    postproc = await normalize_polish_names(raw_transcription)
    transcription = postproc["corrected"]
    postproc_cost = postproc.get("cost_usd", 0.0)
    total_cost = transcription_cost + postproc_cost

    # PII-safe summary log: NO raw transcription, NO change pairs.
    logger.info(
        "handle_voice.postproc summary=%s stt_model=%s stt_fallback=%s "
        "confidence=%s duration_s=%.1f transcription_cost=%.6f",
        _redacted_postproc_summary(postproc),
        stt_model,
        stt_fallback_used,
        f"{confidence:.2f}" if confidence is not None else "n/a",
        duration,
        transcription_cost,
    )

    # ── 4. Cost log — fires ONCE here, regardless of user's next action ──
    await increment_interaction(
        telegram_id, "voice_transcription", f"{stt_model}+haiku",
        0, 0, total_cost,
    )

    # ── 5. Always-show transcript card with 2 buttons ─────────────────────
    pending_data = {
        "transcription": transcription,
        "stt_model": stt_model,
        "stt_fallback_used": stt_fallback_used,
        "duration_seconds": duration,
        "transcription_cost": transcription_cost,
        "postproc_cost": postproc_cost,
        "fallback": postproc.get("fallback"),
    }
    if confidence is not None:
        pending_data["confidence"] = confidence
    if result.get("fallback_from"):
        pending_data["stt_fallback_from"] = result["fallback_from"]
    save_pending_flow(telegram_id, "voice_transcription", pending_data)

    # Render transcript as a quoted italic block, MarkdownV2-escaped so
    # special chars in user speech (e.g. "Kowalski (Warszawa)") don't
    # break Telegram parsing.
    escaped_text = escape_markdown_v2(transcription)
    badge = "🎙 *Transkrypcja*"
    instruction = escape_markdown_v2("Jeśli tekst się zgadza, zapisz.")

    await reply_markdown_v2(update,
        f"{badge}:\n\n_{escaped_text}_\n\n{instruction}",
        reply_markup=build_choice_buttons([
            ("✅ Zapisz", "voice_confirm:yes"),
            ("❌ Anuluj", "voice_confirm:cancel"),
        ]),
    )


def _coerce_duration(value) -> float:
    return float(value) if isinstance(value, (int, float)) else 0.0
