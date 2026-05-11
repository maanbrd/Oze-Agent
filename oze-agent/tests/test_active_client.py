from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest


def _lookup(status: str, clients: list[dict] | None = None):
    return SimpleNamespace(status=status, clients=clients or [])


@pytest.mark.asyncio
async def test_derive_active_client_prefers_latest_assistant_card_known_name():
    jan = {"_row": 1, "Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa"}
    history = [
        {"role": "assistant", "content": "🧾 Jan Kowalski, Warszawa"},
        {"role": "user", "content": "dodaj notatkę: zainteresowany pompą"},
    ]

    with patch("shared.active_client.get_conversation_history", return_value=history), \
         patch("shared.active_client.get_all_clients", new=AsyncMock(return_value=[jan])), \
         patch("shared.active_client.lookup_client", new=AsyncMock(return_value=_lookup("unique", [jan]))):
        from shared.active_client import derive_active_client
        result = await derive_active_client(123, "uid")

    assert result == jan


@pytest.mark.asyncio
async def test_derive_active_client_returns_none_for_ambiguous_candidate():
    jan_a = {"_row": 1, "Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa"}
    jan_b = {"_row": 2, "Imię i nazwisko": "Jan Kowalski", "Miasto": "Kraków"}
    history = [{"role": "assistant", "content": "Jan Kowalski"}]

    with patch("shared.active_client.get_conversation_history", return_value=history), \
         patch("shared.active_client.get_all_clients", new=AsyncMock(return_value=[jan_a, jan_b])), \
         patch("shared.active_client.lookup_client", new=AsyncMock(return_value=_lookup("multi", [jan_a, jan_b]))):
        from shared.active_client import derive_active_client
        result = await derive_active_client(123, "uid")

    assert result is None


@pytest.mark.asyncio
async def test_derive_active_client_returns_none_for_empty_history():
    with patch("shared.active_client.get_conversation_history", return_value=[]), \
         patch("shared.active_client.get_all_clients", new=AsyncMock()) as get_all:
        from shared.active_client import derive_active_client
        result = await derive_active_client(123, "uid")

    assert result is None
    get_all.assert_not_awaited()
