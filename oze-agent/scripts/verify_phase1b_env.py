"""Verify FastAPI environment needed for Phase 1B readiness.

Run from `oze-agent/`:
    PYTHONPATH=. .venv/bin/python scripts/verify_phase1b_env.py
"""

from __future__ import annotations

import os
import sys
from argparse import ArgumentParser
from collections.abc import Mapping
from pathlib import Path

REQUIRED_ENV = [
    "SUPABASE_URL",
    "SUPABASE_SERVICE_KEY",
    "SUPABASE_JWT_SECRET",
    "BILLING_INTERNAL_SECRET",
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "GOOGLE_REDIRECT_URI",
    "ENCRYPTION_KEY",
    "DASHBOARD_URL",
]

OAUTH_STATE_FALLBACK = "GOOGLE_OAUTH_STATE_SECRET or BILLING_INTERNAL_SECRET"


def _present(env: Mapping[str, str], name: str) -> bool:
    return bool((env.get(name) or "").strip())


def _unquote(value: str) -> str:
    stripped = value.strip()
    if (
        len(stripped) >= 2
        and stripped[0] == stripped[-1]
        and stripped[0] in {"'", '"'}
    ):
        return stripped[1:-1]
    return stripped


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        name, separator, value = line.partition("=")
        if not separator:
            continue
        key = name.strip()
        if key.isidentifier():
            values[key] = _unquote(value)
    return values


def merge_env_file(env: Mapping[str, str], path: str | Path) -> dict[str, str]:
    """Return env plus values from path, keeping existing env values first."""
    merged = dict(env)
    for name, value in _parse_env_file(Path(path)).items():
        merged.setdefault(name, value)
    return merged


def collect_missing_phase1b_env(
    env: Mapping[str, str] | None = None,
) -> tuple[list[str], list[str]]:
    values = os.environ if env is None else env
    missing = [name for name in REQUIRED_ENV if not _present(values, name)]
    warnings: list[str] = []

    if not _present(values, "GOOGLE_OAUTH_STATE_SECRET"):
        if _present(values, "BILLING_INTERNAL_SECRET"):
            warnings.append(
                "GOOGLE_OAUTH_STATE_SECRET is unset; using BILLING_INTERNAL_SECRET fallback for signed OAuth state."
            )
        else:
            missing.append(OAUTH_STATE_FALLBACK)

    return missing, warnings


def _default_env_files() -> list[Path]:
    return [Path(".env.local"), Path(".env")]


def _load_env(args_env_file: str | None) -> tuple[Mapping[str, str], list[Path]]:
    env: Mapping[str, str] = os.environ
    loaded: list[Path] = []

    if args_env_file:
        path = Path(args_env_file)
        env = merge_env_file(env, path)
        loaded.append(path.resolve())
        return env, loaded

    merged = dict(env)
    for path in _default_env_files():
        if path.exists():
            merged = merge_env_file(merged, path)
            loaded.append(path.resolve())
    return merged, loaded


def _parse_args() -> str | None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--env-file",
        help="Load Phase 1B values from a dotenv-style file before checking.",
    )
    return parser.parse_args().env_file


def main() -> int:
    env, loaded = _load_env(_parse_args())
    if loaded:
        print(f"Loaded env file(s): {', '.join(str(path) for path in loaded)}")

    missing, warnings = collect_missing_phase1b_env(env)
    for warning in warnings:
        print(f"Warning: {warning}")
    if missing:
        print(f"Missing: {', '.join(missing)}")
        return 1
    print("Phase 1B FastAPI env OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
