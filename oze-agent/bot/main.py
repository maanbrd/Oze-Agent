"""OZE-Agent Telegram bot entry point."""

import logging
import os

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    TypeHandler,
    filters,
)

from bot.config import Config
from bot.healthcheck import HEALTH_STATE, create_healthcheck_server, mark_update_seen
from bot.handlers.buttons import handle_button
from bot.handlers.cancel import handle_cancel_command
from bot.handlers.debug import debug_brief_command
from bot.handlers.fallback import handle_fallback
from bot.handlers.photo import handle_photo
from bot.handlers.start import start_command
from bot.handlers.text import handle_refresh_columns_command, handle_text
from bot.handlers.voice import handle_voice
from bot.scheduler import register_admin_mirror, register_morning_brief

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def _start_healthcheck_server():
    port_raw = os.getenv("HEALTHCHECK_PORT") or os.getenv("PORT")
    if not port_raw:
        return None

    try:
        port = int(port_raw)
    except ValueError:
        logger.warning("Invalid healthcheck port: %r", port_raw)
        return None

    webhook_port = int(os.getenv("BOT_WEBHOOK_PORT", "8443"))
    if Config.ENV != "dev" and port == webhook_port:
        logger.warning(
            "Healthcheck disabled: port %s is reserved for Telegram webhook",
            port,
        )
        return None

    try:
        server = create_healthcheck_server("0.0.0.0", port, HEALTH_STATE)
        server.start()
        logger.info("Healthcheck listening on /healthz port=%s", port)
        return server
    except OSError as e:
        logger.error("Healthcheck failed to bind port=%s: %s", port, e)
        return None


async def error_handler(update, context):
    logger.error("Exception while handling update: %s", context.error, exc_info=context.error)
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ Wystąpił nieoczekiwany błąd. Spróbuj ponownie za chwilę."
        )


def main():
    Config.warn_secret_whitespace()

    missing = Config.validate_phase_a()
    if missing:
        logger.error("Missing required env vars: %s", missing)
        return

    _start_healthcheck_server()

    app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()

    # Order matters — first match wins
    app.add_handler(TypeHandler(Update, mark_update_seen), group=-1)
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("cancel", handle_cancel_command))
    app.add_handler(CommandHandler("debug_brief", debug_brief_command))
    app.add_handler(CommandHandler("odswiez_kolumny", handle_refresh_columns_command))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(handle_button))
    app.add_handler(MessageHandler(filters.ALL, handle_fallback))
    app.add_error_handler(error_handler)

    register_morning_brief(app)
    register_admin_mirror(app)

    if Config.ENV == "dev":
        logger.info("Starting bot in POLLING mode (dev)")
        app.run_polling(drop_pending_updates=True)
    else:
        webhook_url = f"{Config.BASE_URL}/webhooks/telegram"
        webhook_port = int(os.getenv("BOT_WEBHOOK_PORT", "8443"))
        logger.info("Starting bot in WEBHOOK mode: %s", webhook_url)
        app.run_webhook(
            listen="0.0.0.0",
            port=webhook_port,
            url_path="/webhooks/telegram",
            webhook_url=webhook_url,
            drop_pending_updates=True,
        )


if __name__ == "__main__":
    import asyncio
    asyncio.set_event_loop(asyncio.new_event_loop())
    main()
