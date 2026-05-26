from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from shared.offers.pipeline import SendOfferResult


@pytest.mark.asyncio
async def test_offer_confirm_enqueues_without_inline_gmail_send():
    from bot.handlers import text

    repo = MagicMock()
    repo.list_templates.return_value = [{
        "id": "tpl-1",
        "status": "ready",
        "name": "PV",
        "price_net_pln": 10000,
        "vat_rate": 8,
        "product_type": "PV",
    }]
    repo.get_seller_profile.return_value = {"company_name": "Firma"}
    repo.enqueue_send_attempt.return_value = {"idempotency_key": "key-1", "status": "pending"}

    client = {
        "_row": 2,
        "Imię i nazwisko": "Jan Kowalski",
        "Miasto": "Warszawa",
        "Email": "jan@example.com",
    }

    with patch("bot.handlers.text.OfferRepository", return_value=repo), patch(
        "bot.handlers.text.lookup_client_by_row",
        new=AsyncMock(return_value=client),
    ), patch(
        "bot.handlers.text.reply_text",
        new=AsyncMock(),
    ) as reply:
        skip_delete = await text._confirm_offer_send(
            MagicMock(),
            telegram_id=123,
            user_id="user-1",
            flow_data={
                "idempotency_key": "key-1",
                "template_id": "tpl-1",
                "client_row": 2,
                "offer_number": 1,
                "command_text": "wyślij ofertę",
            },
        )

    assert skip_delete is False
    repo.enqueue_send_attempt.assert_called_once()
    payload = repo.enqueue_send_attempt.call_args.kwargs
    assert payload["idempotency_key"] == "key-1"
    assert payload["user_id"] == "user-1"
    assert payload["telegram_id"] == 123
    assert payload["client_row"] == 2
    assert payload["offer_template_id"] == "tpl-1"
    reply.assert_awaited_once()
    assert reply.await_args.args[1] == "Wysyłam ofertę. Dam znać po zakończeniu."


@pytest.mark.asyncio
async def test_offer_confirm_falls_back_to_inline_send_when_queue_schema_is_missing():
    from bot.handlers import text

    repo = MagicMock()
    repo.list_templates.return_value = [{
        "id": "tpl-1",
        "status": "ready",
        "name": "PV",
        "price_net_pln": 10000,
        "vat_rate": 8,
        "product_type": "PV",
    }]
    repo.get_seller_profile.return_value = {"company_name": "Firma"}
    repo.enqueue_send_attempt.side_effect = RuntimeError("queue_schema_missing")

    client = {
        "_row": 2,
        "Imię i nazwisko": "Jan Kowalski",
        "Miasto": "Warszawa",
        "Email": "jan@example.com",
    }

    with patch("bot.handlers.text.OfferRepository", return_value=repo), patch(
        "bot.handlers.text.lookup_client_by_row",
        new=AsyncMock(return_value=client),
    ), patch(
        "bot.handlers.text.send_offer_after_confirmation",
        new=AsyncMock(return_value=SendOfferResult(sent=True)),
    ) as send_pipeline, patch(
        "bot.handlers.text.reply_text",
        new=AsyncMock(),
    ) as reply:
        skip_delete = await text._confirm_offer_send(
            MagicMock(),
            telegram_id=123,
            user_id="user-1",
            flow_data={
                "idempotency_key": "key-1",
                "template_id": "tpl-1",
                "client_row": 2,
                "offer_number": 1,
                "command_text": "wyślij ofertę",
            },
        )

    assert skip_delete is False
    send_pipeline.assert_awaited_once()
    assert reply.await_args.args[1] == "✅ Oferta wysłana."
