"""Prompt-level tests for shared.claude_ai extractors.

These tests verify the CONTENT of the system prompt sent to Claude, not the
behavior of downstream handlers. They guard against regressions in prompt
engineering that bias LLM output in unintended ways.

Background: F7b showed that a hardcoded `"duration_minutes": 60` in the JSON
template biased Claude to always return 60 for every meeting, bypassing the
event-type defaults in the handler. Per Anthropic guidance, example values in
schema templates strongly steer LLM output, so we guard the template shape
separately from handler logic.
"""

from unittest.mock import AsyncMock, patch

import pytest

from shared.claude_ai import extract_meeting_data


_STUB_RESULT = {
    "text": '{"meetings": []}',
    "tokens_in": 0,
    "tokens_out": 0,
    "cost_usd": 0.0,
}


async def _capture_meeting_prompt() -> str:
    """Invoke extract_meeting_data with a harmless input and return the
    system prompt sent to Claude."""
    with patch(
        "shared.claude_ai.call_claude",
        new=AsyncMock(return_value=_STUB_RESULT),
    ) as mock_claude:
        await extract_meeting_data("test", "2026-04-17")
    return mock_claude.call_args.args[0]


@pytest.mark.asyncio
async def test_extract_meeting_prompt_has_no_duration_60_in_template():
    """Regression guard: the hardcoded "60" bias must not return to the prompt.

    Per Anthropic prompt-engineering guidelines, example values in JSON schema
    templates act as patterns the LLM copies. `"duration_minutes": 60` in the
    schema caused F7b where every meeting got 60 min regardless of event_type.
    """
    system_prompt = await _capture_meeting_prompt()
    # Assertion 1: the exact hardcoded "60" bias must not return.
    assert '"duration_minutes": 60' not in system_prompt
    # Assertion 2 (future-proof): the JSON schema template line (first line
    # containing "meetings":) must not contain duration_minutes at all — any
    # value (0, null, 60) in template still biases LLM to always include field.
    lines = system_prompt.split("\n")
    template_line = next(l for l in lines if '"meetings":' in l and "client_name" in l)
    assert "duration_minutes" not in template_line


@pytest.mark.asyncio
async def test_extract_meeting_prompt_has_explicit_duration_instruction():
    """The prompt must instruct the LLM to include duration_minutes ONLY when
    the user explicitly mentions a duration."""
    system_prompt = await _capture_meeting_prompt()
    assert "duration_minutes" in system_prompt
    # Must contain either OPCJONALNE or TYLKO gdy — the conditional clause
    # that tells the LLM not to include this field by default.
    assert "OPCJONALNE" in system_prompt or "TYLKO gdy" in system_prompt


@pytest.mark.asyncio
async def test_extract_meeting_prompt_has_contrasting_duration_examples():
    """Per Anthropic: examples stronger than instructions, must be diverse.

    The prompt should show both a case where duration_minutes is omitted
    (phone_call with no explicit duration) and a case where it is included
    (explicit "na 30 minut").
    """
    system_prompt = await _capture_meeting_prompt()
    # Explicit duration example — "na 30 minut" → duration_minutes: 30
    assert "na 30 minut" in system_prompt
    assert '"duration_minutes": 30' in system_prompt
    # Absent-duration example — phone_call phrasing without any duration
    # phrase must show `bez duration_minutes` guidance
    assert "bez duration_minutes" in system_prompt
