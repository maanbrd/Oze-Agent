from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone

import pytest


class _FakeResult:
    def __init__(self, data):
        self.data = data


class _FakeTable:
    def __init__(self, supabase, name: str):
        self.supabase = supabase
        self.name = name
        self._update_payload: dict | None = None
        self._insert_payload: dict | None = None
        self._eq: tuple[str, object] | None = None

    def insert(self, payload: dict):
        self._insert_payload = payload
        return self

    def select(self, *_args, **_kwargs):
        return self

    def update(self, payload: dict):
        self._update_payload = payload
        return self

    def eq(self, key: str, value: object):
        self._eq = (key, value)
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def execute(self):
        if self.name == "webhook_log" and self._insert_payload is not None:
            self.supabase.webhook_logs.append(self._insert_payload)
            return _FakeResult([self._insert_payload])

        if self.name == "payment_history" and self._insert_payload is not None:
            event_id = self._insert_payload.get("stripe_event_id")
            if event_id and any(row.get("stripe_event_id") == event_id for row in self.supabase.payment_history):
                return _FakeResult([])
            self.supabase.payment_history.append(self._insert_payload)
            return _FakeResult([self._insert_payload])

        if self.name != "users":
            return _FakeResult([])

        rows = self.supabase.users
        if self._eq is not None:
            key, value = self._eq
            rows = [row for row in rows if row.get(key) == value]

        if self._update_payload is not None:
            for row in rows:
                row.update(self._update_payload)
            return _FakeResult(rows)

        return _FakeResult(rows)


class _FakeSupabase:
    def __init__(self):
        self.users = [
            {
                "id": "user-1",
                "auth_user_id": "auth-1",
                "email": "jan@example.pl",
                "subscription_status": "pending_payment",
                "activation_paid": False,
            }
        ]
        self.webhook_logs: list[dict] = []
        self.payment_history: list[dict] = []

    def table(self, name: str):
        return _FakeTable(self, name)


def _signed_headers(body: bytes, secret: str, timestamp: str | None = None):
    timestamp = timestamp or str(int(datetime.now(tz=timezone.utc).timestamp()))
    digest = hmac.new(
        secret.encode(),
        f"{timestamp}.".encode() + body,
        hashlib.sha256,
    ).hexdigest()
    return {
        "x-oze-timestamp": timestamp,
        "x-oze-signature": f"sha256={digest}",
    }


def _iso(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


@pytest.mark.asyncio
async def test_stripe_checkout_event_activates_matching_user(monkeypatch):
    from api.routes import billing

    secret = "test-billing-secret"
    fake = _FakeSupabase()
    event = {
        "id": "evt_reconcile_cs_test_123",
        "type": "checkout.session.completed",
        "created": 1778018828,
        "livemode": False,
        "object": {
            "id": "cs_test_123",
            "object": "checkout.session",
            "livemode": False,
            "mode": "subscription",
            "status": "complete",
            "payment_status": "paid",
            "amount_total": 39900,
            "currency": "pln",
            "customer": "cus_123",
            "subscription": "sub_123",
            "subscription_details": {
                "id": "sub_123",
                "status": "active",
                "current_period_end": 1778623800,
                "cancel_at_period_end": False,
                "livemode": False,
            },
            "client_reference_id": "user-1",
            "customer_email": "jan@example.pl",
            "metadata": {
                "auth_user_id": "auth-1",
                "user_id": "user-1",
                "plan": "monthly",
                "source": "web_onboarding",
            },
        },
    }
    body = json.dumps(event, separators=(",", ":")).encode()

    class _FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            value = datetime.fromtimestamp(1778019000, tz=timezone.utc)
            return value if tz else value.replace(tzinfo=None)

    monkeypatch.setenv("BILLING_INTERNAL_SECRET", secret)
    monkeypatch.setattr(billing, "get_supabase_client", lambda: fake)
    monkeypatch.setattr(billing, "datetime", _FrozenDatetime)

    result = await billing.process_signed_stripe_event(
        body,
        _signed_headers(body, secret, "1778019000"),
    )

    assert result["processed"] is True
    assert fake.users[0]["subscription_status"] == "active"
    assert fake.users[0]["activation_paid"] is True
    assert fake.users[0]["subscription_plan"] == "monthly"
    assert fake.users[0]["stripe_customer_id"] == "cus_123"
    assert fake.users[0]["stripe_subscription_id"] == "sub_123"
    assert fake.users[0]["stripe_checkout_session_id"] == "cs_test_123"
    assert fake.users[0]["stripe_livemode"] is False
    assert fake.users[0]["subscription_current_period_end"] == _iso(1778623800)
    assert fake.payment_history == [
        {
            "user_id": "user-1",
            "amount_pln": 399.0,
            "type": "checkout.session.completed",
            "status": "paid",
            "stripe_event_id": "evt_reconcile_cs_test_123",
            "stripe_checkout_session_id": "cs_test_123",
            "stripe_invoice_id": "",
            "stripe_subscription_id": "sub_123",
            "stripe_customer_id": "cus_123",
            "currency": "pln",
            "stripe_livemode": False,
        }
    ]
    assert fake.webhook_logs[0]["processed"] is True


@pytest.mark.asyncio
async def test_stripe_checkout_event_rejects_mismatched_auth_user(monkeypatch):
    from fastapi import HTTPException
    from api.routes import billing

    secret = "test-billing-secret"
    fake = _FakeSupabase()
    event = {
        "id": "evt_bad",
        "type": "checkout.session.completed",
        "object": {
            "id": "cs_test_bad",
            "object": "checkout.session",
            "mode": "subscription",
            "status": "complete",
            "payment_status": "paid",
            "client_reference_id": "user-1",
            "metadata": {"auth_user_id": "other-auth", "user_id": "user-1"},
        },
    }
    body = json.dumps(event, separators=(",", ":")).encode()

    monkeypatch.setenv("BILLING_INTERNAL_SECRET", secret)
    monkeypatch.setattr(billing, "get_supabase_client", lambda: fake)

    with pytest.raises(HTTPException) as exc:
        await billing.process_signed_stripe_event(
            body,
            _signed_headers(body, secret),
        )

    assert exc.value.status_code == 409
    assert fake.users[0]["subscription_status"] == "pending_payment"


@pytest.mark.asyncio
async def test_stripe_invoice_failed_marks_user_pending_and_logs_payment_snapshot(monkeypatch):
    from api.routes import billing

    secret = "test-billing-secret"
    fake = _FakeSupabase()
    fake.users[0].update({
        "subscription_status": "active",
        "activation_paid": True,
        "stripe_subscription_id": "sub_123",
        "stripe_customer_id": "cus_123",
    })
    event = {
        "id": "evt_invoice_failed_123",
        "type": "invoice.payment_failed",
        "object": {
            "id": "in_123",
            "object": "invoice",
            "livemode": True,
            "subscription": "sub_123",
            "customer": "cus_123",
            "amount_due": 39900,
            "currency": "pln",
            "status": "open",
        },
    }
    body = json.dumps(event, separators=(",", ":")).encode()

    monkeypatch.setenv("BILLING_INTERNAL_SECRET", secret)
    monkeypatch.setattr(billing, "get_supabase_client", lambda: fake)

    result = await billing.process_signed_stripe_event(
        body,
        _signed_headers(body, secret),
    )

    assert result["processed"] is True
    assert fake.users[0]["subscription_status"] == "pending_payment"
    assert fake.users[0]["activation_paid"] is False
    assert fake.users[0]["stripe_livemode"] is True
    assert fake.payment_history == [
        {
            "user_id": "user-1",
            "amount_pln": 399.0,
            "type": "invoice.payment_failed",
            "status": "failed",
            "stripe_event_id": "evt_invoice_failed_123",
            "stripe_checkout_session_id": "",
            "stripe_invoice_id": "in_123",
            "stripe_subscription_id": "sub_123",
            "stripe_customer_id": "cus_123",
            "currency": "pln",
            "stripe_livemode": True,
        }
    ]


@pytest.mark.asyncio
async def test_stripe_event_does_not_duplicate_payment_history_snapshot(monkeypatch):
    from api.routes import billing

    secret = "test-billing-secret"
    fake = _FakeSupabase()
    event = {
        "id": "evt_duplicate",
        "type": "checkout.session.completed",
        "object": {
            "id": "cs_duplicate",
            "object": "checkout.session",
            "mode": "subscription",
            "status": "complete",
            "payment_status": "paid",
            "amount_total": 39900,
            "currency": "pln",
            "customer": "cus_123",
            "subscription": "sub_123",
            "client_reference_id": "user-1",
            "metadata": {"auth_user_id": "auth-1", "user_id": "user-1", "plan": "monthly"},
        },
    }
    body = json.dumps(event, separators=(",", ":")).encode()

    monkeypatch.setenv("BILLING_INTERNAL_SECRET", secret)
    monkeypatch.setattr(billing, "get_supabase_client", lambda: fake)

    await billing.process_signed_stripe_event(body, _signed_headers(body, secret))
    await billing.process_signed_stripe_event(body, _signed_headers(body, secret))

    assert len(fake.payment_history) == 1
