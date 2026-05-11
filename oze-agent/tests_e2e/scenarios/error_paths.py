"""Phase 7A error-path scenarios (S14, S15)."""

from __future__ import annotations

import logging

from tests_e2e.card_parser import is_not_found
from tests_e2e.harness import TelegramE2EHarness
from tests_e2e.report import ScenarioResult
from tests_e2e.scenarios._base import new_result, register, stamp_end
from tests_e2e.scenarios._helpers import (
    E2E_BETA_CITY,
    e2e_beta_name,
    reset_pending,
)

logger = logging.getLogger(__name__)

CATEGORY = "error_path"


# ── S14: change_status against non-existent client ──────────────────────────


@register(
    name="change_status_invalid_client",
    category=CATEGORY,
    description=(
        "Change status for a client that does not exist + invalid status name. "
        "Expect a 'not found'-class reply, no card, no commit."
    ),
)
async def run_change_status_invalid_client(
    harness: TelegramE2EHarness,
) -> ScenarioResult:
    result = new_result("change_status_invalid_client", CATEGORY)
    name = e2e_beta_name("CS-invalid")
    trigger = f"zmień status {name} z {E2E_BETA_CITY} na FoobarStatusNotInEnum"
    result.context["trigger"] = trigger
    try:
        await reset_pending(harness)
        await harness.send(trigger)
        replies = await harness.wait_for_messages(count=2, timeout_s=20.0)
        result.context["reply_count"] = len(replies)
        result.context["reply_texts"] = [m.text[:120] for m in replies]

        if not replies:
            result.add(
                "got_reply", False,
                detail="no reply within 20s",
                tag="blocker",
            )
            return result

        # Should be either "Nie znalazłem" (client doesn't exist) or an
        # invalid-status error ("nieprawidłowy status / nie znam / nieznany").
        # Either way, NO mutation card.
        any_msg = replies[-1]
        text_lo = any_msg.text.lower()
        not_found_or_invalid = (
            is_not_found(any_msg.text)
            or "nie znam" in text_lo
            or "nieznany" in text_lo
            or "nieprawidłowy" in text_lo
        )
        result.add(
            "reply_is_error_class",
            not_found_or_invalid,
            detail=f"reply: {any_msg.text[:200]!r}",
        )

        # Critical: must NOT show a mutation card.
        any_buttons = any(m.button_labels for m in replies)
        result.add(
            "no_mutation_card_shown",
            not any_buttons,
            detail=(
                f"buttons across replies: "
                f"{[m.button_labels for m in replies]!r}"
            ),
        )
    except Exception as e:
        logger.exception("change_status_invalid_client crashed")
        result.add("scenario_no_exception", False, detail=str(e))
    finally:
        stamp_end(result)
    return result


# ── S15: add_meeting with past date ─────────────────────────────────────────


@register(
    name="add_meeting_past_date_rejection",
    category=CATEGORY,
    description='"wczoraj o 10 spotkanie z..." → past-date error, no commit',
)
async def run_add_meeting_past_date_rejection(
    harness: TelegramE2EHarness,
) -> ScenarioResult:
    result = new_result("add_meeting_past_date_rejection", CATEGORY)
    name = e2e_beta_name("AM-past")
    trigger = f"wczoraj o 10 spotkanie z {name} z {E2E_BETA_CITY}"
    result.context["trigger"] = trigger
    try:
        await reset_pending(harness)
        await harness.send(trigger)
        replies = await harness.wait_for_messages(count=2, timeout_s=20.0)
        result.context["reply_count"] = len(replies)
        result.context["reply_texts"] = [m.text[:160] for m in replies]

        if not replies:
            result.add(
                "got_reply", False,
                detail="no reply within 20s",
                tag="blocker",
            )
            return result

        any_msg = replies[-1]
        text = any_msg.text.lower()
        is_past_error = (
            "przeszło" in text
            or "podaj datę przyszłą" in text
            or "data" in text and "wczoraj" in text
        )
        result.add(
            "reply_indicates_past_date_error",
            is_past_error,
            detail=f"reply: {any_msg.text[:200]!r}",
            tag="pass" if is_past_error else "known_drift",
            doc_ref="TEST_PLAN_CURRENT.md AM-4",
        )

        any_buttons = any(m.button_labels for m in replies)
        result.add(
            "no_mutation_card_shown",
            not any_buttons,
            detail=f"buttons: {[m.button_labels for m in replies]!r}",
        )
    except Exception as e:
        logger.exception("add_meeting_past_date_rejection crashed")
        result.add("scenario_no_exception", False, detail=str(e))
    finally:
        stamp_end(result)
    return result
