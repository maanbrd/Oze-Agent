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
    profile = _get_user_profile(auth_user)
    owner_email = (profile or {}).get("email") or auth_user.email
    if not is_owner_admin_email(owner_email, Config.OWNER_ADMIN_EMAILS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner admin access required.",
        )

    users = _list_table_rows("users")
    interactions = _list_table_rows("interaction_log")
    payment_history = _list_table_rows("payment_history")
    offers = _list_table_rows("offer_templates")
    offer_attempts = _list_table_rows("offer_send_attempts")
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
        monthly_subscription_pln=Config.MONTHLY_SUBSCRIPTION_PLN,
        owner_spreadsheet_id=Config.ADMIN_MIRROR_SPREADSHEET_ID,
        owner_calendar_id=Config.ADMIN_MIRROR_CALENDAR_ID,
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
