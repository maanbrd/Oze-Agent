"""Unit tests for shared/database.py — all Supabase calls are mocked."""

from datetime import date, datetime, timedelta, timezone
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
    chain.gte.return_value = chain
    chain.order.return_value = chain
    chain.limit.return_value = chain
    chain.single.return_value = chain

    return chain


def _assert_utc_offset_timestamp(value: str) -> None:
    parsed = datetime.fromisoformat(value)
    assert parsed.tzinfo is not None
    assert parsed.utcoffset() == timedelta(0)


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


def test_get_user_by_id_uses_request_cache_within_context():
    user = {"id": "user-1", "telegram_id": 123, "name": "Jan"}
    client = _make_client(data=user)

    with patch("shared.database.get_supabase_client", return_value=client):
        from shared.database import get_user_by_id
        from shared.request_context import request_context

        with request_context():
            assert get_user_by_id("user-1") == user
            assert get_user_by_id("user-1") == user

    assert client.execute.call_count == 1


def test_update_user_refreshes_cached_user_rows():
    before = {"id": "user-1", "telegram_id": 123, "name": "Jan"}
    after = {"id": "user-1", "telegram_id": 123, "name": "Jan Updated"}
    first = MagicMock()
    first.data = before
    second = MagicMock()
    second.data = [after]

    client = _make_client()
    client.execute.side_effect = [first, second]

    with patch("shared.database.get_supabase_client", return_value=client):
        from shared.database import get_user_by_id, update_user
        from shared.request_context import request_context

        with request_context():
            assert get_user_by_id("user-1") == before
            assert update_user("user-1", {"name": "Jan Updated"}) == after
            assert get_user_by_id("user-1") == after

    assert client.execute.call_count == 2


def test_update_user_sets_timezone_aware_updated_at():
    after = {"id": "user-1", "telegram_id": 123, "name": "Jan Updated"}
    client = _make_client(data=[after])

    with patch("shared.database.get_supabase_client", return_value=client):
        from shared.database import update_user

        update_user("user-1", {"name": "Jan Updated"})

    payload = client.update.call_args.args[0]
    _assert_utc_offset_timestamp(payload["updated_at"])


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
    with patch("shared.database.get_supabase_client", return_value=_make_client(data=[])):
        from shared.database import get_daily_interaction_count
        result = get_daily_interaction_count(123, date.today())
    assert result == 0


def test_get_daily_interaction_count_existing_row():
    rows = [{"count": 5, "borrowed_from_tomorrow": 2}]
    with patch("shared.database.get_supabase_client", return_value=_make_client(data=rows)):
        from shared.database import get_daily_interaction_count
        result = get_daily_interaction_count(123, date.today())
    assert result == 7


# ── increment_daily_interaction_count ─────────────────────────────────────────


def test_increment_daily_interaction_count_inserts_when_no_row():
    client = _make_client(data=[])
    with patch("shared.database.get_supabase_client", return_value=client):
        from shared.database import increment_daily_interaction_count
        result = increment_daily_interaction_count(123, date.today())
    assert result == 1
    insert_calls = [c for c in client.insert.call_args_list]
    assert len(insert_calls) == 1
    payload = insert_calls[0].args[0]
    assert payload["telegram_id"] == 123
    assert payload["date"] == date.today().isoformat()
    assert payload["count"] == 1
    client.update.assert_not_called()


def test_increment_daily_interaction_count_updates_existing_row():
    client = _make_client(data=[{"count": 4}])
    with patch("shared.database.get_supabase_client", return_value=client):
        from shared.database import increment_daily_interaction_count
        result = increment_daily_interaction_count(123, date.today())
    assert result == 5
    client.update.assert_called_once_with({"count": 5})
    client.insert.assert_not_called()


def test_increment_daily_interaction_count_returns_zero_on_error():
    with patch(
        "shared.database.get_supabase_client",
        return_value=_make_client(raises=True),
    ):
        from shared.database import increment_daily_interaction_count
        result = increment_daily_interaction_count(123, date.today())
    assert result == 0


# ── get_conversation_history ──────────────────────────────────────────────────


def test_get_conversation_history_no_since_skips_filter():
    rows = [{"role": "user", "content": "hi", "message_type": "text", "created_at": "2026-04-15T10:00:00+00:00"}]
    client = _make_client(data=rows)
    with patch("shared.database.get_supabase_client", return_value=client):
        from shared.database import get_conversation_history
        result = get_conversation_history(123, limit=5)
    assert result == rows
    client.gte.assert_not_called()


def test_get_conversation_history_with_since_applies_gte():
    client = _make_client(data=[])
    with patch("shared.database.get_supabase_client", return_value=client):
        from shared.database import get_conversation_history
        get_conversation_history(123, limit=5, since=timedelta(minutes=30))

    assert client.gte.call_count == 1
    column, value = client.gte.call_args.args
    assert column == "created_at"
    parsed = datetime.fromisoformat(value)
    assert parsed.tzinfo is not None
    expected = datetime.now(tz=timezone.utc) - timedelta(minutes=30)
    assert abs(parsed - expected) < timedelta(seconds=5)


# ── pending flows ─────────────────────────────────────────────────────────────


def test_save_pending_flow_sets_timezone_aware_updated_at():
    client = _make_client(data=[])

    with patch("shared.database.get_supabase_client", return_value=client):
        from shared.database import save_pending_flow

        save_pending_flow(123, "add_client", {"name": "Jan"})

    payload = client.upsert.call_args.args[0]
    _assert_utc_offset_timestamp(payload["updated_at"])


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


def test_save_active_photo_session_sets_timezone_aware_updated_at():
    client = _make_client(data=[])

    with patch("shared.database.get_supabase_client", return_value=client):
        from shared.database import save_active_photo_session

        save_active_photo_session(
            123,
            "user-1",
            7,
            "folder-1",
            "https://drive.google.com/drive/folders/folder-1",
            "Jan Kowalski, Warszawa",
            datetime.now(timezone.utc),
        )

    payload = client.upsert.call_args.args[0]
    _assert_utc_offset_timestamp(payload["updated_at"])


def test_update_pending_followup_sets_timezone_aware_asked_at():
    client = _make_client(data=[])

    with patch("shared.database.get_supabase_client", return_value=client):
        from shared.database import update_pending_followup

        update_pending_followup("followup-1", "asked")

    payload = client.update.call_args.args[0]
    _assert_utc_offset_timestamp(payload["asked_at"])
