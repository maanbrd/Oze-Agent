from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.handlers.text import handle_confirm


def _update(telegram_id: int = 123) -> MagicMock:
    upd = MagicMock()
    upd.effective_user.id = telegram_id
    upd.effective_message.reply_text = AsyncMock()
    upd.effective_message.reply_markdown_v2 = AsyncMock()
    return upd


@pytest.mark.asyncio
async def test_client_field_update_confirm_writes_fields_and_restores_awaiting_next_step():
    upd = _update()
    flow_data = {
        "row": 22,
        "client_name": "Zbigniew Borek",
        "city": "Zielonka",
        "updates": {"Email": "zbigniew.borek@tlen.pl"},
        "return_flow_type": "awaiting_next_step",
        "return_flow_data": {
            "client_name": "Zbigniew Borek",
            "city": "Zielonka",
            "client_row": 22,
            "current_status": "Spotkanie umówione",
        },
    }

    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value={"flow_type": "client_field_update_confirm", "flow_data": flow_data},
    ), patch(
        "bot.handlers.text.update_client",
        new=AsyncMock(return_value=True),
    ) as mock_update, patch("bot.handlers.text.save_pending") as mock_save, patch(
        "bot.handlers.text.delete_pending_flow"
    ) as mock_delete:
        await handle_confirm(upd, MagicMock(), {"id": "u1"}, {}, "")

    mock_update.assert_awaited_once_with("u1", 22, {"Email": "zbigniew.borek@tlen.pl"})
    upd.effective_message.reply_text.assert_any_await("✅ Zapisane.")
    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_type.value == "awaiting_next_step"
    assert saved_flow.flow_data["client_row"] == 22
    mock_delete.assert_not_called()
