from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException


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
                "stripe_subscription_id": "sub_123",
                "stripe_customer_id": "cus_123",
                "stripe_livemode": False,
            }
        ]
        self.webhook_logs: list[dict] = []
        self.payment_history: list[dict] = []

    def table(self, name: str):
        return _FakeTable(self, name)


class _FrozenDatetime(datetime):
    @classmethod
    def now(cls, tz=None):
        value = datetime.fromtimestamp(1778019000, tz=timezone.utc)
        return value if tz else value.replace(tzinfo=None)


def _signed_headers(body: bytes, secret: str, timestamp: str = "1778019000"):
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


def test_verify_internal_signature_accepts_valid_hmac(monkeypatch):
    from api.routes import billing

    secret = "test-secret"
    body = b'{"id":"evt_1"}'
    monkeypatch.setenv("BILLING_INTERNAL_SECRET", secret)
    monkeypatch.setattr(billing, "datetime", _FrozenDatetime)

    billing._verify_internal_signature(body, _signed_headers(body, secret))


def test_verify_internal_signature_rejects_stale_timestamp(monkeypatch):
    from api.routes import billing

    secret = "test-secret"
    body = b'{"id":"evt_1"}'
    monkeypatch.setenv("BILLING_INTERNAL_SECRET", secret)
    monkeypatch.setattr(billing, "datetime", _FrozenDatetime)

    with pytest.raises(HTTPException) as exc:
        billing._verify_internal_signature(body, _signed_headers(body, secret, "1000"))

    assert exc.value.status_code == 401


def test_verify_internal_signature_rejects_bad_signature(monkeypatch):
    from api.routes import billing

    monkeypatch.setenv("BILLING_INTERNAL_SECRET", "test-secret")
    monkeypatch.setattr(billing, "datetime", _FrozenDatetime)

    with pytest.raises(HTTPException) as exc:
        billing._verify_internal_signature(
            b'{"id":"evt_1"}',
            {
                "x-oze-timestamp": "1778019000",
                "x-oze-signature": "sha256=bad",
            },
        )

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_unsupported_stripe_event_is_logged_without_processing(monkeypatch):
    from api.routes import billing

    secret = "test-secret"
    fake = _FakeSupabase()
    event = {
        "id": "evt_unknown",
        "type": "customer.created",
        "object": {"object": "customer", "id": "cus_123"},
    }
    body = json.dumps(event, separators=(",", ":")).encode()

    monkeypatch.setenv("BILLING_INTERNAL_SECRET", secret)
    monkeypatch.setattr(billing, "datetime", _FrozenDatetime)
    monkeypatch.setattr(billing, "get_supabase_client", lambda: fake)

    result = await billing.process_signed_stripe_event(body, _signed_headers(body, secret))

    assert result == {"received": True, "processed": False}
    assert fake.webhook_logs[0]["processed"] is False
    assert fake.payment_history == []


@pytest.mark.asyncio
async def test_checkout_completed_does_not_activate_until_paid(monkeypatch):
    from api.routes import billing

    secret = "test-secret"
    fake = _FakeSupabase()
    event = {
        "id": "evt_unpaid",
        "type": "checkout.session.completed",
        "object": {
            "object": "checkout.session",
            "id": "cs_1",
            "mode": "subscription",
            "status": "open",
            "payment_status": "unpaid",
            "metadata": {"user_id": "user-1", "plan": "monthly"},
        },
    }
    body = json.dumps(event, separators=(",", ":")).encode()

    monkeypatch.setenv("BILLING_INTERNAL_SECRET", secret)
    monkeypatch.setattr(billing, "datetime", _FrozenDatetime)
    monkeypatch.setattr(billing, "get_supabase_client", lambda: fake)

    with pytest.raises(HTTPException) as exc:
        await billing.process_signed_stripe_event(body, _signed_headers(body, secret))

    assert exc.value.status_code == 409
    assert fake.users[0]["subscription_status"] == "pending_payment"
    assert fake.payment_history == []


@pytest.mark.asyncio
async def test_invoice_payment_succeeded_updates_subscription_and_logs_snapshot(monkeypatch):
    from api.routes import billing

    secret = "test-secret"
    fake = _FakeSupabase()
    event = {
        "id": "evt_invoice",
        "type": "invoice.payment_succeeded",
        "object": {
            "object": "invoice",
            "id": "in_1",
            "livemode": True,
            "customer": "cus_123",
            "subscription": "sub_123",
            "subscription_details": {
                "id": "sub_123",
                "status": "active",
                "current_period_end": 1778623800,
                "cancel_at_period_end": False,
                "livemode": True,
            },
            "amount_paid": 39900,
            "currency": "pln",
        },
    }
    body = json.dumps(event, separators=(",", ":")).encode()

    monkeypatch.setenv("BILLING_INTERNAL_SECRET", secret)
    monkeypatch.setattr(billing, "datetime", _FrozenDatetime)
    monkeypatch.setattr(billing, "get_supabase_client", lambda: fake)

    result = await billing.process_signed_stripe_event(body, _signed_headers(body, secret))

    assert result["processed"] is True
    assert fake.users[0]["subscription_status"] == "active"
    assert fake.users[0]["activation_paid"] is True
    assert fake.users[0]["stripe_livemode"] is True
    assert fake.users[0]["subscription_current_period_end"] == _iso(1778623800)
    assert fake.payment_history == [
        {
            "user_id": "user-1",
            "amount_pln": 399.0,
            "type": "invoice.payment_succeeded",
            "status": "paid",
            "stripe_event_id": "evt_invoice",
            "stripe_checkout_session_id": "",
            "stripe_invoice_id": "in_1",
            "stripe_subscription_id": "sub_123",
            "stripe_customer_id": "cus_123",
            "currency": "pln",
            "stripe_livemode": True,
        }
    ]


@pytest.mark.asyncio
async def test_checkout_session_uses_enriched_subscription_period_and_livemode(monkeypatch):
    from api.routes import billing

    secret = "test-secret"
    fake = _FakeSupabase()
    event = {
        "id": "evt_checkout_live",
        "type": "checkout.session.completed",
        "livemode": True,
        "object": {
            "object": "checkout.session",
            "id": "cs_live_123",
            "livemode": True,
            "mode": "subscription",
            "status": "complete",
            "payment_status": "paid",
            "amount_total": 39900,
            "currency": "pln",
            "customer": "cus_live_123",
            "subscription": "sub_live_123",
            "subscription_details": {
                "id": "sub_live_123",
                "status": "active",
                "current_period_end": 1778623800,
                "cancel_at_period_end": False,
                "livemode": True,
            },
            "metadata": {"user_id": "user-1", "plan": "monthly"},
        },
    }
    body = json.dumps(event, separators=(",", ":")).encode()

    monkeypatch.setenv("BILLING_INTERNAL_SECRET", secret)
    monkeypatch.setattr(billing, "datetime", _FrozenDatetime)
    monkeypatch.setattr(billing, "get_supabase_client", lambda: fake)

    result = await billing.process_signed_stripe_event(body, _signed_headers(body, secret))

    assert result["processed"] is True
    assert fake.users[0]["subscription_status"] == "active"
    assert fake.users[0]["activation_paid"] is True
    assert fake.users[0]["stripe_livemode"] is True
    assert fake.users[0]["stripe_subscription_id"] == "sub_live_123"
    assert fake.users[0]["stripe_checkout_session_id"] == "cs_live_123"
    assert fake.users[0]["subscription_current_period_end"] == _iso(1778623800)
    assert fake.payment_history[0]["stripe_livemode"] is True


@pytest.mark.asyncio
async def test_subscription_updated_cancel_at_period_end_keeps_access_until_period_end(monkeypatch):
    from api.routes import billing

    secret = "test-secret"
    fake = _FakeSupabase()
    fake.users[0].update(
        {
            "subscription_status": "active",
            "activation_paid": True,
            "stripe_livemode": True,
            "subscription_current_period_end": _iso(1778623800),
        }
    )
    event = {
        "id": "evt_sub_updated",
        "type": "customer.subscription.updated",
        "livemode": True,
        "object": {
            "object": "subscription",
            "id": "sub_123",
            "livemode": True,
            "customer": "cus_123",
            "status": "active",
            "cancel_at_period_end": True,
            "current_period_end": 1779228600,
            "currency": "pln",
        },
    }
    body = json.dumps(event, separators=(",", ":")).encode()

    monkeypatch.setenv("BILLING_INTERNAL_SECRET", secret)
    monkeypatch.setattr(billing, "datetime", _FrozenDatetime)
    monkeypatch.setattr(billing, "get_supabase_client", lambda: fake)

    result = await billing.process_signed_stripe_event(body, _signed_headers(body, secret))

    assert result["processed"] is True
    assert fake.users[0]["subscription_status"] == "active"
    assert fake.users[0]["activation_paid"] is True
    assert fake.users[0]["stripe_livemode"] is True
    assert fake.users[0]["subscription_current_period_end"] == _iso(1779228600)


@pytest.mark.asyncio
async def test_subscription_deleted_cancels_user_and_logs_zero_amount_snapshot(monkeypatch):
    from api.routes import billing

    secret = "test-secret"
    fake = _FakeSupabase()
    fake.users[0]["subscription_status"] = "active"
    fake.users[0]["activation_paid"] = True
    event = {
        "id": "evt_sub_deleted",
        "type": "customer.subscription.deleted",
        "object": {
            "object": "subscription",
            "id": "sub_123",
            "livemode": True,
            "customer": "cus_123",
            "status": "canceled",
            "currency": "pln",
        },
    }
    body = json.dumps(event, separators=(",", ":")).encode()

    monkeypatch.setenv("BILLING_INTERNAL_SECRET", secret)
    monkeypatch.setattr(billing, "datetime", _FrozenDatetime)
    monkeypatch.setattr(billing, "get_supabase_client", lambda: fake)

    result = await billing.process_signed_stripe_event(body, _signed_headers(body, secret))

    assert result["processed"] is True
    assert fake.users[0]["subscription_status"] == "canceled"
    assert fake.users[0]["activation_paid"] is False
    assert fake.users[0]["stripe_livemode"] is True
    assert fake.payment_history[0]["amount_pln"] == 0.0
    assert fake.payment_history[0]["status"] == "canceled"
    assert fake.payment_history[0]["stripe_livemode"] is True
