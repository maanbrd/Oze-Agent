"""Unit tests for scenarios/debug_brief.py evaluation logic.

We do NOT hit Telegram or Telethon here. Instead we pass a fake harness
that replays pre-recorded `_ObservedMessage` sequences and assert that
`run_debug_brief_scenario` marks the right checks PASS/FAIL.

This is the local regression net for the scenario contract: any future
change to the /debug_brief bot behavior or to the matcher logic shows up
here before it hits Telegram.
"""

from __future__ import annotations

import pytest

from tests_e2e.harness import _ObservedMessage
from tests_e2e.scenarios.debug_brief import run_debug_brief_scenario


def _msg(mid: int, text: str) -> _ObservedMessage:
    return _ObservedMessage(id=mid, text=text, date_iso="2026-04-24T07:00:00+00:00")


class _FakeHarness:
    """Replay-style double for TelegramE2EHarness.

    `script` is a list of lists of `_ObservedMessage`; each `send()`
    consumes one group and the following `wait_for_messages()` returns
    exactly that group (ignoring the requested count).
    """

    def __init__(self, script: list[list[_ObservedMessage]]) -> None:
        self._script = list(script)
        self._pending: list[_ObservedMessage] = []
        self.sent: list[str] = []

    async def send(self, text: str) -> None:
        self.sent.append(text)
        self._pending = list(self._script.pop(0)) if self._script else []

    async def wait_for_messages(self, count: int, timeout_s: float = 30.0):
        messages = self._pending
        self._pending = []
        return messages


# ── First-run happy path ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_first_run_all_three_messages_pass():
    first = [
        _msg(1, "Uruchamiam morning brief debug..."),
        _msg(2, "Terminarz:\n• 09:00 — Telefon: Jan Kowalski"),
        _msg(
            3,
            "Debug brief zakończony: "
            "total_eligible=1 sent=1 skipped_deduped=0 skipped_error=0",
        ),
    ]
    second = [
        _msg(4, "Uruchamiam morning brief debug..."),
        _msg(
            5,
            "Debug brief zakończony: "
            "total_eligible=1 sent=0 skipped_deduped=1 skipped_error=0",
        ),
    ]
    fake = _FakeHarness([first, second])
    result = await run_debug_brief_scenario(fake, first_run_wait_s=1, second_run_wait_s=1)
    assert result.passed, [c for c in result.checks if not c.passed]
    assert fake.sent == ["/debug_brief", "/debug_brief"]


# ── Failure modes ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_first_run_missing_terminarz_header_fails():
    first = [
        _msg(1, "Uruchamiam morning brief debug..."),
        _msg(2, "Brief without the required header"),
        _msg(3, "Debug brief zakończony: total_eligible=1 sent=1"),
    ]
    second = [
        _msg(4, "Uruchamiam morning brief debug..."),
        _msg(5, "Debug brief zakończony: skipped_deduped=1"),
    ]
    result = await run_debug_brief_scenario(
        _FakeHarness([first, second]),
        first_run_wait_s=1,
        second_run_wait_s=1,
    )
    assert not result.passed
    failed = [c.name for c in result.checks if not c.passed]
    assert "first_run_brief_has_terminarz_header" in failed


@pytest.mark.asyncio
async def test_first_run_zero_messages_fails_cleanly():
    result = await run_debug_brief_scenario(
        _FakeHarness([[], []]),
        first_run_wait_s=1,
        second_run_wait_s=1,
    )
    assert not result.passed
    failed = {c.name for c in result.checks if not c.passed}
    assert "first_run_received_three_messages" in failed
    assert "first_run_ack_present" in failed
    assert "first_run_summary_present" in failed


@pytest.mark.asyncio
async def test_second_run_sends_brief_again_is_dedup_regression():
    first = [
        _msg(1, "Uruchamiam morning brief debug..."),
        _msg(2, "Terminarz:\n• 09:00 — Telefon: Jan"),
        _msg(3, "Debug brief zakończony: total_eligible=1 sent=1 skipped_deduped=0"),
    ]
    # Bug: second run did NOT dedup — brief leaked through again.
    second = [
        _msg(4, "Uruchamiam morning brief debug..."),
        _msg(5, "Terminarz:\n• 09:00 — Telefon: Jan"),
        _msg(6, "Debug brief zakończony: total_eligible=1 sent=1 skipped_deduped=0"),
    ]
    result = await run_debug_brief_scenario(
        _FakeHarness([first, second]),
        first_run_wait_s=1,
        second_run_wait_s=1,
    )
    failed = {c.name for c in result.checks if not c.passed}
    assert "second_run_dedup_blocked_brief_send" in failed
    assert "second_run_summary_reports_skipped_deduped" in failed


@pytest.mark.asyncio
async def test_second_run_summary_missing_skipped_deduped_field_fails():
    first = [
        _msg(1, "Uruchamiam morning brief debug..."),
        _msg(2, "Terminarz:\n..."),
        _msg(3, "Debug brief zakończony: total_eligible=1 sent=1 skipped_deduped=0"),
    ]
    second = [
        _msg(4, "Uruchamiam morning brief debug..."),
        # Malformed summary — no skipped_deduped field at all.
        _msg(5, "Debug brief zakończony: weird_format"),
    ]
    result = await run_debug_brief_scenario(
        _FakeHarness([first, second]),
        first_run_wait_s=1,
        second_run_wait_s=1,
    )
    failed = {c.name for c in result.checks if not c.passed}
    assert "second_run_summary_reports_skipped_deduped" in failed


@pytest.mark.asyncio
async def test_ended_at_is_populated_even_on_failure():
    result = await run_debug_brief_scenario(
        _FakeHarness([[], []]),
        first_run_wait_s=1,
        second_run_wait_s=1,
    )
    assert result.ended_at is not None
    assert result.ended_at >= result.started_at


# ── Exception propagation ───────────────────────────────────────────────────


class _ExplodingHarness:
    async def send(self, text: str) -> None:
        raise RuntimeError("telegram offline")

    async def wait_for_messages(self, count: int, timeout_s: float = 30.0):
        return []


@pytest.mark.asyncio
async def test_harness_crash_is_recorded_as_failed_check():
    result = await run_debug_brief_scenario(
        _ExplodingHarness(),
        first_run_wait_s=1,
        second_run_wait_s=1,
    )
    assert not result.passed
    crash_check = next(
        (c for c in result.checks if c.name == "scenario_no_exception"), None
    )
    assert crash_check is not None
    assert "telegram offline" in crash_check.detail
