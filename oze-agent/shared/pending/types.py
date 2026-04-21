"""Pending-flow data model: enum + dataclass."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class PendingFlowType(str, Enum):
    ADD_CLIENT = "add_client"
    ADD_CLIENT_DUPLICATE = "add_client_duplicate"
    ADD_NOTE = "add_note"
    CHANGE_STATUS = "change_status"
    ADD_MEETING = "add_meeting"
    ADD_MEETING_DISAMBIGUATION = "add_meeting_disambiguation"
    DISAMBIGUATION = "disambiguation"
    R7_PROMPT = "r7_prompt"


@dataclass
class PendingFlow:
    telegram_id: int
    flow_type: PendingFlowType
    flow_data: dict = field(default_factory=dict)
    created_at: Optional[datetime] = None
