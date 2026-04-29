"""Verify Phase 1B Supabase migration files before staging rollout.

Run from `oze-agent/`:
    PYTHONPATH=. python3 scripts/check_phase1b_migrations.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

DEFAULT_MIGRATION_DIR = Path("supabase_migrations")

REQUIRED_MIGRATION_TOKENS: dict[str, list[str]] = {
    "20260428_web_auth_rls.sql": [
        "auth_user_id",
        "REFERENCES auth.users",
        "idx_users_auth_user_id",
        "handle_new_auth_user",
        "on_auth_user_created",
        "ENABLE ROW LEVEL SECURITY",
        "users_select_own_profile",
        "FOR SELECT",
        "auth.uid() = auth_user_id",
    ],
    "20260428_billing_stripe_0c.sql": [
        "onboarding_survey",
        "stripe_customer_id",
        "stripe_subscription_id",
        "stripe_checkout_session_id",
        "subscription_current_period_end",
        "payment_history",
        "stripe_event_id",
        "idx_payment_history_stripe_event_id",
        "webhook_log",
        "idx_webhook_log_stripe_event_id",
        "billing_outbox",
        "TEXT UNIQUE NOT NULL",
        "CREATE TABLE IF NOT EXISTS",
        "ENABLE ROW LEVEL SECURITY",
    ],
}


def _normalized_source(path: Path) -> str:
    return path.read_text(encoding="utf-8").lower()


def collect_missing_migration_requirements(
    migration_dir: Path = DEFAULT_MIGRATION_DIR,
) -> list[str]:
    missing: list[str] = []
    for filename, tokens in REQUIRED_MIGRATION_TOKENS.items():
        path = migration_dir / filename
        if not path.exists():
            missing.append(f"{filename}: file missing")
            continue

        source = _normalized_source(path)
        for token in tokens:
            if token.lower() not in source:
                missing.append(f"{filename}: missing `{token}`")

    return missing


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--migration-dir",
        default=str(DEFAULT_MIGRATION_DIR),
        help="Directory containing Phase 1B Supabase migration SQL files.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    missing = collect_missing_migration_requirements(Path(args.migration_dir))

    if missing:
        print("Phase 1B migration preflight failed:")
        for item in missing:
            print(f"- {item}")
        return 1

    print("Phase 1B migration preflight OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
