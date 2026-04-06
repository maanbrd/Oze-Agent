"""Unit tests for shared/claude_ai.py — Anthropic API is mocked."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _make_anthropic_response(text: str, tokens_in: int = 50, tokens_out: int = 100):
    response = MagicMock()
    response.content = [MagicMock(text=text)]
    response.usage = MagicMock(input_tokens=tokens_in, output_tokens=tokens_out)
    return response


def _mock_client(text: str, **kwargs):
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(
        return_value=_make_anthropic_response(text, **kwargs)
    )
    return mock_client


# ── call_claude ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_call_claude_returns_text_and_cost():
    client = _mock_client("odpowiedź", tokens_in=100, tokens_out=200)
    with patch("shared.claude_ai.anthropic.AsyncAnthropic", return_value=client):
        from shared.claude_ai import call_claude
        result = await call_claude("system", "user", model_type="complex")

    assert result["text"] == "odpowiedź"
    assert result["tokens_in"] == 100
    assert result["tokens_out"] == 200
    assert result["cost_usd"] > 0
    assert "sonnet" in result["model"]


@pytest.mark.asyncio
async def test_call_claude_simple_uses_haiku():
    client = _mock_client("ok")
    with patch("shared.claude_ai.anthropic.AsyncAnthropic", return_value=client):
        from shared.claude_ai import call_claude
        result = await call_claude("system", "user", model_type="simple")

    assert "haiku" in result["model"]


@pytest.mark.asyncio
async def test_call_claude_returns_empty_on_api_error():
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(side_effect=Exception("API down"))
    with patch("shared.claude_ai.anthropic.AsyncAnthropic", return_value=mock_client):
        from shared.claude_ai import call_claude
        result = await call_claude("system", "user")

    assert result["text"] == ""
    assert result["cost_usd"] == 0.0


# ── model routing cost calculation ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_cost_calculation_complex_more_expensive():
    client_c = _mock_client("x", tokens_in=1000, tokens_out=1000)
    client_s = _mock_client("x", tokens_in=1000, tokens_out=1000)

    with patch("shared.claude_ai.anthropic.AsyncAnthropic", return_value=client_c):
        from shared.claude_ai import call_claude
        complex_result = await call_claude("s", "u", model_type="complex")

    with patch("shared.claude_ai.anthropic.AsyncAnthropic", return_value=client_s):
        simple_result = await call_claude("s", "u", model_type="simple")

    assert complex_result["cost_usd"] > simple_result["cost_usd"]


# ── classify_intent ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_classify_intent_returns_valid_intent():
    payload = json.dumps({"intent": "add_client", "entities": {"name": "Jan"}, "confidence": 0.95})
    client = _mock_client(payload)
    with patch("shared.claude_ai.anthropic.AsyncAnthropic", return_value=client):
        from shared.claude_ai import classify_intent
        result = await classify_intent("dodaj klienta Jana")

    assert result["intent"] == "add_client"
    assert result["entities"]["name"] == "Jan"
    assert result["confidence"] == 0.95


@pytest.mark.asyncio
async def test_classify_intent_falls_back_on_invalid_intent():
    payload = json.dumps({"intent": "INVALID_INTENT", "entities": {}, "confidence": 0.9})
    client = _mock_client(payload)
    with patch("shared.claude_ai.anthropic.AsyncAnthropic", return_value=client):
        from shared.claude_ai import classify_intent
        result = await classify_intent("coś dziwnego")

    assert result["intent"] == "general_question"


@pytest.mark.asyncio
async def test_classify_intent_falls_back_on_json_error():
    client = _mock_client("not valid json at all")
    with patch("shared.claude_ai.anthropic.AsyncAnthropic", return_value=client):
        from shared.claude_ai import classify_intent
        result = await classify_intent("test")

    assert result["intent"] == "general_question"
    assert result["confidence"] == 0.0


# ── parse_voice_note ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_parse_voice_note_returns_structured_data():
    payload = json.dumps({
        "client_data": {"Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa"},
        "missing_columns": ["Telefon"],
        "suggested_followup": {"action": "wyślij ofertę", "deadline": "", "calendar_event_title": ""},
    })
    client = _mock_client(payload)
    with patch("shared.claude_ai.anthropic.AsyncAnthropic", return_value=client):
        from shared.claude_ai import parse_voice_note
        result = await parse_voice_note("spotkałem Jana Kowalskiego z Warszawy", ["Imię i nazwisko", "Miasto", "Telefon"], "2026-04-10", 60)

    assert result["client_data"]["Imię i nazwisko"] == "Jan Kowalski"
    assert "Telefon" in result["missing_columns"]
