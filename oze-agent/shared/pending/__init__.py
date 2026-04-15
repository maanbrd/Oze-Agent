"""Typed pending-flow contract for OZE-Agent.

Standalone module — not wired into bot handlers yet. Wraps the legacy
`save_pending_flow` / `get_pending_flow` / `delete_pending_flow` helpers
in `shared.database` with a typed surface (enum + dataclass).
"""

from .store import delete, get, save
from .types import PendingFlow, PendingFlowType

__all__ = ["PendingFlow", "PendingFlowType", "delete", "get", "save"]
