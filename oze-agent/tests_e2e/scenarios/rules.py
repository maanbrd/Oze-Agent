"""Phase 7A + 7B-final behaviour-rule scenarios.

7A:
- S16 cancel_one_click_no_loop (R1)

7B-final additions:
- T01 r3_auto_cancel_pending_on_unrelated_input (R3 route 1)
- T02 r3_explicit_dopisac_with_text_append   (R3 route 3)
- T03 r6_active_client_implicit_reference    (R6 active_client)
- T04 r7_next_action_prompt_after_add_client (R7 follow-up flow)
- T05 r8_frustration_calm_response           (R8 tone)

T01-T04 commit to Sheets/Calendar in some paths, so they're
`default_in_run=False`. T05 is no-write (just tests reply tone) and
also opted out of default for consistency.
"""

from __future__ import annotations

import logging

from tests_e2e.asserts import (
    assert_cancel_reply,
    assert_no_banned_phrases,
    assert_no_internal_leak,
    assert_three_button_card,
)
from tests_e2e.harness import TelegramE2EHarness
from tests_e2e.report import ScenarioResult
from tests_e2e.scenarios._base import new_result, register, stamp_end
from tests_e2e.scenarios._helpers import (
    E2E_BETA_CITY,
    assert_save_confirmed,
    click_save_and_collect,
    e2e_beta_name,
    find_card_message,
    is_save_confirmation,
    reset_pending,
    setup_existing_client,
    verify_calendar_event,
    verify_sheets_row,
)

logger = logging.getLogger(__name__)

CATEGORY = "rules"


@register(
    name="cancel_one_click_no_loop",
    category=CATEGORY,
    description=(
        "R1.❌Anulować must be one-click — zero 'Na pewno?' confirmation loop. "
        "Triggers an add_client card, clicks ❌ Anulować, expects 'Anulowane' once."
    ),
)
async def run_cancel_one_click_no_loop(
    harness: TelegramE2EHarness,
) -> ScenarioResult:
    result = new_result("cancel_one_click_no_loop", CATEGORY)
    name = e2e_beta_name("R1-cancel")
    trigger = f"dodaj klienta {name}, {E2E_BETA_CITY}, 600100200"
    result.context["trigger"] = trigger
    try:
        await reset_pending(harness)
        await harness.send(trigger)
        replies = await harness.wait_for_messages(count=2, timeout_s=20.0)
        if not replies:
            result.add(
                "got_card", False,
                detail="no reply", tag="blocker",
            )
            return result

        card_msg = next((m for m in replies if m.button_labels), None)
        if card_msg is None:
            result.add(
                "got_card", False,
                detail="no card with buttons",
                tag="blocker",
            )
            return result
        result.add("got_card", True, detail=str(card_msg.button_labels))

        cancel_label = next(
            (lbl for lbl in card_msg.button_labels if "Anulować" in lbl or "❌" in lbl),
            None,
        )
        if not cancel_label:
            result.add(
                "cancel_button_present", False,
                detail=f"no cancel in {card_msg.button_labels}",
            )
            return result
        result.add("cancel_button_present", True, detail=cancel_label)

        await harness.click_button(card_msg, cancel_label)

        # Collect ALL messages in the next 3s — we want to assert there is
        # at most one message AND no follow-up question.
        cancel_replies = await harness.collect_messages(duration_s=3.0)
        result.context["cancel_replies"] = [m.text[:120] for m in cancel_replies]
        result.context["cancel_reply_count"] = len(cancel_replies)

        # Bot may either edit the card in-place (zero new messages) OR
        # send a single short "Anulowane." line. Either is acceptable.
        if len(cancel_replies) == 0:
            result.add(
                "one_click_no_loop",
                True,
                detail="card edited in-place, no follow-up question",
                tag="known_drift",
                doc_ref="agent_behavior_spec_v5.md §2.R1 expects '🫡 Anulowane.' line",
            )
            return result

        # Reject any follow-up question shape ("Na pewno?", confirmation prompts).
        forbidden_phrases = (
            "na pewno", "czy na pewno", "potwierdź anulowanie", "potwierdz",
        )
        any_loop = any(
            any(phrase in m.text.lower() for phrase in forbidden_phrases)
            for m in cancel_replies
        )
        result.add(
            "no_confirmation_loop",
            not any_loop,
            detail=f"replies: {[m.text[:80] for m in cancel_replies]!r}",
        )

        # First (or only) cancel reply should match cancel-reply shape.
        ok, detail = assert_cancel_reply(cancel_replies[0])
        result.add("cancel_reply_short_with_keyword", ok, detail)

        # And exactly one cancel reply (one-click semantics).
        result.add(
            "exactly_one_cancel_message",
            len(cancel_replies) == 1,
            detail=f"got {len(cancel_replies)} replies after cancel",
            tag="pass" if len(cancel_replies) == 1 else "known_drift",
            doc_ref="agent_behavior_spec_v5.md §2.R1 — one-click",
        )
    except Exception as e:
        logger.exception("cancel_one_click_no_loop crashed")
        result.add("scenario_no_exception", False, detail=str(e))
    finally:
        stamp_end(result)
    return result


# ── T01: R3 auto-cancel pending on unrelated input ─────────────────────────


@register(
    name="r3_auto_cancel_pending_on_unrelated_input",
    category=CATEGORY,
    description=(
        "R3 route 1: trigger add_client card → send 'co mam dziś?' → "
        "bot auto-cancels add_client pending + shows day plan. NO Sheets "
        "write committed."
    ),
    default_in_run=False,
)
async def run_r3_auto_cancel_pending_on_unrelated_input(
    harness: TelegramE2EHarness,
) -> ScenarioResult:
    result = new_result("r3_auto_cancel_pending_on_unrelated_input", CATEGORY)
    name = e2e_beta_name("T01")
    add_trigger = f"dodaj klienta {name}, {E2E_BETA_CITY}, 600100200, PV"
    result.context["add_trigger"] = add_trigger
    result.context["client_name"] = name
    try:
        await reset_pending(harness)
        await harness.send(add_trigger)
        replies = await harness.wait_for_messages(count=2, timeout_s=20.0)
        card_msg = find_card_message(replies)
        if card_msg is None:
            result.add_blocker("got_card", "no add_client card with buttons")
            return result
        result.add("got_card", True, detail=str(card_msg.button_labels))

        # NOW send unrelated input — should auto-cancel pending and show day plan.
        unrelated_trigger = "co mam dziś?"
        result.context["unrelated_trigger"] = unrelated_trigger
        await harness.send(unrelated_trigger)
        # Allow generous window — bot may emit cancel ack + day plan separately.
        post_replies = await harness.collect_messages(duration_s=15.0)
        result.context["post_unrelated_reply_count"] = len(post_replies)
        result.context["post_unrelated_replies"] = [m.text[:160] for m in post_replies]

        # Assert: bot eventually shows a day plan or "Na dziś nic..." reply.
        all_text = "\n".join(m.text for m in post_replies)
        day_plan_signaled = (
            "📅" in all_text
            or "Na dziś" in all_text
            or "nic nie masz" in all_text.lower()
            or "co mam" in all_text.lower()
        )
        result.add(
            "day_plan_shown_after_unrelated",
            day_plan_signaled,
            detail=f"expected day plan marker; got: {all_text[:300]!r}",
        )

        # The pending add_client should NOT have committed (no row created).
        tid = harness.authenticated_user_id
        if tid is None:
            result.add_blocker("harness_authenticated", "no telegram_id")
        else:
            from tests_e2e.sheets_verify import find_client_row, resolve_user_id
            user_id = await resolve_user_id(tid)
            if user_id is None:
                result.add_blocker("resolve_user_id", f"no Supabase user for {tid}")
            else:
                row = await find_client_row(user_id, name, E2E_BETA_CITY)
                result.add(
                    "no_sheets_row_committed",
                    row is None,
                    detail=(
                        f"add_client should NOT commit on auto-cancel; "
                        f"row found: {row!r}"
                    ),
                )
    except Exception as e:
        logger.exception("r3_auto_cancel_pending_on_unrelated_input crashed")
        result.add_blocker("scenario_crash", f"{type(e).__name__}: {e}")
    finally:
        stamp_end(result)
    return result


# ── T02: R3 explicit ➕ Dopisać with text append ────────────────────────────


@register(
    name="r3_explicit_dopisac_with_text_append",
    category=CATEGORY,
    description=(
        "R3 route 3: trigger add_client card with minimal payload (missing "
        "tel + product) → click ➕ Dopisać → user sends 'tel 600100200, PV' "
        "→ card UPDATED → ✅ → Sheets row has tel + product."
    ),
    default_in_run=False,
)
async def run_r3_explicit_dopisac_with_text_append(
    harness: TelegramE2EHarness,
) -> ScenarioResult:
    result = new_result("r3_explicit_dopisac_with_text_append", CATEGORY)
    name = e2e_beta_name("T02")
    # Deliberately incomplete: name + city only, no tel/product.
    add_trigger = f"dodaj klienta {name}, {E2E_BETA_CITY}"
    fillin = "tel 600100200, PV"
    result.context["add_trigger"] = add_trigger
    result.context["fillin"] = fillin
    result.context["client_name"] = name
    try:
        await reset_pending(harness)
        await harness.send(add_trigger)
        replies = await harness.wait_for_messages(count=2, timeout_s=20.0)
        card_msg = find_card_message(replies)
        if card_msg is None:
            result.add_blocker("got_card", "no card with buttons")
            return result
        result.add("got_card", True, detail=str(card_msg.button_labels))

        dopisac_label = next(
            (
                lbl for lbl in card_msg.button_labels
                if "Dopisać" in lbl or "➕" in lbl
            ),
            None,
        )
        if dopisac_label is None:
            result.add_blocker(
                "dopisac_button_present",
                f"no ➕ Dopisać in {card_msg.button_labels}",
            )
            return result
        result.add("dopisac_button_present", True, detail=dopisac_label)

        await harness.click_button(card_msg, dopisac_label)
        post_dopisac_replies = await harness.collect_messages(duration_s=8.0)
        result.context["post_dopisac_reply_count"] = len(post_dopisac_replies)

        # Now user sends fill-in text — bot should treat it as appending fields.
        await harness.send(fillin)
        fill_replies = await harness.wait_for_messages(count=2, timeout_s=20.0)
        result.context["fill_reply_count"] = len(fill_replies)

        updated_card = find_card_message(fill_replies)
        if updated_card is None:
            result.add_blocker(
                "got_updated_card",
                f"no updated card after fill-in; got "
                f"{[m.text[:80] for m in fill_replies]}",
            )
            return result
        result.add("got_updated_card", True, detail=str(updated_card.button_labels))

        # Updated card should now contain the new fields.
        result.add(
            "updated_card_contains_phone",
            "600" in updated_card.text,
            detail=f"expected '600' marker; got: {updated_card.text[:240]!r}",
        )
        result.add(
            "updated_card_contains_product",
            "PV" in updated_card.text,
            detail=f"expected 'PV' marker; got: {updated_card.text[:240]!r}",
        )

        save_label, confirm_replies = await click_save_and_collect(harness, updated_card)
        if save_label is None:
            result.add_blocker("save_button_present", "no ✅ on updated card")
            return result
        result.add("save_button_present", True, detail=save_label)
        await assert_save_confirmed(harness, result, confirm_replies)

        # API verify: row has tel + product.
        tid = harness.authenticated_user_id
        if tid is not None:
            await verify_sheets_row(
                result, tid, name, E2E_BETA_CITY,
                expected_fields={"Telefon": "600", "Produkt": "PV"},
            )
    except Exception as e:
        logger.exception("r3_explicit_dopisac_with_text_append crashed")
        result.add_blocker("scenario_crash", f"{type(e).__name__}: {e}")
    finally:
        stamp_end(result)
    return result


# ── T03: R6 active_client implicit reference ──────────────────────────────


@register(
    name="r6_active_client_implicit_reference",
    category=CATEGORY,
    description=(
        "R6: setup client → 'dodaj notatkę: zainteresowany pompą' (NO "
        "client name) → bot uses active_client (last-mentioned) → ✅ → "
        "note appended to the right client's row."
    ),
    default_in_run=False,
)
async def run_r6_active_client_implicit_reference(
    harness: TelegramE2EHarness,
) -> ScenarioResult:
    result = new_result("r6_active_client_implicit_reference", CATEGORY)
    name = e2e_beta_name("T03")
    note_content = "zainteresowany pompą ciepła"
    result.context["client_name"] = name
    result.context["note_content"] = note_content
    try:
        await reset_pending(harness)
        if not await setup_existing_client(harness, result, name):
            return result

        # Note WITHOUT client name — relies on active_client from R6 context.
        note_trigger = f"dodaj notatkę: {note_content}"
        result.context["note_trigger"] = note_trigger
        await harness.send(note_trigger)
        replies = await harness.wait_for_messages(count=2, timeout_s=25.0)
        result.context["reply_count"] = len(replies)

        card_msg = find_card_message(replies)
        if card_msg is None:
            result.add_blocker(
                "got_note_card_via_active_client",
                f"R6 active_client failed — bot didn't bind note to last "
                f"client; got {[m.text[:80] for m in replies]}",
            )
            return result
        result.add("got_note_card_via_active_client", True, detail=str(card_msg.button_labels))

        # Card should reference the just-set-up client.
        result.add(
            "card_references_active_client_name",
            name in card_msg.text,
            detail=(
                f"R6 should put active client {name!r} on card; "
                f"got: {card_msg.text[:240]!r}"
            ),
        )
        result.add(
            "card_contains_note_content",
            "pompą" in card_msg.text or "pompa" in card_msg.text.lower(),
            detail=f"expected note text in card; got: {card_msg.text[:240]!r}",
        )

        ok, detail = assert_three_button_card(card_msg)
        result.add("three_button_mutation_card", ok, detail)

        save_label, confirm_replies = await click_save_and_collect(harness, card_msg)
        if save_label is None:
            result.add_blocker("save_button_present", "no ✅ on note card")
            return result
        result.add("save_button_present", True, detail=save_label)
        await assert_save_confirmed(harness, result, confirm_replies)

        tid = harness.authenticated_user_id
        if tid is not None:
            await verify_sheets_row(
                result, tid, name, E2E_BETA_CITY,
                expected_fields={"Notatki": "pompą"},
            )
    except Exception as e:
        logger.exception("r6_active_client_implicit_reference crashed")
        result.add_blocker("scenario_crash", f"{type(e).__name__}: {e}")
    finally:
        stamp_end(result)
    return result


# ── T04: R7 next-action prompt after add_client ────────────────────────────


@register(
    name="r7_next_action_prompt_after_add_client",
    category=CATEGORY,
    description=(
        "R7: setup client (don't close 'Co dalej' prompt) → reply with "
        "'spotkanie jutro o 14' → bot re-routes to add_meeting card for "
        "the same client → ✅ → meeting saved."
    ),
    default_in_run=False,
)
async def run_r7_next_action_prompt_after_add_client(
    harness: TelegramE2EHarness,
) -> ScenarioResult:
    result = new_result("r7_next_action_prompt_after_add_client", CATEGORY)
    name = e2e_beta_name("T04")
    result.context["client_name"] = name
    try:
        await reset_pending(harness)

        # Manually run the add_client → ✅ flow WITHOUT closing 'Co dalej'.
        # We need the bot's "Co dalej?" pending state intact for R7.
        add_trigger = f"dodaj klienta {name}, {E2E_BETA_CITY}, 600100200, PV"
        result.context["add_trigger"] = add_trigger
        await harness.send(add_trigger)
        add_replies = await harness.wait_for_messages(count=2, timeout_s=25.0)
        add_card = find_card_message(add_replies)
        if add_card is None:
            result.add_blocker("setup_card", "no add_client card")
            return result

        save_label, save_confirm = await click_save_and_collect(harness, add_card)
        if save_label is None:
            result.add_blocker("setup_save_button", "no ✅ on add_client card")
            return result
        if not save_confirm or not any(is_save_confirmation(m.text) for m in save_confirm):
            result.add_blocker(
                "setup_save_confirmed",
                f"add_client save unconfirmed; got "
                f"{[m.text[:80] for m in save_confirm]}",
            )
            return result
        result.add("setup_client_committed", True, detail=f"client {name} created")

        # 'Co dalej' should now be in the recent replies — verify it.
        co_dalej_visible = any("Co dalej" in m.text for m in save_confirm)
        result.add(
            "bot_emitted_co_dalej_prompt",
            co_dalej_visible,
            detail=(
                f"R7 needs the 'Co dalej' prompt; replies: "
                f"{[m.text[:120] for m in save_confirm]}"
            ),
        )

        # Reply with continuation — bot should re-route to add_meeting.
        next_action = "spotkanie jutro o 14:00"
        result.context["next_action_trigger"] = next_action
        await harness.send(next_action)
        meeting_replies = await harness.wait_for_messages(count=2, timeout_s=25.0)
        result.context["meeting_reply_count"] = len(meeting_replies)

        meeting_card = find_card_message(meeting_replies)
        if meeting_card is None:
            result.add_blocker(
                "got_meeting_card_via_r7",
                f"R7 reroute failed — no add_meeting card after 'spotkanie' "
                f"continuation; got {[m.text[:80] for m in meeting_replies]}",
            )
            return result
        result.add(
            "got_meeting_card_via_r7", True,
            detail=str(meeting_card.button_labels),
        )

        # Meeting card should bind to the just-saved client.
        result.add(
            "meeting_card_references_client",
            name in meeting_card.text,
            detail=f"expected {name!r}; got: {meeting_card.text[:240]!r}",
        )
        result.add(
            "meeting_card_has_14_00",
            "14:00" in meeting_card.text,
            detail=f"expected '14:00'; got: {meeting_card.text[:240]!r}",
        )

        save2_label, meeting_confirm = await click_save_and_collect(harness, meeting_card)
        if save2_label is None:
            result.add_blocker("meeting_save_button", "no ✅ on meeting card")
            return result
        result.add("meeting_save_button_present", True, detail=save2_label)
        await assert_save_confirmed(
            harness, result, meeting_confirm, check_key="meeting_saved",
        )

        # API verify: meeting event landed.
        tid = harness.authenticated_user_id
        if tid is not None:
            from datetime import datetime, timedelta
            from tests_e2e.scenarios._helpers import WARSAW, tomorrow_warsaw
            tmr = tomorrow_warsaw()
            target_dt = datetime(tmr.year, tmr.month, tmr.day, 14, 0, tzinfo=WARSAW)
            await verify_calendar_event(
                result, tid, name,
                start_window=target_dt - timedelta(hours=1),
                end_window=target_dt + timedelta(hours=2),
                expected_start=target_dt,
            )
    except Exception as e:
        logger.exception("r7_next_action_prompt_after_add_client crashed")
        result.add_blocker("scenario_crash", f"{type(e).__name__}: {e}")
    finally:
        stamp_end(result)
    return result


# ── T05: R8 frustration → calm response (no apology, no platitudes) ───────


@register(
    name="r8_frustration_calm_response",
    category=CATEGORY,
    description=(
        "R8: send 'nie działa to gówno' → bot replies calmly with "
        "'Co chcesz zrobić?'-class question. NO apology phrases "
        "('Rozumiem twoją frustrację', 'Powodzenia')."
    ),
    default_in_run=False,
)
async def run_r8_frustration_calm_response(
    harness: TelegramE2EHarness,
) -> ScenarioResult:
    result = new_result("r8_frustration_calm_response", CATEGORY)
    trigger = "nie działa to gówno"
    result.context["trigger"] = trigger
    try:
        await reset_pending(harness)
        await harness.send(trigger)
        replies = await harness.wait_for_messages(count=1, timeout_s=15.0)
        result.context["reply_count"] = len(replies)
        if not replies:
            result.add_blocker("got_reply", "no reply within 15s")
            return result
        msg = replies[0]
        result.context["reply_text"] = msg.text[:300]

        # Banned-phrase check covers the spec-forbidden apology phrases.
        ok, detail = assert_no_banned_phrases(msg.text)
        result.add("no_banned_phrases", ok, detail)
        ok, detail = assert_no_internal_leak(msg.text)
        result.add("no_internal_field_leak", ok, detail)

        # Reply should be SHORT (calm = brief).
        reply_lines = [ln for ln in msg.text.splitlines() if ln.strip()]
        result.add(
            "reply_is_short",
            len(reply_lines) <= 3,
            detail=f"got {len(reply_lines)} lines: {msg.text[:200]!r}",
        )

        # Calm-question marker — accept any short concrete question that
        # asks for clarification without apologizing. Bot wording varies:
        # "Co konkretnie nie działa?", "Co nie działa?", "Co chcesz?".
        calm_markers = (
            "co chcesz", "co chcesz zrobić", "co dalej", "co konkretnie",
            "co nie działa", "co nie",
            "powiedz", "podaj", "zacznijmy",
        )
        has_calm = any(m in msg.text.lower() for m in calm_markers)
        result.add(
            "reply_has_calm_question",
            has_calm,
            detail=(
                f"expected one of {calm_markers!r}; got: {msg.text[:240]!r}"
            ),
        )
    except Exception as e:
        logger.exception("r8_frustration_calm_response crashed")
        result.add_blocker("scenario_crash", f"{type(e).__name__}: {e}")
    finally:
        stamp_end(result)
    return result
