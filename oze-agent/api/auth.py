"""Supabase Auth JWT validation for FastAPI routes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Any

import jwt
from fastapi import Depends, Header, HTTPException, status
from jwt import PyJWKClient

from bot.config import Config
from shared.database import get_supabase_client


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


async def require_active_access(
    auth_user: AuthUser = Depends(get_current_auth_user),
) -> AuthUser:
    """Authorize paid/trial or explicitly claimed beta product access."""
    result = (
        get_supabase_client()
        .table("users")
        .select("id, subscription_status")
        .eq("auth_user_id", auth_user.user_id)
        .limit(1)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
    user = result.data[0]
    if user.get("subscription_status") in {"active", "trialing"}:
        return auth_user

    grant = (
        get_supabase_client()
        .table("beta_access_grants")
        .select("id, auth_user_id, status")
        .eq("auth_user_id", auth_user.user_id)
        .eq("status", "active")
        .limit(1)
        .execute()
    )
    if grant.data and grant.data[0].get("auth_user_id") == auth_user.user_id:
        return auth_user
    raise HTTPException(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        detail="Active subscription required.",
    )
