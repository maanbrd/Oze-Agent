from scripts.smoke_phase1b_api import is_auth_failure, validate_health_payload


def test_phase1b_api_smoke_accepts_health_payload():
    validate_health_payload({"status": "ok", "version": "0.1.0"})


def test_phase1b_api_smoke_rejects_bad_health_payload():
    try:
        validate_health_payload({"status": "down"})
    except AssertionError as exc:
        assert "status ok" in str(exc)
    else:
        raise AssertionError("Expected invalid health payload to fail.")


def test_phase1b_api_smoke_accepts_standard_auth_failures():
    assert is_auth_failure(401)
    assert is_auth_failure(403)
    assert not is_auth_failure(500)
