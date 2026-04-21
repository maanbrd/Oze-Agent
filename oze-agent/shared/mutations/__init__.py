"""Per-intent mutation pipelines.

Each module here wraps the Sheets + Calendar side effects for one MVP
mutation so bot handlers can stay in the presentation layer. Pipelines
return result dataclasses; the handler picks user-facing copy based on
the result flags. No user-facing strings in this module.
"""

from .add_note import AddNoteResult, commit_add_note

__all__ = [
    "AddNoteResult",
    "commit_add_note",
]
