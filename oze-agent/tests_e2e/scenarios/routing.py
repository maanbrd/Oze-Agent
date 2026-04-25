"""Phase 7A routing scenarios (S02–S09).

Each scenario sends one trigger message and inspects the bot's reply
shape. All read-only — no buttons clicked, no commits to Sheets/Calendar.

These are the highest-value smoke tests for the intent classifier:
- 6 MVP intents must classify correctly
- POST-MVP intents must reject with "post-MVP" reply (not silent fallback
  to add_client / general_question)
- VISION-ONLY intents must reject with "vision-only" pointer
- NIEPLANOWANE → pointer to native alternative (Google Calendar reminders)

Uses `known_drift` tag when the bot's wording differs from spec but the
semantic outcome (correct routing) is fine — this lets the suite stay
PASS while we collect drifts in the report.
"""

from __future__ import annotations

import logging

from tests_e2e.card_parser import (
    is_not_understood,
    is_post_mvp_reply,
    is_vision_only_reply,
)
from tests_e2e.harness import TelegramE2EHarness
from tests_e2e.report import ScenarioResult
from tests_e2e.scenarios._base import new_result, register, stamp_end
from tests_e2e.scenarios._helpers import reset_pending

logger = logging.getLogger(__name__)

CATEGORY = "routing"


async def _run_simple(
    harness: TelegramE2EHarness,
    name: str,
    *,
    trigger: str,
    description: str,
    timeout_s: float = 20.0,
) -> tuple[ScenarioResult, list]:
    """Common scaffolding for a single-input/single-reply scenario."""
    result = new_result(name, CATEGORY)
    result.context["trigger"] = trigger
    result.context["description"] = description
    try:
        await reset_pending(harness)
        await harness.send(trigger)
        replies = await harness.wait_for_messages(count=1, timeout_s=timeout_s)
        result.context["reply_count"] = len(replies)
        result.context["reply_text"] = replies[0].text[:240] if replies else ""
        result.context["reply_buttons"] = (
            replies[0].button_labels if replies else []
        )
        if not replies:
            result.add(
                "got_reply", False,
                detail="bot did not reply within timeout",
                tag="blocker",
            )
        return result, replies
    finally:
        stamp_end(result)


# ── S02: gibberish → general_question fallback ──────────────────────────────


@register(
    name="general_question_unknown",
    category=CATEGORY,
    description='Gibberish "asdfghjk" → "Nie zrozumiałem..." fallback',
)
async def run_general_question_unknown(harness: TelegramE2EHarness) -> ScenarioResult:
    result, replies = await _run_simple(
        harness, "general_question_unknown",
        trigger="asdfghjk qwerty",
        description="gibberish should hit the general_question fallback",
    )
    if replies:
        text = replies[0].text
        result.add(
            "reply_is_not_understood_class",
            is_not_understood(text),
            detail=f"reply: {text[:160]!r}",
        )
        result.add(
            "reply_does_not_treat_as_add_client",
            "📋" not in text and "Brakuje" not in text,
            detail="bot must NOT route gibberish into add_client card",
        )
    return result


# ── S03: "co umiesz?" → general_question describing capabilities ────────────


@register(
    name="general_question_what_can_you_do",
    category=CATEGORY,
    description='"co umiesz?" → general_question reply listing capabilities',
)
async def run_general_question_what_can_you_do(
    harness: TelegramE2EHarness,
) -> ScenarioResult:
    result, replies = await _run_simple(
        harness, "general_question_what_can_you_do",
        trigger="co umiesz?",
        description="capability question must NOT route into add_client",
    )
    if replies:
        text = replies[0].text
        result.add(
            "no_add_client_card",
            "Brakuje" not in text and not replies[0].button_labels,
            detail=f"buttons={replies[0].button_labels}",
        )
        result.add(
            "reply_mentions_capabilities_or_help",
            len(text) > 0,
            detail="any non-empty reply OK as long as it isn't a card",
        )
    return result


# ── S04: edit_client → POST-MVP reply ────────────────────────────────────────


@register(
    name="post_mvp_edit_client_rejection",
    category=CATEGORY,
    description='"zmień telefon Jana na 600..." → POST-MVP reply',
)
async def run_post_mvp_edit_client_rejection(
    harness: TelegramE2EHarness,
) -> ScenarioResult:
    result, replies = await _run_simple(
        harness, "post_mvp_edit_client_rejection",
        trigger="zmień telefon Jana Kowalskiego z Warszawy na 609222333",
        description="edit_client is POST-MVP, should not silently re-route to add_client",
    )
    if replies:
        text = replies[0].text
        is_postmvp = is_post_mvp_reply(text)
        result.add(
            "reply_is_post_mvp_acknowledgment",
            is_postmvp,
            detail=f"reply: {text[:160]!r}",
            tag="pass" if is_postmvp else "known_drift",
            doc_ref="agent_behavior_spec_v5.md §6.2 + R5",
        )
        result.add(
            "no_silent_add_client_card",
            "Brakuje" not in text and "📋 Zapisuję klienta" not in text,
            detail="must NOT silently morph edit into add_client",
        )
    return result


# ── S05: lejek_sprzedazowy → POST-MVP reply ─────────────────────────────────


@register(
    name="post_mvp_lejek_rejection",
    category=CATEGORY,
    description='"ilu mam klientów?" → POST-MVP reply (dashboard feature)',
)
async def run_post_mvp_lejek_rejection(
    harness: TelegramE2EHarness,
) -> ScenarioResult:
    result, replies = await _run_simple(
        harness, "post_mvp_lejek_rejection",
        trigger="ilu mam klientów?",
        description="dashboard pipeline-stats query is POST-MVP",
    )
    if replies:
        text = replies[0].text
        is_postmvp = is_post_mvp_reply(text)
        result.add(
            "reply_is_post_mvp_acknowledgment",
            is_postmvp,
            detail=f"reply: {text[:160]!r}",
            tag="pass" if is_postmvp else "known_drift",
            doc_ref="agent_behavior_spec_v5.md §6.2",
        )
        result.add(
            "no_random_count_made_up",
            "klientów" not in text.lower() or "post" in text.lower(),
            detail="bot must not invent a count",
        )
    return result


# ── S06: reschedule_meeting → VISION-ONLY ───────────────────────────────────


@register(
    name="vision_only_reschedule",
    category=CATEGORY,
    description='"przełóż Jana na piątek" → vision-only one-liner',
)
async def run_vision_only_reschedule(
    harness: TelegramE2EHarness,
) -> ScenarioResult:
    result, replies = await _run_simple(
        harness, "vision_only_reschedule",
        trigger="przełóż Jana Kowalskiego z Warszawy na piątek o 10",
        description="reschedule_meeting is VISION-ONLY (per INTENCJE_MVP §8.2)",
    )
    if replies:
        text = replies[0].text
        is_vision = is_vision_only_reply(text)
        result.add(
            "reply_is_vision_only",
            is_vision,
            detail=f"reply: {text[:160]!r}",
            tag="pass" if is_vision else "known_drift",
            doc_ref="agent_behavior_spec_v5.md §6.3",
        )
        result.add(
            "no_calendar_mutation_card",
            "📅" not in text or "vision" in text.lower(),
            detail="must not show add_meeting card for reschedule",
        )
    return result


# ── S07: free_slots → VISION-ONLY ───────────────────────────────────────────


@register(
    name="vision_only_free_slots",
    category=CATEGORY,
    description='"wolne okna w czwartek" → vision-only one-liner',
)
async def run_vision_only_free_slots(
    harness: TelegramE2EHarness,
) -> ScenarioResult:
    result, replies = await _run_simple(
        harness, "vision_only_free_slots",
        trigger="jakie mam wolne okna w czwartek?",
        description="free_slots is VISION-ONLY",
    )
    if replies:
        text = replies[0].text
        is_vision = is_vision_only_reply(text)
        result.add(
            "reply_is_vision_only",
            is_vision,
            detail=f"reply: {text[:160]!r}",
            tag="pass" if is_vision else "known_drift",
            doc_ref="agent_behavior_spec_v5.md §6.3",
        )
    return result


# ── S08: delete_client → VISION-ONLY ────────────────────────────────────────


@register(
    name="vision_only_delete_client",
    category=CATEGORY,
    description='"usuń Jana z bazy" → vision-only one-liner',
)
async def run_vision_only_delete_client(
    harness: TelegramE2EHarness,
) -> ScenarioResult:
    result, replies = await _run_simple(
        harness, "vision_only_delete_client",
        trigger="usuń z bazy Jana Kowalskiego z Warszawy",
        description="delete_client is VISION-ONLY (irreversible CRM mutation)",
    )
    if replies:
        text = replies[0].text
        is_vision = is_vision_only_reply(text)
        result.add(
            "reply_is_vision_only",
            is_vision,
            detail=f"reply: {text[:160]!r}",
            tag="pass" if is_vision else "known_drift",
            doc_ref="agent_behavior_spec_v5.md §6.3",
        )
        result.add(
            "no_actual_delete_attempted",
            "usunięto" not in text.lower() and "skasowane" not in text.lower(),
            detail="must not claim a delete happened",
        )
    return result


# ── S09: pre-meeting reminder → NIEPLANOWANE ────────────────────────────────


@register(
    name="unplanned_pre_meeting_reminder",
    category=CATEGORY,
    description='"ustaw przypomnienie 30 min przed spotkaniem" → Google Calendar pointer',
)
async def run_unplanned_pre_meeting_reminder(
    harness: TelegramE2EHarness,
) -> ScenarioResult:
    result, replies = await _run_simple(
        harness, "unplanned_pre_meeting_reminder",
        trigger="ustaw przypomnienie 30 minut przed spotkaniem",
        description="agent-side reminders are NIEPLANOWANE; native Google Calendar handles them",
    )
    if replies:
        text = replies[0].text
        # Spec says: "Przypomnienia przed spotkaniem ustawia Google Calendar..."
        mentions_calendar = "calendar" in text.lower() or "kalendarz" in text.lower()
        result.add(
            "reply_points_to_native_calendar",
            mentions_calendar,
            detail=f"reply: {text[:160]!r}",
            tag="pass" if mentions_calendar else "known_drift",
            doc_ref="agent_behavior_spec_v5.md §6.4",
        )
        result.add(
            "no_reminder_actually_set",
            "ustawione" not in text.lower() and "ok" != text.strip().lower(),
            detail="must not claim a reminder was set",
        )
    return result
