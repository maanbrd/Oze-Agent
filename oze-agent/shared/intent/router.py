"""Structured intent router using Anthropic tool use.

Entry point: `classify(message, telegram_id) -> IntentResult`.
Text / no-tool / API-error responses from the underlying wrapper all fold
to a GENERAL_QUESTION fallback.
"""

import logging
import re
from datetime import timedelta
from typing import Optional

from shared.claude_ai import call_claude_with_tools
from shared.database import get_conversation_history

from .intents import IntentResult, IntentType, ScopeTier
from .prompts import build_router_system_prompt
from .schemas import ALL_TOOLS, FEATURE_KEY_TO_CATEGORY, TOOL_NAME_TO_INTENT

logger = logging.getLogger(__name__)

HISTORY_LIMIT = 10
HISTORY_SINCE = timedelta(minutes=30)

# Slice 5.1d.4: deterministic preflight for meeting+client compound messages.
# When the message clearly describes a meeting/call/offer with a temporal
# marker, force record_add_meeting at the API level. This blocks the failure
# mode where rich client data (phone, address, city, product) misled Haiku
# into record_add_client and silently dropped the meeting side of the intent.
_MEETING_KEYWORD_RE = re.compile(
    r"\b(spotkani[aęeu]|spotkanie|zadzwoń|zadzwonić|oddzwoń|oddzwonić|"
    r"rozmow[ay]\s+telefoniczn\w*|telefon\s+(?:do|z)\s+[\wąćęłńóśźż-]+|"
    r"wyślij\s+ofert\w*|wysłać\s+ofert\w*|follow.?up)\b",
    re.IGNORECASE,
)
_TEMPORAL_MARKER_RE = re.compile(
    r"\b(jutro|pojutrze|dzisiaj|dziś|przyszł\w+|"
    r"godz(?:in[ąyaeę])?|o\s+\d{1,2}(?::\d{2})?|\d{1,2}:\d{2}|"
    r"(?:godzin[ąyaeę]\s+)?"
    r"(?:siódm|ósm|dziewiąt|dziesiąt|jedenast|dwunast|trzynast|czternast|"
    r"piętnast|szesnast|siedemnast|osiemnast|dziewiętnast|dwudziest)\w*)\b",
    re.IGNORECASE,
)
_ADD_CLIENT_COMMAND_RE = re.compile(
    r"\b(?:dodaj|dopisz|dodać|dodac)\s+klient[ae]?\b",
    re.IGNORECASE,
)
_NOTE_SHORTHAND_RE = re.compile(r"^\s*[^:\n]{3,100}:\s*\S.{3,}", re.IGNORECASE)
_STATUS_MARKER_RE = re.compile(
    r"\b(podpisał\w*|podpisan\w*|rezygn\w*|zamontowan\w*|umow\w*|status)\b",
    re.IGNORECASE,
)
_PIPELINE_DASHBOARD_RE = re.compile(
    r"\b(?:ilu|ile)\s+mam\s+klient\w*|"
    r"\b(?:statystyk\w*|lejek|lejka|dashboard|panel)\b",
    re.IGNORECASE,
)
_EDIT_CLIENT_RE = re.compile(
    r"\b(?:zmień|zmien|edytuj|popraw|aktualizuj)\b",
    re.IGNORECASE,
)
_RESCHEDULE_RE = re.compile(
    r"\b(?:przełóż|przeloz|przesuń|przesun)\b.*\bspotkan\w*",
    re.IGNORECASE,
)
_FREE_SLOTS_RE = re.compile(
    r"\b(?:wolne\s+(?:okna|terminy)|okna\s+w\s+kalendarzu|wolny\s+termin)\b",
    re.IGNORECASE,
)
_DELETE_CLIENT_RE = re.compile(
    r"\b(?:usuń|usun|skasuj|wykasuj)\b.*\b(?:klient\w*|baz\w*)",
    re.IGNORECASE,
)
_PRE_MEETING_REMINDER_RE = re.compile(
    r"\bprzypomn\w*\b.*\bprzed\s+spotkan\w*",
    re.IGNORECASE,
)


def _meeting_preflight_hint(message: str) -> bool:
    """True iff message contains both a meeting keyword and a temporal marker.

    When True, the classifier forces tool=record_add_meeting at the Anthropic
    API level. The Haiku model still fills the schema fields (client_name,
    date_iso, event_type, ...), it just cannot pick a different tool.

    Edge cases (intentionally NOT forced):
      - "spotkanie z Wojtkiem podpisane"     — meeting keyword, no temporal
      - "co mam jutro?"                      — temporal, no meeting keyword
      - "Dodaj klienta Jana z Warszawy"      — neither
    """
    return bool(
        _MEETING_KEYWORD_RE.search(message) and _TEMPORAL_MARKER_RE.search(message)
    )


def _add_client_preflight_hint(message: str) -> bool:
    """True for explicit add-client commands that do not carry scheduling data."""
    return bool(
        _ADD_CLIENT_COMMAND_RE.search(message)
        and not _MEETING_KEYWORD_RE.search(message)
        and not _TEMPORAL_MARKER_RE.search(message)
    )


def _add_note_preflight_hint(message: str) -> bool:
    """True for terse `Client: note` shorthand without status/meeting markers."""
    return bool(
        _NOTE_SHORTHAND_RE.search(message)
        and not _MEETING_KEYWORD_RE.search(message)
        and not _TEMPORAL_MARKER_RE.search(message)
        and not _STATUS_MARKER_RE.search(message)
    )


def _out_of_scope_preflight(message: str) -> IntentResult | None:
    """Deterministic routing for obvious non-MVP commands.

    These phrases were observed drifting through the general handler in live
    smoke tests. They do not need LLM judgment and must return the frozen R5
    banner categories.
    """
    if _PIPELINE_DASHBOARD_RE.search(message):
        return IntentResult(
            intent=IntentType.POST_MVP_ROADMAP,
            scope_tier=ScopeTier.POST_MVP_ROADMAP,
            entities={},
            confidence=1.0,
            feature_key="pipeline_dashboard",
            reason="deterministic_preflight",
        )
    if _EDIT_CLIENT_RE.search(message) and "status" not in message.lower():
        return IntentResult(
            intent=IntentType.POST_MVP_ROADMAP,
            scope_tier=ScopeTier.POST_MVP_ROADMAP,
            entities={},
            confidence=1.0,
            feature_key="edit_client",
            reason="deterministic_preflight",
        )
    if _RESCHEDULE_RE.search(message):
        return IntentResult(
            intent=IntentType.VISION_ONLY,
            scope_tier=ScopeTier.VISION_ONLY,
            entities={},
            confidence=1.0,
            feature_key="reschedule_meeting",
            reason="deterministic_preflight",
        )
    if _FREE_SLOTS_RE.search(message):
        return IntentResult(
            intent=IntentType.VISION_ONLY,
            scope_tier=ScopeTier.VISION_ONLY,
            entities={},
            confidence=1.0,
            feature_key="free_slots",
            reason="deterministic_preflight",
        )
    if _DELETE_CLIENT_RE.search(message):
        return IntentResult(
            intent=IntentType.VISION_ONLY,
            scope_tier=ScopeTier.VISION_ONLY,
            entities={},
            confidence=1.0,
            feature_key="delete_client",
            reason="deterministic_preflight",
        )
    if _PRE_MEETING_REMINDER_RE.search(message):
        return IntentResult(
            intent=IntentType.UNPLANNED,
            scope_tier=ScopeTier.UNPLANNED,
            entities={},
            confidence=1.0,
            feature_key="pre_meeting_reminders",
            reason="deterministic_preflight",
        )
    return None


_INTENT_TO_SCOPE: dict[IntentType, ScopeTier] = {
    IntentType.ADD_CLIENT: ScopeTier.MVP,
    IntentType.SHOW_CLIENT: ScopeTier.MVP,
    IntentType.ADD_NOTE: ScopeTier.MVP,
    IntentType.CHANGE_STATUS: ScopeTier.MVP,
    IntentType.ADD_MEETING: ScopeTier.MVP,
    IntentType.SHOW_DAY_PLAN: ScopeTier.MVP,
    IntentType.GENERAL_QUESTION: ScopeTier.MVP,
    IntentType.POST_MVP_ROADMAP: ScopeTier.POST_MVP_ROADMAP,
    IntentType.VISION_ONLY: ScopeTier.VISION_ONLY,
    IntentType.UNPLANNED: ScopeTier.UNPLANNED,
    IntentType.MULTI_MEETING: ScopeTier.REJECTED,
}

_CATEGORY_TO_INTENT: dict[str, IntentType] = {
    "post_mvp_roadmap": IntentType.POST_MVP_ROADMAP,
    "vision_only": IntentType.VISION_ONLY,
    "unplanned": IntentType.UNPLANNED,
}


def _fallback(model: Optional[str]) -> IntentResult:
    return IntentResult(
        intent=IntentType.GENERAL_QUESTION,
        scope_tier=ScopeTier.MVP,
        entities={},
        confidence=0.0,
        model=model,
    )


def _to_intent_result(result: dict) -> IntentResult:
    tool_name = result.get("tool_name")
    model = result.get("model")

    if not tool_name:
        return _fallback(model)

    tool_input = dict(result.get("tool_input") or {})

    if tool_name == "record_out_of_scope":
        category = tool_input.pop("category", None)
        feature_key = tool_input.pop("feature_key", None)
        details = tool_input.pop("details", None)
        intent = _CATEGORY_TO_INTENT.get(category) if category else None
        if (
            intent is None
            or feature_key is None
            or FEATURE_KEY_TO_CATEGORY.get(feature_key) != category
        ):
            return _fallback(model)
        return IntentResult(
            intent=intent,
            scope_tier=_INTENT_TO_SCOPE[intent],
            entities=tool_input,
            confidence=1.0,
            feature_key=feature_key,
            reason=details,
            model=model,
        )

    intent = TOOL_NAME_TO_INTENT.get(tool_name)
    if intent is None:
        return _fallback(model)

    reason = (
        tool_input.pop("reason", None)
        if intent == IntentType.GENERAL_QUESTION
        else None
    )
    return IntentResult(
        intent=intent,
        scope_tier=_INTENT_TO_SCOPE[intent],
        entities=tool_input,
        confidence=1.0,
        reason=reason,
        model=model,
    )


async def classify(message: str, telegram_id: int) -> IntentResult:
    preflight_result = _out_of_scope_preflight(message)
    if preflight_result is not None:
        logger.info(
            "intent classify: deterministic_preflight intent=%s feature=%s message_len=%d",
            preflight_result.intent.value,
            preflight_result.feature_key,
            len(message),
        )
        return preflight_result

    history = get_conversation_history(
        telegram_id,
        limit=HISTORY_LIMIT,
        since=HISTORY_SINCE,
    )
    system_prompt = build_router_system_prompt(history=history)
    meeting_hint = _meeting_preflight_hint(message)
    add_client_hint = _add_client_preflight_hint(message)
    add_note_hint = _add_note_preflight_hint(message)
    if meeting_hint:
        force_tool: bool | str = "record_add_meeting"
    elif add_client_hint:
        force_tool = "record_add_client"
    elif add_note_hint:
        force_tool = "record_add_note"
    else:
        force_tool = True
    result = await call_claude_with_tools(
        system_prompt=system_prompt,
        user_message=message,
        tools=ALL_TOOLS,
        model_type="simple",
        force_tool=force_tool,
    )
    logger.info(
        "intent classify: tool=%s preflight_meeting_hint=%s "
        "preflight_add_client_hint=%s preflight_add_note_hint=%s message_len=%d",
        result.get("tool_name"),
        meeting_hint,
        add_client_hint,
        add_note_hint,
        len(message),
    )
    return _to_intent_result(result)
