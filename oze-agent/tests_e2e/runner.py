"""CLI entry point for the Phase 7 E2E harness.

Usage (from oze-agent/, after env is sourced — see tests_e2e/README.md):

    python -m tests_e2e.runner --list            # list scenarios + categories
    python -m tests_e2e.runner debug_brief       # run one scenario
    python -m tests_e2e.runner --category routing  # run one category
    python -m tests_e2e.runner debug_brief --report /tmp/e2e.md

Exit codes:
    0  — all scenarios PASS (or only have known_drift / expected_fail)
    1  — at least one FAIL (regression)
    2  — misconfiguration (missing env), preflight blocker, or harness connect error
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

# Importing the package populates the scenario registry.
import tests_e2e.scenarios  # noqa: F401 — side effect: register
from tests_e2e.config import E2EConfig
from tests_e2e.harness import TelegramE2EHarness
from tests_e2e.preflight import run_preflight
from tests_e2e.report import ScenarioResult, write_report
from tests_e2e.scenarios._base import (
    RegisteredScenario,
    get_scenario,
    list_categories,
    list_scenarios,
)
from tests_e2e.scenarios._helpers import inter_scenario_sleep, reset_pending

logger = logging.getLogger(__name__)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="python -m tests_e2e.runner",
        description="Run OZE-Agent Phase 7 E2E scenarios against a live Telegram bot.",
    )
    p.add_argument(
        "scenarios",
        nargs="*",
        help="Scenario names to run (default: all, or use --category).",
    )
    p.add_argument(
        "--category",
        help="Run all scenarios in the given category.",
    )
    p.add_argument(
        "--list",
        action="store_true",
        help="List scenarios + categories and exit.",
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
    p.add_argument(
        "--no-preflight",
        action="store_true",
        help="Skip preflight sanity checks (NOT recommended).",
    )
    return p.parse_args(argv)


def _print_listing() -> None:
    cats = list_categories()
    print(f"Categories ({len(cats)}): {', '.join(cats)}")
    print()
    print(f"{'Scenario':45}  {'Category':14}  Description")
    print("-" * 100)
    for s in list_scenarios():
        print(f"{s.name:45}  {s.category:14}  {s.description}")


def _select_scenarios(
    names: list[str],
    category: str | None,
) -> list[RegisteredScenario]:
    if names and category:
        raise SystemExit("Use either positional names OR --category, not both.")
    if names:
        try:
            return [get_scenario(n) for n in names]
        except KeyError as e:
            raise SystemExit(str(e)) from e
    if category:
        # Within a category, do NOT filter by default_in_run — explicit
        # category request is intentional.
        sel = list_scenarios(category=category)
        if not sel:
            raise SystemExit(
                f"No scenarios in category {category!r}. "
                f"Available: {list_categories()}"
            )
        return sel
    # Default `runner` (no args, no --category) excludes opt-in scenarios
    # like debug_brief that have noticeable side effects (sends a brief).
    return list_scenarios(only_default=True)


async def _run_all(
    config: E2EConfig,
    selection: list[RegisteredScenario],
    *,
    skip_preflight: bool,
) -> list[ScenarioResult]:
    results: list[ScenarioResult] = []
    async with TelegramE2EHarness(config) as harness:
        if not skip_preflight:
            preflight = await run_preflight(harness)
            if not preflight.ok:
                logger.error("preflight FAILED: %s", preflight.findings)
                # Synthesize a blocker scenario so the report shows the cause.
                from datetime import datetime, timezone
                blocker = ScenarioResult(
                    scenario_name="_preflight",
                    started_at=datetime.now(tz=timezone.utc),
                    ended_at=datetime.now(tz=timezone.utc),
                    category="infra",
                )
                for f in preflight.findings:
                    blocker.add_blocker("preflight", f)
                results.append(blocker)
                return results
            logger.info("preflight OK: %s", preflight.findings)

        for i, scen in enumerate(selection):
            logger.info(
                "e2e.start scenario=%s category=%s (%d/%d)",
                scen.name, scen.category, i + 1, len(selection),
            )
            try:
                # Auto-cancel any pending residue between scenarios.
                if i > 0 or scen.name != "debug_brief":
                    await reset_pending(harness)
                result = await scen.fn(harness)
            except Exception as e:
                logger.exception("scenario %s crashed", scen.name)
                from datetime import datetime, timezone
                result = ScenarioResult(
                    scenario_name=scen.name,
                    started_at=datetime.now(tz=timezone.utc),
                    ended_at=datetime.now(tz=timezone.utc),
                    category=scen.category,
                )
                result.add_blocker("scenario_crash", f"{type(e).__name__}: {e}")
            results.append(result)
            logger.info(
                "e2e.done scenario=%s verdict=%s",
                scen.name, result.verdict(),
            )
            if i + 1 < len(selection):
                await inter_scenario_sleep()
    return results


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )

    if args.list:
        _print_listing()
        return 0

    try:
        config = E2EConfig.from_env()
    except RuntimeError as e:
        print(f"E2E config error: {e}", file=sys.stderr)
        return 2

    if args.report:
        config.report_path = args.report

    try:
        selection = _select_scenarios(args.scenarios, args.category)
    except SystemExit as e:
        print(str(e), file=sys.stderr)
        return 2

    try:
        results = asyncio.run(
            _run_all(config, selection, skip_preflight=args.no_preflight)
        )
    except Exception as e:
        logger.exception("E2E run failed")
        print(f"E2E run crashed: {e}", file=sys.stderr)
        return 2

    write_report(results, config.report_path)
    print(f"Report written to {config.report_path}")

    has_blocker = any(r.has_blocker for r in results)
    overall_pass = bool(results) and not has_blocker and all(r.passed for r in results)
    for r in results:
        print(f"  {r.verdict():8} {r.scenario_name}")
    if has_blocker:
        return 2
    return 0 if overall_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
