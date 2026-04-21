"""change_status pipeline — Sheets-only F+J write. No Calendar, no R7.

Per INTENCJE_MVP §4.4 a status change rewrites column F ("Status") and
bumps column J ("Data ostatniego kontaktu"). R7 ("Co dalej?") follow-up
is a UX concern that lives in the handler layer — compound flows can
suppress it without teaching the pipeline about next-step UX.

Old status is a handler concern (already available in flow_data for the
comparison card), so the result dataclass stays minimal.
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional

from shared.clients import update_client_row_touching_contact


@dataclass
class ChangeStatusResult:
    success: bool
    error_message: Optional[str] = None          # taxonomy key, e.g. "google_down"


async def commit_change_status(
    user_id: str,
    row: int,
    new_status: str,
    today: date,
) -> ChangeStatusResult:
    """Write column F (Status) and bump column J via the touching wrapper.

    Returns ChangeStatusResult(success=True) or
    ChangeStatusResult(success=False, error_message="google_down").
    """
    ok = await update_client_row_touching_contact(
        user_id, row, {"Status": new_status}
    )
    if not ok:
        return ChangeStatusResult(success=False, error_message="google_down")
    return ChangeStatusResult(success=True)
