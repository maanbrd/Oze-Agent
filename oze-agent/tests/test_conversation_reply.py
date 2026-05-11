from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_reply_text_sends_then_saves_assistant_message():
    update = MagicMock()
    update.effective_user.id = 123
    update.effective_message.reply_text = AsyncMock(return_value="sent")

    with patch("bot.utils.conversation_reply.save_conversation_message") as save:
        from bot.utils.conversation_reply import reply_text
        result = await reply_text(update, "Hej")

    assert result == "sent"
    update.effective_message.reply_text.assert_awaited_once_with("Hej")
    save.assert_called_once_with(123, "assistant", "Hej", message_type="text")


@pytest.mark.asyncio
async def test_edit_message_text_saves_visible_edited_text():
    query = MagicMock()
    query.from_user.id = 456
    query.edit_message_text = AsyncMock(return_value="edited")

    with patch("bot.utils.conversation_reply.save_conversation_message") as save:
        from bot.utils.conversation_reply import edit_message_text
        result = await edit_message_text(query, "Karta klienta", parse_mode="MarkdownV2")

    assert result == "edited"
    query.edit_message_text.assert_awaited_once_with("Karta klienta", parse_mode="MarkdownV2")
    save.assert_called_once_with(456, "assistant", "Karta klienta", message_type="text")
