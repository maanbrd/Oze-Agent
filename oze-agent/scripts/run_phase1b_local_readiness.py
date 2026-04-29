"""Run the Phase 1B local readiness gate.

Run from `oze-agent/`:
    PYTHONPATH=. python3 scripts/run_phase1b_local_readiness.py
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


FOCUSED_BACKEND_TESTS = [
    "tests/test_phase1b_local_readiness.py",
    "tests/test_phase1b_api_smoke.py",
    "tests/test_phase1b_migrations.py",
    "tests/test_verify_phase1b_env.py",
    "tests/test_billing.py",
    "tests/test_onboarding_api.py",
    "tests/test_dashboard_api.py",
    "tests/test_api_auth.py",
]


@dataclass(frozen=True)
class ReadinessConfig:
    oze_agent_dir: Path
    web_dir: Path
    web_env_file: Path | None = None
    api_env_file: Path | None = None
    web_base_url: str | None = None
    api_base_url: str | None = None
    full_backend: bool = False


@dataclass(frozen=True)
class Step:
    name: str
    command: list[str]
    cwd: Path
    env: dict[str, str] = field(default_factory=dict)
    skip_reason: str | None = None


@dataclass(frozen=True)
class StepResult:
    name: str
    status: str
    command: list[str]
    cwd: Path
    duration_seconds: float
    exit_code: int | None = None
    output: str = ""


def _abs(path: Path | None) -> Path | None:
    if path is None:
        return None
    return path.expanduser().resolve()


def _pythonpath_env() -> dict[str, str]:
    return {"PYTHONPATH": "."}


def build_steps(config: ReadinessConfig) -> list[Step]:
    web_env_args = []
    if config.web_env_file:
        web_env_args = ["--", f"--env-file={_abs(config.web_env_file)}"]

    api_env_args = []
    if config.api_env_file:
        api_env_args = [f"--env-file={_abs(config.api_env_file)}"]

    steps = [
        Step(
            name="web env",
            command=["npm", "run", "check:phase1b-env", *web_env_args],
            cwd=config.web_dir,
        ),
        Step(
            name="web invariants",
            command=["npm", "run", "test:invariants"],
            cwd=config.web_dir,
        ),
        Step(name="web lint", command=["npm", "run", "lint"], cwd=config.web_dir),
        Step(name="web build", command=["npm", "run", "build"], cwd=config.web_dir),
        Step(
            name="api env",
            command=[sys.executable, "scripts/verify_phase1b_env.py", *api_env_args],
            cwd=config.oze_agent_dir,
            env=_pythonpath_env(),
        ),
        Step(
            name="migration preflight",
            command=[sys.executable, "scripts/check_phase1b_migrations.py"],
            cwd=config.oze_agent_dir,
            env=_pythonpath_env(),
        ),
        Step(
            name="focused backend tests",
            command=[
                sys.executable,
                "-m",
                "pytest",
                *FOCUSED_BACKEND_TESTS,
                "-q",
            ],
            cwd=config.oze_agent_dir,
            env=_pythonpath_env(),
        ),
    ]

    if config.web_base_url:
        steps.append(
            Step(
                name="web smoke",
                command=[
                    "npm",
                    "run",
                    "smoke:phase1b-local",
                    "--",
                    f"--base-url={config.web_base_url}",
                ],
                cwd=config.web_dir,
            )
        )
    else:
        steps.append(
            Step(
                name="web smoke",
                command=[],
                cwd=config.web_dir,
                skip_reason="--web-base-url not provided",
            )
        )

    if config.api_base_url:
        steps.append(
            Step(
                name="api smoke",
                command=[
                    sys.executable,
                    "scripts/smoke_phase1b_api.py",
                    f"--base-url={config.api_base_url}",
                ],
                cwd=config.oze_agent_dir,
                env=_pythonpath_env(),
            )
        )
    else:
        steps.append(
            Step(
                name="api smoke",
                command=[],
                cwd=config.oze_agent_dir,
                skip_reason="--api-base-url not provided",
            )
        )

    if config.full_backend:
        steps.append(
            Step(
                name="full backend tests",
                command=[sys.executable, "-m", "pytest", "-q"],
                cwd=config.oze_agent_dir,
                env=_pythonpath_env(),
            )
        )

    return steps


def redact_command(command: list[str]) -> str:
    redacted = []
    for item in command:
        if item.startswith("--env-file="):
            redacted.append("--env-file=<redacted-path>")
        else:
            redacted.append(item)
    return " ".join(redacted)


def _redact_output(output: str) -> str:
    lines = []
    for line in output.splitlines():
        line = re.sub(r"--env-file=\S+", "--env-file=<redacted-path>", line)
        if line.startswith("Loaded env file(s):"):
            lines.append("Loaded env file(s): <redacted>")
        else:
            lines.append(line)
    return "\n".join(lines)


def run_steps(steps: list[Step]) -> list[StepResult]:
    results: list[StepResult] = []
    for step in steps:
        start = time.monotonic()
        if step.skip_reason:
            results.append(
                StepResult(
                    name=step.name,
                    status="skipped",
                    command=step.command,
                    cwd=step.cwd,
                    duration_seconds=0.0,
                    output=step.skip_reason,
                )
            )
            continue

        env = os.environ.copy()
        env.update(step.env)
        completed = subprocess.run(
            step.command,
            cwd=step.cwd,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        duration = time.monotonic() - start
        results.append(
            StepResult(
                name=step.name,
                status="passed" if completed.returncode == 0 else "failed",
                command=step.command,
                cwd=step.cwd,
                duration_seconds=duration,
                exit_code=completed.returncode,
                output=completed.stdout,
            )
        )

    return results


def render_markdown_report(
    results: list[StepResult],
    *,
    started_at: str,
) -> str:
    lines = [
        "# Phase 1B Local Readiness Report",
        "",
        f"- Run date: {started_at}",
        "",
        "| Step | Status | Exit code | Duration | Command |",
        "|---|---:|---:|---:|---|",
    ]

    for result in results:
        exit_code = "" if result.exit_code is None else str(result.exit_code)
        lines.append(
            "| "
            + " | ".join(
                [
                    result.name,
                    result.status,
                    exit_code,
                    f"{result.duration_seconds:.2f}s",
                    f"`{redact_command(result.command)}`" if result.command else "",
                ]
            )
            + " |"
        )

    lines.append("")
    lines.append("## Output")
    for result in results:
        output = _redact_output(result.output).strip()
        if not output:
            continue
        lines.extend(
            [
                "",
                f"### {result.name}",
                "",
                "```text",
                output[-4000:],
                "```",
            ]
        )

    return "\n".join(lines) + "\n"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--web-env-file", type=Path)
    parser.add_argument("--api-env-file", type=Path)
    parser.add_argument("--web-base-url")
    parser.add_argument("--api-base-url")
    parser.add_argument("--full-backend", action="store_true")
    parser.add_argument("--report", type=Path)
    return parser.parse_args()


def _config_from_args(args: argparse.Namespace) -> ReadinessConfig:
    oze_agent_dir = Path(__file__).resolve().parents[1]
    return ReadinessConfig(
        oze_agent_dir=oze_agent_dir,
        web_dir=oze_agent_dir.parent / "web",
        web_env_file=_abs(args.web_env_file),
        api_env_file=_abs(args.api_env_file),
        web_base_url=args.web_base_url,
        api_base_url=args.api_base_url,
        full_backend=args.full_backend,
    )


def main() -> int:
    args = _parse_args()
    started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results = run_steps(build_steps(_config_from_args(args)))
    report = render_markdown_report(results, started_at=started_at)

    if args.report:
        args.report.expanduser().resolve().write_text(report, encoding="utf-8")
        print(f"Phase 1B local readiness report written: {args.report}")
    else:
        print(report)

    failed = [result for result in results if result.status == "failed"]
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
