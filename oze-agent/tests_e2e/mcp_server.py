"""Optional MCP server wrapping the Phase 7 E2E harness.

Exposes the same scenarios as the CLI (tests_e2e/runner.py) as MCP tools,
so a Claude Code agent can drive smoke tests from chat.

The server is a *thin* wrapper: every tool delegates to the same
scenario functions used by the CLI. Keep it that way — if you are
tempted to add logic here, put it in a scenario module instead.

Install:
    pip install -r tests_e2e/requirements-e2e.txt

Claude Code config (~/.claude.json or similar):
    {
      "mcpServers": {
        "oze-e2e": {
          "command": "python",
          "args": ["-m", "tests_e2e.mcp_server"],
          "cwd": "/ABS/PATH/Agent-OZE/oze-agent",
          "env": {
            "TELEGRAM_E2E_API_ID": "...",
            "TELEGRAM_E2E_API_HASH": "...",
            "TELEGRAM_E2E_BOT_USERNAME": "@OzeAgentBot",
            "TELEGRAM_E2E_ADMIN_ID": "...",
            "TELEGRAM_E2E_SESSION": "/ABS/PATH/.sessions/e2e"
          }
        }
      }
    }
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from tests_e2e.config import E2EConfig
from tests_e2e.harness import TelegramE2EHarness
from tests_e2e.report import ScenarioResult
from tests_e2e.scenarios.debug_brief import run_debug_brief_scenario

logger = logging.getLogger(__name__)


def _render(result: ScenarioResult) -> str:
    """Compact text summary for the MCP tool response."""
    lines = [f"{result.verdict()} — {result.scenario_name}"]
    for c in result.checks:
        icon = "✓" if c.passed else "✗"
        extra = f" — {c.detail}" if c.detail else ""
        lines.append(f"  {icon} {c.name}{extra}")
    return "\n".join(lines)


async def _run_one(scenario_fn) -> str:
    config = E2EConfig.from_env()
    async with TelegramE2EHarness(config) as harness:
        result = await scenario_fn(harness)
    return _render(result)


def _build_server():
    """Defer FastMCP import so the module stays importable without `mcp[cli]`."""
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("oze-e2e")

    @mcp.tool()
    async def run_debug_brief() -> str:
        """Run the /debug_brief round-trip smoke against the configured bot.

        Checks: ack message, Terminarz: header in the brief, summary line
        with sent= field, and dedup behavior on the second same-day run.
        Returns a PASS/FAIL line per check.
        """
        return await _run_one(run_debug_brief_scenario)

    @mcp.tool()
    async def list_scenarios() -> str:
        """List available E2E scenarios."""
        return "available: debug_brief"

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
            f"  now_utc:      {datetime.now(tz=timezone.utc).isoformat()}"
        )

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
