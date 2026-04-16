"""Typed payloads for the seven MVP pending-flow types.

Field names mirror the live `flow_data` shapes saved by
`bot/handlers/text.py` and `bot/handlers/buttons.py` verbatim — including
`AddClientPayload._offer_remaining` (leading underscore is the legacy
key, not a privacy convention).

Validation is intentionally light. Extra keys present in `flow_data` are
silently dropped on `payload_from_flow_data(...)` so the typed surface
is no stricter than current runtime; missing required fields raise
`TypeError` from the dataclass constructor.
"""

import dataclasses
import logging
from dataclasses import dataclass, field
from typing import Optional, Union

from .types import PendingFlowType

logger = logging.getLogger(__name__)


@dataclass
class AddClientPayload:
    client_data: dict
    _offer_remaining: Optional[list] = None


@dataclass
class AddClientDuplicatePayload:
    client_data: dict
    duplicate_row: int
    client_name: str
    city: str


@dataclass
class AddNotePayload:
    row: int
    note_text: str
    client_name: str
    city: str = ""
    old_notes: str = ""


@dataclass
class ChangeStatusPayload:
    row: int
    new_value: str
    client_name: str
    field: str = "Status"
    old_value: str = ""
    city: str = ""


@dataclass
class AddMeetingPayload:
    title: str
    start: str
    end: str
    client_name: str
    location: str = ""
    description: str = ""
    client_data: Optional[dict] = None
    event_type: Optional[str] = None
    status_update: Optional[dict] = None


@dataclass
class DisambiguationPayload:
    intent: str
    note_text: Optional[str] = None
    new_status: Optional[str] = None


@dataclass
class R7PromptPayload:
    client_name: str
    city: str = ""


PendingFlowPayload = Union[
    AddClientPayload,
    AddClientDuplicatePayload,
    AddNotePayload,
    ChangeStatusPayload,
    AddMeetingPayload,
    DisambiguationPayload,
    R7PromptPayload,
]


PAYLOAD_BY_FLOW_TYPE: dict[PendingFlowType, type] = {
    PendingFlowType.ADD_CLIENT: AddClientPayload,
    PendingFlowType.ADD_CLIENT_DUPLICATE: AddClientDuplicatePayload,
    PendingFlowType.ADD_NOTE: AddNotePayload,
    PendingFlowType.CHANGE_STATUS: ChangeStatusPayload,
    PendingFlowType.ADD_MEETING: AddMeetingPayload,
    PendingFlowType.DISAMBIGUATION: DisambiguationPayload,
    PendingFlowType.R7_PROMPT: R7PromptPayload,
}


def payload_from_flow_data(
    flow_type: PendingFlowType, flow_data: dict
) -> PendingFlowPayload:
    cls = PAYLOAD_BY_FLOW_TYPE[flow_type]
    field_names = {f.name for f in dataclasses.fields(cls)}
    known = {k: v for k, v in flow_data.items() if k in field_names}
    dropped = set(flow_data) - field_names
    if dropped:
        logger.debug(
            "payload_from_flow_data(%s): dropped legacy keys %s",
            flow_type.value,
            sorted(dropped),
        )
    return cls(**known)


def payload_to_flow_data(payload: PendingFlowPayload) -> dict:
    return {k: v for k, v in dataclasses.asdict(payload).items() if v is not None}
