"""Unit tests for shared/pending/store.py — legacy DB wrappers mocked."""

from datetime import datetime, timezone
from unittest.mock import patch

from shared.pending import (
    PendingFlow,
    PendingFlowType,
    delete,
    get,
    save,
)


def test_save_delegates_to_legacy_wrapper_with_value_string():
    flow = PendingFlow(
        telegram_id=123,
        flow_type=PendingFlowType.ADD_CLIENT,
        flow_data={"foo": "bar"},
    )
    with patch("shared.pending.store.save_pending_flow") as mock_save:
        save(flow)
    mock_save.assert_called_once_with(123, "add_client", {"foo": "bar"})


def test_get_returns_none_when_underlying_returns_none():
    with patch("shared.pending.store.get_pending_flow", return_value=None):
        result = get(123)
    assert result is None


def test_get_returns_typed_flow_for_known_mvp_type():
    row = {
        "telegram_id": 123,
        "flow_type": "add_note",
        "flow_data": {"row": 7, "note_text": "hi"},
        "created_at": "2026-04-15T10:00:00+00:00",
    }
    with patch("shared.pending.store.get_pending_flow", return_value=row):
        result = get(123)
    assert result is not None
    assert result.telegram_id == 123
    assert result.flow_type is PendingFlowType.ADD_NOTE
    assert result.flow_data == {"row": 7, "note_text": "hi"}
    assert result.created_at == datetime(2026, 4, 15, 10, 0, 0, tzinfo=timezone.utc)


def test_get_parses_supabase_z_suffix_timestamp():
    row = {
        "telegram_id": 1,
        "flow_type": "r7_prompt",
        "flow_data": {},
        "created_at": "2026-04-15T10:00:00Z",
    }
    with patch("shared.pending.store.get_pending_flow", return_value=row):
        result = get(1)
    assert result is not None
    assert result.created_at == datetime(2026, 4, 15, 10, 0, 0, tzinfo=timezone.utc)
    assert result.created_at.tzinfo is not None


def test_get_accepts_datetime_created_at():
    created_at = datetime(2026, 4, 15, 10, 0, 0, tzinfo=timezone.utc)
    row = {
        "telegram_id": 1,
        "flow_type": "r7_prompt",
        "flow_data": {},
        "created_at": created_at,
    }
    with patch("shared.pending.store.get_pending_flow", return_value=row):
        result = get(1)
    assert result is not None
    assert result.created_at == created_at


def test_get_handles_invalid_created_at():
    row = {
        "telegram_id": 1,
        "flow_type": "r7_prompt",
        "flow_data": {},
        "created_at": "not-a-date",
    }
    with patch("shared.pending.store.get_pending_flow", return_value=row):
        result = get(1)
    assert result is not None
    assert result.created_at is None


def test_get_returns_none_for_legacy_post_mvp_flow_type():
    row = {
        "telegram_id": 1,
        "flow_type": "assign_photo",
        "flow_data": {"photo_bytes": []},
        "created_at": "2026-04-15T10:00:00+00:00",
    }
    with patch("shared.pending.store.get_pending_flow", return_value=row) as raw_get, \
         patch("shared.pending.store.delete_pending_flow") as raw_delete:
        result = get(1)
    assert result is None
    raw_get.assert_called_once_with(1)
    raw_delete.assert_not_called()


def test_get_handles_missing_created_at():
    row = {
        "telegram_id": 1,
        "flow_type": "add_client",
        "flow_data": {},
    }
    with patch("shared.pending.store.get_pending_flow", return_value=row):
        result = get(1)
    assert result is not None
    assert result.created_at is None


def test_get_handles_null_flow_data():
    row = {
        "telegram_id": 1,
        "flow_type": "add_client",
        "flow_data": None,
        "created_at": None,
    }
    with patch("shared.pending.store.get_pending_flow", return_value=row):
        result = get(1)
    assert result is not None
    assert result.flow_data == {}


def test_delete_delegates_to_legacy_wrapper():
    with patch("shared.pending.store.delete_pending_flow") as mock_delete:
        delete(123)
    mock_delete.assert_called_once_with(123)
