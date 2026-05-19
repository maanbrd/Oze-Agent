"""Supabase persistence for the admin-only user behavior profile agent."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from shared.database import get_supabase_client

logger = logging.getLogger(__name__)


PROFILE_USER_FIELDS = "id, telegram_id, name, email"
PROFILE_FIELDS = (
    "user_id, telegram_id, profile_markdown, insights_json, "
    "last_analyzed_message_at, last_run_at, status, error, model, "
    "tokens_in, tokens_out, cost_usd, analyzed_messages_count"
)
CONVERSATION_FIELDS = "role, content, message_type, created_at"


def list_profile_agent_users() -> list[dict[str, Any]]:
    """Return active users eligible for the daily profile agent."""
    try:
        result = (
            get_supabase_client()
            .table("users")
            .select(PROFILE_USER_FIELDS)
            .eq("subscription_status", "active")
            .eq("is_suspended", False)
            .eq("is_deleted", False)
            .not_.is_("telegram_id", "null")
            .execute()
        )
        return result.data or []
    except Exception as exc:
        logger.error("user_profile_agent.list_users: %s", exc)
        return []


def get_current_profile_state(user_id: str) -> dict[str, Any] | None:
    """Return the current profile state for a user, if it exists."""
    try:
        result = (
            get_supabase_client()
            .table("user_behavior_profiles")
            .select(PROFILE_FIELDS)
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        return result.data or None
    except Exception as exc:
        logger.warning("user_profile_agent.profile_state(%s): %s", user_id, exc)
        return None


def list_new_conversation_messages(
    telegram_id: int,
    since: str | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    """Return conversation rows newer than `since`, oldest first."""
    query = (
        get_supabase_client()
        .table("conversation_history")
        .select(CONVERSATION_FIELDS)
        .eq("telegram_id", telegram_id)
    )
    if since:
        query = query.gt("created_at", since)
    result = (
        query
        .order("created_at", desc=False)
        .limit(limit)
        .execute()
    )
    return result.data or []


def upsert_current_profile(payload: dict[str, Any]) -> None:
    """Upsert the current profile snapshot."""
    data = dict(payload)
    data["updated_at"] = _now_iso()
    get_supabase_client().table("user_behavior_profiles").upsert(
        data,
        on_conflict="user_id",
    ).execute()


def insert_profile_run(payload: dict[str, Any]) -> None:
    """Append one profile-agent run row."""
    get_supabase_client().table("user_behavior_profile_runs").insert(payload).execute()


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()
