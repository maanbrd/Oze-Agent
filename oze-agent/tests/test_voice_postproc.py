"""Unit tests for shared.voice_postproc.

Mocks `shared.claude_ai.call_claude` so tests run without Anthropic API.
Each guard layer has at least one positive + one negative test.
"""

from unittest.mock import AsyncMock, patch

import pytest

from shared.voice_postproc import (
    FALLBACK_API_ERROR,
    FALLBACK_EMPTY_CORRECTED,
    FALLBACK_EMPTY_INPUT,
    FALLBACK_EMPTY_MODEL_RESPONSE,
    FALLBACK_JSON_INVALID,
    FALLBACK_OVER_LONG,
    FALLBACK_TOO_MANY_CHANGES,
    FALLBACK_TOO_MUCH_DIFF,
    _redacted_postproc_summary,
    normalize_polish_names,
)


def _claude_response(text: str, cost: float = 0.0001) -> dict:
    """Helper: shape that real call_claude returns."""
    return {
        "text": text,
        "tokens_in": 30,
        "tokens_out": 30,
        "cost_usd": cost,
        "model": "claude-haiku-4-5-20251001",
    }


def _claude_json_response(corrected: str, changes: list, cost: float = 0.0001) -> dict:
    import json
    payload = {"corrected": corrected, "changes": changes}
    return _claude_response(json.dumps(payload), cost)


# ── Happy path ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_normalize_corrects_polish_surname():
    """Most common case: Whisper writes 'Kowalsky', haiku corrects to 'Kowalski'."""
    fake = _claude_json_response(
        "spotkanie z Janem Kowalski jutro o 14",
        [["Kowalsky", "Kowalski"]],
    )
    with patch("shared.voice_postproc.call_claude", new=AsyncMock(return_value=fake)):
        result = await normalize_polish_names("spotkanie z Janem Kowalsky jutro o 14")
    assert result["fallback"] is None
    assert "Kowalski" in result["corrected"]
    assert "Kowalsky" not in result["corrected"]
    assert result["changes"] == [("Kowalsky", "Kowalski")]
    assert result["cost_usd"] == 0.0001


@pytest.mark.asyncio
async def test_normalize_no_change_when_input_clean():
    """Input bez polskich nazwisk → empty changes, corrected = original."""
    text = "co mam dzisiaj?"
    fake = _claude_json_response(text, [])
    with patch("shared.voice_postproc.call_claude", new=AsyncMock(return_value=fake)):
        result = await normalize_polish_names(text)
    assert result["fallback"] is None
    assert result["corrected"] == text
    assert result["changes"] == []


@pytest.mark.asyncio
async def test_normalize_strips_fenced_code_block_from_haiku():
    """Haiku może opakować JSON w ```json ... ``` — postproc to obsługuje."""
    import json
    payload = json.dumps({"corrected": "Jan Kowalski", "changes": [["Kowalsky", "Kowalski"]]})
    fenced = f"```json\n{payload}\n```"
    fake = _claude_response(fenced)
    with patch("shared.voice_postproc.call_claude", new=AsyncMock(return_value=fake)):
        result = await normalize_polish_names("Jan Kowalsky")
    assert result["fallback"] is None
    assert result["corrected"] == "Jan Kowalski"


@pytest.mark.asyncio
async def test_normalize_strips_bare_fenced_block():
    """``` (no language) wrapping also handled."""
    import json
    payload = json.dumps({"corrected": "Jan Kowalski", "changes": []})
    fenced = f"```\n{payload}\n```"
    fake = _claude_response(fenced)
    with patch("shared.voice_postproc.call_claude", new=AsyncMock(return_value=fake)):
        result = await normalize_polish_names("Jan Kowalski")
    assert result["fallback"] is None


# ── Conservative behaviour: must NOT touch non-name fields ─────────────────


@pytest.mark.asyncio
async def test_normalize_preserves_phone_number():
    """Phone numbers are NOT names — must pass through unchanged."""
    text = "telefon 600100200"
    fake = _claude_json_response(text, [])  # haiku correctly returns no change
    with patch("shared.voice_postproc.call_claude", new=AsyncMock(return_value=fake)):
        result = await normalize_polish_names(text)
    assert result["corrected"] == text


@pytest.mark.asyncio
async def test_normalize_preserves_dates_and_times():
    """Date/time strings should not be mangled."""
    text = "spotkanie jutro o 14:00 25.04.2026"
    fake = _claude_json_response(text, [])
    with patch("shared.voice_postproc.call_claude", new=AsyncMock(return_value=fake)):
        result = await normalize_polish_names(text)
    assert result["corrected"] == text


@pytest.mark.asyncio
async def test_normalize_preserves_inflection():
    """'z Janem Kowalskim' (instrumental) must NOT be forced to nominative."""
    text = "umowa z Janem Kowalskim z Warszawy"
    # Haiku correctly leaves the inflection alone (only spell-fixes if needed).
    fake = _claude_json_response(text, [])
    with patch("shared.voice_postproc.call_claude", new=AsyncMock(return_value=fake)):
        result = await normalize_polish_names(text)
    assert result["fallback"] is None
    assert "Janem Kowalskim" in result["corrected"]


@pytest.mark.asyncio
async def test_normalize_preserves_city_and_product():
    text = "klient z Warszawy chce PV i pompę ciepła"
    fake = _claude_json_response(text, [])
    with patch("shared.voice_postproc.call_claude", new=AsyncMock(return_value=fake)):
        result = await normalize_polish_names(text)
    assert result["corrected"] == text


# ── Empty / null inputs ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_empty_input_skips_call_returns_fallback():
    """Empty input → no Claude call, FALLBACK_EMPTY_INPUT returned."""
    mock_call = AsyncMock()
    with patch("shared.voice_postproc.call_claude", new=mock_call):
        result = await normalize_polish_names("")
    assert result["fallback"] == FALLBACK_EMPTY_INPUT
    assert result["corrected"] == ""
    assert mock_call.await_count == 0  # no API call wasted


@pytest.mark.asyncio
async def test_whitespace_only_input_skips_call():
    mock_call = AsyncMock()
    with patch("shared.voice_postproc.call_claude", new=mock_call):
        result = await normalize_polish_names("   \n\t  ")
    assert result["fallback"] == FALLBACK_EMPTY_INPUT
    assert mock_call.await_count == 0


# ── call_claude empty-text semantics (NOT exception) ───────────────────────


@pytest.mark.asyncio
async def test_empty_model_response_falls_back():
    """call_claude returns text='' on internal API error — must hit
    FALLBACK_EMPTY_MODEL_RESPONSE, NOT FALLBACK_API_ERROR."""
    fake = {"text": "", "tokens_in": 0, "tokens_out": 0, "cost_usd": 0.0, "model": "haiku"}
    with patch("shared.voice_postproc.call_claude", new=AsyncMock(return_value=fake)):
        result = await normalize_polish_names("Jan Kowalski")
    assert result["fallback"] == FALLBACK_EMPTY_MODEL_RESPONSE
    assert result["corrected"] == "Jan Kowalski"  # original preserved


@pytest.mark.asyncio
async def test_actual_exception_falls_back_to_api_error():
    """Defensive coverage: if call_claude DID raise (not its current behaviour),
    we'd catch it as FALLBACK_API_ERROR."""
    raising = AsyncMock(side_effect=RuntimeError("network down"))
    with patch("shared.voice_postproc.call_claude", new=raising):
        result = await normalize_polish_names("Jan Kowalski")
    assert result["fallback"] == FALLBACK_API_ERROR
    assert result["corrected"] == "Jan Kowalski"


# ── JSON parsing failures ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_invalid_json_falls_back():
    fake = _claude_response("this is not JSON at all")
    with patch("shared.voice_postproc.call_claude", new=AsyncMock(return_value=fake)):
        result = await normalize_polish_names("Jan Kowalski")
    assert result["fallback"] == FALLBACK_JSON_INVALID
    assert result["corrected"] == "Jan Kowalski"


@pytest.mark.asyncio
async def test_partial_json_falls_back():
    fake = _claude_response('{"corrected": "Jan", "changes": [')  # truncated
    with patch("shared.voice_postproc.call_claude", new=AsyncMock(return_value=fake)):
        result = await normalize_polish_names("Jan Kowalski")
    assert result["fallback"] == FALLBACK_JSON_INVALID


@pytest.mark.asyncio
async def test_empty_corrected_in_json_falls_back():
    """Valid JSON but empty 'corrected' field → safe fallback to original."""
    fake = _claude_json_response("", [])
    with patch("shared.voice_postproc.call_claude", new=AsyncMock(return_value=fake)):
        result = await normalize_polish_names("Jan Kowalski")
    assert result["fallback"] == FALLBACK_EMPTY_CORRECTED


@pytest.mark.asyncio
async def test_missing_corrected_key_falls_back():
    """JSON without 'corrected' key → empty_corrected fallback."""
    fake = _claude_response('{"changes": []}')
    with patch("shared.voice_postproc.call_claude", new=AsyncMock(return_value=fake)):
        result = await normalize_polish_names("Jan Kowalski")
    assert result["fallback"] == FALLBACK_EMPTY_CORRECTED


# ── Over-edit guards ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_over_long_output_falls_back():
    """If Claude inflates output >1.5x input length → reject."""
    short_input = "Jan"
    long_corrected = "Jan Kowalski Mazursky Wiśniewski Nowak Kowalczyk Wójcik"
    fake = _claude_json_response(long_corrected, [["Jan", "Jan Kowalski"]])
    with patch("shared.voice_postproc.call_claude", new=AsyncMock(return_value=fake)):
        result = await normalize_polish_names(short_input)
    assert result["fallback"] == FALLBACK_OVER_LONG
    assert result["corrected"] == short_input  # original returned


@pytest.mark.asyncio
async def test_too_many_changes_falls_back():
    """If Claude reports >5 changes → reject (likely over-eager rewrite)."""
    text = "Jan Kowalski Maria Nowak Adam Wójcik z Warszawy z Krakowa"
    changes = [
        ["Jan", "JanX"], ["Kowalski", "KowalskiX"], ["Maria", "MariaX"],
        ["Nowak", "NowakX"], ["Adam", "AdamX"], ["Wójcik", "WójcikX"],
    ]  # 6 changes > 5
    fake = _claude_json_response(text, changes)
    with patch("shared.voice_postproc.call_claude", new=AsyncMock(return_value=fake)):
        result = await normalize_polish_names(text)
    assert result["fallback"] == FALLBACK_TOO_MANY_CHANGES


@pytest.mark.asyncio
async def test_too_many_changes_per_words_ratio_falls_back():
    """For short input (e.g. 3 words), even 2 changes trips the ratio cap."""
    short = "Jan Kowalsky Mazursky"  # 3 words → ratio cap = max(1, 3//4)=1
    changes = [["Kowalsky", "Kowalski"], ["Mazursky", "Mazurski"]]  # 2 > 1
    fake = _claude_json_response("Jan Kowalski Mazurski", changes)
    with patch("shared.voice_postproc.call_claude", new=AsyncMock(return_value=fake)):
        result = await normalize_polish_names(short)
    assert result["fallback"] == FALLBACK_TOO_MANY_CHANGES


@pytest.mark.asyncio
async def test_too_much_token_diff_falls_back():
    """If >30% tokens differ from input → reject (Claude rewrote, not corrected).

    Use input + output of similar length so over_long doesn't fire first.
    Need ≥4 input tokens (short-input bypass kicks in below that).
    """
    text = "ala ma kota psa raz"  # 5 tokens, 19 chars
    rewrite = "Jan ma psa raz dom"  # 5 tokens, 18 chars (no over_long)
    # Input tokens: {ala, ma, kota, psa, raz}
    # Output set:   {jan, ma, psa, raz, dom}
    # Differing in input: ala, kota → 2/5 = 0.4 > 0.30 threshold
    fake = _claude_json_response(rewrite, [])
    with patch("shared.voice_postproc.call_claude", new=AsyncMock(return_value=fake)):
        result = await normalize_polish_names(text)
    assert result["fallback"] == FALLBACK_TOO_MUCH_DIFF
    assert result["corrected"] == text


@pytest.mark.asyncio
async def test_short_input_skips_token_diff_guard():
    """For input with <4 tokens, the token-diff guard is skipped — short
    inputs would always trip the ratio when ANY name fix happens."""
    text = "Jan Kowalsky"  # 2 tokens
    corrected = "Jan Kowalski"  # 1/2 = 50% diff but should still pass
    fake = _claude_json_response(corrected, [["Kowalsky", "Kowalski"]])
    with patch("shared.voice_postproc.call_claude", new=AsyncMock(return_value=fake)):
        result = await normalize_polish_names(text)
    assert result["fallback"] is None
    assert result["corrected"] == "Jan Kowalski"


@pytest.mark.asyncio
async def test_minor_token_diff_passes():
    """Single-name fix (e.g. Kowalsky → Kowalski) tokenwise barely differs → pass."""
    text = "spotkanie z Janem Kowalsky jutro o 14"
    corrected = "spotkanie z Janem Kowalski jutro o 14"
    fake = _claude_json_response(corrected, [["Kowalsky", "Kowalski"]])
    with patch("shared.voice_postproc.call_claude", new=AsyncMock(return_value=fake)):
        result = await normalize_polish_names(text)
    assert result["fallback"] is None


# ── Malformed changes list ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_malformed_changes_entries_skipped():
    """Changes list with bad entries should still parse, dropping invalid ones."""
    fake = _claude_response(
        '{"corrected": "Jan Kowalski", "changes": [["Kowalsky", "Kowalski"], '
        '["only one"], "not-a-list", ["a", "b", "c"]]}'
    )
    with patch("shared.voice_postproc.call_claude", new=AsyncMock(return_value=fake)):
        result = await normalize_polish_names("Jan Kowalsky")
    assert result["fallback"] is None
    # Only the well-formed pair should survive.
    assert result["changes"] == [("Kowalsky", "Kowalski")]


# ── PII-safe summary helper ────────────────────────────────────────────────


def test_redacted_summary_excludes_transcript_and_changes():
    """The summary must never include raw text or change pairs."""
    full_result = {
        "corrected": "Jan Kowalski mieszka w Warszawie, tel 600100200",
        "changes": [("Kowalsky", "Kowalski")],
        "cost_usd": 0.0002,
        "fallback": None,
    }
    summary = _redacted_postproc_summary(full_result)
    # PII redaction: NO raw text, NO change pairs.
    serialized = str(summary)
    assert "Kowalski" not in serialized
    assert "Kowalsky" not in serialized
    assert "Warszawie" not in serialized
    assert "600100200" not in serialized
    # But safe fields are present.
    assert summary["changes_count"] == 1
    assert summary["postproc_applied"] is True
    assert summary["fallback"] is None
    assert summary["cost_usd"] == 0.0002


def test_redacted_summary_marks_fallback_correctly():
    full_result = {
        "corrected": "original raw text",
        "changes": [],
        "cost_usd": 0.0,
        "fallback": FALLBACK_EMPTY_MODEL_RESPONSE,
    }
    summary = _redacted_postproc_summary(full_result)
    assert summary["postproc_applied"] is False
    assert summary["fallback"] == FALLBACK_EMPTY_MODEL_RESPONSE
    assert summary["changes_count"] == 0


def test_redacted_summary_handles_minimal_dict():
    """Defensive: missing keys default sensibly."""
    summary = _redacted_postproc_summary({})
    assert summary["changes_count"] == 0
    assert summary["postproc_applied"] is True  # no fallback → applied
    assert summary["fallback"] is None
    assert summary["cost_usd"] == 0.0


# ── Cost tracking ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cost_propagated_from_claude_response():
    fake = _claude_json_response("Jan Kowalski", [["Kowalsky", "Kowalski"]], cost=0.00042)
    with patch("shared.voice_postproc.call_claude", new=AsyncMock(return_value=fake)):
        result = await normalize_polish_names("Jan Kowalsky")
    assert result["cost_usd"] == 0.00042


@pytest.mark.asyncio
async def test_cost_recorded_even_on_fallback():
    """When haiku call cost something but result was rejected, log the cost."""
    bad = _claude_response("not json", cost=0.0001)
    with patch("shared.voice_postproc.call_claude", new=AsyncMock(return_value=bad)):
        result = await normalize_polish_names("Jan Kowalski")
    assert result["fallback"] == FALLBACK_JSON_INVALID
    assert result["cost_usd"] == 0.0001  # cost preserved despite fallback
