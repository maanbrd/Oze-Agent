import logging
from datetime import datetime, timezone

from shared import database


class _MissingPhotoSessionsQuery:
    def upsert(self, *_args, **_kwargs):
        return self

    def select(self, *_args, **_kwargs):
        return self

    def delete(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def single(self, *_args, **_kwargs):
        return self

    def execute(self):
        raise Exception(
            {
                "message": "Could not find the table 'public.photo_upload_sessions' in the schema cache",
                "code": "PGRST205",
            }
        )


class _PostgrestLikeMissingPhotoSessionsQuery:
    def delete(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def execute(self):
        error = Exception(
            "{'message': \"Could not find the table "
            "'public.photo_upload_sessions' in the schema cache\", "
            "'code': 'PGRST205', 'hint': None, 'details': None}"
        )
        error._raw_error = {
            "message": "Could not find the table 'public.photo_upload_sessions' in the schema cache",
            "code": "PGRST205",
        }
        error.message = (
            "Could not find the table 'public.photo_upload_sessions' "
            "in the schema cache"
        )
        error.code = "PGRST205"
        raise error


class _MissingPhotoSessionsSupabase:
    def table(self, name):
        assert name == "photo_upload_sessions"
        return _MissingPhotoSessionsQuery()


class _PostgrestLikeMissingPhotoSessionsSupabase:
    def table(self, name):
        assert name == "photo_upload_sessions"
        return _PostgrestLikeMissingPhotoSessionsQuery()


def _missing_photo_sessions_logs(caplog):
    return [
        record
        for record in caplog.records
        if "photo_upload_sessions" in record.getMessage()
    ]


def test_get_active_photo_session_treats_missing_table_as_non_blocking(monkeypatch, caplog):
    monkeypatch.setattr(
        database,
        "get_supabase_client",
        lambda: _MissingPhotoSessionsSupabase(),
    )
    caplog.set_level(logging.DEBUG, logger="shared.database")

    assert database.get_active_photo_session(12345) is None

    assert all(
        record.levelno < logging.ERROR
        for record in _missing_photo_sessions_logs(caplog)
    )


def test_delete_active_photo_session_treats_missing_table_as_non_blocking(monkeypatch, caplog):
    monkeypatch.setattr(
        database,
        "get_supabase_client",
        lambda: _MissingPhotoSessionsSupabase(),
    )
    caplog.set_level(logging.DEBUG, logger="shared.database")

    database.delete_active_photo_session(12345)

    assert all(
        record.levelno < logging.ERROR
        for record in _missing_photo_sessions_logs(caplog)
    )


def test_delete_active_photo_session_handles_real_postgrest_api_error_shape(monkeypatch, caplog):
    monkeypatch.setattr(
        database,
        "get_supabase_client",
        lambda: _PostgrestLikeMissingPhotoSessionsSupabase(),
    )
    caplog.set_level(logging.DEBUG, logger="shared.database")

    database.delete_active_photo_session(12345)

    assert all(
        record.levelno < logging.ERROR
        for record in _missing_photo_sessions_logs(caplog)
    )


def test_save_active_photo_session_treats_missing_table_as_non_blocking(monkeypatch, caplog):
    monkeypatch.setattr(
        database,
        "get_supabase_client",
        lambda: _MissingPhotoSessionsSupabase(),
    )
    caplog.set_level(logging.DEBUG, logger="shared.database")

    database.save_active_photo_session(
        12345,
        "user-1",
        7,
        "folder-1",
        "https://drive.google.com/drive/folders/folder-1",
        "Jan Kowalski, Warszawa",
        datetime.now(timezone.utc),
    )

    assert all(
        record.levelno < logging.ERROR
        for record in _missing_photo_sessions_logs(caplog)
    )
