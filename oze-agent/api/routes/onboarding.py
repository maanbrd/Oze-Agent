"""Authenticated web onboarding routes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from api.auth import AuthUser, get_current_auth_user
from shared.database import get_supabase_client

router = APIRouter()

USER_SELECT = (
    "id, auth_user_id, email, name, phone, subscription_status, "
    "subscription_plan, subscription_current_period_end, activation_paid, "
    "google_access_token, google_refresh_token, google_token_expiry, "
    "google_sheets_id, google_sheets_name, google_calendar_id, "
    "google_calendar_name, google_drive_folder_id, telegram_id, "
    "telegram_link_code, telegram_link_code_expires, onboarding_completed"
)


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _get_user_for_auth(auth_user: AuthUser) -> dict[str, Any]:
    result = (
        get_supabase_client()
        .table("users")
        .select(USER_SELECT)
        .eq("auth_user_id", auth_user.user_id)
        .limit(1)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return result.data[0]


def _has_google_tokens(user: dict[str, Any]) -> bool:
    return bool(user.get("google_refresh_token"))


def _has_resources(user: dict[str, Any]) -> bool:
    return bool(
        user.get("google_sheets_id")
        and user.get("google_calendar_id")
        and user.get("google_drive_folder_id")
    )


def _has_payment(user: dict[str, Any]) -> bool:
    return user.get("subscription_status") == "active" and bool(
        user.get("activation_paid")
    )


def _has_telegram(user: dict[str, Any]) -> bool:
    return bool(user.get("telegram_id"))


def _next_step(user: dict[str, Any]) -> str:
    if not _has_payment(user):
        return "/onboarding/platnosc"
    if not _has_google_tokens(user):
        return "/onboarding/google"
    if not _has_resources(user):
        return "/onboarding/zasoby"
    if not _has_telegram(user):
        return "/onboarding/telegram"
    return "/dashboard"


def _status_payload(user: dict[str, Any]) -> dict[str, Any]:
    steps = {
        "payment": _has_payment(user),
        "google": _has_google_tokens(user),
        "resources": _has_resources(user),
        "telegram": _has_telegram(user),
    }
    completed = all(steps.values())
    return {
        "fetchedAt": _now_iso(),
        "nextStep": "/dashboard" if completed else _next_step(user),
        "completed": completed,
        "steps": steps,
        "profile": {
            "id": user.get("id"),
            "auth_user_id": user.get("auth_user_id"),
            "email": user.get("email"),
            "name": user.get("name"),
            "phone": user.get("phone"),
            "subscription_status": user.get("subscription_status"),
            "subscription_plan": user.get("subscription_plan"),
            "subscription_current_period_end": user.get(
                "subscription_current_period_end"
            ),
            "activation_paid": user.get("activation_paid"),
            "google_sheets_id": user.get("google_sheets_id"),
            "google_sheets_name": user.get("google_sheets_name"),
            "google_calendar_id": user.get("google_calendar_id"),
            "google_calendar_name": user.get("google_calendar_name"),
            "google_drive_folder_id": user.get("google_drive_folder_id"),
            "telegram_id": user.get("telegram_id"),
            "onboarding_completed": user.get("onboarding_completed"),
        },
    }


@router.get("/status")
async def get_onboarding_status(auth_user: AuthUser = Depends(get_current_auth_user)):
    user = _get_user_for_auth(auth_user)
    payload = _status_payload(user)
    if payload["completed"] and not user.get("onboarding_completed"):
        get_supabase_client().table("users").update(
            {"onboarding_completed": True, "updated_at": _now_iso()}
        ).eq("id", user["id"]).execute()
        user["onboarding_completed"] = True
        payload = _status_payload(user)
    return payload


@router.patch("/account")
async def update_account(
    payload: dict[str, Any],
    auth_user: AuthUser = Depends(get_current_auth_user),
):
    user = _get_user_for_auth(auth_user)
    update_data: dict[str, Any] = {}
    if "name" in payload:
        update_data["name"] = str(payload.get("name") or "").strip()[:120] or None
    if "phone" in payload:
        update_data["phone"] = str(payload.get("phone") or "").strip()[:40] or None

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No supported account fields provided.",
        )

    update_data["updated_at"] = _now_iso()
    result = (
        get_supabase_client()
        .table("users")
        .update(update_data)
        .eq("id", user["id"])
        .execute()
    )
    updated = result.data[0] if result.data else {**user, **update_data}
    return {"profile": updated}
