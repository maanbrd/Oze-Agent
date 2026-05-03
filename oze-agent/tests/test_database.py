"""Unit tests for shared/database.py — all Supabase calls are mocked."""

import json
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
    chain.neq.return_value = chain
    chain.order.return_value = chain
    chain.limit.return_value = chain
    chain.single.return_value = chain

    return chain


class _TableChain:
    def __init__(self, client, table_name):
        self.client = client
        self.table_name = table_name
        self.filters = []
        self.operation = None

    def select(self, *_args, **_kwargs):
        return self

    def insert(self, payload):
        self.client.insert_calls.append((self.table_name, payload))
        return self

    def upsert(self, payload):
        self.client.upsert_calls.append((self.table_name, payload))
        return self

    def delete(self):
        self.operation = "delete"
        return self

    def eq(self, column, value):
        self.filters.append(("eq", column, value))
        return self

    def neq(self, column, value):
        self.filters.append(("neq", column, value))
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def single(self):
        return self

    def execute(self):
        if self.table_name == "photo_upload_sessions" and self.client.raise_photo_table:
            raise Exception("photo_upload_sessions table missing")
        if self.operation == "delete":
            self.client.delete_calls.append((self.table_name, list(self.filters)))
        rows = self.client.table_data.get(self.table_name, [])
        result = MagicMock()
        result.data = rows
        return result


class _TableAwareClient:
    def __init__(self, *, raise_photo_table=True, table_data=None):
        self.raise_photo_table = raise_photo_table
        self.table_data = table_data or {}
        self.insert_calls = []
        self.upsert_calls = []
        self.delete_calls = []

    def table(self, table_name):
        return _TableChain(self, table_name)


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


def test_get_conversation_history_excludes_photo_session_metadata():
    client = _make_client(data=[])
    with patch("shared.database.get_supabase_client", return_value=client):
        from shared.database import get_conversation_history
        get_conversation_history(123, limit=5)

    client.neq.assert_called_once_with("message_type", "photo_upload_session")


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


# ── active photo sessions ────────────────────────────────────────────────────


def test_save_active_photo_session_falls_back_to_conversation_history_when_table_missing():
    client = _TableAwareClient(raise_photo_table=True)
    expires_at = datetime.now(tz=timezone.utc) + timedelta(minutes=15)

    with patch("shared.database.get_supabase_client", return_value=client):
        from shared.database import save_active_photo_session

        saved = save_active_photo_session(
            telegram_id=123,
            user_id="user-1",
            client_row=7,
            folder_id="folder-1",
            folder_link="https://drive.google.com/drive/folders/folder-1",
            display_label="Jan Kowalski, Warszawa",
            expires_at=expires_at,
        )

    assert saved is True
    assert client.insert_calls
    table_name, payload = client.insert_calls[-1]
    assert table_name == "conversation_history"
    assert payload["telegram_id"] == 123
    assert payload["role"] == "system"
    assert payload["message_type"] == "photo_upload_session"
    content = json.loads(payload["content"])
    assert content["client_row"] == 7
    assert content["folder_id"] == "folder-1"
    assert content["display_label"] == "Jan Kowalski, Warszawa"


def test_get_active_photo_session_falls_back_to_conversation_history_when_table_missing():
    expires_at = datetime.now(tz=timezone.utc) + timedelta(minutes=15)
    session_payload = {
        "telegram_id": 123,
        "user_id": "user-1",
        "client_row": 7,
        "folder_id": "folder-1",
        "folder_link": "https://drive.google.com/drive/folders/folder-1",
        "display_label": "Jan Kowalski, Warszawa",
        "expires_at": expires_at.isoformat(),
    }
    client = _TableAwareClient(
        raise_photo_table=True,
        table_data={
            "conversation_history": [
                {
                    "telegram_id": 123,
                    "role": "system",
                    "message_type": "photo_upload_session",
                    "content": json.dumps(session_payload),
                }
            ]
        },
    )

    with patch("shared.database.get_supabase_client", return_value=client):
        from shared.database import get_active_photo_session

        session = get_active_photo_session(123)

    assert session is not None
    assert session["client_row"] == 7
    assert session["folder_id"] == "folder-1"
    assert session["display_label"] == "Jan Kowalski, Warszawa"


def test_delete_active_photo_session_always_clears_fallback():
    client = _TableAwareClient(raise_photo_table=True)

    with patch("shared.database.get_supabase_client", return_value=client):
        from shared.database import delete_active_photo_session

        delete_active_photo_session(123)

    fallback_deletes = [
        filters for table_name, filters in client.delete_calls
        if table_name == "conversation_history"
    ]
    assert fallback_deletes
    assert ("eq", "telegram_id", 123) in fallback_deletes[-1]
    assert ("eq", "message_type", "photo_upload_session") in fallback_deletes[-1]


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
