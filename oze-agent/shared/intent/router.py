"""Structured intent router using Anthropic tool use.

Entry point: `classify(message, telegram_id) -> IntentResult`.
Text / no-tool / API-error responses from the underlying wrapper all fold
to a GENERAL_QUESTION fallback.
"""

import logging
from datetime import timedelta
from typing import Optional

from shared.claude_ai import call_claude_with_tools
from shared.database import get_conversation_history

from .intents import IntentResult, IntentType, ScopeTier
from .prompts import build_router_system_prompt
from .schemas import ALL_TOOLS, FEATURE_KEY_TO_CATEGORY, TOOL_NAME_TO_INTENT

logger = logging.getLogger(__name__)

HISTORY_LIMIT = 5
HISTORY_SINCE = timedelta(minutes=30)

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
    history = get_conversation_history(
        telegram_id,
        limit=HISTORY_LIMIT,
        since=HISTORY_SINCE,
    )
    system_prompt = build_router_system_prompt(history=history)
    result = await call_claude_with_tools(
        system_prompt=system_prompt,
        user_message=message,
        tools=ALL_TOOLS,
        model_type="simple",
    )
    return _to_intent_result(result)
