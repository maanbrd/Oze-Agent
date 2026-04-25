"""Phase 7A read-only scenarios (S10–S11).

Pure read intents — no Sheets/Calendar mutations. Verify:
- show_day_plan returns the day plan card without buttons,
- show_client for a non-existent client returns "Nie znalazłem".
"""

from __future__ import annotations

import logging

from tests_e2e.asserts import (
    assert_no_banned_phrases,
    assert_no_buttons,
    assert_no_internal_leak,
    assert_pl_date_format,
)
from tests_e2e.card_parser import is_not_found
from tests_e2e.harness import TelegramE2EHarness
from tests_e2e.report import ScenarioResult
from tests_e2e.scenarios._base import new_result, register, stamp_end
from tests_e2e.scenarios._helpers import reset_pending

logger = logging.getLogger(__name__)

CATEGORY = "read_only"


# ── S10: show_day_plan today ────────────────────────────────────────────────


@register(
    name="show_day_plan_today",
    category=CATEGORY,
    description='"co mam dziś?" → day plan card, no buttons, PL date format',
)
async def run_show_day_plan_today(harness: TelegramE2EHarness) -> ScenarioResult:
    result = new_result("show_day_plan_today", CATEGORY)
    result.context["trigger"] = "co mam dziś?"
    try:
        await reset_pending(harness)
        await harness.send("co mam dziś?")
        replies = await harness.wait_for_messages(count=1, timeout_s=20.0)
        result.context["reply_count"] = len(replies)
        if not replies:
            result.add(
                "got_reply", False,
                detail="bot did not reply to 'co mam dziś?' within 20s",
                tag="blocker",
            )
            return result
        msg = replies[0]
        result.context["reply_text"] = msg.text[:240]

        # Read-only intent — no buttons.
        ok, detail = assert_no_buttons(msg)
        result.add("show_day_plan_no_buttons", ok, detail)

        # PL date format if any dates appear (or "Na dziś nic..." with no dates).
        ok, detail = assert_pl_date_format(msg.text)
        result.add("dates_in_pl_format", ok, detail)

        # No banned corporate phrases.
        ok, detail = assert_no_banned_phrases(msg.text)
        result.add("no_banned_phrases", ok, detail)

        # No internal field leak.
        ok, detail = assert_no_internal_leak(msg.text)
        result.add("no_internal_field_leak", ok, detail)

        # Either a plan header (📅) or "Na dziś nic..." copy must show.
        is_plan_or_empty = (
            "📅" in msg.text
            or "Na dziś" in msg.text
            or "nic nie masz" in msg.text.lower()
        )
        result.add(
            "reply_is_day_plan_shape",
            is_plan_or_empty,
            detail=f"reply: {msg.text[:160]!r}",
        )
    except Exception as e:
        logger.exception("show_day_plan_today crashed")
        result.add("scenario_no_exception", False, detail=str(e))
    finally:
        stamp_end(result)
    return result


# ── S11: show_client not found ──────────────────────────────────────────────


@register(
    name="show_client_not_found",
    category=CATEGORY,
    description='"pokaż E2E-Beta-NieIstnieje" → "Nie znalazłem" reply',
)
async def run_show_client_not_found(harness: TelegramE2EHarness) -> ScenarioResult:
    result = new_result("show_client_not_found", CATEGORY)
    trigger = "pokaż E2E-Beta-NieIstnieje z E2E-Beta-City"
    result.context["trigger"] = trigger
    try:
        await reset_pending(harness)
        await harness.send(trigger)
        replies = await harness.wait_for_messages(count=1, timeout_s=20.0)
        result.context["reply_count"] = len(replies)
        if not replies:
            result.add(
                "got_reply", False,
                detail="no reply within 20s",
                tag="blocker",
            )
            return result
        msg = replies[0]
        result.context["reply_text"] = msg.text[:240]
        result.context["reply_buttons"] = msg.button_labels

        # Must surface a "not found"-class message, not silently fallback to add_client.
        result.add(
            "reply_is_not_found_class",
            is_not_found(msg.text),
            detail=f"reply: {msg.text[:160]!r}",
        )
        # Must NOT show an add_client mutation card.
        result.add(
            "no_add_client_card",
            not msg.button_labels and "Brakuje" not in msg.text,
            detail=f"buttons={msg.button_labels}",
        )
        ok, detail = assert_no_internal_leak(msg.text)
        result.add("no_internal_field_leak", ok, detail)
    except Exception as e:
        logger.exception("show_client_not_found crashed")
        result.add("scenario_no_exception", False, detail=str(e))
    finally:
        stamp_end(result)
    return result
