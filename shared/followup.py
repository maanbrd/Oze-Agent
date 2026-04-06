"""Follow-up engine logic for OZE-Agent.

Handles post-meeting follow-up detection, prompts, and response processing.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from shared.claude_ai import parse_followup_response
from shared.database import (
    get_pending_followups,
    save_pending_followup,
    update_pending_followup,
)
from shared.google_calendar import get_events_for_date

logger = logging.getLogger(__name__)


async def check_unreported_meetings(
    user_id: str, telegram_id: int
) -> list[dict]:
    """Return today's past meetings that still have a pending follow-up.

    Fetches events from Google Calendar, cross-references with pending_followups
    in Supabase to find meetings where the user hasn't reported back yet.
    """
    try:
        now = datetime.now(tz=timezone.utc)
        today = now.date()

        events = await get_events_for_date(user_id, today)
        if not events:
            return []

        # Only past events (already ended)
        past_events = []
        for event in events:
            end_str = event.get("end", "")
            if not end_str:
                continue
            try:
                end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                if end_dt < now:
                    past_events.append(event)
            except Exception:
                continue

        if not past_events:
            return []

        # Filter to events that have a pending follow-up record
        pending = get_pending_followups(telegram_id, status="pending")
        pending_event_ids = {f["event_id"] for f in pending}

        unreported = [e for e in past_events if e.get("id") in pending_event_ids]
        return unreported

    except Exception as e:
        logger.error("check_unreported_meetings(%s): %s", user_id, e)
        return []


async def create_followup_prompts(unreported: list[dict]) -> str:
    """Format a message listing unreported meetings for the user to respond to."""
    if not unreported:
        return ""

    lines = ["📋 *Jak przebiegły dzisiejsze spotkania?*\n"]
    for i, event in enumerate(unreported, start=1):
        title = event.get("title", "Spotkanie")
        start = event.get("start", "")
        time_str = start[11:16] if len(start) >= 16 else ""
        lines.append(f"{i}\\. {time_str} — {title}")

    lines.append(
        "\nMożesz opisać wszystkie spotkania jedną wiadomością \\(głosową lub tekstową\\)\\."
    )
    return "\n".join(lines)


async def process_followup_response(
    user_id: str,
    telegram_id: int,
    response_text: str,
    meetings: list[dict],
    user_columns: list[str],
) -> dict:
    """Parse a bulk follow-up response and return structured updates per meeting.

    Returns:
        {"updates": [{"event_id": str, "status": str, "notes": str, "next_step": str}],
         "tokens_in": int, "tokens_out": int, "cost_usd": float}
    """
    try:
        result = await parse_followup_response(response_text, meetings, user_columns)

        # Mark follow-ups as asked
        for update in result.get("updates", []):
            event_id = update.get("event_id")
            if event_id:
                pending = get_pending_followups(telegram_id, status="pending")
                for f in pending:
                    if f.get("event_id") == event_id:
                        update_pending_followup(f["id"], "asked")

        return result
    except Exception as e:
        logger.error("process_followup_response(%s): %s", user_id, e)
        return {"updates": [], "tokens_in": 0, "tokens_out": 0, "cost_usd": 0.0}


async def schedule_followup_reminder(
    telegram_id: int,
    event_id: str,
    event_title: str,
    event_end: datetime,
    follow_up_time: Optional[datetime] = None,
) -> None:
    """Save a follow-up reminder to Supabase pending_followups table.

    follow_up_time defaults to 30 minutes after the event ends.
    """
    try:
        if follow_up_time is None:
            follow_up_time = event_end + timedelta(minutes=30)

        save_pending_followup(
            telegram_id=telegram_id,
            event_id=event_id,
            event_title=event_title,
            event_end_time=event_end,
            follow_up_time=follow_up_time,
        )
    except Exception as e:
        logger.error(
            "schedule_followup_reminder(%s, event=%s): %s", telegram_id, event_id, e
        )
