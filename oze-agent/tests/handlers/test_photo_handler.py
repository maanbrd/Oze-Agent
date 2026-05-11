"""Handler tests for Telegram photo/image upload flow."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _client(row: int = 7, name: str = "Jan Kowalski", city: str = "Warszawa") -> dict:
    return {
        "_row": row,
        "Imię i nazwisko": name,
        "Miasto": city,
        "Adres": "Leśna 5",
        "Zdjęcia": "2",
        "Link do zdjęć": "",
    }


def _make_photo_update(caption: str | None = None, telegram_id: int = 12345):
    update = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = telegram_id
    update.message = MagicMock()
    update.effective_message = update.message
    update.message.caption = caption
    update.message.photo = [MagicMock(file_id="small"), MagicMock(file_id="photo-file-id")]
    update.message.document = None
    update.message.reply_text = AsyncMock()
    return update


def _make_context():
    context = MagicMock()
    context.bot = MagicMock()
    return context


@pytest.mark.asyncio
async def test_photo_caption_matching_client_skips_which_client_question_and_waits_for_save():
    update = _make_photo_update(caption="Jan Kowalski Warszawa")
    context = _make_context()

    with patch("bot.handlers.photo.is_private_chat", new=AsyncMock(return_value=True)), \
         patch("bot.handlers.photo._run_guards", new=AsyncMock(return_value={"id": "user-1"})), \
         patch("bot.handlers.photo.get_active_photo_session", return_value=None), \
         patch("bot.handlers.photo.get_all_clients", new=AsyncMock(return_value=[_client()])), \
         patch("bot.handlers.photo.save_pending_flow") as mock_save, \
         patch("bot.handlers.photo.upload_photo_for_client", new=AsyncMock()) as mock_upload, \
         patch("bot.handlers.photo.reply_text", new=AsyncMock()) as mock_reply:
        from bot.handlers.photo import handle_photo

        await handle_photo(update, context)

    mock_upload.assert_not_called()
    mock_save.assert_called_once()
    assert mock_save.call_args.args[1] == "photo_upload"
    saved = mock_save.call_args.args[2]
    assert saved["file_id"] == "photo-file-id"
    assert saved["client_row"] == 7
    assert saved["caption"] == "Jan Kowalski Warszawa"
    reply_text = mock_reply.await_args.args[1]
    assert "Do którego klienta" not in reply_text
    assert "Zapisać zdjęcie do folderu" in reply_text
    assert "Przez 15 minut" in reply_text


@pytest.mark.asyncio
async def test_photo_without_caption_asks_for_client_and_stores_file_id_only():
    update = _make_photo_update(caption=None)
    context = _make_context()

    with patch("bot.handlers.photo.is_private_chat", new=AsyncMock(return_value=True)), \
         patch("bot.handlers.photo._run_guards", new=AsyncMock(return_value={"id": "user-1"})), \
         patch("bot.handlers.photo.get_active_photo_session", return_value=None), \
         patch("bot.handlers.photo.save_pending_flow") as mock_save, \
         patch("bot.handlers.photo.reply_text", new=AsyncMock()) as mock_reply:
        from bot.handlers.photo import handle_photo

        await handle_photo(update, context)

    mock_save.assert_called_once()
    assert mock_save.call_args.args[1] == "photo_upload"
    assert mock_save.call_args.args[2] == {"file_id": "photo-file-id", "caption": ""}
    assert "Do którego klienta przypisać zdjęcie" in mock_reply.await_args.args[1]


@pytest.mark.asyncio
async def test_active_session_photo_without_caption_uploads_to_session_client():
    update = _make_photo_update(caption=None)
    context = _make_context()
    session = {
        "telegram_id": 12345,
        "user_id": "user-1",
        "client_row": 7,
        "folder_id": "folder-1",
        "folder_link": "https://drive.google.com/drive/folders/folder-1",
        "display_label": "Jan Kowalski, Warszawa, Leśna 5",
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
    }

    with patch("bot.handlers.photo.is_private_chat", new=AsyncMock(return_value=True)), \
         patch("bot.handlers.photo._run_guards", new=AsyncMock(return_value={"id": "user-1"})), \
         patch("bot.handlers.photo.get_active_photo_session", return_value=session), \
         patch("bot.handlers.photo.upload_photo_for_session", new=AsyncMock(return_value=True)) as mock_upload, \
         patch("bot.handlers.photo.reply_text", new=AsyncMock()) as mock_reply:
        from bot.handlers.photo import handle_photo

        await handle_photo(update, context)

    mock_upload.assert_awaited_once_with(context, "user-1", session, "photo-file-id", "")
    assert "Dodane do: Jan Kowalski, Warszawa, Leśna 5" in mock_reply.await_args.args[1]


@pytest.mark.asyncio
async def test_active_session_descriptive_caption_stays_on_session_client():
    update = _make_photo_update(caption="dach północny")
    context = _make_context()
    session = {
        "telegram_id": 12345,
        "user_id": "user-1",
        "client_row": 7,
        "folder_id": "folder-1",
        "folder_link": "https://drive.google.com/drive/folders/folder-1",
        "display_label": "Jan Kowalski, Warszawa, Leśna 5",
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
    }

    with patch("bot.handlers.photo.is_private_chat", new=AsyncMock(return_value=True)), \
         patch("bot.handlers.photo._run_guards", new=AsyncMock(return_value={"id": "user-1"})), \
         patch("bot.handlers.photo.get_active_photo_session", return_value=session), \
         patch("bot.handlers.photo.upload_photo_for_session", new=AsyncMock(return_value=True)) as mock_upload, \
         patch("bot.handlers.photo.reply_text", new=AsyncMock()):
        from bot.handlers.photo import handle_photo

        await handle_photo(update, context)

    mock_upload.assert_awaited_once_with(
        context, "user-1", session, "photo-file-id", "dach północny"
    )


@pytest.mark.asyncio
async def test_active_session_explicit_caption_switch_starts_new_confirmation_not_old_upload():
    update = _make_photo_update(caption="zdjęcia do Anna Nowak Kraków")
    context = _make_context()
    session = {
        "telegram_id": 12345,
        "user_id": "user-1",
        "client_row": 7,
        "folder_id": "folder-1",
        "folder_link": "https://drive.google.com/drive/folders/folder-1",
        "display_label": "Jan Kowalski, Warszawa, Leśna 5",
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
    }

    with patch("bot.handlers.photo.is_private_chat", new=AsyncMock(return_value=True)), \
         patch("bot.handlers.photo._run_guards", new=AsyncMock(return_value={"id": "user-1"})), \
         patch("bot.handlers.photo.get_active_photo_session", return_value=session), \
         patch("bot.handlers.photo.get_all_clients", new=AsyncMock(return_value=[
             _client(),
             _client(row=9, name="Anna Nowak", city="Kraków"),
         ])), \
         patch("bot.handlers.photo.upload_photo_for_session", new=AsyncMock()) as mock_upload, \
         patch("bot.handlers.photo.save_pending_flow") as mock_save, \
         patch("bot.handlers.photo.reply_text", new=AsyncMock()) as mock_reply:
        from bot.handlers.photo import handle_photo

        await handle_photo(update, context)

    mock_upload.assert_not_called()
    mock_save.assert_called_once()
    assert mock_save.call_args.args[2]["client_row"] == 9
    assert "Anna Nowak" in mock_reply.await_args.args[1]
