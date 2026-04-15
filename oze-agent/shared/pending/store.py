"""Typed wrapper over the legacy pending-flow DB helpers.

Every function delegates to `shared.database` — no new DB calls, no schema
change. Unknown / POST-MVP `flow_type` values fall through `get()` as `None`
so callers needing those still use the raw wrappers.
"""

import logging
from datetime import datetime
from typing import Optional

from shared.database import (
    delete_pending_flow,
    get_pending_flow,
    save_pending_flow,
)

from .types import PendingFlow, PendingFlowType

logger = logging.getLogger(__name__)


def save(flow: PendingFlow) -> None:
    save_pending_flow(flow.telegram_id, flow.flow_type.value, flow.flow_data)


def get(telegram_id: int) -> Optional[PendingFlow]:
    row = get_pending_flow(telegram_id)
    if not row:
        return None
    raw_type = row.get("flow_type")
    try:
        flow_type = PendingFlowType(raw_type)
    except ValueError:
        logger.debug(
            "get(%s): flow_type %r outside typed contract", telegram_id, raw_type
        )
        return None
    created_raw = row.get("created_at")
    created_at = (
        datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
        if created_raw
        else None
    )
    return PendingFlow(
        telegram_id=row["telegram_id"],
        flow_type=flow_type,
        flow_data=row.get("flow_data") or {},
        created_at=created_at,
    )


def delete(telegram_id: int) -> None:
    delete_pending_flow(telegram_id)
