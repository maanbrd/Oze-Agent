from __future__ import annotations

from datetime import datetime, timezone

import pytest


class _FakeQuery:
    def __init__(self, rows: list[dict]):
        self.rows = rows
        self.updated: dict | None = None

    def select(self, *_args, **_kwargs):
        return self

    def update(self, payload: dict):
        self.updated = payload
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def execute(self):
        if self.updated:
            self.rows[0].update(self.updated)
        return type("Result", (), {"data": self.rows})()


class _FakeSupabase:
    def __init__(self, rows: list[dict]):
        self.rows = rows
        self.last_query: _FakeQuery | None = None

    def table(self, _name: str):
        self.last_query = _FakeQuery(self.rows)
        return self.last_query


@pytest.mark.asyncio
async def test_generate_telegram_code_expires_after_90_seconds(monkeypatch):
    from api.auth import AuthUser
    from api.routes import onboarding

    now = datetime(2026, 5, 4, 12, 0, 0, tzinfo=timezone.utc)
    fake = _FakeSupabase(
        [
            {
                "id": "user-1",
                "auth_user_id": "auth-1",
                "email": "jan@example.pl",
                "subscription_status": "active",
                "activation_paid": True,
                "google_refresh_token": "encrypted",
                "google_sheets_id": "sheet-1",
                "google_calendar_id": "cal-1",
                "google_drive_folder_id": "drive-1",
                "telegram_id": None,
            }
        ]
    )

    class _FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return now if tz else now.replace(tzinfo=None)

    monkeypatch.setattr(onboarding, "get_supabase_client", lambda: fake)
    monkeypatch.setattr(onboarding.secrets, "randbelow", lambda upper: 12345)
    monkeypatch.setattr(onboarding, "datetime", _FrozenDatetime)

    result = await onboarding.generate_telegram_code(
        AuthUser(user_id="auth-1", email="jan@example.pl", claims={})
    )

    expires_at = datetime.fromisoformat(result["expiresAt"])
    assert result["code"] == "112345"
    assert result["paired"] is False
    assert int((expires_at - now).total_seconds()) == 90
    assert fake.last_query.updated["telegram_link_code_expires"] == result["expiresAt"]
