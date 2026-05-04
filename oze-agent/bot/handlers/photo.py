"""Photo handler — assign client photos to Google Drive with R1 confirmation."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.handlers.text import _run_guards
from bot.utils.conversation_reply import edit_message_text, reply_markdown_v2, reply_text
from bot.utils.telegram_helpers import (
    build_choice_buttons,
    build_mutation_buttons,
    is_private_chat,
    send_processing_stage,
)
from shared.database import (
    delete_active_photo_session,
    get_active_photo_session,
    save_active_photo_session,
    save_pending_flow,
)
from shared.formatting import format_error
from shared.google_drive import get_or_create_client_photo_folder, upload_photo
from shared.google_sheets import get_all_clients, update_client_photo_metadata
from shared.search import normalize_polish

logger = logging.getLogger(__name__)

PHOTO_SESSION_MINUTES = 15
PHOTO_FLOW_TYPE = "photo_upload"
PHOTO_ADD_CLIENT_FLOW_TYPE = "photo_add_client"


def _client_label(client: dict) -> str:
    parts = [
        client.get("Imię i nazwisko", ""),
        client.get("Miasto", client.get("Miejscowość", "")),
        client.get("Adres", ""),
    ]
    return ", ".join(part.strip() for part in parts if part and part.strip())


def _photo_count(value: object) -> int:
    try:
        return int(str(value or "0").strip())
    except ValueError:
        return 0


def _file_id_from_update(update: Update) -> Optional[str]:
    message = update.effective_message
    if not message:
        return None
    if getattr(message, "photo", None):
        return message.photo[-1].file_id
    document = getattr(message, "document", None)
    mime_type = getattr(document, "mime_type", "") if document else ""
    if document and mime_type.startswith("image/"):
        return document.file_id
    return None


def _caption_from_update(update: Update) -> str:
    message = update.effective_message
    return (getattr(message, "caption", "") or "").strip() if message else ""


def _explicit_target_query(text: str) -> Optional[str]:
    """Return target query only for explicit client-switch captions."""
    patterns = [
        r"^\s*(?:zdjęcia|zdjecia|zdjęcie|zdjecie)\s+do\s+(.+)$",
        r"^\s*do\s+klienta\s+(.+)$",
        r"^\s*dla\s+klienta\s+(.+)$",
    ]
    for pattern in patterns:
        match = re.match(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _client_matches_text(client: dict, text: str) -> bool:
    norm_text = normalize_polish(text)
    norm_name = normalize_polish(client.get("Imię i nazwisko", ""))
    norm_city = normalize_polish(client.get("Miasto", client.get("Miejscowość", "")))
    if not norm_name or not norm_city:
        return False
    name_tokens = [token for token in norm_name.split() if len(token) > 1]
    return all(token in norm_text.split() for token in name_tokens) and norm_city in norm_text.split()


async def _resolve_clients_from_text(user_id: str, text: str) -> list[dict]:
    if not text.strip():
        return []
    clients = await get_all_clients(user_id)
    return [client for client in clients if _client_matches_text(client, text)]


def _confirmation_text(client: dict) -> str:
    label = _client_label(client)
    return (
        f"📸 Zapisać zdjęcie do folderu: {label}?\n"
        "Po zapisie: Przez 15 minut kolejne zdjęcia bez opisu wrzucę do tego klienta. "
        "Żeby zmienić klienta, napisz w opisie zdjęcia: zdjęcia do [imię nazwisko miasto]."
    )


def _pending_payload(file_id: str, caption: str, client: dict) -> dict:
    return {
        "file_id": file_id,
        "caption": caption,
        "client_row": client.get("_row"),
        "client": {
            "_row": client.get("_row"),
            "Imię i nazwisko": client.get("Imię i nazwisko", ""),
            "Miasto": client.get("Miasto", client.get("Miejscowość", "")),
            "Adres": client.get("Adres", ""),
            "Zdjęcia": client.get("Zdjęcia", ""),
            "Link do zdjęć": client.get("Link do zdjęć", ""),
        },
    }


async def _show_confirmation(update: Update, file_id: str, caption: str, client: dict) -> None:
    save_pending_flow(
        update.effective_user.id,
        PHOTO_FLOW_TYPE,
        _pending_payload(file_id, caption, client),
    )
    await reply_text(
        update,
        _confirmation_text(client),
        reply_markup=build_mutation_buttons("confirm"),
    )


async def _show_multi_match(update: Update, file_id: str, caption: str, clients: list[dict]) -> None:
    save_pending_flow(
        update.effective_user.id,
        PHOTO_FLOW_TYPE,
        {
            "file_id": file_id,
            "caption": caption,
            "candidates": [
                {
                    "_row": client.get("_row"),
                    "Imię i nazwisko": client.get("Imię i nazwisko", ""),
                    "Miasto": client.get("Miasto", client.get("Miejscowość", "")),
                    "Adres": client.get("Adres", ""),
                    "Zdjęcia": client.get("Zdjęcia", ""),
                    "Link do zdjęć": client.get("Link do zdjęć", ""),
                }
                for client in clients
            ],
        },
    )
    lines = [f"Mam {len(clients)} klientów:"]
    options = []
    for idx, client in enumerate(clients[:10], start=1):
        label = f"{idx}. {_client_label(client)}"
        lines.append(label)
        options.append((label, f"photo_select_client:{client.get('_row')}"))
    lines.append("Którego?")
    await reply_text(update, "\n".join(lines), reply_markup=build_choice_buttons(options))


async def _show_not_found(update: Update, file_id: str, caption: str, query: str) -> None:
    save_pending_flow(
        update.effective_user.id,
        PHOTO_FLOW_TYPE,
        {"file_id": file_id, "caption": caption, "query": query},
    )
    await reply_text(
        update,
        f"Nie znalazłem klienta: {query}.\nDodać klienta i podpiąć to zdjęcie?",
        reply_markup=InlineKeyboardMarkup.from_column([
            InlineKeyboardButton("➕ Dodać klienta", callback_data="photo_add_client:confirm"),
            InlineKeyboardButton("❌ Anulować", callback_data="cancel:confirm"),
        ]),
    )


async def _resolve_and_prompt(
    update: Update,
    user_id: str,
    file_id: str,
    caption: str,
    query: str,
) -> None:
    clients = await _resolve_clients_from_text(user_id, query)
    if len(clients) == 1:
        await _show_confirmation(update, file_id, caption, clients[0])
    elif len(clients) > 1:
        await _show_multi_match(update, file_id, caption, clients)
    else:
        await _show_not_found(update, file_id, caption, query)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Telegram photos and image documents."""
    if not await is_private_chat(update):
        return

    user = await _run_guards(update)
    if not user:
        return

    telegram_id = update.effective_user.id
    user_id = user["id"]
    file_id = _file_id_from_update(update)
    caption = _caption_from_update(update)
    if not file_id:
        await reply_text(update, "❌ Nie udało się odczytać zdjęcia.")
        return

    session = get_active_photo_session(telegram_id)
    explicit_query = _explicit_target_query(caption) if caption else None

    if session and caption and not explicit_query and len(caption.split()) >= 3:
        caption_clients = await _resolve_clients_from_text(user_id, caption)
        if len(caption_clients) == 1:
            await _show_confirmation(update, file_id, caption, caption_clients[0])
            return
        if len(caption_clients) > 1:
            await _show_multi_match(update, file_id, caption, caption_clients)
            return

    if session and not explicit_query:
        ok = await upload_photo_for_session(context, user_id, session, file_id, caption)
        if ok:
            await reply_text(update, f"📸 Dodane do: {session['display_label']}.")
        else:
            await reply_markdown_v2(update, format_error("drive_down"))
        return

    if explicit_query:
        await _resolve_and_prompt(update, user_id, file_id, caption, explicit_query)
        return

    if caption:
        clients = await _resolve_clients_from_text(user_id, caption)
        if len(clients) == 1:
            await _show_confirmation(update, file_id, caption, clients[0])
            return
        if len(clients) > 1:
            await _show_multi_match(update, file_id, caption, clients)
            return

    save_pending_flow(telegram_id, PHOTO_FLOW_TYPE, {"file_id": file_id, "caption": caption})
    await reply_text(
        update,
        "📸 Do którego klienta przypisać zdjęcie?\nPodaj imię, nazwisko i miasto.",
    )


async def handle_photo_text_reply(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict,
    flow_data: dict,
    message_text: str,
) -> bool:
    """Resolve a text reply for the first-photo assignment flow."""
    file_id = flow_data.get("file_id")
    if not file_id:
        await reply_markdown_v2(update, format_error("timeout"))
        return True

    if flow_data.get("client_row"):
        client = dict(flow_data.get("client") or {})
        new_caption = message_text.strip()
        await _show_confirmation(update, file_id, new_caption, client)
        return True

    await _resolve_and_prompt(
        update,
        user["id"],
        file_id,
        flow_data.get("caption", ""),
        message_text.strip(),
    )
    return True


async def handle_photo_select_client(query, telegram_id: int, row_str: str) -> None:
    """Resume photo confirmation after multi-match selection."""
    from shared.database import get_pending_flow

    flow = get_pending_flow(telegram_id)
    if not flow or flow.get("flow_type") != PHOTO_FLOW_TYPE:
        await edit_message_text(query, "Brak aktywnego zdjęcia.")
        return
    flow_data = flow.get("flow_data", {})
    row = int(row_str)
    candidates = flow_data.get("candidates", [])
    selected = next((client for client in candidates if client.get("_row") == row), None)
    if not selected:
        await edit_message_text(query, "Nie znalazłem tego klienta na liście.")
        return
    save_pending_flow(
        telegram_id,
        PHOTO_FLOW_TYPE,
        _pending_payload(flow_data["file_id"], flow_data.get("caption", ""), selected),
    )
    await edit_message_text(
        query,
        _confirmation_text(selected),
        reply_markup=build_mutation_buttons("confirm"),
    )


async def start_photo_add_client(query, telegram_id: int) -> None:
    """Switch a not-found photo flow into add-client-with-photo input mode."""
    from shared.database import get_pending_flow

    flow = get_pending_flow(telegram_id)
    if not flow or flow.get("flow_type") != PHOTO_FLOW_TYPE:
        await edit_message_text(query, "Brak aktywnego zdjęcia.")
        return
    flow_data = flow.get("flow_data", {})
    save_pending_flow(
        telegram_id,
        PHOTO_ADD_CLIENT_FLOW_TYPE,
        {
            "file_id": flow_data.get("file_id"),
            "caption": flow_data.get("caption", ""),
            "query": flow_data.get("query", ""),
        },
    )
    await edit_message_text(
        query,
        "Podaj dane klienta: imię, nazwisko, miasto, adres, telefon, produkt.",
    )


async def upload_photo_for_session(
    context: ContextTypes.DEFAULT_TYPE,
    user_id: str,
    session: dict,
    file_id: str,
    caption: str,
) -> bool:
    """Upload directly into an already confirmed active photo session."""
    clients = await get_all_clients(user_id)
    client = next(
        (row for row in clients if int(row.get("_row", 0) or 0) == int(session["client_row"])),
        {
            "_row": session.get("client_row"),
            "Zdjęcia": "",
            "Link do zdjęć": session.get("folder_link", ""),
        },
    )
    client = dict(client)
    client["Link do zdjęć"] = client.get("Link do zdjęć") or session.get("folder_link", "")
    return await upload_photo_for_client(
        context,
        user_id,
        int(session["client_row"]),
        client,
        file_id,
        caption,
        telegram_id=int(session["telegram_id"]),
        folder_id=session.get("folder_id"),
        folder_link=session.get("folder_link"),
        display_label=session.get("display_label", ""),
        refresh_session=True,
    )


async def upload_photo_for_client(
    context: ContextTypes.DEFAULT_TYPE,
    user_id: str,
    client_row: int,
    client: dict,
    file_id: str,
    caption: str = "",
    *,
    telegram_id: int | None = None,
    folder_id: str | None = None,
    folder_link: str | None = None,
    display_label: str | None = None,
    refresh_session: bool = True,
) -> bool:
    """Download Telegram file, upload to Drive, update Sheets N/O, and session."""
    telegram_file = await context.bot.get_file(file_id)
    photo_bytes = bytes(await telegram_file.download_as_bytearray())

    folder = None
    if folder_id and folder_link:
        folder = {"id": folder_id, "webViewLink": folder_link}
    else:
        folder = await get_or_create_client_photo_folder(user_id, client)
    if not folder:
        return False

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", client.get("Imię i nazwisko", "klient")).strip("_")
    filename = f"{safe_name or 'klient'}_{timestamp}.jpg"
    link = await upload_photo(user_id, folder["id"], photo_bytes, filename, description=caption)
    if not link:
        return False

    next_count = _photo_count(client.get("Zdjęcia")) + 1
    folder_web_link = folder.get("webViewLink") or folder_link or ""
    ok = await update_client_photo_metadata(user_id, client_row, next_count, folder_web_link)
    if not ok:
        return False

    if refresh_session:
        save_active_photo_session(
            telegram_id=telegram_id or 0,
            user_id=user_id,
            client_row=client_row,
            folder_id=folder["id"],
            folder_link=folder_web_link,
            display_label=display_label or _client_label(client),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=PHOTO_SESSION_MINUTES),
        )
    return True


async def confirm_photo_upload(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict,
    flow_data: dict,
) -> bool:
    """Commit first confirmed photo upload and open the active session."""
    client = dict(flow_data.get("client") or {})
    client_row = flow_data.get("client_row")
    file_id = flow_data.get("file_id")
    if not client_row or not file_id:
        await reply_markdown_v2(update, format_error("timeout"))
        return False

    await send_processing_stage(context, update.effective_user.id, "uploading")
    ok = await upload_photo_for_client(
        context,
        user["id"],
        int(client_row),
        client,
        file_id,
        flow_data.get("caption", ""),
        display_label=_client_label(client),
        refresh_session=False,
    )
    if not ok:
        await reply_markdown_v2(update, format_error("drive_down"))
        return False

    folder = await get_or_create_client_photo_folder(user["id"], client)
    if folder:
        save_active_photo_session(
            update.effective_user.id,
            user["id"],
            int(client_row),
            folder["id"],
            folder.get("webViewLink", ""),
            _client_label(client),
            datetime.now(timezone.utc) + timedelta(minutes=PHOTO_SESSION_MINUTES),
        )
    await reply_text(
        update,
        f"📸 Dodane do: {_client_label(client)}. "
        "Przez 15 minut kolejne zdjęcia bez opisu wrzucę do tego klienta. "
        "Żeby zmienić klienta, napisz w opisie: zdjęcia do [imię nazwisko miasto].",
    )
    return False


async def complete_photo_after_add_client(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: str,
    client_row: int,
    client_data: dict,
    photo_data: dict,
) -> bool:
    """Upload the carried first photo after add_client creates the Sheets row."""
    client = dict(client_data)
    client["_row"] = client_row
    ok = await upload_photo_for_client(
        context,
        user_id,
        client_row,
        client,
        photo_data.get("file_id", ""),
        photo_data.get("caption", ""),
        display_label=_client_label(client),
        refresh_session=False,
    )
    if not ok:
        return False
    folder = await get_or_create_client_photo_folder(user_id, client)
    if folder:
        save_active_photo_session(
            update.effective_user.id,
            user_id,
            client_row,
            folder["id"],
            folder.get("webViewLink", ""),
            _client_label(client),
            datetime.now(timezone.utc) + timedelta(minutes=PHOTO_SESSION_MINUTES),
        )
    return True
