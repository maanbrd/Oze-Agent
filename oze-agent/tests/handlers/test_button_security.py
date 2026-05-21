from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta, timezone

import pytest


def _update(callback_data: str = "set_status:7:Podpisane", telegram_id: int = 123):
    update = MagicMock()
    update.effective_user.id = telegram_id
    update.effective_chat.type = "private"
    update.callback_query.data = callback_data
    update.callback_query.from_user.id = telegram_id
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.callback_query.message.date = datetime.now(tz=timezone.utc)
    return update


@pytest.mark.asyncio
async def test_set_status_callback_without_pending_flow_is_rejected():
    from bot.handlers.buttons import handle_button

    update = _update()
    with patch("bot.handlers.buttons._run_guards", new=AsyncMock(return_value={"id": "user-1"})), \
         patch("bot.handlers.buttons.get_pending_flow", return_value=None), \
         patch("bot.handlers.buttons.update_client", new=AsyncMock()) as update_client:
        await handle_button(update, MagicMock())

    update_client.assert_not_awaited()
    update.callback_query.edit_message_text.assert_awaited_once()
    assert "Nieaktualny" in update.callback_query.edit_message_text.await_args.args[0]


@pytest.mark.asyncio
async def test_stale_save_callback_does_not_confirm_newer_pending_flow():
    from bot.handlers.buttons import handle_button

    update = _update("save:confirm")
    update.callback_query.message.date = datetime.now(tz=timezone.utc) - timedelta(minutes=10)
    flow = {
        "flow_type": "add_client",
        "flow_data": {},
        "updated_at": datetime.now(tz=timezone.utc).isoformat(),
    }

    with patch("bot.handlers.buttons._run_guards", new=AsyncMock(return_value={"id": "user-1"})), \
         patch("bot.handlers.buttons.get_pending_flow", return_value=flow), \
         patch("bot.handlers.buttons.handle_confirm", new=AsyncMock()) as handle_confirm:
        await handle_button(update, MagicMock())

    handle_confirm.assert_not_awaited()
    update.callback_query.edit_message_text.assert_awaited_once()
    assert "Nieaktualny" in update.callback_query.edit_message_text.await_args.args[0]
