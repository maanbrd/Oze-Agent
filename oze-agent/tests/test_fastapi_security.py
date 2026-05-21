def test_fastapi_cors_does_not_allow_wildcard_with_credentials(monkeypatch):
    from api.main import build_cors_origins
    from bot.config import Config

    monkeypatch.setattr(Config, "ENV", "production", raising=False)
    monkeypatch.setattr(Config, "DASHBOARD_URL", "https://app.agent-oze.pl", raising=False)

    origins = build_cors_origins()

    assert "*" not in origins
    assert "https://app.agent-oze.pl" in origins
