"""Post-campaign app smoke checks for Drive/photo and offer/Gmail flows.

This runner is intentionally separate from the 500+ Telegram campaign because
photo uploads and Gmail sends use external app surfaces that should not be
interleaved with the high-volume text flow.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from shared.database import delete_active_photo_session
from shared.google_drive import (
    _get_drive_service_sync,
    extract_folder_id,
    get_client_photos,
)
from shared.offers.numbering import list_ready_with_numbers
from shared.offers.repository import OfferRepository

from tests_e2e.config import E2EConfig
from tests_e2e.fixtures import cleanup_synthetic_data
from tests_e2e.harness import TelegramE2EHarness
from tests_e2e.report import ScenarioResult, write_report
from tests_e2e.scenarios._base import new_result, stamp_end
from tests_e2e.scenarios._helpers import (
    assert_save_confirmed,
    click_save_and_collect,
    find_card_message,
    reset_pending,
    wait_for_card_messages,
)
from tests_e2e.sheets_verify import find_client_row, resolve_user_id

logger = logging.getLogger(__name__)

SYNTHETIC_DOMAIN = "e2e-noinbox.local"
OFFER_RECIPIENT_ENV = "TELEGRAM_E2E_OFFER_RECIPIENT"

# 1x1 transparent PNG. Telegram sends it as an image document if it does not
# transcode it into a photo; the bot supports both paths.
_PNG_1PX = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%H%M%S") + "-" + uuid4().hex[:6]


def _email(slug: str, run_id: str) -> str:
    return f"{slug}+{run_id}@{SYNTHETIC_DOMAIN}"


async def _hard_cancel(harness: TelegramE2EHarness) -> None:
    await harness.send("/cancel")
    await harness.collect_messages(duration_s=3.0)


async def _add_client(
    harness: TelegramE2EHarness,
    result: ScenarioResult,
    *,
    user_id: str,
    name: str,
    city: str,
    address: str,
    phone: str,
    email: str,
    product: str,
) -> dict | None:
    before = await find_client_row(user_id, name, city)
    result.add("client_absent_before_trigger", before is None, detail=str(before))

    trigger = (
        f"dodaj klienta {name}, {city}, {address}, telefon {phone}, "
        f"email {email}, {product}, polecenie"
    )
    result.context["add_client_trigger"] = trigger
    await reset_pending(harness)
    await harness.send(trigger)
    card_replies = await wait_for_card_messages(harness, timeout_s=30.0)
    result.context["add_client_card_replies"] = [m.text[:240] for m in card_replies]
    card = find_card_message(card_replies)
    if card is None:
        result.add_blocker("add_client_card", "no confirmation card")
        return None

    pre_confirm = await find_client_row(user_id, name, city)
    result.add("no_sheet_write_before_client_confirm", pre_confirm is None, detail=str(pre_confirm))

    label, save_replies = await click_save_and_collect(harness, card, duration_s=12.0)
    if label is None:
        result.add_blocker("client_save_button", f"buttons={card.button_labels}")
        return None
    result.add("client_save_button", True, detail=label)
    await assert_save_confirmed(harness, result, save_replies, check_key="client_save_confirmed")
    result.context["add_client_save_replies"] = [m.text[:240] for m in save_replies]

    row = await find_client_row(user_id, name, city)
    result.add("sheet_row_after_client_confirm", row is not None, detail=str(row))
    return row


def _write_test_jpeg(path: Path) -> None:
    path.write_bytes(base64.b64decode(_PNG_1PX))


async def _delete_drive_folder(user_id: str, folder_id: str) -> bool:
    def _delete() -> bool:
        service = _get_drive_service_sync(user_id)
        if not service:
            return False
        service.files().delete(fileId=folder_id).execute()
        return True

    return await asyncio.to_thread(_delete)


async def run_drive_photo_smoke(config: E2EConfig) -> ScenarioResult:
    result = new_result("post_drive_photo_smoke", "post_campaign_apps")
    run_id = _run_id()
    name = "Agnieszka Lewandowska"
    city = "Kalisz"
    email = _email("agnieszka.lewandowska", run_id)
    folder_id = ""
    try:
        user_id = await resolve_user_id(config.admin_telegram_id)
        if not user_id:
            result.add_blocker("user_id", "could not resolve Supabase user id")
            return result
        result.context["user_id"] = user_id
        result.context["client_name"] = name
        result.context["client_city"] = city
        result.context["client_email"] = email

        async with TelegramE2EHarness(config) as harness:
            await _hard_cancel(harness)
            row = await _add_client(
                harness,
                result,
                user_id=user_id,
                name=name,
                city=city,
                address="ul. Ogrodowa 4",
                phone="607998877",
                email=email,
                product="fotowoltaika 8 kW",
            )
            if row is None:
                return result

            image_path = Path("/tmp/oze-drive-photo-smoke.png")
            _write_test_jpeg(image_path)
            caption = f"zdjęcia do {name} {city}"
            await harness.send_file(image_path, caption=caption)
            photo_replies = await wait_for_card_messages(harness, timeout_s=30.0)
            result.context["photo_card_replies"] = [m.text[:240] for m in photo_replies]
            photo_card = find_card_message(photo_replies)
            if photo_card is None:
                result.add_blocker("photo_confirm_card", "no photo confirmation card")
                return result

            pre_photo = await find_client_row(user_id, name, city)
            pre_count = str((pre_photo or {}).get("Zdjęcia", "")).strip()
            pre_link = str((pre_photo or {}).get("Link do zdjęć", "")).strip()
            result.add("no_drive_sheet_write_before_photo_confirm", not pre_count and not pre_link)

            label, photo_save_replies = await click_save_and_collect(harness, photo_card, duration_s=12.0)
            if label is None:
                result.add_blocker("photo_save_button", f"buttons={photo_card.button_labels}")
                return result
            result.add("photo_save_button", True, detail=label)
            result.context["photo_save_replies"] = [m.text[:240] for m in photo_save_replies]

        row_after = await find_client_row(user_id, name, city)
        result.add("sheet_photo_metadata_row_present", row_after is not None, detail=str(row_after))
        if row_after:
            photo_count = str(row_after.get("Zdjęcia", "")).strip()
            folder_link = str(row_after.get("Link do zdjęć", "")).strip()
            folder_id = extract_folder_id(folder_link) or ""
            result.add("sheet_photo_count_updated", photo_count == "1", detail=photo_count)
            result.add("sheet_photo_folder_link_updated", bool(folder_id), detail=folder_link)
            if folder_id:
                photos = await get_client_photos(user_id, folder_id)
                result.context["drive_folder_id"] = folder_id
                result.context["drive_photos"] = photos
                result.add("drive_file_uploaded", len(photos) >= 1, detail=str(photos[:3]))

        if folder_id:
            deleted = await _delete_drive_folder(user_id, folder_id)
            result.add("drive_folder_cleanup", deleted, detail=folder_id)
        delete_active_photo_session(config.admin_telegram_id)
        cleanup = await cleanup_synthetic_data(config.admin_telegram_id, include_fixtures=True)
        result.context["cleanup"] = cleanup
        result.add(
            "sheets_calendar_cleanup",
            cleanup.get("sheets_rows_found", 0) == cleanup.get("sheets_deleted", -1),
            detail=str(cleanup),
        )
    except Exception as e:
        logger.exception("drive photo smoke crashed")
        result.add_blocker("scenario_crash", f"{type(e).__name__}: {e}")
    finally:
        stamp_end(result)
    return result


async def run_offer_gmail_smoke(config: E2EConfig) -> ScenarioResult:
    result = new_result("post_offer_gmail_smoke", "post_campaign_apps")
    recipient = os.getenv(OFFER_RECIPIENT_ENV, "").strip()
    run_id = _run_id()
    name = "Piotr Malinowski"
    city = "Opole"
    email = recipient or _email("piotr.malinowski", run_id)
    try:
        user_id = await resolve_user_id(config.admin_telegram_id)
        if not user_id:
            result.add_blocker("user_id", "could not resolve Supabase user id")
            return result
        result.context["user_id"] = user_id
        result.context["client_name"] = name
        result.context["client_city"] = city
        result.context["client_email"] = email

        repo = OfferRepository()
        try:
            templates = repo.list_templates(user_id)
        except Exception as e:
            result.add_blocker("offer_templates_read", f"{type(e).__name__}: {e}")
            async with TelegramE2EHarness(config) as harness:
                await _hard_cancel(harness)
                await harness.send("jakie mam oferty?")
                replies = await harness.collect_messages(duration_s=8.0)
                result.context["telegram_offer_list_replies"] = [m.text[:240] for m in replies]
                result.add("telegram_offer_list_request_sent", bool(replies), detail=str([m.text[:120] for m in replies]))
            return result

        ready = list_ready_with_numbers(templates)
        result.context["ready_offer_count"] = len(ready)
        result.add("ready_offer_templates_present", bool(ready), detail=str([t[0] for t in ready[:5]]))
        if not ready:
            return result
        result.add("offer_recipient_configured", bool(recipient), detail=OFFER_RECIPIENT_ENV)
        if not recipient:
            return result

        offer_number, template = ready[0]
        result.context["offer_number"] = offer_number
        result.context["offer_name"] = template.get("name")
        attempts_before_command = _offer_attempts_for_client(repo, user_id, name, city)
        result.context["offer_attempts_before_command"] = len(attempts_before_command)

        async with TelegramE2EHarness(config) as harness:
            await _hard_cancel(harness)
            row = await _add_client(
                harness,
                result,
                user_id=user_id,
                name=name,
                city=city,
                address="ul. Lipowa 12",
                phone="606123987",
                email=email,
                product="pompa ciepła i fotowoltaika",
            )
            if row is None:
                return result

            command = f"wyślij ofertę nr {offer_number} dla {name} {city}"
            result.context["offer_send_trigger"] = command
            await harness.send(command)
            card_replies = await wait_for_card_messages(harness, timeout_s=30.0)
            result.context["offer_card_replies"] = [m.text[:300] for m in card_replies]
            card = find_card_message(card_replies)
            if card is None:
                result.add_blocker("offer_send_confirm_card", "no offer confirmation card")
                return result
            result.add("offer_send_confirm_card", True, detail=str(card.button_labels))
            attempts_before_confirm = _offer_attempts_for_client(repo, user_id, name, city)
            result.context["offer_attempts_before_confirm"] = len(attempts_before_confirm)
            result.add(
                "no_offer_attempt_before_confirm",
                len(attempts_before_confirm) == len(attempts_before_command),
                detail=f"before_command={len(attempts_before_command)} before_confirm={len(attempts_before_confirm)}",
            )

            await harness.click_button(card, "✅ Wysłać")
            replies = await harness.collect_messages(duration_s=20.0)
            result.context["offer_send_replies"] = [m.text[:300] for m in replies]
            sent_text = "\n".join(m.text for m in replies)
            result.add("telegram_offer_send_confirmed", "Oferta wysłana" in sent_text, detail=sent_text[:300])
            attempts_after_send = _offer_attempts_for_client(repo, user_id, name, city)
            sent_attempts = [a for a in attempts_after_send if a.get("status") == "sent"]
            result.context["offer_attempts_after_send"] = attempts_after_send
            result.add(
                "offer_send_attempt_sent",
                bool(sent_attempts),
                detail=str(sent_attempts[:2]),
            )
            result.add(
                "offer_send_attempt_gmail_message_id",
                bool(sent_attempts and sent_attempts[-1].get("gmail_message_id")),
                detail=str(sent_attempts[-1].get("gmail_message_id") if sent_attempts else ""),
            )

            second_click_error = ""
            try:
                await harness.click_button(card, "✅ Wysłać")
                second_replies = await harness.collect_messages(duration_s=8.0)
                result.context["offer_second_click_replies"] = [m.text[:300] for m in second_replies]
            except Exception as exc:
                second_click_error = f"{type(exc).__name__}: {exc}"
                result.context["offer_second_click_error"] = second_click_error
            attempts_after_second_click = _offer_attempts_for_client(repo, user_id, name, city)
            result.add(
                "offer_second_confirm_no_duplicate_attempt",
                len(attempts_after_second_click) == len(attempts_after_send),
                detail=(
                    f"after_send={len(attempts_after_send)} "
                    f"after_second_click={len(attempts_after_second_click)} "
                    f"second_click_error={second_click_error}"
                ),
            )
            result.add(
                "gmail_sent_connector_evidence_required",
                True,
                detail=(
                    "Verify externally with Codex Gmail connector: "
                    f"in:sent to:{email} filename:pdf"
                ),
            )

        cleanup = await cleanup_synthetic_data(config.admin_telegram_id, include_fixtures=True)
        result.context["cleanup"] = cleanup
    except Exception as e:
        logger.exception("offer gmail smoke crashed")
        result.add_blocker("scenario_crash", f"{type(e).__name__}: {e}")
    finally:
        stamp_end(result)
    return result


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


def validate_post_campaign_args(args: argparse.Namespace) -> str | None:
    if args.photo_runs < 0 or args.offer_runs < 0:
        return "--photo-runs and --offer-runs must be >= 0"
    if args.photo_runs == 0 and args.offer_runs == 0:
        return "at least one post-campaign app run is required"
    if args.offer_runs > 0 and not os.getenv(OFFER_RECIPIENT_ENV, "").strip():
        return f"{OFFER_RECIPIENT_ENV} is required when --offer-runs > 0"
    return None


async def _main_async(
    config: E2EConfig,
    report: str,
    *,
    photo_runs: int = 1,
    offer_runs: int = 1,
) -> int:
    results = []
    for _ in range(photo_runs):
        results.append(await run_drive_photo_smoke(config))
    for _ in range(offer_runs):
        results.append(await run_offer_gmail_smoke(config))
    write_report(results, report)
    return 0 if all(r.passed for r in results) else 1


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m tests_e2e.post_campaign_checks")
    parser.add_argument("--report", default="/tmp/oze-e2e-post-apps.md")
    parser.add_argument("--photo-runs", type=int, default=1)
    parser.add_argument("--offer-runs", type=int, default=1)
    parser.add_argument("--verbose", "-v", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    error = validate_post_campaign_args(args)
    if error:
        print(f"Post-campaign config error: {error}", file=sys.stderr)
        return 2
    config = E2EConfig.from_env()
    return asyncio.run(
        _main_async(
            config,
            args.report,
            photo_runs=args.photo_runs,
            offer_runs=args.offer_runs,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
