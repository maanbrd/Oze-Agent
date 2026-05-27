from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_extract_voice_fields_forces_structured_tool_and_normalizes_output():
    with patch(
        "shared.voice_extraction.call_claude_with_tools",
        new=AsyncMock(return_value={
            "tool_name": "extract_voice_fields",
            "tool_input": {
                "intent": "add_meeting",
                "name": "Jan Kowalski",
                "city": "Warszawa",
                "phone": "600 100 200",
                "email": "jan.kowalski małpa gmail kropka com",
                "date": "2026-05-28",
                "time": "14:00",
                "product_or_next_action": "PV + Magazyn energii",
            },
            "tokens_in": 120,
            "tokens_out": 40,
            "cost_usd": 0.00025,
            "model": "claude-haiku-4-5-20251001",
        }),
    ) as mock_call:
        from shared.voice_extraction import extract_voice_fields

        result = await extract_voice_fields(
            "Dodaj spotkanie z Janem Kowalskim jutro o 14 w Warszawie. "
            "Telefon 600 100 200, PV i magazyn energii."
        )

    assert result["fields"] == {
        "intent": "add_meeting",
        "name": "Jan Kowalski",
        "city": "Warszawa",
        "phone": "600100200",
        "email": "jan.kowalski@gmail.com",
        "date": "2026-05-28",
        "time": "14:00",
        "product_or_next_action": "PV + Magazyn energii",
    }
    assert result["fallback"] is None
    assert result["cost_usd"] == 0.00025
    assert result["model"] == "claude-haiku-4-5-20251001"
    assert mock_call.await_args.kwargs["model_type"] == "simple"
    assert mock_call.await_args.kwargs["force_tool"] == "extract_voice_fields"


@pytest.mark.asyncio
async def test_extract_voice_fields_returns_fallback_when_model_does_not_call_tool():
    with patch(
        "shared.voice_extraction.call_claude_with_tools",
        new=AsyncMock(return_value={
            "tool_name": None,
            "tool_input": {},
            "tokens_in": 0,
            "tokens_out": 0,
            "cost_usd": 0.0,
            "model": "claude-haiku-4-5-20251001",
        }),
    ):
        from shared.voice_extraction import extract_voice_fields

        result = await extract_voice_fields("niezrozumiały tekst")

    assert result["fields"] == {}
    assert result["fallback"] == "no_tool"


@pytest.mark.asyncio
async def test_extract_voice_fields_skips_empty_input():
    from shared.voice_extraction import extract_voice_fields

    result = await extract_voice_fields("  ")

    assert result["fields"] == {}
    assert result["fallback"] == "empty_input"


@pytest.mark.asyncio
async def test_extract_voice_fields_normalizes_spoken_polish_phone_and_email():
    with patch(
        "shared.voice_extraction.call_claude_with_tools",
        new=AsyncMock(return_value={
            "tool_name": "extract_voice_fields",
            "tool_input": {
                "intent": "add_client",
                "phone": "sześćset sto dwieście",
                "email": "maciej kropka mitura małpa gmail kropka com",
            },
            "tokens_in": 90,
            "tokens_out": 25,
            "cost_usd": 0.0002,
            "model": "claude-haiku-4-5-20251001",
        }),
    ):
        from shared.voice_extraction import extract_voice_fields

        result = await extract_voice_fields(
            "Dodaj klienta. Telefon sześćset sto dwieście. "
            "Email maciej kropka mitura małpa gmail kropka com."
        )

    assert result["fields"]["phone"] == "600100200"
    assert result["fields"]["email"] == "maciej.mitura@gmail.com"
