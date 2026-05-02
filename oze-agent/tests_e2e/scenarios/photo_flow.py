"""Opt-in E2E smoke for Google Drive photo upload flow.

This scenario writes synthetic clients and Drive files. It is intentionally
excluded from the default runner and should be executed explicitly via MCP:

    run_scenario("photo_flow_smoke")
"""

from __future__ import annotations

import io
import logging
from base64 import b64decode

from tests_e2e.asserts import assert_cancel_reply, assert_three_button_card
from tests_e2e.harness import TelegramE2EHarness, _ObservedMessage
from tests_e2e.report import ScenarioResult
from tests_e2e.scenarios._base import new_result, register, stamp_end
from tests_e2e.scenarios._helpers import (
    E2E_BETA_CITY,
    find_card_message,
    make_run_id,
    reset_pending,
    setup_existing_client,
    verify_sheets_row,
)

logger = logging.getLogger(__name__)

CATEGORY = "photo_flow"

_PNG_BYTES = b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


async def _send_image(
    harness: TelegramE2EHarness,
    *,
    caption: str | None = None,
    as_document: bool = False,
) -> None:
    if harness._client is None or harness._bot_entity is None:
        raise RuntimeError("Harness not connected")
    await harness._drain_inbox()
    image = io.BytesIO(_PNG_BYTES)
    image.name = "e2e-photo.png"
    await harness._client.send_file(
        harness._bot_entity,
        image,
        caption=caption,
        force_document=as_document,
    )


def _find_cancel_label(button_labels: list[str]) -> str | None:
    for label in button_labels:
        if "Anulować" in label or "❌" in label:
            return label
    return None


def _has_photo_added(messages: list[_ObservedMessage], expected_label: str | None = None) -> bool:
    for message in messages:
        if "Dodane do" not in message.text and "Zdjęcie dodane" not in message.text:
            continue
        if expected_label and expected_label not in message.text:
            continue
        return True
    return False


async def _click_cancel_and_collect(
    harness: TelegramE2EHarness,
    card_msg: _ObservedMessage,
) -> list[_ObservedMessage]:
    label = _find_cancel_label(card_msg.button_labels)
    if label is None:
        return []
    await harness.click_button(card_msg, label)
    return await harness.collect_messages(duration_s=5.0)


async def _click_save_and_collect(
    harness: TelegramE2EHarness,
    card_msg: _ObservedMessage,
) -> tuple[str | None, list[_ObservedMessage]]:
    label = next(
        (lbl for lbl in card_msg.button_labels if "Zapisać" in lbl or "✅" in lbl),
        None,
    )
    if label is None:
        return None, []
    await harness.click_button(card_msg, label)
    return label, await harness.collect_messages(duration_s=15.0)


async def _assert_photo_metadata(
    result: ScenarioResult,
    harness: TelegramE2EHarness,
    name: str,
    check_prefix: str,
) -> dict | None:
    tid = harness.authenticated_user_id
    if tid is None:
        result.add_blocker(f"{check_prefix}_sheets_row", "harness has no authenticated_user_id")
        return None
    row = await verify_sheets_row(
        result,
        tid,
        name,
        E2E_BETA_CITY,
        check_key=f"{check_prefix}_sheets_row",
    )
    if not row:
        return None
    photo_count = str(row.get("Zdjęcia", "")).strip()
    folder_link = str(row.get("Link do zdjęć", "")).strip()
    result.add(
        f"{check_prefix}_n_is_numeric",
        photo_count.isdigit(),
        detail=f"N/Zdjęcia={photo_count!r}",
    )
    result.add(
        f"{check_prefix}_o_is_folder_link",
        "drive.google.com/drive/folders" in folder_link,
        detail=f"O/Link do zdjęć={folder_link!r}",
    )
    return row


@register(
    name="photo_flow_smoke",
    category=CATEGORY,
    description="Google Drive photo flow: R1 card, cancel, save, session, switch target, image document. WRITES Sheets/Drive.",
    default_in_run=False,
)
async def run_photo_flow_smoke(harness: TelegramE2EHarness) -> ScenarioResult:
    result = new_result("photo_flow_smoke", CATEGORY)
    run_id = make_run_id()
    alpha = f"E2E-Beta-Photo-{run_id}-Alpha"
    beta = f"E2E-Beta-Photo-{run_id}-Beta"
    result.context.update({"alpha": alpha, "beta": beta})

    try:
        await reset_pending(harness)
        if not await setup_existing_client(harness, result, alpha):
            return result
        if not await setup_existing_client(harness, result, beta):
            return result

        await _send_image(harness, caption=f"{alpha} {E2E_BETA_CITY}")
        replies = await harness.wait_for_messages(count=1, timeout_s=25.0)
        card = find_card_message(replies)
        if card is None:
            result.add_blocker(
                "caption_card_arrived",
                f"no photo R1 card; got {[m.text[:120] for m in replies]}",
            )
            return result
        result.add("caption_card_arrived", True, detail=str(card.button_labels))
        ok, detail = assert_three_button_card(card)
        result.add("caption_card_three_buttons", ok, detail)
        result.add(
            "caption_card_no_prewrite_success",
            not _has_photo_added(replies),
            detail=f"replies={[m.text[:120] for m in replies]}",
        )

        cancel_replies = await _click_cancel_and_collect(harness, card)
        if cancel_replies:
            ok, detail = assert_cancel_reply(cancel_replies[-1])
            result.add("cancel_reply_ok", ok, detail)
        else:
            result.add_blocker("cancel_reply_ok", "no reply after ❌ Anulować")
            return result

        if harness.authenticated_user_id is None:
            result.add_blocker("after_cancel_sheets_row", "harness has no authenticated_user_id")
            row_after_cancel = None
        else:
            row_after_cancel = await verify_sheets_row(
                result,
                harness.authenticated_user_id,
                alpha,
                E2E_BETA_CITY,
                check_key="after_cancel_sheets_row",
            )
        if row_after_cancel:
            result.add(
                "cancel_wrote_no_count",
                not str(row_after_cancel.get("Zdjęcia", "")).strip(),
                detail=f"N={row_after_cancel.get('Zdjęcia', '')!r}",
            )
            result.add(
                "cancel_wrote_no_folder_link",
                not str(row_after_cancel.get("Link do zdjęć", "")).strip(),
                detail=f"O={row_after_cancel.get('Link do zdjęć', '')!r}",
            )

        await _send_image(harness, caption=f"{alpha} {E2E_BETA_CITY}")
        replies = await harness.wait_for_messages(count=1, timeout_s=25.0)
        card = find_card_message(replies)
        if card is None:
            result.add_blocker("save_card_arrived", "no card before save")
            return result
        save_label, save_replies = await _click_save_and_collect(harness, card)
        result.add("save_button_present", save_label is not None, detail=str(card.button_labels))
        result.add(
            "first_photo_saved",
            _has_photo_added(save_replies, alpha),
            detail=f"replies={[m.text[:160] for m in save_replies]}",
        )
        await _assert_photo_metadata(result, harness, alpha, "after_first_save")

        try:
            from shared.database import get_active_photo_session

            session = get_active_photo_session(harness.authenticated_user_id or 0)
            result.add(
                "active_session_created",
                bool(session and session.get("display_label") and alpha in session["display_label"]),
                detail=str(session),
            )
        except Exception as e:
            result.add("active_session_created", False, detail=f"{type(e).__name__}: {e}")

        await _send_image(harness)
        session_replies = await harness.wait_for_messages(count=1, timeout_s=25.0)
        result.add(
            "second_photo_no_caption_same_client",
            _has_photo_added(session_replies, alpha),
            detail=f"replies={[m.text[:160] for m in session_replies]}",
        )

        await _send_image(harness, caption="dach północny")
        desc_replies = await harness.wait_for_messages(count=1, timeout_s=25.0)
        result.add(
            "descriptive_caption_stays_same_client",
            _has_photo_added(desc_replies, alpha),
            detail=f"replies={[m.text[:160] for m in desc_replies]}",
        )

        await _send_image(harness, caption=f"zdjęcia do {beta} {E2E_BETA_CITY}")
        switch_replies = await harness.wait_for_messages(count=1, timeout_s=25.0)
        switch_card = find_card_message(switch_replies)
        result.add(
            "explicit_switch_shows_new_card",
            bool(switch_card and beta in switch_card.text),
            detail=f"replies={[m.text[:160] for m in switch_replies]}",
        )
        result.add(
            "explicit_switch_no_old_upload",
            not _has_photo_added(switch_replies, alpha),
            detail=f"replies={[m.text[:160] for m in switch_replies]}",
        )
        if switch_card:
            await _click_cancel_and_collect(harness, switch_card)

        await _send_image(
            harness,
            caption=f"{beta} {E2E_BETA_CITY}",
            as_document=True,
        )
        doc_replies = await harness.wait_for_messages(count=1, timeout_s=25.0)
        doc_card = find_card_message(doc_replies)
        result.add(
            "image_document_shows_card",
            bool(doc_card and beta in doc_card.text),
            detail=f"replies={[m.text[:160] for m in doc_replies]}",
        )
        if doc_card:
            _, doc_save_replies = await _click_save_and_collect(harness, doc_card)
            result.add(
                "image_document_saved",
                _has_photo_added(doc_save_replies, beta),
                detail=f"replies={[m.text[:160] for m in doc_save_replies]}",
            )
            await _assert_photo_metadata(result, harness, beta, "after_document_save")
    except Exception as e:
        logger.exception("photo_flow_smoke crashed")
        result.add_blocker("scenario_crash", f"{type(e).__name__}: {e}")
    finally:
        stamp_end(result)
    return result
