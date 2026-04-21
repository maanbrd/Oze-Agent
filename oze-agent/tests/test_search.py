"""Unit tests for shared/search.py — pure Python, no mocking needed."""

from shared.search import (
    normalize_polish,
    levenshtein_distance,
    fuzzy_match,
    search_clients,
    find_best_match,
    detect_duplicate_candidates,
    detect_potential_duplicate,
)


# ── normalize_polish ──────────────────────────────────────────────────────────


def test_normalize_polish_removes_diacritics():
    assert normalize_polish("Łódź") == "lodz"
    assert normalize_polish("Kraków") == "krakow"
    assert normalize_polish("Józef Ślązak") == "jozef slazak"


def test_normalize_polish_lowercases():
    assert normalize_polish("WARSZAWA") == "warszawa"


# ── levenshtein_distance ──────────────────────────────────────────────────────


def test_levenshtein_identical():
    assert levenshtein_distance("abc", "abc") == 0


def test_levenshtein_one_insertion():
    assert levenshtein_distance("abc", "abcd") == 1


def test_levenshtein_one_substitution():
    assert levenshtein_distance("Kowalski", "Kowalsky") == 1


def test_levenshtein_empty_strings():
    assert levenshtein_distance("", "abc") == 3
    assert levenshtein_distance("abc", "") == 3


# ── fuzzy_match ───────────────────────────────────────────────────────────────


def test_fuzzy_match_typo():
    results = fuzzy_match("Kowalsky", ["Jan Kowalski", "Anna Nowak"])
    names = [r[0] for r in results]
    assert "Jan Kowalski" in names


def test_fuzzy_match_polish_diacritics():
    """'Lodz' should match 'Łódź' after normalization."""
    results = fuzzy_match("Lodz", ["Łódź", "Kraków"])
    names = [r[0] for r in results]
    assert "Łódź" in names


def test_fuzzy_match_no_match_beyond_threshold():
    results = fuzzy_match("Xyz123", ["Kowalski", "Nowak"], threshold=2)
    assert results == []


def test_fuzzy_match_sorted_by_distance():
    results = fuzzy_match("Nowak", ["Nowaka", "Nowakowski", "Kowalski"])
    if len(results) >= 2:
        assert results[0][1] <= results[1][1]


# ── search_clients ────────────────────────────────────────────────────────────


def test_search_clients_finds_by_name():
    clients = [
        {"Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa", "_row": 2},
        {"Imię i nazwisko": "Anna Nowak", "Miasto": "Kraków", "_row": 3},
    ]
    results = search_clients(clients, "Kowalsky")
    assert len(results) == 1
    assert results[0]["Imię i nazwisko"] == "Jan Kowalski"


def test_search_clients_finds_by_city():
    clients = [
        {"Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa", "_row": 2},
        {"Imię i nazwisko": "Anna Nowak", "Miasto": "Kraków", "_row": 3},
    ]
    results = search_clients(clients, "Krakow")
    assert any(c["Imię i nazwisko"] == "Anna Nowak" for c in results)


def test_search_clients_empty_query():
    clients = [{"Imię i nazwisko": "Jan", "_row": 2}]
    assert search_clients(clients, "") == []


def test_search_clients_empty_list():
    assert search_clients([], "Jan") == []


def test_search_clients_phone():
    clients = [
        {"Imię i nazwisko": "Jan", "Telefon": "600100200", "_row": 2},
        {"Imię i nazwisko": "Anna", "Telefon": "601200300", "_row": 3},
    ]
    results = search_clients(clients, "600100200")
    assert results[0]["Imię i nazwisko"] == "Jan"


# ── find_best_match ───────────────────────────────────────────────────────────


def test_find_best_match_returns_closest():
    result = find_best_match("Kowalsky", ["Kowalski", "Nowak", "Wiśniewski"])
    assert result == "Kowalski"


def test_find_best_match_returns_none_on_no_match():
    result = find_best_match("Xyz999abc", ["Kowalski", "Nowak"])
    assert result is None


# ── detect_potential_duplicate ────────────────────────────────────────────────


def test_detect_potential_duplicate_finds_typo():
    existing = [
        {"Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa", "_row": 2},
    ]
    result = detect_potential_duplicate("Jan Kowalsky", "Warszawa", existing)
    assert result is not None
    assert result["Imię i nazwisko"] == "Jan Kowalski"


def test_detect_potential_duplicate_different_city_still_matches():
    """Same full name in a different city is now flagged as a potential duplicate."""
    existing = [
        {"Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa", "_row": 2},
    ]
    result = detect_potential_duplicate("Jan Kowalski", "Kraków", existing)
    assert result is not None
    assert result["Imię i nazwisko"] == "Jan Kowalski"


def test_detect_potential_duplicate_no_match():
    existing = [{"Imię i nazwisko": "Anna Nowak", "Miasto": "Kraków", "_row": 2}]
    result = detect_potential_duplicate("Piotr Wiśniewski", "Gdańsk", existing)
    assert result is None


def test_detect_potential_duplicate_new_missing_city_matches():
    existing = [
        {"Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa", "_row": 2},
    ]
    result = detect_potential_duplicate("Jan Kowalski", "", existing)
    assert result is not None
    assert result["Imię i nazwisko"] == "Jan Kowalski"


def test_detect_potential_duplicate_existing_missing_city_matches():
    existing = [
        {"Imię i nazwisko": "Jan Kowalski", "Miasto": "", "_row": 2},
    ]
    result = detect_potential_duplicate("Jan Kowalski", "Warszawa", existing)
    assert result is not None
    assert result["Imię i nazwisko"] == "Jan Kowalski"


def test_detect_potential_duplicate_both_missing_city_matches():
    existing = [
        {"Imię i nazwisko": "Jan Kowalski", "Miasto": "", "_row": 2},
    ]
    result = detect_potential_duplicate("Jan Kowalski", "", existing)
    assert result is not None
    assert result["Imię i nazwisko"] == "Jan Kowalski"


def test_detect_potential_duplicate_first_name_only_no_match():
    """Single-token input like 'Jan' must not match 'Jan Kowalski' — guards
    against overmatching first-name-only entries."""
    existing = [
        {"Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa", "_row": 2},
    ]
    result = detect_potential_duplicate("Jan", "Warszawa", existing)
    assert result is None


def test_detect_potential_duplicate_prefers_same_city_over_name_only():
    """When multiple same-name rows exist, a same-city match must beat a
    name-only fallback even if the name-only row is listed first."""
    existing = [
        {"Imię i nazwisko": "Jan Kowalski", "Miasto": "Kraków", "_row": 2},
        {"Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa", "_row": 3},
    ]
    result = detect_potential_duplicate("Jan Kowalski", "Warszawa", existing)
    assert result is not None
    assert result["_row"] == 3


# ── detect_duplicate_candidates ───────────────────────────────────────────────


def test_detect_duplicate_candidates_empty_when_no_match():
    existing = [{"Imię i nazwisko": "Anna Nowak", "Miasto": "Kraków", "_row": 2}]
    assert detect_duplicate_candidates("Piotr Wiśniewski", "Gdańsk", existing) == []


def test_detect_duplicate_candidates_first_name_only_returns_empty():
    existing = [{"Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa", "_row": 2}]
    assert detect_duplicate_candidates("Jan", "Warszawa", existing) == []


def test_detect_duplicate_candidates_single_same_city():
    existing = [{"Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa", "_row": 2}]
    result = detect_duplicate_candidates("Jan Kowalski", "Warszawa", existing)
    assert len(result) == 1
    assert result[0]["_row"] == 2


def test_detect_duplicate_candidates_multi_same_name_no_city():
    existing = [
        {"Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa", "_row": 2},
        {"Imię i nazwisko": "Jan Kowalski", "Miasto": "Kraków", "_row": 3},
    ]
    result = detect_duplicate_candidates("Jan Kowalski", "", existing)
    assert len(result) == 2
    assert {c["_row"] for c in result} == {2, 3}


def test_detect_duplicate_candidates_city_narrows_to_same_city():
    existing = [
        {"Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa", "_row": 2},
        {"Imię i nazwisko": "Jan Kowalski", "Miasto": "Kraków", "_row": 3},
    ]
    result = detect_duplicate_candidates("Jan Kowalski", "Warszawa", existing)
    assert len(result) == 1
    assert result[0]["_row"] == 2


def test_detect_duplicate_candidates_city_without_match_returns_cross_city():
    """City provided but no same-city candidate — fall back to all name-only
    matches so the cross-city duplicate warning is still raised."""
    existing = [
        {"Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa", "_row": 2},
        {"Imię i nazwisko": "Jan Kowalski", "Miasto": "Kraków", "_row": 3},
    ]
    result = detect_duplicate_candidates("Jan Kowalski", "Gdańsk", existing)
    assert len(result) == 2
    assert {c["_row"] for c in result} == {2, 3}


def test_detect_duplicate_candidates_miejscowosc_fallback():
    """Rows using legacy `Miejscowość` column participate in same-city filter."""
    existing = [
        {"Imię i nazwisko": "Jan Kowalski", "Miejscowość": "Warszawa", "_row": 2},
        {"Imię i nazwisko": "Jan Kowalski", "Miasto": "Kraków", "_row": 3},
    ]
    result = detect_duplicate_candidates("Jan Kowalski", "Warszawa", existing)
    assert len(result) == 1
    assert result[0]["_row"] == 2
