"""Phase 7B-final — Polish slang + relative-time scenarios (NEW category `polish_edge`).

Two scenarios validating that the bot's NLU handles colloquial Polish:

- P01 polish_slang_pv_pompeczka_parsing — slang names for products
  (PV-ka, pompeczka, magazyn) preserved in note content.
- P02 polish_relative_time_wpol_kwadrans — "wpół do ósmej" → 7:30 in
  the meeting card.

These exercise paths that aren't on the canonical INTENCJE_MVP grammar
list but are exactly how a Polish salesperson talks. Failures here are
typically `known_drift` (parser doesn't fully cover slang) rather than
`fail` — log and move on.
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

CATEGORY = "polish_edge"


# ── P01: polish_slang_pv_pompeczka_parsing ──────────────────────────────────


@register(
    name="polish_slang_pv_pompeczka_parsing",
    category=CATEGORY,
    description=(
        "setup client → 'dodaj notatkę {name}: ma PV-kę, pompeczkę i magazyn' "
        "→ 📝 note card → ✅ → slang text preserved in Sheets Notatki."
    ),
    default_in_run=False,
)
async def run_polish_slang_pv_pompeczka_parsing(
    harness: TelegramE2EHarness,
) -> ScenarioResult:
    result = new_result("polish_slang_pv_pompeczka_parsing", CATEGORY)
    name = e2e_beta_name("P01")
    slang_text = "ma PV-kę, pompeczkę i magazyn"
    result.context["client_name"] = name
    result.context["slang_text"] = slang_text
    try:
        await reset_pending(harness)
        if not await setup_existing_client(harness, result, name):
            return result

        trigger = f"dodaj notatkę {name}, {E2E_BETA_CITY}: {slang_text}"
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

        # Parser must preserve slang (don't auto-translate to "fotowoltaika"
        # / "pompa ciepła") — that's the whole point. Accept any inflection
        # of "PV-ka" since user said "ma PV-kę" (akusativ); preserving the
        # verb form is the right behavior, not changing case.
        text_lo = card_msg.text.lower()
        result.add(
            "card_preserves_pv_ka_slang",
            "pv-k" in text_lo,
            detail=f"expected 'PV-k...' (any inflection); got: {card_msg.text[:200]!r}",
        )
        result.add(
            "card_preserves_pompeczka_slang",
            "pompeczka" in card_msg.text or "pompeczkę" in card_msg.text,
            detail=f"expected 'pompeczka' or inflection in card; got: {card_msg.text[:200]!r}",
        )

        save_label, confirm_replies = await click_save_and_collect(harness, card_msg)
        result.context["save_label"] = save_label
        if save_label is None:
            result.add_blocker("save_button_present", f"no ✅ on note card")
            return result
        result.add("save_button_present", True, detail=save_label)
        await assert_save_confirmed(harness, result, confirm_replies)

        admin_id = harness.authenticated_user_id
        if admin_id is None:
            result.add_blocker("harness_authenticated", "no telegram_id")
        else:
            # Sheets Notatki should contain at least PV-ka or pompeczka literal.
            await verify_sheets_row(
                result, admin_id, name, E2E_BETA_CITY,
                expected_fields={"Notatki": "PV-k"},
            )
    except Exception as e:
        logger.exception("polish_slang_pv_pompeczka_parsing crashed")
        result.add_blocker("scenario_crash", f"{type(e).__name__}: {e}")
    finally:
        stamp_end(result)
    return result


# ── P02: polish_relative_time_wpol_kwadrans ────────────────────────────────


@register(
    name="polish_relative_time_wpol",
    category=CATEGORY,
    description=(
        "setup client → 'spotkanie z {name} {date} wpół do ósmej' → "
        "card with resolved 07:30 → ✅ → Calendar event at 07:30."
    ),
    default_in_run=False,
)
async def run_polish_relative_time_wpol(
    harness: TelegramE2EHarness,
) -> ScenarioResult:
    result = new_result("polish_relative_time_wpol", CATEGORY)
    name = e2e_beta_name("P02")
    # +4 days from today so the date is unambiguous and not colliding.
    target_day = today_warsaw() + timedelta(days=4)
    target_dt = datetime(
        target_day.year, target_day.month, target_day.day, 7, 30, tzinfo=WARSAW,
    )
    result.context["client_name"] = name
    result.context["expected_pl_date"] = fmt_pl_date(target_day)
    result.context["expected_time"] = "07:30"
    try:
        await reset_pending(harness)
        if not await setup_existing_client(harness, result, name):
            return result

        # Polish phrasing: "wpół do ósmej" = 7:30. Use absolute date to
        # avoid weekday-parsing variability and keep the slang isolated
        # to the time component.
        trigger = (
            f"spotkanie z {name}, {E2E_BETA_CITY} "
            f"{target_day.strftime('%d.%m.%Y')} wpół do ósmej"
        )
        result.context["trigger"] = trigger
        await harness.send(trigger)
        replies = await harness.wait_for_messages(count=2, timeout_s=25.0)
        result.context["reply_count"] = len(replies)

        card_msg = find_card_message(replies)
        if card_msg is None:
            result.add_blocker("got_card", "no meeting card with buttons")
            return result
        result.add("got_card", True, detail=str(card_msg.button_labels))

        ok, detail = assert_three_button_card(card_msg)
        result.add("three_button_mutation_card", ok, detail)

        # Card should resolve "wpół do ósmej" → "07:30" / "7:30".
        has_seven_thirty = (
            "07:30" in card_msg.text
            or "7:30" in card_msg.text
        )
        result.add(
            "card_resolves_wpol_to_07_30",
            has_seven_thirty,
            detail=f"expected '07:30' or '7:30' in card; got: {card_msg.text[:200]!r}",
        )

        save_label, confirm_replies = await click_save_and_collect(harness, card_msg)
        result.context["save_label"] = save_label
        if save_label is None:
            result.add_blocker("save_button_present", f"no ✅ on meeting card")
            return result
        result.add("save_button_present", True, detail=save_label)
        await assert_save_confirmed(harness, result, confirm_replies)

        admin_id = harness.authenticated_user_id
        if admin_id is None:
            result.add_blocker("harness_authenticated", "no telegram_id")
        else:
            window_start = target_dt - timedelta(hours=1)
            window_end = target_dt + timedelta(hours=2)
            await verify_calendar_event(
                result, admin_id, name,
                start_window=window_start,
                end_window=window_end,
                expected_start=target_dt,
            )
    except Exception as e:
        logger.exception("polish_relative_time_wpol crashed")
        result.add_blocker("scenario_crash", f"{type(e).__name__}: {e}")
    finally:
        stamp_end(result)
    return result
