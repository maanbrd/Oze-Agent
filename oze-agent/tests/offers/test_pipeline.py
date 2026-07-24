import pytest

from shared.offers.pipeline import SendOfferResult, send_offer_after_confirmation
from shared.offers.status_policy import should_mark_offer_sent


class RecordingRepo:
    def __init__(self, attempt_status="pending"):
        self.attempt_status = attempt_status
        self.events = []
        self.failed_error = None
        self.gmail_message_id = None

    def ensure_send_attempt(self, **kwargs):
        self.events.append(("ensure", kwargs["idempotency_key"], kwargs["recipients"]))
        return {
            "idempotency_key": kwargs["idempotency_key"],
            "status": self.attempt_status,
            "gmail_message_id": self.gmail_message_id,
        }

    def claim_send_attempt(self, idempotency_key):
        self.events.append(("claim", idempotency_key))
        return {"idempotency_key": idempotency_key, "status": "sending"}

    def get_send_attempt(self, idempotency_key):
        self.events.append(("get", idempotency_key))
        return {
            "idempotency_key": idempotency_key,
            "status": self.attempt_status,
            "gmail_message_id": self.gmail_message_id,
            "error": self.failed_error,
        }

    def mark_send_sent(self, idempotency_key, gmail_message_id):
        self.events.append(("sent", idempotency_key, gmail_message_id))
        self.attempt_status = "sent"
        self.gmail_message_id = gmail_message_id

    def mark_send_failed(self, idempotency_key, error):
        self.events.append(("failed", idempotency_key, error))
        self.attempt_status = "failed"
        self.failed_error = error

    def mark_send_reconcile_required(self, idempotency_key, gmail_message_id, error):
        self.events.append(("reconcile", idempotency_key, gmail_message_id, error))
        self.attempt_status = "reconcile_required"


def _template():
    return {
        "id": "tpl-1",
        "name": "PV 6 kWp",
        "price_net_pln": 30000,
        "vat_rate": 8,
        "product_type": "PV",
    }


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


@pytest.mark.asyncio
async def test_send_pipeline_does_not_touch_sheets_when_gmail_fails(monkeypatch):
    monkeypatch.setattr("shared.offers.pipeline.render_offer_pdf", lambda *_args, **_kwargs: b"%PDF-1")
    repo = RecordingRepo()
    sheet_calls = []

    async def gmail_sender(*_args, **_kwargs):
        raise RuntimeError("gmail_down")

    async def update_email(*args):
        sheet_calls.append(("email", args))
        return True

    async def update_status(*args):
        sheet_calls.append(("status", args))
        return True

    result = await send_offer_after_confirmation(
        user_id="user-1",
        telegram_id=123,
        idempotency_key="key-fail",
        offer_number=1,
        template=_template(),
        seller_profile={"company_name": "Firma"},
        client={
            "_row": 2,
            "Imię i nazwisko": "Jan Kowalski",
            "Email": "jan@example.com",
            "Status": "Nowy lead",
        },
        command_text="wyślij też na nowy@example.com",
        repository=repo,
        gmail_sender=gmail_sender,
        update_email=update_email,
        update_status=update_status,
    )

    assert not result.sent
    assert result.error == "gmail_down"
    assert sheet_calls == []
    assert repo.events[-1] == ("failed", "key-fail", "gmail_down")


@pytest.mark.asyncio
async def test_send_pipeline_requires_valid_recipient_before_gmail_or_sheets(monkeypatch):
    monkeypatch.setattr("shared.offers.pipeline.render_offer_pdf", lambda *_args, **_kwargs: b"%PDF-1")
    repo = RecordingRepo()
    gmail_calls = []
    sheet_calls = []

    async def gmail_sender(*args, **_kwargs):
        gmail_calls.append(args)
        return "msg-1"

    async def update_status(*args):
        sheet_calls.append(args)
        return True

    result = await send_offer_after_confirmation(
        user_id="user-1",
        telegram_id=123,
        idempotency_key="key-missing-email",
        offer_number=1,
        template=_template(),
        seller_profile={"company_name": "Firma"},
        client={
            "_row": 2,
            "Imię i nazwisko": "Jan Kowalski",
            "Email": "bledny@@x",
            "Status": "Nowy lead",
        },
        command_text="",
        repository=repo,
        gmail_sender=gmail_sender,
        update_status=update_status,
    )

    assert result == SendOfferResult(
        sent=False,
        recipients=[],
        invalid_recipients=["bledny@@x"],
        error="missing_valid_email",
    )
    assert gmail_calls == []
    assert sheet_calls == []
    assert repo.events[-1] == ("failed", "key-missing-email", "missing_valid_email")


@pytest.mark.asyncio
async def test_send_pipeline_redacts_unclassified_gmail_exception(monkeypatch):
    monkeypatch.setattr("shared.offers.pipeline.render_offer_pdf", lambda *_args, **_kwargs: b"%PDF-1")
    repo = RecordingRepo()

    async def gmail_sender(*_args, **_kwargs):
        raise RuntimeError("recipient jan@example.com failed")

    result = await send_offer_after_confirmation(
        user_id="user-1",
        telegram_id=123,
        idempotency_key="key-redacted-fail",
        offer_number=1,
        template=_template(),
        seller_profile={"company_name": "Firma"},
        client={
            "_row": 2,
            "Imię i nazwisko": "Jan Kowalski",
            "Email": "jan@example.com",
            "Status": "Nowy lead",
        },
        command_text="",
        repository=repo,
        gmail_sender=gmail_sender,
    )

    assert not result.sent
    assert result.error == "RuntimeError"
    assert repo.events[-1] == ("failed", "key-redacted-fail", "RuntimeError")


@pytest.mark.asyncio
async def test_send_pipeline_updates_sheets_only_after_success_and_reports_partial_failures(monkeypatch):
    monkeypatch.setattr("shared.offers.pipeline.render_offer_pdf", lambda *_args, **_kwargs: b"%PDF-1")
    repo = RecordingRepo()

    async def gmail_sender(*_args, **_kwargs):
        repo.events.append(("gmail",))
        return "msg-1"

    async def update_email(*_args):
        repo.events.append(("sheet_email",))
        return False

    async def update_status(*_args):
        repo.events.append(("sheet_status",))
        return False

    result = await send_offer_after_confirmation(
        user_id="user-1",
        telegram_id=123,
        idempotency_key="key-partial",
        offer_number=1,
        template=_template(),
        seller_profile={"company_name": "Firma"},
        client={
            "_row": 2,
            "Imię i nazwisko": "Jan Kowalski",
            "Email": "jan@example.com",
            "Status": "Nowy lead",
        },
        command_text="wyślij też na nowy@example.com",
        repository=repo,
        gmail_sender=gmail_sender,
        update_email=update_email,
        update_status=update_status,
    )

    assert result.sent
    assert result.gmail_message_id == "msg-1"
    assert result.recipients == ["jan@example.com", "nowy@example.com"]
    assert result.sheets_errors == ["email", "status"]
    assert repo.events == [
        ("ensure", "key-partial", ["jan@example.com", "nowy@example.com"]),
        ("claim", "key-partial"),
        ("gmail",),
        ("sent", "key-partial", "msg-1"),
        ("sheet_email",),
        ("sheet_status",),
    ]


@pytest.mark.asyncio
async def test_gmail_success_with_db_ack_failure_is_not_retried(monkeypatch):
    """After Gmail accepted a message, uncertainty must stop automatic retries."""
    monkeypatch.setattr("shared.offers.pipeline.render_offer_pdf", lambda *_a, **_k: b"%PDF-1")

    class AckFailRepo(RecordingRepo):
        def mark_send_sent(self, idempotency_key, gmail_message_id):
            raise RuntimeError("db_down")

    repo = AckFailRepo()

    async def gmail_sender(*_args, **_kwargs):
        return "gmail-accepted-1"

    result = await send_offer_after_confirmation(
        user_id="user-1",
        telegram_id=123,
        idempotency_key="key-ambiguous",
        offer_number=1,
        template=_template(),
        seller_profile={"company_name": "Firma"},
        client={"_row": 2, "Imię i nazwisko": "Jan Kowalski", "Email": "jan@example.com"},
        command_text="",
        repository=repo,
        gmail_sender=gmail_sender,
    )

    assert not result.sent
    assert result.error == "delivery_ambiguous"
    assert repo.events[-1][:3] == ("reconcile", "key-ambiguous", "gmail-accepted-1")
