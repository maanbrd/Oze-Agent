"""Intent router data model: enums and result dataclass."""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class IntentType(str, Enum):
    ADD_CLIENT = "add_client"
    SHOW_CLIENT = "show_client"
    ADD_NOTE = "add_note"
    CHANGE_STATUS = "change_status"
    ADD_MEETING = "add_meeting"
    SHOW_DAY_PLAN = "show_day_plan"
    GENERAL_QUESTION = "general_question"
    POST_MVP_ROADMAP = "post_mvp_roadmap"
    VISION_ONLY = "vision_only"
    UNPLANNED = "unplanned"
    MULTI_MEETING = "multi_meeting"


class ScopeTier(str, Enum):
    MVP = "mvp"
    POST_MVP_ROADMAP = "post_mvp_roadmap"
    VISION_ONLY = "vision_only"
    UNPLANNED = "unplanned"
    REJECTED = "rejected"


@dataclass
class IntentResult:
    intent: IntentType
    scope_tier: ScopeTier
    entities: dict = field(default_factory=dict)
    confidence: float = 0.0
    feature_key: Optional[str] = None
    reason: Optional[str] = None
    model: Optional[str] = None
