"""Proactive (non-request-response) messaging for OZE-Agent.

Phase 6 hosts the morning brief (07:00 Europe/Warsaw, Mon-Fri). Future
additions like evening follow-up would live here too.
"""

from shared.proactive.morning_brief import (
    MorningBriefRunResult,
    run_morning_brief,
)

__all__ = ["MorningBriefRunResult", "run_morning_brief"]
