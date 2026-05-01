from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import pytest


def test_build_oauth_url_forces_refresh_token_consent(monkeypatch):
    from shared import google_auth

    monkeypatch.setattr(
        google_auth.Config,
        "GOOGLE_CLIENT_ID",
        "google-client-id",
        raising=False,
    )
    monkeypatch.setattr(
        google_auth.Config,
        "GOOGLE_REDIRECT_URI",
        "https://api.example.com/auth/google/callback",
        raising=False,
    )

    url = google_auth.build_oauth_url("user-1", state="signed-state")
    query = parse_qs(urlparse(url).query)

    assert query["access_type"] == ["offline"]
    assert query["prompt"] == ["consent"]
    assert query["state"] == ["signed-state"]


def test_store_google_tokens_rejects_missing_refresh_token(monkeypatch):
    from shared import google_auth

    monkeypatch.setattr(google_auth, "update_user", pytest.fail)

    with pytest.raises(ValueError, match="refresh token"):
        google_auth.store_google_tokens(
            "user-1",
            SimpleNamespace(token="access-token", refresh_token=None, expiry=None),
        )


def test_store_google_tokens_raises_when_database_update_fails(monkeypatch):
    from shared import google_auth

    monkeypatch.setattr(google_auth, "encrypt_token", lambda token: f"enc:{token}")
    monkeypatch.setattr(google_auth, "update_user", lambda _user_id, _data: None)

    with pytest.raises(RuntimeError, match="failed to persist"):
        google_auth.store_google_tokens(
            "user-1",
            SimpleNamespace(
                token="access-token",
                refresh_token="refresh-token",
                expiry=None,
            ),
        )

