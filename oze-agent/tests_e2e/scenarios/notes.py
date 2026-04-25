"""Phase 7B-final — add_note scenarios (3 scenarios, NEW category `notes`).

Phase 7A + 7B.1 had ZERO add_note coverage. This module adds:

- N01 add_note_pure_short_save     — Flow A: "{name}: ma duży dom" → 1-line confirm
- N02 add_note_pure_bullets_save   — Flow B: multi-line bullets card
- N03 add_note_compound_phone_save — note + phone_call event compound

All scenarios commit (default_in_run=False) and verify the Sheets
Notatki column actually got the new content via API verification.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from tests_e2e.asserts import (
    assert_no_banned_phrases,
    assert_no_internal_leak,
    assert_three_button_card,
)
from tests_e2e.harness import TelegramE2EHarness
from tests_e2e.report import ScenarioResult
from tests_e2e.scenarios._base import new_result, register, stamp_end
from tests_e2e.scenarios._helpers import (
    E2E_BETA_CITY,
    WARSAW,
    assert_save_confirmed,
    card_mentions_date_pl_str,
    check_pl_date_or_drift,
    click_save_and_collect,
    e2e_beta_name,
    find_card_message,
    fmt_pl_date,
    reset_pending,
    setup_existing_client,
    today_warsaw,
    verify_calendar_event,
    verify_sheets_row,
)

logger = logging.getLogger(__name__)

CATEGORY = "notes"


def _verify_admin_id(harness: TelegramE2EHarness, result: ScenarioResult) -> int | None:
    """Return harness.authenticated_user_id or None+blocker."""
    tid = harness.authenticated_user_id
    if tid is None:
        result.add_blocker(
            "harness_authenticated", "harness not authenticated — preflight should have caught this",
        )
    return tid


# ── N01: add_note_pure_short_save ───────────────────────────────────────────


@register(
    name="add_note_pure_short_save",
    category=CATEGORY,
    description=(
        "setup client → '{name}: ma duży dom' (Flow A short note) → "
        "📝 1-line confirm card → ✅ → Notatki updated in Sheets."
    ),
    default_in_run=False,
)
async def run_add_note_pure_short_save(
    harness: TelegramE2EHarness,
) -> ScenarioResult:
    result = new_result("add_note_pure_short_save", CATEGORY)
    name = e2e_beta_name("N01")
    note_content = "ma duży dom"
    result.context["client_name"] = name
    result.context["note_content"] = note_content
    try:
        await reset_pending(harness)
        if not await setup_existing_client(harness, result, name):
            return result

        # Flow A trigger: "{name}: ma duży dom"
        trigger = f"{name}: {note_content}"
        result.context["trigger"] = trigger
        await harness.send(trigger)
        replies = await harness.wait_for_messages(count=2, timeout_s=25.0)
        result.context["reply_count"] = len(replies)

        card_msg = find_card_message(replies)
        if card_msg is None:
            result.add_blocker("got_card", "no note card with buttons")
            return result
        result.add("got_card", True, detail=str(card_msg.button_labels))

        ok, detail = assert_three_button_card(card_msg)
        result.add("three_button_mutation_card", ok, detail)
        ok, detail = assert_no_banned_phrases(card_msg.text)
        result.add("no_banned_phrases", ok, detail)
        ok, detail = assert_no_internal_leak(card_msg.text)
        result.add("no_internal_field_leak", ok, detail)

        # Card should contain the note text, marked with the 📝 icon.
        result.add(
            "card_has_note_icon",
            "📝" in card_msg.text,
            detail=f"card text: {card_msg.text[:200]!r}",
        )
        result.add(
            "card_contains_note_content",
            note_content in card_msg.text,
            detail=f"expected '{note_content}' in card; got: {card_msg.text[:200]!r}",
        )

        save_label, confirm_replies = await click_save_and_collect(harness, card_msg)
        result.context["save_label"] = save_label
        if save_label is None:
            result.add_blocker("save_button_present", f"no ✅ on note card")
            return result
        result.add("save_button_present", True, detail=save_label)
        await assert_save_confirmed(harness, result, confirm_replies)

        # API verification — Sheets Notatki should contain the new note.
        admin_id = _verify_admin_id(harness, result)
        if admin_id is not None:
            await verify_sheets_row(
                result, admin_id, name, E2E_BETA_CITY,
                expected_fields={"Notatki": note_content},
            )
    except Exception as e:
        logger.exception("add_note_pure_short_save crashed")
        result.add_blocker("scenario_crash", f"{type(e).__name__}: {e}")
    finally:
        stamp_end(result)
    return result


# ── N02: add_note_pure_bullets_save ─────────────────────────────────────────


@register(
    name="add_note_pure_bullets_save",
    category=CATEGORY,
    description=(
        "setup client → 'dodaj notatkę do {name}: ...' multi-line → "
        "📝 Flow B bullets card → ✅ → bullets in Sheets Notatki."
    ),
    default_in_run=False,
)
async def run_add_note_pure_bullets_save(
    harness: TelegramE2EHarness,
) -> ScenarioResult:
    result = new_result("add_note_pure_bullets_save", CATEGORY)
    name = e2e_beta_name("N02")
    bullet_a = "klient zainteresowany pompą ciepła 12kW"
    bullet_b = "umówiona wizyta techniczna w przyszłym tygodniu"
    result.context["client_name"] = name
    try:
        await reset_pending(harness)
        if not await setup_existing_client(harness, result, name):
            return result

        # Flow B trigger: multi-line note instruction.
        trigger = f"dodaj notatkę do {name}, {E2E_BETA_CITY}:\n- {bullet_a}\n- {bullet_b}"
        result.context["trigger"] = trigger
        await harness.send(trigger)
        replies = await harness.wait_for_messages(count=2, timeout_s=25.0)
        result.context["reply_count"] = len(replies)

        card_msg = find_card_message(replies)
        if card_msg is None:
            result.add_blocker("got_card", "no note card with buttons")
            return result
        result.add("got_card", True, detail=str(card_msg.button_labels))

        ok, detail = assert_three_button_card(card_msg)
        result.add("three_button_mutation_card", ok, detail)
        ok, detail = assert_no_banned_phrases(card_msg.text)
        result.add("no_banned_phrases", ok, detail)
        ok, detail = assert_no_internal_leak(card_msg.text)
        result.add("no_internal_field_leak", ok, detail)

        # Both bullet contents should appear on the card (loose substring).
        result.add(
            "card_contains_bullet_a",
            "pompą ciepła" in card_msg.text or "12kW" in card_msg.text,
            detail=f"expected '{bullet_a}' marker in card; got: {card_msg.text[:200]!r}",
        )
        result.add(
            "card_contains_bullet_b",
            "wizyta techniczna" in card_msg.text or "przyszłym tygodniu" in card_msg.text,
            detail=f"expected '{bullet_b}' marker in card; got: {card_msg.text[:200]!r}",
        )

        save_label, confirm_replies = await click_save_and_collect(harness, card_msg)
        result.context["save_label"] = save_label
        if save_label is None:
            result.add_blocker("save_button_present", f"no ✅ on note card")
            return result
        result.add("save_button_present", True, detail=save_label)
        await assert_save_confirmed(harness, result, confirm_replies)

        admin_id = _verify_admin_id(harness, result)
        if admin_id is not None:
            await verify_sheets_row(
                result, admin_id, name, E2E_BETA_CITY,
                expected_fields={"Notatki": "pompą ciepła"},
            )
    except Exception as e:
        logger.exception("add_note_pure_bullets_save crashed")
        result.add_blocker("scenario_crash", f"{type(e).__name__}: {e}")
    finally:
        stamp_end(result)
    return result


# ── N03: add_note_compound_phone_save ───────────────────────────────────────


@register(
    name="add_note_compound_phone_save",
    category=CATEGORY,
    description=(
        "setup client → 'notatka {name}: zadzwonić w piątek o 10' → "
        "compound card (note + phone_call event) → ✅ → Sheets Notatki "
        "+ Calendar event with type=phone_call."
    ),
    default_in_run=False,
)
async def run_add_note_compound_phone_save(
    harness: TelegramE2EHarness,
) -> ScenarioResult:
    result = new_result("add_note_compound_phone_save", CATEGORY)
    name = e2e_beta_name("N03")
    # Pick a date 3 days out so the absolute date is unambiguous.
    target_day = today_warsaw() + timedelta(days=3)
    target_dt = datetime(
        target_day.year, target_day.month, target_day.day, 10, 0, tzinfo=WARSAW,
    )
    result.context["client_name"] = name
    result.context["expected_pl_date"] = fmt_pl_date(target_day)
    try:
        await reset_pending(harness)
        if not await setup_existing_client(harness, result, name):
            return result

        # Use absolute date to avoid weekday parsing fragility.
        trigger = (
            f"dodaj notatkę {name}, {E2E_BETA_CITY}: zadzwonić "
            f"{target_day.strftime('%d.%m.%Y')} o 10:00"
        )
        result.context["trigger"] = trigger
        await harness.send(trigger)
        replies = await harness.wait_for_messages(count=2, timeout_s=25.0)
        result.context["reply_count"] = len(replies)

        card_msg = find_card_message(replies)
        if card_msg is None:
            result.add_blocker("got_card", "no compound card with buttons")
            return result
        result.add("got_card", True, detail=str(card_msg.button_labels))

        ok, detail = assert_three_button_card(card_msg)
        result.add("three_button_mutation_card", ok, detail)
        ok, detail = assert_no_banned_phrases(card_msg.text)
        result.add("no_banned_phrases", ok, detail)
        ok, detail = assert_no_internal_leak(card_msg.text)
        result.add("no_internal_field_leak", ok, detail)

        expected_date = fmt_pl_date(target_day).split(" ")[0]
        result.add(
            "card_mentions_phone_call_date",
            card_mentions_date_pl_str(card_msg.text, expected_date),
            detail=(
                f"expected '{expected_date}' (PL) or its ISO form; "
                f"got: {card_msg.text[:200]!r}"
            ),
        )
        check_pl_date_or_drift(result, card_msg)

        save_label, confirm_replies = await click_save_and_collect(harness, card_msg)
        result.context["save_label"] = save_label
        if save_label is None:
            result.add_blocker("save_button_present", f"no ✅ on compound card")
            return result
        result.add("save_button_present", True, detail=save_label)
        await assert_save_confirmed(harness, result, confirm_replies)

        admin_id = _verify_admin_id(harness, result)
        if admin_id is not None:
            # Sheets — note appended.
            await verify_sheets_row(
                result, admin_id, name, E2E_BETA_CITY,
                expected_fields={"Notatki": "zadzwonić"},
            )
            # Calendar — phone_call event at the right time.
            window_start = target_dt - timedelta(hours=1)
            window_end = target_dt + timedelta(hours=2)
            await verify_calendar_event(
                result, admin_id, name,
                start_window=window_start,
                end_window=window_end,
                expected_event_type="phone_call",
                expected_start=target_dt,
                expected_duration_min=15,
            )
    except Exception as e:
        logger.exception("add_note_compound_phone_save crashed")
        result.add_blocker("scenario_crash", f"{type(e).__name__}: {e}")
    finally:
        stamp_end(result)
    return result
