from unittest.mock import AsyncMock

import pytest

from shared.offers.pipeline import SendOfferResult


class FakeRepo:
    def __init__(self, attempts):
        self.attempts = attempts
        self.released = []
        self.notified = []

    def claim_due_send_attempts(self, limit, lock_owner):
        return self.attempts[:limit]

    def get_template(self, user_id, template_id):
        return {
            "id": template_id,
            "status": "ready",
            "name": "PV",
            "price_net_pln": 10000,
            "vat_rate": 8,
            "product_type": "PV",
        }

    def get_seller_profile(self, user_id):
        return {"company_name": "Firma"}

    def release_or_fail_send_attempt(self, idempotency_key, error, permanent=False, max_attempts=3):
        self.released.append((idempotency_key, error, permanent, max_attempts))
        return {"idempotency_key": idempotency_key, "status": "failed" if permanent else "pending"}

    def mark_result_notified(self, idempotency_key):
        self.notified.append(idempotency_key)


class FailingClaimRepo:
    def claim_due_send_attempts(self, limit, lock_owner):
        raise RuntimeError("queue_schema_missing")


def _attempt(**overrides):
    base = {
        "idempotency_key": "key-1",
        "user_id": "user-1",
        "telegram_id": 123,
        "client_row": 2,
        "offer_template_id": "tpl-1",
        "offer_number": 1,
        "command_text": "wyślij ofertę",
        "attempt_count": 1,
    }
    base.update(overrides)
    return base


@pytest.mark.asyncio
async def test_offer_queue_worker_sends_final_success_message(monkeypatch):
    from shared.offers.queue_worker import process_offer_send_queue_once

    repo = FakeRepo([_attempt()])
    bot = AsyncMock()

    monkeypatch.setattr(
        "shared.offers.queue_worker.lookup_client_by_row",
        AsyncMock(return_value={"_row": 2, "Imię i nazwisko": "Jan Kowalski", "Email": "jan@example.com"}),
    )
    monkeypatch.setattr(
        "shared.offers.queue_worker.send_offer_after_confirmation",
        AsyncMock(return_value=SendOfferResult(sent=True, gmail_message_id="msg-1")),
    )

    processed = await process_offer_send_queue_once(bot, repository=repo, lock_owner="worker-1")

    assert processed == 1
    bot.send_message.assert_awaited_once()
    assert "Oferta wysłana" in bot.send_message.await_args.kwargs["text"]
    assert repo.notified == ["key-1"]


@pytest.mark.asyncio
async def test_offer_queue_worker_retries_transient_failure_without_final_message(monkeypatch):
    from shared.offers.queue_worker import process_offer_send_queue_once

    repo = FakeRepo([_attempt(attempt_count=1)])
    bot = AsyncMock()

    monkeypatch.setattr(
        "shared.offers.queue_worker.lookup_client_by_row",
        AsyncMock(return_value={"_row": 2, "Imię i nazwisko": "Jan Kowalski", "Email": "jan@example.com"}),
    )
    monkeypatch.setattr(
        "shared.offers.queue_worker.send_offer_after_confirmation",
        AsyncMock(return_value=SendOfferResult(sent=False, error="gmail_down")),
    )

    processed = await process_offer_send_queue_once(bot, repository=repo, lock_owner="worker-1")

    assert processed == 1
    assert repo.released == [("key-1", "gmail_down", False, 3)]
    bot.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_offer_queue_worker_reports_permanent_missing_email_failure(monkeypatch):
    from shared.offers.queue_worker import process_offer_send_queue_once

    repo = FakeRepo([_attempt(attempt_count=1)])
    bot = AsyncMock()

    monkeypatch.setattr(
        "shared.offers.queue_worker.lookup_client_by_row",
        AsyncMock(return_value={"_row": 2, "Imię i nazwisko": "Jan Kowalski", "Email": ""}),
    )
    monkeypatch.setattr(
        "shared.offers.queue_worker.send_offer_after_confirmation",
        AsyncMock(return_value=SendOfferResult(sent=False, error="missing_valid_email")),
    )

    processed = await process_offer_send_queue_once(bot, repository=repo, lock_owner="worker-1")

    assert processed == 1
    assert repo.released == [("key-1", "missing_valid_email", True, 3)]
    bot.send_message.assert_awaited_once()
    assert "Klient nie ma poprawnego maila" in bot.send_message.await_args.kwargs["text"]
    assert repo.notified == ["key-1"]


@pytest.mark.asyncio
async def test_offer_queue_worker_noops_when_queue_schema_is_missing():
    from shared.offers.queue_worker import process_offer_send_queue_once

    processed = await process_offer_send_queue_once(
        AsyncMock(),
        repository=FailingClaimRepo(),
        lock_owner="worker-1",
    )

    assert processed == 0
