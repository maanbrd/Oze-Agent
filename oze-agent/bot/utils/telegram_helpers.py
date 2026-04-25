"""Common Telegram bot utilities for OZE-Agent."""

import logging
import os
from datetime import date
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from bot.config import Config
from shared.database import (
    get_daily_interaction_count,
    get_user_by_telegram_id,
    increment_daily_interaction_count,
    log_interaction,
)

logger = logging.getLogger(__name__)

# Daily interaction cap. Production default = 100. Override via env var
# DAILY_INTERACTION_LIMIT (e.g. set 99999 on Railway during voice/feature
# smoke testing; remove the env var to restore the default).
DAILY_LIMIT = int(os.getenv("DAILY_INTERACTION_LIMIT", "100"))
BORROW_LIMIT = 20  # Max interactions borrowable from tomorrow


# ── Typing / status indicators ────────────────────────────────────────────────


async def send_typing(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    """Send a typing indicator to the chat."""
    try:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    except Exception as e:
        logger.warning("send_typing(%s): %s", chat_id, e)


async def send_processing_stage(
    context: ContextTypes.DEFAULT_TYPE, chat_id: int, stage: str
) -> None:
    """Send a status update message during multi-step processing.

    stage examples: "transcribing", "analyzing", "writing"
    """
    messages = {
        "transcribing": "🎙 Transkrybuję...",
        "analyzing": "🔍 Analizuję...",
        "writing": "✍️ Zapisuję...",
        "searching": "🔎 Szukam...",
        "uploading": "📤 Przesyłam zdjęcie...",
    }
    text = messages.get(stage, "⏳ Przetwarzam...")
    try:
        await context.bot.send_message(chat_id=chat_id, text=text)
    except Exception as e:
        logger.warning("send_processing_stage(%s, %s): %s", chat_id, stage, e)


# ── User / subscription checks ────────────────────────────────────────────────


async def check_user_registered(telegram_id: int) -> Optional[dict]:
    """Return user dict if telegram_id is in Supabase, else None."""
    return get_user_by_telegram_id(telegram_id)


async def check_subscription_active(user: dict) -> bool:
    """Return True if the user's subscription is currently active."""
    return user.get("subscription_status") == "active" and not user.get("is_suspended", False)


async def check_interaction_limit(telegram_id: int) -> dict:
    """Check daily interaction count against the DAILY_LIMIT.

    Returns:
        {"allowed": bool, "count": int, "limit": int, "can_borrow": bool}
    """
    today = date.today()
    count = get_daily_interaction_count(telegram_id, today)
    allowed = count < DAILY_LIMIT
    can_borrow = not allowed and count < (DAILY_LIMIT + BORROW_LIMIT)
    return {
        "allowed": allowed,
        "count": count,
        "limit": DAILY_LIMIT,
        "can_borrow": can_borrow,
    }


async def increment_interaction(
    telegram_id: int,
    interaction_type: str,
    model: str,
    tokens_in: int,
    tokens_out: int,
    cost: float,
) -> None:
    """Log the interaction to Supabase and increment daily counter."""
    log_interaction(telegram_id, interaction_type, model, tokens_in, tokens_out, cost)
    increment_daily_interaction_count(telegram_id, date.today())


# ── Standard error / gate messages ───────────────────────────────────────────


async def send_unregistered_message(update: Update) -> None:
    """Inform user they need to register at oze-agent.pl."""
    dashboard_url = Config.DASHBOARD_URL or "https://oze-agent.pl"
    await update.effective_message.reply_text(
        f"Nie jesteś jeszcze zarejestrowany w OZE-Agent.\n\n"
        f"Aby uzyskać dostęp, zarejestruj się na: {dashboard_url}"
    )


async def send_subscription_expired_message(update: Update) -> None:
    """Inform user their subscription has expired and send payment link."""
    dashboard_url = Config.DASHBOARD_URL or "https://oze-agent.pl"
    await update.effective_message.reply_text(
        f"💳 Twoja subskrypcja wygasła.\n\n"
        f"Odnów dostęp tutaj: {dashboard_url}/billing"
    )


async def send_rate_limit_message(
    update: Update, count: int, can_borrow: bool
) -> None:
    """Inform user they've hit the daily limit and optionally offer borrowing."""
    text = (
        f"📊 Osiągnąłeś dzienny limit {DAILY_LIMIT} interakcji "
        f"(wykorzystano: {count}).\n\nLimit odnawia się o północy."
    )
    if can_borrow:
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Tak", callback_data="borrow:yes"),
            InlineKeyboardButton("❌ Nie", callback_data="borrow:no"),
        ]])
        await update.effective_message.reply_text(
            text + f"\n\nCzy chcesz pożyczyć do {BORROW_LIMIT} interakcji z jutra?",
            reply_markup=keyboard,
        )
    else:
        await update.effective_message.reply_text(text)


# ── Inline keyboard builders ──────────────────────────────────────────────────


def build_mutation_buttons(pending_id: str) -> InlineKeyboardMarkup:
    """Return R1-compliant 3-button mutation card keyboard.

    [✅ Zapisać]  [➕ Dopisać]  [❌ Anulować]
    callback_data: save:{id}, append:{id}, cancel:{id}
    """
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Zapisać", callback_data=f"save:{pending_id}"),
        InlineKeyboardButton("➕ Dopisać", callback_data=f"append:{pending_id}"),
        InlineKeyboardButton("❌ Anulować", callback_data=f"cancel:{pending_id}"),
    ]])


def build_confirm_cancel_buttons(pending_id: str) -> InlineKeyboardMarkup:
    """Return 2-button keyboard for single-field mutations (e.g. change_status).

    [✅ Zapisać]  [❌ Anulować]
    """
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Zapisać", callback_data=f"save:{pending_id}"),
        InlineKeyboardButton("❌ Anulować", callback_data=f"cancel:{pending_id}"),
    ]])


def build_duplicate_buttons(pending_id: str) -> InlineKeyboardMarkup:
    """Return R4-compliant 2-button duplicate disambiguation keyboard.

    [📋 Dopisz do istniejącego]  [➕ Utwórz nowy wpis]
    callback_data: merge:{id}, new:{id}
    """
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("📋 Dopisz do istniejącego", callback_data=f"merge:{pending_id}"),
        InlineKeyboardButton("➕ Utwórz nowy wpis", callback_data=f"new:{pending_id}"),
    ]])


def build_choice_buttons(options: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    """Build a vertical list of choice buttons.

    options: list of (label, callback_data) tuples.
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(label, callback_data=data)]
        for label, data in options
    ])


# ── Chat type guard ───────────────────────────────────────────────────────────


async def is_private_chat(update: Update) -> bool:
    """Return True only for private (1-on-1) chats."""
    return update.effective_chat is not None and update.effective_chat.type == "private"
