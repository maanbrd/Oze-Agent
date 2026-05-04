"""Unit tests for bot/config.py."""

import logging


def test_warn_secret_whitespace_logs_redacted_warning(caplog, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-secret\u2028")

    from bot.config import Config

    with caplog.at_level(logging.WARNING, logger="bot.config"):
        Config.warn_secret_whitespace()

    assert "ANTHROPIC_API_KEY" in caplog.text
    assert "raw_len=10" in caplog.text
    assert "stripped_len=9" in caplog.text
    assert "sk-secret" not in caplog.text
