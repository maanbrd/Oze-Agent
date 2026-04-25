"""Phase 7A + 7B-final read-only scenarios.

Pure read intents — no Sheets/Calendar mutations directly (some Phase
7B-final scenarios DO setup a client via add_client → ✅ first, then
exercise the read path against that just-saved data).

7A scenarios:
- S10 show_day_plan_today
- S11 show_client_not_found

7B-final additions:
- R03 show_client_existing_just_created (after setup)
- R04 show_client_existing_with_history (setup + note + status → show)
- R05 show_day_plan_tomorrow ("co mam jutro?")
- R06 show_day_plan_empty_distant_day
- R07 show_day_plan_with_just_added_meeting (setup + meeting → show today)
- R08 show_client_multi_match_disambig (uses fixture: 2 Jan Kowalski)
"""

from __future__ import annotations

import logging
from datetime import timedelta

from tests_e2e.asserts import (
    assert_no_banned_phrases,
    assert_no_buttons,
    assert_no_internal_leak,
    assert_pl_date_format,
)
from tests_e2e.card_parser import is_not_found
from tests_e2e.harness import TelegramE2EHarness
from tests_e2e.report import ScenarioResult
from tests_e2e.scenarios._base import new_result, register, stamp_end
from tests_e2e.scenarios._helpers import (
    E2E_BETA_CITY,
    assert_save_confirmed,
    click_save_and_collect,
    e2e_beta_name,
    find_card_message,
    fmt_pl_date,
    post_setup_settle,
    reset_pending,
    setup_existing_client,
    today_warsaw,
    tomorrow_warsaw,
)

logger = logging.getLogger(__name__)

CATEGORY = "read_only"


# ── S10: show_day_plan today ────────────────────────────────────────────────


@register(
    name="show_day_plan_today",
    category=CATEGORY,
    description='"co mam dziś?" → day plan card, no buttons, PL date format',
)
async def run_show_day_plan_today(harness: TelegramE2EHarness) -> ScenarioResult:
    result = new_result("show_day_plan_today", CATEGORY)
    result.context["trigger"] = "co mam dziś?"
    try:
        await reset_pending(harness)
        await harness.send("co mam dziś?")
        replies = await harness.wait_for_messages(count=1, timeout_s=20.0)
        result.context["reply_count"] = len(replies)
        if not replies:
            result.add(
                "got_reply", False,
                detail="bot did not reply to 'co mam dziś?' within 20s",
                tag="blocker",
            )
            return result
        msg = replies[0]
        result.context["reply_text"] = msg.text[:240]

        # Read-only intent — no buttons.
        ok, detail = assert_no_buttons(msg)
        result.add("show_day_plan_no_buttons", ok, detail)

        # PL date format if any dates appear (or "Na dziś nic..." with no dates).
        ok, detail = assert_pl_date_format(msg.text)
        result.add("dates_in_pl_format", ok, detail)

        # No banned corporate phrases.
        ok, detail = assert_no_banned_phrases(msg.text)
        result.add("no_banned_phrases", ok, detail)

        # No internal field leak.
        ok, detail = assert_no_internal_leak(msg.text)
        result.add("no_internal_field_leak", ok, detail)

        # Either a plan header (📅) or "Na dziś nic..." copy must show.
        is_plan_or_empty = (
            "📅" in msg.text
            or "Na dziś" in msg.text
            or "nic nie masz" in msg.text.lower()
        )
        result.add(
            "reply_is_day_plan_shape",
            is_plan_or_empty,
            detail=f"reply: {msg.text[:160]!r}",
        )
    except Exception as e:
        logger.exception("show_day_plan_today crashed")
        result.add("scenario_no_exception", False, detail=str(e))
    finally:
        stamp_end(result)
    return result


# ── S11: show_client not found ──────────────────────────────────────────────


@register(
    name="show_client_not_found",
    category=CATEGORY,
    description='"pokaż E2E-Beta-NieIstnieje" → "Nie znalazłem" reply',
)
async def run_show_client_not_found(harness: TelegramE2EHarness) -> ScenarioResult:
    result = new_result("show_client_not_found", CATEGORY)
    trigger = "pokaż E2E-Beta-NieIstnieje z E2E-Beta-City"
    result.context["trigger"] = trigger
    try:
        await reset_pending(harness)
        await harness.send(trigger)
        replies = await harness.wait_for_messages(count=1, timeout_s=20.0)
        result.context["reply_count"] = len(replies)
        if not replies:
            result.add(
                "got_reply", False,
                detail="no reply within 20s",
                tag="blocker",
            )
            return result
        msg = replies[0]
        result.context["reply_text"] = msg.text[:240]
        result.context["reply_buttons"] = msg.button_labels

        # Must surface a "not found"-class message, not silently fallback to add_client.
        result.add(
            "reply_is_not_found_class",
            is_not_found(msg.text),
            detail=f"reply: {msg.text[:160]!r}",
        )
        # Must NOT show an add_client mutation card.
        result.add(
            "no_add_client_card",
            not msg.button_labels and "Brakuje" not in msg.text,
            detail=f"buttons={msg.button_labels}",
        )
        ok, detail = assert_no_internal_leak(msg.text)
        result.add("no_internal_field_leak", ok, detail)
    except Exception as e:
        logger.exception("show_client_not_found crashed")
        result.add("scenario_no_exception", False, detail=str(e))
    finally:
        stamp_end(result)
    return result


# ── R03: show_client existing (just created in same scenario) ──────────────


@register(
    name="show_client_existing_just_created",
    category=CATEGORY,
    description=(
        "setup client → 'pokaż {name}, {city}' → read-only card with "
        "client data, no buttons (no mutation card)."
    ),
    default_in_run=False,
)
async def run_show_client_existing_just_created(
    harness: TelegramE2EHarness,
) -> ScenarioResult:
    result = new_result("show_client_existing_just_created", CATEGORY)
    name = e2e_beta_name("R03")
    result.context["client_name"] = name
    try:
        await reset_pending(harness)
        if not await setup_existing_client(harness, result, name):
            return result

        trigger = f"pokaż {name}, {E2E_BETA_CITY}"
        result.context["trigger"] = trigger
        await harness.send(trigger)
        replies = await harness.wait_for_messages(count=1, timeout_s=20.0)
        result.context["reply_count"] = len(replies)
        if not replies:
            result.add_blocker("got_reply", "no reply within 20s")
            return result
        msg = replies[0]
        result.context["reply_text"] = msg.text[:300]
        result.context["reply_buttons"] = msg.button_labels

        ok, detail = assert_no_buttons(msg)
        result.add("show_client_no_buttons", ok, detail)

        result.add(
            "card_contains_client_name",
            name in msg.text,
            detail=f"expected {name!r} in card; got: {msg.text[:240]!r}",
        )

        ok, detail = assert_no_banned_phrases(msg.text)
        result.add("no_banned_phrases", ok, detail)

        ok, detail = assert_no_internal_leak(msg.text)
        result.add("no_internal_field_leak", ok, detail)

        result.add(
            "card_has_client_icon",
            "📋" in msg.text,
            detail=f"expected 📋 read-only card; got: {msg.text[:200]!r}",
        )

        # Phone we set during setup should appear (loose substring).
        result.add(
            "card_includes_phone",
            "600100200" in msg.text or "600 100 200" in msg.text,
            detail=f"expected '600100200' in card; got: {msg.text[:240]!r}",
        )
    except Exception as e:
        logger.exception("show_client_existing_just_created crashed")
        result.add_blocker("scenario_crash", f"{type(e).__name__}: {e}")
    finally:
        stamp_end(result)
    return result


# ── R04: show_client existing with history (note + status applied) ─────────


@register(
    name="show_client_existing_with_history",
    category=CATEGORY,
    description=(
        "setup client → add_note → change_status → 'pokaż {name}' → "
        "read-only card reflects both the note AND the new status."
    ),
    default_in_run=False,
)
async def run_show_client_existing_with_history(
    harness: TelegramE2EHarness,
) -> ScenarioResult:
    result = new_result("show_client_existing_with_history", CATEGORY)
    name = e2e_beta_name("R04")
    history_note = "test note dla R04 — historia"
    result.context["client_name"] = name
    result.context["history_note"] = history_note
    try:
        await reset_pending(harness)
        if not await setup_existing_client(harness, result, name):
            return result

        # Step 1: add a note via Flow A.
        note_trigger = f"{name}: {history_note}"
        result.context["note_trigger"] = note_trigger
        await harness.send(note_trigger)
        note_replies = await harness.wait_for_messages(count=2, timeout_s=25.0)
        note_card = find_card_message(note_replies)
        if note_card is None:
            result.add_blocker(
                "step1_note_card", "no note card after add_note trigger",
            )
            return result
        save_label, note_confirm = await click_save_and_collect(harness, note_card)
        if save_label is None:
            result.add_blocker("step1_note_save_button", "no ✅ on note card")
            return result
        await assert_save_confirmed(
            harness, result, note_confirm, check_key="step1_note_saved",
        )
        await post_setup_settle()

        # Step 2: change status to "podpisał".
        status_trigger = f"{name} ma podpisaną umowę"
        result.context["status_trigger"] = status_trigger
        await harness.send(status_trigger)
        status_replies = await harness.wait_for_messages(count=2, timeout_s=25.0)
        status_card = find_card_message(status_replies)
        if status_card is None:
            result.add_blocker(
                "step2_status_card", "no status card after change_status trigger",
            )
            return result
        save_label2, status_confirm = await click_save_and_collect(harness, status_card)
        if save_label2 is None:
            result.add_blocker("step2_status_save_button", "no ✅ on status card")
            return result
        await assert_save_confirmed(
            harness, result, status_confirm, check_key="step2_status_saved",
        )
        await post_setup_settle()

        # Step 3: show_client and verify both pieces are visible.
        show_trigger = f"pokaż {name}, {E2E_BETA_CITY}"
        result.context["show_trigger"] = show_trigger
        await harness.send(show_trigger)
        show_replies = await harness.wait_for_messages(count=1, timeout_s=20.0)
        result.context["show_reply_count"] = len(show_replies)
        if not show_replies:
            result.add_blocker("step3_show_reply", "no reply to pokaż within 20s")
            return result
        show_msg = show_replies[0]
        result.context["show_reply_text"] = show_msg.text[:400]

        ok, detail = assert_no_buttons(show_msg)
        result.add("show_client_no_buttons", ok, detail)

        # Note content visible.
        result.add(
            "card_includes_history_note",
            "historia" in show_msg.text.lower() or history_note[:20].lower() in show_msg.text.lower(),
            detail=(
                f"expected note marker in card; got: {show_msg.text[:300]!r}"
            ),
        )

        # New status visible (Podpisane / Umowa podpisana / podpisał).
        status_visible = any(
            m in show_msg.text
            for m in ("Podpisane", "Umowa podpisana", "Podpisana", "podpisana")
        )
        result.add(
            "card_includes_new_status",
            status_visible,
            detail=f"expected umowa-status marker; got: {show_msg.text[:300]!r}",
        )

        ok, detail = assert_no_banned_phrases(show_msg.text)
        result.add("no_banned_phrases", ok, detail)
    except Exception as e:
        logger.exception("show_client_existing_with_history crashed")
        result.add_blocker("scenario_crash", f"{type(e).__name__}: {e}")
    finally:
        stamp_end(result)
    return result


# ── R05: show_day_plan tomorrow ────────────────────────────────────────────


@register(
    name="show_day_plan_tomorrow",
    category=CATEGORY,
    description='"co mam jutro?" → day plan card for tomorrow, no buttons.',
    default_in_run=False,
)
async def run_show_day_plan_tomorrow(
    harness: TelegramE2EHarness,
) -> ScenarioResult:
    result = new_result("show_day_plan_tomorrow", CATEGORY)
    tmr = tomorrow_warsaw()
    result.context["expected_pl_date"] = fmt_pl_date(tmr)
    result.context["trigger"] = "co mam jutro?"
    try:
        await reset_pending(harness)
        await harness.send("co mam jutro?")
        replies = await harness.wait_for_messages(count=1, timeout_s=20.0)
        result.context["reply_count"] = len(replies)
        if not replies:
            result.add_blocker("got_reply", "no reply within 20s")
            return result
        msg = replies[0]
        result.context["reply_text"] = msg.text[:240]

        ok, detail = assert_no_buttons(msg)
        result.add("show_day_plan_no_buttons", ok, detail)

        ok, detail = assert_pl_date_format(msg.text)
        result.add("dates_in_pl_format", ok, detail)

        ok, detail = assert_no_banned_phrases(msg.text)
        result.add("no_banned_phrases", ok, detail)

        ok, detail = assert_no_internal_leak(msg.text)
        result.add("no_internal_field_leak", ok, detail)

        # Either tomorrow's date is mentioned, or "Na jutro nic..." copy.
        expected_date = fmt_pl_date(tmr).split(" ")[0]
        is_plan_or_empty = (
            expected_date in msg.text
            or "Na jutro" in msg.text
            or "nic nie masz" in msg.text.lower()
            or "📅" in msg.text
        )
        result.add(
            "reply_is_tomorrow_plan_or_empty",
            is_plan_or_empty,
            detail=(
                f"expected '{expected_date}' or 'Na jutro' or empty marker; "
                f"got: {msg.text[:200]!r}"
            ),
        )
    except Exception as e:
        logger.exception("show_day_plan_tomorrow crashed")
        result.add_blocker("scenario_crash", f"{type(e).__name__}: {e}")
    finally:
        stamp_end(result)
    return result


# ── R06: show_day_plan empty (distant day) ────────────────────────────────


@register(
    name="show_day_plan_empty_distant_day",
    category=CATEGORY,
    description=(
        "'co mam {date 6 months out}?' → 'Na dziś nic...' / empty-day "
        "reply (no buttons, no banned phrases)."
    ),
    default_in_run=False,
)
async def run_show_day_plan_empty_distant_day(
    harness: TelegramE2EHarness,
) -> ScenarioResult:
    result = new_result("show_day_plan_empty_distant_day", CATEGORY)
    distant = today_warsaw() + timedelta(days=180)
    trigger = f"co mam {distant.strftime('%d.%m.%Y')}?"
    result.context["trigger"] = trigger
    result.context["expected_pl_date"] = fmt_pl_date(distant)
    try:
        await reset_pending(harness)
        await harness.send(trigger)
        replies = await harness.wait_for_messages(count=1, timeout_s=20.0)
        result.context["reply_count"] = len(replies)
        if not replies:
            result.add_blocker("got_reply", "no reply within 20s")
            return result
        msg = replies[0]
        result.context["reply_text"] = msg.text[:240]

        ok, detail = assert_no_buttons(msg)
        result.add("show_day_plan_no_buttons", ok, detail)

        ok, detail = assert_no_banned_phrases(msg.text)
        result.add("no_banned_phrases", ok, detail)

        ok, detail = assert_no_internal_leak(msg.text)
        result.add("no_internal_field_leak", ok, detail)

        # 180 days out should be empty for our test user. Tolerant: accept
        # any "no events"-class reply OR a plan with that exact date echoed.
        empty_marker = (
            "Na " in msg.text and "nic" in msg.text.lower()
        ) or "nic nie masz" in msg.text.lower() or "wolne" in msg.text.lower()
        date_echoed = distant.strftime("%d.%m.%Y") in msg.text
        result.add(
            "reply_is_empty_or_plan_with_distant_date",
            empty_marker or date_echoed,
            detail=(
                f"expected empty-day marker or echoed date "
                f"{distant.strftime('%d.%m.%Y')!r}; got: {msg.text[:200]!r}"
            ),
        )
    except Exception as e:
        logger.exception("show_day_plan_empty_distant_day crashed")
        result.add_blocker("scenario_crash", f"{type(e).__name__}: {e}")
    finally:
        stamp_end(result)
    return result


# ── R07: show_day_plan with a meeting just added in same scenario ──────────


@register(
    name="show_day_plan_with_just_added_meeting",
    category=CATEGORY,
    description=(
        "setup client → add_meeting (in_person, jutro 14:00) → ✅ → "
        "'co mam jutro?' → day plan card lists the just-added meeting."
    ),
    default_in_run=False,
)
async def run_show_day_plan_with_just_added_meeting(
    harness: TelegramE2EHarness,
) -> ScenarioResult:
    result = new_result("show_day_plan_with_just_added_meeting", CATEGORY)
    name = e2e_beta_name("R07")
    tmr = tomorrow_warsaw()
    result.context["client_name"] = name
    result.context["expected_pl_date"] = fmt_pl_date(tmr)
    try:
        await reset_pending(harness)
        if not await setup_existing_client(harness, result, name):
            return result

        # Step 1: add a meeting tomorrow 14:00.
        meeting_trigger = f"jutro o 14:00 spotkanie z {name}, {E2E_BETA_CITY}"
        result.context["meeting_trigger"] = meeting_trigger
        await harness.send(meeting_trigger)
        meeting_replies = await harness.wait_for_messages(count=2, timeout_s=25.0)
        meeting_card = find_card_message(meeting_replies)
        if meeting_card is None:
            result.add_blocker("step1_meeting_card", "no meeting card")
            return result
        save_label, meeting_confirm = await click_save_and_collect(harness, meeting_card)
        if save_label is None:
            result.add_blocker("step1_meeting_save_button", "no ✅ on meeting card")
            return result
        await assert_save_confirmed(
            harness, result, meeting_confirm, check_key="step1_meeting_saved",
        )
        await post_setup_settle()

        # Step 2: ask for tomorrow's plan.
        await harness.send("co mam jutro?")
        plan_replies = await harness.wait_for_messages(count=1, timeout_s=20.0)
        result.context["plan_reply_count"] = len(plan_replies)
        if not plan_replies:
            result.add_blocker("step2_plan_reply", "no plan reply")
            return result
        plan = plan_replies[0]
        result.context["plan_reply_text"] = plan.text[:300]

        ok, detail = assert_no_buttons(plan)
        result.add("show_day_plan_no_buttons", ok, detail)

        # Plan should mention the just-added meeting (client name + 14:00).
        result.add(
            "plan_mentions_client_name",
            name in plan.text,
            detail=f"expected {name!r}; got: {plan.text[:240]!r}",
        )
        result.add(
            "plan_mentions_meeting_time",
            "14:00" in plan.text,
            detail=f"expected '14:00' in plan; got: {plan.text[:240]!r}",
        )

        ok, detail = assert_no_banned_phrases(plan.text)
        result.add("no_banned_phrases", ok, detail)

        ok, detail = assert_no_internal_leak(plan.text)
        result.add("no_internal_field_leak", ok, detail)
    except Exception as e:
        logger.exception("show_day_plan_with_just_added_meeting crashed")
        result.add_blocker("scenario_crash", f"{type(e).__name__}: {e}")
    finally:
        stamp_end(result)
    return result


# ── R08: show_client multi-match disambiguation (uses fixture) ────────────


@register(
    name="show_client_multi_match_disambig",
    category=CATEGORY,
    description=(
        "REQUIRES e2e_seed_fixtures pre-call. 'pokaż Jana Kowalskiego' → "
        "bot lists multiple matches (Warszawa + Kraków) for disambig."
    ),
    default_in_run=False,
)
async def run_show_client_multi_match_disambig(
    harness: TelegramE2EHarness,
) -> ScenarioResult:
    result = new_result("show_client_multi_match_disambig", CATEGORY)
    # Fixture names are E2E-Beta-Fixture-Jan-Kowalski (Warszawa + Kraków).
    # Bot's fuzzy/Polish-inflection search must surface BOTH when querying
    # by the first-name+last-name pair without a city.
    trigger = "pokaż Jana Kowalskiego"
    result.context["trigger"] = trigger
    result.context["fixture_dependency"] = (
        "Run mcp__oze-e2e__e2e_seed_fixtures before this scenario. "
        "Two E2E-Beta-Fixture-Jan-Kowalski rows must exist (Warszawa + Kraków)."
    )
    try:
        await reset_pending(harness)
        await harness.send(trigger)
        replies = await harness.wait_for_messages(count=1, timeout_s=20.0)
        result.context["reply_count"] = len(replies)
        if not replies:
            result.add_blocker("got_reply", "no reply within 20s")
            return result
        msg = replies[0]
        result.context["reply_text"] = msg.text[:400]
        result.context["reply_buttons"] = msg.button_labels

        # Multi-match should list both cities. Bot may format as text list
        # or inline buttons — accept either.
        warszawa_visible = "Warszawa" in msg.text or any(
            "Warszawa" in lbl for lbl in msg.button_labels
        )
        krakow_visible = (
            "Kraków" in msg.text or "Krakow" in msg.text
        ) or any("Kraków" in lbl or "Krakow" in lbl for lbl in msg.button_labels)
        result.add(
            "lists_warszawa_match",
            warszawa_visible,
            detail=f"expected 'Warszawa' marker; got: {msg.text[:300]!r}",
        )
        result.add(
            "lists_krakow_match",
            krakow_visible,
            detail=f"expected 'Kraków' marker; got: {msg.text[:300]!r}",
        )

        # No mutation card — disambig is read-only routing.
        result.add(
            "no_mutation_buttons",
            not any("Zapisać" in lbl or "Dopisać" in lbl for lbl in msg.button_labels),
            detail=f"buttons={msg.button_labels}",
        )

        ok, detail = assert_no_banned_phrases(msg.text)
        result.add("no_banned_phrases", ok, detail)
    except Exception as e:
        logger.exception("show_client_multi_match_disambig crashed")
        result.add_blocker("scenario_crash", f"{type(e).__name__}: {e}")
    finally:
        stamp_end(result)
    return result
