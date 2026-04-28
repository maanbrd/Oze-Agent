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
    monkeypatch.setattr(
        onboarding.Config,
        "GOOGLE_OAUTH_STATE_SECRET",
        "state-secret",
        raising=False,
    )
    monkeypatch.setattr(
        onboarding,
        "build_oauth_url",
        lambda user_id, state=None: f"https://google.test?state={state}&user={user_id}",
        raising=False,
    )

    result = await onboarding.start_google_oauth(
        AuthUser(user_id="auth-1", email="jan@example.pl", claims={})
    )

    assert result["url"].startswith("https://google.test")
    assert "user=user-1" in result["url"]
    assert "auth-1" not in result["url"]


def test_oauth_state_roundtrip(monkeypatch):
    from api.routes import onboarding

    monkeypatch.setattr(
        onboarding.Config,
        "GOOGLE_OAUTH_STATE_SECRET",
        "state-secret",
        raising=False,
    )
    state = onboarding.encode_oauth_state("user-1")

    assert onboarding.decode_oauth_state(state) == "user-1"


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
    assert fake.last_query.updated["google_calendar_id"] == "calendar-1"
