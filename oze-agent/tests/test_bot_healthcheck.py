from datetime import datetime, timezone


def test_health_state_payload_includes_last_update_age():
    from bot.healthcheck import HealthState

    state = HealthState(started_at=datetime(2026, 5, 8, 10, 0, tzinfo=timezone.utc))
    state.mark_update(datetime(2026, 5, 8, 10, 1, 30, tzinfo=timezone.utc))

    payload = state.payload(now=datetime(2026, 5, 8, 10, 2, tzinfo=timezone.utc))

    assert payload["status"] == "ok"
    assert payload["started_at"] == "2026-05-08T10:00:00+00:00"
    assert payload["last_update_at"] == "2026-05-08T10:01:30+00:00"
    assert payload["uptime_seconds"] == 120
    assert payload["seconds_since_last_update"] == 30


def test_create_healthcheck_server_serves_healthz_json():
    import json
    from urllib.request import urlopen

    from bot.healthcheck import HealthState, create_healthcheck_server

    state = HealthState(started_at=datetime(2026, 5, 8, 10, 0, tzinfo=timezone.utc))
    server = create_healthcheck_server("127.0.0.1", 0, state)
    host, port = server.server_address
    try:
        server.start()
        with urlopen(f"http://{host}:{port}/healthz", timeout=2) as response:
            assert response.status == 200
            assert response.headers["Content-Type"] == "application/json"
            body = json.loads(response.read().decode("utf-8"))
    finally:
        server.stop()

    assert body["status"] == "ok"
    assert "started_at" in body
