import pytest

from shared.offers.pipeline import SendOfferResult, send_offer_after_confirmation
from shared.offers.status_policy import should_mark_offer_sent


def test_terminal_statuses_are_not_moved_back_to_offer_sent():
    for status in [
        "Podpisane",
        "Zamontowana",
        "Rezygnacja z umowy",
        "Nieaktywny",
        "Odrzucone",
        "Oferta wysłana",
    ]:
        assert not should_mark_offer_sent(status)


def test_early_statuses_can_move_to_offer_sent():
    assert should_mark_offer_sent("")
    assert should_mark_offer_sent("Nowy lead")
    assert should_mark_offer_sent("Spotkanie umówione")
    assert should_mark_offer_sent("Spotkanie odbyte")


@pytest.mark.asyncio
async def test_send_pipeline_is_idempotent_when_attempt_already_sent():
    class Repo:
        def ensure_send_attempt(self, **kwargs):
            return {"idempotency_key": kwargs["idempotency_key"], "status": "sent", "gmail_message_id": "msg-1"}

        def claim_send_attempt(self, idempotency_key):
            return None

        def get_send_attempt(self, idempotency_key):
            return {"status": "sent", "gmail_message_id": "msg-1"}

    result = await send_offer_after_confirmation(
        user_id="user-1",
        telegram_id=123,
        idempotency_key="key-1",
        offer_number=1,
        template={"id": "tpl-1", "name": "PV", "price_net_pln": 10000, "vat_rate": 8, "product_type": "PV"},
        seller_profile={"company_name": "Firma"},
        client={"_row": 2, "Imię i nazwisko": "Jan Kowalski", "Email": "jan@example.com"},
        command_text="",
        repository=Repo(),
        gmail_sender=None,
        update_email=None,
        update_status=None,
    )

    assert result == SendOfferResult(
        sent=True,
        already_sent=True,
        gmail_message_id="msg-1",
        recipients=[],
        invalid_recipients=[],
        sheets_errors=[],
    )
