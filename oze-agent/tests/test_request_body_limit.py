"""Request body-size cap middleware (Item 5).

Runs before routing/auth, so an oversized body is rejected with 413 regardless
of credentials. JSON is capped at 1 MB; multipart (logo upload) at 6 MB.

Note: ``api.main`` is imported lazily inside each test (not at module level) so
collection does not freeze its ``bot.config`` binding ahead of other tests that
reload ``bot.config`` (e.g. test_config), which would diverge the ``Config``
class object across modules.
"""

import pytest


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from api.main import app

    return TestClient(app)


def test_oversized_json_body_rejected_with_413(client):
    big = "x" * (2 * 1024 * 1024)  # 2 MB > 1 MB JSON limit
    resp = client.patch(
        "/api/onboarding/account",
        content=f'{{"name": "{big}"}}',
        headers={"content-type": "application/json"},
    )
    assert resp.status_code == 413
    assert resp.json()["detail"] == "Request body too large."


def test_small_json_body_not_blocked_by_size_limit(client):
    # Passes the size gate; then fails auth (no token) — must NOT be 413.
    resp = client.patch(
        "/api/onboarding/account",
        json={"name": "Jan Kowalski"},
    )
    assert resp.status_code != 413


def test_multipart_under_6mb_not_blocked_by_size_limit(client):
    # 2 MB multipart is over the JSON limit but under the multipart limit, so
    # the size gate must let it through (it then fails downstream, not 413).
    payload = b"y" * (2 * 1024 * 1024)
    resp = client.post(
        "/offers/profile/logo",
        files={"file": ("logo.png", payload, "image/png")},
    )
    assert resp.status_code != 413
