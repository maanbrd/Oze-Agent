"""Decisions API routes — web-driven mutations for /dashboard/decyzje-preview.

Per docs/agent_behavior_spec_v5.md R1.web (added in this PR), the web layer
can mutate three specific CRM fields directly from explicit user clicks
(no Telegram confirmation card). This module exposes:

  GET  /api/decisions/pending           — list of clients qualifying as "stale"
  GET  /api/decisions/count             — count for sidebar badge
  POST /api/decisions/change-status     — Status (F) + auto-derive K/L
  POST /api/decisions/touch-contact     — bump Data ostatniego kontaktu (J)
  POST /api/decisions/schedule-call     — Calendar event + K/L/P sync

All mutations reuse existing Python pipelines:
  shared.mutations.commit_change_status
  shared.clients.update_client_row_touching_contact (touching wrapper)
  shared.mutations.commit_add_meeting (event_type="phone_call", 15-min)
  shared.google_calendar.delete_event
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from zoneinfo import ZoneInfo

from api.auth import AuthUser, get_current_auth_user
from shared.clients import update_client_row_touching_contact
from shared.database import get_supabase_client
from shared.google_calendar import delete_event
from shared.google_sheets import get_all_clients
from shared.mutations import commit_add_meeting, commit_change_status

router = APIRouter()

# ── Constants ─────────────────────────────────────────────────────────────────

WARSAW_TZ = ZoneInfo("Europe/Warsaw")

OPEN_STATUSES: set[str] = {
    "Nowy lead",
    "Spotkanie umówione",
    "Spotkanie odbyte",
    "Oferta wysłana",
    "Podpisane",
}

# Listed clients on /api/decisions/pending: open status AND no contact in 7+ days.
STALENESS_DAYS = 7

# Auto-derive K (Następny krok) and L (Data następnego kroku) when the user
# clicks the "happy" transition button. Key = the *new* status (the one we
# transition INTO). Out / Stay decisions do not touch K/L. "Nowy lead" →
# "Spotkanie umówione" leaves K/L empty (the salesperson sets the actual
# meeting date by other means). Terminal "Zamontowana" leaves K/L empty too.
NEXT_STEP_AFTER_STATUS: dict[str, tuple[str, int]] = {
    "Spotkanie odbyte": ("Wysłać ofertę", 3),
    "Oferta wysłana": ("Zapytać o decyzję", 7),
    "Podpisane": ("Zaplanować montaż", 14),
}

ALL_STATUSES: set[str] = {
    "Nowy lead",
    "Spotkanie umówione",
    "Spotkanie odbyte",
    "Oferta wysłana",
    "Podpisane",
    "Zamontowana",
    "Rezygnacja z umowy",
    "Nieaktywny",
    "Odrzucone",
}


# ── Request / response models ─────────────────────────────────────────────────


class ChangeStatusRequest(BaseModel):
    row: int = Field(..., ge=2, description="Sheets 1-based row number (data starts at row 2).")
    new_status: str = Field(..., description="Target status — must be one of the 9 funnel states.")


class TouchContactRequest(BaseModel):
    row: int = Field(..., ge=2)


class ScheduleCallRequest(BaseModel):
    row: int = Field(..., ge=2)
    date: str = Field(..., description="ISO date YYYY-MM-DD (Warsaw local date).")
    time: str = Field(..., description="HH:MM (Warsaw local time).")
    note: str = Field("", description="Free-text note inserted into Calendar event description.")
    mode: str = Field("create", description="One of: create | overwrite | cancel-only.")


class DecisionResult(BaseModel):
    success: bool
    error_code: Optional[str] = None


class ScheduleCallResult(BaseModel):
    success: bool
    error_code: Optional[str] = None
    event_id: Optional[str] = None
    sheets_synced: bool = False


# ── Helpers ───────────────────────────────────────────────────────────────────


def _resolve_user_record(auth_user: AuthUser) -> dict[str, Any]:
    """Fetch the internal users-table row (returns {} on 'not onboarded yet')."""
    result = (
        get_supabase_client()
        .table("users")
        .select("id, auth_user_id, google_sheets_id, google_calendar_id, google_drive_folder_id")
        .eq("auth_user_id", auth_user.user_id)
        .limit(1)
        .execute()
    )
    if not result.data:
        return {}
    return result.data[0]


def _require_user_with_sheets(auth_user: AuthUser) -> dict[str, Any]:
    record = _resolve_user_record(auth_user)
    if not record or not record.get("google_sheets_id"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="user_not_onboarded",
        )
    return record


def _today_warsaw() -> date:
    return datetime.now(tz=WARSAW_TZ).date()


def _parse_iso_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _is_decision_pending(row: dict[str, Any], today: date) -> bool:
    """Open funnel status AND no contact in STALENESS_DAYS+ days.

    A client with empty 'Data ostatniego kontaktu' is treated as stale —
    the very fact that the date is missing means we have no proof of recent
    activity, which is exactly the "needs attention" case we want to flag.
    """
    status_value = (row.get("Status") or "").strip() or "Nowy lead"
    if status_value not in OPEN_STATUSES:
        return False
    last = _parse_iso_date(row.get("Data ostatniego kontaktu"))
    if last is None:
        return True
    return (today - last).days >= STALENESS_DAYS


def _stale_days(row: dict[str, Any], today: date) -> int:
    """How many days since 'Data ostatniego kontaktu'. Defaults to STALENESS_DAYS for empty."""
    last = _parse_iso_date(row.get("Data ostatniego kontaktu"))
    if last is None:
        return STALENESS_DAYS
    return max(0, (today - last).days)


def _client_str(row: dict[str, Any], key: str) -> Optional[str]:
    value = row.get(key)
    if value in (None, ""):
        return None
    return str(value)


def _serialize_client(row: dict[str, Any], today: date) -> dict[str, Any]:
    """Shape used by /api/decisions/pending. Mirrors web/lib/crm/types.ts CrmClient
    plus two extra fields the prototype card needs:
      staleDays            — for the badge color and sort order
      calendarEventId      — for the re-schedule confirmation modal (kolumna P)
    """
    full_name = _client_str(row, "Imię i nazwisko") or "Klient bez nazwy"
    return {
        "id": f"sheet-row-{row.get('_row', full_name)}",
        "row": row.get("_row"),
        "fullName": full_name,
        "city": _client_str(row, "Miasto") or "brak miasta",
        "phone": _client_str(row, "Telefon"),
        "email": _client_str(row, "Email"),
        "address": _client_str(row, "Adres"),
        "product": _client_str(row, "Produkt"),
        "status": _client_str(row, "Status") or "Nowy lead",
        "notes": _client_str(row, "Notatki"),
        "lastContactAt": _client_str(row, "Data ostatniego kontaktu"),
        "nextAction": _client_str(row, "Następny krok"),
        "nextActionAt": _client_str(row, "Data następnego kroku"),
        "calendarEventId": _client_str(row, "ID wydarzenia Kalendarz"),
        "staleDays": _stale_days(row, today),
    }


def _find_client_row(rows: list[dict[str, Any]], row_number: int) -> Optional[dict[str, Any]]:
    for row in rows:
        if row.get("_row") == row_number:
            return row
    return None


def _format_call_description(row: dict[str, Any], note: str) -> str:
    """Build the Calendar event description for a scheduled phone call.

    Includes every CRM field that helps the salesperson make the call without
    flipping back to Sheets. Empty values are skipped.
    """
    fields: list[tuple[str, Optional[str]]] = [
        ("📋 Klient", _client_str(row, "Imię i nazwisko")),
        ("📍 Miasto", _client_str(row, "Miasto")),
        ("🏠 Adres", _client_str(row, "Adres")),
        ("📞 Telefon", _client_str(row, "Telefon")),
        ("✉️ Email", _client_str(row, "Email")),
        ("⚡ Produkt", _client_str(row, "Produkt")),
        ("🎯 Status", _client_str(row, "Status")),
        ("📝 Notatki w CRM", _client_str(row, "Notatki")),
    ]
    lines = [f"{label}: {value}" for label, value in fields if value]
    if note.strip():
        lines.append("")
        lines.append("📌 Cel telefonu:")
        lines.append(note.strip())
    return "\n".join(lines)


def _validate_status(value: str) -> str:
    if value not in ALL_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"unknown_status:{value}",
        )
    return value


def _parse_warsaw_datetime(date_str: str, time_str: str) -> datetime:
    try:
        d = date.fromisoformat(date_str)
        t = time.fromisoformat(time_str)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"bad_datetime:{exc}",
        ) from exc
    return datetime.combine(d, t, tzinfo=WARSAW_TZ)


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get("/decisions/pending")
async def get_pending_decisions(auth_user: AuthUser = Depends(get_current_auth_user)) -> dict[str, Any]:
    """Clients qualifying as 'wymagają decyzji' — open status + stale > 7 days.

    Sorted by stale days desc, then by full name. Returns max 50 clients —
    if the salesperson somehow has more, they have bigger problems than UI lag.
    """
    record = _resolve_user_record(auth_user)
    today = _today_warsaw()
    if not record or not record.get("google_sheets_id"):
        return {
            "fetchedAt": datetime.now(tz=timezone.utc).isoformat(),
            "today": today.isoformat(),
            "count": 0,
            "clients": [],
            "source": "unavailable",
        }

    rows = await get_all_clients(record["id"])
    pending = [r for r in rows if _is_decision_pending(r, today)]
    pending.sort(key=lambda r: (-_stale_days(r, today), _client_str(r, "Imię i nazwisko") or ""))
    serialized = [_serialize_client(r, today) for r in pending[:50]]
    return {
        "fetchedAt": datetime.now(tz=timezone.utc).isoformat(),
        "today": today.isoformat(),
        "count": len(pending),
        "clients": serialized,
        "source": "live",
    }


@router.get("/decisions/count")
async def get_pending_decisions_count(
    auth_user: AuthUser = Depends(get_current_auth_user),
) -> dict[str, Any]:
    """Cheap count for sidebar badge. Same staleness rule as /pending."""
    record = _resolve_user_record(auth_user)
    if not record or not record.get("google_sheets_id"):
        return {"count": 0}

    today = _today_warsaw()
    rows = await get_all_clients(record["id"])
    return {"count": sum(1 for r in rows if _is_decision_pending(r, today))}


@router.post("/decisions/change-status", response_model=DecisionResult)
async def post_change_status(
    body: ChangeStatusRequest,
    auth_user: AuthUser = Depends(get_current_auth_user),
) -> DecisionResult:
    new_status = _validate_status(body.new_status)
    record = _require_user_with_sheets(auth_user)
    user_id = record["id"]
    today = _today_warsaw()

    result = await commit_change_status(user_id, body.row, new_status, today=today)
    if not result.success:
        return DecisionResult(success=False, error_code=result.error_message or "google_down")

    # Auto-derive K/L for "happy" transitions only.
    next_step_pair = NEXT_STEP_AFTER_STATUS.get(new_status)
    if next_step_pair is not None:
        next_step_label, days_offset = next_step_pair
        next_step_date = (today + timedelta(days=days_offset)).isoformat()
        ok = await update_client_row_touching_contact(
            user_id,
            body.row,
            {
                "Następny krok": next_step_label,
                "Data następnego kroku": next_step_date,
            },
        )
        if not ok:
            # Status already landed in column F; only K/L missed.
            return DecisionResult(success=False, error_code="next_step_sync_failed")

    return DecisionResult(success=True)


@router.post("/decisions/touch-contact", response_model=DecisionResult)
async def post_touch_contact(
    body: TouchContactRequest,
    auth_user: AuthUser = Depends(get_current_auth_user),
) -> DecisionResult:
    """'Stay / Nadal czeka' — bump column J only, no other changes."""
    record = _require_user_with_sheets(auth_user)
    ok = await update_client_row_touching_contact(record["id"], body.row, {})
    if not ok:
        return DecisionResult(success=False, error_code="google_down")
    return DecisionResult(success=True)


@router.post("/decisions/schedule-call", response_model=ScheduleCallResult)
async def post_schedule_call(
    body: ScheduleCallRequest,
    auth_user: AuthUser = Depends(get_current_auth_user),
) -> ScheduleCallResult:
    """Create / overwrite / cancel a 15-min Calendar phone call appointment.

    Always re-fetches the current row from Sheets to (a) read 'ID wydarzenia
    Kalendarz' for delete operations and (b) build the full description from
    live data — we never trust whatever the client snapshot says about column P.
    """
    if body.mode not in {"create", "overwrite", "cancel-only"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"bad_mode:{body.mode}",
        )

    record = _require_user_with_sheets(auth_user)
    user_id = record["id"]
    today = _today_warsaw()

    rows = await get_all_clients(user_id)
    client_row = _find_client_row(rows, body.row)
    if client_row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"client_row_not_found:{body.row}",
        )
    existing_event_id = _client_str(client_row, "ID wydarzenia Kalendarz")

    # ── Mode: cancel-only ─────────────────────────────────────────────────────
    if body.mode == "cancel-only":
        if not existing_event_id:
            return ScheduleCallResult(success=False, error_code="nothing_to_cancel")
        deleted = await delete_event(user_id, existing_event_id)
        ok = await update_client_row_touching_contact(
            user_id,
            body.row,
            {
                "Następny krok": "",
                "Data następnego kroku": "",
                "ID wydarzenia Kalendarz": "",
            },
        )
        if not ok:
            return ScheduleCallResult(
                success=False,
                error_code="sheets_clear_failed" if deleted else "delete_and_clear_failed",
            )
        return ScheduleCallResult(success=True, sheets_synced=True)

    # ── Mode: overwrite (delete old then fall through to create) ──────────────
    if body.mode == "overwrite":
        if existing_event_id:
            deleted = await delete_event(user_id, existing_event_id)
            if not deleted:
                # Soft fail: log via logger but don't abort — handler may want
                # to push the new event regardless. Surface a distinct code so
                # the UI can show "stary event mógł zostać".
                pass

    # ── Mode: create (or fallthrough from overwrite) ──────────────────────────
    start_dt = _parse_warsaw_datetime(body.date, body.time)
    end_dt = start_dt + timedelta(minutes=15)
    full_name = _client_str(client_row, "Imię i nazwisko") or "Klient"
    title = f"📞 Telefon — {full_name}"
    description = _format_call_description(client_row, body.note)

    result = await commit_add_meeting(
        user_id=user_id,
        title=title,
        start=start_dt,
        end=end_dt,
        event_type="phone_call",
        location="",
        description=description,
        client_row=body.row,
        today=today,
    )

    if not result.success:
        return ScheduleCallResult(
            success=False,
            error_code=result.error_message or "calendar_down",
        )

    return ScheduleCallResult(
        success=True,
        event_id=result.calendar_event_id,
        sheets_synced=result.sheets_synced,
        error_code=result.sheets_error if not result.sheets_synced else None,
    )
