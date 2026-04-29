from scripts.verify_phase1b_env import collect_missing_phase1b_env, merge_env_file


def _valid_env() -> dict[str, str]:
    return {
        "SUPABASE_URL": "https://project.supabase.co",
        "SUPABASE_SERVICE_KEY": "service-role",
        "SUPABASE_JWT_SECRET": "jwt-secret",
        "BILLING_INTERNAL_SECRET": "billing-secret",
        "GOOGLE_CLIENT_ID": "google-client",
        "GOOGLE_CLIENT_SECRET": "google-secret",
        "GOOGLE_REDIRECT_URI": "https://api.example.com/auth/google/callback",
        "ENCRYPTION_KEY": "fernet-key",
        "DASHBOARD_URL": "https://web.example.com",
    }


def test_phase1b_env_accepts_billing_secret_as_oauth_state_fallback():
    missing, warnings = collect_missing_phase1b_env(_valid_env())

    assert missing == []
    assert any("GOOGLE_OAUTH_STATE_SECRET" in warning for warning in warnings)


def test_phase1b_env_requires_fastapi_readiness_values():
    env = _valid_env()
    del env["SUPABASE_SERVICE_KEY"]
    del env["DASHBOARD_URL"]

    missing, _ = collect_missing_phase1b_env(env)

    assert missing == ["SUPABASE_SERVICE_KEY", "DASHBOARD_URL"]


def test_phase1b_env_requires_oauth_state_secret_when_billing_secret_missing():
    env = _valid_env()
    del env["BILLING_INTERNAL_SECRET"]

    missing, _ = collect_missing_phase1b_env(env)

    assert "BILLING_INTERNAL_SECRET" in missing
    assert "GOOGLE_OAUTH_STATE_SECRET or BILLING_INTERNAL_SECRET" in missing


def test_phase1b_env_can_merge_values_from_env_file(tmp_path):
    env_file = tmp_path / "phase1b.env"
    env_file.write_text(
        "\n".join(
            [
                "SUPABASE_URL=https://project.supabase.co",
                "SUPABASE_SERVICE_KEY=service-role",
                "SUPABASE_JWT_SECRET=jwt-secret",
                "BILLING_INTERNAL_SECRET=billing-secret",
                "GOOGLE_CLIENT_ID=google-client",
                "GOOGLE_CLIENT_SECRET=google-secret",
                "GOOGLE_REDIRECT_URI=https://api.example.com/auth/google/callback",
                "ENCRYPTION_KEY=fernet-key",
                "DASHBOARD_URL=https://web.example.com",
                "GOOGLE_OAUTH_STATE_SECRET=oauth-state",
            ]
        ),
        encoding="utf-8",
    )

    env = merge_env_file({}, env_file)
    missing, warnings = collect_missing_phase1b_env(env)

    assert missing == []
    assert warnings == []
