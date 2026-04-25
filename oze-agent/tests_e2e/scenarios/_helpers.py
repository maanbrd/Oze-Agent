"""Shared scenario helpers.

Keeps individual scenario modules thin — they should focus on inputs and
assertions, not bookkeeping.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from tests_e2e.harness import TelegramE2EHarness

logger = logging.getLogger(__name__)

WARSAW = ZoneInfo("Europe/Warsaw")


# ── Pending residue cleanup ──────────────────────────────────────────────────


async def reset_pending(harness: TelegramE2EHarness) -> None:
    """Drain stale replies between scenarios — DOES NOT send anything.

    Earlier versions sent "anuluj" hoping to close any pending flow.
    Backfired: when no pending exists, the bot interprets "anuluj" as a
    new intent and replies "Co chcesz anulować?", creating *fresh*
    pending residue that contaminates the next scenario. Smoke run on
    25.04.2026 verified this (5 of 8 routing scenarios got the wrong
    reply because of the bleed).

    Phase 7A scenarios either don't create pending (read-only / route-only)
    or self-cancel via button click. Residue from a self-cancel may still
    take ~1-3s to arrive, so we sleep + drain instead of sending. R3
    auto-cancel mechanism (`agent_behavior_spec_v5.md §2.R3`) takes care
    of any leftover pending the moment the next scenario's trigger lands.
    """
    try:
        # Give late replies from the previous scenario time to settle,
        # then drain so they don't leak into the next scenario's
        # wait_for_messages call.
        await asyncio.sleep(2.5)
        drained = await harness._drain_inbox()
        if drained:
            logger.debug("reset_pending: drained %d stale message(s)", drained)
    except Exception as e:
        logger.warning("reset_pending: %s", e)


# ── Date helpers (dynamic, never hardcoded) ──────────────────────────────────


def today_warsaw() -> date:
    return datetime.now(tz=WARSAW).date()


def tomorrow_warsaw() -> date:
    return today_warsaw() + timedelta(days=1)


def yesterday_warsaw() -> date:
    return today_warsaw() - timedelta(days=1)


_PL_WEEKDAY = (
    "Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela",
)


def fmt_pl_date(d: date) -> str:
    """Format as DD.MM.YYYY (Dzień). Matches bot's user-facing convention."""
    return f"{d.strftime('%d.%m.%Y')} ({_PL_WEEKDAY[d.weekday()]})"


# ── Test data prefixing ──────────────────────────────────────────────────────


def e2e_beta_name(suffix: str = "") -> str:
    """Generate an E2E-Beta-prefixed client name. Suffix optional.

    Used for cancel-only scenarios — even though no commit happens, names
    that touch parser/disambiguation paths must be unmistakably synthetic
    so manual review of any Sheet residue is trivial.
    """
    ts = datetime.now(tz=WARSAW).strftime("%H%M%S")
    return f"E2E-Beta-Tester-{ts}-{suffix}" if suffix else f"E2E-Beta-Tester-{ts}"


E2E_BETA_CITY = "E2E-Beta-City"


# ── Sleep between scenario triggers (Telegram rate-limit politeness) ─────────


async def inter_scenario_sleep() -> None:
    """Sleep between scenarios so Telegram doesn't throttle the test user.

    Bumped to 2s after observing cross-scenario reply bleed when the bot's
    reply to scenario N arrives only after scenario N+1 has already begun.
    Combined with `reset_pending`'s 2.5s drain, total gap is ~4.5s.
    """
    await asyncio.sleep(2.0)
