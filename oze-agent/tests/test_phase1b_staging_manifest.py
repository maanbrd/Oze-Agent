from datetime import datetime
from zoneinfo import ZoneInfo

from scripts.check_phase1b_staging_manifest import (
    EXPECTED_RAILWAY_API_START_COMMAND,
    generate_smoke_identity,
    validate_manifest,
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


def test_valid_manifest_passes():
    assert validate_manifest(_valid_manifest()) == []


def test_rejects_live_mode():
    manifest = _valid_manifest()
    manifest["stripe_mode"] = "live"

    errors = validate_manifest(manifest)

    assert any("stripe_mode" in error and "test" in error for error in errors)


def test_requires_https_urls():
    manifest = _valid_manifest()
    manifest["web_url"] = "http://agent-oze-preview.vercel.app"
    manifest["api_url"] = "http://agent-oze-api-staging.up.railway.app"
    manifest["supabase_url"] = "http://project-ref.supabase.co"
    manifest["stripe_webhook_url"] = "http://agent-oze-preview.vercel.app/api/webhooks/stripe"

    errors = validate_manifest(manifest)

    assert any("web_url" in error and "https" in error for error in errors)
    assert any("api_url" in error and "https" in error for error in errors)
    assert any("supabase_url" in error and "https" in error for error in errors)
    assert any("stripe_webhook_url" in error and "https" in error for error in errors)


def test_requires_distinct_web_and_api_origins():
    manifest = _valid_manifest()
    manifest["api_url"] = "https://agent-oze-preview.vercel.app/api"

    errors = validate_manifest(manifest)

    assert any("web_url and api_url must use different origins" in error for error in errors)


def test_requires_exact_webhook_url():
    manifest = _valid_manifest()
    manifest["web_url"] = "https://agent-oze-preview.vercel.app/"
    manifest["stripe_webhook_url"] = "https://agent-oze-preview.vercel.app/api/stripe"

    errors = validate_manifest(manifest)

    assert any("${web_url}/api/webhooks/stripe" in error for error in errors)


def test_requires_exact_railway_start_command():
    manifest = _valid_manifest()
    manifest["railway_api_start_command"] = "python -m bot.main"

    errors = validate_manifest(manifest)

    assert any("railway_api_start_command" in error for error in errors)


def test_rejects_secret_keys_and_secret_values():
    manifest = _valid_manifest()
    manifest["STRIPE_SECRET_KEY"] = "sk_test_secret"
    manifest["stripe_webhook_secret"] = "whsec_secret"
    manifest["billing"] = {"BILLING_INTERNAL_SECRET": "not-public"}
    manifest["supabase"] = {"service": "service_role_token"}

    errors = validate_manifest(manifest)

    assert any("STRIPE_SECRET_KEY" in error for error in errors)
    assert any("stripe_webhook_secret" in error for error in errors)
    assert any("BILLING_INTERNAL_SECRET" in error for error in errors)
    assert any("service_role" in error for error in errors)


def test_rejects_invalid_smoke_email_domain():
    for value in [
        "",
        "phase1b@example.com",
        "https://example.com",
        "example",
        "bad domain.example",
    ]:
        manifest = _valid_manifest()
        manifest["smoke_email_domain"] = value

        errors = validate_manifest(manifest)

        assert any("smoke_email_domain" in error for error in errors)


def test_generate_smoke_identity():
    now = datetime(2026, 4, 29, 12, 34, tzinfo=ZoneInfo("Europe/Warsaw"))

    identity = generate_smoke_identity("staging.agent-oze.example", now)

    assert identity.email == "phase1b+20260429-1234@staging.agent-oze.example"
    assert identity.google_resource_prefix == "P1B Smoke 2026-04-29 1234"
