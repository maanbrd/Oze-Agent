from types import SimpleNamespace

from fastapi.testclient import TestClient


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
