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


def make_run_id() -> str:
    """Generate a per-scenario run_id (HHMMSS) for synthetic name namespacing.

    Each scenario captures one run_id at start; all `e2e_beta_name` calls
    within the scenario should pass it so the cleanup tool can scope a
    delete to one scenario's writes.
    """
    return datetime.now(tz=WARSAW).strftime("%H%M%S")


def e2e_beta_name(suffix: str = "", run_id: str | None = None) -> str:
    """Generate an E2E-Beta-prefixed client name.

    `run_id` is the scenario-scoped HHMMSS marker (see `make_run_id`).
    When omitted, a fresh timestamp is derived per call (legacy behavior
    used by Phase 7A scenarios that don't track run_id explicitly).

    Used for cancel-only scenarios — even though no commit happens, names
    that touch parser/disambiguation paths must be unmistakably synthetic
    so manual review of any Sheet residue is trivial.
    """
    rid = run_id if run_id is not None else make_run_id()
    return f"E2E-Beta-Tester-{rid}-{suffix}" if suffix else f"E2E-Beta-Tester-{rid}"


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
#
# "Zapisane" added 25.04.2026 after first 7B.1 smoke run revealed bot's
# canonical confirm form is `✅ Zapisane.` (impersonal past participle),
# not the spec-suggested `Zapisałem` (1st person). Eight blockers in one
# run traced to this single missing marker.
_SAVE_CONFIRMATION_MARKERS = (
    "Zapisałem", "Zapisałam", "Zapisano", "Zapisana", "Zapisane",
    "Dodałem", "Dodałam", "Dodano",
    "Zaktualizowano", "Zaktualizowane", "Zaktualizowałem",
    "Spotkanie umówione", "Spotkanie zapisane", "Spotkanie dodane",
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


# ── Co-dalej cleanup (post-save text-pending state) ─────────────────────────


def _has_co_dalej(replies: list[_ObservedMessage]) -> bool:
    """True iff any reply text contains the bot's 'Co dalej —' follow-up."""
    return any("Co dalej" in m.text for m in replies)


async def close_post_save_followup(
    harness: TelegramE2EHarness,
    replies: list[_ObservedMessage],
) -> bool:
    """Close the soft text-pending state bot enters after a successful save.

    Bot's post-save pattern (observed 25.04.2026):

        msg 1: "✅ Zapisane."
        msg 2: "Co dalej — {client} ({city})? Spotkanie, telefon, mail, ..."

    The "Co dalej" message creates a soft pending — if the next user
    message arrives without closing it, bot replies "Nie rozumiem. Podaj
    np. 'spotkanie jutro o 14', 'telefon', albo napisz 'nic' żeby..."
    instead of treating the message as a fresh intent.

    Bot's own hint is to send 'nic' to close it, so that's what we do —
    only when we actually saw 'Co dalej' (avoid creating residue when no
    follow-up was emitted).

    Returns True iff cleanup was sent. Failures are swallowed — this is
    teardown, not assertion.
    """
    if not _has_co_dalej(replies):
        return False
    try:
        await harness.send("nic")
        # 3s is enough for bot's ack of 'nic' to land. Not asserted on.
        await harness.collect_messages(duration_s=3.0)
        return True
    except Exception as e:
        logger.warning("close_post_save_followup failed: %s", e)
        return False


# ── Setup helper (PUBLIC; used by Stage-2 scenario modules) ─────────────────


async def setup_existing_client(
    harness: TelegramE2EHarness,
    result,  # tests_e2e.report.ScenarioResult — avoid import cycle
    name: str,
    city: str = E2E_BETA_CITY,
    extra_fields: str = "600100200, PV",
) -> bool:
    """Create a client via add_client → ✅ Zapisać. Returns True on success.

    Public counterpart of `mutating_core._setup_existing_client`. Use this
    in scenarios that need a pre-existing client (notes, R6 active_client,
    etc.). On failure adds a `blocker` check to `result` and returns False
    so the calling scenario can short-circuit cleanly.

    The `also_change_status_to` and `also_add_note` extension knobs from
    the plan are deferred — Stage-2 scenarios that need history can chain
    explicit follow-up trigger sends after this helper returns.
    """
    setup_trigger = f"dodaj klienta {name}, {city}, {extra_fields}"
    result.context["setup_trigger"] = setup_trigger
    await harness.send(setup_trigger)
    setup_replies = await harness.wait_for_messages(count=2, timeout_s=25.0)
    setup_card = find_card_message(setup_replies)
    if setup_card is None:
        result.add_blocker(
            "setup_client_card_arrived",
            f"no setup card with buttons; got "
            f"{[m.text[:80] for m in setup_replies]}",
        )
        return False

    save_label, confirm_replies = await click_save_and_collect(harness, setup_card)
    if save_label is None:
        result.add_blocker(
            "setup_save_button_present",
            f"setup card had no ✅ Zapisać; labels={setup_card.button_labels}",
        )
        return False
    if not confirm_replies:
        result.add_blocker(
            "setup_save_confirmed",
            "no reply after clicking ✅ on setup card",
        )
        return False
    if not any(is_save_confirmation(m.text) for m in confirm_replies):
        result.add_blocker(
            "setup_save_confirmed",
            f"setup save reply lacks confirm marker; got "
            f"{[m.text[:80] for m in confirm_replies]}",
        )
        return False

    result.add("setup_client_created", True, detail=f"client '{name}' setup OK")
    closed = await close_post_save_followup(harness, confirm_replies)
    result.context["setup_co_dalej_closed"] = closed
    await post_setup_settle()
    return True


# ── API verification wrappers (Sheets + Calendar) ────────────────────────────


async def verify_sheets_row(
    result,  # ScenarioResult (avoid import cycle)
    telegram_id: int,
    name: str,
    city: str | None = None,
    expected_fields: dict[str, str] | None = None,
    *,
    check_key: str = "sheets_row_created",
) -> dict | None:
    """Verify a Sheets row exists for `name` (and optional `city`) and that
    each `expected_fields` key→substring is present in the row's value.

    Adds one check per scenario: `{check_key}` (PASS if row found and all
    expected fields match), plus optional per-field sub-checks.

    Settles 1.5s before reading to absorb Sheets eventual-consistency.
    Returns the row dict (with `_row` key) on success, None otherwise.
    """
    # Local import: avoid module-load cost when scenarios don't verify.
    from tests_e2e.sheets_verify import (
        assert_row_field, find_client_row, resolve_user_id,
    )

    await asyncio.sleep(1.5)  # eventual consistency cushion
    user_id = await resolve_user_id(telegram_id)
    if not user_id:
        result.add(check_key, False, detail=f"no Supabase user for telegram_id={telegram_id}",
                   tag="blocker")
        return None

    row = await find_client_row(user_id, name, city)
    if row is None:
        result.add(
            check_key, False,
            detail=f"no Sheets row matched name={name!r} city={city!r}",
        )
        return None

    result.add(check_key, True, detail=f"row {row.get('_row')} matched")

    if expected_fields:
        for field, expected_substring in expected_fields.items():
            ok, detail = assert_row_field(row, field, expected_substring)
            result.add(f"{check_key}_field_{field}", ok, detail)

    return row


async def verify_calendar_event(
    result,
    telegram_id: int,
    summary_marker: str,
    start_window,  # datetime
    end_window,    # datetime
    *,
    expected_event_type: str | None = None,
    expected_start=None,  # datetime
    expected_duration_min: int | None = None,
    check_key: str = "calendar_event_created",
) -> dict | None:
    """Verify a Calendar event matching `summary_marker` exists in
    [start_window, end_window). Optionally check event_type / start / duration.

    Settles 1.5s before reading. Returns the event dict on success.
    """
    from tests_e2e.calendar_verify import (
        assert_event_at_time,
        assert_event_duration,
        assert_event_type,
        find_event_by_summary_in_window,
    )
    from tests_e2e.sheets_verify import resolve_user_id

    await asyncio.sleep(1.5)
    user_id = await resolve_user_id(telegram_id)
    if not user_id:
        result.add(check_key, False, detail=f"no Supabase user for telegram_id={telegram_id}",
                   tag="blocker")
        return None

    event = await find_event_by_summary_in_window(
        user_id, summary_marker, start_window, end_window,
    )
    if event is None:
        result.add(
            check_key, False,
            detail=(
                f"no Calendar event matched summary~={summary_marker!r} "
                f"in [{start_window.isoformat()}, {end_window.isoformat()})"
            ),
        )
        return None

    result.add(
        check_key, True,
        detail=f"event id={event.get('id')!r} title={event.get('title')!r}",
    )

    if expected_event_type is not None:
        ok, detail = assert_event_type(event, expected_event_type)
        result.add(f"{check_key}_event_type", ok, detail)
    if expected_start is not None:
        ok, detail = assert_event_at_time(event, expected_start)
        result.add(f"{check_key}_start_time", ok, detail)
    if expected_duration_min is not None:
        ok, detail = assert_event_duration(event, expected_duration_min)
        result.add(f"{check_key}_duration_min", ok, detail)

    return event
