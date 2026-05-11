"""Policy wrapper for R6 history use in LLM prompts."""

from datetime import timedelta

from shared.database import get_conversation_history, get_pending_flow

HISTORY_LIMIT = 10
HISTORY_SINCE = timedelta(minutes=30)


def get_history_unless_pending(telegram_id: int) -> list[dict]:
    """Return R6 history unless a pending mutation flow owns context."""
    if get_pending_flow(telegram_id):
        return []
    return get_conversation_history(
        telegram_id,
        limit=HISTORY_LIMIT,
        since=HISTORY_SINCE,
    )
