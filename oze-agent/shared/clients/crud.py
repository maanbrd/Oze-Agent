"""CRUD wrappers for the clients domain.

Thin forwards over `shared.google_sheets` that isolate mutation pipelines
(Slices 5.2-5.5) from two implementation quirks of the sheets layer:

1. `update_client` always touches column J ("Data ostatniego kontaktu") —
   documented here so callers know the side effect is intentional per
   INTENCJE_MVP §4.2-4.5.
2. Both `add_client` and `update_client` mutate the dict they receive.
   We copy the caller's dict before forwarding so mutation pipelines can
   safely reuse their local inputs without aliasing surprises.

No `raw_update_client_row` (i.e. update without touching J) is exported
in Phase 5 — POST-MVP edit_client will add a dedicated implementation
when needed.
"""

from typing import Optional

from shared.google_sheets import add_client, get_all_clients, update_client


async def create_client_row(user_id: str, data: dict) -> Optional[int]:
    """Append a new client row. Returns the 1-indexed row number or None.

    Copies `data` before forwarding so the caller's dict is not mutated
    (google_sheets.add_client injects 'Data pierwszego kontaktu' if the
    caller did not supply one).
    """
    return await add_client(user_id, dict(data))


async def update_client_row_touching_contact(
    user_id: str,
    row: int,
    updates: dict,
) -> bool:
    """Update selected client fields AND auto-bump 'Data ostatniego kontaktu'.

    Every MVP mutation (add_note / change_status / add_meeting sync) must
    refresh column J per INTENCJE_MVP §4.2-4.5. google_sheets.update_client
    already appends today's date to the update payload; we wrap it so
    callers can opt-in by name and so the caller's dict is copied before
    forwarding.
    """
    return await update_client(user_id, row, dict(updates))


async def list_all_clients(user_id: str) -> list[dict]:
    """Passthrough over google_sheets.get_all_clients.

    Kept in the crud module so mutation pipelines depend on a single
    `shared.clients` surface instead of reaching through to
    `shared.google_sheets` directly.
    """
    return await get_all_clients(user_id)
