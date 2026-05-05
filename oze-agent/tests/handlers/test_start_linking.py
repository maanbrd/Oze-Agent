from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from bot.handlers import start


class _FakeSupabaseResult:
    def __init__(self, data):
        self.data = data


class _FakeUserQuery:
    def __init__(self, user):
        self.user = user

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def single(self):
        return self

    def execute(self):
        return _FakeSupabaseResult(self.user)


class _FakeSupabase:
    def __init__(self, user):
        self.user = user

    def table(self, _name: str):
        return _FakeUserQuery(self.user)


def _linked_user(**overrides):
    return {
        "id": "user-1",
        "name": "Jan Testowy",
        "telegram_link_code": "123456",
        "telegram_link_code_expires": (
            datetime.now(timezone.utc) + timedelta(seconds=60)
        ).isoformat(),
        "telegram_id": None,
        **overrides,
    }


@pytest.mark.asyncio
async def test_linking_code_updates_user_and_confirms_success(monkeypatch):
    replies: list[str] = []
    update = MagicMock()
    user = _linked_user()

    async def fake_reply_text(_update, text, **_kwargs):
        replies.append(text)

    monkeypatch.setattr(start, "reply_text", fake_reply_text)
    monkeypatch.setattr(start, "get_supabase_client", lambda: _FakeSupabase(user))
    monkeypatch.setattr(start, "get_user_by_telegram_id", lambda _telegram_id: None)
    monkeypatch.setattr(
        start,
        "update_user",
        lambda user_id, payload: {"id": user_id, **payload},
    )

    await start._handle_linking_code(update, telegram_id=987654, linking_code="123456")

    assert "pomyślnie połączone" in replies[0]


@pytest.mark.asyncio
async def test_linking_code_does_not_confirm_when_update_fails(monkeypatch):
    replies: list[str] = []
    update = MagicMock()
    user = _linked_user()

    async def fake_reply_text(_update, text, **_kwargs):
        replies.append(text)

    monkeypatch.setattr(start, "reply_text", fake_reply_text)
    monkeypatch.setattr(start, "get_supabase_client", lambda: _FakeSupabase(user))
    monkeypatch.setattr(start, "get_user_by_telegram_id", lambda _telegram_id: None)
    monkeypatch.setattr(start, "update_user", lambda _user_id, _payload: None)

    await start._handle_linking_code(update, telegram_id=987654, linking_code="123456")

    assert "Nie udało się połączyć konta Telegram" in replies[0]
    assert "pomyślnie połączone" not in replies[0]


@pytest.mark.asyncio
async def test_linking_code_blocks_telegram_id_already_used_by_other_user(monkeypatch):
    replies: list[str] = []
    update = MagicMock()
    user = _linked_user()
    updates: list[dict] = []

    async def fake_reply_text(_update, text, **_kwargs):
        replies.append(text)

    monkeypatch.setattr(start, "reply_text", fake_reply_text)
    monkeypatch.setattr(start, "get_supabase_client", lambda: _FakeSupabase(user))
    monkeypatch.setattr(
        start,
        "get_user_by_telegram_id",
        lambda _telegram_id: {"id": "other-user"},
    )
    monkeypatch.setattr(
        start,
        "update_user",
        lambda _user_id, payload: updates.append(payload),
    )

    await start._handle_linking_code(update, telegram_id=987654, linking_code="123456")

    assert "już połączone z innym użytkownikiem" in replies[0]
    assert updates == []
