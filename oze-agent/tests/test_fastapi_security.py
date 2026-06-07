def test_fastapi_cors_does_not_allow_wildcard_with_credentials(monkeypatch):
    from api.main import build_cors_origins
    from bot.config import Config

    monkeypatch.setattr(Config, "ENV", "production", raising=False)
    monkeypatch.setattr(Config, "DASHBOARD_URL", "https://app.agent-oze.pl", raising=False)

    origins = build_cors_origins()

    assert "*" not in origins
    assert "https://app.agent-oze.pl" in origins


def test_cors_methods_and_headers_are_explicit_not_wildcard():
    from api.main import (
        CORS_ALLOWED_HEADERS,
        CORS_ALLOWED_METHODS,
        CORS_EXPOSE_HEADERS,
    )

    assert "*" not in CORS_ALLOWED_METHODS
    assert "*" not in CORS_ALLOWED_HEADERS
    # Essentials the web app relies on must be present.
    assert "Authorization" in CORS_ALLOWED_HEADERS
    assert "Content-Type" in CORS_ALLOWED_HEADERS
    assert {"GET", "POST", "PATCH"}.issubset(set(CORS_ALLOWED_METHODS))
    # PDF download filename must be readable cross-origin.
    assert "Content-Disposition" in CORS_EXPOSE_HEADERS


def test_cors_preflight_reflects_allowlist_for_trusted_origin():
    """A real OPTIONS preflight echoes only our allowlist for a trusted origin
    and never reflects an untrusted one.

    Uses a throwaway app wired with the production CORS constants so it exercises
    real CORSMiddleware behaviour without reloading (and polluting) app modules.
    """
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.testclient import TestClient

    from api.main import (
        CORS_ALLOWED_HEADERS,
        CORS_ALLOWED_METHODS,
        CORS_EXPOSE_HEADERS,
    )

    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://app.agent-oze.pl"],
        allow_credentials=True,
        allow_methods=CORS_ALLOWED_METHODS,
        allow_headers=CORS_ALLOWED_HEADERS,
        expose_headers=CORS_EXPOSE_HEADERS,
    )

    @app.get("/ping")
    async def ping():
        return {"ok": True}

    client = TestClient(app)

    resp = client.options(
        "/ping",
        headers={
            "Origin": "https://app.agent-oze.pl",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization",
        },
    )
    assert resp.status_code in (200, 204)
    assert resp.headers["access-control-allow-origin"] == "https://app.agent-oze.pl"
    allow_methods = resp.headers.get("access-control-allow-methods", "")
    assert "*" not in allow_methods
    assert "GET" in allow_methods

    untrusted = client.options(
        "/ping",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert untrusted.headers.get("access-control-allow-origin") != "https://evil.example"
