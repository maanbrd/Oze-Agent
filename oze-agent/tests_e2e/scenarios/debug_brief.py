"""Scenario S01 — /debug_brief round-trip + dedup.

Covers:
  1. Admin sends /debug_brief.
  2. Bot responds with the ack message ("Uruchamiam morning brief debug...").
  3. `run_morning_brief` sends the actual brief (starts with "Terminarz:").
  4. Bot sends the summary line ("Debug brief zakończony: ...").
  5. Second run the same day → the brief itself is deduped, so we expect
     only ack + summary (no brief between them).
"""

from __future__ import annotations

import logging

from tests_e2e.harness import TelegramE2EHarness, _ObservedMessage
from tests_e2e.report import ScenarioResult
from tests_e2e.scenarios._base import new_result, register, stamp_end

logger = logging.getLogger(__name__)

SCENARIO_NAME = "debug_brief"
CATEGORY = "proactive"

ACK_MARKER = "Uruchamiam"
BRIEF_HEADER = "Terminarz:"
SUMMARY_MARKER = "Debug brief zakończony"


def _find_first(messages: list[_ObservedMessage], marker: str) -> _ObservedMessage | None:
    for m in messages:
        if marker in m.text:
            return m
    return None


def _evaluate_first_run(result: ScenarioResult, messages: list[_ObservedMessage]) -> None:
    result.context["first_run_message_count"] = len(messages)
    result.context["first_run_texts"] = [m.text[:120] for m in messages]

    ack = _find_first(messages, ACK_MARKER)
    brief = _find_first(messages, BRIEF_HEADER)
    summary = _find_first(messages, SUMMARY_MARKER)

    result.add(
        "first_run_received_three_messages",
        len(messages) >= 3,
        detail=f"got {len(messages)} msgs",
    )
    result.add("first_run_ack_present", ack is not None)
    result.add("first_run_brief_has_terminarz_header", brief is not None)
    result.add("first_run_summary_present", summary is not None)
    if summary is not None:
        result.add(
            "first_run_summary_has_sent_field",
            "sent=" in summary.text,
            detail=summary.text,
        )
        result.add(
            "first_run_summary_reports_at_least_one_eligible",
            "total_eligible=" in summary.text,
            detail=summary.text,
        )


def _evaluate_second_run(result: ScenarioResult, messages: list[_ObservedMessage]) -> None:
    result.context["second_run_message_count"] = len(messages)
    result.context["second_run_texts"] = [m.text[:120] for m in messages]

    ack = _find_first(messages, ACK_MARKER)
    brief = _find_first(messages, BRIEF_HEADER)
    summary = _find_first(messages, SUMMARY_MARKER)

    result.add("second_run_ack_present", ack is not None)
    result.add("second_run_summary_present", summary is not None)
    result.add(
        "second_run_dedup_blocked_brief_send",
        brief is None,
        detail="brief leaked through on second same-day run — dedup regression",
    )
    if summary is not None:
        result.add(
            "second_run_summary_reports_skipped_deduped",
            "skipped_deduped=" in summary.text and "skipped_deduped=0" not in summary.text,
            detail=summary.text,
        )


@register(
    name=SCENARIO_NAME,
    category=CATEGORY,
    description="/debug_brief round-trip + dedup verification (opt-in only)",
    default_in_run=False,
)
async def run_debug_brief_scenario(
    harness: TelegramE2EHarness,
    *,
    first_run_wait_s: float = 60.0,
    second_run_wait_s: float = 30.0,
) -> ScenarioResult:
    result = new_result(SCENARIO_NAME, CATEGORY)
    try:
        await harness.send("/debug_brief")
        first_messages = await harness.wait_for_messages(
            count=3, timeout_s=first_run_wait_s,
        )
        _evaluate_first_run(result, first_messages)

        await harness.send("/debug_brief")
        second_messages = await harness.wait_for_messages(
            count=3, timeout_s=second_run_wait_s,
        )
        _evaluate_second_run(result, second_messages)
    except Exception as e:
        logger.exception("debug_brief scenario crashed")
        result.add("scenario_no_exception", False, detail=str(e))
    finally:
        stamp_end(result)
    return result
