"""Unit tests for shared/google_sheets.py — Google API and DB calls are mocked."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class _Execute:
    def __init__(self, value=None, error=None):
        self.value = value
        self.error = error

    def execute(self):
        if self.error:
            raise self.error
        return self.value


class _ValuesService:
    def __init__(self, get_result=None, get_error=None):
        self.get_result = get_result if get_result is not None else {"values": []}
        self.get_error = get_error
        self.get_kwargs = None

    def get(self, **kwargs):
        self.get_kwargs = kwargs
        return _Execute(self.get_result, self.get_error)


class _SpreadsheetsService:
    def __init__(self, values: _ValuesService):
        self._values = values

    def values(self):
        return self._values


class _SheetsService:
    def __init__(self, values: _ValuesService):
        self._values = values

    def spreadsheets(self):
        return _SpreadsheetsService(self._values)


# ── search_clients fuzzy matching ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_clients_fuzzy_typo():
    """'Kowalsky' should match 'Kowalski' via fuzzy matching."""
    clients = [
        {"Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa", "Telefon": "600100200", "_row": 2},
        {"Imię i nazwisko": "Anna Nowak", "Miasto": "Kraków", "Telefon": "601200300", "_row": 3},
    ]
    with patch("shared.google_sheets.get_all_clients", new=AsyncMock(return_value=clients)):
        from shared.google_sheets import search_clients
        results = await search_clients("user-1", "Kowalsky")
    assert len(results) == 1
    assert results[0]["Imię i nazwisko"] == "Jan Kowalski"


@pytest.mark.asyncio
async def test_search_clients_by_city():
    clients = [
        {"Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa", "Telefon": "", "_row": 2},
        {"Imię i nazwisko": "Anna Nowak", "Miasto": "Kraków", "Telefon": "", "_row": 3},
    ]
    with patch("shared.google_sheets.get_all_clients", new=AsyncMock(return_value=clients)):
        from shared.google_sheets import search_clients
        results = await search_clients("user-1", "Kraków")
    assert len(results) == 1
    assert results[0]["Imię i nazwisko"] == "Anna Nowak"


@pytest.mark.asyncio
async def test_search_clients_no_match():
    clients = [
        {"Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa", "Telefon": "", "_row": 2},
    ]
    with patch("shared.google_sheets.get_all_clients", new=AsyncMock(return_value=clients)):
        from shared.google_sheets import search_clients
        results = await search_clients("user-1", "Xyz123abc")
    assert results == []


@pytest.mark.asyncio
async def test_search_clients_empty_sheet():
    with patch("shared.google_sheets.get_all_clients", new=AsyncMock(return_value=[])):
        from shared.google_sheets import search_clients
        results = await search_clients("user-1", "Kowalski")
    assert results == []


# ── get_pipeline_stats ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_pipeline_stats_counts_correctly():
    clients = [
        {"Status": "Nowy lead", "_row": 2},
        {"Status": "Nowy lead", "_row": 3},
        {"Status": "Spotkanie umówione", "_row": 4},
        {"Status": "", "_row": 5},
    ]
    with patch("shared.google_sheets.get_all_clients", new=AsyncMock(return_value=clients)):
        from shared.google_sheets import get_pipeline_stats
        stats = await get_pipeline_stats("user-1")
    assert stats["Nowy lead"] == 2
    assert stats["Spotkanie umówione"] == 1
    assert stats["Brak statusu"] == 1


@pytest.mark.asyncio
async def test_get_pipeline_stats_empty_sheet():
    with patch("shared.google_sheets.get_all_clients", new=AsyncMock(return_value=[])):
        from shared.google_sheets import get_pipeline_stats
        stats = await get_pipeline_stats("user-1")
    assert stats == {}


# ── error handling ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_all_clients_returns_empty_on_error():
    with patch("shared.google_sheets.get_user_by_id", side_effect=Exception("DB down")):
        from shared.google_sheets import get_all_clients
        result = await get_all_clients("user-1")
    assert result == []


@pytest.mark.asyncio
async def test_add_client_returns_none_on_missing_sheet():
    """User with no google_sheets_id → add_client returns None."""
    with patch("shared.google_sheets.get_user_by_id", return_value={"id": "u1"}):
        from shared.google_sheets import add_client
        result = await add_client("user-1", {"Imię i nazwisko": "Jan"})
    assert result is None


@pytest.mark.asyncio
async def test_get_sheet_headers_returns_empty_on_missing_sheet():
    with patch("shared.google_sheets.get_user_by_id", return_value={"id": "u1"}):
        from shared.google_sheets import get_sheet_headers
        result = await get_sheet_headers("user-1")
    assert result == []


# ── strict proactive fetch ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_all_clients_or_raise_raises_when_sheets_id_missing():
    from shared.errors import ProactiveFetchError
    from shared.google_sheets import get_all_clients_or_raise

    with patch("shared.google_sheets.get_user_by_id", return_value={"id": "u1"}):
        with pytest.raises(ProactiveFetchError, match="sheets_not_configured"):
            await get_all_clients_or_raise("user-1")


@pytest.mark.asyncio
async def test_get_all_clients_or_raise_raises_on_api_error():
    from shared.errors import ProactiveFetchError
    from shared.google_sheets import get_all_clients_or_raise

    values = _ValuesService(get_error=RuntimeError("Google 500"))
    with patch(
        "shared.google_sheets.get_user_by_id",
        return_value={"google_sheets_id": "sheet-1"},
    ), patch(
        "shared.google_sheets._get_sheets_service_sync",
        return_value=_SheetsService(values),
    ):
        with pytest.raises(ProactiveFetchError, match="sheets_api_error"):
            await get_all_clients_or_raise("user-1")


@pytest.mark.asyncio
async def test_get_all_clients_or_raise_returns_empty_for_empty_sheet():
    from shared.google_sheets import get_all_clients_or_raise

    values = _ValuesService(get_result={"values": [["Imię i nazwisko", "Miasto"]]})
    with patch(
        "shared.google_sheets.get_user_by_id",
        return_value={"google_sheets_id": "sheet-1"},
    ), patch(
        "shared.google_sheets._get_sheets_service_sync",
        return_value=_SheetsService(values),
    ):
        result = await get_all_clients_or_raise("user-1")

    assert result == []
    assert values.get_kwargs["spreadsheetId"] == "sheet-1"
    assert values.get_kwargs["range"] == "A1:ZZ"


@pytest.mark.asyncio
async def test_get_all_clients_or_raise_returns_rows_for_valid_sheet():
    from shared.google_sheets import get_all_clients_or_raise

    values = _ValuesService(get_result={
        "values": [
            ["Imię i nazwisko", "Miasto"],
            ["Jan Kowalski", "Warszawa"],
        ],
    })
    with patch(
        "shared.google_sheets.get_user_by_id",
        return_value={"google_sheets_id": "sheet-1"},
    ), patch(
        "shared.google_sheets._get_sheets_service_sync",
        return_value=_SheetsService(values),
    ):
        result = await get_all_clients_or_raise("user-1")

    assert result == [{"Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa", "_row": 2}]
