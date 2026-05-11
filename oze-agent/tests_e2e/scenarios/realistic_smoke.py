"""Realistic-name smoke scenarios for live Telegram/Google verification.

These scenarios intentionally avoid visible `E2E-Beta-*` names and cities in
Telegram. Cleanup is anchored by the synthetic email domain only.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, time, timedelta

from tests_e2e.asserts import assert_no_banned_phrases, assert_no_internal_leak
from tests_e2e.harness import TelegramE2EHarness
from tests_e2e.report import ScenarioResult
from tests_e2e.scenarios._base import new_result, register, stamp_end
from tests_e2e.scenarios._helpers import (
    WARSAW,
    assert_save_confirmed,
    click_save_and_collect,
    find_card_message,
    make_run_id,
    reset_pending,
    setup_existing_client,
    tomorrow_warsaw,
    verify_calendar_event,
    verify_sheets_row,
    wait_for_card_messages,
)

logger = logging.getLogger(__name__)

CATEGORY = "realistic_smoke"
SYNTHETIC_DOMAIN = "e2e-noinbox.local"


@dataclass(frozen=True)
class SmokeClient:
    name: str
    city: str
    address: str
    phone: str
    product: str
    email_slug: str

    def email(self, run_id: str) -> str:
        return f"{self.email_slug}+{run_id}@{SYNTHETIC_DOMAIN}"


CLIENT_A = SmokeClient(
    name="Michał Zieliński",
    city="Legnica",
    address="ul. Słoneczna 18",
    phone="604112233",
    product="fotowoltaika i magazyn energii",
    email_slug="michal.zielinski",
)

CLIENT_B = SmokeClient(
    name="Karolina Woźniak",
    city="Świdnica",
    address="ul. Brzozowa 7",
    phone="608445566",
    product="pompa ciepła i PV",
    email_slug="karolina.wozniak",
)


def _admin_id(harness: TelegramE2EHarness, result: ScenarioResult) -> int | None:
    telegram_id = harness.authenticated_user_id
    if telegram_id is None:
        result.add_blocker("telegram_identity", "harness has no authenticated_user_id")
        return None
    return telegram_id


def _assert_clean_card(result: ScenarioResult, text: str) -> None:
    ok, detail = assert_no_banned_phrases(text)
    result.add("no_banned_phrases", ok, detail)
    ok, detail = assert_no_internal_leak(text)
    result.add("no_internal_field_leak", ok, detail)
    result.add("no_visible_e2e_beta_marker", "E2E-Beta" not in text, detail=text[:240])


async def _send_and_get_card(
    harness: TelegramE2EHarness,
    result: ScenarioResult,
    trigger: str,
):
    result.context["trigger"] = trigger
    await reset_pending(harness)
    await harness.send(trigger)
    replies = await wait_for_card_messages(harness, timeout_s=25.0)
    result.context["reply_count"] = len(replies)
    result.context["initial_replies"] = [m.text[:240] for m in replies]
    card = find_card_message(replies)
    if card is None:
        result.add_blocker("got_card", "no card with buttons arrived")
        return None
    result.add("got_card", True, detail=str(card.button_labels))
    _assert_clean_card(result, card.text)
    return card


async def _save_card(harness: TelegramE2EHarness, result: ScenarioResult, card) -> bool:
    save_label, replies = await click_save_and_collect(
        harness,
        card,
        duration_s=12.0,
    )
    result.context["save_label"] = save_label
    result.context["confirm_replies"] = [m.text[:240] for m in replies]
    if save_label is None:
        result.add_blocker("save_button_present", f"no save button in {card.button_labels}")
        return False
    result.add("save_button_present", True, detail=save_label)
    await assert_save_confirmed(harness, result, replies)
    for reply in replies:
        _assert_clean_card(result, reply.text)
    return True


@register(
    name="realistic_add_client_sheets_save",
    category=CATEGORY,
    description="Realistic add_client → confirm → Sheets row verified.",
    default_in_run=False,
)
async def run_realistic_add_client_sheets_save(
    harness: TelegramE2EHarness,
) -> ScenarioResult:
    result = new_result("realistic_add_client_sheets_save", CATEGORY)
    run_id = make_run_id()
    client = CLIENT_A
    email = client.email(run_id)
    result.context.update({"client_name": client.name, "client_city": client.city, "email": email})
    try:
        trigger = (
            f"dodaj klienta {client.name}, {client.city}, {client.address}, "
            f"telefon {client.phone}, email {email}, {client.product}, polecenie"
        )
        card = await _send_and_get_card(harness, result, trigger)
        if card is None:
            return result
        if not await _save_card(harness, result, card):
            return result

        telegram_id = _admin_id(harness, result)
        if telegram_id is not None:
            await verify_sheets_row(
                result,
                telegram_id,
                client.name,
                client.city,
                expected_fields={
                    "Telefon": client.phone,
                    "Email": email,
                    "Adres": client.address,
                    "Produkt": "PV + Magazyn energii",
                },
            )
    except Exception as exc:
        logger.exception("realistic_add_client_sheets_save crashed")
        result.add_blocker("scenario_crash", f"{type(exc).__name__}: {exc}")
    finally:
        stamp_end(result)
    return result


@register(
    name="realistic_add_meeting_calendar_sheets_save",
    category=CATEGORY,
    description="Realistic existing client → add_meeting → Calendar + Sheets verified.",
    default_in_run=False,
)
async def run_realistic_add_meeting_calendar_sheets_save(
    harness: TelegramE2EHarness,
) -> ScenarioResult:
    result = new_result("realistic_add_meeting_calendar_sheets_save", CATEGORY)
    run_id = make_run_id()
    client = CLIENT_B
    email = client.email(run_id)
    start_date = tomorrow_warsaw()
    start_dt = datetime.combine(start_date, time(13, 30), tzinfo=WARSAW)
    end_dt = start_dt + timedelta(hours=1)
    result.context.update({"client_name": client.name, "client_city": client.city, "email": email})
    try:
        created = await setup_existing_client(
            harness,
            result,
            client.name,
            city=client.city,
            extra_fields=(
                f"{client.address}, telefon {client.phone}, email {email}, "
                f"{client.product}, polecenie"
            ),
        )
        if not created:
            return result

        trigger = f"jutro o 13:30 spotkanie z {client.name}, {client.city}"
        card = await _send_and_get_card(harness, result, trigger)
        if card is None:
            return result
        if not await _save_card(harness, result, card):
            return result

        telegram_id = _admin_id(harness, result)
        if telegram_id is not None:
            await verify_calendar_event(
                result,
                telegram_id,
                client.name,
                start_dt - timedelta(minutes=5),
                end_dt + timedelta(minutes=5),
                expected_event_type="in_person",
                expected_start=start_dt,
                expected_duration_min=60,
            )
            await verify_sheets_row(
                result,
                telegram_id,
                client.name,
                client.city,
                expected_fields={
                    "Następny krok": "Spotkanie",
                    "Email": email,
                },
                check_key="sheets_next_step_updated",
            )
    except Exception as exc:
        logger.exception("realistic_add_meeting_calendar_sheets_save crashed")
        result.add_blocker("scenario_crash", f"{type(exc).__name__}: {exc}")
    finally:
        stamp_end(result)
    return result


@register(
    name="realistic_show_day_plan_after_meeting",
    category=CATEGORY,
    description="Read today's/tomorrow plan shape with no visible E2E marker.",
    default_in_run=False,
)
async def run_realistic_show_day_plan_after_meeting(
    harness: TelegramE2EHarness,
) -> ScenarioResult:
    result = new_result("realistic_show_day_plan_after_meeting", CATEGORY)
    trigger = "co mam jutro?"
    try:
        await reset_pending(harness)
        await harness.send(trigger)
        replies = await harness.wait_for_messages(count=1, timeout_s=25.0)
        result.context["trigger"] = trigger
        result.context["reply_count"] = len(replies)
        if not replies:
            result.add_blocker("got_reply", "no reply")
            return result
        reply = replies[0]
        result.context["reply_text"] = reply.text[:500]
        result.add("got_reply", True, detail=reply.text[:240])
        result.add("no_buttons", not reply.button_labels, detail=str(reply.button_labels))
        _assert_clean_card(result, reply.text)
        result.add(
            "reply_is_plan_shape",
            "Plan na" in reply.text or "Na jutro" in reply.text or "nic" in reply.text.lower(),
            detail=reply.text[:240],
        )
    except Exception as exc:
        logger.exception("realistic_show_day_plan_after_meeting crashed")
        result.add_blocker("scenario_crash", f"{type(exc).__name__}: {exc}")
    finally:
        stamp_end(result)
    return result
