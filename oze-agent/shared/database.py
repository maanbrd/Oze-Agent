"""Supabase client wrapper for OZE-Agent.

All functions use the service key (bypasses RLS). Returns None on failure.
"""

import logging
from datetime import date, datetime
from typing import Optional

from supabase import Client, create_client

from bot.config import Config

logger = logging.getLogger(__name__)

_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Return a singleton Supabase client using the service key."""
    global _client
    if _client is None:
        _client = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
    return _client


# ── Users ────────────────────────────────────────────────────────────────────


def get_user_by_telegram_id(telegram_id: int) -> Optional[dict]:
    """Return user dict or None if not found."""
    try:
        result = (
            get_supabase_client()
            .table("users")
            .select("*")
            .eq("telegram_id", telegram_id)
            .single()
            .execute()
        )
        return result.data
    except Exception as e:
        logger.debug("get_user_by_telegram_id(%s): %s", telegram_id, e)
        return None


def get_user_by_id(user_id: str) -> Optional[dict]:
    """Return user dict by UUID or None if not found."""
    try:
        result = (
            get_supabase_client()
            .table("users")
            .select("*")
            .eq("id", user_id)
            .single()
            .execute()
        )
        return result.data
    except Exception as e:
        logger.error("get_user_by_id(%s): %s", user_id, e)
        return None


def create_user(data: dict) -> Optional[dict]:
    """Insert a new user row. Returns the created user dict or None."""
    try:
        result = (
            get_supabase_client()
            .table("users")
            .insert(data)
            .execute()
        )
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error("create_user: %s", e)
        return None


def update_user(user_id: str, data: dict) -> Optional[dict]:
    """Update user fields by UUID. Returns updated user dict or None."""
    try:
        data["updated_at"] = datetime.utcnow().isoformat()
        result = (
            get_supabase_client()
            .table("users")
            .update(data)
            .eq("id", user_id)
            .execute()
        )
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error("update_user(%s): %s", user_id, e)
        return None


# ── Interaction logging ───────────────────────────────────────────────────────


def log_interaction(
    telegram_id: int,
    interaction_type: str,
    model: str,
    tokens_in: int,
    tokens_out: int,
    cost: float,
) -> None:
    """Log a single AI interaction to interaction_log."""
    try:
        get_supabase_client().table("interaction_log").insert(
            {
                "telegram_id": telegram_id,
                "interaction_type": interaction_type,
                "model_used": model,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "cost_usd": cost,
            }
        ).execute()
    except Exception as e:
        logger.error("log_interaction(%s): %s", telegram_id, e)


def get_daily_interaction_count(telegram_id: int, day: date) -> int:
    """Return total interactions used today (count + borrowed). 0 if no row."""
    try:
        result = (
            get_supabase_client()
            .table("daily_interaction_counts")
            .select("count, borrowed_from_tomorrow")
            .eq("telegram_id", telegram_id)
            .eq("date", day.isoformat())
            .single()
            .execute()
        )
        if result.data:
            return result.data["count"] + result.data["borrowed_from_tomorrow"]
        return 0
    except Exception as e:
        logger.debug("get_daily_interaction_count(%s, %s): %s", telegram_id, day, e)
        return 0


def increment_daily_interaction_count(telegram_id: int, day: date) -> int:
    """Upsert daily count row, increment by 1. Returns new count."""
    try:
        client = get_supabase_client()
        result = (
            client.table("daily_interaction_counts")
            .select("count")
            .eq("telegram_id", telegram_id)
            .eq("date", day.isoformat())
            .single()
            .execute()
        )
        if result.data:
            new_count = result.data["count"] + 1
            client.table("daily_interaction_counts").update(
                {"count": new_count}
            ).eq("telegram_id", telegram_id).eq("date", day.isoformat()).execute()
        else:
            new_count = 1
            client.table("daily_interaction_counts").insert(
                {"telegram_id": telegram_id, "date": day.isoformat(), "count": 1}
            ).execute()
        return new_count
    except Exception as e:
        logger.error("increment_daily_interaction_count(%s): %s", telegram_id, e)
        return 0


# ── Conversation history ──────────────────────────────────────────────────────


def save_conversation_message(
    telegram_id: int,
    role: str,
    content: str,
    message_type: str = "text",
) -> None:
    """Append a message to conversation_history."""
    try:
        get_supabase_client().table("conversation_history").insert(
            {
                "telegram_id": telegram_id,
                "role": role,
                "content": content,
                "message_type": message_type,
            }
        ).execute()
    except Exception as e:
        logger.error("save_conversation_message(%s): %s", telegram_id, e)


def get_conversation_history(telegram_id: int, limit: int = 10) -> list:
    """Return the last `limit` messages for this user, oldest first."""
    try:
        result = (
            get_supabase_client()
            .table("conversation_history")
            .select("role, content, message_type, created_at")
            .eq("telegram_id", telegram_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return list(reversed(result.data)) if result.data else []
    except Exception as e:
        logger.error("get_conversation_history(%s): %s", telegram_id, e)
        return []


# ── Pending flows (multi-step operations) ────────────────────────────────────


def save_pending_flow(telegram_id: int, flow_type: str, flow_data: dict) -> None:
    """Upsert a pending flow for this user (one active flow per user at a time)."""
    try:
        get_supabase_client().table("pending_flows").upsert(
            {
                "telegram_id": telegram_id,
                "flow_type": flow_type,
                "flow_data": flow_data,
                "reminder_sent": False,
                "updated_at": datetime.utcnow().isoformat(),
            }
        ).execute()
    except Exception as e:
        logger.error("save_pending_flow(%s): %s", telegram_id, e)


def get_pending_flow(telegram_id: int) -> Optional[dict]:
    """Return the active pending flow for this user, or None."""
    try:
        result = (
            get_supabase_client()
            .table("pending_flows")
            .select("*")
            .eq("telegram_id", telegram_id)
            .single()
            .execute()
        )
        return result.data
    except Exception as e:
        logger.debug("get_pending_flow(%s): %s", telegram_id, e)
        return None


def delete_pending_flow(telegram_id: int) -> None:
    """Remove the pending flow for this user."""
    try:
        get_supabase_client().table("pending_flows").delete().eq(
            "telegram_id", telegram_id
        ).execute()
    except Exception as e:
        logger.error("delete_pending_flow(%s): %s", telegram_id, e)


# ── Pending follow-ups ────────────────────────────────────────────────────────


def save_pending_followup(
    telegram_id: int,
    event_id: str,
    event_title: str,
    event_end_time: datetime,
    follow_up_time: datetime,
) -> None:
    """Schedule a follow-up check after a meeting ends."""
    try:
        get_supabase_client().table("pending_followups").insert(
            {
                "telegram_id": telegram_id,
                "event_id": event_id,
                "event_title": event_title,
                "event_end_time": event_end_time.isoformat(),
                "follow_up_time": follow_up_time.isoformat(),
                "status": "pending",
            }
        ).execute()
    except Exception as e:
        logger.error("save_pending_followup(%s, %s): %s", telegram_id, event_id, e)


def get_pending_followups(telegram_id: int, status: str = "pending") -> list:
    """Return all follow-ups for this user with the given status."""
    try:
        result = (
            get_supabase_client()
            .table("pending_followups")
            .select("*")
            .eq("telegram_id", telegram_id)
            .eq("status", status)
            .order("event_end_time")
            .execute()
        )
        return result.data if result.data else []
    except Exception as e:
        logger.error("get_pending_followups(%s): %s", telegram_id, e)
        return []


def update_pending_followup(followup_id: str, status: str) -> None:
    """Update follow-up status ('pending', 'asked', 'completed', 'skipped')."""
    try:
        data: dict = {"status": status}
        if status == "asked":
            data["asked_at"] = datetime.utcnow().isoformat()
        get_supabase_client().table("pending_followups").update(data).eq(
            "id", followup_id
        ).execute()
    except Exception as e:
        logger.error("update_pending_followup(%s): %s", followup_id, e)
