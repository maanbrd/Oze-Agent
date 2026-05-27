"""Edge-case campaign v1 for high-risk OZE-Agent flows.

These scenarios are opt-in only. Run explicitly with:

    python -m tests_e2e.runner --category edge_case
"""

from __future__ import annotations

import logging
import os
from datetime import date, datetime, time, timedelta
from pathlib import Path
from uuid import uuid4

from shared.database import delete_active_photo_session, delete_pending_flow
from shared.google_drive import extract_folder_id, get_client_photos
from shared.google_sheets import update_client
from shared.offers.numbering import list_ready_with_numbers
from shared.offers.repository import OfferRepository
from tests_e2e.asserts import (
    assert_no_buttons,
    assert_no_internal_leak,
    assert_pl_date_format,
    assert_three_button_card,
)
from tests_e2e.fixtures import cleanup_synthetic_data
from tests_e2e.harness import TelegramE2EHarness, _ObservedMessage
from tests_e2e.post_campaign_checks import (
    OFFER_RECIPIENT_ENV,
    _cleanup_offer_attempts_for_client,
    _delete_drive_folder,
    _find_matching_card_message,
    _offer_send_reply_acknowledged,
    _wait_for_matching_card,
    _write_test_jpeg,
)
from tests_e2e.report import ScenarioResult
from tests_e2e.scenarios._base import new_result, register, stamp_end
from tests_e2e.scenarios._helpers import (
    WARSAW,
    assert_save_confirmed,
    card_mentions_date_pl_str,
    click_save_and_collect,
    find_card_message,
    fmt_pl_date,
    reset_pending,
    setup_existing_client,
    wait_for_card_messages,
)
from tests_e2e.sheets_verify import find_client_row, resolve_user_id

logger = logging.getLogger(__name__)

CATEGORY = "edge_case"
CITY_A = "Opole"
CITY_B = "Kraków"


def _run_id() -> str:
    return datetime.now(tz=WARSAW).strftime("%H%M%S") + "-" + uuid4().hex[:6]


def _edge_name(run_id: str, suffix: str = "") -> str:
    base = f"E2E Beta Klient {run_id}"
    return f"{base} {suffix}" if suffix else base


def _edge_email(slug: str, run_id: str) -> str:
    return f"{slug}+{run_id}@e2e-noinbox.local"


def _gmail_plus_alias(email: str, run_id: str) -> str:
    local, at, domain = email.partition("@")
    if not at:
        return email
    return f"{local}+edge{run_id.replace('-', '')}@{domain}"


def _all_text(messages: list[_ObservedMessage]) -> str:
    return "\n".join(m.text for m in messages)


def _looks_like_disambiguation(text: str) -> bool:
    lower = text.lower()
    return any(marker in lower for marker in ("którego", "ktorego", "kilka", "mam 2", "mam 3", "nieaktualny przycisk"))


def _looks_like_missing_email_offer_reply(text: str) -> bool:
    lower = text.lower()
    return "email" in lower and any(marker in lower for marker in ("brak", "brakuje", "podaj", "uzupełnij", "uzupelnij"))


def _has_mutation_buttons(messages: list[_ObservedMessage]) -> bool:
    mutation_labels = {"✅ Zapisać", "➕ Dopisać", "❌ Anulować", "✅ Wysłać"}
    return any(
        any(label in mutation_labels for label in message.button_labels)
        for message in messages
    )


def _next_named_weekday(start: date, *, target_weekday: int, force_next: bool) -> date:
    delta = (target_weekday - start.weekday()) % 7
    if delta == 0 or force_next:
        delta += 7
    return start + timedelta(days=delta)


async def _cleanup_after(harness: TelegramE2EHarness, result: ScenarioResult, *, run_id: str | None = None) -> None:
    telegram_id = harness.authenticated_user_id
    if telegram_id is None:
        return
    try:
        delete_pending_flow(telegram_id)
        delete_active_photo_session(telegram_id)
        cleanup = await cleanup_synthetic_data(telegram_id, run_id=run_id)
        result.context["cleanup"] = cleanup
    except Exception as exc:
        result.context["cleanup_error"] = f"{type(exc).__name__}: {exc}"


async def _hard_reset(harness: TelegramE2EHarness) -> None:
    await reset_pending(harness)
    telegram_id = harness.authenticated_user_id
    if telegram_id is None:
        return
    delete_pending_flow(telegram_id)
    delete_active_photo_session(telegram_id)
    await harness.collect_messages(duration_s=1.0)


async def _user_id_or_blocker(harness: TelegramE2EHarness, result: ScenarioResult) -> str | None:
    telegram_id = harness.authenticated_user_id
    if telegram_id is None:
        result.add_blocker("harness_authenticated", "no authenticated user id")
        return None
    user_id = await resolve_user_id(telegram_id)
    if not user_id:
        result.add_blocker("resolve_user_id", f"no Supabase user for telegram_id={telegram_id}")
        return None
    return user_id


async def _add_client_card(
    harness: TelegramE2EHarness,
    result: ScenarioResult,
    *,
    name: str,
    city: str,
    extra_fields: str,
    check_key: str,
) -> _ObservedMessage | None:
    trigger = f"dodaj klienta {name}, {city}, {extra_fields}"
    result.context[f"{check_key}_trigger"] = trigger
    await harness.send(trigger)
    replies = await wait_for_card_messages(harness, timeout_s=30.0)
    result.context[f"{check_key}_replies"] = [m.text[:240] for m in replies]
    card = find_card_message(replies)
    if card is None:
        result.add_blocker(f"{check_key}_card", f"no card; got {[m.text[:120] for m in replies]}")
        return None
    result.add(f"{check_key}_card", True, detail=str(card.button_labels))
    return card


async def _add_client_and_save(
    harness: TelegramE2EHarness,
    result: ScenarioResult,
    *,
    name: str,
    city: str,
    extra_fields: str,
    check_key: str = "setup",
) -> bool:
    card = await _add_client_card(
        harness,
        result,
        name=name,
        city=city,
        extra_fields=extra_fields,
        check_key=check_key,
    )
    if card is None:
        return False
    label, replies = await click_save_and_collect(harness, card, duration_s=20.0)
    if label is None:
        result.add_blocker(f"{check_key}_save_button", f"buttons={card.button_labels}")
        return False
    result.add(f"{check_key}_save_button", True, detail=label)
    return await assert_save_confirmed(harness, result, replies, check_key=f"{check_key}_saved")


async def _send_offer_and_get_card(
    harness: TelegramE2EHarness,
    result: ScenarioResult,
    *,
    name: str,
    city: str,
    offer_number: int,
    template_name: str,
    command_suffix: str = "",
) -> _ObservedMessage | None:
    command = f"wyślij ofertę nr {offer_number} dla {name} {city}{command_suffix}".strip()
    result.context["offer_command"] = command
    await harness.send(command)
    replies = await _wait_for_matching_card(
        harness,
        required_buttons=("✅ Wysłać", "❌ Anulować"),
        text_markers=(name, template_name),
        timeout_s=30.0,
    )
    result.context["offer_card_replies"] = [m.text[:300] for m in replies]
    card = _find_matching_card_message(
        replies,
        required_buttons=("✅ Wysłać", "❌ Anulować"),
        text_markers=(name, template_name),
    )
    return card


def _offer_attempts_for_client(repo: OfferRepository, user_id: str, name: str, city: str) -> list[dict]:
    result = (
        repo.client.table("offer_send_attempts")
        .select("id, status, gmail_message_id, client_name, client_city, created_at")
        .eq("user_id", user_id)
        .eq("client_name", name)
        .eq("client_city", city)
        .execute()
    )
    return result.data or []


def _ready_offer(result: ScenarioResult, user_id: str) -> tuple[OfferRepository | None, dict | None]:
    repo = OfferRepository()
    templates = list_ready_with_numbers(repo.list_templates(user_id))
    result.add("ready_offer_templates_present", bool(templates), detail=str([t.get("number") for t in templates[:5]]))
    if not templates:
        return repo, None
    return repo, templates[0]


@register(
    name="stale_save_button_rejected",
    category=CATEGORY,
    description="Old add_client ✅ after a newer pending flow must be rejected and write nothing.",
    default_in_run=False,
)
async def run_stale_save_button_rejected(harness: TelegramE2EHarness) -> ScenarioResult:
    result = new_result("stale_save_button_rejected", CATEGORY)
    run_id = _run_id()
    name_old = _edge_name(run_id, "Stary")
    name_new = _edge_name(run_id, "Nowy")
    try:
        await _hard_reset(harness)
        user_id = await _user_id_or_blocker(harness, result)
        if not user_id:
            return result
        old_card = await _add_client_card(
            harness,
            result,
            name=name_old,
            city=CITY_A,
            extra_fields=f"600100200, PV, email {_edge_email('stale.old', run_id)}",
            check_key="old",
        )
        if old_card is None:
            return result
        new_card = await _add_client_card(
            harness,
            result,
            name=name_new,
            city=CITY_A,
            extra_fields=f"600100201, PV, email {_edge_email('stale.new', run_id)}",
            check_key="new",
        )
        if new_card is None:
            return result
        await harness.click_button(old_card, "✅ Zapisać")
        replies = await harness.collect_messages(duration_s=5.0)
        refreshed = await harness.refetch_message(old_card)
        text = _all_text(replies) or refreshed.text
        result.context["stale_click_reply"] = text[:240]
        result.add(
            "stale_button_rejected",
            "Nieaktualny przycisk" in text,
            detail=text[:240],
        )
        row = await find_client_row(user_id, name_old, CITY_A)
        result.add("old_client_not_written", row is None, detail=str(row))
        await harness.click_button(new_card, "❌ Anulować")
        await harness.collect_messages(duration_s=3.0)
    except Exception as exc:
        logger.exception("stale_save_button_rejected crashed")
        result.add_blocker("scenario_crash", f"{type(exc).__name__}: {exc}")
    finally:
        await _cleanup_after(harness, result, run_id=run_id)
        stamp_end(result)
    return result


@register(
    name="duplicate_same_name_two_cities_show_client",
    category=CATEGORY,
    description="Two same-name clients in different cities; show_client without city must disambiguate.",
    default_in_run=False,
)
async def run_duplicate_same_name_two_cities_show_client(harness: TelegramE2EHarness) -> ScenarioResult:
    result = new_result("duplicate_same_name_two_cities_show_client", CATEGORY)
    run_id = _run_id()
    name = _edge_name(run_id, "Duplikat")
    try:
        await _hard_reset(harness)
        if not await setup_existing_client(harness, result, name, CITY_A, f"600100210, PV, email {_edge_email('dup.a', run_id)}"):
            return result
        if not await setup_existing_client(harness, result, name, CITY_B, f"600100211, PV, email {_edge_email('dup.b', run_id)}"):
            return result
        await harness.send(f"pokaż {name}")
        replies = await harness.wait_for_messages(count=1, timeout_s=25.0)
        text = _all_text(replies)
        result.context["show_reply"] = text[:400]
        result.add("reply_is_disambiguation", _looks_like_disambiguation(text), detail=text[:240])
        result.add("reply_mentions_both_cities", CITY_A in text and CITY_B in text, detail=text[:240])
        if replies:
            ok, detail = assert_no_internal_leak(replies[0].text)
            result.add("no_internal_field_leak", ok, detail)
    except Exception as exc:
        logger.exception("duplicate_same_name_two_cities_show_client crashed")
        result.add_blocker("scenario_crash", f"{type(exc).__name__}: {exc}")
    finally:
        await _cleanup_after(harness, result, run_id=run_id)
        stamp_end(result)
    return result


@register(
    name="duplicate_add_note_requires_city_or_choice",
    category=CATEGORY,
    description="add_note for duplicated same-name client without city must ask which one and not write silently.",
    default_in_run=False,
)
async def run_duplicate_add_note_requires_city_or_choice(harness: TelegramE2EHarness) -> ScenarioResult:
    result = new_result("duplicate_add_note_requires_city_or_choice", CATEGORY)
    run_id = _run_id()
    name = _edge_name(run_id, "Notatka")
    marker = f"edge-notatka-{run_id}"
    try:
        await _hard_reset(harness)
        user_id = await _user_id_or_blocker(harness, result)
        if not user_id:
            return result
        if not await setup_existing_client(harness, result, name, CITY_A, f"600100220, PV, email {_edge_email('note.a', run_id)}"):
            return result
        if not await setup_existing_client(harness, result, name, CITY_B, f"600100221, PV, email {_edge_email('note.b', run_id)}"):
            return result
        await harness.send(f"{name}: {marker}")
        replies = await harness.wait_for_messages(count=2, timeout_s=25.0)
        text = _all_text(replies)
        result.context["note_reply"] = text[:400]
        result.add("reply_requires_choice", _looks_like_disambiguation(text), detail=text[:240])
        result.add("no_mutation_card_before_choice", not _has_mutation_buttons(replies), detail=str([m.button_labels for m in replies]))
        row_a = await find_client_row(user_id, name, CITY_A)
        row_b = await find_client_row(user_id, name, CITY_B)
        notes = f"{(row_a or {}).get('Notatki', '')}\n{(row_b or {}).get('Notatki', '')}"
        result.add("note_not_written_without_choice", marker not in notes, detail=notes[:240])
    except Exception as exc:
        logger.exception("duplicate_add_note_requires_city_or_choice crashed")
        result.add_blocker("scenario_crash", f"{type(exc).__name__}: {exc}")
    finally:
        await _cleanup_after(harness, result, run_id=run_id)
        stamp_end(result)
    return result


@register(
    name="pending_dopisac_then_unrelated_command",
    category=CATEGORY,
    description="After ➕ Dopisać, unrelated show_day_plan must not write the pending client.",
    default_in_run=False,
)
async def run_pending_dopisac_then_unrelated_command(harness: TelegramE2EHarness) -> ScenarioResult:
    result = new_result("pending_dopisac_then_unrelated_command", CATEGORY)
    run_id = _run_id()
    name = _edge_name(run_id, "Dopisac")
    try:
        await _hard_reset(harness)
        user_id = await _user_id_or_blocker(harness, result)
        if not user_id:
            return result
        card = await _add_client_card(
            harness,
            result,
            name=name,
            city=CITY_A,
            extra_fields=f"email {_edge_email('dopisac', run_id)}",
            check_key="pending",
        )
        if card is None:
            return result
        await harness.click_button(card, "➕ Dopisać")
        await harness.collect_messages(duration_s=5.0)
        await harness.send("co mam dziś?")
        replies = await harness.collect_messages(duration_s=15.0)
        text = _all_text(replies)
        result.context["unrelated_reply"] = text[:400]
        result.add("day_plan_shown", "📅" in text or "Na dziś" in text or "nic nie masz" in text.lower(), detail=text[:240])
        row = await find_client_row(user_id, name, CITY_A)
        result.add("pending_client_not_written", row is None, detail=str(row))
    except Exception as exc:
        logger.exception("pending_dopisac_then_unrelated_command crashed")
        result.add_blocker("scenario_crash", f"{type(exc).__name__}: {exc}")
    finally:
        await _cleanup_after(harness, result, run_id=run_id)
        stamp_end(result)
    return result


@register(
    name="multi_intent_status_plus_meeting",
    category=CATEGORY,
    description="Status + meeting in one message must show compound card and commit both only after ✅.",
    default_in_run=False,
)
async def run_multi_intent_status_plus_meeting(harness: TelegramE2EHarness) -> ScenarioResult:
    result = new_result("multi_intent_status_plus_meeting", CATEGORY)
    run_id = _run_id()
    name = _edge_name(run_id, "Compound")
    target = _next_named_weekday(datetime.now(tz=WARSAW).date(), target_weekday=4, force_next=True)
    try:
        await _hard_reset(harness)
        user_id = await _user_id_or_blocker(harness, result)
        if not user_id:
            return result
        if not await setup_existing_client(harness, result, name, CITY_A, f"600100230, PV, email {_edge_email('compound', run_id)}"):
            return result
        trigger = f"{name} podpisał umowę, spotkanie w przyszły piątek o 10"
        result.context["trigger"] = trigger
        await harness.send(trigger)
        replies = await wait_for_card_messages(harness, timeout_s=30.0)
        card = find_card_message(replies)
        if card is None:
            result.add_blocker("compound_card", f"no card; got {[m.text[:120] for m in replies]}")
            return result
        result.context["compound_card"] = card.text[:400]
        ok, detail = assert_three_button_card(card)
        result.add("three_button_compound_card", ok, detail)
        result.add("card_mentions_status", "Podpis" in card.text, detail=card.text[:240])
        result.add("card_mentions_meeting_date", card_mentions_date_pl_str(card.text, target.strftime("%d.%m.%Y")), detail=card.text[:240])
        before = await find_client_row(user_id, name, CITY_A)
        result.add("no_status_write_before_confirm", (before or {}).get("Status") != "Podpisane", detail=str((before or {}).get("Status")))
        label, confirm = await click_save_and_collect(harness, card, duration_s=20.0)
        if label is None:
            result.add_blocker("save_button_present", f"buttons={card.button_labels}")
            return result
        await assert_save_confirmed(harness, result, confirm)
        row = await find_client_row(user_id, name, CITY_A)
        result.add("status_written_after_confirm", (row or {}).get("Status") == "Podpisane", detail=str(row))
    except Exception as exc:
        logger.exception("multi_intent_status_plus_meeting crashed")
        result.add_blocker("scenario_crash", f"{type(exc).__name__}: {exc}")
    finally:
        await _cleanup_after(harness, result, run_id=run_id)
        stamp_end(result)
    return result


@register(
    name="relative_date_next_friday",
    category=CATEGORY,
    description="'w przyszły piątek' must resolve to a future Friday on the confirmation card.",
    default_in_run=False,
)
async def run_relative_date_next_friday(harness: TelegramE2EHarness) -> ScenarioResult:
    result = new_result("relative_date_next_friday", CATEGORY)
    run_id = _run_id()
    name = _edge_name(run_id, "Piatek")
    expected = _next_named_weekday(datetime.now(tz=WARSAW).date(), target_weekday=4, force_next=True)
    try:
        await _hard_reset(harness)
        if not await setup_existing_client(harness, result, name, CITY_A, f"ul. Testowa 1, 600100235, PV, email {_edge_email('friday', run_id)}"):
            return result
        await harness.send(f"spotkanie z {name} z {CITY_A} w przyszły piątek o 10")
        replies = await wait_for_card_messages(harness, timeout_s=30.0)
        card = find_card_message(replies)
        if card is None:
            result.add_blocker("meeting_card", f"no card; got {[m.text[:120] for m in replies]}")
            return result
        result.context["meeting_card"] = card.text[:400]
        result.add("card_mentions_expected_friday", expected.strftime("%d.%m.%Y") in card.text, detail=f"expected {fmt_pl_date(expected)}; got {card.text[:240]!r}")
        result.add("date_is_future", expected > datetime.now(tz=WARSAW).date(), detail=fmt_pl_date(expected))
        ok, detail = assert_pl_date_format(card.text)
        result.add("pl_date_format", ok, detail)
        await harness.click_button(card, "❌ Anulować")
        await harness.collect_messages(duration_s=3.0)
    except Exception as exc:
        logger.exception("relative_date_next_friday crashed")
        result.add_blocker("scenario_crash", f"{type(exc).__name__}: {exc}")
    finally:
        await _cleanup_after(harness, result, run_id=run_id)
        stamp_end(result)
    return result


@register(
    name="past_date_no_card",
    category=CATEGORY,
    description="Past meeting date should be rejected without a mutation card or write.",
    default_in_run=False,
)
async def run_past_date_no_card(harness: TelegramE2EHarness) -> ScenarioResult:
    result = new_result("past_date_no_card", CATEGORY)
    run_id = _run_id()
    name = _edge_name(run_id, "Past")
    try:
        await _hard_reset(harness)
        await harness.send(f"wczoraj o 10 spotkanie z {name} z {CITY_A}")
        replies = await harness.wait_for_messages(count=2, timeout_s=25.0)
        text = _all_text(replies)
        result.context["reply"] = text[:400]
        result.add("past_date_rejected", "przeszłości" in text or "przeszlosci" in text.lower(), detail=text[:240])
        result.add("no_mutation_card", find_card_message(replies) is None, detail=str([m.button_labels for m in replies]))
    except Exception as exc:
        logger.exception("past_date_no_card crashed")
        result.add_blocker("scenario_crash", f"{type(exc).__name__}: {exc}")
    finally:
        await _cleanup_after(harness, result, run_id=run_id)
        stamp_end(result)
    return result


@register(
    name="active_client_pronoun_not_silent_write",
    category=CATEGORY,
    description="Ambiguous pronoun note must ask for client instead of silently writing to a guessed active client.",
    default_in_run=False,
)
async def run_active_client_pronoun_not_silent_write(harness: TelegramE2EHarness) -> ScenarioResult:
    result = new_result("active_client_pronoun_not_silent_write", CATEGORY)
    marker = f"edge-pronoun-{_run_id()}"
    try:
        await _hard_reset(harness)
        await harness.send(f"dopisz mu notatkę: {marker}")
        replies = await harness.wait_for_messages(count=2, timeout_s=25.0)
        text = _all_text(replies)
        result.context["reply"] = text[:400]
        asks_for_client = any(m in text.lower() for m in ("którego", "ktorego", "podaj", "klienta", "nie wiem"))
        result.add("asks_for_client", asks_for_client, detail=text[:240])
        result.add("no_mutation_card_without_client", find_card_message(replies) is None, detail=str([m.button_labels for m in replies]))
    except Exception as exc:
        logger.exception("active_client_pronoun_not_silent_write crashed")
        result.add_blocker("scenario_crash", f"{type(exc).__name__}: {exc}")
    finally:
        await _cleanup_after(harness, result)
        stamp_end(result)
    return result


@register(
    name="offer_missing_email_no_send",
    category=CATEGORY,
    description="Offer send for a client without email must ask for email and create no send attempt.",
    default_in_run=False,
)
async def run_offer_missing_email_no_send(harness: TelegramE2EHarness) -> ScenarioResult:
    result = new_result("offer_missing_email_no_send", CATEGORY)
    run_id = _run_id()
    name = _edge_name(run_id)
    city = CITY_A
    repo: OfferRepository | None = None
    try:
        await _hard_reset(harness)
        user_id = await _user_id_or_blocker(harness, result)
        if not user_id:
            return result
        repo, template = _ready_offer(result, user_id)
        if template is None:
            return result
        if not await _add_client_and_save(harness, result, name=name, city=city, extra_fields="600100240, PV", check_key="client"):
            return result
        await harness.send(f"wyślij ofertę nr {int(template['number'])} dla {name} {city}")
        replies = await harness.collect_messages(duration_s=20.0)
        text = _all_text(replies)
        result.context["offer_reply"] = text[:400]
        result.add("missing_email_requested", _looks_like_missing_email_offer_reply(text), detail=text[:240])
        attempts = _offer_attempts_for_client(repo, user_id, name, city)
        result.add("no_offer_attempt_created", len(attempts) == 0, detail=str(attempts))
    except Exception as exc:
        logger.exception("offer_missing_email_no_send crashed")
        result.add_blocker("scenario_crash", f"{type(exc).__name__}: {exc}")
    finally:
        if repo is not None:
            _cleanup_offer_attempts_for_client(repo, user_id=await resolve_user_id(harness.authenticated_user_id or 0) or "", name=name, city=city)
        await _cleanup_after(harness, result, run_id=run_id)
        stamp_end(result)
    return result


@register(
    name="offer_two_emails_single_attempt",
    category=CATEGORY,
    description="Two valid emails must produce one sent offer attempt with a Gmail message id.",
    default_in_run=False,
)
async def run_offer_two_emails_single_attempt(harness: TelegramE2EHarness) -> ScenarioResult:
    result = new_result("offer_two_emails_single_attempt", CATEGORY)
    recipient = os.getenv(OFFER_RECIPIENT_ENV, "").strip()
    run_id = _run_id()
    name = _edge_name(run_id)
    city = CITY_A
    repo: OfferRepository | None = None
    user_id = ""
    try:
        await _hard_reset(harness)
        result.add("offer_recipient_configured", bool(recipient), detail=OFFER_RECIPIENT_ENV)
        if not recipient:
            return result
        user_id = await _user_id_or_blocker(harness, result) or ""
        if not user_id:
            return result
        repo, template = _ready_offer(result, user_id)
        if template is None:
            return result
        alias = _gmail_plus_alias(recipient, run_id)
        extra = f"600100250, PV, email {recipient}, {alias}"
        if not await _add_client_and_save(harness, result, name=name, city=city, extra_fields=extra, check_key="client"):
            return result
        card = await _send_offer_and_get_card(
            harness,
            result,
            name=name,
            city=city,
            offer_number=int(template["number"]),
            template_name=str(template.get("name") or ""),
        )
        if card is None:
            result.add_blocker("offer_card", "no offer card")
            return result
        result.add("offer_card_mentions_both_recipients", recipient in card.text and alias in card.text, detail=card.text[:300])
        before = _offer_attempts_for_client(repo, user_id, name, city)
        await harness.click_button(card, "✅ Wysłać")
        replies = await harness.collect_messages(duration_s=20.0)
        result.add("telegram_offer_send_acknowledged", _offer_send_reply_acknowledged(_all_text(replies)), detail=_all_text(replies)[:240])
        after = _offer_attempts_for_client(repo, user_id, name, city)
        sent = [a for a in after if a.get("status") == "sent"]
        result.add("single_offer_attempt_created", len(after) == len(before) + 1, detail=str(after))
        result.add("sent_attempt_has_gmail_message_id", bool(sent and sent[-1].get("gmail_message_id")), detail=str(sent[-1] if sent else ""))
    except Exception as exc:
        logger.exception("offer_two_emails_single_attempt crashed")
        result.add_blocker("scenario_crash", f"{type(exc).__name__}: {exc}")
    finally:
        if repo is not None and user_id:
            _cleanup_offer_attempts_for_client(repo, user_id=user_id, name=name, city=city)
        await _cleanup_after(harness, result, run_id=run_id)
        stamp_end(result)
    return result


@register(
    name="offer_invalid_extra_email_skipped",
    category=CATEGORY,
    description="Invalid extra email should be skipped while valid recipients remain sendable.",
    default_in_run=False,
)
async def run_offer_invalid_extra_email_skipped(harness: TelegramE2EHarness) -> ScenarioResult:
    result = new_result("offer_invalid_extra_email_skipped", CATEGORY)
    recipient = os.getenv(OFFER_RECIPIENT_ENV, "").strip()
    run_id = _run_id()
    name = _edge_name(run_id)
    city = CITY_A
    repo: OfferRepository | None = None
    user_id = ""
    try:
        await _hard_reset(harness)
        result.add("offer_recipient_configured", bool(recipient), detail=OFFER_RECIPIENT_ENV)
        if not recipient:
            return result
        user_id = await _user_id_or_blocker(harness, result) or ""
        if not user_id:
            return result
        repo, template = _ready_offer(result, user_id)
        if template is None:
            return result
        if not await _add_client_and_save(harness, result, name=name, city=city, extra_fields=f"600100260, PV, email {recipient}", check_key="client"):
            return result
        row = await find_client_row(user_id, name, city)
        row_number = int((row or {}).get("_row") or 0)
        result.add("client_row_found_for_invalid_email_setup", row_number > 0, detail=str(row))
        if not row_number:
            return result
        updated = await update_client(user_id, row_number, {"Email": f"{recipient}; zły-email"})
        result.add("invalid_email_fixture_written", updated, detail=f"row={row_number}")
        if not updated:
            return result
        card = await _send_offer_and_get_card(
            harness,
            result,
            name=name,
            city=city,
            offer_number=int(template["number"]),
            template_name=str(template.get("name") or ""),
        )
        if card is None:
            result.add_blocker("offer_card", "no offer card")
            return result
        result.add("valid_recipient_present", recipient in card.text, detail=card.text[:300])
        result.add("invalid_recipient_skip_visible", "Pominięte błędne adresy" in card.text, detail=card.text[:300])
        await harness.click_button(card, "✅ Wysłać")
        replies = await harness.collect_messages(duration_s=20.0)
        result.add("telegram_offer_send_acknowledged", _offer_send_reply_acknowledged(_all_text(replies)), detail=_all_text(replies)[:240])
        attempts = _offer_attempts_for_client(repo, user_id, name, city)
        sent = [a for a in attempts if a.get("status") == "sent"]
        result.add("sent_attempt_created", bool(sent), detail=str(sent))
    except Exception as exc:
        logger.exception("offer_invalid_extra_email_skipped crashed")
        result.add_blocker("scenario_crash", f"{type(exc).__name__}: {exc}")
    finally:
        if repo is not None and user_id:
            _cleanup_offer_attempts_for_client(repo, user_id=user_id, name=name, city=city)
        await _cleanup_after(harness, result, run_id=run_id)
        stamp_end(result)
    return result


@register(
    name="photo_session_three_files",
    category=CATEGORY,
    description="After first photo confirm, two captionless photos should land in the same folder and Sheets count should be 3.",
    default_in_run=False,
)
async def run_photo_session_three_files(harness: TelegramE2EHarness) -> ScenarioResult:
    result = new_result("photo_session_three_files", CATEGORY)
    run_id = _run_id()
    name = _edge_name(run_id, "PhotoThree")
    city = CITY_A
    folder_id = ""
    try:
        await _hard_reset(harness)
        delete_active_photo_session(harness.authenticated_user_id or 0)
        user_id = await _user_id_or_blocker(harness, result)
        if not user_id:
            return result
        if not await _add_client_and_save(harness, result, name=name, city=city, extra_fields=f"600100270, PV, email {_edge_email('photo.three', run_id)}", check_key="client"):
            return result
        image_path = Path("/tmp/oze-edge-photo-three.png")
        _write_test_jpeg(image_path)
        await harness.send_file(image_path, caption=f"zdjęcia do {name} {city}")
        replies = await wait_for_card_messages(harness, timeout_s=30.0)
        card = find_card_message(replies)
        if card is None:
            result.add_blocker("photo_card", "no photo confirmation card")
            return result
        label, save_replies = await click_save_and_collect(harness, card, duration_s=20.0)
        if label is None:
            result.add_blocker("photo_save_button", f"buttons={card.button_labels}")
            return result
        result.add("first_photo_saved", bool(save_replies), detail=str([m.text[:120] for m in save_replies]))
        await harness.send_file(image_path)
        await harness.collect_messages(duration_s=10.0)
        await harness.send_file(image_path)
        await harness.collect_messages(duration_s=10.0)
        row = await find_client_row(user_id, name, city)
        folder_link = str((row or {}).get("Link do zdjęć", ""))
        folder_id = extract_folder_id(folder_link) or ""
        photo_count = str((row or {}).get("Zdjęcia", "")).strip()
        result.add("sheet_photo_count_is_three", photo_count == "3", detail=str(row))
        photos = await get_client_photos(user_id, folder_id) if folder_id else []
        result.add("drive_has_three_files", len(photos) >= 3, detail=str(photos[:5]))
    except Exception as exc:
        logger.exception("photo_session_three_files crashed")
        result.add_blocker("scenario_crash", f"{type(exc).__name__}: {exc}")
    finally:
        if folder_id and (harness.authenticated_user_id is not None):
            user_id = await resolve_user_id(harness.authenticated_user_id)
            if user_id:
                result.add("drive_folder_cleanup", await _delete_drive_folder(user_id, folder_id), detail=folder_id)
        await _cleanup_after(harness, result, run_id=run_id)
        stamp_end(result)
    return result


@register(
    name="photo_session_switch_client",
    category=CATEGORY,
    description="Caption 'zdjęcia do ...' during an active photo session should switch to a new confirmation card.",
    default_in_run=False,
)
async def run_photo_session_switch_client(harness: TelegramE2EHarness) -> ScenarioResult:
    result = new_result("photo_session_switch_client", CATEGORY)
    run_id = _run_id()
    old_name = _edge_name(run_id, "PhotoOld")
    new_name = _edge_name(run_id, "PhotoNew")
    folder_id = ""
    try:
        await _hard_reset(harness)
        user_id = await _user_id_or_blocker(harness, result)
        if not user_id:
            return result
        if not await _add_client_and_save(harness, result, name=old_name, city=CITY_A, extra_fields=f"600100280, PV, email {_edge_email('photo.old', run_id)}", check_key="old_client"):
            return result
        if not await _add_client_and_save(harness, result, name=new_name, city=CITY_B, extra_fields=f"600100281, PV, email {_edge_email('photo.new', run_id)}", check_key="new_client"):
            return result
        image_path = Path("/tmp/oze-edge-photo-switch.png")
        _write_test_jpeg(image_path)
        await harness.send_file(image_path, caption=f"zdjęcia do {old_name} {CITY_A}")
        replies = await wait_for_card_messages(harness, timeout_s=30.0)
        old_card = find_card_message(replies)
        if old_card is None:
            result.add_blocker("old_photo_card", "no first photo card")
            return result
        _, save_replies = await click_save_and_collect(harness, old_card, duration_s=20.0)
        result.context["old_photo_save_replies"] = [m.text[:160] for m in save_replies]
        old_row = await find_client_row(user_id, old_name, CITY_A)
        folder_id = extract_folder_id(str((old_row or {}).get("Link do zdjęć", ""))) or ""
        await harness.send_file(image_path, caption=f"zdjęcia do {new_name} {CITY_B}")
        switch_replies = await wait_for_card_messages(harness, timeout_s=30.0)
        result.context["switch_replies"] = [m.text[:240] for m in switch_replies]
        switch_card = find_card_message(switch_replies)
        if switch_card is None:
            result.add_blocker("switch_photo_card", "no switch confirmation card")
            return result
        result.add("switch_card_mentions_new_client", new_name in switch_card.text and CITY_B in switch_card.text, detail=switch_card.text[:240])
        old_after = await find_client_row(user_id, old_name, CITY_A)
        result.add("old_client_photo_count_still_one", str((old_after or {}).get("Zdjęcia", "")).strip() == "1", detail=str(old_after))
        await harness.click_button(switch_card, "❌ Anulować")
        await harness.collect_messages(duration_s=3.0)
    except Exception as exc:
        logger.exception("photo_session_switch_client crashed")
        result.add_blocker("scenario_crash", f"{type(exc).__name__}: {exc}")
    finally:
        if folder_id and (harness.authenticated_user_id is not None):
            user_id = await resolve_user_id(harness.authenticated_user_id)
            if user_id:
                result.add("drive_folder_cleanup", await _delete_drive_folder(user_id, folder_id), detail=folder_id)
        await _cleanup_after(harness, result, run_id=run_id)
        stamp_end(result)
    return result
