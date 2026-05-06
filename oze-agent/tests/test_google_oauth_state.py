from __future__ import annotations

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
