"""Deterministic contract for add_meeting -> add_client handoff.

The LLM can carry useful contact details into the handoff, but it must not
decide the CRM state produced by a confirmed Calendar-backed meeting.
"""

from datetime import datetime
from typing import Iterable, Optional

from .add_meeting import (
    STATUS_MEETING_BOOKED,
    format_next_step_date_for_sheets,
)
from shared.behavior.action_type import action_label


IMPORTANT_MISSING_CLIENT_FIELDS = (
    "Telefon",
    "Email",
    "Adres",
    "Produkt",
    "Źródło pozyskania",
)


def _has_value(value: object) -> bool:
    return bool(str(value or "").strip())


def canonical_missing_client_fields(
    sheet_columns: Iterable[str] | None,
    client_data: dict,
) -> list[str]:
    """Return only optional-but-important missing fields for add_client cards."""
    available = set(sheet_columns or [])
    fields = [
        field
        for field in IMPORTANT_MISSING_CLIENT_FIELDS
        if not available or field in available
    ]
    return [field for field in fields if not _has_value(client_data.get(field))]


def build_meeting_seeded_client_data(
    *,
    client_data: dict,
    client_name: str,
    event_type: str,
    start: datetime,
    calendar_event_id: Optional[str],
) -> dict:
    """Build canonical client_data for a new client created from a meeting.

    Contact/product facts from extraction are preserved, while meeting-owned
    fields are overwritten from the confirmed Calendar event.
    """
    draft = {key: value for key, value in (client_data or {}).items() if _has_value(value)}
    if _has_value(client_name):
        draft["Imię i nazwisko"] = client_name

    if event_type == "in_person":
        draft["Status"] = STATUS_MEETING_BOOKED

    draft["Następny krok"] = action_label(event_type)
    draft["Data następnego kroku"] = format_next_step_date_for_sheets(start)
    if _has_value(calendar_event_id):
        draft["ID wydarzenia Kalendarz"] = calendar_event_id
    else:
        draft.pop("ID wydarzenia Kalendarz", None)
    return draft
