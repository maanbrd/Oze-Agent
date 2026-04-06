"""Unit tests for shared/database.py — all Supabase calls are mocked."""

from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest

# Patch Config before importing database so no real .env is required
with patch("bot.config.Config.SUPABASE_URL", "https://fake.supabase.co"), \
     patch("bot.config.Config.SUPABASE_SERVICE_KEY", "fake-service-key"):
    pass  # Config is a class with class-level attrs; patch individually in tests


def _make_client(data=None, raises=False):
    """Return a mock Supabase client whose table chain returns `data`."""
    mock_result = MagicMock()
    mock_result.data = data

    chain = MagicMock()
    if raises:
        chain.execute.side_effect = Exception("DB error")
    else:
        chain.execute.return_value = mock_result

    # Every chained method returns the same mock so .table().select().eq()... works
    chain.table.return_value = chain
    chain.select.return_value = chain
    chain.insert.return_value = chain
    chain.update.return_value = chain
    chain.upsert.return_value = chain
    chain.delete.return_value = chain
    chain.eq.return_value = chain
    chain.order.return_value = chain
    chain.limit.return_value = chain
    chain.single.return_value = chain

    return chain


# ── get_user_by_telegram_id ───────────────────────────────────────────────────


def test_get_user_by_telegram_id_found():
    user = {"id": "abc", "telegram_id": 123, "name": "Jan"}
    with patch("shared.database.get_supabase_client", return_value=_make_client(data=user)):
        from shared.database import get_user_by_telegram_id
        result = get_user_by_telegram_id(123)
    assert result == user


def test_get_user_by_telegram_id_not_found():
    with patch("shared.database.get_supabase_client", return_value=_make_client(data=None, raises=True)):
        from shared.database import get_user_by_telegram_id
        result = get_user_by_telegram_id(999)
    assert result is None


# ── create_user ───────────────────────────────────────────────────────────────


def test_create_user_returns_created_dict():
    created = {"id": "uuid-1", "name": "Anna", "email": "anna@test.pl"}
    client = _make_client(data=[created])
    with patch("shared.database.get_supabase_client", return_value=client):
        from shared.database import create_user
        result = create_user({"name": "Anna", "email": "anna@test.pl"})
    assert result == created


def test_create_user_returns_none_on_error():
    with patch("shared.database.get_supabase_client", return_value=_make_client(raises=True)):
        from shared.database import create_user
        result = create_user({"name": "Anna", "email": "anna@test.pl"})
    assert result is None


# ── log_interaction ───────────────────────────────────────────────────────────


def test_log_interaction_does_not_raise():
    client = _make_client(data=[])
    with patch("shared.database.get_supabase_client", return_value=client):
        from shared.database import log_interaction
        log_interaction(123, "text", "claude-haiku-4-5", 100, 200, 0.0003)


def test_log_interaction_does_not_raise_on_db_error():
    with patch("shared.database.get_supabase_client", return_value=_make_client(raises=True)):
        from shared.database import log_interaction
        log_interaction(123, "text", "claude-haiku-4-5", 100, 200, 0.0003)


# ── get_daily_interaction_count ───────────────────────────────────────────────


def test_get_daily_interaction_count_new_day_returns_zero():
    with patch("shared.database.get_supabase_client", return_value=_make_client(data=None, raises=True)):
        from shared.database import get_daily_interaction_count
        result = get_daily_interaction_count(123, date.today())
    assert result == 0


def test_get_daily_interaction_count_existing_row():
    row = {"count": 5, "borrowed_from_tomorrow": 2}
    with patch("shared.database.get_supabase_client", return_value=_make_client(data=row)):
        from shared.database import get_daily_interaction_count
        result = get_daily_interaction_count(123, date.today())
    assert result == 7


# ── pending flows ─────────────────────────────────────────────────────────────


def test_get_pending_flow_returns_none_when_not_found():
    with patch("shared.database.get_supabase_client", return_value=_make_client(data=None, raises=True)):
        from shared.database import get_pending_flow
        result = get_pending_flow(123)
    assert result is None


def test_get_pending_flow_returns_flow():
    flow = {"telegram_id": 123, "flow_type": "add_client", "flow_data": {}}
    with patch("shared.database.get_supabase_client", return_value=_make_client(data=flow)):
        from shared.database import get_pending_flow
        result = get_pending_flow(123)
    assert result == flow
