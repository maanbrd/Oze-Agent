from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import HTTPException


def _token(secret: str, issuer: str, subject: str = "auth-user-1") -> str:
    now = datetime.now(tz=timezone.utc)
    return jwt.encode(
        {
            "iss": issuer,
            "sub": subject,
            "aud": "authenticated",
            "email": "jan@example.com",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=10)).timestamp()),
        },
        secret,
        algorithm="HS256",
    )


def test_decode_supabase_jwt_hs256_fallback(monkeypatch):
    from api import auth
    from bot.config import Config

    monkeypatch.setattr(Config, "SUPABASE_URL", "https://project-ref.supabase.co")
    monkeypatch.setattr(Config, "SUPABASE_JWT_SECRET", "legacy-secret-with-enough-length-32")

    decoded = auth._decode_supabase_jwt(
        _token(
            "legacy-secret-with-enough-length-32",
            "https://project-ref.supabase.co/auth/v1",
        )
    )

    assert decoded["sub"] == "auth-user-1"
    assert decoded["email"] == "jan@example.com"


@pytest.mark.asyncio
async def test_get_current_auth_user_requires_bearer_token():
    from api.auth import get_current_auth_user

    with pytest.raises(HTTPException) as exc:
        await get_current_auth_user(None)

    assert exc.value.status_code == 401
