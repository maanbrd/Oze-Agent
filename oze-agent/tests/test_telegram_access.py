from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from bot.utils import telegram_helpers


class _FakeResult:
    def __init__(self, data):
        self.data = data


class _FakeQuery:
    def __init__(self, rows):
        self.rows = rows
        self.filters: dict[str, str] = {}

    def table(self, _name: str):
        return self

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, key: str, value):
        self.filters[key] = value
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def execute(self):
        rows = [
            row
            for row in self.rows
            if all(row.get(key) == value for key, value in self.filters.items())
        ]
        return _FakeResult(rows)


def _future_period_end() -> str:
    return (datetime.now(tz=timezone.utc) + timedelta(days=30)).isoformat()


def _expired_period_end() -> str:
    return (datetime.now(tz=timezone.utc) - timedelta(seconds=1)).isoformat()


@pytest.mark.asyncio
async def test_subscription_guard_allows_active_live_paid_user(monkeypatch):
    fake = _FakeQuery([])
    monkeypatch.setattr(telegram_helpers, "get_supabase_client", lambda: fake)

    allowed = await telegram_helpers.check_subscription_active(
        {
            "auth_user_id": "auth-1",
            "subscription_status": "active",
            "activation_paid": True,
            "stripe_livemode": True,
            "subscription_current_period_end": _future_period_end(),
            "is_suspended": False,
        }
    )

    assert allowed is True


@pytest.mark.asyncio
async def test_subscription_guard_rejects_active_test_mode_payment(monkeypatch):
    fake = _FakeQuery([])
    monkeypatch.setattr(telegram_helpers, "get_supabase_client", lambda: fake)

    allowed = await telegram_helpers.check_subscription_active(
        {
            "auth_user_id": "auth-1",
            "subscription_status": "active",
            "activation_paid": True,
            "stripe_livemode": False,
            "subscription_current_period_end": _future_period_end(),
            "is_suspended": False,
        }
    )

    assert allowed is False


@pytest.mark.asyncio
async def test_subscription_guard_rejects_expired_live_payment(monkeypatch):
    fake = _FakeQuery([])
    monkeypatch.setattr(telegram_helpers, "get_supabase_client", lambda: fake)

    allowed = await telegram_helpers.check_subscription_active(
        {
            "auth_user_id": "auth-1",
            "subscription_status": "active",
            "activation_paid": True,
            "stripe_livemode": True,
            "subscription_current_period_end": _expired_period_end(),
            "is_suspended": False,
        }
    )

    assert allowed is False


@pytest.mark.asyncio
async def test_subscription_guard_allows_claimed_beta_access(monkeypatch):
    fake = _FakeQuery(
        [{"id": "grant-1", "auth_user_id": "auth-1", "status": "active"}]
    )
    monkeypatch.setattr(telegram_helpers, "get_supabase_client", lambda: fake)

    allowed = await telegram_helpers.check_subscription_active(
        {
            "auth_user_id": "auth-1",
            "subscription_status": "pending_payment",
            "is_suspended": False,
        }
    )

    assert allowed is True


@pytest.mark.asyncio
async def test_subscription_guard_rejects_unclaimed_beta_access(monkeypatch):
    fake = _FakeQuery(
        [{"id": "grant-1", "auth_user_id": None, "status": "active"}]
    )
    monkeypatch.setattr(telegram_helpers, "get_supabase_client", lambda: fake)

    allowed = await telegram_helpers.check_subscription_active(
        {
            "auth_user_id": "auth-1",
            "subscription_status": "pending_payment",
            "is_suspended": False,
        }
    )

    assert allowed is False
