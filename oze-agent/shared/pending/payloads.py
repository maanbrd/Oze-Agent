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
    photo_upload: Optional[dict] = None


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
    client_updates: Optional[dict] = None
    event_type: Optional[str] = None
    status_update: Optional[dict] = None
    # Resolved by _enrich_meeting so handle_confirm can Sheets-sync without a
    # second lookup (Slice 5.1d). Legacy pendings missing these fall to the
    # safe not_found path; we never re-enter search_clients.
    client_row: Optional[int] = None
    current_status: Optional[str] = None
    ambiguous_client: bool = False


@dataclass
class DisambiguationPayload:
    intent: str
    note_text: Optional[str] = None
    new_status: Optional[str] = None


@dataclass
class R7PromptPayload:
    client_name: str
    city: str = ""
    # Slice 5.1d.1: resolved client context carried from the preceding
    # mutation confirm. Lets the R7 follow-up skip _enrich_meeting's lookup
    # and sync the add_meeting straight to the known row — Gate A no longer
    # flips to ambiguous when change_status/add_note already identified it.
    client_row: Optional[int] = None
    current_status: Optional[str] = None


@dataclass
class AddMeetingDisambiguationPayload:
    # Slice 5.1d.3: carries the full meeting spec when lookup_client returns
    # multi, so the user can pick a candidate before we show the confirm card.
    # On resume the selected candidate populates an AddMeetingPayload (upsert
    # by telegram_id PK) and standard confirm flow resumes. "Żaden z nich"
    # forwards the meeting with client_row=None so confirm goes not_found path.
    title: str
    start: str                                   # ISO datetime
    end: str                                     # ISO datetime
    client_name: str                             # original query (from intent / R7)
    location: str = ""                           # location_hint from the message
    description: str = ""                        # placeholder — rebuilt from selected client on resume
    event_type: Optional[str] = None
    status_update: Optional[dict] = None         # explicit compound (if any)
    source_client_data: Optional[dict] = None    # ADD_CLIENT pre-seed preserved for "Żaden z nich"
    # Minimal per-candidate dict: {"row": int, "full_name": str, "city": str, "current_status": str}
    candidates: list = field(default_factory=list)


PendingFlowPayload = Union[
    AddClientPayload,
    AddClientDuplicatePayload,
    AddNotePayload,
    ChangeStatusPayload,
    AddMeetingPayload,
    AddMeetingDisambiguationPayload,
    DisambiguationPayload,
    R7PromptPayload,
]


PAYLOAD_BY_FLOW_TYPE: dict[PendingFlowType, type] = {
    PendingFlowType.ADD_CLIENT: AddClientPayload,
    PendingFlowType.ADD_CLIENT_DUPLICATE: AddClientDuplicatePayload,
    PendingFlowType.ADD_NOTE: AddNotePayload,
    PendingFlowType.CHANGE_STATUS: ChangeStatusPayload,
    PendingFlowType.ADD_MEETING: AddMeetingPayload,
    PendingFlowType.ADD_MEETING_DISAMBIGUATION: AddMeetingDisambiguationPayload,
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
