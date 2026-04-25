"""add_client pipeline — Sheets-only writes (no Calendar).

Two operations in one module:

- `commit_add_client`: append a new client row (duplicate-aware handler
  path is out of scope; that routing decision is made before this call).
- `commit_update_client_fields`: touch-contact update of selected fields
  for the duplicate-merge path (INTENCJE_MVP §4.2–4.5 — column J always
  bumps automatically via update_client_row_touching_contact).

Both operations return dataclass results with an error_message taxonomy
key ("google_down") on failure; the pipeline does not assemble any
user-facing strings.
"""

from dataclasses import dataclass
from typing import Optional

from shared.clients import create_client_row, update_client_row_touching_contact


@dataclass
class AddClientResult:
    success: bool
    row: Optional[int] = None
    error_message: Optional[str] = None          # "google_down" on Sheets fail


@dataclass
class UpdateClientFieldsResult:
    success: bool
    error_message: Optional[str] = None          # "google_down" on Sheets fail


async def commit_add_client(
    user_id: str,
    client_data: dict,
) -> AddClientResult:
    """Append a new client row to Sheets.

    `create_client_row` already copies the dict before forwarding
    (shared/clients/crud.py), so callers can safely reuse their local
    inputs. Column I ("Data pierwszego kontaktu") is auto-populated by
    google_sheets.add_client; F ("Status") / J ("Data ostatniego
    kontaktu") stay untouched unless the caller supplied them.
    """
    row = await create_client_row(user_id, client_data)
    if row is None:
        return AddClientResult(success=False, error_message="google_down")
    return AddClientResult(success=True, row=row)


async def commit_update_client_fields(
    user_id: str,
    row: int,
    updates: dict,
) -> UpdateClientFieldsResult:
    """Touch-contact update of selected client fields (duplicate-merge path).

    Column J ("Data ostatniego kontaktu") bumps automatically via
    update_client_row_touching_contact per INTENCJE_MVP §4.2-4.5 — the
    caller does not need to pass it explicitly.
    """
    ok = await update_client_row_touching_contact(user_id, row, updates)
    if not ok:
        return UpdateClientFieldsResult(success=False, error_message="google_down")
    return UpdateClientFieldsResult(success=True)
