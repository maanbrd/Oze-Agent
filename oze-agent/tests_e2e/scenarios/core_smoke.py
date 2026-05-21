"""Core bot-test smoke scenarios from docs/TEST_PLAN_CURRENT.md SM-1..SM-11.

These are slow, opt-in live checks. They drive Telegram through Telethon and
verify resulting Google/Supabase state through the existing strict E2E helpers.
"""

from __future__ import annotations

import asyncio
import logging
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from pathlib import Path

from tests_e2e.asserts import assert_no_internal_leak, assert_three_button_card
from tests_e2e.calendar_verify import find_event_by_summary_in_window
from tests_e2e.harness import TelegramE2EHarness, _ObservedMessage
from tests_e2e.report import ScenarioResult
from tests_e2e.scenarios._base import new_result, register, stamp_end
from tests_e2e.scenarios._helpers import (
    WARSAW,
    assert_save_confirmed,
    click_save_and_collect,
    e2e_beta_name,
    find_card_message,
    find_save_button_label,
    make_run_id,
    post_setup_settle,
    reset_pending,
    setup_existing_client,
    tomorrow_warsaw,
    verify_calendar_event,
    verify_sheets_row,
    wait_for_card_messages,
)
from tests_e2e.sheets_verify import find_client_row, resolve_user_id
from shared.database import delete_pending_flow, get_supabase_client

logger = logging.getLogger(__name__)

CATEGORY = "core_smoke"


@dataclass(frozen=True)
class CoreClient:
    name: str
    city: str
    address: str
    phone: str
    product: str


def _client(suffix: str, *, run_id: str | None = None, city: str = "Marki") -> CoreClient:
    rid = run_id or make_run_id()
    return CoreClient(
        name=e2e_beta_name(suffix, rid),
        city=city,
        address="ul. Zielona 28",
        phone="600100200",
        product="fotowoltaika i magazyn energii",
    )


def _meeting_start(hour: int, minute: int = 0):
    return datetime.combine(tomorrow_warsaw(), time(hour, minute), tzinfo=WARSAW)


async def _user_id(result: ScenarioResult, harness: TelegramE2EHarness) -> str | None:
    telegram_id = harness.authenticated_user_id
    if telegram_id is None:
        result.add_blocker("telegram_identity", "harness has no authenticated_user_id")
        return None
    user_id = await resolve_user_id(telegram_id)
    if not user_id:
        result.add_blocker("resolve_user_id", f"no Supabase user for telegram_id={telegram_id}")
        return None
    return user_id


def _assert_clean_text(result: ScenarioResult, text: str, *, key_prefix: str) -> None:
    ok, detail = assert_no_internal_leak(text)
    result.add(f"{key_prefix}_no_internal_leak", ok, detail)


def _digits_only(value: str) -> str:
    return "".join(ch for ch in str(value) if ch.isdigit())


def _card_text_contains_phone(text: str, expected_phone: str) -> bool:
    expected_digits = _digits_only(expected_phone)
    return bool(expected_digits and expected_digits in _digits_only(text))


def _card_text_contains_product(text: str, expected_product: str) -> bool:
    text_lo = text.lower()
    expected_lo = expected_product.lower()
    if "fotowoltaika" in expected_lo and not (
        "fotowoltaika" in text_lo or re.search(r"\bpv\b", text_lo)
    ):
        return False
    if "magazyn" in expected_lo and "magazyn" not in text_lo:
        return False
    return True


def _extract_card_client_name(card: _ObservedMessage) -> str | None:
    """Extract the client name from a meeting/seeded card.

    Voice STT commonly turns the synthetic cleanup marker
    `E2E-Beta-Tester-123456-SM2` into `E2E Beta Tester 123456 SM2`.
    Downstream checks should verify the actual name the bot committed.
    """
    for line in card.text.splitlines():
        stripped = line.strip()
        match = re.match(r"^[•-]\s*Klient:\s*(.+)$", stripped)
        if match:
            return match.group(1).strip()
        if stripped.startswith("📋 "):
            return stripped[2:].split(",", 1)[0].strip()
    return None


def _client_with_card_name(client: CoreClient, card: _ObservedMessage) -> CoreClient:
    observed_name = _extract_card_client_name(card)
    if not observed_name:
        return client
    return CoreClient(
        name=observed_name,
        city=client.city,
        address=client.address,
        phone=client.phone,
        product=client.product,
    )


def _assert_meeting_card(result: ScenarioResult, card: _ObservedMessage, client: CoreClient) -> None:
    ok, detail = assert_three_button_card(card)
    result.add("meeting_three_button_card", ok, detail)
    lower = card.text.lower()
    result.add("first_card_is_meeting_not_client", "spotkanie" in lower, detail=card.text[:240])
    result.add("first_card_not_add_client_heading", "dodać klienta" not in lower, detail=card.text[:240])
    for check, expected in (
        ("card_contains_client_name", client.name),
        ("card_contains_city", client.city),
        ("card_contains_address", "Zielona"),
    ):
        result.add(check, expected in card.text, detail=card.text[:300])
    result.add("card_contains_phone", _card_text_contains_phone(card.text, client.phone), detail=card.text[:300])
    result.add("card_contains_product", _card_text_contains_product(card.text, client.product), detail=card.text[:300])
    _assert_clean_text(result, card.text, key_prefix="meeting_card")


async def _event_exists(
    user_id: str,
    client_name: str,
    start_dt: datetime,
    end_dt: datetime,
) -> bool:
    event = await find_event_by_summary_in_window(
        user_id,
        client_name,
        start_dt - timedelta(minutes=10),
        end_dt + timedelta(minutes=10),
    )
    return event is not None


async def _save_meeting_then_seeded_client(
    harness: TelegramE2EHarness,
    result: ScenarioResult,
    card: _ObservedMessage,
    client: CoreClient,
    start_dt: datetime,
) -> None:
    user_id = await _user_id(result, harness)
    if not user_id:
        return
    end_dt = start_dt + timedelta(hours=1)

    row_before = await find_client_row(user_id, client.name, client.city)
    result.add("no_sheet_write_before_meeting_confirm", row_before is None, detail=str(row_before))
    event_before = await _event_exists(user_id, client.name, start_dt, end_dt)
    result.add("no_calendar_write_before_meeting_confirm", not event_before)

    save_label, replies = await click_save_and_collect(harness, card, duration_s=15.0)
    result.context["meeting_save_label"] = save_label
    result.context["meeting_save_replies"] = [m.text[:300] for m in replies]
    if save_label is None:
        result.add_blocker("meeting_save_button", f"labels={card.button_labels}")
        return
    result.add("meeting_save_button", True, detail=save_label)

    seeded_card = find_card_message(replies)
    if seeded_card is None:
        result.add_blocker("seeded_add_client_card", "no add_client card after meeting save")
        return
    result.add("seeded_add_client_card", True, detail=str(seeded_card.button_labels))
    seeded_text = seeded_card.text
    for check, expected in (
        ("seeded_card_contains_client_name", client.name),
        ("seeded_card_contains_city", client.city),
        ("seeded_card_contains_address", "Zielona"),
    ):
        result.add(check, expected in seeded_text, detail=seeded_text[:300])
    result.add("seeded_card_contains_phone", _card_text_contains_phone(seeded_text, client.phone), detail=seeded_text[:300])
    result.add("seeded_card_contains_product", _card_text_contains_product(seeded_text, client.product), detail=seeded_text[:300])

    await verify_calendar_event(
        result,
        harness.authenticated_user_id,
        client.name,
        start_dt - timedelta(minutes=10),
        end_dt + timedelta(minutes=10),
        expected_event_type="in_person",
        expected_start=start_dt,
        expected_duration_min=60,
        check_key="calendar_event_after_meeting_confirm",
    )

    row_mid = await find_client_row(user_id, client.name, client.city)
    result.add("no_sheet_row_before_seeded_client_confirm", row_mid is None, detail=str(row_mid))
    add_client_label, add_client_replies = await click_save_and_collect(
        harness,
        seeded_card,
        duration_s=12.0,
    )
    result.context["seeded_client_save_label"] = add_client_label
    result.context["seeded_client_save_replies"] = [m.text[:300] for m in add_client_replies]
    if add_client_label is None:
        result.add_blocker("seeded_client_save_button", f"labels={seeded_card.button_labels}")
        return
    result.add("seeded_client_save_button", True, detail=add_client_label)
    await assert_save_confirmed(
        harness,
        result,
        add_client_replies,
        check_key="seeded_client_save_confirmed",
    )
    await verify_sheets_row(
        result,
        harness.authenticated_user_id,
        client.name,
        client.city,
        expected_fields={
            "Telefon": client.phone,
            "Adres": "Zielona",
            "Produkt": "PV",
            "Następny krok": "Spotkanie",
        },
        check_key="seeded_client_sheet_row_created",
    )


async def _run_compound_meeting_flow(
    harness: TelegramE2EHarness,
    result: ScenarioResult,
    *,
    client: CoreClient,
    start_dt: datetime,
    trigger: str,
) -> None:
    result.context["trigger"] = trigger
    await reset_pending(harness)
    await _isolate_scenario_context(harness, result)
    await harness.send(trigger)
    replies = await wait_for_card_messages(harness, timeout_s=75.0)
    result.context["initial_replies"] = [m.text[:300] for m in replies]
    card = find_card_message(replies)
    if card is None:
        result.add_blocker("meeting_card_arrived", f"replies={[m.text[:120] for m in replies]}")
        return
    result.add("meeting_card_arrived", True, detail=str(card.button_labels))
    _assert_meeting_card(result, card, client)
    await _save_meeting_then_seeded_client(harness, result, card, client, start_dt)


def _voice_text(client: CoreClient) -> str:
    return (
        f"Dodaj spotkanie z {client.name} na jutro o czternastej. "
        f"Mieszka w {client.city} na ulicy Zielonej 28. "
        f"Telefon {client.phone}. Interesuje go fotowoltaika i magazyn energii."
    )


def _build_voice_note(result: ScenarioResult, text: str, run_id: str) -> Path | None:
    say = shutil.which("say")
    ffmpeg = shutil.which("ffmpeg")
    if not say or not ffmpeg:
        result.add_blocker("voice_dependencies", f"say={bool(say)} ffmpeg={bool(ffmpeg)}")
        return None
    base = Path("/tmp") / f"oze-core-smoke-{run_id}"
    aiff = base.with_suffix(".aiff")
    ogg = base.with_suffix(".ogg")
    try:
        subprocess.run([say, "-v", "Zosia", "-o", str(aiff), text], check=True)
        subprocess.run(
            [ffmpeg, "-y", "-i", str(aiff), "-c:a", "libopus", "-b:a", "32k", str(ogg)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as exc:
        result.add_blocker("voice_file_generated", f"{type(exc).__name__}: {exc}")
        return None
    result.add("voice_file_generated", ogg.exists() and ogg.stat().st_size > 0, detail=str(ogg))
    return ogg


async def _isolate_scenario_context(
    harness: TelegramE2EHarness,
    result: ScenarioResult,
) -> None:
    """Expire prior active-client memory so scenarios do not contaminate each other."""
    telegram_id = harness.authenticated_user_id
    if telegram_id is None:
        result.add_blocker("telegram_identity", "harness has no authenticated_user_id")
        return
    await asyncio.to_thread(delete_pending_flow, telegram_id)
    await _expire_conversation_history(telegram_id)
    result.context["context_isolated_before_trigger"] = True


async def _click_voice_save_and_wait_for_card(
    harness: TelegramE2EHarness,
    result: ScenarioResult,
    voice_card: _ObservedMessage,
) -> _ObservedMessage | None:
    label = find_save_button_label(voice_card.button_labels)
    if label is None:
        result.add_blocker("voice_save_button", f"labels={voice_card.button_labels}")
        return None
    await harness.click_button(voice_card, label)
    replies = await wait_for_card_messages(harness, timeout_s=45.0)
    result.context["post_voice_confirm_replies"] = [m.text[:300] for m in replies]
    result.add("voice_save_button", True, detail=label)
    card = find_card_message(replies)
    if card is None:
        result.add_blocker("meeting_card_after_voice_confirm", f"replies={[m.text[:120] for m in replies]}")
    return card


@register(
    name="sm1_compound_meeting_new_client_preseed",
    category=CATEGORY,
    description="SM-1: rich meeting+client command routes to add_meeting first, then preseeded add_client.",
    default_in_run=False,
)
async def run_sm1_compound_meeting_new_client_preseed(harness: TelegramE2EHarness) -> ScenarioResult:
    result = new_result("sm1_compound_meeting_new_client_preseed", CATEGORY)
    run_id = make_run_id()
    client = _client("SM1", run_id=run_id)
    start_dt = _meeting_start(14)
    trigger = (
        f"Dodaj spotkanie z {client.name} na jutro o 14. "
        f"Mieszka w {client.city} na ulicy Zielonej 28. Telefon {client.phone}. "
        f"Interesuje go fotowoltaika i magazyn energii."
    )
    try:
        await _run_compound_meeting_flow(
            harness,
            result,
            client=client,
            start_dt=start_dt,
            trigger=trigger,
        )
    except Exception as exc:
        logger.exception("SM-1 core smoke crashed")
        result.add_blocker("scenario_crash", f"{type(exc).__name__}: {exc}")
    finally:
        stamp_end(result)
    return result


@register(
    name="sm2_voice_compound_meeting_new_client_preseed",
    category=CATEGORY,
    description="SM-2: voice transcript card, then same meeting+client flow as SM-1.",
    default_in_run=False,
)
async def run_sm2_voice_compound_meeting_new_client_preseed(harness: TelegramE2EHarness) -> ScenarioResult:
    result = new_result("sm2_voice_compound_meeting_new_client_preseed", CATEGORY)
    run_id = make_run_id()
    client = _client("SM2", run_id=run_id)
    start_dt = _meeting_start(14)
    try:
        await reset_pending(harness)
        await _isolate_scenario_context(harness, result)
        voice_path = _build_voice_note(result, _voice_text(client), run_id)
        if voice_path is None:
            return result
        await harness.send_file(voice_path, voice_note=True)
        voice_replies = await wait_for_card_messages(harness, timeout_s=60.0)
        result.context["voice_replies"] = [m.text[:300] for m in voice_replies]
        voice_card = find_card_message(voice_replies)
        if voice_card is None:
            result.add_blocker("voice_transcript_card", f"replies={[m.text[:120] for m in voice_replies]}")
            return result
        result.add("voice_transcript_card", True, detail=str(voice_card.button_labels))
        result.add("voice_card_has_two_buttons", len(voice_card.button_labels) == 2, detail=str(voice_card.button_labels))
        result.add("voice_card_mentions_transcript", bool(voice_card.text.strip()), detail=voice_card.text[:240])
        meeting_card = await _click_voice_save_and_wait_for_card(harness, result, voice_card)
        if meeting_card is None:
            return result
        client = _client_with_card_name(client, meeting_card)
        _assert_meeting_card(result, meeting_card, client)
        await _save_meeting_then_seeded_client(harness, result, meeting_card, client, start_dt)
    except Exception as exc:
        logger.exception("SM-2 core smoke crashed")
        result.add_blocker("scenario_crash", f"{type(exc).__name__}: {exc}")
    finally:
        stamp_end(result)
    return result


@register(
    name="sm3_phone_field_does_not_force_meeting",
    category=CATEGORY,
    description="SM-3: phone field plus 'jutro podeślę dane' stays add_client, not Calendar meeting.",
    default_in_run=False,
)
async def run_sm3_phone_field_does_not_force_meeting(harness: TelegramE2EHarness) -> ScenarioResult:
    result = new_result("sm3_phone_field_does_not_force_meeting", CATEGORY)
    run_id = make_run_id()
    client = _client("SM3", run_id=run_id, city="Radom")
    start_dt = _meeting_start(10)
    end_dt = start_dt + timedelta(hours=1)
    trigger = f"Dodaj klienta {client.name}, telefon {client.phone}, jutro podeślę dane"
    result.context["trigger"] = trigger
    try:
        await reset_pending(harness)
        await _isolate_scenario_context(harness, result)
        user_id = await _user_id(result, harness)
        if not user_id:
            return result
        await harness.send(trigger)
        replies = await wait_for_card_messages(harness, timeout_s=45.0)
        result.context["initial_replies"] = [m.text[:300] for m in replies]
        card = find_card_message(replies)
        if card is None:
            result.add_blocker("add_client_card_arrived", f"replies={[m.text[:120] for m in replies]}")
            return result
        result.add("add_client_card_arrived", True, detail=str(card.button_labels))
        lower = card.text.lower()
        is_add_client_card = not any(
            marker in lower
            for marker in ("dodać spotkanie", "godzina:", "czas trwania:")
        )
        result.add("card_is_add_client_not_meeting", is_add_client_card, detail=card.text[:240])
        result.add("card_contains_phone", _card_text_contains_phone(card.text, client.phone), detail=card.text[:240])
        row_before = await find_client_row(user_id, client.name)
        result.add("no_sheet_write_before_confirm", row_before is None, detail=str(row_before))
        event_before = await _event_exists(user_id, client.name, start_dt, end_dt)
        result.add("no_calendar_write_before_confirm", not event_before)
        label, confirm_replies = await click_save_and_collect(harness, card, duration_s=12.0)
        result.context["save_label"] = label
        result.context["confirm_replies"] = [m.text[:300] for m in confirm_replies]
        if label is None:
            result.add_blocker("save_button", f"labels={card.button_labels}")
            return result
        result.add("save_button", True, detail=label)
        await assert_save_confirmed(harness, result, confirm_replies)
        await verify_sheets_row(
            result,
            harness.authenticated_user_id,
            client.name,
            None,
            expected_fields={"Telefon": client.phone},
            check_key="client_sheet_row_created",
        )
        event_after = await _event_exists(user_id, client.name, start_dt, end_dt)
        result.add("no_calendar_event_after_add_client_save", not event_after)
    except Exception as exc:
        logger.exception("SM-3 core smoke crashed")
        result.add_blocker("scenario_crash", f"{type(exc).__name__}: {exc}")
    finally:
        stamp_end(result)
    return result


@register(
    name="sm7_add_meeting_new_client_preseed",
    category=CATEGORY,
    description="SM-7: meeting for non-existing client creates Calendar event and preseeded add_client draft.",
    default_in_run=False,
)
async def run_sm7_add_meeting_new_client_preseed(harness: TelegramE2EHarness) -> ScenarioResult:
    result = new_result("sm7_add_meeting_new_client_preseed", CATEGORY)
    run_id = make_run_id()
    client = _client("SM7", run_id=run_id, city="Otwock")
    start_dt = _meeting_start(15, 20)
    trigger = (
        f"Jutro o 15:20 spotkanie z {client.name}. "
        f"{client.city}, {client.address}, telefon {client.phone}, {client.product}."
    )
    try:
        await _run_compound_meeting_flow(
            harness,
            result,
            client=client,
            start_dt=start_dt,
            trigger=trigger,
        )
    except Exception as exc:
        logger.exception("SM-7 core smoke crashed")
        result.add_blocker("scenario_crash", f"{type(exc).__name__}: {exc}")
    finally:
        stamp_end(result)
    return result


def _expire_conversation_history_sync(telegram_id: int) -> None:
    stale = (datetime.now(tz=timezone.utc) - timedelta(minutes=31)).isoformat()
    get_supabase_client().table("conversation_history").update(
        {"created_at": stale}
    ).eq("telegram_id", telegram_id).execute()


async def _expire_conversation_history(telegram_id: int) -> None:
    await asyncio.to_thread(_expire_conversation_history_sync, telegram_id)


@register(
    name="sm10_r6_memory_window_expired_requires_client",
    category=CATEGORY,
    description="SM-10: after expiring R6 history, implicit add_note must ask for client.",
    default_in_run=False,
)
async def run_sm10_r6_memory_window_expired_requires_client(harness: TelegramE2EHarness) -> ScenarioResult:
    result = new_result("sm10_r6_memory_window_expired_requires_client", CATEGORY)
    run_id = make_run_id()
    client = _client("SM10", run_id=run_id, city="Płock")
    try:
        await reset_pending(harness)
        created = await setup_existing_client(
            harness,
            result,
            client.name,
            city=client.city,
            extra_fields=f"{client.phone}, {client.product}",
        )
        if not created:
            return result
        await verify_sheets_row(
            result,
            harness.authenticated_user_id,
            client.name,
            client.city,
            expected_fields={"Telefon": client.phone},
            check_key="setup_sheet_row_created",
        )
        telegram_id = harness.authenticated_user_id
        if telegram_id is None:
            result.add_blocker("telegram_identity", "harness has no authenticated_user_id")
            return result
        await _expire_conversation_history(telegram_id)
        result.add("conversation_history_expired", True, detail="created_at shifted 31 minutes back")
        trigger = "dodaj notatkę: zainteresowany pompą"
        result.context["trigger"] = trigger
        await harness.send(trigger)
        replies = await harness.collect_messages(duration_s=12.0)
        result.context["note_without_context_replies"] = [m.text[:300] for m in replies]
        any_card = find_card_message(replies)
        result.add("no_add_note_card_without_recent_context", any_card is None, detail=str(any_card.button_labels if any_card else []))
        text = "\n".join(m.text.lower() for m in replies)
        asks_for_client = any(marker in text for marker in ("którego klienta", "podaj", "nie znalazłem", "jakiego klienta", "imię"))
        result.add("asks_for_client_after_memory_expiry", asks_for_client, detail=text[:400])
        row = await verify_sheets_row(
            result,
            telegram_id,
            client.name,
            client.city,
            expected_fields={"Telefon": client.phone},
            check_key="sheet_row_still_present",
        )
        if row:
            result.add("note_not_appended_without_context", "zainteresowany pompą" not in (row.get("Notatki") or "").lower())
    except Exception as exc:
        logger.exception("SM-10 core smoke crashed")
        result.add_blocker("scenario_crash", f"{type(exc).__name__}: {exc}")
    finally:
        stamp_end(result)
    return result
