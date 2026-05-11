"""Google Sheets CRM operations for OZE-Agent.

All public functions are async and use asyncio.to_thread() for sync Google API calls.
Returns None / False / empty list on failure — never raises.
"""

import asyncio
import difflib
import logging
import re
from datetime import date
from typing import Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from shared.database import get_user_by_id, update_user
from shared.errors import ProactiveFetchError
from shared.google_auth import get_google_credentials

logger = logging.getLogger(__name__)

DEFAULT_COLUMNS = [
    "Imię i nazwisko",        # A
    "Telefon",                 # B
    "Email",                   # C
    "Miasto",                  # D
    "Adres",                   # E
    "Status",                  # F
    "Produkt",                 # G
    "Notatki",                 # H — tech specs (moc, metraż, kierunek) go here
    "Data pierwszego kontaktu",  # I
    "Data ostatniego kontaktu",  # J
    "Następny krok",           # K — enum: Telefon / Spotkanie / Wysłać ofertę / …
    "Data następnego kroku",   # L
    "Źródło pozyskania",       # M
    "Zdjęcia",                 # N
    "Link do zdjęć",           # O
    "ID wydarzenia Kalendarz", # P
]

STATUS_OPTIONS = [
    "Nowy lead",
    "Spotkanie umówione",
    "Spotkanie odbyte",
    "Oferta wysłana",
    "Podpisane",
    "Zamontowana",
    "Rezygnacja z umowy",
    "Nieaktywny",
    "Odrzucone",
]

NEXT_STEP_OPTIONS = [
    "Telefon",
    "Spotkanie",
    "Wysłać ofertę",
    "Follow-up dokumentowy",
    "Czekać na decyzję klienta",
    "Nic — zamknięte",
    "Inne",
]

SOURCE_OPTIONS = [
    "Polecenie",
    "Facebook ads",
    "Targi / event",
    "Formularz WWW",
    "Door to Door",
    "Baza własna",
    "Inne",
]

CRM_TEMPLATE_ROW_LIMIT = 1000

_COLUMN_WIDTHS = [
    180,  # A Imię i nazwisko
    115,  # B Telefon
    190,  # C Email
    130,  # D Miasto
    210,  # E Adres
    165,  # F Status
    155,  # G Produkt
    380,  # H Notatki
    145,  # I Data pierwszego kontaktu
    145,  # J Data ostatniego kontaktu
    200,  # K Następny krok
    165,  # L Data następnego kroku
    165,  # M Źródło pozyskania
    90,   # N Zdjęcia
    260,  # O Link do zdjęć
    230,  # P ID wydarzenia Kalendarz
]


# ── Internal helpers ──────────────────────────────────────────────────────────


def _rgb(hex_color: str) -> dict[str, float]:
    value = hex_color.removeprefix("#")
    return {
        "red": int(value[0:2], 16) / 255,
        "green": int(value[2:4], 16) / 255,
        "blue": int(value[4:6], 16) / 255,
    }


def _canonical_schema_matches(headers: list[str]) -> bool:
    return headers == DEFAULT_COLUMNS


def _log_schema_mismatch(user_id: str, headers: list[str]) -> None:
    logger.error(
        "sheet_schema_mismatch(%s): expected=%r actual=%r. "
        "Repair required: restore A1:P1 to the canonical OZE-Agent CRM headers.",
        user_id,
        DEFAULT_COLUMNS,
        headers,
    )


async def _get_verified_sheet_headers(user_id: str) -> list[str]:
    headers = await get_sheet_headers(user_id)
    if not headers:
        return []
    if not _canonical_schema_matches(headers):
        return []
    return headers


def _grid_range(
    sheet_id: int,
    *,
    start_row: int | None = None,
    end_row: int | None = None,
    start_col: int | None = None,
    end_col: int | None = None,
) -> dict:
    range_body: dict[str, int] = {"sheetId": sheet_id}
    if start_row is not None:
        range_body["startRowIndex"] = start_row
    if end_row is not None:
        range_body["endRowIndex"] = end_row
    if start_col is not None:
        range_body["startColumnIndex"] = start_col
    if end_col is not None:
        range_body["endColumnIndex"] = end_col
    return range_body


def _data_validation_rule(options: list[str]) -> dict:
    return {
        "condition": {
            "type": "ONE_OF_LIST",
            "values": [{"userEnteredValue": option} for option in options],
        },
        "inputMessage": "Wybierz wartość z listy OZE-Agent.",
        "strict": True,
        "showCustomUi": True,
    }


def _conditional_text_eq_rule(
    sheet_id: int,
    *,
    column_index: int,
    value: str,
    background: str,
    foreground: str = "#050806",
) -> dict:
    return {
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [
                    _grid_range(
                        sheet_id,
                        start_row=1,
                        end_row=CRM_TEMPLATE_ROW_LIMIT,
                        start_col=column_index,
                        end_col=column_index + 1,
                    )
                ],
                "booleanRule": {
                    "condition": {
                        "type": "TEXT_EQ",
                        "values": [{"userEnteredValue": value}],
                    },
                    "format": {
                        "backgroundColor": _rgb(background),
                        "textFormat": {
                            "bold": True,
                            "foregroundColor": _rgb(foreground),
                        },
                    },
                },
            },
            "index": 0,
        }
    }


def _border(color: str, style: str = "SOLID") -> dict:
    return {
        "style": style,
        "width": 1,
        "color": _rgb(color),
    }


def _build_operational_crm_template_requests(sheet_id: int) -> list[dict]:
    requests: list[dict] = [
        {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": sheet_id,
                    "gridProperties": {"frozenRowCount": 1, "hideGridlines": True},
                    "tabColor": _rgb("#3DFF7A"),
                },
                "fields": "gridProperties.frozenRowCount,gridProperties.hideGridlines,tabColor",
            }
        },
        {
            "setBasicFilter": {
                "filter": {
                    "range": _grid_range(sheet_id, start_row=0, start_col=0, end_col=len(DEFAULT_COLUMNS)),
                }
            }
        },
        {
            "repeatCell": {
                "range": _grid_range(sheet_id, start_row=0, end_row=1, start_col=0, end_col=len(DEFAULT_COLUMNS)),
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": _rgb("#050806"),
                        "horizontalAlignment": "CENTER",
                        "verticalAlignment": "MIDDLE",
                        "wrapStrategy": "WRAP",
                        "textFormat": {
                            "bold": True,
                            "fontSize": 10,
                            "foregroundColor": _rgb("#6DFF7A"),
                        },
                    }
                },
                "fields": (
                    "userEnteredFormat(backgroundColor,horizontalAlignment,"
                    "verticalAlignment,wrapStrategy,textFormat)"
                ),
            }
        },
        {
            "repeatCell": {
                "range": _grid_range(
                    sheet_id,
                    start_row=1,
                    end_row=CRM_TEMPLATE_ROW_LIMIT,
                    start_col=0,
                    end_col=len(DEFAULT_COLUMNS),
                ),
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": _rgb("#F4FAF6"),
                        "verticalAlignment": "TOP",
                        "wrapStrategy": "WRAP",
                        "textFormat": {
                            "foregroundColor": _rgb("#101815"),
                            "fontSize": 10,
                        },
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,verticalAlignment,wrapStrategy,textFormat)",
            }
        },
        {
            "updateBorders": {
                "range": _grid_range(
                    sheet_id,
                    start_row=0,
                    end_row=CRM_TEMPLATE_ROW_LIMIT,
                    start_col=0,
                    end_col=len(DEFAULT_COLUMNS),
                ),
                "top": _border("#C7D8CC"),
                "bottom": _border("#C7D8CC"),
                "left": _border("#C7D8CC"),
                "right": _border("#C7D8CC"),
                "innerHorizontal": _border("#C7D8CC"),
                "innerVertical": _border("#C7D8CC"),
            }
        },
        {
            "updateBorders": {
                "range": _grid_range(
                    sheet_id,
                    start_row=0,
                    end_row=1,
                    start_col=0,
                    end_col=len(DEFAULT_COLUMNS),
                ),
                "bottom": _border("#3DFF7A", "SOLID_THICK"),
            }
        },
        {
            "repeatCell": {
                "range": _grid_range(sheet_id, start_row=1, end_row=CRM_TEMPLATE_ROW_LIMIT, start_col=8, end_col=10),
                "cell": {
                    "userEnteredFormat": {
                        "numberFormat": {"type": "DATE", "pattern": "dd.mm.yyyy"}
                    }
                },
                "fields": "userEnteredFormat.numberFormat",
            }
        },
        {
            "repeatCell": {
                "range": _grid_range(sheet_id, start_row=1, end_row=CRM_TEMPLATE_ROW_LIMIT, start_col=11, end_col=12),
                "cell": {
                    "userEnteredFormat": {
                        "numberFormat": {"type": "DATE_TIME", "pattern": "dd.mm.yyyy hh:mm"}
                    }
                },
                "fields": "userEnteredFormat.numberFormat",
            }
        },
        {
            "repeatCell": {
                "range": _grid_range(sheet_id, start_row=1, end_row=CRM_TEMPLATE_ROW_LIMIT, start_col=5, end_col=6),
                "cell": {"dataValidation": _data_validation_rule(STATUS_OPTIONS)},
                "fields": "dataValidation",
            }
        },
        {
            "repeatCell": {
                "range": _grid_range(sheet_id, start_row=1, end_row=CRM_TEMPLATE_ROW_LIMIT, start_col=10, end_col=11),
                "cell": {"dataValidation": _data_validation_rule(NEXT_STEP_OPTIONS)},
                "fields": "dataValidation",
            }
        },
        {
            "repeatCell": {
                "range": _grid_range(sheet_id, start_row=1, end_row=CRM_TEMPLATE_ROW_LIMIT, start_col=12, end_col=13),
                "cell": {"dataValidation": _data_validation_rule(SOURCE_OPTIONS)},
                "fields": "dataValidation",
            }
        },
        {
            "addProtectedRange": {
                "protectedRange": {
                    "description": "OZE-Agent schema header - do not edit",
                    "range": _grid_range(sheet_id, start_row=0, end_row=1, start_col=0, end_col=len(DEFAULT_COLUMNS)),
                    "warningOnly": False,
                }
            }
        },
        {
            "addProtectedRange": {
                "protectedRange": {
                    "description": "OZE-Agent Calendar event IDs - do not edit",
                    "range": _grid_range(sheet_id, start_row=1, start_col=15, end_col=16),
                    "warningOnly": False,
                }
            }
        },
    ]

    for index, width in enumerate(_COLUMN_WIDTHS):
        requests.append({
            "updateDimensionProperties": {
                "range": {
                    "sheetId": sheet_id,
                    "dimension": "COLUMNS",
                    "startIndex": index,
                    "endIndex": index + 1,
                },
                "properties": {"pixelSize": width},
                "fields": "pixelSize",
            }
        })

    requests.append({
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "COLUMNS",
                "startIndex": 15,
                "endIndex": 16,
            },
            "properties": {"hiddenByUser": True},
            "fields": "hiddenByUser",
        }
    })

    status_colors = {
        "Nowy lead": ("#6DFF7A", "#050806"),
        "Spotkanie umówione": ("#57D9FF", "#050806"),
        "Spotkanie odbyte": ("#60CDBB", "#050806"),
        "Oferta wysłana": ("#FFD34D", "#050806"),
        "Podpisane": ("#A7F3D0", "#050806"),
        "Zamontowana": ("#16A34A", "#FFFFFF"),
        "Rezygnacja z umowy": ("#FF6B7A", "#050806"),
        "Nieaktywny": ("#7C8087", "#FFFFFF"),
        "Odrzucone": ("#EF4444", "#FFFFFF"),
    }
    for status, (background, foreground) in status_colors.items():
        requests.append(_conditional_text_eq_rule(
            sheet_id,
            column_index=5,
            value=status,
            background=background,
            foreground=foreground,
        ))

    next_step_colors = {
        "Telefon": ("#6DFF7A", "#050806"),
        "Spotkanie": ("#57D9FF", "#050806"),
        "Wysłać ofertę": ("#FFD34D", "#050806"),
        "Follow-up dokumentowy": ("#B084FF", "#050806"),
        "Czekać na decyzję klienta": ("#F2AA65", "#050806"),
        "Nic — zamknięte": ("#7C8087", "#FFFFFF"),
        "Inne": ("#C7D2FE", "#050806"),
    }
    for next_step, (background, foreground) in next_step_colors.items():
        requests.append(_conditional_text_eq_rule(
            sheet_id,
            column_index=10,
            value=next_step,
            background=background,
            foreground=foreground,
        ))

    source_colors = {
        "Polecenie": ("#6DFF7A", "#050806"),
        "Facebook ads": ("#3B82F6", "#FFFFFF"),
        "Targi / event": ("#F97316", "#050806"),
        "Formularz WWW": ("#22D3EE", "#050806"),
        "Door to Door": ("#FACC15", "#050806"),
        "Baza własna": ("#A78BFA", "#050806"),
        "Inne": ("#9CA3AF", "#050806"),
    }
    for source, (background, foreground) in source_colors.items():
        requests.append(_conditional_text_eq_rule(
            sheet_id,
            column_index=12,
            value=source,
            background=background,
            foreground=foreground,
        ))

    return requests


def _get_sheets_service_sync(user_id: str):
    """Build and return a Google Sheets API service (sync)."""
    creds = get_google_credentials(user_id)
    if not creds:
        return None
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def _is_auth_error(error: HttpError) -> bool:
    return error.resp.status in (401, 403)


def _digits_only(s: str) -> str:
    """Strip all non-digit characters."""
    return re.sub(r"\D", "", s)


def _is_phone_query(q: str) -> bool:
    """Return True if q is a phone-number query (7+ digits, ≤4 non-digit chars)."""
    digits = _digits_only(q)
    non_digits = len(q) - len(digits)
    return len(digits) >= 7 and non_digits <= 4


def _fuzzy_match(query: str, value: str, threshold: float = 0.75) -> bool:
    """Return True if query loosely matches value (case-insensitive).

    For multi-word queries (e.g. full names): uses word-to-word comparison only —
    ALL query words must find a fuzzy match in value words. This prevents
    last-name-only false positives where shared surnames inflate the full-string
    ratio (e.g. "Marcin Kowalski" must NOT match "Jan Kowalski").

    For single-word queries: checks full-string ratio then word-level ratio,
    so "Kowalsky" matches "Jan Kowalski" even with a typo.
    """
    q = query.lower().strip()
    v = value.lower().strip()

    # q in v: query is a substring of the stored value — always valid
    if q in v:
        return True

    q_words = q.split()
    v_words = v.split()

    # v in q: allow only when v is a multi-word phrase (full name contained inside a
    # longer query like "Jan Kowalski Wrocław") or the query is a single word.
    # This prevents single-word stored values (e.g. city "Wrocław") from falsely
    # matching multi-word name+city queries (e.g. "Ala Wrocław").
    if v in q and (len(v_words) > 1 or len(q_words) == 1):
        return True

    if len(q_words) > 1:
        # Multi-word query: skip full-string ratio (shared prefixes like "jan "
        # inflate the score). Require ALL query words to match a value word.
        for qw in q_words:
            if not any(difflib.SequenceMatcher(None, qw, vw).ratio() >= threshold for vw in v_words):
                return False
        return True

    # Single-word query: full-string ratio first, then word-level
    if difflib.SequenceMatcher(None, q, v).ratio() >= threshold:
        return True
    for vw in v_words:
        if difflib.SequenceMatcher(None, q, vw).ratio() >= threshold:
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
        if headers and _canonical_schema_matches(headers):
            update_user(user_id, {"sheet_columns": headers})
        elif headers:
            _log_schema_mismatch(user_id, headers)
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


async def get_all_clients_or_raise(user_id: str) -> list[dict]:
    """Return all client rows, raising when data cannot be trusted.

    Existing `get_all_clients` keeps its legacy "[] on error" contract for
    Phase 3/4/5 handlers. The proactive morning brief uses this strict variant
    so a Sheets/config outage cannot be rendered as an empty follow-up list.
    """
    user = get_user_by_id(user_id)
    if not user:
        raise ProactiveFetchError(f"user_not_found:{user_id}")
    if not user.get("google_sheets_id"):
        raise ProactiveFetchError("sheets_not_configured")
    spreadsheet_id = user["google_sheets_id"]

    def _fetch():
        service = _get_sheets_service_sync(user_id)
        if not service:
            raise ProactiveFetchError("sheets_no_credentials")
        return service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range="A1:ZZ"
        ).execute()

    try:
        result = await asyncio.to_thread(_fetch)
    except ProactiveFetchError:
        raise
    except Exception as e:
        raise ProactiveFetchError(f"sheets_api_error: {e}") from e

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


_POLISH_NAME_SUFFIXES = (
    "skiego", "ckiego", "owego", "iego", "ego", "emu", "owi", "skim", "im", "ą",
)


def _strip_polish_suffix(query: str) -> str:
    """Strip common Polish genitive/locative suffixes from name queries.

    "Kowalskiego" → "Kowalsk", "Mazurowi" → "Mazur", "Nowaka" → "Nowak".
    Returns the original string unchanged when no known suffix is found.
    """
    lower = query.lower()
    for suffix in _POLISH_NAME_SUFFIXES:
        if lower.endswith(suffix) and len(query) > len(suffix) + 2:
            return query[: -len(suffix)]
    return query


async def search_clients(user_id: str, query: str) -> list[dict]:
    """Fuzzy search clients by name, city, or phone. Typo-tolerant.

    Tries both the raw query and a suffix-stripped version so inflected Polish
    names like "Kowalskiego" match stored "Kowalski".

    Phone-number queries (7+ digits) use exact digit matching to avoid
    fuzzy false-positives on similar numbers (e.g. 600123456 ≠ 601123456).
    """
    clients = await get_all_clients(user_id)
    if not clients:
        return []

    # Phone-number path: exact digit matching only
    if _is_phone_query(query):
        q_digits = _digits_only(query)
        results = []
        for client in clients:
            stored = _digits_only(client.get("Telefon", ""))
            if stored and (stored == q_digits or q_digits in stored or stored in q_digits):
                results.append(client)
        return results

    stripped = _strip_polish_suffix(query)
    queries_to_try = [query] if stripped.lower() == query.lower() else [query, stripped]

    search_cols = ["Imię i nazwisko", "Miasto", "Telefon", "Email"]
    results: list[dict] = []
    seen_rows: set = set()
    for q in queries_to_try:
        for client in clients:
            row = client.get("_row")
            if row in seen_rows:
                continue
            for col in search_cols:
                value = client.get(col, "")
                if value and _fuzzy_match(q, value):
                    results.append(client)
                    seen_rows.add(row)
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

        headers = await _get_verified_sheet_headers(user_id)
        if not headers:
            return None

        if "Data pierwszego kontaktu" not in client_data:
            client_data["Data pierwszego kontaktu"] = date.today().strftime("%Y-%m-%d")

        def _value_for_header(header: str):
            value = client_data.get(header, "")
            if header == "Status" and not str(value).strip():
                return "Nowy lead"
            return value

        row = [_value_for_header(h) for h in headers]

        def _append():
            service = _get_sheets_service_sync(user_id)
            if not service:
                logger.error("add_client: no service for user %s", user_id)
                return None
            logger.info("add_client: appending %d-cell row to %s", len(row), spreadsheet_id)
            result = service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range="A1",
                valueInputOption="USER_ENTERED",
                insertDataOption="OVERWRITE",
                body={"values": [row]},
            ).execute()
            updated_range = result.get("updates", {}).get("updatedRange", "")
            logger.info("add_client: updatedRange=%s", updated_range)
            # Extract row number from range like "Sheet1!A5:Q5"
            try:
                row_num = int(updated_range.split("!")[1].split(":")[0][1:])
                return row_num
            except Exception as e:
                logger.error("add_client: row_num parse failed, updatedRange=%r: %s", updated_range, e)
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

        headers = await _get_verified_sheet_headers(user_id)
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


async def update_client_fields_without_touch(user_id: str, row_number: int, updates: dict) -> bool:
    """Update specific client fields without touching last-contact date.

    Offer sending uses this for appending newly supplied email addresses after
    Gmail success. "Data ostatniego kontaktu" must change only when the status
    actually moves to "Oferta wysłana".
    """
    try:
        user = get_user_by_id(user_id)
        if not user or not user.get("google_sheets_id"):
            return False
        spreadsheet_id = user["google_sheets_id"]

        headers = await _get_verified_sheet_headers(user_id)
        if not headers:
            return False

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
        logger.error(
            "update_client_fields_without_touch(%s, row=%s): %s",
            user_id,
            row_number,
            e,
        )
        return False


async def update_client_photo_metadata(
    user_id: str,
    row_number: int,
    photo_count: int,
    folder_link: str,
) -> bool:
    """Update only photo metadata columns N/O for a client row.

    Unlike update_client(), this helper deliberately does not touch
    "Data ostatniego kontaktu" because uploading documentation photos is not
    a client contact event.
    """
    try:
        user = get_user_by_id(user_id)
        if not user or not user.get("google_sheets_id"):
            return False
        spreadsheet_id = user["google_sheets_id"]

        headers = await _get_verified_sheet_headers(user_id)
        if not headers:
            return False

        updates = {
            "Zdjęcia": photo_count,
            "Link do zdjęć": folder_link,
        }

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
        logger.error(
            "update_client_photo_metadata(%s, row=%s): %s",
            user_id,
            row_number,
            e,
        )
        return False


async def delete_client(user_id: str, row_number: int) -> bool:
    """Delete an entire row from the spreadsheet."""
    try:
        user = get_user_by_id(user_id)
        if not user or not user.get("google_sheets_id"):
            return False
        spreadsheet_id = user["google_sheets_id"]

        headers = await _get_verified_sheet_headers(user_id)
        if not headers:
            return False

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
                body={
                    "properties": {
                        "title": name,
                        "locale": "pl_PL",
                        "timeZone": "Europe/Warsaw",
                    },
                    "sheets": [{
                        "properties": {
                            "title": "OZE Klienci",
                            "gridProperties": {
                                "rowCount": CRM_TEMPLATE_ROW_LIMIT,
                                "columnCount": len(DEFAULT_COLUMNS),
                                "frozenRowCount": 1,
                            },
                        }
                    }],
                }
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

            # Operational CRM template: visual polish, validations, protection.
            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={"requests": _build_operational_crm_template_requests(sheet_id)},
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
