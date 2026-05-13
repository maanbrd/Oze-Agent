from unittest.mock import AsyncMock, patch

import pytest

from bot.handlers.text import _extract_meeting_client_data


@pytest.mark.asyncio
async def test_meeting_client_data_does_not_store_full_command_as_note_for_product_only():
    message = (
        "Zapisz w kalendarzu spotkanie na jutro na godzinę czternastą z Maciejem "
        "Miturą, adres ulica Konwaliowa 28D w Markach, numer telefonu 725-225-252, "
        "spotkanie na fotowoltaikę i magazyn energii."
    )

    with patch(
        "bot.handlers.text.extract_client_data",
        new=AsyncMock(return_value={
            "client_data": {
                "Imię i nazwisko": "Maciej Mitura",
                "Telefon": "725225252",
                "Miasto": "Marki",
                "Adres": "ul. Konwaliowa 28D",
                "Produkt": "PV + Magazyn energii",
                "Notatki": message,
            }
        }),
    ):
        data = await _extract_meeting_client_data(
            {"id": "u1", "sheet_columns": ["Imię i nazwisko", "Telefon", "Miasto", "Adres", "Produkt", "Notatki"]},
            message,
            "Maciej Mitura",
        )

    assert data["Produkt"] == "PV + Magazyn energii"
    assert "Notatki" not in data
