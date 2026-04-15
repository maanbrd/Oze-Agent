"""Routing tests for add_meeting replies after tapping Dopisać."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.handlers.text import _route_pending_flow, handle_add_meeting
from shared.pending import PendingFlowType


def _flow(description: str = "", event_type: str | None = None) -> dict:
    flow_data = {
        "title": "Spotkanie — Anna Testowa",
        "start": "2026-04-17T14:00:00+02:00",
        "end": "2026-04-17T15:00:00+02:00",
        "client_name": "Anna Testowa",
        "location": "Zatory",
        "description": description,
        "client_data": {
            "Imię i nazwisko": "Anna Testowa",
            "Miasto": "Zatory",
        },
    }
    if event_type is not None:
        flow_data["event_type"] = event_type
    return {
        "flow_type": "add_meeting",
        "flow_data": flow_data,
    }


def _update(telegram_id: int = 123) -> MagicMock:
    upd = MagicMock()
    upd.effective_user.id = telegram_id
    upd.effective_message.reply_text = AsyncMock()
    upd.effective_message.reply_markdown_v2 = AsyncMock()
    return upd


@pytest.mark.asyncio
async def test_add_meeting_augment_product_details_go_to_client_data_not_description():
    upd = _update()
    with patch("bot.handlers.text.save_pending") as mock_save:
        consumed = await _route_pending_flow(
            upd,
            MagicMock(),
            {"id": 1},
            _flow(),
            "Zużycie 4500kw, magazyn 10kw",
        )

    assert consumed is True
    mock_save.assert_called_once()
    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_type is PendingFlowType.ADD_MEETING
    assert saved_flow.flow_data["description"] == ""
    assert saved_flow.flow_data["client_data"]["Produkt"] == "Magazyn energii"
    assert saved_flow.flow_data["client_data"]["Notatki"] == "Zużycie 4500kw, magazyn 10kw"
    upd.effective_message.reply_markdown_v2.assert_awaited_once()
    assert "Anna Testowa" in upd.effective_message.reply_markdown_v2.call_args.args[0]
    assert "Dane klienta do zapisu" in upd.effective_message.reply_markdown_v2.call_args.args[0]


@pytest.mark.asyncio
async def test_add_meeting_augment_preserves_existing_description():
    upd = _update()
    with patch("bot.handlers.text.save_pending") as mock_save:
        consumed = await _route_pending_flow(
            upd,
            MagicMock(),
            {"id": 1},
            _flow("Tel: 123456789"),
            "parking pod bramą",
        )

    assert consumed is True
    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_data["description"] == (
        "Tel: 123456789\nparking pod bramą"
    )


@pytest.mark.asyncio
async def test_add_meeting_augment_preserves_event_type():
    upd = _update()
    with patch("bot.handlers.text.save_pending") as mock_save:
        consumed = await _route_pending_flow(
            upd,
            MagicMock(),
            {"id": 1},
            _flow(event_type="in_person"),
            "parking pod bramą",
        )

    assert consumed is True
    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_data["event_type"] == "in_person"


@pytest.mark.asyncio
async def test_handle_add_meeting_preserves_router_event_type():
    upd = _update()
    with patch(
        "bot.handlers.text.extract_meeting_data",
        new=AsyncMock(return_value={
            "meetings": [{
                "date": "2026-04-20",
                "time": "14:00",
                "client_name": "Anna Testowa",
                "location": "Zatory",
            }]
        }),
    ), patch(
        "bot.handlers.text._enrich_meeting",
        new=AsyncMock(return_value={
            "title": "Spotkanie — Anna Testowa",
            "location": "Zatory",
            "description": "",
            "full_name": "Anna Testowa",
            "client_found": True,
        }),
    ), patch("bot.handlers.text.check_conflicts", new=AsyncMock(return_value=[])), \
         patch("bot.handlers.text.save_pending") as mock_save:
        await handle_add_meeting(
            upd,
            MagicMock(),
            {"id": 1, "default_meeting_duration": 60},
            {"entities": {"event_type": "in_person"}},
            "spotkanie z Anną w poniedziałek o 14",
        )

    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_type is PendingFlowType.ADD_MEETING
    assert saved_flow.flow_data["event_type"] == "in_person"
