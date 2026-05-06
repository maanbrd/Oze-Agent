"""Authenticated web onboarding routes."""

from __future__ import annotations

import inspect
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status

from api.auth import AuthUser, get_current_auth_user
from shared.database import get_supabase_client
from shared.google_auth import build_oauth_url
from shared.google_calendar import create_calendar
from shared.google_drive import create_root_folder
from shared.google_sheets import create_spreadsheet

router = APIRouter()

TELEGRAM_LINK_CODE_TTL_SECONDS = 90

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


def _resource_name(payload: dict[str, Any], key: str, fallback: str) -> str:
    value = str(payload.get(key) or "").strip()
    return value[:120] if value else fallback


async def _maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value


def _persist_user_update(user: dict[str, Any], update_data: dict[str, Any]) -> None:
    if not update_data:
        return
    payload = {**update_data, "updated_at": _now_iso()}
    get_supabase_client().table("users").update(payload).eq(
        "id", user["id"]
    ).execute()
    user.update(payload)


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


@router.post("/google/oauth-url")
async def start_google_oauth(
    payload: dict[str, Any] | None = Body(default=None),
    auth_user: AuthUser = Depends(get_current_auth_user),
):
    user = _get_user_for_auth(auth_user)
    if not _has_payment(user):
        raise HTTPException(
            status_code=402,
            detail="Payment is required before Google OAuth.",
        )
    return_url = str((payload or {}).get("returnUrl") or "").strip() or None
    return {"url": build_oauth_url(user["id"], return_url=return_url)}


@router.post("/resources")
async def create_google_resources(
    payload: dict[str, Any],
    auth_user: AuthUser = Depends(get_current_auth_user),
):
    user = _get_user_for_auth(auth_user)
    if not _has_payment(user):
        raise HTTPException(
            status_code=402,
            detail="Payment is required before resource creation.",
        )
    if not _has_google_tokens(user):
        raise HTTPException(
            status_code=409,
            detail="Google OAuth is required before resource creation.",
        )

    label = user.get("name") or user.get("email") or user["id"]
    sheets_id = user.get("google_sheets_id")
    calendar_id = user.get("google_calendar_id")
    drive_folder_id = user.get("google_drive_folder_id")

    if not sheets_id:
        sheets_name = _resource_name(payload, "sheetsName", f"Agent-OZE CRM - {label}")
        sheets_id = await _maybe_await(create_spreadsheet(user["id"], sheets_name))
        if not sheets_id:
            raise HTTPException(
                status_code=502,
                detail="Could not create Google Sheets resource.",
            )
        _persist_user_update(
            user,
            {"google_sheets_id": sheets_id, "google_sheets_name": sheets_name},
        )

    if not calendar_id:
        calendar_name = _resource_name(
            payload,
            "calendarName",
            f"Agent-OZE - {label}",
        )
        calendar_id = await _maybe_await(create_calendar(user["id"], calendar_name))
        if not calendar_id:
            raise HTTPException(
                status_code=502,
                detail="Could not create Google Calendar resource.",
            )
        _persist_user_update(
            user,
            {
                "google_calendar_id": calendar_id,
                "google_calendar_name": calendar_name,
            },
        )

    if not drive_folder_id:
        drive_folder_id = await _maybe_await(create_root_folder(user["id"]))
        if not drive_folder_id:
            raise HTTPException(
                status_code=502,
                detail="Could not create Google Drive resource.",
            )
        _persist_user_update(user, {"google_drive_folder_id": drive_folder_id})

    return {
        "resources": {
            "sheetsId": sheets_id,
            "calendarId": calendar_id,
            "driveFolderId": drive_folder_id,
        },
        "nextStep": _next_step(user),
    }


def _telegram_code() -> str:
    return f"{100000 + secrets.randbelow(900000):06d}"


@router.post("/telegram-code")
async def generate_telegram_code(auth_user: AuthUser = Depends(get_current_auth_user)):
    user = _get_user_for_auth(auth_user)
    if not _has_payment(user) or not _has_google_tokens(user) or not _has_resources(user):
        raise HTTPException(
            status_code=409,
            detail="Complete payment and Google setup before Telegram pairing.",
        )
    if user.get("telegram_id"):
        return {
            "paired": True,
            "telegramId": user["telegram_id"],
            "code": None,
            "expiresAt": None,
        }

    code = _telegram_code()
    expires_at = datetime.now(tz=timezone.utc) + timedelta(
        seconds=TELEGRAM_LINK_CODE_TTL_SECONDS
    )
    get_supabase_client().table("users").update(
        {
            "telegram_link_code": code,
            "telegram_link_code_expires": expires_at.isoformat(),
            "updated_at": _now_iso(),
        }
    ).eq("id", user["id"]).execute()
    return {
        "paired": False,
        "telegramId": None,
        "code": code,
        "expiresAt": expires_at.isoformat(),
    }


@router.get("/telegram-status")
async def get_telegram_status(auth_user: AuthUser = Depends(get_current_auth_user)):
    user = _get_user_for_auth(auth_user)
    return {
        "paired": bool(user.get("telegram_id")),
        "telegramId": user.get("telegram_id"),
        "code": None if user.get("telegram_id") else user.get("telegram_link_code"),
        "expiresAt": None
        if user.get("telegram_id")
        else user.get("telegram_link_code_expires"),
    }
