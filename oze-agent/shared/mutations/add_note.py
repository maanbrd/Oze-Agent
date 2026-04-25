"""add_note pipeline — single Sheets write, no Calendar.

Per INTENCJE_MVP §4.3 a clean note is a closed act: we append one dated
history entry to column H ("Notatki") and bump column J ("Data ostatniego
kontaktu"). No R7 follow-up, no Calendar event.

The dated entry format `[DD.MM.YYYY]: text` (with a colon after the date)
is a hard contract — existing handler copy test_plans and user history
rely on it.
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional

from shared.clients import update_client_row_touching_contact


@dataclass
class AddNoteResult:
    success: bool
    error_message: Optional[str] = None          # taxonomy key, e.g. "google_down"
    final_notes: Optional[str] = None            # full column H value written


def _format_note_entry(note_text: str, today: date) -> str:
    """Single history entry: `[DD.MM.YYYY]: text` — colon is required."""
    return f"[{today.strftime('%d.%m.%Y')}]: {note_text}"


def _merge_with_existing(existing: str, entry: str) -> str:
    return f"{existing}; {entry}" if existing else entry


async def commit_add_note(
    user_id: str,
    row: int,
    note_text: str,
    existing_notes: str,
    today: date,
) -> AddNoteResult:
    """Append a dated note to column H for the given client row.

    Column J is bumped automatically via update_client_row_touching_contact
    — callers don't need to pass 'Data ostatniego kontaktu' explicitly.

    Returns AddNoteResult(success=True, final_notes=...) on success or
    AddNoteResult(success=False, error_message="google_down") when the
    sheets write fails. The handler maps error_message → format_error(...)
    copy; the pipeline itself stays Polish-string-free.
    """
    entry = _format_note_entry(note_text, today)
    final_notes = _merge_with_existing(existing_notes, entry)
    ok = await update_client_row_touching_contact(
        user_id, row, {"Notatki": final_notes}
    )
    if not ok:
        return AddNoteResult(success=False, error_message="google_down")
    return AddNoteResult(success=True, final_notes=final_notes)
