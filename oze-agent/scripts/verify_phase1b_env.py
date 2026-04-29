"""Verify FastAPI environment needed for Phase 1B readiness.

Run from `oze-agent/`:
    PYTHONPATH=. python3 scripts/verify_phase1b_env.py
"""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping

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


def main() -> int:
    missing, warnings = collect_missing_phase1b_env()
    for warning in warnings:
        print(f"Warning: {warning}")
    if missing:
        print(f"Missing: {', '.join(missing)}")
        return 1
    print("Phase 1B FastAPI env OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
