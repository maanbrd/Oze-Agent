"""Scenario registry + common scenario wrapper.

Each scenario module declares scenarios by decorating async functions with
`@register(name=..., category=...)`. The decorator captures metadata
(category, description) and adds the function to SCENARIOS so the runner
and the MCP server can list / dispatch them.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Awaitable, Callable

from tests_e2e.harness import TelegramE2EHarness
from tests_e2e.report import ScenarioResult

logger = logging.getLogger(__name__)

ScenarioFn = Callable[[TelegramE2EHarness], Awaitable[ScenarioResult]]


@dataclass(frozen=True)
class RegisteredScenario:
    name: str
    category: str
    fn: ScenarioFn
    description: str = ""
    # If False, the scenario is registered but excluded from the default
    # `runner` selection (`runner` without args). Used for scenarios with
    # noticeable side effects — e.g. `debug_brief` sends the morning brief
    # to the chat. Per Codex review: opt-in only, never default.
    default_in_run: bool = True


SCENARIOS: dict[str, RegisteredScenario] = {}


def register(
    name: str,
    category: str,
    description: str = "",
    *,
    default_in_run: bool = True,
):
    """Decorator that adds a scenario function to SCENARIOS."""
    def decorator(fn: ScenarioFn) -> ScenarioFn:
        if name in SCENARIOS:
            raise RuntimeError(f"duplicate scenario name: {name!r}")
        SCENARIOS[name] = RegisteredScenario(
            name=name,
            category=category,
            fn=fn,
            description=description,
            default_in_run=default_in_run,
        )
        return fn
    return decorator


def list_categories() -> list[str]:
    return sorted({s.category for s in SCENARIOS.values()})


def list_scenarios(
    category: str | None = None,
    *,
    only_default: bool = False,
) -> list[RegisteredScenario]:
    """List scenarios; optionally filter by category and `default_in_run`.

    `only_default=True` excludes opt-in scenarios (e.g. `debug_brief`).
    """
    items = sorted(SCENARIOS.values(), key=lambda s: (s.category, s.name))
    if category is not None:
        items = [s for s in items if s.category == category]
    if only_default:
        items = [s for s in items if s.default_in_run]
    return items


def get_scenario(name: str) -> RegisteredScenario:
    if name not in SCENARIOS:
        raise KeyError(f"unknown scenario: {name!r}; available: {sorted(SCENARIOS)}")
    return SCENARIOS[name]


# ── Common scenario scaffolding ─────────────────────────────────────────────


def new_result(name: str, category: str) -> ScenarioResult:
    """Create a freshly-stamped ScenarioResult with category set."""
    r = ScenarioResult(
        scenario_name=name,
        started_at=datetime.now(tz=timezone.utc),
        category=category,
    )
    return r


def stamp_end(result: ScenarioResult) -> None:
    result.ended_at = datetime.now(tz=timezone.utc)
