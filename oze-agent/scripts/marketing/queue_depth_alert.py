"""Queue-depth alert — notifies Maan via Telegram when APPROVED queue gets thin.

Cron-friendly. Runs once daily (suggested 17:00 Warsaw — before evening
publish slot, giving time to approve more before the queue drains).

Threshold: APPROVED < 4 (covers next 2 days of 2/day cadence). Sends a
short Polish Telegram message to Maan with both APPROVED and PENDING
counts so he can decide whether to approve more PENDING rows or ask the
agent for a fresh batch.

Usage (from ``oze-agent/``)::

    railway run --service bot --environment production .venv/bin/python3 \\
        scripts/marketing/queue_depth_alert.py [--threshold N] [--always]

Exit codes:

- ``0`` — ran successfully (alert sent OR queue healthy).
- ``1`` — alert needed to be sent but Telegram delivery failed.

Lookups:
- Counts via ``list_approved_fifo(ADMIN_USER_ID, limit=100)`` and ``list_pending``.
- Recipient telegram_id from Supabase users row of OZE_OWNER_USER_ID (Maan).
- Telegram bot token from ``TELEGRAM_BOT_TOKEN`` env (same bot Maan uses).
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys

import httpx

from shared.database import get_user_by_id
from shared.marketing_sheets import (
    list_approved_fifo,
    list_pending,
)

logger = logging.getLogger(__name__)

# Marketing Sheet owner (admin@agent-oze.pl). Holds the sheet rows we count.
ADMIN_USER_ID = "ada45bc3-4e05-4e64-9f0d-2d98e138debd"

# Notification recipient (Maan). admin user has no telegram_id, so we look up
# Maan's user row and send there.
MAAN_USER_ID = "bd381405-66d2-4544-b817-117f8f8de441"

DEFAULT_THRESHOLD = 4
QUEUE_DEPTH_PROBE = 100  # max APPROVED we count (well above any healthy state)


async def _send_telegram(chat_id: int, text: str) -> bool:
    """Direct Telegram Bot API call — no Application bootstrap needed.

    Returns True on HTTP 200 + ``ok=true``. Logs failure verbosely so Railway
    cron logs surface delivery issues.
    """
    token = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
    if not token:
        logger.error("queue_depth_alert: TELEGRAM_BOT_TOKEN env var is empty")
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "disable_web_page_preview": True,
                },
            )
        if response.status_code != 200:
            logger.error(
                "queue_depth_alert: Telegram HTTP %d — %s",
                response.status_code,
                response.text[:300],
            )
            return False
        payload = response.json()
        if not payload.get("ok"):
            logger.error(
                "queue_depth_alert: Telegram ok=false — %s", payload
            )
            return False
        return True
    except Exception as e:
        logger.error("queue_depth_alert: Telegram send exception — %s", e)
        return False


def _build_message(approved: int, pending: int, threshold: int) -> str:
    """Polish notification body — concise, no meta phrases."""
    return (
        "🚨 Marketing queue niska:\n"
        f"• APPROVED: {approved} (próg: {threshold})\n"
        f"• PENDING (do review): {pending}\n\n"
        "Zatwierdź więcej lub poproś Agenta o nową paczkę."
    )


async def _run(threshold: int, always_send: bool) -> int:
    # 1. Counts.
    approved_rows = await list_approved_fifo(ADMIN_USER_ID, limit=QUEUE_DEPTH_PROBE)
    pending_rows = await list_pending(ADMIN_USER_ID)
    approved = len(approved_rows)
    pending = len(pending_rows)

    print(f"queue_depth_alert: APPROVED={approved} PENDING={pending} threshold={threshold}")

    if approved >= threshold and not always_send:
        print("queue_depth_alert: queue healthy, no notification sent")
        return 0

    # 2. Recipient lookup.
    maan = get_user_by_id(MAAN_USER_ID)
    if not maan:
        logger.error(
            "queue_depth_alert: Maan user %s not found in Supabase", MAAN_USER_ID
        )
        return 1
    telegram_id = maan.get("telegram_id")
    if not telegram_id:
        logger.error(
            "queue_depth_alert: Maan (user %s) has no telegram_id — cannot notify",
            MAAN_USER_ID,
        )
        return 1

    # 3. Send.
    text = _build_message(approved, pending, threshold)
    ok = await _send_telegram(int(telegram_id), text)
    if not ok:
        print("queue_depth_alert: ERROR — Telegram delivery failed", file=sys.stderr)
        return 1

    print(f"queue_depth_alert: notification sent to telegram_id={telegram_id}")
    return 0


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Notify Maan via Telegram when marketing APPROVED queue is thin.",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=DEFAULT_THRESHOLD,
        help=f"Trigger if APPROVED count below this (default: {DEFAULT_THRESHOLD}).",
    )
    parser.add_argument(
        "--always",
        action="store_true",
        help="Send notification regardless of threshold (for testing).",
    )
    args = parser.parse_args()

    return asyncio.run(_run(args.threshold, args.always))


if __name__ == "__main__":
    raise SystemExit(main())
