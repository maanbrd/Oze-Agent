"""Authenticated account routes for the web app."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from api.auth import AuthUser, get_current_auth_user
from shared.database import get_supabase_client

router = APIRouter()

ACCOUNT_PROFILE_SELECT = (
    "id, auth_user_id, email, name, phone, subscription_status, "
    "subscription_plan, subscription_current_period_end, activation_paid, "
    "onboarding_completed, google_sheets_id, google_calendar_id, "
    "google_drive_folder_id, telegram_id"
)


def _get_account_profile(auth_user: AuthUser) -> dict[str, Any]:
    result = (
        get_supabase_client()
        .table("users")
        .select(ACCOUNT_PROFILE_SELECT)
        .eq("auth_user_id", auth_user.user_id)
        .limit(1)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return result.data[0]


@router.get("/me")
async def get_current_account(auth_user: AuthUser = Depends(get_current_auth_user)):
    profile = _get_account_profile(auth_user)
    return {
        "auth_user_id": auth_user.user_id,
        "email": profile.get("email") or auth_user.email,
        "profile": profile,
    }
