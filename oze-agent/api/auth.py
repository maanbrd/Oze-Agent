"""Supabase Auth JWT validation for FastAPI routes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Any

import jwt
from fastapi import Header, HTTPException, status
from jwt import PyJWKClient

from bot.config import Config


@dataclass(frozen=True)
class AuthUser:
    user_id: str
    email: str | None
    claims: dict[str, Any]


def _issuer() -> str:
    return Config.SUPABASE_URL.rstrip("/") + "/auth/v1"


def _decode_supabase_jwt(token: str) -> dict[str, Any]:
    issuer = _issuer()
    header = jwt.get_unverified_header(token)
    algorithm = header.get("alg")
    if not algorithm:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has no signing algorithm.",
        )

    if algorithm.startswith("HS"):
        if not Config.SUPABASE_JWT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Supabase JWT secret fallback is not configured.",
            )
        return jwt.decode(
            token,
            Config.SUPABASE_JWT_SECRET,
            algorithms=[algorithm],
            audience="authenticated",
            issuer=issuer,
        )

    jwks_client = PyJWKClient(f"{issuer}/.well-known/jwks.json")
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=[algorithm],
        audience="authenticated",
        issuer=issuer,
    )


async def get_current_auth_user(
    authorization: Annotated[str | None, Header()] = None,
) -> AuthUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
        )

    token = authorization.removeprefix("Bearer ").strip()
    try:
        claims = _decode_supabase_jwt(token)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token.",
        ) from exc

    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has no subject.",
        )

    return AuthUser(
        user_id=user_id,
        email=claims.get("email"),
        claims=claims,
    )
