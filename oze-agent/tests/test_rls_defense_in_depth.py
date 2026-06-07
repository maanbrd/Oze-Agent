"""Guardrail G4: RLS deny-all defense-in-depth migration is present & complete.

Static check (no live DB): every sensitive table named in supabase_schema.sql's
RLS-enable block (except `users`, which keeps its own SELECT-own policy) must be
covered by the 20260607_rls_defense_in_depth.sql migration with FORCE RLS and a
RESTRICTIVE deny-all policy. This locks the audit fix in place so a later schema
edit can't silently leave a table world-readable to anon/authenticated.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCHEMA = REPO / "supabase_schema.sql"
MIGRATION = REPO / "supabase_migrations" / "20260607_rls_defense_in_depth.sql"

# Tables intentionally NOT deny-all here (they carry their own policies).
EXCLUDED = {"users"}


def _rls_enabled_tables() -> set[str]:
    text = SCHEMA.read_text(encoding="utf-8")
    found = re.findall(
        r"ALTER TABLE\s+(?:public\.)?(\w+)\s+ENABLE ROW LEVEL SECURITY", text
    )
    return set(found) - EXCLUDED


def test_migration_file_exists():
    assert MIGRATION.exists(), "RLS defense-in-depth migration is missing"


def test_every_sensitive_table_is_denied():
    migration = MIGRATION.read_text(encoding="utf-8")
    missing = [t for t in _rls_enabled_tables() if f"'{t}'" not in migration]
    assert missing == [], f"Tables not covered by deny-all migration: {missing}"


def test_migration_uses_force_and_restrictive_deny():
    migration = MIGRATION.read_text(encoding="utf-8")
    assert "FORCE ROW LEVEL SECURITY" in migration
    assert "AS RESTRICTIVE" in migration
    assert "USING (false)" in migration
    assert "WITH CHECK (false)" in migration


def test_users_table_is_not_locked_to_deny_all():
    # `users` must keep its real SELECT-own policy, not a blanket deny.
    migration = MIGRATION.read_text(encoding="utf-8")
    assert "'users'" not in migration
