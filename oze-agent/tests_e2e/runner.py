"""CLI entry point for the Phase 7 E2E harness.

Usage (from repo root, after setting env vars — see tests_e2e/README.md):

    python -m tests_e2e.runner                       # run all scenarios
    python -m tests_e2e.runner debug_brief           # run one scenario
    python -m tests_e2e.runner debug_brief --report /tmp/e2e.md

Exit codes:
    0  — all scenarios PASS
    1  — at least one FAIL
    2  — misconfiguration (missing env, harness connect error)
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from typing import Awaitable, Callable

from tests_e2e.config import E2EConfig
from tests_e2e.harness import TelegramE2EHarness
from tests_e2e.report import ScenarioResult, write_report
from tests_e2e.scenarios.debug_brief import run_debug_brief_scenario

logger = logging.getLogger(__name__)


# Registry — add new scenarios here as they land.
ScenarioFn = Callable[[TelegramE2EHarness], Awaitable[ScenarioResult]]
SCENARIOS: dict[str, ScenarioFn] = {
    "debug_brief": run_debug_brief_scenario,
}


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="python -m tests_e2e.runner",
        description="Run OZE-Agent Phase 7 E2E scenarios against a live Telegram bot.",
    )
    p.add_argument(
        "scenarios",
        nargs="*",
        help="Scenario names to run (default: all). Available: "
        + ", ".join(sorted(SCENARIOS)),
    )
    p.add_argument(
        "--report",
        help="Override report output path (default: from TELEGRAM_E2E_REPORT env).",
    )
    p.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable DEBUG logging.",
    )
    return p.parse_args(argv)


def _select_scenarios(names: list[str]) -> list[tuple[str, ScenarioFn]]:
    if not names:
        return list(SCENARIOS.items())
    selected: list[tuple[str, ScenarioFn]] = []
    unknown: list[str] = []
    for n in names:
        fn = SCENARIOS.get(n)
        if fn is None:
            unknown.append(n)
        else:
            selected.append((n, fn))
    if unknown:
        raise SystemExit(
            f"Unknown scenario(s): {unknown}. "
            f"Available: {sorted(SCENARIOS)}"
        )
    return selected


async def _run_all(config: E2EConfig, scenarios: list[tuple[str, ScenarioFn]]) -> list[ScenarioResult]:
    results: list[ScenarioResult] = []
    async with TelegramE2EHarness(config) as harness:
        for name, fn in scenarios:
            logger.info("e2e.start scenario=%s", name)
            result = await fn(harness)
            logger.info("e2e.done scenario=%s verdict=%s", name, result.verdict())
            results.append(result)
    return results


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )
    try:
        config = E2EConfig.from_env()
    except RuntimeError as e:
        print(f"E2E config error: {e}", file=sys.stderr)
        return 2
    if args.report:
        config.report_path = args.report

    scenarios = _select_scenarios(args.scenarios)

    try:
        results = asyncio.run(_run_all(config, scenarios))
    except Exception as e:
        logger.exception("E2E run failed")
        print(f"E2E run crashed: {e}", file=sys.stderr)
        return 2

    write_report(results, config.report_path)
    print(f"Report written to {config.report_path}")

    overall_pass = bool(results) and all(r.passed for r in results)
    for r in results:
        print(f"  {r.verdict():4} {r.scenario_name}")
    return 0 if overall_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
