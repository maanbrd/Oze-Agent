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
        self.update_kwargs = None
        self.append_kwargs = None
        self.batch_update_kwargs = None

    def get(self, **kwargs):
        self.get_kwargs = kwargs
        return _Execute(self.get_result, self.get_error)

    def update(self, **kwargs):
        self.update_kwargs = kwargs
        return _Execute({})

    def append(self, **kwargs):
        self.append_kwargs = kwargs
        return _Execute({"updates": {"updatedRange": "Arkusz1!A2:P2"}})

    def batchUpdate(self, **kwargs):
        self.batch_update_kwargs = kwargs
        return _Execute({})


class _SpreadsheetsService:
    def __init__(self, values: _ValuesService, create_result=None, get_result=None):
        self._values = values
        self.create_result = create_result or {
            "spreadsheetId": "created-sheet",
            "sheets": [{"properties": {"sheetId": 123}}],
        }
        self.get_result = get_result or {"sheets": [{"properties": {"sheetId": 123}}]}
        self.create_kwargs = None
        self.batch_update_kwargs = None
        self.get_kwargs = None

    def values(self):
        return self._values

    def create(self, **kwargs):
        self.create_kwargs = kwargs
        return _Execute(self.create_result)

    def batchUpdate(self, **kwargs):
        self.batch_update_kwargs = kwargs
        return _Execute({})

    def get(self, **kwargs):
        self.get_kwargs = kwargs
        return _Execute(self.get_result)


class _SheetsService:
    def __init__(self, values: _ValuesService, create_result=None, get_result=None):
        self._spreadsheets = _SpreadsheetsService(values, create_result, get_result)

    def spreadsheets(self):
        return self._spreadsheets


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
async def test_create_spreadsheet_applies_operational_crm_template():
    from shared.google_sheets import DEFAULT_COLUMNS, create_spreadsheet

    values = _ValuesService()
    service = _SheetsService(values)

    with patch(
        "shared.google_sheets._get_sheets_service_sync",
        return_value=service,
    ):
        spreadsheet_id = await create_spreadsheet("user-1", "Agent-OZE CRM - Test")

    assert spreadsheet_id == "created-sheet"
    assert service.spreadsheets().create_kwargs["body"] == {
        "properties": {
            "title": "Agent-OZE CRM - Test",
            "locale": "pl_PL",
            "timeZone": "Europe/Warsaw",
        },
        "sheets": [{
            "properties": {
                "title": "OZE Klienci",
                "gridProperties": {
                    "rowCount": 1000,
                    "columnCount": 16,
                    "frozenRowCount": 1,
                },
            }
        }],
    }
    assert values.update_kwargs["body"] == {"values": [DEFAULT_COLUMNS]}

    requests = service.spreadsheets().batch_update_kwargs["body"]["requests"]
    request_keys = {next(iter(request)) for request in requests}

    assert "updateSheetProperties" in request_keys
    assert "setBasicFilter" in request_keys
    assert "updateDimensionProperties" in request_keys
    assert "repeatCell" in request_keys
    assert "addProtectedRange" in request_keys
    assert "addConditionalFormatRule" in request_keys
    assert "updateBorders" in request_keys

    frozen_request = next(request["updateSheetProperties"] for request in requests if "updateSheetProperties" in request)
    assert frozen_request["properties"]["gridProperties"]["frozenRowCount"] == 1

    filter_request = next(request["setBasicFilter"] for request in requests if "setBasicFilter" in request)
    assert filter_request["filter"]["range"] == {
        "sheetId": 123,
        "startRowIndex": 0,
        "startColumnIndex": 0,
        "endColumnIndex": 16,
    }

    hidden_column_requests = [
        request["updateDimensionProperties"]
        for request in requests
        if "updateDimensionProperties" in request
        and request["updateDimensionProperties"]["properties"].get("hiddenByUser") is True
    ]
    assert hidden_column_requests == [{
        "range": {
            "sheetId": 123,
            "dimension": "COLUMNS",
            "startIndex": 15,
            "endIndex": 16,
        },
        "properties": {"hiddenByUser": True},
        "fields": "hiddenByUser",
    }]

    protected_ranges = [request["addProtectedRange"]["protectedRange"] for request in requests if "addProtectedRange" in request]
    assert {
        "description": "OZE-Agent schema header - do not edit",
        "range": {
            "sheetId": 123,
            "startRowIndex": 0,
            "endRowIndex": 1,
            "startColumnIndex": 0,
            "endColumnIndex": 16,
        },
        "warningOnly": False,
    } in protected_ranges

    validations = [
        request["repeatCell"]
        for request in requests
        if "repeatCell" in request
        and "dataValidation" in request["repeatCell"]["cell"]
    ]
    validation_columns = {
        request["range"]["startColumnIndex"]: request["cell"]["dataValidation"]["condition"]["values"]
        for request in validations
    }
    assert validation_columns[5][0]["userEnteredValue"] == "Nowy lead"
    assert validation_columns[10][0]["userEnteredValue"] == "Telefon"
    assert validation_columns[12][0]["userEnteredValue"] == "Polecenie"

    sheet_property_updates = [
        request["updateSheetProperties"]
        for request in requests
        if "updateSheetProperties" in request
    ]
    assert any(
        update["properties"].get("gridProperties", {}).get("hideGridlines") is True
        and update["properties"].get("tabColor") == {
            "red": 61 / 255,
            "green": 255 / 255,
            "blue": 122 / 255,
        }
        for update in sheet_property_updates
    )

    header_format_request = next(
        request["repeatCell"]
        for request in requests
        if "repeatCell" in request
        and request["repeatCell"]["range"].get("startRowIndex") == 0
        and request["repeatCell"]["range"].get("endRowIndex") == 1
    )
    header_format = header_format_request["cell"]["userEnteredFormat"]
    assert header_format["backgroundColor"] == {
        "red": 5 / 255,
        "green": 8 / 255,
        "blue": 6 / 255,
    }
    assert header_format["textFormat"]["foregroundColor"] == {
        "red": 109 / 255,
        "green": 255 / 255,
        "blue": 122 / 255,
    }

    conditional_ranges = [
        request["addConditionalFormatRule"]["rule"]["ranges"][0]
        for request in requests
        if "addConditionalFormatRule" in request
    ]
    assert {"sheetId": 123, "startRowIndex": 1, "endRowIndex": 1000, "startColumnIndex": 5, "endColumnIndex": 6} in conditional_ranges
    assert {"sheetId": 123, "startRowIndex": 1, "endRowIndex": 1000, "startColumnIndex": 10, "endColumnIndex": 11} in conditional_ranges
    assert {"sheetId": 123, "startRowIndex": 1, "endRowIndex": 1000, "startColumnIndex": 12, "endColumnIndex": 13} in conditional_ranges

    table_border_request = next(request["updateBorders"] for request in requests if "updateBorders" in request)
    assert table_border_request["range"] == {
        "sheetId": 123,
        "startRowIndex": 0,
        "endRowIndex": 1000,
        "startColumnIndex": 0,
        "endColumnIndex": 16,
    }
    assert table_border_request["innerHorizontal"]["style"] == "SOLID"
    assert table_border_request["innerVertical"]["style"] == "SOLID"
    assert table_border_request["innerHorizontal"]["color"] == {
        "red": 199 / 255,
        "green": 216 / 255,
        "blue": 204 / 255,
    }


@pytest.mark.asyncio
async def test_add_client_blocks_when_sheet_headers_do_not_match_schema():
    from shared.google_sheets import add_client

    values = _ValuesService(get_result={"values": [[
        "Imię i nazwisko",
        "Telefon",
        "Email",
        "Miasto",
        "Adres",
        "Status",
        "Produkt",
        "Zmienione notatki",
    ]]})

    with patch(
        "shared.google_sheets.get_user_by_id",
        return_value={"google_sheets_id": "sheet-1"},
    ), patch(
        "shared.google_sheets._get_sheets_service_sync",
        return_value=_SheetsService(values),
    ):
        row = await add_client("user-1", {"Imię i nazwisko": "Jan Kowalski"})

    assert row is None
    assert values.append_kwargs is None


@pytest.mark.asyncio
async def test_update_client_blocks_when_sheet_headers_do_not_match_schema():
    from shared.google_sheets import DEFAULT_COLUMNS, update_client

    drifted_headers = list(DEFAULT_COLUMNS)
    drifted_headers[7] = "Zmienione notatki"
    values = _ValuesService(get_result={"values": [drifted_headers]})

    with patch(
        "shared.google_sheets.get_user_by_id",
        return_value={"google_sheets_id": "sheet-1"},
    ), patch(
        "shared.google_sheets._get_sheets_service_sync",
        return_value=_SheetsService(values),
    ):
        ok = await update_client("user-1", 7, {"Status": "Podpisane"})

    assert ok is False
    assert values.batch_update_kwargs is None


@pytest.mark.asyncio
async def test_add_client_allows_exact_sheet_schema():
    from shared.google_sheets import DEFAULT_COLUMNS, add_client

    values = _ValuesService(get_result={"values": [DEFAULT_COLUMNS]})

    with patch(
        "shared.google_sheets.get_user_by_id",
        return_value={"google_sheets_id": "sheet-1"},
    ), patch(
        "shared.google_sheets._get_sheets_service_sync",
        return_value=_SheetsService(values),
    ), patch("shared.google_sheets.update_user"):
        row = await add_client("user-1", {"Imię i nazwisko": "Jan Kowalski"})

    assert row == 2
    assert values.append_kwargs["spreadsheetId"] == "sheet-1"
    assert values.append_kwargs["insertDataOption"] == "OVERWRITE"


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
async def test_update_client_photo_metadata_does_not_touch_last_contact():
    values = _ValuesService(get_result={"values": [[
        "Imię i nazwisko",
        "Telefon",
        "Email",
        "Miasto",
        "Adres",
        "Status",
        "Produkt",
        "Notatki",
        "Data pierwszego kontaktu",
        "Data ostatniego kontaktu",
        "Następny krok",
        "Data następnego kroku",
        "Źródło pozyskania",
        "Zdjęcia",
        "Link do zdjęć",
        "ID wydarzenia Kalendarz",
    ]]})

    with patch(
        "shared.google_sheets.get_user_by_id",
        return_value={"google_sheets_id": "sheet-1"},
    ), patch(
        "shared.google_sheets._get_sheets_service_sync",
        return_value=_SheetsService(values),
    ):
        from shared.google_sheets import update_client_photo_metadata

        ok = await update_client_photo_metadata(
            "user-1",
            row_number=7,
            photo_count=3,
            folder_link="https://drive.google.com/drive/folders/folder-1",
        )

    assert ok is True
    data = values.batch_update_kwargs["body"]["data"]
    assert data == [
        {"range": "N7", "values": [[3]]},
        {"range": "O7", "values": [["https://drive.google.com/drive/folders/folder-1"]]},
    ]


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
