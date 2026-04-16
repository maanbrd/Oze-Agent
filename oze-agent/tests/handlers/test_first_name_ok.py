"""Tests for safe client-name matching in handler flows."""

from bot.handlers.text import _first_name_ok


def test_single_word_query_always_true():
    assert _first_name_ok("Krzysztof", {"Imię i nazwisko": "Krzysztof Wojcik"})
    assert _first_name_ok("Krzysztof", {"Imię i nazwisko": "Anna Nowak"})


def test_multi_word_full_match():
    assert _first_name_ok("Jan Kowalski", {"Imię i nazwisko": "Jan Kowalski"})


def test_multi_word_wrong_surname_rejected():
    assert not _first_name_ok(
        "Krzysztof Krzysztofiński",
        {"Imię i nazwisko": "Krzysztof Wojcik"},
    )


def test_multi_word_typo_tolerated():
    assert _first_name_ok("Jan Kowalsky", {"Imię i nazwisko": "Jan Kowalski"})


def test_multi_word_with_city_matches_identity():
    assert _first_name_ok(
        "Jan Kowalski Warszawa",
        {"Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa"},
    )


def test_reverse_order_ok():
    assert _first_name_ok("Kowalski Jan", {"Imię i nazwisko": "Jan Kowalski"})


def test_polish_diacritics_normalized():
    assert _first_name_ok("Łukasz Żak", {"Imię i nazwisko": "Lukasz Zak"})


def test_short_tokens_skipped():
    assert _first_name_ok("Jan J. Kowalski", {"Imię i nazwisko": "Jan Kowalski"})


def test_empty_stored_name_true():
    assert _first_name_ok("Jan Kowalski", {"Imię i nazwisko": ""})


def test_similar_first_name_does_not_reuse_surname_token():
    assert not _first_name_ok(
        "Jurek Jurecki",
        {"Imię i nazwisko": "Zbigniew Jurecki"},
    )
