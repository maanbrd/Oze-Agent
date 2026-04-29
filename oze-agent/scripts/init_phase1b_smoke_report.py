"""Initialize a Phase 1B staging smoke report from a validated manifest.

Run from `oze-agent/`:
    PYTHONPATH=. python3 scripts/init_phase1b_smoke_report.py \
      --manifest ../docs/phase1b-staging-manifest.example.json \
      --output ../docs/phase1b-smoke-report-YYYYMMDD-HHMM.md
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Mapping

from scripts.check_phase1b_staging_manifest import (
    WARSAW,
    generate_smoke_identity,
    validate_manifest,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TEMPLATE_PATH = REPO_ROOT / "docs" / "PHASE1B_SMOKE_REPORT_TEMPLATE.md"


class SmokeReportInitError(RuntimeError):
    """Raised when the smoke report cannot be safely initialized."""


def parse_now(value: str | None) -> datetime:
    if not value:
        return datetime.now(WARSAW)
    return datetime.strptime(value, "%Y-%m-%dT%H:%M").replace(tzinfo=WARSAW)


def resolve_operator(operator: str | None, environ: Mapping[str, str] | None = None) -> str:
    if operator and operator.strip():
        return operator.strip()
    env = os.environ if environ is None else environ
    fallback = env.get("USER", "").strip()
    return fallback or "unknown"


def read_git_ref(repo_root: Path) -> tuple[str, str]:
    try:
        branch = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--abbrev-ref", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        commit = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--short", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SmokeReportInitError("Unable to read git branch/commit from repo root.") from exc

    if not branch or not commit:
        raise SmokeReportInitError("Unable to read git branch/commit from repo root.")
    return branch, commit


def _load_manifest(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SmokeReportInitError(f"Unable to read manifest: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SmokeReportInitError(f"Manifest is not valid JSON: {path}") from exc

    if not isinstance(data, dict):
        raise SmokeReportInitError("Manifest must be a JSON object.")
    return data


def _replace_prefixed_line(text: str, prefix: str, replacement: str) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.startswith(prefix):
            lines[index] = replacement
            return "\n".join(lines) + "\n"
    raise SmokeReportInitError(f"Template is missing expected line prefix: {prefix}")


def render_smoke_report(
    *,
    template: str,
    manifest: dict,
    run_at: datetime,
    branch: str,
    commit: str,
    operator: str,
    environment: str,
) -> str:
    lookup_keys = manifest["stripe_lookup_keys"]
    identity = generate_smoke_identity(manifest["smoke_email_domain"], run_at)

    replacements = [
        ("_Run date:", f"_Run date: {run_at.astimezone(WARSAW):%Y-%m-%d %H:%M} Europe/Warsaw_"),
        ("_Branch/commit:", f"_Branch/commit: {branch} / {commit}_"),
        ("_Operator:", f"_Operator: {operator}_"),
        ("_Environment:", f"_Environment: {environment}_"),
        ("- Email:", f"- Email: `{identity.email}`"),
        ("- Google resource prefix:", f"- Google resource prefix: `{identity.google_resource_prefix}`"),
        ("- Vercel URL:", f"- Vercel URL: {manifest['web_url']}"),
        ("- Railway API URL:", f"- Railway API URL: {manifest['api_url']}"),
        (
            "- Railway API start command:",
            f"- Railway API start command: `{manifest['railway_api_start_command']}`",
        ),
        ("- Supabase project:", f"- Supabase project: {manifest['supabase_url']}"),
        ("- Stripe mode:", f"- Stripe mode: {manifest['stripe_mode']}"),
        (
            "- Activation price ID / lookup key:",
            f"- Activation price ID / lookup key: {lookup_keys['activation']}",
        ),
        (
            "- Monthly price ID / lookup key:",
            f"- Monthly price ID / lookup key: {lookup_keys['monthly']}",
        ),
        (
            "- Yearly price ID / lookup key:",
            f"- Yearly price ID / lookup key: {lookup_keys['yearly']}",
        ),
    ]

    rendered = template
    for prefix, replacement in replacements:
        rendered = _replace_prefixed_line(rendered, prefix, replacement)
    return rendered


def init_smoke_report(
    *,
    manifest_path: Path,
    output_path: Path,
    now_value: str | None = None,
    operator: str | None = None,
    environment: str = "staging",
    force: bool = False,
    repo_root: Path = REPO_ROOT,
    template_path: Path = DEFAULT_TEMPLATE_PATH,
    git_ref_override: tuple[str, str] | None = None,
) -> Path:
    if environment not in {"staging", "local"}:
        raise SmokeReportInitError("environment must be `staging` or `local`.")

    if output_path.exists() and not force:
        raise SmokeReportInitError(f"Output already exists: {output_path}")
    if not output_path.parent.exists():
        raise SmokeReportInitError(f"Output directory does not exist: {output_path.parent}")
    if not template_path.exists():
        raise SmokeReportInitError(f"Smoke report template does not exist: {template_path}")

    manifest = _load_manifest(manifest_path)
    errors = validate_manifest(manifest)
    if errors:
        details = "\n".join(f"- {error}" for error in errors)
        raise SmokeReportInitError(f"manifest preflight failed:\n{details}")

    branch, commit = git_ref_override or read_git_ref(repo_root)
    template = template_path.read_text(encoding="utf-8")
    run_at = parse_now(now_value)

    report = render_smoke_report(
        template=template,
        manifest=manifest,
        run_at=run_at,
        branch=branch,
        commit=commit,
        operator=resolve_operator(operator),
        environment=environment,
    )
    output_path.write_text(report, encoding="utf-8")
    return output_path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--now", help="Deterministic Europe/Warsaw time: YYYY-MM-DDTHH:MM")
    parser.add_argument("--operator")
    parser.add_argument("--environment", choices=["staging", "local"], default="staging")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        output_path = init_smoke_report(
            manifest_path=args.manifest,
            output_path=args.output,
            now_value=args.now,
            operator=args.operator,
            environment=args.environment,
            force=args.force,
        )
    except SmokeReportInitError as exc:
        print(f"Phase 1B smoke report init failed: {exc}", file=sys.stderr)
        return 1

    print(f"Phase 1B smoke report initialized: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
