"""Authenticated web onboarding routes."""

from __future__ import annotations

import base64
import hashlib
import hmac
import inspect
import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from api.auth import AuthUser, get_current_auth_user
from bot.config import Config
from shared.database import get_supabase_client
from shared.google_calendar import create_calendar
from shared.google_auth import build_oauth_url
from shared.google_drive import create_root_folder
from shared.google_sheets import create_spreadsheet

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


def _oauth_state_secret() -> str:
    secret = Config.GOOGLE_OAUTH_STATE_SECRET or Config.BILLING_INTERNAL_SECRET
    if not secret:
        raise HTTPException(
            status_code=500,
            detail="OAuth state secret is not configured.",
        )
    return secret


def encode_oauth_state(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "iat": int(datetime.now(tz=timezone.utc).timestamp()),
    }
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    body = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    sig = hmac.new(
        _oauth_state_secret().encode("utf-8"),
        body.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()
    return f"{body}.{sig}"


def decode_oauth_state(state: str, max_age_seconds: int = 900) -> str:
    try:
        body, sig = state.split(".", 1)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid OAuth state.") from exc

    expected = hmac.new(
        _oauth_state_secret().encode("utf-8"),
        body.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, sig):
        raise HTTPException(status_code=400, detail="Invalid OAuth state signature.")

    padded = body + "=" * (-len(body) % 4)
    payload = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")))
    iat = int(payload.get("iat", 0))
    now = int(datetime.now(tz=timezone.utc).timestamp())
    if now - iat > max_age_seconds:
        raise HTTPException(status_code=400, detail="OAuth state expired.")

    user_id = payload.get("user_id")
    if not isinstance(user_id, str) or not user_id:
        raise HTTPException(status_code=400, detail="OAuth state missing user.")
    return user_id


def _resource_name(payload: dict[str, Any], key: str, fallback: str) -> str:
    value = str(payload.get(key) or "").strip()
    return value[:120] if value else fallback


async def _maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value


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
async def start_google_oauth(auth_user: AuthUser = Depends(get_current_auth_user)):
    user = _get_user_for_auth(auth_user)
    if not _has_payment(user):
        raise HTTPException(
            status_code=402,
            detail="Payment is required before Google OAuth.",
        )
    state = encode_oauth_state(user["id"])
    return {"url": build_oauth_url(user["id"], state=state)}


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
    update_data: dict[str, Any] = {}
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
        update_data["google_sheets_id"] = sheets_id
        update_data["google_sheets_name"] = sheets_name

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
        update_data["google_calendar_id"] = calendar_id
        update_data["google_calendar_name"] = calendar_name

    if not drive_folder_id:
        drive_folder_id = await _maybe_await(create_root_folder(user["id"]))
        if not drive_folder_id:
            raise HTTPException(
                status_code=502,
                detail="Could not create Google Drive resource.",
            )
        update_data["google_drive_folder_id"] = drive_folder_id

    if update_data:
        update_data["updated_at"] = _now_iso()
        get_supabase_client().table("users").update(update_data).eq(
            "id", user["id"]
        ).execute()
        user.update(update_data)

    return {
        "resources": {
            "sheetsId": sheets_id,
            "calendarId": calendar_id,
            "driveFolderId": drive_folder_id,
        },
        "nextStep": _next_step(user),
    }
