"""Google Sheets CRM operations for OZE-Agent.

All public functions are async and use asyncio.to_thread() for sync Google API calls.
Returns None / False / empty list on failure — never raises.
"""

import asyncio
import difflib
import logging
from datetime import date
from typing import Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from shared.database import get_user_by_id, update_user
from shared.google_auth import get_google_credentials

logger = logging.getLogger(__name__)

DEFAULT_COLUMNS = [
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
    "Źródło",
    "Wartość kontraktu",
    "Zdjęcia",
    "Link do zdjęć",
    "ID kalendarza",
    "Dodatkowe info",
]


# ── Internal helpers ──────────────────────────────────────────────────────────


def _get_sheets_service_sync(user_id: str):
    """Build and return a Google Sheets API service (sync)."""
    creds = get_google_credentials(user_id)
    if not creds:
        return None
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def _is_auth_error(error: HttpError) -> bool:
    return error.resp.status in (401, 403)


def _fuzzy_match(query: str, value: str, threshold: float = 0.75) -> bool:
    """Return True if query loosely matches value (case-insensitive).

    Checks the full string and also each word individually, so 'Kowalsky'
    matches 'Jan Kowalski' even though the full-string ratio is below threshold.
    """
    q = query.lower().strip()
    v = value.lower().strip()
    if q in v or v in q:
        return True
    # Full-string ratio
    if difflib.SequenceMatcher(None, q, v).ratio() >= threshold:
        return True
    # Word-level ratio — match query against each word in the value
    for word in v.split():
        if difflib.SequenceMatcher(None, q, word).ratio() >= threshold:
            return True
    return False


# ── Public async API ──────────────────────────────────────────────────────────


async def get_sheets_service(user_id: str):
    """Return a Sheets API service for this user, or None."""
    return await asyncio.to_thread(_get_sheets_service_sync, user_id)


async def get_sheet_headers(user_id: str) -> list[str]:
    """Read row 1 from user's spreadsheet and cache in users.sheet_columns."""
    try:
        user = get_user_by_id(user_id)
        if not user or not user.get("google_sheets_id"):
            return []
        spreadsheet_id = user["google_sheets_id"]

        def _read():
            service = _get_sheets_service_sync(user_id)
            if not service:
                return []
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id, range="A1:ZZ1"
            ).execute()
            return result.get("values", [[]])[0]

        headers = await asyncio.to_thread(_read)
        if headers:
            update_user(user_id, {"sheet_columns": headers})
        return headers
    except Exception as e:
        logger.error("get_sheet_headers(%s): %s", user_id, e)
        return []


async def get_all_clients(user_id: str) -> list[dict]:
    """Return all client rows as a list of dicts {header: value}."""
    try:
        user = get_user_by_id(user_id)
        if not user or not user.get("google_sheets_id"):
            return []
        spreadsheet_id = user["google_sheets_id"]

        def _read():
            service = _get_sheets_service_sync(user_id)
            if not service:
                return []
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id, range="A1:ZZ"
            ).execute()
            rows = result.get("values", [])
            if len(rows) < 2:
                return []
            headers = rows[0]
            clients = []
            for i, row in enumerate(rows[1:], start=2):
                padded = row + [""] * (len(headers) - len(row))
                client = dict(zip(headers, padded))
                client["_row"] = i
                clients.append(client)
            return clients

        return await asyncio.to_thread(_read)
    except Exception as e:
        logger.error("get_all_clients(%s): %s", user_id, e)
        return []


async def search_clients(user_id: str, query: str) -> list[dict]:
    """Fuzzy search clients by name, city, or phone. Typo-tolerant."""
    clients = await get_all_clients(user_id)
    if not clients:
        return []

    search_cols = ["Imię i nazwisko", "Miasto", "Telefon", "Email"]
    results = []
    for client in clients:
        for col in search_cols:
            value = client.get(col, "")
            if value and _fuzzy_match(query, value):
                results.append(client)
                break
    return results


async def get_client_by_name_and_city(
    user_id: str, name: str, city: str
) -> Optional[dict]:
    """Find a client by exact-ish name + city match (for duplicate detection)."""
    clients = await get_all_clients(user_id)
    for client in clients:
        name_match = _fuzzy_match(name, client.get("Imię i nazwisko", ""), threshold=0.85)
        city_match = _fuzzy_match(city, client.get("Miasto", ""), threshold=0.85)
        if name_match and city_match:
            return client
    return None


async def add_client(user_id: str, client_data: dict) -> Optional[int]:
    """Append a new client row. Returns the row number (1-indexed) or None."""
    try:
        user = get_user_by_id(user_id)
        if not user or not user.get("google_sheets_id"):
            return None
        spreadsheet_id = user["google_sheets_id"]

        headers = await get_sheet_headers(user_id)
        if not headers:
            return None

        if "Data pierwszego kontaktu" not in client_data:
            client_data["Data pierwszego kontaktu"] = date.today().strftime("%Y-%m-%d")

        row = [client_data.get(h, "") for h in headers]

        def _append():
            service = _get_sheets_service_sync(user_id)
            if not service:
                return None
            result = service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range="A1",
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body={"values": [row]},
            ).execute()
            updated_range = result.get("updates", {}).get("updatedRange", "")
            # Extract row number from range like "Sheet1!A5:Q5"
            try:
                row_num = int(updated_range.split("!")[1].split(":")[0][1:])
                return row_num
            except Exception:
                return None

        return await asyncio.to_thread(_append)
    except Exception as e:
        logger.error("add_client(%s): %s", user_id, e)
        return None


async def update_client(user_id: str, row_number: int, updates: dict) -> bool:
    """Update specific fields in an existing client row."""
    try:
        user = get_user_by_id(user_id)
        if not user or not user.get("google_sheets_id"):
            return False
        spreadsheet_id = user["google_sheets_id"]

        headers = await get_sheet_headers(user_id)
        if not headers:
            return False

        updates["Data ostatniego kontaktu"] = date.today().strftime("%Y-%m-%d")

        def _update():
            service = _get_sheets_service_sync(user_id)
            if not service:
                return False
            data = []
            for col_name, value in updates.items():
                if col_name in headers:
                    col_idx = headers.index(col_name)
                    col_letter = chr(ord("A") + col_idx)
                    data.append({
                        "range": f"{col_letter}{row_number}",
                        "values": [[value]],
                    })
            if not data:
                return False
            service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={"valueInputOption": "USER_ENTERED", "data": data},
            ).execute()
            return True

        return await asyncio.to_thread(_update)
    except Exception as e:
        logger.error("update_client(%s, row=%s): %s", user_id, row_number, e)
        return False


async def delete_client(user_id: str, row_number: int) -> bool:
    """Delete an entire row from the spreadsheet."""
    try:
        user = get_user_by_id(user_id)
        if not user or not user.get("google_sheets_id"):
            return False
        spreadsheet_id = user["google_sheets_id"]

        def _get_sheet_id():
            service = _get_sheets_service_sync(user_id)
            if not service:
                return None
            meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            return meta["sheets"][0]["properties"]["sheetId"]

        sheet_id = await asyncio.to_thread(_get_sheet_id)
        if sheet_id is None:
            return False

        def _delete():
            service = _get_sheets_service_sync(user_id)
            if not service:
                return False
            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={
                    "requests": [{
                        "deleteDimension": {
                            "range": {
                                "sheetId": sheet_id,
                                "dimension": "ROWS",
                                "startIndex": row_number - 1,
                                "endIndex": row_number,
                            }
                        }
                    }]
                },
            ).execute()
            return True

        return await asyncio.to_thread(_delete)
    except Exception as e:
        logger.error("delete_client(%s, row=%s): %s", user_id, row_number, e)
        return False


async def create_spreadsheet(user_id: str, name: str) -> Optional[str]:
    """Create a new spreadsheet with default 17 columns and bold frozen header."""
    try:
        def _create():
            service = _get_sheets_service_sync(user_id)
            if not service:
                return None

            spreadsheet = service.spreadsheets().create(
                body={"properties": {"title": name}}
            ).execute()
            spreadsheet_id = spreadsheet["spreadsheetId"]
            sheet_id = spreadsheet["sheets"][0]["properties"]["sheetId"]

            # Write headers
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range="A1",
                valueInputOption="RAW",
                body={"values": [DEFAULT_COLUMNS]},
            ).execute()

            # Bold + freeze header row
            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={
                    "requests": [
                        {
                            "repeatCell": {
                                "range": {
                                    "sheetId": sheet_id,
                                    "startRowIndex": 0,
                                    "endRowIndex": 1,
                                },
                                "cell": {
                                    "userEnteredFormat": {
                                        "textFormat": {"bold": True}
                                    }
                                },
                                "fields": "userEnteredFormat.textFormat.bold",
                            }
                        },
                        {
                            "updateSheetProperties": {
                                "properties": {
                                    "sheetId": sheet_id,
                                    "gridProperties": {"frozenRowCount": 1},
                                },
                                "fields": "gridProperties.frozenRowCount",
                            }
                        },
                    ]
                },
            ).execute()
            return spreadsheet_id

        return await asyncio.to_thread(_create)
    except Exception as e:
        logger.error("create_spreadsheet(%s): %s", user_id, e)
        return None


async def get_pipeline_stats(user_id: str) -> dict:
    """Count clients per pipeline status. Returns {status: count}."""
    clients = await get_all_clients(user_id)
    stats: dict[str, int] = {}
    for client in clients:
        status = client.get("Status", "Brak statusu") or "Brak statusu"
        stats[status] = stats.get(status, 0) + 1
    return stats
