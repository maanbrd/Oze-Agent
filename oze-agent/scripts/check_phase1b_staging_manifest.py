"""Validate the public Phase 1B staging smoke manifest.

Run from `oze-agent/`:
    PYTHONPATH=. .venv/bin/python scripts/check_phase1b_staging_manifest.py \
      --manifest ../docs/phase1b-staging-manifest.example.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

EXPECTED_RAILWAY_API_START_COMMAND = "uvicorn api.main:app --host 0.0.0.0 --port $PORT"
EXPECTED_LOOKUP_KEYS = {
    "activation": "agent_oze_activation_199",
    "monthly": "agent_oze_monthly_49",
    "yearly": "agent_oze_yearly_350",
}
FORBIDDEN_SECRET_KEY_NAMES = {
    "STRIPE_SECRET_KEY",
    "STRIPE_WEBHOOK_SECRET",
    "SUPABASE_SERVICE_KEY",
    "BILLING_INTERNAL_SECRET",
}
FORBIDDEN_VALUE_PREFIXES = ("sk_", "whsec_", "rk_", "eyJ")
WARSAW = ZoneInfo("Europe/Warsaw")


@dataclass(frozen=True)
class SmokeIdentity:
    email: str
    google_resource_prefix: str


def _field(manifest: dict[str, Any], name: str) -> str:
    value = manifest.get(name)
    return value if isinstance(value, str) else ""


def _parsed_https_url(manifest: dict[str, Any], name: str, errors: list[str]):
    value = _field(manifest, name)
    parsed = urlparse(value)
    if not value:
        errors.append(f"{name} is required.")
        return parsed
    if parsed.scheme != "https" or not parsed.netloc:
        errors.append(f"{name} must be an https URL.")
    return parsed


def _origin(parsed) -> str:
    return f"{parsed.scheme}://{parsed.netloc.lower()}"


def _normalized_webhook_url(web_url: str) -> str:
    return f"{web_url.rstrip('/')}/api/webhooks/stripe"


def _validate_lookup_keys(manifest: dict[str, Any], errors: list[str]) -> None:
    lookup_keys = manifest.get("stripe_lookup_keys")
    if not isinstance(lookup_keys, dict):
        errors.append("stripe_lookup_keys must be an object.")
        return

    for name, expected in EXPECTED_LOOKUP_KEYS.items():
        actual = lookup_keys.get(name)
        if actual != expected:
            errors.append(f"stripe_lookup_keys.{name} must be `{expected}`.")


def _validate_smoke_domain(domain: str, errors: list[str]) -> None:
    if not domain:
        errors.append("smoke_email_domain is required.")
        return
    if "@" in domain or "://" in domain or any(char.isspace() for char in domain):
        errors.append("smoke_email_domain must be a domain, not an email, URL, or spaced value.")
        return
    if "." not in domain or domain.startswith(".") or domain.endswith("."):
        errors.append("smoke_email_domain must be a real domain containing a dot.")
        return
    if not re.fullmatch(r"[A-Za-z0-9.-]+", domain):
        errors.append("smoke_email_domain contains invalid domain characters.")


def _walk_manifest(value: Any, path: str = ""):
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            yield child_path, key, child
            yield from _walk_manifest(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]"
            yield child_path, str(index), child
            yield from _walk_manifest(child, child_path)


def _validate_no_secrets(manifest: dict[str, Any], errors: list[str]) -> None:
    for path, key, value in _walk_manifest(manifest):
        if key in FORBIDDEN_SECRET_KEY_NAMES or key.lower().endswith("secret"):
            errors.append(f"{path} must not be present in the public staging manifest.")

        if not isinstance(value, str):
            continue

        stripped = value.strip()
        if stripped.startswith(FORBIDDEN_VALUE_PREFIXES):
            errors.append(f"{path} looks like a secret value and must not be in the manifest.")
        if "service_role" in stripped.lower():
            errors.append(f"{path} contains service_role and must not be in the manifest.")


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    web = _parsed_https_url(manifest, "web_url", errors)
    api = _parsed_https_url(manifest, "api_url", errors)
    _parsed_https_url(manifest, "supabase_url", errors)
    _parsed_https_url(manifest, "stripe_webhook_url", errors)

    if web.scheme and api.scheme and web.netloc and api.netloc and _origin(web) == _origin(api):
        errors.append("web_url and api_url must use different origins.")

    expected_webhook = _normalized_webhook_url(_field(manifest, "web_url"))
    if _field(manifest, "stripe_webhook_url") != expected_webhook:
        errors.append("stripe_webhook_url must equal ${web_url}/api/webhooks/stripe.")

    if _field(manifest, "stripe_mode") != "test":
        errors.append("stripe_mode must be `test`.")

    if _field(manifest, "railway_api_start_command") != EXPECTED_RAILWAY_API_START_COMMAND:
        errors.append(
            f"railway_api_start_command must be `{EXPECTED_RAILWAY_API_START_COMMAND}`."
        )

    _validate_lookup_keys(manifest, errors)
    _validate_smoke_domain(_field(manifest, "smoke_email_domain"), errors)
    _validate_no_secrets(manifest, errors)

    return errors


def generate_smoke_identity(domain: str, now: datetime) -> SmokeIdentity:
    if now.tzinfo is None:
        now = now.replace(tzinfo=WARSAW)
    now = now.astimezone(WARSAW)
    return SmokeIdentity(
        email=f"phase1b+{now:%Y%m%d-%H%M}@{domain}",
        google_resource_prefix=f"P1B Smoke {now:%Y-%m-%d %H%M}",
    )


def _load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_now(value: str | None) -> datetime:
    if not value:
        return datetime.now(WARSAW)
    return datetime.strptime(value, "%Y-%m-%dT%H:%M").replace(tzinfo=WARSAW)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--generate-smoke-id", action="store_true")
    parser.add_argument("--now", help="Deterministic Europe/Warsaw time: YYYY-MM-DDTHH:MM")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    manifest = _load_manifest(args.manifest)
    errors = validate_manifest(manifest)

    if errors:
        print("Phase 1B staging manifest preflight failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Phase 1B staging manifest preflight OK")
    if args.generate_smoke_id:
        identity = generate_smoke_identity(
            _field(manifest, "smoke_email_domain"),
            _parse_now(args.now),
        )
        print(f"Smoke email: {identity.email}")
        print(f"Google resource prefix: {identity.google_resource_prefix}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
