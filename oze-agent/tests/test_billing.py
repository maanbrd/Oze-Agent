import pytest
from fastapi import HTTPException


def test_verify_internal_signature_accepts_valid_hmac(monkeypatch):
    from api.routes import billing
    from bot.config import Config

    monkeypatch.setattr(Config, "BILLING_INTERNAL_SECRET", "test-secret")
    raw_body = b'{"id":"evt_1"}'
    timestamp = "1000"
    signature = billing._expected_signature(raw_body, timestamp, "test-secret")

    billing.verify_internal_signature(raw_body, timestamp, signature, now=1000)


def test_verify_internal_signature_rejects_stale_timestamp(monkeypatch):
    from api.routes import billing
    from bot.config import Config

    monkeypatch.setattr(Config, "BILLING_INTERNAL_SECRET", "test-secret")
    raw_body = b'{"id":"evt_1"}'
    signature = billing._expected_signature(raw_body, "1000", "test-secret")

    with pytest.raises(HTTPException) as exc:
        billing.verify_internal_signature(raw_body, "1000", signature, now=2000)

    assert exc.value.status_code == 401


def test_verify_internal_signature_rejects_bad_signature(monkeypatch):
    from api.routes import billing
    from bot.config import Config

    monkeypatch.setattr(Config, "BILLING_INTERNAL_SECRET", "test-secret")

    with pytest.raises(HTTPException) as exc:
        billing.verify_internal_signature(
            b'{"id":"evt_1"}',
            "1000",
            "sha256=bad",
            now=1000,
        )

    assert exc.value.status_code == 401


def test_process_stripe_event_skips_processed_duplicate(monkeypatch):
    from api.routes import billing

    monkeypatch.setattr(
        billing,
        "_get_existing_log",
        lambda event_id: {"id": "log-1", "processed": True},
    )

    result = billing.process_stripe_event(
        {
            "id": "evt_1",
            "type": "checkout.session.completed",
            "object": {"object": "checkout.session"},
        }
    )

    assert result == {"processed": False, "duplicate": True}


def test_process_stripe_event_rejects_live_mode(monkeypatch):
    from api.routes import billing

    monkeypatch.setattr(billing, "_get_existing_log", lambda event_id: None)

    with pytest.raises(HTTPException) as exc:
        billing.process_stripe_event(
            {
                "id": "evt_live",
                "type": "checkout.session.completed",
                "livemode": True,
                "object": {"object": "checkout.session", "payment_status": "paid"},
            }
        )

    assert exc.value.status_code == 400
    assert "Live Stripe events are disabled" in exc.value.detail


def test_checkout_completed_does_not_activate_until_paid(monkeypatch):
    from api.routes import billing

    marked = []
    monkeypatch.setattr(billing, "_get_existing_log", lambda event_id: None)
    monkeypatch.setattr(billing, "_insert_log", lambda payload: "log-1")
    monkeypatch.setattr(billing, "_mark_log_processed", lambda log_id: marked.append(log_id))

    result = billing.process_stripe_event(
        {
            "id": "evt_unpaid",
            "type": "checkout.session.completed",
            "object": {
                "object": "checkout.session",
                "id": "cs_1",
                "payment_status": "unpaid",
                "metadata": {"user_id": "user-1", "plan": "monthly"},
            },
        }
    )

    assert result["activated"] is False
    assert result["reason"] == "payment_not_paid"
    assert marked == ["log-1"]


class _FakeSupabase:
    def __init__(self):
        self.current_table = None
        self.updates = []
        self.filters = []

    def table(self, name):
        self.current_table = name
        return self

    def update(self, data):
        self.updates.append((self.current_table, data))
        return self

    def eq(self, key, value):
        self.filters.append((self.current_table, key, value))
        return self

    def execute(self):
        class Result:
            data = []

        return Result()


def test_checkout_paid_activates_user_and_records_side_effects(monkeypatch):
    from api.routes import billing

    fake_db = _FakeSupabase()
    payments = []
    outbox = []

    monkeypatch.setattr(billing, "_get_existing_log", lambda event_id: None)
    monkeypatch.setattr(billing, "_insert_log", lambda payload: "log-1")
    monkeypatch.setattr(billing, "_mark_log_processed", lambda log_id: None)
    monkeypatch.setattr(billing, "get_supabase_client", lambda: fake_db)
    monkeypatch.setattr(
        billing,
        "_insert_payment_history",
        lambda user_id, event_id, obj, payment_type: payments.append(
            (user_id, event_id, payment_type)
        ),
    )
    monkeypatch.setattr(
        billing,
        "_insert_outbox",
        lambda user_id, event_id, event_type, payload: outbox.append(
            (user_id, event_id, event_type)
        ),
    )

    result = billing.process_stripe_event(
        {
            "id": "evt_paid",
            "type": "checkout.session.completed",
            "object": {
                "object": "checkout.session",
                "id": "cs_1",
                "payment_status": "paid",
                "customer": "cus_1",
                "subscription": "sub_1",
                "amount_total": 24800,
                "currency": "pln",
                "metadata": {"user_id": "user-1", "plan": "monthly"},
            },
        }
    )

    assert result["activated"] is True
    assert ("users", "id", "user-1") in fake_db.filters
    assert fake_db.updates[0][1]["subscription_status"] == "active"
    assert fake_db.updates[0][1]["activation_paid"] is True
    assert payments == [("user-1", "evt_paid", "stripe_checkout")]
    assert outbox == [("user-1", "evt_paid", "billing_activated")]


def test_checkout_paid_requires_user_metadata(monkeypatch):
    from api.routes import billing

    monkeypatch.setattr(billing, "_get_existing_log", lambda event_id: None)
    monkeypatch.setattr(billing, "_insert_log", lambda payload: "log-1")

    with pytest.raises(HTTPException) as exc:
        billing.process_stripe_event(
            {
                "id": "evt_no_user",
                "type": "checkout.session.completed",
                "object": {
                    "object": "checkout.session",
                    "id": "cs_1",
                    "payment_status": "paid",
                    "metadata": {},
                },
            }
        )

    assert exc.value.status_code == 422
