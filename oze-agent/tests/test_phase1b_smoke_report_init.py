import json
from pathlib import Path

import pytest

from scripts.check_phase1b_staging_manifest import EXPECTED_RAILWAY_API_START_COMMAND
from scripts.init_phase1b_smoke_report import (
    SmokeReportInitError,
    init_smoke_report,
    resolve_operator,
)


def _valid_manifest() -> dict:
    web_url = "https://agent-oze-preview.vercel.app"
    return {
        "web_url": web_url,
        "api_url": "https://agent-oze-api-staging.up.railway.app",
        "supabase_url": "https://project-ref.supabase.co",
        "railway_api_start_command": EXPECTED_RAILWAY_API_START_COMMAND,
        "stripe_mode": "test",
        "stripe_lookup_keys": {
            "activation": "agent_oze_activation_199",
            "monthly": "agent_oze_monthly_49",
            "yearly": "agent_oze_yearly_350",
        },
        "stripe_webhook_url": f"{web_url}/api/webhooks/stripe",
        "smoke_email_domain": "staging.agent-oze.example",
    }


def _write_manifest(tmp_path: Path, manifest: dict) -> Path:
    path = tmp_path / "phase1b-staging-manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def _init_report(tmp_path: Path, manifest: dict, **kwargs) -> Path:
    manifest_path = _write_manifest(tmp_path, manifest)
    output_path = tmp_path / "phase1b-smoke-report.md"
    init_smoke_report(
        manifest_path=manifest_path,
        output_path=output_path,
        now_value="2026-04-29T12:34",
        operator="Maan",
        environment="staging",
        git_ref_override=("feat/test", "abc1234"),
        **kwargs,
    )
    return output_path


def test_valid_manifest_creates_report_with_smoke_identity(tmp_path):
    output_path = _init_report(tmp_path, _valid_manifest())

    report = output_path.read_text(encoding="utf-8")

    assert "phase1b+20260429-1234@staging.agent-oze.example" in report
    assert "P1B Smoke 2026-04-29 1234" in report
    assert "_Run date: 2026-04-29 12:34 Europe/Warsaw_" in report


def test_report_contains_public_manifest_values_and_lookup_keys(tmp_path):
    output_path = _init_report(tmp_path, _valid_manifest())

    report = output_path.read_text(encoding="utf-8")

    assert "- Vercel URL: https://agent-oze-preview.vercel.app" in report
    assert "- Railway API URL: https://agent-oze-api-staging.up.railway.app" in report
    assert f"- Railway API start command: `{EXPECTED_RAILWAY_API_START_COMMAND}`" in report
    assert "- Supabase project: https://project-ref.supabase.co" in report
    assert "- Stripe mode: test" in report
    assert "- Activation price ID / lookup key: agent_oze_activation_199" in report
    assert "- Monthly price ID / lookup key: agent_oze_monthly_49" in report
    assert "- Yearly price ID / lookup key: agent_oze_yearly_350" in report


def test_report_contains_git_branch_and_commit(tmp_path):
    output_path = _init_report(tmp_path, _valid_manifest())

    report = output_path.read_text(encoding="utf-8")

    assert "_Branch/commit: feat/test / abc1234_" in report


def test_operator_fallback_uses_user_then_unknown():
    assert resolve_operator(None, {"USER": "maan"}) == "maan"
    assert resolve_operator(None, {"USER": ""}) == "unknown"
    assert resolve_operator("", {}) == "unknown"


def test_report_does_not_include_secret_fields_or_secret_like_values(tmp_path):
    output_path = _init_report(tmp_path, _valid_manifest())

    report = output_path.read_text(encoding="utf-8")

    assert "STRIPE_SECRET_KEY" not in report
    assert "BILLING_INTERNAL_SECRET" not in report
    assert "sk_" not in report
    assert "whsec_" not in report
    assert "service_role" not in report


def test_existing_output_without_force_fails(tmp_path):
    manifest_path = _write_manifest(tmp_path, _valid_manifest())
    output_path = tmp_path / "phase1b-smoke-report.md"
    output_path.write_text("existing", encoding="utf-8")

    with pytest.raises(SmokeReportInitError, match="already exists"):
        init_smoke_report(
            manifest_path=manifest_path,
            output_path=output_path,
            now_value="2026-04-29T12:34",
            operator="Maan",
            environment="staging",
            git_ref_override=("feat/test", "abc1234"),
        )

    assert output_path.read_text(encoding="utf-8") == "existing"


def test_invalid_manifest_fails_and_does_not_create_report(tmp_path):
    manifest = _valid_manifest()
    manifest["stripe_mode"] = "live"
    manifest_path = _write_manifest(tmp_path, manifest)
    output_path = tmp_path / "phase1b-smoke-report.md"

    with pytest.raises(SmokeReportInitError, match="manifest preflight failed"):
        init_smoke_report(
            manifest_path=manifest_path,
            output_path=output_path,
            now_value="2026-04-29T12:34",
            operator="Maan",
            environment="staging",
            git_ref_override=("feat/test", "abc1234"),
        )

    assert not output_path.exists()


def test_manifest_with_secret_fails_and_does_not_create_report(tmp_path):
    manifest = _valid_manifest()
    manifest["STRIPE_SECRET_KEY"] = "sk_test_secret"
    manifest_path = _write_manifest(tmp_path, manifest)
    output_path = tmp_path / "phase1b-smoke-report.md"

    with pytest.raises(SmokeReportInitError, match="manifest preflight failed"):
        init_smoke_report(
            manifest_path=manifest_path,
            output_path=output_path,
            now_value="2026-04-29T12:34",
            operator="Maan",
            environment="staging",
            git_ref_override=("feat/test", "abc1234"),
        )

    assert not output_path.exists()
