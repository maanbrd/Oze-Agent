from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _admin_test_client(monkeypatch, *, email: str | None):
    from api.auth import AuthUser, get_current_auth_user
    from api.routes import admin
    from bot.config import Config

    monkeypatch.setattr(Config, "OWNER_ADMIN_EMAILS", "owner@example.com")
    monkeypatch.setattr(admin, "_get_user_profile", lambda auth_user: {"email": email})

    app = FastAPI()
    app.include_router(admin.router, prefix="/api")

    if email is not None:
        app.dependency_overrides[get_current_auth_user] = lambda: AuthUser(
            user_id="auth-owner",
            email=email,
            claims={},
        )

    return TestClient(app)


def test_admin_user_profiles_requires_owner(monkeypatch):
    client = _admin_test_client(monkeypatch, email="seller@example.com")

    response = client.get("/api/admin/user-profiles")

    assert response.status_code == 403


def test_admin_user_profiles_lists_profiles_with_user_metadata(monkeypatch):
    from api.routes import admin

    monkeypatch.setattr(
        admin,
        "_list_table_rows",
        lambda table_name, fields="*", page_size=1000: {
            "users": [
                {
                    "id": "user-1",
                    "name": "Jan Kowalski",
                    "email": "jan@example.pl",
                    "telegram_id": 123,
                    "subscription_status": "active",
                    "is_suspended": False,
                    "is_deleted": False,
                }
            ],
            "user_behavior_profiles": [
                {
                    "user_id": "user-1",
                    "telegram_id": 123,
                    "profile_markdown": "# Profil użytkownika\n\n## Podsumowanie\nJan często dyktuje.",
                    "insights_json": {"confidence": "high"},
                    "last_run_at": "2026-05-19T02:16:00+00:00",
                    "last_analyzed_message_at": "2026-05-18T20:00:00+00:00",
                    "status": "ok",
                    "error": None,
                    "analyzed_messages_count": 7,
                }
            ],
        }.get(table_name, []),
    )
    client = _admin_test_client(monkeypatch, email="owner@example.com")

    response = client.get("/api/admin/user-profiles")

    assert response.status_code == 200
    payload = response.json()
    assert payload["profiles"][0]["user_id"] == "user-1"
    assert payload["profiles"][0]["name"] == "Jan Kowalski"
    assert payload["profiles"][0]["profile_markdown"].startswith("# Profil użytkownika")
    assert payload["profiles"][0]["insights_json"]["confidence"] == "high"
    assert "conversation_history" not in str(payload)


def test_admin_user_profile_detail_returns_404_for_missing_profile(monkeypatch):
    from api.routes import admin

    monkeypatch.setattr(
        admin,
        "_list_table_rows",
        lambda table_name, fields="*", page_size=1000: {
            "users": [{"id": "user-1", "name": "Jan", "email": "jan@example.pl"}],
            "user_behavior_profiles": [],
        }.get(table_name, []),
    )
    client = _admin_test_client(monkeypatch, email="owner@example.com")

    response = client.get("/api/admin/user-profiles/user-1")

    assert response.status_code == 404
