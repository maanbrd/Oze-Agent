"""OZE-Agent Telegram bot entry point."""

import logging

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from bot.config import Config
from bot.handlers.buttons import handle_button
from bot.handlers.debug import debug_brief_command
from bot.handlers.fallback import handle_fallback
from bot.handlers.photo import handle_photo
from bot.handlers.start import start_command
from bot.handlers.text import handle_refresh_columns_command, handle_text
from bot.handlers.voice import handle_voice
from bot.scheduler import register_morning_brief

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def error_handler(update, context):
    logger.error("Exception while handling update: %s", context.error, exc_info=context.error)
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ Wystąpił nieoczekiwany błąd. Spróbuj ponownie za chwilę."
        )


def main():
    missing = Config.validate_phase_a()
    if missing:
        logger.error("Missing required env vars: %s", missing)
        return

    app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()

    # Order matters — first match wins
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("debug_brief", debug_brief_command))
    app.add_handler(CommandHandler("odswiez_kolumny", handle_refresh_columns_command))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(handle_button))
    app.add_handler(MessageHandler(filters.ALL, handle_fallback))
    app.add_error_handler(error_handler)

    register_morning_brief(app)

    if Config.ENV == "dev":
        logger.info("Starting bot in POLLING mode (dev)")
        app.run_polling(drop_pending_updates=True)
    else:
        webhook_url = f"{Config.BASE_URL}/webhooks/telegram"
        logger.info("Starting bot in WEBHOOK mode: %s", webhook_url)
        app.run_webhook(
            listen="0.0.0.0",
            port=8443,
            url_path="/webhooks/telegram",
            webhook_url=webhook_url,
            drop_pending_updates=True,
        )


if __name__ == "__main__":
    import asyncio
    asyncio.set_event_loop(asyncio.new_event_loop())
    main()
