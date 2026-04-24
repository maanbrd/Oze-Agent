"""Phase 6 morning brief — scheduler entry point + rules.

Runs at 07:00 Europe/Warsaw, Monday–Friday. One send per eligible user
per Warsaw-local date (dedup via users.last_morning_brief_sent_date).

Data sources, explicitly separated:
- Terminarz = Google Calendar events (event_type → Spotkanie / Telefon / Oferta).
- Do dopilnowania dziś = Sheets K/L ("Następny krok" + "Data następnego kroku"
  ≤ today) where Status is non-terminal.

Per-user errors are isolated; one user's Google outage does not abort the
whole run. The dedup column is updated only on successful send — a failed
user retries naturally the next weekday.
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from telegram import Bot
from telegram.constants import ParseMode

from shared.database import (
    get_eligible_users_for_morning_brief,
    update_last_morning_brief_sent,
)
from shared.errors import ProactiveFetchError
from shared.formatting import format_morning_brief_short
from shared.google_calendar import get_events_for_range_or_raise
from shared.google_sheets import get_all_clients_or_raise

logger = logging.getLogger(__name__)

WARSAW = ZoneInfo("Europe/Warsaw")

# Statuses that close the client lifecycle — no more follow-up due today.
TERMINAL_STATUSES = frozenset({
    "Podpisane",
    "Zamontowana",
    "Rezygnacja z umowy",
    "Nieaktywny",
    "Odrzucone",
})


@dataclass
class MorningBriefRunResult:
    total_eligible: int = 0
    sent: int = 0
    skipped_deduped: int = 0
    skipped_error: int = 0

    def __str__(self) -> str:
        return (
            f"total_eligible={self.total_eligible} sent={self.sent} "
            f"skipped_deduped={self.skipped_deduped} skipped_error={self.skipped_error}"
        )


def _today_warsaw() -> date:
    return datetime.now(tz=WARSAW).date()


def _warsaw_day_bounds(day: date) -> tuple[datetime, datetime]:
    """Return Warsaw-local [midnight, next midnight) bounds for Calendar."""
    start = datetime.combine(day, time.min, tzinfo=WARSAW)
    return start, start + timedelta(days=1)


def _already_sent_today(row: dict, today: date) -> bool:
    stored = row.get("last_morning_brief_sent_date")
    if not stored:
        return False
    # Supabase returns DATE as ISO string "YYYY-MM-DD".
    return str(stored) == today.isoformat()


def _parse_next_step_date(value) -> date | None:
    """Best-effort parse of Sheets 'Data następnego kroku' cell.

    Accepts ISO ("2026-04-23" or "2026-04-23 14:00"), Excel serial
    integer (40000+), and Polish "DD.MM.YYYY". Returns None on any
    other shape — the row is then silently skipped from the brief.
    """
    if value is None or value == "":
        return None
    if isinstance(value, str):
        s = value.strip()
        if len(s) >= 10 and s[4:5] == "-":
            try:
                return date.fromisoformat(s[:10])
            except ValueError:
                pass
        if "." in s:
            parts = s.split(" ")[0].split(".")
            if len(parts) == 3:
                try:
                    return date(int(parts[2]), int(parts[1]), int(parts[0]))
                except ValueError:
                    pass
    try:
        n = int(value)
        if 40000 < n < 60000:
            return (datetime(1899, 12, 30) + timedelta(days=n)).date()
    except (TypeError, ValueError):
        pass
    return None


async def _fetch_open_next_steps(user_id: str, today: date) -> list[dict]:
    """Return clients with an open 'Następny krok' due on/before `today`.

    Excludes clients in terminal statuses. Sorted by next_step_date
    ascending (oldest overdue first). Each item exposes the minimum
    fields needed by the formatter: name, next_step, next_step_date,
    status.
    """
    clients = await get_all_clients_or_raise(user_id)
    results: list[dict] = []
    for row in clients:
        status = (row.get("Status") or "").strip()
        if status in TERMINAL_STATUSES:
            continue
        next_step = (row.get("Następny krok") or "").strip()
        if not next_step:
            continue
        due = _parse_next_step_date(row.get("Data następnego kroku"))
        if due is None or due > today:
            continue
        name = (row.get("Imię i nazwisko") or "").strip()
        if not name:
            continue
        results.append({
            "name": name,
            "next_step": next_step,
            "next_step_date": due,
            "status": status,
        })
    results.sort(key=lambda r: r["next_step_date"])
    return results


async def run_morning_brief(bot: Bot) -> MorningBriefRunResult:
    """Send the Phase 6 morning brief to every eligible user.

    Called from the PTB JobQueue callback at 07:00 Warsaw on Mon–Fri.
    Safe to call multiple times on the same Warsaw date — per-user
    dedup prevents double-send.
    """
    result = MorningBriefRunResult()
    today = _today_warsaw()
    eligible = get_eligible_users_for_morning_brief()
    result.total_eligible = len(eligible)

    for row in eligible:
        user_id = row.get("id")
        telegram_id = row.get("telegram_id")
        if not user_id or not telegram_id:
            result.skipped_error += 1
            continue

        if _already_sent_today(row, today):
            result.skipped_deduped += 1
            continue

        try:
            start_warsaw, end_warsaw = _warsaw_day_bounds(today)
            events = await get_events_for_range_or_raise(user_id, start_warsaw, end_warsaw)
            open_next_steps = await _fetch_open_next_steps(user_id, today)
            text = format_morning_brief_short(events, open_next_steps)
            await bot.send_message(
                chat_id=telegram_id,
                text=text,
                parse_mode=ParseMode.MARKDOWN_V2,
            )
            if not update_last_morning_brief_sent(user_id, today):
                logger.error(
                    "morning_brief.dedup_write_failed user_id=%s "
                    "brief_delivered=True possible_double_send_risk=True",
                    user_id,
                )
            result.sent += 1
        except ProactiveFetchError as e:
            logger.warning(
                "morning_brief.skipped_fetch_error user_id=%s reason=%s",
                user_id,
                e,
            )
            result.skipped_error += 1
        except Exception as e:
            logger.error(
                "morning_brief.send_failed user_id=%s telegram_id=%s err=%s",
                user_id, telegram_id, e,
            )
            result.skipped_error += 1

    return result
