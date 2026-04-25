"""add_meeting pipeline — ordered Calendar → Sheets write with partial-success semantics.

Not an "atomic" pipeline: Calendar creates first (K/L/P sync on the client
row needs the returned event_id), and Sheets sync follows only when a
resolvable sync_row is supplied. Partial success (Calendar OK, Sheets
fail) returns success=True with sheets_synced=False so the handler can
render the matching Polish copy.

Three control fields on the result carry the Sheets-side outcome:
  sheets_attempted — True iff the pipeline tried to write to Sheets
  sheets_synced    — True iff attempt succeeded
  sheets_error     — taxonomy key when attempted AND failed

Calendar-only (client_row=None + no compound status_update.row) leaves
sheets_attempted=False; it is NOT an error. The handler distinguishes
not_found (pre-seed ADD_CLIENT) from ambiguous (Gate A message) based
on flow_data it already has, not on pipeline result.

Copy and R7 stay in the handler. This module is user-string-free.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from shared.clients import update_client_row_touching_contact
from shared.google_calendar import create_event


# ── Shared constants (imported by handler for the pre-confirm card path) ──────

STATUS_NEW_LEAD = "Nowy lead"
STATUS_MEETING_BOOKED = "Spotkanie umówione"
# "" covers newly-created rows that landed in ADD_CLIENT without a status yet.
STATUS_MEETING_AUTO_UPGRADE_FROM = {"", STATUS_NEW_LEAD}

EVENT_TYPE_TO_NEXT_STEP_LABEL = {
    "in_person": "Spotkanie",
    "phone_call": "Telefon",
    "offer_email": "Wysłać ofertę",
    "doc_followup": "Follow-up dokumentowy",
}


# ── Result dataclass ─────────────────────────────────────────────────────────


@dataclass
class AddMeetingResult:
    success: bool                                # False iff Calendar step failed
    error_message: Optional[str] = None          # taxonomy key when success=False
    calendar_event_id: Optional[str] = None

    # Three-state Sheets outcome (do not conflate with success):
    sheets_attempted: bool = False
    sheets_synced: bool = False
    sheets_error: Optional[str] = None           # taxonomy key when attempted AND not synced

    # Status update info — handler reads to pick "Status klienta: X." copy.
    status_updated: bool = False
    status_new_value: Optional[str] = None


# ── Pipeline ─────────────────────────────────────────────────────────────────


async def commit_add_meeting(
    user_id: str,
    title: str,
    start: datetime,
    end: datetime,
    event_type: str,
    location: str,
    description: str,
    client_row: Optional[int],
    *,
    today: date,
    client_current_status: Optional[str] = None,
    status_update: Optional[dict] = None,
) -> AddMeetingResult:
    """Create the Calendar event and (if a client row is resolvable) sync
    K/L/P/F on that row.

    Compound-row rule: a non-null status_update["row"] overrides client_row.
    This prevents split-row bugs where the prior change_status confirm
    already picked row X but enrichment/disambiguation produced row Y.

    Auto-upgrade fires only when event_type == "in_person" AND
    client_current_status is in STATUS_MEETING_AUTO_UPGRADE_FROM
    (covers both "Nowy lead" and empty-status rows) AND the caller did
    NOT pass a compound status_update.new_value.

    today is accepted for API consistency with commit_add_note /
    commit_change_status / commit_add_client. commit_add_meeting does
    NOT use it to set column J — J is bumped automatically inside
    update_client_row_touching_contact. Callers must NOT use today to
    stamp J or any other column manually.
    """
    # Step 1: Calendar
    event = await create_event(
        user_id,
        title=title,
        start=start,
        end=end,
        location=location or None,
        description=description or None,
        event_type=event_type,
    )
    if not event:
        return AddMeetingResult(
            success=False,
            error_message="calendar_down",
        )

    calendar_event_id = event.get("id")

    # Step 2: Resolve sync_row via compound-wins rule.
    sync_row: Optional[int] = None
    if status_update and status_update.get("row"):
        sync_row = status_update["row"]
    elif client_row:
        sync_row = client_row

    if sync_row is None:
        # Calendar-only: handler decides not_found pre-seed vs ambiguous fallback
        return AddMeetingResult(
            success=True,
            calendar_event_id=calendar_event_id,
            sheets_attempted=False,
        )

    # Step 3: Build Sheets payload
    sheet_updates: dict = {
        "Następny krok": EVENT_TYPE_TO_NEXT_STEP_LABEL.get(event_type, "Spotkanie"),
        "Data następnego kroku": start.isoformat(),
    }
    if calendar_event_id:
        sheet_updates["ID wydarzenia Kalendarz"] = calendar_event_id

    status_updated = False
    status_new_value: Optional[str] = None
    compound_new_value = status_update.get("new_value") if status_update else None
    if compound_new_value:
        # Compound (explicit from prior change_status) wins over auto-upgrade.
        sheet_updates[status_update.get("field", "Status")] = compound_new_value
        status_updated = True
        status_new_value = compound_new_value
    else:
        current = (client_current_status or "").strip()
        if event_type == "in_person" and current in STATUS_MEETING_AUTO_UPGRADE_FROM:
            sheet_updates["Status"] = STATUS_MEETING_BOOKED
            status_updated = True
            status_new_value = STATUS_MEETING_BOOKED

    # Step 4: Sheets write (touching wrapper bumps column J automatically)
    ok = await update_client_row_touching_contact(user_id, sync_row, sheet_updates)
    if not ok:
        return AddMeetingResult(
            success=True,
            calendar_event_id=calendar_event_id,
            sheets_attempted=True,
            sheets_synced=False,
            sheets_error="google_down",
            # On Sheets failure status did not actually land in the column —
            # but we still report it here so the handler can decide whether
            # to mention it. Current handler contract: "partial" copy trumps
            # "Status klienta: X." copy, so status_updated remains False.
        )

    return AddMeetingResult(
        success=True,
        calendar_event_id=calendar_event_id,
        sheets_attempted=True,
        sheets_synced=True,
        status_updated=status_updated,
        status_new_value=status_new_value,
    )
