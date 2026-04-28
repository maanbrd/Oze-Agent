"""Dashboard API routes."""

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends

from api.auth import AuthUser, get_current_auth_user
from shared.database import get_supabase_client
from shared.google_calendar import get_events_for_range
from shared.google_sheets import get_all_clients

router = APIRouter()


@router.get("/me")
async def get_me(auth_user: AuthUser = Depends(get_current_auth_user)):
    """Return the authenticated user's profile.

    FastAPI uses the service key, so RLS is not the authorization boundary here.
    The `auth_user_id` always comes from the verified JWT subject.
    """
    result = (
        get_supabase_client()
        .table("users")
        .select(
            "id, auth_user_id, name, email, phone, subscription_status, "
            "subscription_plan, subscription_current_period_end, activation_paid, "
            "onboarding_completed, google_sheets_id, google_calendar_id, "
            "google_drive_folder_id, telegram_id"
        )
        .eq("auth_user_id", auth_user.user_id)
        .limit(1)
        .execute()
    )

    return {
        "auth_user_id": auth_user.user_id,
        "email": auth_user.email,
        "profile": result.data[0] if result.data else None,
    }


def _google_sheets_url(sheet_id: str, row_number: Any = None) -> str:
    base = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
    if isinstance(row_number, int):
        return f"{base}/edit#gid=0&range=A{row_number}"
    return base


def _google_calendar_url(calendar_id: str) -> str:
    return f"https://calendar.google.com/calendar/u/0/r?cid={calendar_id}"


def _client_value(row: dict[str, Any], key: str) -> str | None:
    value = row.get(key)
    if value in (None, ""):
        return None
    return str(value)


def _map_sheet_client(row: dict[str, Any], sheet_id: str) -> dict[str, Any]:
    full_name = _client_value(row, "Imię i nazwisko") or "Klient bez nazwy"
    city = _client_value(row, "Miasto") or "brak miasta"
    return {
        "id": f"sheet-row-{row.get('_row', full_name)}",
        "fullName": full_name,
        "city": city,
        "phone": _client_value(row, "Telefon"),
        "email": _client_value(row, "Email"),
        "address": _client_value(row, "Adres"),
        "product": _client_value(row, "Produkt"),
        "status": _client_value(row, "Status") or "Nowy lead",
        "notes": _client_value(row, "Notatki"),
        "lastContactAt": _client_value(row, "Data ostatniego kontaktu"),
        "nextAction": _client_value(row, "Następny krok"),
        "nextActionAt": _client_value(row, "Data następnego kroku"),
        "sheetsUrl": _google_sheets_url(sheet_id, row.get("_row")),
        "calendarUrl": None,
        "driveUrl": _client_value(row, "Link do zdjęć"),
    }


def _map_calendar_event(event: dict[str, Any], calendar_id: str) -> dict[str, Any]:
    title = str(event.get("title") or "")
    return {
        "id": str(event.get("id") or title),
        "clientId": None,
        "title": title,
        "clientName": title.split(":")[-1].strip() or title or "Wydarzenie",
        "city": None,
        "startsAt": event.get("start"),
        "endsAt": event.get("end"),
        "type": event.get("event_type") or "in_person",
        "location": event.get("location") or None,
        "calendarUrl": _google_calendar_url(calendar_id),
    }


async def _fetch_sheet_clients(user_id: str, sheet_id: str) -> list[dict[str, Any]]:
    rows = await get_all_clients(user_id)
    return [_map_sheet_client(row, sheet_id) for row in rows]


async def _fetch_calendar_events(user_id: str, calendar_id: str) -> list[dict[str, Any]]:
    start = datetime.now(tz=timezone.utc) - timedelta(days=7)
    end = datetime.now(tz=timezone.utc) + timedelta(days=30)
    events = await get_events_for_range(user_id, start, end)
    return [_map_calendar_event(event, calendar_id) for event in events]


@router.get("/dashboard/crm")
async def get_dashboard_crm(auth_user: AuthUser = Depends(get_current_auth_user)):
    user_result = (
        get_supabase_client()
        .table("users")
        .select("id, auth_user_id, google_sheets_id, google_calendar_id, google_drive_folder_id")
        .eq("auth_user_id", auth_user.user_id)
        .limit(1)
        .execute()
    )
    if not user_result.data:
        return {
            "fetchedAt": datetime.now(tz=timezone.utc).isoformat(),
            "clients": [],
            "events": [],
        }

    user = user_result.data[0]
    clients = []
    events = []
    if user.get("google_sheets_id"):
        clients = await _fetch_sheet_clients(user["id"], user["google_sheets_id"])
    if user.get("google_calendar_id"):
        events = await _fetch_calendar_events(user["id"], user["google_calendar_id"])

    return {
        "fetchedAt": datetime.now(tz=timezone.utc).isoformat(),
        "clients": clients,
        "events": events,
    }
