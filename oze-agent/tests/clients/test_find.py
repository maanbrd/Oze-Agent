"""Unit tests for shared.clients.find."""

from unittest.mock import AsyncMock, patch

import pytest

from shared.clients import (
    FuzzySuggestion,
    lookup_client,
    suggest_fuzzy_client,
)


def _row(name: str, city: str = "", phone: str = "", row_num: int = 2) -> dict:
    return {
        "_row": row_num,
        "Imię i nazwisko": name,
        "Miasto": city,
        "Telefon": phone,
    }


def _patched_search_clients(return_value):
    """Patch the search_clients that find.lookup_client actually imports."""
    return patch(
        "shared.clients.find.search_clients",
        new=AsyncMock(return_value=return_value),
    )


def _patched_get_all_clients(return_value):
    return patch(
        "shared.clients.find.get_all_clients",
        new=AsyncMock(return_value=return_value),
    )


# ── name lookup ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unique_exact_match():
    rows = [_row("Jan Kowalski", "Warszawa")]
    with _patched_search_clients(rows):
        result = await lookup_client("u1", "Jan Kowalski")
    assert result.status == "unique"
    assert result.clients == rows
    assert result.is_phone_query is False


@pytest.mark.asyncio
async def test_unique_via_first_name_ok_middle_name():
    """Query 'Jan Kowalski' should match stored 'Jan Piotr Kowalski' via first_name_ok."""
    rows = [_row("Jan Piotr Kowalski", "Warszawa")]
    with _patched_search_clients(rows):
        result = await lookup_client("u1", "Jan Kowalski")
    assert result.status == "unique"


@pytest.mark.asyncio
async def test_multi_same_name_two_cities():
    rows = [
        _row("Jan Kowalski", "Warszawa", row_num=2),
        _row("Jan Kowalski", "Kraków", row_num=5),
    ]
    with _patched_search_clients(rows):
        result = await lookup_client("u1", "Jan Kowalski")
    assert result.status == "multi"
    assert len(result.clients) == 2


@pytest.mark.asyncio
async def test_not_found_zero_rows():
    with _patched_search_clients([]):
        result = await lookup_client("u1", "Piotr Wiśniewski")
    assert result.status == "not_found"
    assert result.clients == []


@pytest.mark.asyncio
async def test_regression_kowalsky_fuzzy_only_is_not_unique():
    """Codex runda 4 #1: single-token fuzzy-only must NOT become unique."""
    # search_clients returns 'Kowalski' for 'Kowalsky' via fuzzy
    rows = [_row("Kowalski", "Warszawa")]
    with _patched_search_clients(rows):
        result = await lookup_client("u1", "Kowalsky")
    assert result.status == "not_found"


@pytest.mark.asyncio
async def test_regression_kowal_substring_is_not_unique():
    """'Kowal' is a substring of 'Kowalski' but not a standalone token — fuzzy-only."""
    rows = [_row("Kowalski", "Warszawa")]
    with _patched_search_clients(rows):
        result = await lookup_client("u1", "Kowal")
    assert result.status == "not_found"


@pytest.mark.asyncio
async def test_single_token_literal_match_is_unique():
    """'Jan' is a standalone token in 'Jan Kowalski' → unique (literal substring match)."""
    rows = [_row("Jan Kowalski", "Warszawa")]
    with _patched_search_clients(rows):
        result = await lookup_client("u1", "Jan")
    assert result.status == "unique"


@pytest.mark.asyncio
async def test_bare_surname_multi():
    rows = [
        _row("Jan Kowalski", "Warszawa"),
        _row("Anna Kowalski", "Kraków"),
    ]
    with _patched_search_clients(rows):
        result = await lookup_client("u1", "Kowalski")
    assert result.status == "multi"


@pytest.mark.asyncio
async def test_bare_first_name_single_row_unique():
    rows = [_row("Jan Kowalski", "Warszawa")]
    with _patched_search_clients(rows):
        result = await lookup_client("u1", "Jan")
    assert result.status == "unique"


@pytest.mark.asyncio
async def test_city_narrows_two_rows_to_unique():
    rows = [
        _row("Jan Kowalski", "Warszawa", row_num=2),
        _row("Jan Kowalski", "Kraków", row_num=5),
    ]
    with _patched_search_clients(rows):
        result = await lookup_client("u1", "Jan Kowalski", city="Warszawa")
    assert result.status == "unique"
    assert result.clients[0]["_row"] == 2


@pytest.mark.asyncio
async def test_city_no_match_preserves_cross_city_multi():
    """'Jan Kowalski' in Kraków, city='Gdańsk', no Gdańsk row — candidates stay cross-city."""
    rows = [
        _row("Jan Kowalski", "Warszawa"),
        _row("Jan Kowalski", "Kraków"),
    ]
    with _patched_search_clients(rows):
        result = await lookup_client("u1", "Jan Kowalski", city="Gdańsk")
    assert result.status == "multi"


# ── phone lookup ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_phone_exact_unique():
    rows = [_row("Jan Kowalski", "Warszawa", phone="+48 600 123 456")]
    with (
        _patched_get_all_clients(rows),
        _patched_search_clients(rows) as mock_search,
    ):
        result = await lookup_client("u1", "+48600123456")
    assert result.status == "unique"
    assert result.is_phone_query is True
    mock_search.assert_not_called()


@pytest.mark.asyncio
async def test_phone_matches_with_or_without_polish_country_code():
    rows = [_row("Jan Kowalski", "Warszawa", phone="+48 600 123 456")]
    with _patched_get_all_clients(rows):
        result = await lookup_client("u1", "600123456")
    assert result.status == "unique"
    assert result.clients == rows


@pytest.mark.asyncio
async def test_phone_different_digits_is_not_found():
    """600123456 and 601123456 must NOT collide."""
    rows = [_row("Jan Kowalski", "Warszawa", phone="+48 600 123 456")]
    with _patched_get_all_clients(rows):
        result = await lookup_client("u1", "+48601123456")
    assert result.status == "not_found"
    assert result.is_phone_query is True


@pytest.mark.asyncio
async def test_phone_partial_digits_do_not_match_substrings():
    """A 7-digit phone-like fragment must not match a longer stored number."""
    rows = [_row("Jan Kowalski", "Warszawa", phone="+48 600 123 456")]
    with (
        _patched_get_all_clients(rows),
        _patched_search_clients(rows) as mock_search,
    ):
        result = await lookup_client("u1", "6001234")
    assert result.status == "not_found"
    mock_search.assert_not_called()


# ── suggest_fuzzy_client ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_suggest_fuzzy_client_returns_closest_row():
    rows = [_row("Jan Kowalski", "Warszawa")]
    with patch(
        "shared.clients.find.search_clients",
        new=AsyncMock(return_value=rows),
    ):
        suggestion = await suggest_fuzzy_client("u1", "Kowalsky")
    assert isinstance(suggestion, FuzzySuggestion)
    assert suggestion.candidate["Imię i nazwisko"] == "Jan Kowalski"
    assert suggestion.distance > 0


@pytest.mark.asyncio
async def test_suggest_fuzzy_client_none_when_no_rows():
    with patch(
        "shared.clients.find.search_clients",
        new=AsyncMock(return_value=[]),
    ):
        suggestion = await suggest_fuzzy_client("u1", "Kowalsky")
    assert suggestion is None


@pytest.mark.asyncio
async def test_suggest_fuzzy_client_ignores_non_name_raw_matches():
    """Raw search hits from city/email must not become name typo suggestions."""
    rows = [_row("Jan Kowalski", "Warszawa")]
    with patch(
        "shared.clients.find.search_clients",
        new=AsyncMock(return_value=rows),
    ):
        suggestion = await suggest_fuzzy_client("u1", "Warszawa")
    assert suggestion is None


@pytest.mark.asyncio
async def test_suggest_fuzzy_client_rejects_phone_query():
    """Phone fuzzy is unsafe per INTENCJE_MVP — must return None without hitting Sheets."""
    with patch(
        "shared.clients.find.search_clients",
        new=AsyncMock(return_value=[_row("Someone", phone="+48600123456")]),
    ) as mock_search:
        suggestion = await suggest_fuzzy_client("u1", "+48601123456")
    assert suggestion is None
    mock_search.assert_not_called()
