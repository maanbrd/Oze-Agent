"""Unit tests for bot/config.py."""

import importlib
import logging
import sys


def _reload_config(monkeypatch):
    monkeypatch.delenv("MONTHLY_SUBSCRIPTION_PLN", raising=False)
    sys.modules.pop("bot.config", None)
    return importlib.import_module("bot.config").Config


def test_monthly_subscription_default_matches_current_price(monkeypatch):
    Config = _reload_config(monkeypatch)

    assert Config.MONTHLY_SUBSCRIPTION_PLN == 399


def test_warn_secret_whitespace_logs_redacted_warning(caplog, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-secret\u2028")

    from bot.config import Config

    with caplog.at_level(logging.WARNING, logger="bot.config"):
        Config.warn_secret_whitespace()

    assert "ANTHROPIC_API_KEY" in caplog.text
    assert "raw_len=10" in caplog.text
    assert "stripped_len=9" in caplog.text
    assert "sk-secret" not in caplog.text
