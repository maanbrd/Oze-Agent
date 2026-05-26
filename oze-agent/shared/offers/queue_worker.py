"""Durable background worker for confirmed offer sends."""

from __future__ import annotations

import logging
from uuid import uuid4

from telegram import Bot

from shared.clients import lookup_client_by_row
from shared.observability import exception_type, id_hash
from shared.offers.pipeline import SendOfferResult, send_offer_after_confirmation
from shared.offers.repository import OfferRepository
from shared.request_context import request_context

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3
PERMANENT_ERRORS = {"missing_valid_email", "template_missing", "client_missing"}


def _success_text(result: SendOfferResult) -> str:
    if result.already_sent:
        return "Ta oferta została już wysłana."
    lines = ["✅ Oferta wysłana."]
    if result.invalid_recipients:
        lines.append(f"Pominięte błędne adresy: {', '.join(result.invalid_recipients)}.")
    if result.sheets_errors:
        labels = {"email": "nowy email", "status": "status"}
        failed = ", ".join(labels.get(item, item) for item in result.sheets_errors)
        lines.append(f"Nie udało się zapisać w arkuszu: {failed}.")
    return "\n".join(lines)


def _failure_text(error: str | None) -> str:
    if error == "missing_valid_email":
        return "Klient nie ma poprawnego maila. Arkusz nie został zmieniony."
    if error == "template_missing":
        return "Ta oferta nie jest już dostępna. Arkusz nie został zmieniony."
    if error == "client_missing":
        return "Nie znalazłem klienta w arkuszu. Arkusz nie został zmieniony."
    return "Nie udało się wysłać maila. Arkusz nie został zmieniony."


async def process_offer_send_queue_once(
    bot: Bot,
    *,
    repository: OfferRepository | None = None,
    limit: int = 5,
    lock_owner: str | None = None,
) -> int:
    """Claim and process a small batch of due offer-send attempts."""
    repo = repository or OfferRepository()
    owner = lock_owner or f"offer-worker-{uuid4()}"
    attempts = repo.claim_due_send_attempts(limit=limit, lock_owner=owner)
    processed = 0

    for attempt in attempts:
        processed += 1
        with request_context():
            await _process_attempt(bot, repo, attempt)

    return processed


async def _process_attempt(bot: Bot, repo: OfferRepository, attempt: dict) -> None:
    idempotency_key = attempt.get("idempotency_key")
    user_id = attempt.get("user_id")
    telegram_id = attempt.get("telegram_id")
    if not idempotency_key or not user_id or not telegram_id:
        return

    try:
        template = repo.get_template(user_id, attempt.get("offer_template_id"))
        if not template or template.get("status") != "ready":
            await _final_fail(bot, repo, idempotency_key, telegram_id, "template_missing")
            return

        client = await lookup_client_by_row(user_id, attempt.get("client_row") or 0)
        if not client:
            await _final_fail(bot, repo, idempotency_key, telegram_id, "client_missing")
            return

        result = await send_offer_after_confirmation(
            user_id=user_id,
            telegram_id=int(telegram_id),
            idempotency_key=idempotency_key,
            offer_number=attempt.get("offer_number") or 0,
            template=template,
            seller_profile=repo.get_seller_profile(user_id),
            client=client,
            command_text=attempt.get("command_text") or "",
            repository=repo,
            preclaimed=True,
        )
        if result.sent:
            await bot.send_message(chat_id=telegram_id, text=_success_text(result))
            repo.mark_result_notified(idempotency_key)
            return

        error = result.error or "send_failed"
        permanent = error in PERMANENT_ERRORS
        released = repo.release_or_fail_send_attempt(
            idempotency_key,
            error,
            permanent=permanent,
            max_attempts=MAX_ATTEMPTS,
        ) or {}
        if permanent or released.get("status") == "failed":
            await bot.send_message(chat_id=telegram_id, text=_failure_text(error))
            repo.mark_result_notified(idempotency_key)
    except Exception as exc:
        logger.error(
            "offer_queue.attempt_failed user_hash=%s telegram_hash=%s exc_type=%s",
            id_hash(user_id),
            id_hash(telegram_id),
            exception_type(exc),
        )
        released = repo.release_or_fail_send_attempt(
            idempotency_key,
            exception_type(exc),
            permanent=False,
            max_attempts=MAX_ATTEMPTS,
        ) or {}
        if released.get("status") == "failed":
            await bot.send_message(chat_id=telegram_id, text=_failure_text(exception_type(exc)))
            repo.mark_result_notified(idempotency_key)


async def _final_fail(
    bot: Bot,
    repo: OfferRepository,
    idempotency_key: str,
    telegram_id: int,
    error: str,
) -> None:
    repo.release_or_fail_send_attempt(
        idempotency_key,
        error,
        permanent=True,
        max_attempts=MAX_ATTEMPTS,
    )
    await bot.send_message(chat_id=telegram_id, text=_failure_text(error))
    repo.mark_result_notified(idempotency_key)
