"""Unit tests for shared/formatting.py — pure Python, no mocking needed."""

from shared.formatting import (
    escape_markdown_v2,
    format_client_card,
    format_pipeline_stats,
    format_error,
    format_meeting,
    format_confirmation,
    format_edit_comparison,
)


# ── escape_markdown_v2 ────────────────────────────────────────────────────────


def test_escape_markdown_v2_escapes_underscore():
    result = escape_markdown_v2("test_name")
    assert "\\_ " in result or "\\_" in result


def test_escape_markdown_v2_escapes_dot():
    result = escape_markdown_v2("3.14")
    assert "3\\.14" == result


def test_escape_markdown_v2_escapes_parentheses():
    result = escape_markdown_v2("(test)")
    assert "\\(test\\)" == result


def test_escape_markdown_v2_no_change_on_plain_text():
    result = escape_markdown_v2("hello world")
    assert result == "hello world"


# ── format_client_card ────────────────────────────────────────────────────────


def test_format_client_card_contains_name():
    client = {"Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa", "Telefon": "600100200"}
    result = format_client_card(client)
    assert "Jan Kowalski" in result


def test_format_client_card_contains_phone():
    client = {"Imię i nazwisko": "Jan", "Telefon": "600100200"}
    result = format_client_card(client)
    assert "600100200" in result


def test_format_client_card_contains_city():
    client = {"Imię i nazwisko": "Jan", "Miasto": "Kraków"}
    result = format_client_card(client)
    assert "Kraków" in result or "Krak" in result


def test_format_client_card_skips_empty_fields():
    client = {"Imię i nazwisko": "Jan", "Telefon": "", "Email": ""}
    result = format_client_card(client)
    assert "Telefon" not in result
    assert "Email" not in result


# ── format_pipeline_stats ─────────────────────────────────────────────────────


def test_format_pipeline_stats_contains_all_statuses():
    stats = {"Nowy lead": 5, "Spotkanie umówione": 3, "Podpisane": 1}
    result = format_pipeline_stats(stats)
    assert "Nowy lead" in result
    assert "5" in result
    assert "Podpisane" in result


def test_format_pipeline_stats_empty():
    result = format_pipeline_stats({})
    assert "brak danych" in result


# ── format_error ──────────────────────────────────────────────────────────────


def test_format_error_google_down_is_polish():
    result = format_error("google_down")
    assert "Google" in result
    assert "NIE zostały zapisane" in result


def test_format_error_token_expired_mentions_autoryzacja():
    result = format_error("token_expired")
    assert "autoryzacj" in result.lower()


def test_format_error_rate_limit_mentions_limit():
    result = format_error("rate_limit")
    assert "limit" in result.lower()


def test_format_error_unknown_returns_generic_polish():
    result = format_error("unknown_xyz")
    assert "błąd" in result.lower()


# ── format_confirmation ───────────────────────────────────────────────────────


def test_format_confirmation_contains_details():
    result = format_confirmation("add_client", {"Imię i nazwisko": "Jan", "Miasto": "Gdańsk"})
    assert "Jan" in result
    assert "Dodać klienta?" in result
    assert "tak" not in result.lower()


# ── format_edit_comparison ────────────────────────────────────────────────────


def test_format_edit_comparison_shows_arrow():
    result = format_edit_comparison("Telefon", "600111222", "601234567")
    assert "600111222" in result
    assert "601234567" in result
    assert "→" in result
