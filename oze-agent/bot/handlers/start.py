"""Handler for the /start command — Telegram account linking."""

import logging
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import ContextTypes

from bot.config import Config
from bot.utils.telegram_helpers import is_private_chat
from shared.database import get_supabase_client, get_user_by_telegram_id, update_user

logger = logging.getLogger(__name__)

_WELCOME_MESSAGE = """👋 Witaj w OZE-Agent!

Twoje konto Telegram zostało pomyślnie połączone z OZE-Agent.

Możesz teraz:
• Dodawać klientów głosowo lub tekstowo
• Zarządzać spotkaniami w kalendarzu
• Przeglądać swój pipeline
• Przypisywać zdjęcia do klientów

Napisz cokolwiek, żeby zacząć! 🚀"""

_ALREADY_LINKED_MESSAGE = "✅ Jesteś już połączony z OZE-Agent. Napisz cokolwiek, żeby zacząć!"

_NOT_REGISTERED_MESSAGE = (
    "Aby korzystać z OZE-Agent, zarejestruj się na: {dashboard_url}\n\n"
    "Po rejestracji i płatności otrzymasz link do połączenia konta Telegram."
)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command.

    Flow:
    1. Ignore non-private chats.
    2. If a linking code is provided (deep link): validate and link Telegram account.
    3. If no code and user already linked: greet them.
    4. If no code and user not linked: send registration link.
    """
    if not await is_private_chat(update):
        return

    telegram_id = update.effective_user.id
    args = context.args or []
    linking_code = args[0] if args else None

    if linking_code:
        await _handle_linking_code(update, telegram_id, linking_code)
        return

    # No linking code — check if already registered
    user = get_user_by_telegram_id(telegram_id)
    if user:
        await update.message.reply_text(_ALREADY_LINKED_MESSAGE)
    else:
        dashboard_url = Config.DASHBOARD_URL or "https://oze-agent.pl"
        await update.message.reply_text(
            _NOT_REGISTERED_MESSAGE.format(dashboard_url=dashboard_url)
        )


async def _handle_linking_code(
    update: Update, telegram_id: int, linking_code: str
) -> None:
    """Validate the linking code and connect the Telegram account to the user."""
    try:
        client = get_supabase_client()
        result = (
            client.table("users")
            .select("id, name, telegram_link_code, telegram_link_code_expires, telegram_id")
            .eq("telegram_link_code", linking_code)
            .single()
            .execute()
        )
        user = result.data
    except Exception as e:
        logger.error("start_command linking: DB lookup failed: %s", e)
        await update.message.reply_text(
            "❌ Nie udało się zweryfikować kodu. Spróbuj ponownie lub skontaktuj się z pomocą."
        )
        return

    if not user:
        await update.message.reply_text(
            "❌ Nieprawidłowy lub wygasły kod. Wygeneruj nowy w ustawieniach konta."
        )
        return

    # Check expiry
    expires_str = user.get("telegram_link_code_expires")
    if expires_str:
        try:
            expires = datetime.fromisoformat(expires_str.replace("Z", "+00:00"))
            if datetime.now(tz=timezone.utc) > expires:
                await update.message.reply_text(
                    "❌ Kod wygasł. Wygeneruj nowy w ustawieniach konta."
                )
                return
        except Exception:
            pass

    # Check if this Telegram account is already linked to a different user
    if user.get("telegram_id") and user["telegram_id"] != telegram_id:
        await update.message.reply_text(
            "❌ To konto jest już połączone z innym użytkownikiem Telegram."
        )
        return

    # Link the account
    update_user(user["id"], {
        "telegram_id": telegram_id,
        "telegram_link_code": None,
        "telegram_link_code_expires": None,
    })

    logger.info("Linked telegram_id=%s to user_id=%s", telegram_id, user["id"])
    await update.message.reply_text(_WELCOME_MESSAGE)
