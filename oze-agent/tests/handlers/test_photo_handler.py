"""Handler tests for Telegram photo/image upload flow."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _client(**overrides):
    data = {
        "_row": 7,
        "Imię i nazwisko": "Jan Kowalski",
        "Miasto": "Warszawa",
        "Adres": "Leśna 5",
        "Zdjęcia": "",
        "Link do zdjęć": "",
    }
    data.update(overrides)
    return data


def _make_photo_update(caption: str | None = None, telegram_id: int = 12345):
    update = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = telegram_id
    update.effective_message = MagicMock()
    update.message = update.effective_message
    update.message.caption = caption
    update.message.photo = [MagicMock(file_id="small"), MagicMock(file_id="photo-file-id")]
    update.message.document = None
    update.message.reply_text = AsyncMock()
    return update


def _make_document_update(caption: str | None = None, telegram_id: int = 12345):
    update = _make_photo_update(caption=caption, telegram_id=telegram_id)
    update.message.photo = []
    update.message.document = MagicMock()
    update.message.document.file_id = "document-file-id"
    update.message.document.mime_type = "image/png"
    return update


def _make_context():
    context = MagicMock()
    context.bot = MagicMock()
    fake_file = MagicMock()
    fake_file.download_as_bytearray = AsyncMock(return_value=bytearray(b"image-bytes"))
    context.bot.get_file = AsyncMock(return_value=fake_file)
    context.bot.send_message = AsyncMock()
    return context


@pytest.mark.asyncio
async def test_photo_caption_matching_client_shows_r1_card_without_drive_write():
    update = _make_photo_update(caption="Jan Kowalski Warszawa")
    context = _make_context()

    with patch("bot.handlers.photo.is_private_chat", new=AsyncMock(return_value=True)), \
         patch("bot.handlers.photo._run_guards", new=AsyncMock(return_value={"id": "user-1"})), \
         patch("bot.handlers.photo.get_active_photo_session", return_value=None, create=True), \
         patch("bot.handlers.photo.get_all_clients", new=AsyncMock(return_value=[_client()]), create=True), \
         patch("bot.handlers.photo.save_pending_flow") as mock_save, \
         patch("bot.handlers.photo.upload_photo_for_client", new=AsyncMock(), create=True) as mock_upload, \
         patch("bot.handlers.photo.reply_text", new=AsyncMock()) as mock_reply:
        from bot.handlers.photo import handle_photo

        await handle_photo(update, context)

    context.bot.get_file.assert_not_awaited()
    mock_upload.assert_not_awaited()
    mock_save.assert_called_once()
    assert mock_save.call_args.args[1] == "photo_upload"
    saved = mock_save.call_args.args[2]
    assert saved["file_id"] == "photo-file-id"
    assert "photo_bytes" not in saved
    reply_text = mock_reply.call_args.args[1]
    assert "Zapisać zdjęcie do folderu" in reply_text
    assert "Przez 15 minut" in reply_text
    assert "Do którego klienta" not in reply_text


@pytest.mark.asyncio
async def test_photo_without_caption_stores_file_id_only_and_asks_for_client():
    update = _make_photo_update(caption=None)
    context = _make_context()

    with patch("bot.handlers.photo.is_private_chat", new=AsyncMock(return_value=True)), \
         patch("bot.handlers.photo._run_guards", new=AsyncMock(return_value={"id": "user-1"})), \
         patch("bot.handlers.photo.get_active_photo_session", return_value=None, create=True), \
         patch("bot.handlers.photo.save_pending_flow") as mock_save, \
         patch("bot.handlers.photo.reply_text", new=AsyncMock()) as mock_reply:
        from bot.handlers.photo import handle_photo

        await handle_photo(update, context)

    context.bot.get_file.assert_not_awaited()
    assert mock_save.call_args.args[1] == "photo_upload"
    assert mock_save.call_args.args[2] == {"file_id": "photo-file-id", "caption": ""}
    assert "Podaj imię, nazwisko i miasto" in mock_reply.call_args.args[1]


@pytest.mark.asyncio
async def test_confirm_photo_upload_warns_when_session_cannot_be_saved():
    update = _make_photo_update()
    context = _make_context()
    flow_data = {
        "file_id": "photo-file-id",
        "caption": "",
        "client_row": 7,
        "client": _client(),
    }

    with patch("bot.handlers.photo.send_processing_stage", new=AsyncMock()), \
         patch("bot.handlers.photo.get_or_create_client_photo_folder", new=AsyncMock(
             return_value={"id": "folder-1", "webViewLink": "https://drive/folder-1"}
         ), create=True), \
         patch("bot.handlers.photo.upload_photo", new=AsyncMock(return_value="https://drive/file-1")), \
         patch("bot.handlers.photo.count_photos_in_folder", new=AsyncMock(return_value=1), create=True), \
         patch("bot.handlers.photo.update_client_photo_metadata", new=AsyncMock(return_value=True), create=True), \
         patch("bot.handlers.photo.save_active_photo_session", return_value=False, create=True), \
         patch("bot.handlers.photo.reply_text", new=AsyncMock()) as mock_reply:
        from bot.handlers.photo import confirm_photo_upload

        skip_delete = await confirm_photo_upload(update, context, {"id": "user-1"}, flow_data)

    assert skip_delete is False
    final_text = mock_reply.call_args.args[1]
    assert "Zdjęcie dodane" in final_text
    assert "nie udało się otworzyć sesji" in final_text
    assert "Przez 15 minut" not in final_text


@pytest.mark.asyncio
async def test_upload_photo_for_client_recovers_legacy_file_link_in_photo_count():
    context = _make_context()
    client = _client(
        **{
            "Zdjęcia": "https://drive.google.com/file/d/legacy-file/view",
            "Link do zdjęć": "",
        }
    )

    with patch("bot.handlers.photo.get_or_create_client_photo_folder", new=AsyncMock(
        return_value={"id": "folder-1", "webViewLink": "https://drive/folder-1"}
    ), create=True), \
         patch("bot.handlers.photo.upload_photo", new=AsyncMock(return_value="https://drive/file-2")), \
         patch("bot.handlers.photo.count_photos_in_folder", new=AsyncMock(return_value=4), create=True), \
         patch("bot.handlers.photo.update_client_photo_metadata", new=AsyncMock(return_value=True), create=True) as mock_update, \
         patch("bot.handlers.photo.save_active_photo_session", return_value=True, create=True):
        from bot.handlers.photo import upload_photo_for_client

        ok = await upload_photo_for_client(
            context,
            "user-1",
            7,
            client,
            "photo-file-id",
            telegram_id=12345,
        )

    assert ok is True
    mock_update.assert_awaited_once_with("user-1", 7, 4, "https://drive/folder-1")


@pytest.mark.asyncio
async def test_image_document_uses_document_file_id_and_shows_r1_card():
    update = _make_document_update(caption="Jan Kowalski Warszawa")
    context = _make_context()

    with patch("bot.handlers.photo.is_private_chat", new=AsyncMock(return_value=True)), \
         patch("bot.handlers.photo._run_guards", new=AsyncMock(return_value={"id": "user-1"})), \
         patch("bot.handlers.photo.get_active_photo_session", return_value=None, create=True), \
         patch("bot.handlers.photo.get_all_clients", new=AsyncMock(return_value=[_client()]), create=True), \
         patch("bot.handlers.photo.save_pending_flow") as mock_save, \
         patch("bot.handlers.photo.reply_text", new=AsyncMock()) as mock_reply:
        from bot.handlers.photo import handle_photo

        await handle_photo(update, context)

    context.bot.get_file.assert_not_awaited()
    assert mock_save.call_args.args[2]["file_id"] == "document-file-id"
    assert "Zapisać zdjęcie do folderu" in mock_reply.call_args.args[1]


@pytest.mark.asyncio
async def test_active_session_image_document_caption_matching_client_starts_new_confirmation():
    update = _make_document_update(caption="E2E-Beta-Photo-123-Beta E2E-Beta-City")
    context = _make_context()
    session = {
        "telegram_id": 12345,
        "user_id": "user-1",
        "client_row": 7,
        "folder_id": "alpha-folder",
        "folder_link": "https://drive/alpha-folder",
        "display_label": "E2E-Beta-Photo-123-Alpha, E2E-Beta-City",
    }
    beta = _client(
        _row=8,
        **{
            "Imię i nazwisko": "E2E-Beta-Photo-123-Beta",
            "Miasto": "E2E-Beta-City",
        },
    )

    with patch("bot.handlers.photo.is_private_chat", new=AsyncMock(return_value=True)), \
         patch("bot.handlers.photo._run_guards", new=AsyncMock(return_value={"id": "user-1"})), \
         patch("bot.handlers.photo.get_active_photo_session", return_value=session, create=True), \
         patch("bot.handlers.photo.get_all_clients", new=AsyncMock(return_value=[beta]), create=True), \
         patch("bot.handlers.photo.upload_photo_for_session", new=AsyncMock(), create=True) as mock_upload_session, \
         patch("bot.handlers.photo.save_pending_flow") as mock_save, \
         patch("bot.handlers.photo.reply_text", new=AsyncMock()) as mock_reply:
        from bot.handlers.photo import handle_photo

        await handle_photo(update, context)

    mock_upload_session.assert_not_awaited()
    assert mock_save.call_args.args[1] == "photo_upload"
    assert mock_save.call_args.args[2]["file_id"] == "document-file-id"
    reply_text = mock_reply.call_args.args[1]
    assert "Zapisać zdjęcie do folderu" in reply_text
    assert "E2E-Beta-Photo-123-Beta" in reply_text
