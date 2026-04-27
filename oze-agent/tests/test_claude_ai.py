"""Unit tests for shared/claude_ai.py — Anthropic API is mocked."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _make_anthropic_response(text: str, tokens_in: int = 50, tokens_out: int = 100):
    response = MagicMock()
    response.content = [MagicMock(text=text)]
    response.usage = MagicMock(input_tokens=tokens_in, output_tokens=tokens_out)
    return response


def _make_tool_response(tool_name: str, tool_input: dict):
    block = MagicMock()
    block.type = "tool_use"
    block.name = tool_name
    block.input = tool_input
    response = MagicMock()
    response.content = [block]
    response.usage = MagicMock(input_tokens=50, output_tokens=100)
    return response


def _mock_client(text: str, **kwargs):
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(
        return_value=_make_anthropic_response(text, **kwargs)
    )
    return mock_client


def _mock_tool_client(tool_name: str, tool_input: dict):
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(
        return_value=_make_tool_response(tool_name, tool_input)
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


@pytest.mark.asyncio
async def test_call_claude_normalizes_unicode_line_separators():
    client = _mock_client("ok")
    with patch("shared.claude_ai.anthropic.AsyncAnthropic", return_value=client):
        from shared.claude_ai import call_claude
        await call_claude("sys\u2028tem", "u\u2029ser", model_type="simple")

    kwargs = client.messages.create.call_args.kwargs
    assert kwargs["system"] == "sys\ntem"
    assert kwargs["messages"] == [{"role": "user", "content": "u\nser"}]


@pytest.mark.asyncio
async def test_call_claude_strips_anthropic_api_key():
    client = _mock_client("ok")
    with patch("shared.claude_ai.Config.ANTHROPIC_API_KEY", "sk-test\u2028"), \
         patch("shared.claude_ai.anthropic.AsyncAnthropic", return_value=client) as mock_anthropic:
        from shared.claude_ai import call_claude
        await call_claude("system", "user", model_type="simple")

    mock_anthropic.assert_called_once_with(api_key="sk-test")


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


# ── call_claude_with_tools ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_call_claude_with_tools_force_tool_sets_tool_choice():
    client = _mock_tool_client("record_general_question", {"reason": "test"})
    with patch("shared.claude_ai.anthropic.AsyncAnthropic", return_value=client):
        from shared.claude_ai import call_claude_with_tools
        result = await call_claude_with_tools(
            "system",
            "user",
            [{"name": "record_general_question", "input_schema": {"type": "object"}}],
            model_type="simple",
            force_tool=True,
        )

    kwargs = client.messages.create.call_args.kwargs
    assert kwargs["tool_choice"] == {"type": "any"}
    assert result["tool_name"] == "record_general_question"


@pytest.mark.asyncio
async def test_call_claude_with_tools_force_specific_tool_sets_tool_choice_name():
    client = _mock_tool_client("record_add_meeting", {"client_name": "Jan"})
    with patch("shared.claude_ai.anthropic.AsyncAnthropic", return_value=client):
        from shared.claude_ai import call_claude_with_tools
        result = await call_claude_with_tools(
            "system",
            "user",
            [{"name": "record_add_meeting", "input_schema": {"type": "object"}}],
            model_type="simple",
            force_tool="record_add_meeting",
        )

    kwargs = client.messages.create.call_args.kwargs
    assert kwargs["tool_choice"] == {"type": "tool", "name": "record_add_meeting"}
    assert result["tool_name"] == "record_add_meeting"


@pytest.mark.asyncio
async def test_call_claude_with_tools_normalizes_unicode_line_separators():
    client = _mock_tool_client("record_general_question", {"reason": "test"})
    with patch("shared.claude_ai.anthropic.AsyncAnthropic", return_value=client):
        from shared.claude_ai import call_claude_with_tools
        await call_claude_with_tools(
            "sys\u2028tem",
            "u\u2029ser",
            [{"name": "record_general_question", "input_schema": {"type": "object"}}],
            model_type="simple",
            force_tool=True,
        )

    kwargs = client.messages.create.call_args.kwargs
    assert kwargs["system"] == "sys\ntem"
    assert kwargs["messages"] == [{"role": "user", "content": "u\nser"}]


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
