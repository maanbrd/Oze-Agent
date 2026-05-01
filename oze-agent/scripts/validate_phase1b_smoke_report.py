"""Validate a completed Phase 1B smoke report.

Run from `oze-agent/`:
    PYTHONPATH=. .venv/bin/python scripts/validate_phase1b_smoke_report.py \
      --report ../docs/phase1b-smoke-report-YYYYMMDD-HHMM.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from scripts.check_phase1b_staging_manifest import EXPECTED_RAILWAY_API_START_COMMAND

PLACEHOLDER_PATTERNS = ("YYYY", "<staging-test-domain>", "yes / no")
SECRET_PATTERNS = (
    "STRIPE_SECRET_KEY",
    "SUPABASE_SERVICE_KEY",
    "BILLING_INTERNAL_SECRET",
    "sk_",
    "whsec_",
    "rk_",
    "eyJ",
    "service_role",
)
EMPTY_OK = {"brak", "none", "n/a", "-", ""}
EXPECTED_LOOKUP_KEYS = {
    "Activation price ID / lookup key": "agent_oze_activation_199",
    "Monthly price ID / lookup key": "agent_oze_monthly_49",
    "Yearly price ID / lookup key": "agent_oze_yearly_350",
}


@dataclass(frozen=True)
class ValidationResult:
    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict:
        return {"ok": self.ok, "errors": self.errors, "warnings": self.warnings}


def _strip_formatting(value: str) -> str:
    return value.strip().strip("_").strip().strip("`").strip()


def _field_value(text: str, label: str) -> str | None:
    marker = f"{label}:"
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith(("- ", "_")):
            continue
        content = stripped[2:] if stripped.startswith("- ") else stripped
        content = content.strip("_").strip()
        if content.startswith(marker):
            return _strip_formatting(content[len(marker) :])
    return None


def _require_filled(fields: dict[str, str | None], errors: list[str]) -> None:
    for label, value in fields.items():
        if value is None or not value.strip():
            errors.append(f"{label} is required.")


def _require_yes(label: str, value: str | None, errors: list[str]) -> None:
    if value != "yes":
        errors.append(f"{label} must be `yes`.")


def _require_https_url(label: str, value: str | None, errors: list[str]) -> None:
    if value is None or not value:
        errors.append(f"{label} is required.")
        return
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        errors.append(f"{label} must be an https URL.")


def _require_id_or_na_with_explanation(
    label: str,
    value: str | None,
    prefix: str,
    explanation_terms: tuple[str, ...],
    errors: list[str],
) -> None:
    if value is None or not value.strip():
        errors.append(f"{label} is required.")
        return
    normalized = value.strip().lower()
    if normalized.startswith(f"{prefix.lower()}_"):
        return
    if normalized.startswith("n/a") and all(term in normalized for term in explanation_terms):
        return
    errors.append(
        f"{label} must be a `{prefix}_...` ID or explicit `n/a` with "
        f"{' + '.join(explanation_terms)} explanation."
    )


def _is_empty_ok(value: str | None) -> bool:
    if value is None:
        return True
    return value.strip().lower() in EMPTY_OK


def _validate_global_text(text: str, errors: list[str]) -> None:
    for pattern in PLACEHOLDER_PATTERNS:
        if pattern in text:
            errors.append(f"Report contains unresolved placeholder `{pattern}`.")

    lower_text = text.lower()
    if "livemode: true" in lower_text:
        errors.append("Report contains `livemode: true`.")

    for pattern in SECRET_PATTERNS:
        if pattern.lower() in lower_text:
            errors.append(f"Report contains secret-looking value `{pattern}`.")

    if "not applied to staging" in lower_text:
        errors.append("Report says a required item is not applied to staging.")


def _validate_metadata(text: str, errors: list[str]) -> None:
    fields = {
        "Run date": _field_value(text, "Run date"),
        "Branch/commit": _field_value(text, "Branch/commit"),
        "Operator": _field_value(text, "Operator"),
        "Environment": _field_value(text, "Environment"),
    }
    _require_filled(fields, errors)
    if fields["Environment"] and fields["Environment"] != "staging":
        errors.append("Environment must be `staging`.")


def _validate_smoke_account(text: str, errors: list[str]) -> None:
    fields = {
        "Email": _field_value(text, "Email"),
        "Supabase auth user ID": _field_value(text, "Supabase auth user ID"),
        "Supabase public user ID": _field_value(text, "Supabase public user ID"),
        "Google resource prefix": _field_value(text, "Google resource prefix"),
    }
    _require_filled(fields, errors)
    email = fields["Email"] or ""
    if email and not re.fullmatch(
        r"phase1b\+(?:\d{8}-\d{4}|\d{13})@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        email,
    ):
        errors.append("Email must use phase1b+YYYYMMDD-HHMM@domain or phase1b+timestamp@domain format.")


def _validate_local_readiness(text: str, errors: list[str]) -> None:
    commands = [
        "`cd web && npm run check:phase1b-env`",
        "`cd web && npm run test:invariants && npm run lint && npm run build`",
        "`cd oze-agent && PYTHONPATH=. .venv/bin/python scripts/verify_phase1b_env.py`",
        "`cd oze-agent && PYTHONPATH=. .venv/bin/python -m pytest tests/test_billing.py tests/test_onboarding_api.py tests/test_dashboard_api.py tests/test_api_auth.py -q`",
        "`cd oze-agent && PYTHONPATH=. .venv/bin/python -m pytest -q`",
    ]
    _require_filled({command.strip("`"): _field_value(text, command) for command in commands}, errors)


def _validate_services(text: str, errors: list[str]) -> None:
    _require_https_url("Vercel URL", _field_value(text, "Vercel URL"), errors)
    _require_https_url("Railway API URL", _field_value(text, "Railway API URL"), errors)
    _require_https_url("Supabase project", _field_value(text, "Supabase project"), errors)

    railway_command = _field_value(text, "Railway API start command")
    if railway_command != EXPECTED_RAILWAY_API_START_COMMAND:
        errors.append("Railway API start command must match the Phase 1B command.")

    if _field_value(text, "Stripe mode") != "test":
        errors.append("Stripe mode must be `test`.")

    _require_filled({"Railway bot service": _field_value(text, "Railway bot service")}, errors)


def _validate_stripe(text: str, errors: list[str]) -> None:
    required = {
        "Product ID": _field_value(text, "Product ID"),
        "Checkout Session ID": _field_value(text, "Checkout Session ID"),
        "Customer ID": _field_value(text, "Customer ID"),
        "Webhook event IDs": _field_value(text, "Webhook event IDs"),
        "Replay event ID": _field_value(text, "Replay event ID"),
    }
    _require_filled(required, errors)
    _require_id_or_na_with_explanation(
        "Invoice ID",
        _field_value(text, "Invoice ID"),
        "in",
        ("activation-only", "no-invoice"),
        errors,
    )

    for label, expected in EXPECTED_LOOKUP_KEYS.items():
        if _field_value(text, label) != expected:
            errors.append(f"{label} must be `{expected}`.")

    subscription_id = _field_value(text, "Subscription ID")
    if not subscription_id:
        errors.append("Subscription ID is required or must be explicit `n/a` with explanation.")
    elif subscription_id.lower() == "n/a":
        lower_text = text.lower()
        if "activation-only" not in lower_text or "no-subscription" not in lower_text:
            errors.append("Subscription ID `n/a` requires activation-only no-subscription explanation.")

    duplicate_rows = _field_value(text, "Duplicate rows with same `stripe_event_id`")
    if duplicate_rows != "no":
        errors.append("Duplicate rows with same stripe_event_id must be `no`.")


def _validate_supabase(text: str, errors: list[str]) -> None:
    _require_yes("users.subscription_status = active", _field_value(text, "`users.subscription_status = active`"), errors)
    _require_yes("users.activation_paid = true", _field_value(text, "`users.activation_paid = true`"), errors)
    _require_filled(
        {
            "payment_history row": _field_value(text, "`payment_history` row"),
            "webhook_log.processed = true": _field_value(text, "`webhook_log.processed = true`"),
            "billing_outbox row": _field_value(text, "`billing_outbox` row"),
        },
        errors,
    )


def _validate_onboarding(text: str, errors: list[str]) -> None:
    for label in [
        "Google OAuth redirect succeeded",
        "Telegram pairing code shown",
        "Telegram `/start <code>` consumed",
        "`users.telegram_id` linked",
    ]:
        _require_yes(label.replace("`", ""), _field_value(text, label), errors)

    _require_filled(
        {
            "Sheets ID": _field_value(text, "Sheets ID"),
            "Calendar ID": _field_value(text, "Calendar ID"),
            "Drive folder ID": _field_value(text, "Drive folder ID"),
        },
        errors,
    )


def _validate_browser(text: str, errors: list[str]) -> None:
    route_labels = [
        "/rejestracja",
        "/login",
        "/onboarding/platnosc",
        "/onboarding/google",
        "/onboarding/zasoby",
        "/onboarding/telegram",
        "/dashboard",
        "/klienci",
        "/kalendarz",
    ]
    _require_filled({label: _field_value(text, f"`{label}`") for label in route_labels}, errors)
    _require_yes(
        "Completed user source state is live or unavailable",
        _field_value(text, "Completed user source state is `live` or `unavailable`"),
        errors,
    )
    _require_yes("CRM mutation forms absent", _field_value(text, "CRM mutation forms absent"), errors)


def _validate_issues(text: str, errors: list[str], warnings: list[str]) -> None:
    blockers = _field_value(text, "Blockers")
    cleanup = _field_value(text, "Cleanup required")
    followups = _field_value(text, "Follow-ups")

    if not _is_empty_ok(blockers):
        errors.append("Blockers must be empty or explicitly `brak`/`none`/`n/a`/`-`.")
    if not _is_empty_ok(cleanup):
        errors.append("Cleanup required must be empty or explicitly `brak`/`none`/`n/a`/`-`.")
    if not _is_empty_ok(followups):
        warnings.append("Follow-ups are present; they do not block Phase 1B readiness.")


def validate_report_text(text: str) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    _validate_global_text(text, errors)
    _validate_metadata(text, errors)
    _validate_smoke_account(text, errors)
    _validate_local_readiness(text, errors)
    _validate_services(text, errors)
    _validate_stripe(text, errors)
    _validate_supabase(text, errors)
    _validate_onboarding(text, errors)
    _validate_browser(text, errors)
    _validate_issues(text, errors, warnings)

    return ValidationResult(errors=errors, warnings=warnings)


def validate_report_file(path: Path) -> ValidationResult:
    return validate_report_text(path.read_text(encoding="utf-8"))


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    result = validate_report_file(args.report)

    if args.json:
        print(json.dumps(result.as_dict(), ensure_ascii=False, indent=2))
        return 0 if result.ok else 1

    if result.ok:
        print("Phase 1B smoke report validation OK")
        for warning in result.warnings:
            print(f"Warning: {warning}")
        return 0

    print("Phase 1B smoke report validation failed:")
    for error in result.errors:
        print(f"- {error}")
    for warning in result.warnings:
        print(f"Warning: {warning}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
