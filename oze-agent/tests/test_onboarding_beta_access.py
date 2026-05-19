from __future__ import annotations

from datetime import datetime, timezone

import pytest


class _FakeResult:
    def __init__(self, data):
        self.data = data


class _FakeTable:
    def __init__(self, supabase, name: str):
        self.supabase = supabase
        self.name = name
        self._filters: list[tuple[str, object]] = []
        self._limit: int | None = None
        self._update_payload: dict | None = None

    def select(self, *_args, **_kwargs):
        return self

    def update(self, payload: dict):
        self._update_payload = payload
        return self

    def eq(self, key: str, value: object):
        self._filters.append((key, value))
        return self

    def limit(self, value: int):
        self._limit = value
        return self

    def execute(self):
        if self.name == "users":
            rows = self.supabase.users
        elif self.name == "beta_access_grants":
            rows = self.supabase.beta_access_grants
        else:
            rows = []

        for key, value in self._filters:
            rows = [row for row in rows if row.get(key) == value]

        if self._update_payload is not None:
            for row in rows:
                row.update(self._update_payload)

        if self._limit is not None:
            rows = rows[: self._limit]

        return _FakeResult(rows)


class _FakeSupabase:
    def __init__(
        self,
        *,
        users: list[dict],
        beta_access_grants: list[dict] | None = None,
    ):
        self.users = users
        self.beta_access_grants = beta_access_grants or []

    def table(self, name: str):
        return _FakeTable(self, name)


def _auth_user():
    from api.auth import AuthUser

    return AuthUser(user_id="auth-1", email="Jan@Example.pl", claims={})


def _user(**overrides):
    data = {
        "id": "user-1",
        "auth_user_id": "auth-1",
        "email": "Jan@Example.pl",
        "name": "Jan",
        "phone": None,
        "subscription_status": "pending_payment",
        "subscription_plan": None,
        "subscription_current_period_end": None,
        "activation_paid": False,
        "google_access_token": None,
        "google_refresh_token": None,
        "google_token_expiry": None,
        "google_sheets_id": None,
        "google_sheets_name": None,
        "google_calendar_id": None,
        "google_calendar_name": None,
        "google_drive_folder_id": None,
        "telegram_id": None,
        "telegram_link_code": None,
        "telegram_link_code_expires": None,
        "onboarding_completed": False,
    }
    data.update(overrides)
    return data


def _future_period_end() -> str:
    return datetime(2099, 1, 1, tzinfo=timezone.utc).isoformat()


def _grant(**overrides):
    data = {
        "id": "grant-1",
        "email": "jan@example.pl",
        "status": "active",
        "auth_user_id": None,
        "claimed_at": None,
        "revoked_at": None,
        "note": None,
    }
    data.update(overrides)
    return data


@pytest.mark.asyncio
async def test_unclaimed_beta_email_is_eligible_but_stays_on_payment(monkeypatch):
    from api.routes import onboarding

    fake = _FakeSupabase(users=[_user()], beta_access_grants=[_grant()])
    monkeypatch.setattr(onboarding, "get_supabase_client", lambda: fake)

    payload = await onboarding.get_onboarding_status(_auth_user())

    assert payload["nextStep"] == "/onboarding/platnosc"
    assert payload["steps"]["payment"] is False
    assert payload["access"] == {
        "active": False,
        "type": None,
        "betaEligible": True,
    }


@pytest.mark.asyncio
async def test_activate_beta_access_claims_grant_without_marking_payment(monkeypatch):
    from api.routes import onboarding

    now = datetime(2026, 5, 8, 12, 0, 0, tzinfo=timezone.utc)
    fake = _FakeSupabase(users=[_user()], beta_access_grants=[_grant()])

    class _FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return now if tz else now.replace(tzinfo=None)

    monkeypatch.setattr(onboarding, "get_supabase_client", lambda: fake)
    monkeypatch.setattr(onboarding, "datetime", _FrozenDatetime)

    payload = await onboarding.activate_beta_access(_auth_user())

    assert fake.beta_access_grants[0]["auth_user_id"] == "auth-1"
    assert fake.beta_access_grants[0]["claimed_at"] == now.isoformat()
    assert fake.users[0]["activation_paid"] is False
    assert fake.users[0]["subscription_status"] == "pending_payment"
    assert payload["nextStep"] == "/onboarding/google"
    assert payload["steps"]["payment"] is True
    assert payload["access"] == {
        "active": True,
        "type": "beta",
        "betaEligible": True,
    }


@pytest.mark.asyncio
async def test_claimed_beta_access_allows_google_oauth_without_payment(monkeypatch):
    from api.routes import onboarding

    fake = _FakeSupabase(
        users=[_user()],
        beta_access_grants=[_grant(auth_user_id="auth-1", claimed_at="2026-05-08T12:00:00+00:00")],
    )
    monkeypatch.setattr(onboarding, "get_supabase_client", lambda: fake)
    monkeypatch.setattr(
        onboarding,
        "build_oauth_url",
        lambda user_id, return_url=None: f"https://oauth.example/{user_id}?return={return_url}",
    )

    payload = await onboarding.start_google_oauth(
        {"returnUrl": "https://app.example/onboarding/google/sukces"},
        _auth_user(),
    )

    assert payload == {
        "url": "https://oauth.example/user-1?return=https://app.example/onboarding/google/sukces"
    }


@pytest.mark.asyncio
async def test_claimed_beta_access_allows_resource_creation_without_payment(monkeypatch):
    from api.routes import onboarding

    fake = _FakeSupabase(
        users=[_user(google_refresh_token="encrypted-token")],
        beta_access_grants=[_grant(auth_user_id="auth-1", claimed_at="2026-05-08T12:00:00+00:00")],
    )
    monkeypatch.setattr(onboarding, "get_supabase_client", lambda: fake)
    monkeypatch.setattr(onboarding, "create_spreadsheet", lambda *_args: "sheet-1")
    monkeypatch.setattr(onboarding, "create_calendar", lambda *_args: "calendar-1")
    monkeypatch.setattr(onboarding, "create_root_folder", lambda *_args: "drive-1")

    payload = await onboarding.create_google_resources({}, _auth_user())

    assert payload["resources"] == {
        "sheetsId": "sheet-1",
        "calendarId": "calendar-1",
        "driveFolderId": "drive-1",
    }
    assert payload["nextStep"] == "/onboarding/telegram"


@pytest.mark.asyncio
async def test_revoked_beta_access_does_not_unlock_payment_gate(monkeypatch):
    from fastapi import HTTPException
    from api.routes import onboarding

    fake = _FakeSupabase(
        users=[_user()],
        beta_access_grants=[_grant(status="revoked", auth_user_id="auth-1")],
    )
    monkeypatch.setattr(onboarding, "get_supabase_client", lambda: fake)

    payload = await onboarding.get_onboarding_status(_auth_user())

    assert payload["nextStep"] == "/onboarding/platnosc"
    assert payload["steps"]["payment"] is False
    assert payload["access"] == {
        "active": False,
        "type": None,
        "betaEligible": False,
    }
    with pytest.raises(HTTPException) as exc:
        await onboarding.start_google_oauth({}, _auth_user())
    assert exc.value.status_code == 402


@pytest.mark.asyncio
async def test_paid_access_wins_over_revoked_beta_grant(monkeypatch):
    from api.routes import onboarding

    fake = _FakeSupabase(
        users=[
            _user(
                subscription_status="active",
                activation_paid=True,
                stripe_livemode=True,
                subscription_current_period_end=_future_period_end(),
            )
        ],
        beta_access_grants=[_grant(status="revoked", auth_user_id="auth-1")],
    )
    monkeypatch.setattr(onboarding, "get_supabase_client", lambda: fake)

    payload = await onboarding.get_onboarding_status(_auth_user())

    assert payload["steps"]["payment"] is True
    assert payload["access"] == {
        "active": True,
        "type": "paid",
        "betaEligible": False,
    }
