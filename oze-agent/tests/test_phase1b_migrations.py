from pathlib import Path

from scripts.check_phase1b_migrations import collect_missing_migration_requirements


def test_phase1b_migration_checker_accepts_repo_migrations():
    missing = collect_missing_migration_requirements(Path("supabase_migrations"))

    assert missing == []


def test_phase1b_migration_checker_reports_missing_tokens(tmp_path):
    migration_dir = tmp_path / "migrations"
    migration_dir.mkdir()
    (migration_dir / "20260428_web_auth_rls.sql").write_text(
        "ALTER TABLE public.users ADD COLUMN IF NOT EXISTS auth_user_id UUID;",
        encoding="utf-8",
    )
    (migration_dir / "20260428_billing_stripe_0c.sql").write_text(
        "CREATE TABLE IF NOT EXISTS public.billing_outbox (id UUID);",
        encoding="utf-8",
    )

    missing = collect_missing_migration_requirements(migration_dir)

    assert any("users_select_own_profile" in item for item in missing)
    assert any("idx_payment_history_stripe_event_id" in item for item in missing)
