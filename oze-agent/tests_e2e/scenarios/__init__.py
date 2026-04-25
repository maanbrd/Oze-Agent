"""E2E test scenarios.

Importing this package populates the SCENARIOS registry as a side effect
of importing each module that uses `@register(...)`. Add new categories
by creating a new module and importing it below.
"""

# Order doesn't matter for correctness — registry is a dict keyed by name.
# But keep alphabetical for stable diffs.
from tests_e2e.scenarios import (  # noqa: F401  (registration side effect)
    card_structure,
    debug_brief,
    error_paths,
    read_only,
    routing,
    rules,
)
from tests_e2e.scenarios._base import (
    SCENARIOS,
    RegisteredScenario,
    get_scenario,
    list_categories,
    list_scenarios,
)

# Backwards-compat re-export for existing callers.
from tests_e2e.scenarios.debug_brief import run_debug_brief_scenario  # noqa: F401

__all__ = [
    "SCENARIOS",
    "RegisteredScenario",
    "get_scenario",
    "list_categories",
    "list_scenarios",
    "run_debug_brief_scenario",
]
