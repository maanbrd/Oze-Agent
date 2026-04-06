"""Photo handler — assign client photos to Google Drive."""

import logging
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import ContextTypes

from bot.handlers.text import _run_guards
from bot.utils.telegram_helpers import is_private_chat, send_processing_stage
from shared.database import delete_pending_flow, get_pending_flow, save_pending_flow
from shared.formatting import format_error
from shared.google_drive import get_or_create_client_folder, upload_photo
from shared.google_sheets import search_clients, update_client

logger = logging.getLogger(__name__)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle photo messages — assign to a client folder in Google Drive.

    Flow:
    1. Standard guards.
    2. Download highest-resolution photo.
    3. Check for existing photo flow (batch upload in progress).
    4. If no flow: ask which client.
    5. If flow exists: upload, update Sheets link, confirm.
    """
    if not await is_private_chat(update):
        return

    user = await _run_guards(update)
    if not user:
        return

    telegram_id = update.effective_user.id
    user_id = user["id"]

    # Download highest resolution photo
    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        photo_bytes = await file.download_as_bytearray()
    except Exception as e:
        logger.error("handle_photo: download failed for %s: %s", telegram_id, e)
        await update.message.reply_text("❌ Nie udało się pobrać zdjęcia. Spróbuj ponownie.")
        return

    # Check for active photo flow
    flow = get_pending_flow(telegram_id)
    if flow and flow.get("flow_type") == "assign_photo":
        await _upload_to_client(update, context, user, flow, bytes(photo_bytes))
        return

    # No active flow — ask which client
    caption = update.message.caption or ""
    if caption:
        # Caption may contain client name — try to find them
        results = await search_clients(user_id, caption)
        if results and len(results) == 1:
            client = results[0]
            save_pending_flow(telegram_id, "assign_photo", {
                "client_name": client.get("Imię i nazwisko", ""),
                "city": client.get("Miasto", client.get("Miejscowość", "")),
                "row": client.get("_row"),
                "photo_bytes": list(bytes(photo_bytes)),  # store as list for JSON serialization
            })
            await _upload_to_client(update, context, user, get_pending_flow(telegram_id), bytes(photo_bytes))
            return

    # Ask user which client
    save_pending_flow(telegram_id, "assign_photo_pending", {
        "photo_bytes": list(bytes(photo_bytes)),
    })
    await update.message.reply_text(
        "📸 Do którego klienta przypisać to zdjęcie?\n"
        "Podaj imię i miejscowość klienta."
    )


async def _upload_to_client(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict,
    flow: dict,
    photo_bytes: bytes,
) -> None:
    """Upload photo to the client's Drive folder and update Sheets."""
    user_id = user["id"]
    telegram_id = update.effective_user.id
    flow_data = flow.get("flow_data", {})

    client_name = flow_data.get("client_name", "")
    city = flow_data.get("city", "")
    row = flow_data.get("row")

    await send_processing_stage(context, telegram_id, "uploading")

    try:
        folder_id = await get_or_create_client_folder(user_id, client_name, city)
        if not folder_id:
            await update.message.reply_markdown_v2(format_error("drive_down"))
            return

        timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"{client_name}_{timestamp}.jpg"

        link = await upload_photo(user_id, folder_id, photo_bytes, filename)
        if not link:
            await update.message.reply_markdown_v2(format_error("drive_down"))
            return

        # Update Sheets "Zdjęcia" column if we have the row number
        if row:
            await update_client(user_id, row, {"Zdjęcia": link})

        await update.message.reply_text(
            f"📸 Zdjęcie dodane do klienta *{client_name}*\\.",
            parse_mode="MarkdownV2",
        )
    except Exception as e:
        logger.error("_upload_to_client(%s): %s", telegram_id, e)
        await update.message.reply_markdown_v2(format_error("drive_down"))
    finally:
        delete_pending_flow(telegram_id)
