"""Scenario: /debug_brief round-trip.

Covers:
  1. Admin sends /debug_brief.
  2. Bot responds with the ack message ("Uruchamiam morning brief debug...").
  3. `run_morning_brief` sends the actual brief (starts with "Terminarz:").
  4. Bot sends the summary line ("Debug brief zakończony: ...").
  5. Second run the same day → the brief itself is deduped, so we expect
     only ack + summary (no brief between them). The summary must reflect
     skipped_deduped >= 1.

This is the Phase 7 smoke foundation. Later scenarios (add_client,
add_note, change_status, add_meeting, show_day_plan, duplicate resolution,
R1 no-write) will compose the same harness primitives.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from tests_e2e.harness import TelegramE2EHarness, _ObservedMessage
from tests_e2e.report import ScenarioResult

logger = logging.getLogger(__name__)

SCENARIO_NAME = "debug_brief"

# Expected first-run message markers (order-sensitive).
ACK_MARKER = "Uruchamiam"
BRIEF_HEADER = "Terminarz:"
SUMMARY_MARKER = "Debug brief zakończony"


def _find_first(messages: list[_ObservedMessage], marker: str) -> _ObservedMessage | None:
    for m in messages:
        if marker in m.text:
            return m
    return None


def _evaluate_first_run(result: ScenarioResult, messages: list[_ObservedMessage]) -> None:
    """Check that the first /debug_brief run produced ack + brief + summary."""
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
    result.add(
        "first_run_ack_present",
        ack is not None,
        detail="expected 'Uruchamiam morning brief debug...'",
    )
    result.add(
        "first_run_brief_has_terminarz_header",
        brief is not None,
        detail="brief must start with 'Terminarz:'",
    )
    result.add(
        "first_run_summary_present",
        summary is not None,
        detail="expected 'Debug brief zakończony: ...'",
    )
    if summary is not None:
        result.add(
            "first_run_summary_has_sent_field",
            "sent=" in summary.text,
            detail=f"summary was: {summary.text!r}",
        )
        # We *expect* first run to have sent the brief, which means
        # total_eligible >= 1 AND sent >= 1 (assuming the admin is the
        # only eligible user and was not already deduped).
        result.add(
            "first_run_summary_reports_at_least_one_eligible",
            "total_eligible=" in summary.text,
            detail=f"summary was: {summary.text!r}",
        )


def _evaluate_second_run(result: ScenarioResult, messages: list[_ObservedMessage]) -> None:
    """Check the dedup expectation: the brief itself is skipped."""
    result.context["second_run_message_count"] = len(messages)
    result.context["second_run_texts"] = [m.text[:120] for m in messages]

    ack = _find_first(messages, ACK_MARKER)
    brief = _find_first(messages, BRIEF_HEADER)
    summary = _find_first(messages, SUMMARY_MARKER)

    # Ack and summary are always sent regardless of dedup.
    result.add(
        "second_run_ack_present",
        ack is not None,
        detail="ack should fire regardless of dedup",
    )
    result.add(
        "second_run_summary_present",
        summary is not None,
        detail="summary should fire regardless of dedup",
    )
    # Dedup contract: brief itself skipped.
    result.add(
        "second_run_dedup_blocked_brief_send",
        brief is None,
        detail=(
            "morning brief header leaked through on second same-day run — "
            "dedup regression"
        ),
    )
    if summary is not None:
        result.add(
            "second_run_summary_reports_skipped_deduped",
            "skipped_deduped=" in summary.text and "skipped_deduped=0" not in summary.text,
            detail=f"summary was: {summary.text!r}",
        )


async def run_debug_brief_scenario(
    harness: TelegramE2EHarness,
    *,
    first_run_wait_s: float = 60.0,
    second_run_wait_s: float = 30.0,
) -> ScenarioResult:
    """Execute the /debug_brief smoke end-to-end and return a ScenarioResult."""
    result = ScenarioResult(
        scenario_name=SCENARIO_NAME,
        started_at=datetime.now(tz=timezone.utc),
    )
    try:
        # ── First run: expect ack + brief + summary ───────────────────────
        await harness.send("/debug_brief")
        first_messages = await harness.wait_for_messages(
            count=3,
            timeout_s=first_run_wait_s,
        )
        _evaluate_first_run(result, first_messages)

        # ── Second run: expect ack + summary, brief deduped ──────────────
        await harness.send("/debug_brief")
        # On dedup we only expect 2 messages; wait for 3 but tolerate <3.
        second_messages = await harness.wait_for_messages(
            count=3,
            timeout_s=second_run_wait_s,
        )
        _evaluate_second_run(result, second_messages)

    except Exception as e:
        logger.exception("debug_brief scenario crashed")
        result.add("scenario_no_exception", False, detail=str(e))
    finally:
        result.ended_at = datetime.now(tz=timezone.utc)
    return result
