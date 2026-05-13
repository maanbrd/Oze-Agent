from __future__ import annotations

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
