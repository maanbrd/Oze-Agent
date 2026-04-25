"""Optional MCP server wrapping the Phase 7 E2E harness.

Exposes the same scenarios as the CLI (tests_e2e/runner.py) as MCP tools.

Tools (Phase 7A):
    e2e_status            — config health (no Telegram contact)
    list_scenarios        — registered scenarios + categories
    run_debug_brief       — convenience for the most-used scenario
    run_scenario(name)    — run one scenario by name
    run_category(name)    — run every scenario in a category

Intentionally NOT provided (anti-timeout):
    run_all               — long sweep would exceed MCP per-call timeout

Install:
    pip install -r tests_e2e/requirements-e2e.txt

Claude Code config: see tests_e2e/run_mcp_server.sh — that wrapper loads
the .env and selects the venv Python so the registry imports cleanly.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

# Importing the package populates the SCENARIOS registry.
import tests_e2e.scenarios  # noqa: F401
from tests_e2e.config import E2EConfig
from tests_e2e.harness import TelegramE2EHarness
from tests_e2e.preflight import run_preflight
from tests_e2e.report import ScenarioResult
from tests_e2e.scenarios._base import (
    RegisteredScenario,
    get_scenario,
    list_categories,
)
from tests_e2e.scenarios._base import list_scenarios as _registry_list
from tests_e2e.scenarios._helpers import inter_scenario_sleep, reset_pending
from tests_e2e.scenarios.debug_brief import run_debug_brief_scenario

logger = logging.getLogger(__name__)


def _render_one(result: ScenarioResult) -> str:
    """Compact text summary of a single scenario."""
    lines = [f"{result.verdict():8} — {result.scenario_name}  [{result.category}]"]
    for c in result.checks:
        marker = {
            "pass": "✓", "known_drift": "~", "expected_fail": "·",
            "fail": "✗", "blocker": "!",
        }.get(c.tag, "?")
        extra = f" — {c.detail}" if c.detail else ""
        lines.append(f"  {marker} [{c.tag}] {c.name}{extra}")
    return "\n".join(lines)


def _render_many(results: list[ScenarioResult]) -> str:
    """Text summary of multiple scenarios + an overall counter line."""
    sections = [_render_one(r) for r in results]
    pass_count = sum(1 for r in results if r.passed)
    blocker_count = sum(1 for r in results if r.has_blocker)
    sections.append(
        f"\n=== {pass_count}/{len(results)} PASS, {blocker_count} blocker(s) ==="
    )
    return "\n\n".join(sections)


async def _run_one(scenario_fn) -> str:
    """Run a single scenario with preflight, return rendered text."""
    config = E2EConfig.from_env()
    async with TelegramE2EHarness(config) as harness:
        preflight = await run_preflight(harness)
        if not preflight.ok:
            return "PREFLIGHT BLOCKER\n" + "\n".join(preflight.findings)
        result = await scenario_fn(harness)
    return _render_one(result)


async def _run_named(scen: RegisteredScenario) -> str:
    return await _run_one(scen.fn)


async def _run_selection(selection: list[RegisteredScenario]) -> str:
    """Run multiple scenarios in one harness session, with preflight + reset."""
    if not selection:
        return "no scenarios selected"
    config = E2EConfig.from_env()
    results: list[ScenarioResult] = []
    async with TelegramE2EHarness(config) as harness:
        preflight = await run_preflight(harness)
        if not preflight.ok:
            return "PREFLIGHT BLOCKER\n" + "\n".join(preflight.findings)
        for i, scen in enumerate(selection):
            try:
                if i > 0 or scen.name != "debug_brief":
                    await reset_pending(harness)
                result = await scen.fn(harness)
            except Exception as e:
                result = ScenarioResult(
                    scenario_name=scen.name,
                    started_at=datetime.now(tz=timezone.utc),
                    ended_at=datetime.now(tz=timezone.utc),
                    category=scen.category,
                )
                result.add_blocker("scenario_crash", f"{type(e).__name__}: {e}")
            results.append(result)
            if i + 1 < len(selection):
                await inter_scenario_sleep()
    return _render_many(results)


def _build_server():
    """Defer FastMCP import so the module stays importable without `mcp[cli]`."""
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("oze-e2e")

    @mcp.tool()
    async def e2e_status() -> str:
        """Report harness configuration health without touching Telegram."""
        try:
            config = E2EConfig.from_env()
        except RuntimeError as e:
            return f"MISCONFIG — {e}"
        return (
            "OK — config loaded\n"
            f"  bot_username: {config.bot_username}\n"
            f"  admin_id:     {config.admin_telegram_id}\n"
            f"  session_path: {config.session_path}\n"
            f"  report_path:  {config.report_path}\n"
            f"  now_utc:      {datetime.now(tz=timezone.utc).isoformat()}\n"
            f"  scenarios:    {len(_registry_list())}\n"
            f"  categories:   {', '.join(list_categories())}"
        )

    @mcp.tool()
    async def list_scenarios() -> str:
        """List registered scenarios with categories and descriptions."""
        items = _registry_list()
        lines = [f"{len(items)} scenarios in {len(list_categories())} categories:"]
        for s in items:
            lines.append(f"  [{s.category:14}] {s.name:40}  {s.description}")
        return "\n".join(lines)

    @mcp.tool()
    async def run_debug_brief() -> str:
        """Run the /debug_brief round-trip smoke against the configured bot.

        Two /debug_brief sends, dedup verification, ack/Terminarz/summary
        check. ~35 seconds. Returns a multi-line PASS/FAIL summary.
        """
        return await _run_one(run_debug_brief_scenario)

    @mcp.tool()
    async def run_scenario(name: str) -> str:
        """Run a single scenario by name. See list_scenarios for options."""
        try:
            scen = get_scenario(name)
        except KeyError as e:
            return f"ERROR — {e}"
        return await _run_named(scen)

    @mcp.tool()
    async def run_category(name: str) -> str:
        """Run every scenario in a category. Categories: routing, read_only,
        card_structure, error_path, rules, proactive."""
        selection = _registry_list(category=name)
        if not selection:
            return (
                f"ERROR — unknown category {name!r}. "
                f"Available: {list_categories()}"
            )
        return await _run_selection(selection)

    return mcp


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )
    mcp = _build_server()
    mcp.run()


if __name__ == "__main__":
    main()
