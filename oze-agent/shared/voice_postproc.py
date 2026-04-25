"""Conservative Polish-name normalizer for Whisper voice transcriptions.

Whisper mangles polskie nazwiska/imiona (e.g. "Kowalsky" zamiast "Kowalski",
"Mazursky" zamiast "Mazurski"). This module post-processes the raw Whisper
output through a Claude haiku call that ONLY corrects obvious ASR errors in
Polish names — leaving cities, products, dates, phone numbers, statuses,
and inflection forms untouched.

Used by `bot/handlers/voice.py` after `transcribe_voice()` and before
showing the transcript to the user.

Public API:
    async normalize_polish_names(transcription: str) -> dict

Returns a dict that NEVER raises:
    {
        "corrected": str,
        "changes": list[tuple[str, str]],
        "cost_usd": float,
        "fallback": str | None,  # None on success, marker on any failure
    }
"""

from __future__ import annotations

import json
import logging
import re

from shared.claude_ai import call_claude

logger = logging.getLogger(__name__)


# ── Constants ────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT_PL = (
    "Jesteś korektorem polskich nazwisk i imion w transkrypcji audio.\n"
    "Popraw TYLKO oczywiste błędy ASR w polskich imionach/nazwiskach\n"
    '(np. "Kowalsky" → "Kowalski"). Resztę tekstu — miasta, produkty,\n'
    "daty, godziny, telefony, emaile, statusy, liczby, formy fleksyjne\n"
    "— zostaw bez zmian. Nie wymuszaj mianownika.\n"
    'Output: JSON {"corrected": str, "changes": [[orig, fixed], ...]}.\n'
    "Jeśli nic do poprawienia → empty changes, corrected = oryginał."
)

_MAX_TOKENS = 200

# Guard thresholds.
_OVER_LONG_RATIO = 1.5
_MAX_CHANGES_ABS = 5
_MAX_CHANGES_PER_4_WORDS = 4  # i.e. > input_word_count // 4 fails
_TOKEN_DIFF_THRESHOLD = 0.30  # >30% tokens changed → reject

# All possible fallback markers (kept centralised for tests).
FALLBACK_EMPTY_INPUT = "empty_input"
FALLBACK_EMPTY_MODEL_RESPONSE = "empty_model_response"
FALLBACK_EMPTY_CORRECTED = "empty_corrected"
FALLBACK_OVER_LONG = "over_long"
FALLBACK_TOO_MANY_CHANGES = "too_many_changes"
FALLBACK_TOO_MUCH_DIFF = "too_much_diff"
FALLBACK_JSON_INVALID = "json_invalid"
FALLBACK_API_ERROR = "api_error"


# ── Helpers ──────────────────────────────────────────────────────────────────


def _tokenize(text: str) -> list[str]:
    """Cheap tokenizer — splits on whitespace + punctuation, lowercases."""
    return [t.lower() for t in re.findall(r"\w+", text)]


def _token_diff_ratio(original: str, corrected: str) -> float:
    """Return fraction of tokens in `original` that differ from `corrected`.

    Uses set-difference of multi-set as a cheap approximation. Returns 0.0
    if `original` is empty.
    """
    orig_tokens = _tokenize(original)
    if not orig_tokens:
        return 0.0
    corr_tokens = set(_tokenize(corrected))
    differing = sum(1 for t in orig_tokens if t not in corr_tokens)
    return differing / len(orig_tokens)


def _result_with_fallback(
    transcription: str, fallback: str, cost: float = 0.0,
) -> dict:
    """Helper: build a fallback-passthrough result preserving the original."""
    return {
        "corrected": transcription,
        "changes": [],
        "cost_usd": cost,
        "fallback": fallback,
    }


def _redacted_postproc_summary(result: dict) -> dict:
    """PII-safe summary for logging / interactions table.

    NEVER includes raw transcription or change pairs. Keeps only counts,
    cost, and the fallback marker.
    """
    return {
        "changes_count": len(result.get("changes", [])),
        "postproc_applied": result.get("fallback") is None,
        "fallback": result.get("fallback"),
        "cost_usd": result.get("cost_usd", 0.0),
    }


# ── Public API ───────────────────────────────────────────────────────────────


async def normalize_polish_names(transcription: str) -> dict:
    """Conservative Polish-name normalizer for Whisper transcripts.

    Calls Claude haiku once. Applies 8 layers of guards — any failure
    returns the original transcription with a `fallback` marker so the
    caller can log the cause without exposing PII.

    Never raises.
    """
    if not transcription or not transcription.strip():
        return _result_with_fallback(transcription, FALLBACK_EMPTY_INPUT)

    try:
        response = await call_claude(
            system_prompt=_SYSTEM_PROMPT_PL,
            user_message=transcription,
            model_type="simple",  # haiku
            max_tokens=_MAX_TOKENS,
        )
    except Exception as e:  # defensive: call_claude normalnie nie rzuca
        logger.warning(
            "normalize_polish_names: unexpected exception from call_claude (%s)",
            type(e).__name__,
        )
        return _result_with_fallback(transcription, FALLBACK_API_ERROR)

    cost = response.get("cost_usd", 0.0)
    raw_text = response.get("text", "")

    # call_claude returns text="" on internal error (its own catch-all).
    if not raw_text:
        logger.info("normalize_polish_names: empty model response")
        return _result_with_fallback(transcription, FALLBACK_EMPTY_MODEL_RESPONSE, cost)

    # Parse JSON. Claude haiku may wrap in fenced code blocks — strip them.
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        # Drop optional language tag and closing fence.
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.info("normalize_polish_names: JSON parse failed")
        return _result_with_fallback(transcription, FALLBACK_JSON_INVALID, cost)

    corrected = parsed.get("corrected", "")
    changes_raw = parsed.get("changes", [])

    # Coerce changes into list of tuples; tolerant of malformed entries.
    changes: list[tuple[str, str]] = []
    for entry in changes_raw:
        if isinstance(entry, list) and len(entry) == 2:
            changes.append((str(entry[0]), str(entry[1])))

    if not corrected:
        return _result_with_fallback(transcription, FALLBACK_EMPTY_CORRECTED, cost)

    # Guard 1: over-long output (Claude inflated the text).
    if len(corrected) > _OVER_LONG_RATIO * len(transcription):
        logger.info("normalize_polish_names: over_long guard tripped")
        return _result_with_fallback(transcription, FALLBACK_OVER_LONG, cost)

    # Guard 2: too many changes (absolute or per-word ratio).
    word_count = len(_tokenize(transcription))
    max_per_ratio = max(1, word_count // _MAX_CHANGES_PER_4_WORDS)
    if len(changes) > _MAX_CHANGES_ABS or len(changes) > max_per_ratio:
        logger.info(
            "normalize_polish_names: too_many_changes (got %d, abs cap %d, ratio cap %d)",
            len(changes), _MAX_CHANGES_ABS, max_per_ratio,
        )
        return _result_with_fallback(transcription, FALLBACK_TOO_MANY_CHANGES, cost)

    # Guard 3: token-level diff ratio (catches Claude rewriting whole text).
    # Skip for short inputs (<4 tokens) — one name correction in 2-3-word
    # text would always trip the ratio. Short inputs are protected by the
    # `over_long` and `too_many_changes` guards instead.
    if word_count >= 4 and _token_diff_ratio(transcription, corrected) > _TOKEN_DIFF_THRESHOLD:
        logger.info("normalize_polish_names: too_much_diff guard tripped")
        return _result_with_fallback(transcription, FALLBACK_TOO_MUCH_DIFF, cost)

    return {
        "corrected": corrected,
        "changes": changes,
        "cost_usd": cost,
        "fallback": None,
    }
