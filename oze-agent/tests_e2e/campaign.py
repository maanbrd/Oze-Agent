"""Smoke-campaign planner and runner for the OZE-Agent E2E harness.

The campaign combines the existing Telethon scenarios with external checks
that must be driven by Codex connectors / browser tooling. The Python CLI runs
only the Telethon-owned part; Drive, Gmail and dashboard-browser checks are
listed in the manifest so they cannot be silently counted as passing.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Literal

import tests_e2e.scenarios  # noqa: F401 - populate registry
from tests_e2e.config import E2EConfig
from tests_e2e.fixtures import cleanup_synthetic_data, seed_fixtures
from tests_e2e.harness import TelegramE2EHarness
from tests_e2e.preflight import run_preflight
from tests_e2e.report import ScenarioResult, write_report
from tests_e2e.scenarios._base import (
    RegisteredScenario,
    get_scenario,
    list_scenarios,
)
from tests_e2e.scenarios._helpers import inter_scenario_sleep, reset_pending

logger = logging.getLogger(__name__)

Driver = Literal["telethon", "codex_connector", "browser"]

DASHBOARD_URL_ENV = "TELEGRAM_E2E_DASHBOARD_URL"
OFFER_RECIPIENT_ENV = "TELEGRAM_E2E_OFFER_RECIPIENT"
PILOT_LIMIT = 50
CAMPAIGN_TARGET = 500
REALISTIC_SCENARIOS = (
    "realistic_add_client_sheets_save",
    "realistic_add_meeting_calendar_sheets_save",
    "realistic_show_day_plan_after_meeting",
)


async def _hard_cancel_pending(harness: TelegramE2EHarness) -> None:
    """Clear Telegram pending state without treating the reply as a scenario."""
    try:
        await harness.send("/cancel")
        await harness.collect_messages(duration_s=3.0)
    except Exception as e:
        logger.warning("campaign.hard_cancel_pending failed: %s", e)


def _cleanup_is_safe(report: dict) -> bool:
    """True when cleanup definitely did not leave known synthetic residue."""
    return bool(report.get("cleanup_safe", True)) and not report.get("cleanup_error")


def _cleanup_blocker_result(
    scenario_name: str,
    report: dict,
    *,
    iteration: int | None = None,
) -> ScenarioResult:
    result = ScenarioResult(
        scenario_name=scenario_name,
        started_at=datetime.now(tz=timezone.utc),
        ended_at=datetime.now(tz=timezone.utc),
        category="infra",
    )
    if iteration is not None:
        result.context["realistic_iteration"] = iteration
    result.add_blocker("cleanup_failed", repr(report))
    return result


@dataclass(frozen=True)
class CampaignBucket:
    name: str
    requested_runs: int
    normalized_runs: int
    driver: Driver
    surfaces: tuple[str, ...]
    categories: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()
    description: str = ""


@dataclass(frozen=True)
class CampaignUnit:
    index: int
    bucket: str
    driver: Driver
    target: str
    surfaces: tuple[str, ...]


# The written campaign matrix from the plan sums to 540. Keep the raw count
# visible for auditability, then normalize the repeat-heavy core bucket to hit
# the explicit 500-run campaign target without dropping any surface.
REQUESTED_MATRIX: tuple[CampaignBucket, ...] = (
    CampaignBucket(
        name="baseline_existing_scenarios",
        requested_runs=48,
        normalized_runs=48,
        driver="telethon",
        surfaces=("telegram", "sheets", "calendar"),
        description="One pass over the 48 registered E2E scenarios.",
    ),
    CampaignBucket(
        name="core_mutations",
        requested_runs=240,
        normalized_runs=200,
        driver="telethon",
        surfaces=("telegram", "sheets", "calendar", "dashboard"),
        categories=("mutating_core", "notes"),
        description="add_client/add_meeting/change_status/add_note repeats.",
    ),
    CampaignBucket(
        name="r1_confirmation_idempotency",
        requested_runs=80,
        normalized_runs=80,
        driver="telethon",
        surfaces=("telegram", "sheets", "calendar"),
        categories=("rules", "card_structure", "error_path"),
        description="No-write-before-confirmation, cancel and pending rules.",
    ),
    CampaignBucket(
        name="calendar_edge_cases",
        requested_runs=60,
        normalized_runs=60,
        driver="telethon",
        surfaces=("telegram", "calendar", "sheets"),
        categories=("mutating_core", "read_only", "rules"),
        keywords=("meeting", "calendar", "day_plan", "offer_email", "doc_followup"),
        description="Calendar type/date/duration/conflict coverage.",
    ),
    CampaignBucket(
        name="drive_photo_flow",
        requested_runs=40,
        normalized_runs=40,
        driver="codex_connector",
        surfaces=("telegram", "drive", "sheets"),
        description="Photo upload: Drive file/folder plus Sheets N/O checks.",
    ),
    CampaignBucket(
        name="offer_gmail_flow",
        requested_runs=40,
        normalized_runs=40,
        driver="codex_connector",
        surfaces=("telegram", "gmail", "sheets"),
        description="Offer send: Gmail Sent/PDF/idempotency checks.",
    ),
    CampaignBucket(
        name="read_only_dashboard_refresh",
        requested_runs=32,
        normalized_runs=32,
        driver="telethon",
        surfaces=("telegram", "calendar", "sheets", "dashboard"),
        categories=("read_only", "routing", "polish_edge"),
        description="show_client/show_day_plan/cancel/Polish date formatting.",
    ),
)


def requested_total() -> int:
    return sum(b.requested_runs for b in REQUESTED_MATRIX)


def normalized_total() -> int:
    return sum(b.normalized_runs for b in REQUESTED_MATRIX)


def _round_robin(items: list[str], count: int) -> list[str]:
    if count <= 0:
        return []
    if not items:
        raise RuntimeError("campaign bucket has no runnable Telethon scenarios")
    return [items[i % len(items)] for i in range(count)]


def _scenario_names_for_bucket(bucket: CampaignBucket) -> list[str]:
    if bucket.name == "baseline_existing_scenarios":
        return [s.name for s in list_scenarios()]

    selected: list[RegisteredScenario] = []
    if bucket.categories:
        selected.extend(
            s for s in list_scenarios()
            if s.category in set(bucket.categories)
        )
    if bucket.keywords:
        lowered = tuple(k.lower() for k in bucket.keywords)
        selected = [
            s for s in selected
            if any(k in s.name.lower() or k in s.description.lower() for k in lowered)
        ]
    return [s.name for s in selected]


def build_campaign_units() -> list[CampaignUnit]:
    if normalized_total() != CAMPAIGN_TARGET:
        raise RuntimeError(
            f"normalized campaign matrix must be {CAMPAIGN_TARGET}, "
            f"got {normalized_total()}"
        )

    units: list[CampaignUnit] = []
    next_index = 1
    for bucket in REQUESTED_MATRIX:
        if bucket.driver == "telethon":
            targets = _round_robin(
                _scenario_names_for_bucket(bucket),
                bucket.normalized_runs,
            )
        else:
            targets = [f"{bucket.driver}:{bucket.name}"] * bucket.normalized_runs

        for target in targets:
            units.append(
                CampaignUnit(
                    index=next_index,
                    bucket=bucket.name,
                    driver=bucket.driver,
                    target=target,
                    surfaces=bucket.surfaces,
                )
            )
            next_index += 1
    return units


def telethon_units(units: Iterable[CampaignUnit]) -> list[CampaignUnit]:
    return [u for u in units if u.driver == "telethon"]


def external_units(units: Iterable[CampaignUnit]) -> list[CampaignUnit]:
    return [u for u in units if u.driver != "telethon"]


def validate_pilot_limit(limit: int) -> int:
    if limit < 1:
        raise ValueError("pilot limit must be at least 1")
    if limit > PILOT_LIMIT:
        raise ValueError(
            f"pilot limit is capped at {PILOT_LIMIT} until isolated resources "
            f"are confirmed"
        )
    return limit


def render_plan(units: list[CampaignUnit] | None = None) -> str:
    units = units or build_campaign_units()
    by_bucket = Counter(u.bucket for u in units)
    by_driver = Counter(u.driver for u in units)
    by_surface = Counter(surface for u in units for surface in u.surfaces)
    lines = [
        "# OZE-Agent Smoke E2E Campaign",
        "",
        f"Requested matrix total: {requested_total()}",
        f"Normalized campaign total: {normalized_total()}",
        (
            "Normalization: the written matrix sums to 540; "
            "core_mutations is reduced from 240 to 200 so the campaign "
            "has exactly 500 checks without dropping any surface."
        ),
        "",
        "## Buckets",
    ]
    for bucket in REQUESTED_MATRIX:
        lines.append(
            "- "
            f"{bucket.name}: requested={bucket.requested_runs}, "
            f"normalized={bucket.normalized_runs}, driver={bucket.driver}, "
            f"surfaces={','.join(bucket.surfaces)}"
        )
    lines.extend([
        "",
        "## Driver counts",
        *[f"- {name}: {count}" for name, count in sorted(by_driver.items())],
        "",
        "## Surface counts",
        *[f"- {name}: {count}" for name, count in sorted(by_surface.items())],
        "",
        "## Execution gates",
        f"- Pilot mode is capped at {PILOT_LIMIT} Telethon runs.",
        "- Full Telethon campaign requires --confirm-test-environment.",
        (
            f"- Dashboard/browser checks require {DASHBOARD_URL_ENV} to point "
            "at the feat/web-bootstrap dashboard deployment."
        ),
        (
            f"- Offer/Gmail checks require {OFFER_RECIPIENT_ENV} to point at "
            "a controlled inbox."
        ),
        (
            "- Gmail Sent verification requires the connected Gmail account to "
            "match the Google account used by the bot-test sender."
        ),
        "- Drive/Gmail/dashboard connector checks are not run by the Python CLI.",
        "",
        "## Planned unit counts",
        *[f"- {name}: {count}" for name, count in sorted(by_bucket.items())],
    ])
    return "\n".join(lines)


def _campaign_footer(units: list[CampaignUnit], omitted: list[CampaignUnit]) -> str:
    lines = [
        "",
        "---",
        "",
        "## Campaign Surface Evidence",
        "",
        "The report above is produced by the Telethon harness. PASS only means "
        "the executed Telethon scenarios passed their own assertions.",
        "",
        "Executed driver counts:",
    ]
    for name, count in sorted(Counter(u.driver for u in units).items()):
        lines.append(f"- {name}: {count}")
    if omitted:
        lines.append("")
        lines.append("Omitted non-Telethon checks requiring Codex connectors/browser:")
        for name, count in sorted(Counter(u.bucket for u in omitted).items()):
            lines.append(f"- {name}: {count}")
    lines.extend([
        "",
        "## Post-app Results",
        "",
        "Post-app checks are required for Drive/Gmail PASS.",
        "Run `python -m tests_e2e.post_campaign_checks` after the Telethon wave.",
        "",
        "## Codex Connector Evidence",
        "",
        "Sheets, Calendar, Drive and Gmail connector reads must be attached to the final campaign report.",
        "The Python CLI cannot verify Gmail Sent because the bot OAuth scope is gmail.send only.",
        "",
        "## Dashboard Evidence",
        "",
        "Dashboard PASS requires live dashboard API data and browser/Vercel evidence.",
        "If the UI redirects to login, record API evidence and do not count UI as PASS.",
    ])
    lines.append("")
    lines.append("Target systems expected by the full 500 campaign:")
    surface_counts = Counter(
        surface for unit in units + omitted for surface in unit.surfaces
    )
    for surface, count in sorted(surface_counts.items()):
        lines.append(f"- {surface}: {count}")
    return "\n".join(lines)


async def _run_telethon_units(
    config: E2EConfig,
    units: list[CampaignUnit],
    *,
    skip_preflight: bool,
    wave_size: int,
) -> list[ScenarioResult]:
    results: list[ScenarioResult] = []

    initial_cleanup = await cleanup_synthetic_data(config.admin_telegram_id)
    if not _cleanup_is_safe(initial_cleanup):
        return [_cleanup_blocker_result("_initial_cleanup", initial_cleanup)]
    await seed_fixtures(config.admin_telegram_id)

    async with TelegramE2EHarness(config) as harness:
        if not skip_preflight:
            preflight = await run_preflight(harness)
            if not preflight.ok:
                blocker = ScenarioResult(
                    scenario_name="_preflight",
                    started_at=datetime.now(tz=timezone.utc),
                    ended_at=datetime.now(tz=timezone.utc),
                    category="infra",
                )
                for finding in preflight.findings:
                    blocker.add_blocker("preflight", finding)
                return [blocker]

        for i, unit in enumerate(units):
            scen = get_scenario(unit.target)
            logger.info(
                "campaign.start unit=%s bucket=%s scenario=%s",
                unit.index,
                unit.bucket,
                unit.target,
            )
            try:
                await reset_pending(harness)
                result = await scen.fn(harness)
            except Exception as e:
                logger.exception("campaign unit %s crashed", unit.index)
                result = ScenarioResult(
                    scenario_name=unit.target,
                    started_at=datetime.now(tz=timezone.utc),
                    ended_at=datetime.now(tz=timezone.utc),
                    category=scen.category,
                )
                result.add_blocker("scenario_crash", f"{type(e).__name__}: {e}")

            result.context["campaign_unit"] = unit.index
            result.context["campaign_bucket"] = unit.bucket
            result.context["target_surfaces"] = ", ".join(unit.surfaces)
            results.append(result)

            if i + 1 < len(units):
                await inter_scenario_sleep()
            if wave_size > 0 and (i + 1) % wave_size == 0:
                cleanup = await cleanup_synthetic_data(config.admin_telegram_id)
                if cleanup.get("sheets_rows_found") or cleanup.get("calendar_events_found"):
                    logger.info("campaign.wave_cleanup report=%s", cleanup)
                if not _cleanup_is_safe(cleanup):
                    results.append(_cleanup_blocker_result("_wave_cleanup", cleanup))
                    return results

    final_cleanup = await cleanup_synthetic_data(config.admin_telegram_id)
    if not _cleanup_is_safe(final_cleanup):
        results.append(_cleanup_blocker_result("_final_cleanup", final_cleanup))
    return results


async def _run_realistic_iterations(
    config: E2EConfig,
    *,
    iterations: int,
    skip_preflight: bool,
) -> list[ScenarioResult]:
    results: list[ScenarioResult] = []
    initial_cleanup = await cleanup_synthetic_data(
        config.admin_telegram_id,
        include_fixtures=True,
    )
    if not _cleanup_is_safe(initial_cleanup):
        return [_cleanup_blocker_result("_initial_cleanup", initial_cleanup)]

    async with TelegramE2EHarness(config) as harness:
        if not skip_preflight:
            preflight = await run_preflight(harness)
            if not preflight.ok:
                blocker = ScenarioResult(
                    scenario_name="_preflight",
                    started_at=datetime.now(tz=timezone.utc),
                    ended_at=datetime.now(tz=timezone.utc),
                    category="infra",
                )
                for finding in preflight.findings:
                    blocker.add_blocker("preflight", finding)
                return [blocker]

        await _hard_cancel_pending(harness)

        for iteration in range(1, iterations + 1):
            for name in REALISTIC_SCENARIOS:
                scen = get_scenario(name)
                logger.info(
                    "realistic_campaign.start iteration=%s/%s scenario=%s",
                    iteration,
                    iterations,
                    name,
                )
                try:
                    result = await scen.fn(harness)
                except Exception as e:
                    logger.exception("realistic campaign scenario %s crashed", name)
                    result = ScenarioResult(
                        scenario_name=name,
                        started_at=datetime.now(tz=timezone.utc),
                        ended_at=datetime.now(tz=timezone.utc),
                        category=scen.category,
                    )
                    result.add_blocker("scenario_crash", f"{type(e).__name__}: {e}")

                result.context["realistic_iteration"] = iteration
                results.append(result)
                if result.has_blocker or not result.passed:
                    await _hard_cancel_pending(harness)
                await inter_scenario_sleep()

            cleanup = await cleanup_synthetic_data(
                config.admin_telegram_id,
                include_fixtures=True,
            )
            logger.info(
                "realistic_campaign.cleanup iteration=%s report=%s",
                iteration,
                cleanup,
            )
            if not _cleanup_is_safe(cleanup):
                results.append(
                    _cleanup_blocker_result(
                        "_realistic_iteration_cleanup",
                        cleanup,
                        iteration=iteration,
                    )
                )
                break

    final_cleanup = await cleanup_synthetic_data(
        config.admin_telegram_id,
        include_fixtures=True,
    )
    if not _cleanup_is_safe(final_cleanup):
        results.append(_cleanup_blocker_result("_final_cleanup", final_cleanup))
    return results


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m tests_e2e.campaign",
        description="Plan and run the OZE-Agent smoke E2E campaign.",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true", help="Print the 500-run manifest.")
    mode.add_argument("--pilot", action="store_true", help="Run up to 50 Telethon units.")
    mode.add_argument(
        "--telethon-full",
        action="store_true",
        help="Run the Telethon-owned part of the full campaign.",
    )
    mode.add_argument(
        "--realistic-iterations",
        type=int,
        help="Run the realistic smoke pack N times, cleaning up after each iteration.",
    )
    parser.add_argument("--limit", type=int, default=PILOT_LIMIT)
    parser.add_argument("--wave-size", type=int, default=25)
    parser.add_argument("--report", help="Override markdown report path.")
    parser.add_argument("--no-preflight", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument(
        "--confirm-test-environment",
        action="store_true",
        help="Required for --telethon-full; confirms current Google/Supabase are test resources.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

    units = build_campaign_units()
    if args.plan:
        print(render_plan(units))
        return 0

    try:
        config = E2EConfig.from_env()
    except RuntimeError as e:
        print(f"E2E config error: {e}", file=sys.stderr)
        return 2

    if args.report:
        config.report_path = args.report

    all_telethon = telethon_units(units)
    omitted = external_units(units)
    if args.realistic_iterations is not None:
        if args.realistic_iterations < 1:
            print("Campaign config error: --realistic-iterations must be >= 1", file=sys.stderr)
            return 2
        results = asyncio.run(
            _run_realistic_iterations(
                config,
                iterations=args.realistic_iterations,
                skip_preflight=args.no_preflight,
            )
        )
        write_report(results, config.report_path)
        print(f"Report written to {config.report_path}")
        has_blocker = any(r.has_blocker for r in results)
        overall_pass = (
            bool(results)
            and not has_blocker
            and all(r.passed for r in results)
        )
        if has_blocker:
            return 2
        return 0 if overall_pass else 1

    if args.pilot:
        try:
            limit = validate_pilot_limit(args.limit)
        except ValueError as e:
            print(f"Campaign config error: {e}", file=sys.stderr)
            return 2
        selected = all_telethon[:limit]
    else:
        if not args.confirm_test_environment:
            print(
                f"Campaign config error: --telethon-full requires "
                "--confirm-test-environment",
                file=sys.stderr,
            )
            return 2
        selected = all_telethon

    results = asyncio.run(
        _run_telethon_units(
            config,
            selected,
            skip_preflight=args.no_preflight,
            wave_size=args.wave_size,
        )
    )

    write_report(results, config.report_path)
    report_path = Path(config.report_path)
    report_path.write_text(
        report_path.read_text(encoding="utf-8")
        + _campaign_footer(selected, omitted),
        encoding="utf-8",
    )
    print(f"Report written to {config.report_path}")

    has_blocker = any(r.has_blocker for r in results)
    overall_pass = (
        bool(results)
        and not has_blocker
        and all(r.passed for r in results)
    )
    if has_blocker:
        return 2
    return 0 if overall_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
