import json

from scripts.check_phase1b_staging_manifest import EXPECTED_RAILWAY_API_START_COMMAND
from scripts.validate_phase1b_smoke_report import main, validate_report_text


def _completed_report() -> str:
    return f"""# Phase 1B Smoke Report

_Run date: 2026-04-29 12:34 Europe/Warsaw_
_Branch/commit: feat/web-phase-0c / 53bba91_
_Operator: Maan_
_Environment: staging_

## Smoke Account

- Email: `phase1b+20260429-1234@staging.agent-oze.example`
- Supabase auth user ID: auth-user-123
- Supabase public user ID: public-user-123
- Google resource prefix: `P1B Smoke 2026-04-29 1234`

## Local Readiness

- `cd web && npm run check:phase1b-env`: pass
- `cd web && npm run test:invariants && npm run lint && npm run build`: pass
- `cd oze-agent && PYTHONPATH=. python3 scripts/verify_phase1b_env.py`: pass
- `cd oze-agent && PYTHONPATH=. pytest tests/test_billing.py tests/test_onboarding_api.py tests/test_dashboard_api.py tests/test_api_auth.py -q`: pass
- `cd oze-agent && PYTHONPATH=. pytest -q`: pass

## Staging Services

- Vercel URL: https://agent-oze-preview.vercel.app
- Railway API URL: https://agent-oze-api-staging.up.railway.app
- Railway API start command: `{EXPECTED_RAILWAY_API_START_COMMAND}`
- Railway bot service: agent-oze-bot-staging
- Supabase project: https://project-ref.supabase.co
- Stripe mode: test

## Stripe Sandbox

- Product ID: prod_123
- Activation price ID / lookup key: agent_oze_activation_199
- Monthly price ID / lookup key: agent_oze_monthly_49
- Yearly price ID / lookup key: agent_oze_yearly_350
- Checkout Session ID: cs_test_123
- Customer ID: cus_123
- Subscription ID: sub_123
- Invoice ID: in_123
- Webhook event IDs: evt_checkout, evt_invoice
- Replay event ID: evt_checkout
- Duplicate rows with same `stripe_event_id`: no

## Supabase Verification

- `users.subscription_status = active`: yes
- `users.activation_paid = true`: yes
- `payment_history` row: payment_history.id=payhist-123
- `webhook_log.processed = true`: webhook_log.id=webhook-123
- `billing_outbox` row: billing_outbox.id=outbox-123

## Onboarding Continuation

- Google OAuth redirect succeeded: yes
- Sheets ID: sheet-123
- Calendar ID: calendar-123
- Drive folder ID: drive-123
- Telegram pairing code shown: yes
- Telegram `/start <code>` consumed: yes
- `users.telegram_id` linked: yes

## Browser Smoke

- `/rejestracja`: pass
- `/login`: pass
- `/onboarding/platnosc`: pass
- `/onboarding/google`: pass
- `/onboarding/zasoby`: pass
- `/onboarding/telegram`: pass
- `/dashboard`: pass
- `/klienci`: pass
- `/kalendarz`: pass
- Completed user source state is `live` or `unavailable`: yes
- CRM mutation forms absent: yes

## Issues

- Blockers: brak
- Follow-ups: brak
- Cleanup required: brak
"""


def test_valid_completed_report_passes():
    result = validate_report_text(_completed_report())

    assert result.ok
    assert result.errors == []
    assert result.warnings == []


def test_template_report_fails_with_placeholders():
    template = open("../docs/PHASE1B_SMOKE_REPORT_TEMPLATE.md", encoding="utf-8").read()

    result = validate_report_text(template)

    assert not result.ok
    assert any("placeholder" in error for error in result.errors)


def test_rejects_empty_required_fields():
    report = _completed_report().replace("- Customer ID: cus_123", "- Customer ID:")

    result = validate_report_text(report)

    assert any("Customer ID" in error for error in result.errors)


def test_rejects_empty_local_readiness_results():
    report = _completed_report().replace(
        "- `cd web && npm run check:phase1b-env`: pass",
        "- `cd web && npm run check:phase1b-env`:",
    )

    result = validate_report_text(report)

    assert any("cd web && npm run check:phase1b-env" in error for error in result.errors)


def test_rejects_local_environment():
    report = _completed_report().replace("_Environment: staging_", "_Environment: local_")

    result = validate_report_text(report)

    assert any("Environment" in error and "staging" in error for error in result.errors)


def test_rejects_http_service_urls():
    report = _completed_report().replace(
        "- Vercel URL: https://agent-oze-preview.vercel.app",
        "- Vercel URL: http://agent-oze-preview.vercel.app",
    )

    result = validate_report_text(report)

    assert any("Vercel URL" in error and "https" in error for error in result.errors)


def test_requires_exact_railway_start_command():
    report = _completed_report().replace(
        EXPECTED_RAILWAY_API_START_COMMAND,
        "python -m bot.main",
    )

    result = validate_report_text(report)

    assert any("Railway API start command" in error for error in result.errors)


def test_rejects_live_mode():
    report = _completed_report().replace("- Stripe mode: test", "- Stripe mode: live")

    result = validate_report_text(report)

    assert any("Stripe mode" in error for error in result.errors)


def test_requires_duplicate_rows_no():
    report = _completed_report().replace(
        '- Duplicate rows with same `stripe_event_id`: no',
        '- Duplicate rows with same `stripe_event_id`: yes',
    )

    result = validate_report_text(report)

    assert any("Duplicate rows" in error for error in result.errors)


def test_allows_subscription_id_na_with_activation_only_note():
    report = _completed_report().replace(
        "- Subscription ID: sub_123",
        "- Subscription ID: n/a - activation-only no-subscription smoke",
    )

    result = validate_report_text(report)

    assert result.ok


def test_rejects_subscription_id_na_without_explanation():
    report = _completed_report().replace("- Subscription ID: sub_123", "- Subscription ID: n/a")

    result = validate_report_text(report)

    assert any("Subscription ID" in error for error in result.errors)


def test_rejects_secret_like_values():
    report = _completed_report() + "\nDebug value: whsec_secret\nSUPABASE_SERVICE_KEY=service_role\n"

    result = validate_report_text(report)

    assert any("secret" in error.lower() for error in result.errors)


def test_blockers_and_cleanup_required_fail():
    report = _completed_report().replace("- Blockers: brak", "- Blockers: webhook failed")
    report = report.replace("- Cleanup required: brak", "- Cleanup required: rotate test key")

    result = validate_report_text(report)

    assert any("Blockers" in error for error in result.errors)
    assert any("Cleanup required" in error for error in result.errors)


def test_followups_are_warning_only():
    report = _completed_report().replace("- Follow-ups: brak", "- Follow-ups: poprawić copy")

    result = validate_report_text(report)

    assert result.ok
    assert any("Follow-ups" in warning for warning in result.warnings)


def test_json_output_reports_errors_and_warnings(tmp_path, capsys):
    report = _completed_report().replace("- Follow-ups: brak", "- Follow-ups: poprawić copy")
    report = report.replace("- Stripe mode: test", "- Stripe mode: live")
    path = tmp_path / "phase1b-smoke-report.md"
    path.write_text(report, encoding="utf-8")

    exit_code = main(["--report", str(path), "--json"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert output["ok"] is False
    assert any("Stripe mode" in error for error in output["errors"])
    assert any("Follow-ups" in warning for warning in output["warnings"])
