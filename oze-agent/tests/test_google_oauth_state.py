from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

import pytest


def test_google_oauth_state_preserves_current_preview_return_url():
    from shared.google_auth import build_oauth_state, parse_oauth_state

    return_url = (
        "https://oze-agent-g6hvtgg4l-maanbrds-projects.vercel.app"
        "/onboarding/google/sukces"
    )

    state = build_oauth_state("user-1", return_url)
    parsed = parse_oauth_state(state)

    assert parsed["user_id"] == "user-1"
    assert parsed["return_url"] == return_url


def test_google_oauth_url_forces_consent_so_google_returns_refresh_token(monkeypatch):
    from bot.config import Config
    from shared.google_auth import build_oauth_url

    monkeypatch.setattr(Config, "GOOGLE_CLIENT_ID", "client-id")
    monkeypatch.setattr(
        Config,
        "GOOGLE_REDIRECT_URI",
        "https://api-staging-staging-7359.up.railway.app/auth/google/callback",
    )

    url = build_oauth_url("user-1")
    query = parse_qs(urlparse(url).query)

    assert query["access_type"] == ["offline"]
    assert query["prompt"] == ["consent"]


def test_google_oauth_state_rejects_untrusted_return_url():
    from shared.google_auth import build_oauth_state, parse_oauth_state

    state = build_oauth_state(
        "user-1",
        "https://evil.example.com/onboarding/google/sukces",
    )
    parsed = parse_oauth_state(state)

    assert parsed["user_id"] == "user-1"
    assert parsed["return_url"] is None


def test_google_oauth_state_keeps_legacy_plain_user_id():
    from shared.google_auth import parse_oauth_state

    parsed = parse_oauth_state("legacy-user-id")

    assert parsed == {"user_id": "legacy-user-id", "return_url": None}


@pytest.mark.asyncio
async def test_google_callback_redirects_to_state_return_url(monkeypatch):
    from api.routes import google_oauth

    return_url = (
        "https://oze-agent-g6hvtgg4l-maanbrds-projects.vercel.app"
        "/onboarding/google/sukces"
    )

    monkeypatch.setattr(
        google_oauth,
        "handle_oauth_callback",
        lambda code, state: {"id": "user-1", "_oauth_return_url": return_url},
    )

    response = await google_oauth.google_callback(code="code", state="state")

    assert response.status_code in {302, 307}
    assert response.headers["location"] == return_url


def test_store_google_tokens_rejects_missing_refresh_token(monkeypatch):
    from google.oauth2.credentials import Credentials
    from shared import google_auth

    update_calls: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        google_auth,
        "encrypt_token",
        lambda token: f"encrypted:{token}",
    )
    monkeypatch.setattr(
        google_auth,
        "update_user",
        lambda user_id, data: update_calls.append((user_id, data)),
    )

    credentials = Credentials(
        token="access-token",
        refresh_token=None,
        expiry=datetime(2026, 5, 6, tzinfo=timezone.utc),
    )

    assert google_auth.store_google_tokens("user-1", credentials) is False
    assert update_calls == []


def test_handle_oauth_callback_fails_when_tokens_are_not_stored(monkeypatch):
    from google.oauth2.credentials import Credentials
    from shared import google_auth

    class FakeFlow:
        credentials = Credentials(token="access-token", refresh_token=None)

        def fetch_token(self, code: str) -> None:
            assert code == "oauth-code"

    class FakeFlowFactory:
        @staticmethod
        def from_client_config(**kwargs):
            return FakeFlow()

    monkeypatch.setattr(google_auth, "Flow", FakeFlowFactory)
    monkeypatch.setattr(google_auth, "store_google_tokens", lambda user_id, credentials: False)
    monkeypatch.setattr(google_auth, "get_user_by_id", lambda user_id: {"id": user_id})

    assert google_auth.handle_oauth_callback("oauth-code", "user-1") is None


@pytest.mark.asyncio
async def test_onboarding_google_oauth_url_forwards_return_url(monkeypatch):
    from api.routes import onboarding

    return_url = (
        "https://oze-agent-m5wy4dpqs-maanbrds-projects.vercel.app"
        "/onboarding/google/sukces"
    )
    captured: dict[str, str | None] = {}

    monkeypatch.setattr(onboarding, "_get_user_for_auth", lambda auth_user: {"id": "user-1"})
    monkeypatch.setattr(onboarding, "_has_payment", lambda user: True)

    def fake_build_oauth_url(user_id: str, return_url: str | None = None) -> str:
        captured["user_id"] = user_id
        captured["return_url"] = return_url
        return "https://accounts.google.com/o/oauth2/auth"

    monkeypatch.setattr(onboarding, "build_oauth_url", fake_build_oauth_url)

    response = await onboarding.start_google_oauth(
        {"returnUrl": return_url},
        auth_user=object(),
    )

    assert response == {"url": "https://accounts.google.com/o/oauth2/auth"}
    assert captured == {"user_id": "user-1", "return_url": return_url}
