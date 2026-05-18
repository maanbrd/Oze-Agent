"""Google API IO for the owner-facing admin mirror."""

from __future__ import annotations

import asyncio

from googleapiclient.discovery import build

from shared.google_auth import get_google_credentials


def _quote_sheet_name(name: str) -> str:
    return "'" + name.replace("'", "''") + "'"


def build_admin_sheets_service(admin_user_id: str):
    creds = get_google_credentials(admin_user_id)
    if not creds:
        return None
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def build_admin_calendar_service(admin_user_id: str):
    creds = get_google_credentials(admin_user_id)
    if not creds:
        return None
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def ensure_sheet_tabs_sync(service, spreadsheet_id: str, tab_names: list[str]) -> None:
    result = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        fields="sheets.properties.title",
    ).execute()
    existing = {
        sheet.get("properties", {}).get("title")
        for sheet in result.get("sheets", [])
    }
    requests = [
        {"addSheet": {"properties": {"title": name}}}
        for name in tab_names
        if name not in existing
    ]
    if requests:
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": requests},
        ).execute()


def read_tab_values_sync(service, spreadsheet_id: str, tab_name: str) -> list[list]:
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=f"{_quote_sheet_name(tab_name)}!A:ZZ",
        ).execute()
        return result.get("values", [])
    except Exception:
        return []


def write_tab_values_sync(
    service,
    spreadsheet_id: str,
    tab_name: str,
    values: list[list],
) -> None:
    range_prefix = _quote_sheet_name(tab_name)
    service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id,
        range=f"{range_prefix}!A:ZZ",
        body={},
    ).execute()
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"{range_prefix}!A1",
        valueInputOption="RAW",
        body={"values": values},
    ).execute()


def write_workbook_sync(service, spreadsheet_id: str, tabs: dict[str, list[list]]) -> None:
    ensure_sheet_tabs_sync(service, spreadsheet_id, list(tabs))
    for name, values in tabs.items():
        write_tab_values_sync(service, spreadsheet_id, name, values)


async def write_workbook(service, spreadsheet_id: str, tabs: dict[str, list[list]]) -> None:
    await asyncio.to_thread(write_workbook_sync, service, spreadsheet_id, tabs)


async def read_tab_values(service, spreadsheet_id: str, tab_name: str) -> list[list]:
    return await asyncio.to_thread(read_tab_values_sync, service, spreadsheet_id, tab_name)
