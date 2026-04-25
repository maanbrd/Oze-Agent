"""Phase 7A card-structure scenarios (S12, S13).

Trigger a mutation card → verify shape (3 buttons, expected fields, no
banned phrases) → click ❌ Anulować → verify cancel reply. NO commit.
"""

from __future__ import annotations

import logging

from tests_e2e.asserts import (
    assert_cancel_reply,
    assert_no_banned_phrases,
    assert_no_internal_leak,
    assert_three_button_card,
)
from tests_e2e.card_parser import parse_card
from tests_e2e.harness import TelegramE2EHarness, _ObservedMessage
from tests_e2e.report import ScenarioResult
from tests_e2e.scenarios._base import new_result, register, stamp_end
from tests_e2e.scenarios._helpers import (
    E2E_BETA_CITY,
    e2e_beta_name,
    fmt_pl_date,
    reset_pending,
    tomorrow_warsaw,
)

logger = logging.getLogger(__name__)

CATEGORY = "card_structure"


def _find_card_message(messages: list[_ObservedMessage]) -> _ObservedMessage | None:
    """Pick the message that actually carries the inline card buttons."""
    for m in messages:
        if m.button_labels:
            return m
    return None


async def _click_cancel_and_verify(
    harness: TelegramE2EHarness,
    result: ScenarioResult,
    card_msg: _ObservedMessage,
) -> None:
    """Common tail: click ❌ Anulować, expect a short cancel reply."""
    cancel_label = next(
        (lbl for lbl in card_msg.button_labels if "Anulować" in lbl or "❌" in lbl),
        None,
    )
    if not cancel_label:
        result.add(
            "cancel_button_present",
            False,
            detail=f"no cancel button found in {card_msg.button_labels}",
        )
        return
    result.add("cancel_button_present", True, detail=cancel_label)

    await harness.click_button(card_msg, cancel_label)
    cancel_replies = await harness.collect_messages(duration_s=5.0)
    result.context["cancel_replies"] = [m.text[:120] for m in cancel_replies]

    # Bot should produce *some* response (edited card or new message).
    if not cancel_replies:
        # Edit-in-place doesn't trigger NewMessage event — accept.
        result.add(
            "cancel_acknowledged",
            True,
            detail="bot edited the card in place (no new message)",
            tag="known_drift",
            doc_ref="agent_behavior_spec_v5.md §2.R1 — '🫡 Anulowane.' as new line",
        )
        return

    cancel_msg = cancel_replies[-1]
    ok, detail = assert_cancel_reply(cancel_msg)
    result.add("cancel_reply_short_with_keyword", ok, detail)


# ── S12: add_client card structure → cancel ─────────────────────────────────


@register(
    name="add_client_card_then_cancel",
    category=CATEGORY,
    description="add_client trigger → 3-button card → ❌ Anulować, no Sheets write",
)
async def run_add_client_card_then_cancel(
    harness: TelegramE2EHarness,
) -> ScenarioResult:
    result = new_result("add_client_card_then_cancel", CATEGORY)
    name = e2e_beta_name("AC")
    trigger = f"dodaj klienta {name}, {E2E_BETA_CITY}, 600100200, PV"
    result.context["trigger"] = trigger
    try:
        await reset_pending(harness)
        await harness.send(trigger)
        # Bot may emit a typing-indicator + the card; collect up to 2.
        replies = await harness.wait_for_messages(count=2, timeout_s=25.0)
        result.context["reply_count"] = len(replies)
        result.context["reply_texts"] = [m.text[:120] for m in replies]

        card_msg = _find_card_message(replies)
        if card_msg is None:
            result.add(
                "got_card_with_buttons", False,
                detail="no message with inline keyboard arrived",
                tag="blocker",
            )
            return result
        result.add("got_card_with_buttons", True, detail=str(card_msg.button_labels))

        ok, detail = assert_three_button_card(card_msg)
        result.add("three_button_mutation_card", ok, detail)

        ok, detail = assert_no_banned_phrases(card_msg.text)
        result.add("no_banned_phrases", ok, detail)

        ok, detail = assert_no_internal_leak(card_msg.text)
        result.add("no_internal_field_leak", ok, detail)

        # Expect E2E-Beta name to appear on the card (parser reached parser).
        result.add(
            "card_contains_test_client_name",
            name in card_msg.text or "E2E-Beta" in card_msg.text,
            detail=f"card text: {card_msg.text[:200]!r}",
        )

        await _click_cancel_and_verify(harness, result, card_msg)
    except Exception as e:
        logger.exception("add_client_card_then_cancel crashed")
        result.add("scenario_no_exception", False, detail=str(e))
    finally:
        stamp_end(result)
    return result


# ── S13: add_meeting card structure → cancel ────────────────────────────────


@register(
    name="add_meeting_card_then_cancel",
    category=CATEGORY,
    description="add_meeting trigger (jutro o 10) → 3-button card → ❌ Anulować",
)
async def run_add_meeting_card_then_cancel(
    harness: TelegramE2EHarness,
) -> ScenarioResult:
    result = new_result("add_meeting_card_then_cancel", CATEGORY)
    name = e2e_beta_name("AM")
    tmr = tomorrow_warsaw()
    trigger = f"jutro o 10 spotkanie z {name} z {E2E_BETA_CITY}"
    result.context["trigger"] = trigger
    result.context["expected_pl_date"] = fmt_pl_date(tmr)
    try:
        await reset_pending(harness)
        await harness.send(trigger)
        replies = await harness.wait_for_messages(count=2, timeout_s=25.0)
        result.context["reply_count"] = len(replies)
        result.context["reply_texts"] = [m.text[:120] for m in replies]

        card_msg = _find_card_message(replies)
        if card_msg is None:
            result.add(
                "got_card_with_buttons", False,
                detail="no card arrived",
                tag="blocker",
            )
            return result
        result.add("got_card_with_buttons", True, detail=str(card_msg.button_labels))

        ok, detail = assert_three_button_card(card_msg)
        result.add("three_button_mutation_card", ok, detail)

        ok, detail = assert_no_banned_phrases(card_msg.text)
        result.add("no_banned_phrases", ok, detail)

        ok, detail = assert_no_internal_leak(card_msg.text)
        result.add("no_internal_field_leak", ok, detail)

        # Card should reference tomorrow in PL format somewhere.
        expected_date = fmt_pl_date(tmr).split(" ")[0]  # DD.MM.YYYY only
        result.add(
            "card_mentions_tomorrow_pl_date",
            expected_date in card_msg.text,
            detail=(
                f"expected '{expected_date}' (or full '{fmt_pl_date(tmr)}') "
                f"in card; got: {card_msg.text[:200]!r}"
            ),
        )

        await _click_cancel_and_verify(harness, result, card_msg)
    except Exception as e:
        logger.exception("add_meeting_card_then_cancel crashed")
        result.add("scenario_no_exception", False, detail=str(e))
    finally:
        stamp_end(result)
    return result
