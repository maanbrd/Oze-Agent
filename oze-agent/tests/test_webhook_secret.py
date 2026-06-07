"""Security: Telegram webhook secret_token wiring.

Verifies that in webhook (non-dev) mode the bot:
  * requires TELEGRAM_WEBHOOK_SECRET via validate_phase_a (fail-closed at startup),
  * passes secret_token to run_webhook so PTB validates the
    X-Telegram-Bot-Api-Secret-Token header on every incoming update,
  * never falls back to an unauthenticated webhook.
"""

import importlib
import sys
from unittest.mock import MagicMock


def _reload_config(monkeypatch, **env):
    for key, value in env.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)
    sys.modules.pop("bot.config", None)
    return importlib.import_module("bot.config").Config


def _set_required_phase_a_env(monkeypatch):
    """Set every Phase-A required var so only the var under test can be missing."""
    for key in (
        "TELEGRAM_BOT_TOKEN",
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "SUPABASE_SERVICE_KEY",
        "ENCRYPTION_KEY",
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "BASE_URL",
    ):
        monkeypatch.setenv(key, f"dummy-{key.lower()}")


def test_webhook_secret_listed_as_secret_env():
    from bot.config import SECRET_ENV_NAMES

    assert "TELEGRAM_WEBHOOK_SECRET" in SECRET_ENV_NAMES


def test_validate_phase_a_requires_webhook_secret_in_prod(monkeypatch):
    _set_required_phase_a_env(monkeypatch)
    Config = _reload_config(
        monkeypatch, ENV="production", TELEGRAM_WEBHOOK_SECRET=None
    )

    missing = Config.validate_phase_a()

    assert "TELEGRAM_WEBHOOK_SECRET" in missing


def test_validate_phase_a_passes_with_webhook_secret_in_prod(monkeypatch):
    _set_required_phase_a_env(monkeypatch)
    Config = _reload_config(
        monkeypatch, ENV="production", TELEGRAM_WEBHOOK_SECRET="s3cr3t-token_value"
    )

    assert Config.validate_phase_a() == []


def test_validate_phase_a_skips_webhook_secret_in_dev(monkeypatch):
    _set_required_phase_a_env(monkeypatch)
    Config = _reload_config(monkeypatch, ENV="dev", TELEGRAM_WEBHOOK_SECRET=None)

    assert "TELEGRAM_WEBHOOK_SECRET" not in Config.validate_phase_a()


def test_run_app_passes_secret_token_in_webhook_mode(monkeypatch):
    from bot import main as bot_main

    monkeypatch.setattr(bot_main.Config, "ENV", "production")
    monkeypatch.setattr(bot_main.Config, "BASE_URL", "https://agent-oze.pl")
    monkeypatch.setattr(
        bot_main.Config, "TELEGRAM_WEBHOOK_SECRET", "s3cr3t-token_value"
    )

    app = MagicMock()
    bot_main.run_app(app)

    app.run_webhook.assert_called_once()
    assert app.run_polling.call_count == 0
    kwargs = app.run_webhook.call_args.kwargs
    assert kwargs["secret_token"] == "s3cr3t-token_value"


def test_run_app_fails_closed_without_secret_in_webhook_mode(monkeypatch):
    from bot import main as bot_main

    monkeypatch.setattr(bot_main.Config, "ENV", "production")
    monkeypatch.setattr(bot_main.Config, "BASE_URL", "https://agent-oze.pl")
    monkeypatch.setattr(bot_main.Config, "TELEGRAM_WEBHOOK_SECRET", "")

    app = MagicMock()
    try:
        bot_main.run_app(app)
    except RuntimeError:
        pass
    else:
        raise AssertionError("run_app must fail closed when secret is missing")

    assert app.run_webhook.call_count == 0


def test_run_app_uses_polling_in_dev(monkeypatch):
    from bot import main as bot_main

    monkeypatch.setattr(bot_main.Config, "ENV", "dev")

    app = MagicMock()
    bot_main.run_app(app)

    app.run_polling.assert_called_once()
    assert app.run_webhook.call_count == 0
