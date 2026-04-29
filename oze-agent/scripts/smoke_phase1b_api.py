"""Run local Phase 1B FastAPI route smoke checks.

Run from `oze-agent/` while the API server is running:
    PYTHONPATH=. python3 scripts/smoke_phase1b_api.py --base-url=http://127.0.0.1:8000
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_TIMEOUT_SECONDS = 8


@dataclass(frozen=True)
class SmokeResponse:
    status: int
    body: str


@dataclass(frozen=True)
class SmokeResult:
    name: str
    ok: bool
    error: str | None = None


def validate_health_payload(payload: dict[str, Any]) -> None:
    assert payload.get("status") == "ok", "/health did not return status ok."
    assert payload.get("version"), "/health did not return an API version."


def is_auth_failure(status: int) -> bool:
    return status in {401, 403}


def _request(base_url: str, path: str, timeout: int) -> SmokeResponse:
    url = f"{base_url.rstrip('/')}{path}"
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return SmokeResponse(status=response.status, body=body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        return SmokeResponse(status=exc.code, body=body)


def _check(name: str, fn) -> SmokeResult:
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 - smoke output should report all failures.
        return SmokeResult(name=name, ok=False, error=str(exc))
    return SmokeResult(name=name, ok=True)


def run_smoke(base_url: str, timeout: int) -> list[SmokeResult]:
    results: list[SmokeResult] = []

    def health() -> None:
        response = _request(base_url, "/health", timeout)
        assert response.status == 200, f"/health returned {response.status}."
        validate_health_payload(json.loads(response.body))

    def onboarding_auth() -> None:
        response = _request(base_url, "/api/onboarding/status", timeout)
        assert is_auth_failure(response.status), (
            "/api/onboarding/status without auth returned "
            f"{response.status}, expected 401 or 403."
        )

    def dashboard_auth() -> None:
        response = _request(base_url, "/api/dashboard/crm", timeout)
        assert is_auth_failure(response.status), (
            "/api/dashboard/crm without auth returned "
            f"{response.status}, expected 401 or 403."
        )

    results.append(_check("health route returns JSON", health))
    results.append(_check("onboarding route requires auth", onboarding_auth))
    results.append(_check("dashboard route requires auth", dashboard_auth))
    return results


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    results = run_smoke(args.base_url, args.timeout)

    print(f"Phase 1B FastAPI smoke target: {args.base_url.rstrip('/')}")
    for result in results:
        if result.ok:
            print(f"OK {result.name}")
        else:
            print(f"FAIL {result.name}: {result.error}")

    return 1 if any(not result.ok for result in results) else 0


if __name__ == "__main__":
    sys.exit(main())
