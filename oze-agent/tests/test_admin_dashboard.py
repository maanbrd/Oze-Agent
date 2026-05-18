from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _user(**overrides):
    base = {
        "id": "user-1",
        "auth_user_id": "auth-1",
        "name": "Łukasz Fathi",
        "email": "lukasz@example.com",
        "phone": "+48794757420",
        "telegram_id": 123,
        "subscription_status": "active",
        "subscription_plan": "monthly",
        "activation_paid": True,
        "onboarding_completed": True,
        "google_sheets_id": "sheet-1",
        "google_calendar_id": "cal-1",
        "google_drive_folder_id": "drive-1",
        "created_at": "2026-05-01T10:00:00+00:00",
        "updated_at": "2026-05-17T10:00:00+00:00",
        "is_suspended": False,
        "is_deleted": False,
    }
    base.update(overrides)
    return base


def test_owner_email_parser_is_case_insensitive():
    from shared.admin_dashboard import is_owner_admin_email, parse_owner_admin_emails

    raw = " lukaszfathioze@gmail.com, Owner@Example.COM "

    assert parse_owner_admin_emails(raw) == {
        "lukaszfathioze@gmail.com",
        "owner@example.com",
    }
    assert is_owner_admin_email("OWNER@example.com", raw) is True
    assert is_owner_admin_email("seller@example.com", raw) is False
    assert is_owner_admin_email(None, raw) is False


def test_owner_dashboard_aggregates_business_and_funnel_metrics():
    from shared.admin_dashboard import build_owner_dashboard_payload

    payload = build_owner_dashboard_payload(
        users=[
            _user(),
            _user(
                id="user-2",
                auth_user_id="auth-2",
                email="anna@example.com",
                telegram_id=456,
                subscription_status="pending_payment",
                onboarding_completed=False,
                google_sheets_id=None,
                google_calendar_id=None,
            ),
            _user(
                id="user-3",
                auth_user_id="auth-3",
                email="piotr@example.com",
                telegram_id=None,
                subscription_status="canceled",
            ),
        ],
        interactions=[
            {
                "telegram_id": 123,
                "cost_usd": 0.25,
                "created_at": "2026-05-17T10:00:00+00:00",
            },
            {
                "telegram_id": 456,
                "cost_usd": 0.15,
                "created_at": "2026-05-17T11:00:00+00:00",
            },
        ],
        payment_history=[],
        offers=[
            {
                "id": "offer-1",
                "user_id": "user-1",
                "product_type": "PV + Magazyn",
                "price_net_pln": 42000,
                "pv_power_kwp": 6.2,
                "storage_capacity_kwh": 10,
                "city": "Warszawa",
            }
        ],
        offer_attempts=[],
        contact_rows=[
            {
                "User ID": "user-1",
                "Miasto": "Warszawa",
                "Status": "Oferta wysłana",
            }
        ],
        calendar_rows=[],
        monthly_subscription_pln=399,
        owner_spreadsheet_id="sheet-admin",
        owner_calendar_id="calendar-admin",
    )

    assert payload["business"]["mrr_pln"] == 399
    assert payload["business"]["active_paid_accounts"] == 1
    assert payload["business"]["pending_payment_accounts"] == 1
    assert payload["business"]["pending_payment_pln"] == 399
    assert payload["business"]["canceled_accounts"] == 1
    assert payload["business"]["ai_cost_usd_month"] == 0.4
    assert payload["funnel"][0] == {"label": "Rejestracja", "count": 3, "conversion_pct": 100.0}
    assert payload["funnel"][-1]["label"] == "Pierwsza oferta"
    assert payload["funnel"][-1]["count"] == 1
    assert payload["oze"]["offers_total"] == 1
    assert payload["oze"]["popular_offer_types"][0]["label"] == "PV + Magazyn"
    assert payload["links"]["sheets_url"].endswith("/sheet-admin/edit")
    assert "conversation_history" not in str(payload)


def _admin_test_client(monkeypatch, *, email: str | None):
    from api.auth import AuthUser, get_current_auth_user
    from api.routes import admin
    from bot.config import Config

    monkeypatch.setattr(Config, "OWNER_ADMIN_EMAILS", "owner@example.com")
    monkeypatch.setattr(Config, "MONTHLY_SUBSCRIPTION_PLN", 399)
    monkeypatch.setattr(Config, "ADMIN_MIRROR_SPREADSHEET_ID", "sheet-admin")
    monkeypatch.setattr(Config, "ADMIN_MIRROR_CALENDAR_ID", "calendar-admin")
    monkeypatch.setattr(admin, "_list_table_rows", lambda table_name, fields="*": [])
    monkeypatch.setattr(admin, "_read_owner_mirror_rows", lambda tab_name: [])
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


def test_admin_dashboard_requires_bearer_token(monkeypatch):
    client = _admin_test_client(monkeypatch, email=None)

    response = client.get("/api/admin/dashboard")

    assert response.status_code == 401


def test_admin_dashboard_rejects_non_owner(monkeypatch):
    client = _admin_test_client(monkeypatch, email="seller@example.com")

    response = client.get("/api/admin/dashboard")

    assert response.status_code == 403


def test_admin_dashboard_accepts_owner_email(monkeypatch):
    client = _admin_test_client(monkeypatch, email="OWNER@example.com")

    response = client.get("/api/admin/dashboard")

    assert response.status_code == 200
    assert response.json()["business"]["mrr_pln"] == 0
