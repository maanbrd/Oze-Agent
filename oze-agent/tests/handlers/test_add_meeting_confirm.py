"""Confirmation tests for add_meeting with carried client data."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.handlers.text import handle_confirm
from shared.pending import PendingFlowType


def _update(telegram_id: int = 123) -> MagicMock:
    upd = MagicMock()
    upd.effective_user.id = telegram_id
    upd.effective_message.reply_text = AsyncMock()
    upd.effective_message.reply_markdown_v2 = AsyncMock()
    return upd


@pytest.mark.asyncio
async def test_add_meeting_confirm_offers_add_client_with_carried_client_data():
    flow_data = {
        "title": "Spotkanie - Jurek Jurecki",
        "start": "2026-04-17T11:00:00+02:00",
        "end": "2026-04-17T12:00:00+02:00",
        "client_name": "Jurek Jurecki",
        "location": "Warszawa",
        "description": "",
        "client_data": {
            "Imię i nazwisko": "Jurek Jurecki",
            "Telefon": "746938764",
            "Produkt": "Magazyn energii",
            "Notatki": "Zużycie 4500kw, magazyn 10kw",
        },
    }
    upd = _update()

    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value={"flow_type": "add_meeting", "flow_data": flow_data},
    ), patch(
        "bot.handlers.text.create_event",
        new=AsyncMock(return_value={"id": "event-1"}),
    ), patch(
        "bot.handlers.text.search_clients",
        new=AsyncMock(return_value=[]),
    ), patch("bot.handlers.text.save_pending") as mock_save, patch(
        "bot.handlers.text.delete_pending_flow"
    ) as mock_delete:
        await handle_confirm(
            upd,
            MagicMock(),
            {"id": 1, "sheet_columns": ["Imię i nazwisko", "Telefon", "Produkt", "Notatki"]},
            {},
            "",
        )

    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_type is PendingFlowType.ADD_CLIENT
    assert saved_flow.flow_data["client_data"]["Telefon"] == "746938764"
    assert saved_flow.flow_data["client_data"]["Produkt"] == "Magazyn energii"
    assert saved_flow.flow_data["client_data"]["Notatki"] == "Zużycie 4500kw, magazyn 10kw"
    mock_delete.assert_not_called()
    response = upd.effective_message.reply_text.call_args.args[0]
    assert "Spotkanie dodane" in response
    assert "Tel. 746 938 764" in response
    assert "Magazyn energii" in response
    assert "Zużycie 4500kw, magazyn 10kw" in response
