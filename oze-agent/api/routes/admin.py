"""Owner admin API routes."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from api.auth import AuthUser, get_current_auth_user
from bot.config import Config
from shared.admin_dashboard import (
    build_owner_dashboard_payload,
    is_owner_admin_email,
)
from shared.admin_mirror.google_io import (
    build_admin_sheets_service,
    read_tab_values_sync,
)
from shared.database import get_supabase_client

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/admin/dashboard")
async def get_owner_admin_dashboard(
    auth_user: AuthUser = Depends(get_current_auth_user),
) -> dict[str, Any]:
    _require_owner_admin(auth_user)

    users = _list_table_rows("users")
    interactions = _list_table_rows("interaction_log")
    payment_history = _list_table_rows("payment_history")
    offers = _list_table_rows("offer_templates")
    offer_attempts = _list_table_rows("offer_send_attempts")
    metric_snapshots = _list_table_rows("admin_metric_snapshots")
    mirror_runs = _list_table_rows("admin_mirror_runs")
    contact_rows = _read_owner_mirror_rows("Kontakty")
    calendar_rows = _read_owner_mirror_rows("Kalendarz")

    return build_owner_dashboard_payload(
        users=users,
        interactions=interactions,
        payment_history=payment_history,
        offers=offers,
        offer_attempts=offer_attempts,
        contact_rows=contact_rows,
        calendar_rows=calendar_rows,
        metric_snapshots=metric_snapshots,
        mirror_runs=mirror_runs,
        monthly_subscription_pln=Config.MONTHLY_SUBSCRIPTION_PLN,
        admin_usd_pln_rate=Config.ADMIN_USD_PLN_RATE,
        owner_spreadsheet_id=Config.ADMIN_MIRROR_SPREADSHEET_ID,
        owner_calendar_id=Config.ADMIN_MIRROR_CALENDAR_ID,
    )


@router.get("/admin/user-profiles")
async def get_owner_user_profiles(
    auth_user: AuthUser = Depends(get_current_auth_user),
) -> dict[str, Any]:
    _require_owner_admin(auth_user)
    return {"profiles": _build_user_profile_rows()}


@router.get("/admin/user-profiles/{user_id}")
async def get_owner_user_profile(
    user_id: str,
    auth_user: AuthUser = Depends(get_current_auth_user),
) -> dict[str, Any]:
    _require_owner_admin(auth_user)
    for row in _build_user_profile_rows():
        if row["user_id"] == user_id:
            return {"profile": row}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User profile not found.",
    )


def _require_owner_admin(auth_user: AuthUser) -> None:
    profile = _get_user_profile(auth_user)
    owner_email = (profile or {}).get("email") or auth_user.email
    if not is_owner_admin_email(owner_email, Config.OWNER_ADMIN_EMAILS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner admin access required.",
        )


def _get_user_profile(auth_user: AuthUser) -> dict[str, Any] | None:
    try:
        result = (
            get_supabase_client()
            .table("users")
            .select("id, auth_user_id, email, name")
            .eq("auth_user_id", auth_user.user_id)
            .maybe_single()
            .execute()
        )
        return result.data if result.data else None
    except Exception as exc:
        logger.warning("admin.profile_lookup_failed(%s): %s", auth_user.user_id, exc)
        return None


def _build_user_profile_rows() -> list[dict[str, Any]]:
    users = _list_table_rows(
        "users",
        "id, name, email, telegram_id, subscription_status, is_suspended, is_deleted",
    )
    profiles = _list_table_rows("user_behavior_profiles")
    users_by_id = {str(user.get("id")): user for user in users if user.get("id")}
    rows: list[dict[str, Any]] = []
    for profile in profiles:
        user_id = str(profile.get("user_id") or "")
        user = users_by_id.get(user_id, {})
        rows.append({
            "user_id": user_id,
            "telegram_id": profile.get("telegram_id") or user.get("telegram_id"),
            "name": user.get("name") or "",
            "email": user.get("email") or "",
            "subscription_status": user.get("subscription_status") or "",
            "is_suspended": bool(user.get("is_suspended")),
            "is_deleted": bool(user.get("is_deleted")),
            "profile_markdown": profile.get("profile_markdown") or "",
            "insights_json": profile.get("insights_json") or {},
            "last_analyzed_message_at": profile.get("last_analyzed_message_at"),
            "last_run_at": profile.get("last_run_at"),
            "status": profile.get("status") or "unknown",
            "error": profile.get("error"),
            "model": profile.get("model"),
            "tokens_in": profile.get("tokens_in") or 0,
            "tokens_out": profile.get("tokens_out") or 0,
            "cost_usd": profile.get("cost_usd") or 0,
            "analyzed_messages_count": profile.get("analyzed_messages_count") or 0,
        })
    return sorted(rows, key=lambda row: row.get("last_run_at") or "", reverse=True)


def _list_table_rows(table_name: str, fields: str = "*", page_size: int = 1000) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    offset = 0
    while True:
        try:
            result = (
                get_supabase_client()
                .table(table_name)
                .select(fields)
                .range(offset, offset + page_size - 1)
                .execute()
            )
        except Exception as exc:
            logger.warning("admin.table_read_failed(%s): %s", table_name, exc)
            return rows
        page = result.data or []
        rows.extend(page)
        if len(page) < page_size:
            return rows
        offset += page_size


def _read_owner_mirror_rows(tab_name: str) -> list[dict[str, Any]]:
    if not Config.ADMIN_MIRROR_GOOGLE_USER_ID or not Config.ADMIN_MIRROR_SPREADSHEET_ID:
        return []
    try:
        service = build_admin_sheets_service(Config.ADMIN_MIRROR_GOOGLE_USER_ID)
        if not service:
            return []
        values = read_tab_values_sync(
            service,
            Config.ADMIN_MIRROR_SPREADSHEET_ID,
            tab_name,
        )
    except Exception as exc:
        logger.warning("admin.owner_mirror_read_failed(%s): %s", tab_name, exc)
        return []
    return _sheet_values_to_dicts(values)


def _sheet_values_to_dicts(values: list[list[Any]]) -> list[dict[str, Any]]:
    if len(values) < 2:
        return []
    headers = [str(value) for value in values[0]]
    rows: list[dict[str, Any]] = []
    for raw_row in values[1:]:
        row = {}
        for index, header in enumerate(headers):
            row[header] = raw_row[index] if index < len(raw_row) else ""
        rows.append(row)
    return rows
