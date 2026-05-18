"""Supabase data readers for the owner-facing admin mirror."""

from __future__ import annotations

from shared.database import get_supabase_client


MIRROR_USER_FIELDS = ",".join([
    "id",
    "name",
    "email",
    "phone",
    "telegram_id",
    "subscription_status",
    "subscription_plan",
    "subscription_expires_at",
    "subscription_current_period_end",
    "activation_paid",
    "stripe_customer_id",
    "stripe_subscription_id",
    "stripe_checkout_session_id",
    "google_sheets_id",
    "google_calendar_id",
    "google_drive_folder_id",
    "onboarding_completed",
    "created_at",
    "updated_at",
    "is_suspended",
    "is_deleted",
])


def is_mirror_user(user: dict) -> bool:
    if user.get("is_deleted") or user.get("is_suspended"):
        return False
    return user.get("subscription_status") in {"active", "canceled"}


def is_refreshable_user(user: dict) -> bool:
    return is_mirror_user(user) and user.get("subscription_status") == "active"


def list_mirror_users(client=None) -> list[dict]:
    client = client or get_supabase_client()
    rows = _select_all(client, "users", MIRROR_USER_FIELDS)
    return [user for user in rows if is_mirror_user(user)]


def list_table_rows(table_name: str, client=None) -> list[dict]:
    client = client or get_supabase_client()
    return _select_all(client, table_name, "*")


def _select_all(client, table_name: str, fields: str, page_size: int = 1000) -> list[dict]:
    rows: list[dict] = []
    offset = 0
    while True:
        result = (
            client.table(table_name)
            .select(fields)
            .range(offset, offset + page_size - 1)
            .execute()
        )
        page = result.data or []
        rows.extend(page)
        if len(page) < page_size:
            return rows
        offset += page_size
