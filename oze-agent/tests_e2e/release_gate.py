"""Controlled release gate for Agent OZE E2E hardening.

This module is intentionally non-mutating by default. It validates that a
pre-production E2E run targets the test bot/test Railway service and prints the
exact commands that make up the release-risk pack.
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass, field
from pathlib import Path

import tests_e2e.scenarios  # noqa: F401 - populate registry
from tests_e2e.scenarios._base import list_categories


TEST_BOT_USERNAME = "@OZEAgentTestBot"
TEST_RAILWAY_SERVICE = "bot-test"

RELEASE_GATE_CATEGORIES: tuple[str, ...] = (
    "routing",
    "card_structure",
    "error_path",
    "read_only",
    "rules",
    "notes",
    "polish_edge",
    "mutating_core",
    "photo_flow",
)


@dataclass(frozen=True)
class GateCommand:
    """A command a release manager can run from `oze-agent/`."""

    argv: tuple[str, ...]

    def render(self) -> str:
        return " ".join(self.argv)


@dataclass
class GateFindings:
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.blockers

    def add_blocker(self, message: str) -> None:
        self.blockers.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def add_info(self, message: str) -> None:
        self.info.append(message)


def _norm_bot(value: str) -> str:
    value = value.strip()
    if value and not value.startswith("@"):
        value = "@" + value
    return value


def validate_release_environment(
    *,
    bot_username: str,
    railway_service: str,
    allow_prod_bot: bool,
    include_offer_send: bool,
    offer_recipient: str,
) -> GateFindings:
    """Validate env safety before live E2E or controlled Gmail smoke.

    The default gate is for `bot-test` only. Production smoke is possible, but
    must be explicit through `allow_prod_bot=True`.
    """
    findings = GateFindings()
    bot = _norm_bot(bot_username)
    service = railway_service.strip()

    if not bot:
        findings.add_blocker("TELEGRAM_E2E_BOT_USERNAME is not set")
    elif bot != TEST_BOT_USERNAME and not allow_prod_bot:
        findings.add_blocker(
            f"bot username {bot!r} is not {TEST_BOT_USERNAME}; pass "
            "--allow-prod-bot only for the small production smoke subset"
        )
    else:
        findings.add_info(f"bot username OK: {bot}")

    if not service:
        findings.add_blocker("TELEGRAM_E2E_RAILWAY_SERVICE is not set")
    elif service != TEST_RAILWAY_SERVICE and not allow_prod_bot:
        findings.add_blocker(
            f"Railway service {service!r} is not {TEST_RAILWAY_SERVICE}; pass "
            "--allow-prod-bot only for production smoke"
        )
    else:
        findings.add_info(f"Railway service OK: {service}")

    registered = set(list_categories())
    missing = set(RELEASE_GATE_CATEGORIES) - registered
    if missing:
        findings.add_blocker(
            "release gate categories missing from registry: "
            + ", ".join(sorted(missing))
        )
    else:
        findings.add_info(
            "release gate categories present: "
            + ", ".join(RELEASE_GATE_CATEGORIES)
        )

    if include_offer_send:
        recipient = offer_recipient.strip()
        if not recipient:
            findings.add_blocker(
                "TELEGRAM_E2E_OFFER_RECIPIENT is required for controlled "
                "Gmail offer-send smoke"
            )
        elif "@" not in recipient:
            findings.add_blocker(
                "TELEGRAM_E2E_OFFER_RECIPIENT must be an email address"
            )
        else:
            findings.add_info(f"controlled offer recipient configured: {recipient}")

    if allow_prod_bot:
        findings.add_warning(
            "production bot override enabled; run only the minimal smoke subset "
            "on controlled data"
        )

    return findings


def validate_environment_from_env(
    *,
    allow_prod_bot: bool = False,
    include_offer_send: bool = False,
) -> GateFindings:
    return validate_release_environment(
        bot_username=os.getenv("TELEGRAM_E2E_BOT_USERNAME", ""),
        railway_service=os.getenv("TELEGRAM_E2E_RAILWAY_SERVICE", ""),
        allow_prod_bot=allow_prod_bot,
        include_offer_send=include_offer_send,
        offer_recipient=os.getenv("TELEGRAM_E2E_OFFER_RECIPIENT", ""),
    )


def build_release_gate_commands(
    *,
    report_dir: str = "output/smoke/release-gate",
) -> list[GateCommand]:
    """Return the canonical command sequence for bot-test release gating."""
    report = Path(report_dir)
    wrapper = "./tests_e2e/run_release_gate.sh"
    commands: list[GateCommand] = [
        GateCommand((wrapper, "pytest-tests")),
        GateCommand((wrapper, "list")),
        GateCommand(
            (
                wrapper,
                "google-health",
                "--report",
                str(report / "google-health.md"),
            )
        ),
        GateCommand((wrapper, "seed")),
    ]
    for category in RELEASE_GATE_CATEGORIES:
        commands.append(
            GateCommand(
                (
                    wrapper,
                    "category",
                    category,
                    "--report",
                    str(report / f"{category}.md"),
                )
            )
        )
    commands.append(GateCommand((wrapper, "cleanup")))
    return commands


def _render_findings(findings: GateFindings) -> str:
    lines: list[str] = []
    status = "OK" if findings.ok else "BLOCKED"
    lines.append(f"Release gate environment: {status}")
    for message in findings.blockers:
        lines.append(f"BLOCKER: {message}")
    for message in findings.warnings:
        lines.append(f"WARNING: {message}")
    for message in findings.info:
        lines.append(f"INFO: {message}")
    return "\n".join(lines)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m tests_e2e.release_gate",
        description="Validate E2E release-gate env and print the command pack.",
    )
    parser.add_argument("--allow-prod-bot", action="store_true")
    parser.add_argument("--include-offer-send", action="store_true")
    parser.add_argument(
        "--report-dir",
        default="output/smoke/release-gate",
        help="Directory used in generated E2E report command paths.",
    )
    parser.add_argument(
        "--commands-only",
        action="store_true",
        help="Print commands without environment validation.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if not args.commands_only:
        findings = validate_environment_from_env(
            allow_prod_bot=args.allow_prod_bot,
            include_offer_send=args.include_offer_send,
        )
        print(_render_findings(findings))
        if not findings.ok:
            return 2
        print()

    print("Release gate commands (run from oze-agent/):")
    for i, command in enumerate(
        build_release_gate_commands(report_dir=args.report_dir),
        start=1,
    ):
        print(f"{i:02d}. {command.render()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
