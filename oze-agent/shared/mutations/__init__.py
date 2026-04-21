"""Per-intent mutation pipelines.

Each module here wraps the Sheets + Calendar side effects for one MVP
mutation so bot handlers can stay in the presentation layer. Pipelines
return result dataclasses; the handler picks user-facing copy based on
the result flags. No user-facing strings in this module.
"""

from .add_meeting import (
    EVENT_TYPE_TO_NEXT_STEP_LABEL,
    STATUS_MEETING_AUTO_UPGRADE_FROM,
    STATUS_MEETING_BOOKED,
    STATUS_NEW_LEAD,
    AddMeetingResult,
    commit_add_meeting,
)
from .add_note import AddNoteResult, commit_add_note
from .change_status import ChangeStatusResult, commit_change_status

__all__ = [
    "AddMeetingResult",
    "AddNoteResult",
    "ChangeStatusResult",
    "EVENT_TYPE_TO_NEXT_STEP_LABEL",
    "STATUS_MEETING_AUTO_UPGRADE_FROM",
    "STATUS_MEETING_BOOKED",
    "STATUS_NEW_LEAD",
    "commit_add_meeting",
    "commit_add_note",
    "commit_change_status",
]
