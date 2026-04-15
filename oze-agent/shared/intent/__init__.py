"""Structured intent router for OZE-Agent.

Standalone module — not wired into bot handlers yet.
"""

from .intents import IntentResult, IntentType, ScopeTier
from .router import classify

__all__ = ["IntentResult", "IntentType", "ScopeTier", "classify"]
