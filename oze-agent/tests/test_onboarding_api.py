import asyncio
from types import SimpleNamespace

import pytest


class _FakeQuery:
    def __init__(self, rows):
        self.rows = rows
        self.updated = None

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def update(self, data):
        self.updated = data
        for row in self.rows:
            row.update(data)
        return self

    def execute(self):
        return SimpleNamespace(data=self.rows)


class _FakeSupabase:
    def __init__(self, rows):
        self.rows = rows
        self.last_query = None

    def table(self, name):
        assert name == "users"
        self.last_query = _FakeQuery(self.rows)
        return self.last_query


@pytest.mark.asyncio
async def test_onboarding_status_next_step_payment(monkeypatch):
    from api.auth import AuthUser
    from api.routes import onboarding

    fake = _FakeSupabase(
        [
            {
                "id": "user-1",
                "auth_user_id": "auth-1",
                "email": "jan@example.pl",
                "name": "Jan",
                "phone": None,
                "subscription_status": "pending_payment",
                "activation_paid": False,
                "google_access_token": None,
                "google_refresh_token": None,
                "google_sheets_id": None,
                "google_calendar_id": None,
                "google_drive_folder_id": None,
                "telegram_id": None,
                "telegram_link_code": None,
                "telegram_link_code_expires": None,
                "onboarding_completed": False,
            }
        ]
    )
    monkeypatch.setattr(onboarding, "get_supabase_client", lambda: fake)

    result = await onboarding.get_onboarding_status(
        AuthUser(user_id="auth-1", email="jan@example.pl", claims={})
    )

    assert result["nextStep"] == "/onboarding/platnosc"
    assert result["steps"]["payment"] is False
    assert result["steps"]["google"] is False
    assert result["profile"]["id"] == "user-1"


@pytest.mark.asyncio
async def test_update_account_allows_only_system_fields(monkeypatch):
    from api.auth import AuthUser
    from api.routes import onboarding

    fake = _FakeSupabase(
        [
            {
                "id": "user-1",
                "auth_user_id": "auth-1",
                "email": "jan@example.pl",
                "name": "Jan",
                "phone": None,
            }
        ]
    )
    monkeypatch.setattr(onboarding, "get_supabase_client", lambda: fake)

    result = await onboarding.update_account(
        {"name": "Jan Test", "phone": "600100200", "google_sheets_id": "blocked"},
        AuthUser(user_id="auth-1", email="jan@example.pl", claims={}),
    )

    assert result["profile"]["name"] == "Jan Test"
    assert result["profile"]["phone"] == "600100200"
    assert "google_sheets_id" not in fake.last_query.updated


@pytest.mark.asyncio
async def test_google_oauth_url_uses_authenticated_user(monkeypatch):
    from api.auth import AuthUser
    from api.routes import onboarding

    fake = _FakeSupabase(
        [
            {
                "id": "user-1",
                "auth_user_id": "auth-1",
                "email": "jan@example.pl",
                "subscription_status": "active",
                "activation_paid": True,
            }
        ]
    )
    monkeypatch.setattr(onboarding, "get_supabase_client", lambda: fake)
    captured: dict[str, str | None] = {}

    def fake_build_oauth_url(user_id: str, return_url: str | None = None) -> str:
        captured["user_id"] = user_id
        captured["return_url"] = return_url
        return f"https://google.test?user={user_id}"

    monkeypatch.setattr(onboarding, "build_oauth_url", fake_build_oauth_url)

    result = await onboarding.start_google_oauth(
        {"returnUrl": "https://app.example/onboarding/google/sukces"},
        AuthUser(user_id="auth-1", email="jan@example.pl", claims={})
    )

    assert result == {"url": "https://google.test?user=user-1"}
    assert captured == {
        "user_id": "user-1",
        "return_url": "https://app.example/onboarding/google/sukces",
    }
    assert "auth-1" not in result["url"]


def test_oauth_state_roundtrip():
    from shared.google_auth import build_oauth_state, parse_oauth_state

    state = build_oauth_state("user-1")

    assert parse_oauth_state(state)["user_id"] == "user-1"


@pytest.mark.asyncio
async def test_create_google_resources_only_creates_missing(monkeypatch):
    from api.auth import AuthUser
    from api.routes import onboarding

    fake = _FakeSupabase(
        [
            {
                "id": "user-1",
                "auth_user_id": "auth-1",
                "email": "jan@example.pl",
                "name": "Jan Test",
                "subscription_status": "active",
                "activation_paid": True,
                "google_refresh_token": "encrypted",
                "google_sheets_id": "existing-sheet",
                "google_sheets_name": "Existing Sheet",
                "google_calendar_id": None,
                "google_calendar_name": None,
                "google_drive_folder_id": None,
            }
        ]
    )
    monkeypatch.setattr(onboarding, "get_supabase_client", lambda: fake)
    monkeypatch.setattr(onboarding, "create_spreadsheet", pytest.fail, raising=False)
    monkeypatch.setattr(
        onboarding,
        "create_calendar",
        lambda user_id, name: "calendar-1",
        raising=False,
    )
    monkeypatch.setattr(
        onboarding,
        "create_root_folder",
        lambda user_id: "drive-1",
        raising=False,
    )

    result = await onboarding.create_google_resources(
        {"calendarName": "Agent-OZE Calendar"},
        AuthUser(user_id="auth-1", email="jan@example.pl", claims={}),
    )

    assert result["resources"]["sheetsId"] == "existing-sheet"
    assert result["resources"]["calendarId"] == "calendar-1"
    assert result["resources"]["driveFolderId"] == "drive-1"
    assert fake.rows[0]["google_calendar_id"] == "calendar-1"
    assert fake.rows[0]["google_drive_folder_id"] == "drive-1"


@pytest.mark.asyncio
async def test_create_google_resources_rechecks_user_between_resource_steps(monkeypatch):
    from api.auth import AuthUser
    from api.routes import onboarding

    fake = _FakeSupabase(
        [
            {
                "id": "user-1",
                "auth_user_id": "auth-1",
                "email": "jan@example.pl",
                "name": "Jan Test",
                "subscription_status": "active",
                "activation_paid": True,
                "google_refresh_token": "encrypted",
                "google_sheets_id": None,
                "google_sheets_name": None,
                "google_calendar_id": None,
                "google_calendar_name": None,
                "google_drive_folder_id": "existing-drive",
            }
        ]
    )
    monkeypatch.setattr(onboarding, "get_supabase_client", lambda: fake)

    async def create_sheet(_user_id, _name):
        fake.rows[0]["google_calendar_id"] = "calendar-from-other-request"
        fake.rows[0]["google_calendar_name"] = "Existing Calendar"
        return "sheet-1"

    monkeypatch.setattr(onboarding, "create_spreadsheet", create_sheet)
    monkeypatch.setattr(onboarding, "create_calendar", pytest.fail)
    monkeypatch.setattr(onboarding, "create_root_folder", pytest.fail)

    result = await onboarding.create_google_resources(
        {"sheetsName": "Agent-OZE CRM", "calendarName": "Agent-OZE Calendar"},
        AuthUser(user_id="auth-1", email="jan@example.pl", claims={}),
    )

    assert result["resources"]["sheetsId"] == "sheet-1"
    assert result["resources"]["calendarId"] == "calendar-from-other-request"
    assert result["resources"]["driveFolderId"] == "existing-drive"


@pytest.mark.asyncio
async def test_create_google_resources_serializes_concurrent_requests(monkeypatch):
    from api.auth import AuthUser
    from api.routes import onboarding

    fake = _FakeSupabase(
        [
            {
                "id": "user-1",
                "auth_user_id": "auth-1",
                "email": "jan@example.pl",
                "name": "Jan Test",
                "subscription_status": "active",
                "activation_paid": True,
                "google_refresh_token": "encrypted",
                "google_sheets_id": None,
                "google_sheets_name": None,
                "google_calendar_id": None,
                "google_calendar_name": None,
                "google_drive_folder_id": None,
            }
        ]
    )
    monkeypatch.setattr(onboarding, "get_supabase_client", lambda: fake)
    calls = {"sheets": 0, "calendar": 0, "drive": 0}

    async def create_sheet(_user_id, _name):
        calls["sheets"] += 1
        await asyncio.sleep(0.01)
        return "sheet-1"

    async def create_cal(_user_id, _name):
        calls["calendar"] += 1
        await asyncio.sleep(0.01)
        return "calendar-1"

    async def create_drive(_user_id):
        calls["drive"] += 1
        await asyncio.sleep(0.01)
        return "drive-1"

    monkeypatch.setattr(onboarding, "create_spreadsheet", create_sheet)
    monkeypatch.setattr(onboarding, "create_calendar", create_cal)
    monkeypatch.setattr(onboarding, "create_root_folder", create_drive)

    results = await asyncio.gather(
        onboarding.create_google_resources(
            {"sheetsName": "Agent-OZE CRM", "calendarName": "Agent-OZE Calendar"},
            AuthUser(user_id="auth-1", email="jan@example.pl", claims={}),
        ),
        onboarding.create_google_resources(
            {"sheetsName": "Agent-OZE CRM", "calendarName": "Agent-OZE Calendar"},
            AuthUser(user_id="auth-1", email="jan@example.pl", claims={}),
        ),
    )

    assert calls == {"sheets": 1, "calendar": 1, "drive": 1}
    assert [result["resources"] for result in results] == [
        {"sheetsId": "sheet-1", "calendarId": "calendar-1", "driveFolderId": "drive-1"},
        {"sheetsId": "sheet-1", "calendarId": "calendar-1", "driveFolderId": "drive-1"},
    ]


@pytest.mark.asyncio
async def test_create_google_resources_persists_partial_success_before_later_failure(monkeypatch):
    from fastapi import HTTPException
    from api.auth import AuthUser
    from api.routes import onboarding

    fake = _FakeSupabase(
        [
            {
                "id": "user-1",
                "auth_user_id": "auth-1",
                "email": "jan@example.pl",
                "name": "Jan Test",
                "subscription_status": "active",
                "activation_paid": True,
                "google_refresh_token": "encrypted",
                "google_sheets_id": "existing-sheet",
                "google_calendar_id": None,
                "google_drive_folder_id": None,
            }
        ]
    )
    monkeypatch.setattr(onboarding, "get_supabase_client", lambda: fake)
    monkeypatch.setattr(onboarding, "create_calendar", lambda user_id, name: "calendar-1")
    monkeypatch.setattr(onboarding, "create_root_folder", lambda user_id: None)

    with pytest.raises(HTTPException):
        await onboarding.create_google_resources(
            {"calendarName": "Agent-OZE Calendar"},
            AuthUser(user_id="auth-1", email="jan@example.pl", claims={}),
        )

    assert fake.rows[0]["google_calendar_id"] == "calendar-1"


@pytest.mark.asyncio
async def test_generate_telegram_code_sets_expiry(monkeypatch):
    from api.auth import AuthUser
    from api.routes import onboarding

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
    monkeypatch.setattr(onboarding, "get_supabase_client", lambda: fake)
    monkeypatch.setattr(onboarding.secrets, "randbelow", lambda upper: 12345)

    result = await onboarding.generate_telegram_code(
        AuthUser(user_id="auth-1", email="jan@example.pl", claims={})
    )

    assert result["code"] == "112345"
    assert result["paired"] is False
    assert fake.last_query.updated["telegram_link_code"] == "112345"
    assert fake.last_query.updated["telegram_link_code_expires"] is not None


@pytest.mark.asyncio
async def test_telegram_status_completed_when_telegram_id_exists(monkeypatch):
    from api.auth import AuthUser
    from api.routes import onboarding

    fake = _FakeSupabase(
        [
            {
                "id": "user-1",
                "auth_user_id": "auth-1",
                "telegram_id": 123456,
                "telegram_link_code": None,
                "telegram_link_code_expires": None,
            }
        ]
    )
    monkeypatch.setattr(onboarding, "get_supabase_client", lambda: fake)

    result = await onboarding.get_telegram_status(
        AuthUser(user_id="auth-1", email="jan@example.pl", claims={})
    )

    assert result["paired"] is True
    assert result["telegramId"] == 123456
