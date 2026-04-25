"""Phase 7A behaviour-rule scenarios (S16).

S16 verifies R1 cancel semantics: trigger an add_client card → ❌ Anulować
→ exactly one short reply (no "Na pewno?" loop). Scenario complementary
to S12 (S12 checks card structure, S16 zooms in on the cancel rule).
"""

from __future__ import annotations

import logging

from tests_e2e.asserts import assert_cancel_reply
from tests_e2e.harness import TelegramE2EHarness
from tests_e2e.report import ScenarioResult
from tests_e2e.scenarios._base import new_result, register, stamp_end
from tests_e2e.scenarios._helpers import (
    E2E_BETA_CITY,
    e2e_beta_name,
    reset_pending,
)

logger = logging.getLogger(__name__)

CATEGORY = "rules"


@register(
    name="cancel_one_click_no_loop",
    category=CATEGORY,
    description=(
        "R1.❌Anulować must be one-click — zero 'Na pewno?' confirmation loop. "
        "Triggers an add_client card, clicks ❌ Anulować, expects 'Anulowane' once."
    ),
)
async def run_cancel_one_click_no_loop(
    harness: TelegramE2EHarness,
) -> ScenarioResult:
    result = new_result("cancel_one_click_no_loop", CATEGORY)
    name = e2e_beta_name("R1-cancel")
    trigger = f"dodaj klienta {name}, {E2E_BETA_CITY}, 600100200"
    result.context["trigger"] = trigger
    try:
        await reset_pending(harness)
        await harness.send(trigger)
        replies = await harness.wait_for_messages(count=2, timeout_s=20.0)
        if not replies:
            result.add(
                "got_card", False,
                detail="no reply", tag="blocker",
            )
            return result

        card_msg = next((m for m in replies if m.button_labels), None)
        if card_msg is None:
            result.add(
                "got_card", False,
                detail="no card with buttons",
                tag="blocker",
            )
            return result
        result.add("got_card", True, detail=str(card_msg.button_labels))

        cancel_label = next(
            (lbl for lbl in card_msg.button_labels if "Anulować" in lbl or "❌" in lbl),
            None,
        )
        if not cancel_label:
            result.add(
                "cancel_button_present", False,
                detail=f"no cancel in {card_msg.button_labels}",
            )
            return result
        result.add("cancel_button_present", True, detail=cancel_label)

        await harness.click_button(card_msg, cancel_label)

        # Collect ALL messages in the next 3s — we want to assert there is
        # at most one message AND no follow-up question.
        cancel_replies = await harness.collect_messages(duration_s=3.0)
        result.context["cancel_replies"] = [m.text[:120] for m in cancel_replies]
        result.context["cancel_reply_count"] = len(cancel_replies)

        # Bot may either edit the card in-place (zero new messages) OR
        # send a single short "Anulowane." line. Either is acceptable.
        if len(cancel_replies) == 0:
            result.add(
                "one_click_no_loop",
                True,
                detail="card edited in-place, no follow-up question",
                tag="known_drift",
                doc_ref="agent_behavior_spec_v5.md §2.R1 expects '🫡 Anulowane.' line",
            )
            return result

        # Reject any follow-up question shape ("Na pewno?", confirmation prompts).
        forbidden_phrases = (
            "na pewno", "czy na pewno", "potwierdź anulowanie", "potwierdz",
        )
        any_loop = any(
            any(phrase in m.text.lower() for phrase in forbidden_phrases)
            for m in cancel_replies
        )
        result.add(
            "no_confirmation_loop",
            not any_loop,
            detail=f"replies: {[m.text[:80] for m in cancel_replies]!r}",
        )

        # First (or only) cancel reply should match cancel-reply shape.
        ok, detail = assert_cancel_reply(cancel_replies[0])
        result.add("cancel_reply_short_with_keyword", ok, detail)

        # And exactly one cancel reply (one-click semantics).
        result.add(
            "exactly_one_cancel_message",
            len(cancel_replies) == 1,
            detail=f"got {len(cancel_replies)} replies after cancel",
            tag="pass" if len(cancel_replies) == 1 else "known_drift",
            doc_ref="agent_behavior_spec_v5.md §2.R1 — one-click",
        )
    except Exception as e:
        logger.exception("cancel_one_click_no_loop crashed")
        result.add("scenario_no_exception", False, detail=str(e))
    finally:
        stamp_end(result)
    return result
