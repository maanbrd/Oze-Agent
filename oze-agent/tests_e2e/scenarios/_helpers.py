"""Shared scenario helpers.

Keeps individual scenario modules thin — they should focus on inputs and
assertions, not bookkeeping.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from tests_e2e.harness import TelegramE2EHarness, _ObservedMessage

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


# ── Card message picking (Phase 7B.1 mutating-flow shared helpers) ───────────


def find_card_message(messages: list[_ObservedMessage]) -> _ObservedMessage | None:
    """Pick the message that actually carries the inline card buttons.

    Bot may emit a typing indicator + the card as separate messages; the
    one we want is whichever has `button_labels`. Returns None if no
    message in the list has buttons.
    """
    for m in messages:
        if m.button_labels:
            return m
    return None


# ── Save-flow markers (mutation confirmation) ────────────────────────────────

# Tolerant marker set — bot wording drifts. PASS if ANY marker is present
# in the post-click reply text. Keep these as substrings (no anchors).
_SAVE_CONFIRMATION_MARKERS = (
    "Zapisałem", "Zapisałam", "Zapisano", "Zapisana",
    "Dodałem", "Dodałam", "Dodano",
    "Zaktualizowano", "Zaktualizowane", "Zaktualizowałem",
    "Spotkanie umówione", "Spotkanie zapisane",
    "Status zmieniony", "Zmieniłem status",
    "Notatka dodana", "Notatkę dodano", "Notatkę zapisałem",
)


def is_save_confirmation(text: str) -> bool:
    """True if `text` contains any tolerant save-confirmation marker."""
    return any(m in text for m in _SAVE_CONFIRMATION_MARKERS)


def find_save_button_label(button_labels: list[str]) -> str | None:
    """Locate the ✅ Zapisać button label tolerantly (icon OR word)."""
    for lbl in button_labels:
        if "Zapisać" in lbl or "✅" in lbl:
            return lbl
    return None


def find_routing_button_label(
    button_labels: list[str], target: str,
) -> str | None:
    """Locate routing button by target ('nowy' or 'aktualizuj'), case-insensitive."""
    target_lo = target.lower()
    for lbl in button_labels:
        if target_lo in lbl.lower():
            return lbl
    return None


async def click_save_and_collect(
    harness: TelegramE2EHarness,
    card_msg: _ObservedMessage,
    duration_s: float = 12.0,
) -> tuple[str | None, list[_ObservedMessage]]:
    """Click ✅ Zapisać on a card, return (label_used, replies).

    Returns (None, []) if no save button is present on the card.
    `duration_s` is the post-click collection window — bumped from cancel
    flow's 5s because save can trigger Sheets+Calendar writes that take
    longer than a one-line cancel reply.
    """
    save_label = find_save_button_label(card_msg.button_labels)
    if save_label is None:
        return None, []
    await harness.click_button(card_msg, save_label)
    replies = await harness.collect_messages(duration_s=duration_s)
    return save_label, replies


# ── Pause helper between setup-and-main steps within ONE scenario ───────────


async def post_setup_settle() -> None:
    """Pause after a setup save commits, before sending the main test trigger.

    Bot may still be flushing Sheets/Calendar writes; sending the next
    trigger immediately can race the previous flow's tail and cause
    `pending_flow` confusion. 2s is enough in practice.
    """
    await asyncio.sleep(2.0)
