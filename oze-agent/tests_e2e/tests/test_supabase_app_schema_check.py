"""Pure tests for the Supabase post-MVP app schema checker."""

from pathlib import Path

from tests_e2e import supabase_app_schema_check as check


class _Query:
    def __init__(self, *, data=None, error=None):
        self.data = data if data is not None else []
        self.error = error

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def execute(self):
        if self.error:
            raise self.error
        return type("Result", (), {"data": self.data})()


class _StorageBucketQuery:
    def __init__(self, data):
        self.data = data

    def list_buckets(self):
        return self.data


class _Client:
    def __init__(self, *, tables=None, bucket_names=None, user_rows=None):
        self.tables = tables or {}
        self.storage = _StorageBucketQuery(
            [type("Bucket", (), {"name": name})() for name in (bucket_names or [])]
        )
        self.user_rows = user_rows or []

    def table(self, name):
        if name == "users":
            return _Query(data=self.user_rows)
        return self.tables[name]


def test_detects_missing_postgrest_table_as_blocker():
    error = Exception(
        {
            "message": "Could not find the table 'public.offer_send_attempts' in the schema cache",
            "code": "PGRST205",
        }
    )
    client = _Client(tables={"offer_send_attempts": _Query(error=error)})

    result = check.check_table_visible(client, "offer_send_attempts")

    assert result.name == "table_offer_send_attempts_visible"
    assert result.tag == "blocker"
    assert "PGRST205" in result.detail


def test_schema_checker_requires_user_google_resources():
    user_rows = [{
        "google_sheets_id": "sheet-1",
        "google_calendar_id": "calendar-1",
        "google_drive_folder_id": "drive-1",
    }]
    client = _Client(user_rows=user_rows)

    checks = check.check_user_google_resources(client, telegram_id=123)

    assert [c.name for c in checks] == [
        "user_google_sheets_id_present",
        "user_google_calendar_id_present",
        "user_google_drive_folder_id_present",
    ]
    assert all(c.tag == "pass" for c in checks)


def test_schema_checker_can_resolve_admin_id_without_telethon_env(monkeypatch):
    args = check._parse_args([])
    monkeypatch.setenv("ADMIN_TELEGRAM_ID", "1690210103")
    monkeypatch.delenv("TELEGRAM_E2E_ADMIN_ID", raising=False)

    assert check.resolve_telegram_id(args) == 1690210103


def test_schema_patch_contains_reload_and_server_side_grants_only():
    patch = Path("supabase/patches/20260511_post_mvp_app_tables.sql")

    sql = patch.read_text(encoding="utf-8")

    assert "NOTIFY pgrst, 'reload schema';" in sql
    assert "GRANT ALL ON TABLE public.offer_send_attempts TO service_role;" in sql
    assert "GRANT ALL ON TABLE public.photo_upload_sessions TO service_role;" in sql
    assert "TO anon" not in sql
    assert "TO authenticated" not in sql
