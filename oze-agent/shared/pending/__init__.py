"""Typed pending-flow contract for OZE-Agent.

Standalone module — not wired into bot handlers yet. Wraps the legacy
`save_pending_flow` / `get_pending_flow` / `delete_pending_flow` helpers
in `shared.database` with a typed surface (enum + dataclass).
"""

from .payloads import (
    PAYLOAD_BY_FLOW_TYPE,
    AddClientDuplicatePayload,
    AddClientPayload,
    AddMeetingDisambiguationPayload,
    AddMeetingPayload,
    AddNotePayload,
    ChangeStatusPayload,
    DisambiguationPayload,
    PendingFlowPayload,
    R7PromptPayload,
    payload_from_flow_data,
    payload_to_flow_data,
)
from .store import delete, get, save
from .types import PendingFlow, PendingFlowType

__all__ = [
    "AddClientDuplicatePayload",
    "AddClientPayload",
    "AddMeetingDisambiguationPayload",
    "AddMeetingPayload",
    "AddNotePayload",
    "ChangeStatusPayload",
    "DisambiguationPayload",
    "PAYLOAD_BY_FLOW_TYPE",
    "PendingFlow",
    "PendingFlowPayload",
    "PendingFlowType",
    "R7PromptPayload",
    "delete",
    "get",
    "payload_from_flow_data",
    "payload_to_flow_data",
    "save",
]
