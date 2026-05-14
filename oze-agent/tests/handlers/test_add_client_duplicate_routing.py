from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.handlers.text import handle_add_client
from shared.pending import PendingFlowType


def _update(telegram_id: int = 123) -> MagicMock:
    upd = MagicMock()
    upd.effective_user.id = telegram_id
    upd.effective_message.reply_text = AsyncMock()
    upd.effective_message.reply_markdown_v2 = AsyncMock()
    return upd


@pytest.mark.asyncio
async def test_add_client_same_full_name_different_known_city_creates_new_client_flow():
    upd = _update()
    new_client = {
        "Imię i nazwisko": "Adam Wysocki",
        "Miasto": "Zielonka",
        "Telefon": "501222222",
        "Produkt": "Magazyn energii",
    }
    existing_clients = [
        {
            "_row": 7,
            "Imię i nazwisko": "Adam Wysocki",
            "Miasto": "Marki",
            "Telefon": "501111111",
            "Produkt": "PV",
        },
    ]

    with patch(
        "bot.handlers.text.get_sheet_headers",
        new=AsyncMock(return_value=["Imię i nazwisko", "Telefon", "Miasto", "Produkt"]),
    ), patch(
        "bot.handlers.text.extract_client_data",
        new=AsyncMock(return_value={"client_data": new_client}),
    ), patch(
        "bot.handlers.text.get_all_clients",
        new=AsyncMock(return_value=existing_clients),
    ), patch("bot.handlers.text.save_pending") as mock_save:
        await handle_add_client(
            upd,
            MagicMock(),
            {"id": "u1"},
            {},
            "Dodaj klienta Adam Wysocki z Zielonki, telefon 501 222 222, produkt magazyn energii.",
        )

    saved_flow = mock_save.call_args.args[0]
    assert saved_flow.flow_type is PendingFlowType.ADD_CLIENT
    assert saved_flow.flow_data["client_data"]["Miasto"] == "Zielonka"

    reply = upd.effective_message.reply_text.await_args.args[0]
    assert "Adam Wysocki, Zielonka" in reply
    assert "Masz już Adam Wysocki" not in reply
