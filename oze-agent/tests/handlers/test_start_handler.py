from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.handlers.start import _WELCOME_MESSAGE, _handle_linking_code


class _FakeUsersQuery:
    def __init__(self, user: dict | None):
        self._user = user

    def select(self, *_args):
        return self

    def eq(self, *_args):
        return self

    def single(self):
        return self

    def execute(self):
        result = MagicMock()
        result.data = self._user
        return result


class _FakeSupabaseClient:
    def __init__(self, user: dict | None):
        self._user = user

    def table(self, table_name: str):
        assert table_name == "users"
        return _FakeUsersQuery(self._user)


def _update() -> MagicMock:
    update = MagicMock()
    update.message.reply_text = AsyncMock()
    return update


def _link_user(**overrides) -> dict:
    user = {
        "id": "user-123",
        "name": "Smoke User",
        "telegram_link_code": "868509",
        "telegram_link_code_expires": (
            datetime.now(tz=timezone.utc) + timedelta(minutes=15)
        ).isoformat(),
        "telegram_id": None,
    }
    user.update(overrides)
    return user


@pytest.mark.asyncio
async def test_linking_code_rejects_when_update_fails():
    update = _update()
    user = _link_user()

    with patch(
        "bot.handlers.start.get_supabase_client",
        return_value=_FakeSupabaseClient(user),
    ), patch(
        "bot.handlers.start.get_user_by_telegram_id",
        return_value=None,
    ), patch("bot.handlers.start.update_user", return_value=None) as update_user:
        await _handle_linking_code(update, telegram_id=1690210103, linking_code="868509")

    update_user.assert_called_once()
    reply = update.message.reply_text.await_args.args[0]
    assert "Nie udało się połączyć konta Telegram" in reply
    assert reply != _WELCOME_MESSAGE


@pytest.mark.asyncio
async def test_linking_code_sends_welcome_only_after_successful_update():
    update = _update()
    user = _link_user()
    updated_user = {**user, "telegram_id": 1690210103}

    with patch(
        "bot.handlers.start.get_supabase_client",
        return_value=_FakeSupabaseClient(user),
    ), patch(
        "bot.handlers.start.get_user_by_telegram_id",
        return_value=None,
    ), patch("bot.handlers.start.update_user", return_value=updated_user) as update_user:
        await _handle_linking_code(update, telegram_id=1690210103, linking_code="868509")

    update_user.assert_called_once_with(
        "user-123",
        {
            "telegram_id": 1690210103,
            "telegram_link_code": None,
            "telegram_link_code_expires": None,
        },
    )
    update.message.reply_text.assert_awaited_once_with(_WELCOME_MESSAGE)


@pytest.mark.asyncio
async def test_linking_code_rejects_existing_telegram_link():
    update = _update()
    user = _link_user()
    existing_user = {"id": "other-user", "telegram_id": 1690210103}

    with patch(
        "bot.handlers.start.get_supabase_client",
        return_value=_FakeSupabaseClient(user),
    ), patch(
        "bot.handlers.start.get_user_by_telegram_id",
        return_value=existing_user,
    ), patch("bot.handlers.start.update_user") as update_user:
        await _handle_linking_code(update, telegram_id=1690210103, linking_code="868509")

    update_user.assert_not_called()
    reply = update.message.reply_text.await_args.args[0]
    assert "już połączone z innym użytkownikiem" in reply
