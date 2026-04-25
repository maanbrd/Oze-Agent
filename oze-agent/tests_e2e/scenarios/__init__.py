"""E2E test scenarios. One file per scenario / flow.

Naming convention: module name = logical scenario name (e.g. debug_brief).
Each module exports an async entry point that takes a connected
`TelegramE2EHarness` and returns a `ScenarioResult`.
"""

from tests_e2e.scenarios.debug_brief import run_debug_brief_scenario

__all__ = ["run_debug_brief_scenario"]
