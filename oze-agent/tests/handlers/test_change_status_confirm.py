"""Handler integration for confirm → commit_change_status + R7.

Pipeline-surface tests live in tests/mutations/test_change_status.py.
This file verifies the handler wiring only: reply copy on success,
format_error key on failure, R7 firing with the resolved row/status,
and the compound opt-out guard.
"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.handlers.text import handle_confirm
from shared.mutations import ChangeStatusResult


def _update(telegram_id: int = 123) -> MagicMock:
    upd = MagicMock()
    upd.effective_user.id = telegram_id
    upd.effective_message.reply_text = AsyncMock()
    upd.effective_message.reply_markdown_v2 = AsyncMock()
    return upd


def _pending_change_status(extra: dict | None = None) -> dict:
    data = {
        "row": 7,
        "field": "Status",
        "old_value": "Oferta wysłana",
        "new_value": "Podpisane",
        "client_name": "Mariusz Krzywinski",
        "city": "Marki",
    }
    if extra:
        data.update(extra)
    return {"flow_type": "change_status", "flow_data": data}


@pytest.mark.asyncio
async def test_success_sends_exact_polish_copy_and_fires_r7():
    upd = _update()
    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value=_pending_change_status(),
    ), patch(
        "bot.handlers.text.commit_change_status",
        new=AsyncMock(return_value=ChangeStatusResult(success=True)),
    ), patch(
        "bot.handlers.text.send_next_action_prompt",
        new=AsyncMock(),
    ) as mock_r7, patch("bot.handlers.text.delete_pending_flow") as mock_delete:
        await handle_confirm(upd, MagicMock(), {"id": "u1"}, {}, "")

    upd.effective_message.reply_text.assert_awaited_once_with(
        "✅ Status zmieniony na: Podpisane"
    )
    upd.effective_message.reply_markdown_v2.assert_not_called()

    mock_r7.assert_awaited_once()
    args = mock_r7.await_args.args
    assert args[1] == 123                            # telegram_id
    assert args[2] == "Mariusz Krzywinski"           # client_name
    assert args[3] == "Marki"                        # city
    kwargs = mock_r7.await_args.kwargs
    assert kwargs["client_row"] == 7
    assert kwargs["current_status"] == "Podpisane"

    # skip_delete=True keeps R7 pending alive for the follow-up
    mock_delete.assert_not_called()


@pytest.mark.asyncio
async def test_handler_forwards_row_new_value_and_today_to_pipeline():
    upd = _update()
    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value=_pending_change_status(),
    ), patch(
        "bot.handlers.text.commit_change_status",
        new=AsyncMock(return_value=ChangeStatusResult(success=True)),
    ) as mock_pipeline, patch(
        "bot.handlers.text.send_next_action_prompt", new=AsyncMock(),
    ):
        await handle_confirm(upd, MagicMock(), {"id": "u1"}, {}, "")

    mock_pipeline.assert_awaited_once()
    args = mock_pipeline.await_args.args
    assert args[0] == "u1"                      # user_id
    assert args[1] == 7                         # row
    assert args[2] == "Podpisane"               # new_status
    assert args[3] == date.today()              # today


@pytest.mark.asyncio
async def test_failure_replies_with_google_down_error_and_skips_r7():
    upd = _update()
    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value=_pending_change_status(),
    ), patch(
        "bot.handlers.text.commit_change_status",
        new=AsyncMock(return_value=ChangeStatusResult(success=False, error_message="google_down")),
    ), patch(
        "bot.handlers.text.format_error",
        return_value="ESCAPED_ERROR",
    ) as mock_err, patch(
        "bot.handlers.text.send_next_action_prompt", new=AsyncMock(),
    ) as mock_r7:
        await handle_confirm(upd, MagicMock(), {"id": "u1"}, {}, "")

    mock_err.assert_called_once_with("google_down")
    upd.effective_message.reply_markdown_v2.assert_awaited_once_with("ESCAPED_ERROR")
    upd.effective_message.reply_text.assert_not_called()
    mock_r7.assert_not_called()


@pytest.mark.asyncio
async def test_compound_add_meeting_marker_suppresses_r7():
    """Future compound flow can set flow_data['compound_add_meeting']=True
    to silence the R7 prompt when a meeting already defines the next step.
    The guard is defensive — no current code path sets it — but the
    contract is documented here so future compound handlers can opt in.
    """
    upd = _update()
    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value=_pending_change_status({"compound_add_meeting": True}),
    ), patch(
        "bot.handlers.text.commit_change_status",
        new=AsyncMock(return_value=ChangeStatusResult(success=True)),
    ), patch(
        "bot.handlers.text.send_next_action_prompt",
        new=AsyncMock(),
    ) as mock_r7:
        await handle_confirm(upd, MagicMock(), {"id": "u1"}, {}, "")

    upd.effective_message.reply_text.assert_awaited_once_with(
        "✅ Status zmieniony na: Podpisane"
    )
    mock_r7.assert_not_called()
