"""Routing tests for add_meeting replies after tapping Dopisać."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.handlers.text import _route_pending_flow
from shared.pending import PendingFlowType


def _flow(description: str = "") -> dict:
    return {
        "flow_type": "add_meeting",
        "flow_data": {
            "title": "Spotkanie — Anna Testowa",
            "start": "2026-04-17T14:00:00+02:00",
            "end": "2026-04-17T15:00:00+02:00",
            "client_name": "Anna Testowa",
            "location": "Zatory",
            "description": description,
        },
    }


def _update(telegram_id: int = 123) -> MagicMock:
    upd = MagicMock()
    upd.effective_user.id = telegram_id
    upd.effective_message.reply_text = AsyncMock()
    upd.effective_message.reply_markdown_v2 = AsyncMock()
    return upd


@pytest.mark.asyncio
async def test_add_meeting_augment_appends_description_and_keeps_meeting_flow():
    upd = _update()
    with patch("bot.handlers.text.save_pending") as mock_save:
        consumed = await _route_pending_flow(
            upd,
            MagicMock(),
            {"id": 1},
            _flow(),
            "Jest zainteresowany PV i magazynem",
        )

    assert consumed is True
    mock_save.assert_called_once()
    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_type is PendingFlowType.ADD_MEETING
    assert saved_flow.flow_data["description"] == "Jest zainteresowany PV i magazynem"
    upd.effective_message.reply_markdown_v2.assert_awaited_once()
    assert "Anna Testowa" in upd.effective_message.reply_markdown_v2.call_args.args[0]


@pytest.mark.asyncio
async def test_add_meeting_augment_preserves_existing_description():
    upd = _update()
    with patch("bot.handlers.text.save_pending") as mock_save:
        consumed = await _route_pending_flow(
            upd,
            MagicMock(),
            {"id": 1},
            _flow("Tel: 123456789"),
            "Jest zainteresowany magazynem",
        )

    assert consumed is True
    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_data["description"] == (
        "Tel: 123456789\nJest zainteresowany magazynem"
    )
