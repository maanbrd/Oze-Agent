from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest


class _FakeQuery:
    def __init__(self, rows):
        self.rows = rows
        self.filters = []

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, key, value):
        self.filters.append((key, value))
        return self

    def limit(self, *_args, **_kwargs):
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


@pytest.fixture(autouse=True)
def _active_subscription_for_authenticated_route_tests(monkeypatch):
    from api import auth

    monkeypatch.setattr(
        auth,
        "get_supabase_client",
        lambda: _FakeSupabase([{"id": "owner-user", "subscription_status": "active"}]),
    )


def test_offers_routes_require_bearer_token():
    from api.main import app

    client = TestClient(app)

    response = client.get("/offers/templates")

    assert response.status_code == 401


def test_offers_routes_ignore_spoofed_user_id_and_use_authenticated_profile(monkeypatch):
    from api.main import app
    from api import auth
    from api.routes import offers

    captured = {}

    class FakeOfferRepository:
        def list_templates(self, user_id):
            captured["user_id"] = user_id
            return [{"id": "template-1", "user_id": user_id}]

    monkeypatch.setattr(
        auth,
        "_decode_supabase_jwt",
        lambda token: {
            "sub": "auth-owner",
            "email": "owner@example.pl",
        },
    )
    monkeypatch.setattr(
        offers,
        "get_supabase_client",
        lambda: _FakeSupabase([{"id": "owner-user", "auth_user_id": "auth-owner"}]),
        raising=False,
    )
    monkeypatch.setattr(offers, "OfferRepository", FakeOfferRepository)

    client = TestClient(app)
    response = client.get(
        "/offers/templates?user_id=victim-user",
        headers={"Authorization": "Bearer signed-token"},
    )

    assert response.status_code == 200
    assert captured["user_id"] == "owner-user"
    assert response.json()["templates"][0]["user_id"] == "owner-user"


def test_offer_template_routes_reject_non_uuid_ids_before_repository_lookup(monkeypatch):
    from api.main import app
    from api import auth
    from api.routes import offers

    class FakeOfferRepository:
        def get_template(self, *_args, **_kwargs):
            raise AssertionError("repository should not receive a non-UUID template id")

    monkeypatch.setattr(
        auth,
        "_decode_supabase_jwt",
        lambda token: {
            "sub": "auth-owner",
            "email": "owner@example.pl",
        },
    )
    monkeypatch.setattr(
        offers,
        "get_supabase_client",
        lambda: _FakeSupabase([{"id": "owner-user", "auth_user_id": "auth-owner"}]),
        raising=False,
    )
    monkeypatch.setattr(offers, "OfferRepository", FakeOfferRepository)

    client = TestClient(app)
    response = client.patch(
        "/offers/templates/demo-ready-pv",
        headers={"Authorization": "Bearer signed-token"},
        json={"data": {"name": "PV"}},
    )

    assert response.status_code == 422


def test_create_template_rejects_invalid_ready_payload(monkeypatch):
    from api.main import app
    from api import auth
    from api.routes import offers

    class FakeOfferRepository:
        def create_template(self, *_args, **_kwargs):
            raise AssertionError("invalid ready templates must not be created")

    monkeypatch.setattr(
        auth,
        "_decode_supabase_jwt",
        lambda token: {
            "sub": "auth-owner",
            "email": "owner@example.pl",
        },
    )
    monkeypatch.setattr(
        offers,
        "get_supabase_client",
        lambda: _FakeSupabase([{"id": "owner-user", "auth_user_id": "auth-owner"}]),
        raising=False,
    )
    monkeypatch.setattr(offers, "OfferRepository", FakeOfferRepository)

    client = TestClient(app)
    response = client.post(
        "/offers/templates",
        headers={"Authorization": "Bearer signed-token"},
        json={"data": {"status": "ready", "name": "Niepełna oferta"}},
    )

    assert response.status_code == 400
    assert "Brakuje ceny netto zestawu." in str(response.json()["detail"])


def test_patch_template_rejects_draft_to_ready_without_required_fields(monkeypatch):
    from api.main import app
    from api import auth
    from api.routes import offers

    template_id = "11111111-1111-4111-8111-111111111111"

    class FakeOfferRepository:
        def get_template(self, user_id, incoming_template_id):
            assert user_id == "owner-user"
            assert incoming_template_id == template_id
            return {
                "id": template_id,
                "user_id": "owner-user",
                "status": "draft",
                "name": "Szkic",
                "product_type": "PV",
            }

        def update_template(self, *_args, **_kwargs):
            raise AssertionError("invalid draft must not be promoted to ready")

    monkeypatch.setattr(
        auth,
        "_decode_supabase_jwt",
        lambda token: {
            "sub": "auth-owner",
            "email": "owner@example.pl",
        },
    )
    monkeypatch.setattr(
        offers,
        "get_supabase_client",
        lambda: _FakeSupabase([{"id": "owner-user", "auth_user_id": "auth-owner"}]),
        raising=False,
    )
    monkeypatch.setattr(offers, "OfferRepository", FakeOfferRepository)

    client = TestClient(app)
    response = client.patch(
        f"/offers/templates/{template_id}",
        headers={"Authorization": "Bearer signed-token"},
        json={"data": {"status": "ready"}},
    )

    assert response.status_code == 400
    assert "Brakuje ceny netto zestawu." in str(response.json()["detail"])


def test_reorder_rejects_non_ready_template_ids(monkeypatch):
    from api.main import app
    from api import auth
    from api.routes import offers

    ready_id = "11111111-1111-4111-8111-111111111111"
    draft_id = "22222222-2222-4222-8222-222222222222"

    class FakeOfferRepository:
        def list_templates(self, user_id):
            assert user_id == "owner-user"
            return [
                {"id": ready_id, "status": "ready", "name": "Gotowa"},
                {"id": draft_id, "status": "draft", "name": "Szkic"},
            ]

        def reorder_ready(self, *_args, **_kwargs):
            raise AssertionError("reorder must not promote draft templates")

    monkeypatch.setattr(
        auth,
        "_decode_supabase_jwt",
        lambda token: {
            "sub": "auth-owner",
            "email": "owner@example.pl",
        },
    )
    monkeypatch.setattr(
        offers,
        "get_supabase_client",
        lambda: _FakeSupabase([{"id": "owner-user", "auth_user_id": "auth-owner"}]),
        raising=False,
    )
    monkeypatch.setattr(offers, "OfferRepository", FakeOfferRepository)

    client = TestClient(app)
    response = client.post(
        "/offers/templates/reorder",
        headers={"Authorization": "Bearer signed-token"},
        json={"ordered_template_ids": [ready_id, draft_id]},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Kolejność można zmieniać tylko dla gotowych ofert."
