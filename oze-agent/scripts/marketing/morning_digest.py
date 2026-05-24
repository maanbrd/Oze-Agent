"""Morning digest cron — Phase 0.18, daily 08:00 Warsaw.

Sends Maan ONE Telegram message summarizing the marketing queue:
- Published yesterday (post IDs + count)
- New PENDING ready today (campaign_id + Drive link + thumbnail)
- APPROVED queue depth + ETA to empty (at 2/day publish cadence)
- Any FAILED rows (with truncated error_message)
- Iteration count from yesterday's feedback_log file

This replaces per-event Telegram pings — single calm digest at start of day.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from shared.database import get_user_by_id
from shared.marketing_sheets import (
    _read_all_rows,
    _row_to_dict,
    list_approved_fifo,
    list_pending,
)

logger = logging.getLogger(__name__)

ADMIN_USER_ID = "ada45bc3-4e05-4e64-9f0d-2d98e138debd"
MAAN_USER_ID = "bd381405-66d2-4544-b817-117f8f8de441"

WARSAW = ZoneInfo("Europe/Warsaw")
MEMORY_DIR = Path(
    "/Users/mansoniasty/.claude/projects/-Users-mansoniasty-workflows-Agent-OZE/memory"
)
PUBLISH_PER_DAY = 2  # used for ETA-to-empty computation


async def _send_telegram(chat_id: int, text: str) -> bool:
    token = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
    if not token:
        logger.error("morning_digest: TELEGRAM_BOT_TOKEN env var empty")
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "disable_web_page_preview": True,
                    "parse_mode": "HTML",
                },
            )
        if r.status_code != 200:
            logger.error("morning_digest: Telegram HTTP %d %s", r.status_code, r.text[:200])
            return False
        if not r.json().get("ok"):
            logger.error("morning_digest: Telegram ok=false %s", r.json())
            return False
        return True
    except Exception as e:
        logger.error("morning_digest: Telegram exception %s", e)
        return False


def _yesterday_log_iterations() -> int:
    """How many iteration entries did yesterday's feedback_log_*.md contain?"""
    date = (datetime.now(WARSAW) - timedelta(days=1)).strftime("%Y-%m-%d")
    path = MEMORY_DIR / f"feedback_log_{date}.md"
    if not path.is_file():
        return 0
    # Each entry starts with `## HH:MM —` header. Count those.
    return sum(
        1 for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith("## ") and "—" in line
    )


def _yesterday_published_rows(all_rows: list[list[Any]]) -> list[dict]:
    """Filter PUBLISHED rows whose published_at is yesterday (Warsaw)."""
    yesterday = (datetime.now(WARSAW) - timedelta(days=1)).strftime("%Y-%m-%d")
    out = []
    for i, raw in enumerate(all_rows[1:], start=2):
        d = _row_to_dict(raw, i)
        if d.get("status") != "PUBLISHED":
            continue
        pub_at = (d.get("published_at") or "")
        if pub_at.startswith(yesterday):
            out.append(d)
    return out


def _new_today_pending(pending_rows: list[dict]) -> list[dict]:
    """PENDING rows whose campaign_id starts with today's date (Warsaw)."""
    today = datetime.now(WARSAW).strftime("%Y-%m-%d")
    return [r for r in pending_rows if (r.get("campaign_id") or "").startswith(today)]


def _failed_rows(all_rows: list[list[Any]]) -> list[dict]:
    out = []
    for i, raw in enumerate(all_rows[1:], start=2):
        d = _row_to_dict(raw, i)
        if d.get("status") == "FAILED":
            out.append(d)
    return out


def _build_message(
    *,
    published_yesterday: list[dict],
    new_pending: list[dict],
    approved_count: int,
    failed: list[dict],
    iterations_yesterday: int,
) -> str:
    """Build a calm, scannable Polish digest. HTML-safe (Telegram parse mode HTML)."""
    eta_days = (approved_count / PUBLISH_PER_DAY) if PUBLISH_PER_DAY else 0
    lines: list[str] = []
    lines.append("☀️ <b>Marketing digest</b>")
    lines.append("")
    if published_yesterday:
        lines.append("✅ Wczoraj opublikowane:")
        for r in published_yesterday:
            cid = r.get("campaign_id", "?")
            post_id = (r.get("post_id") or "").strip()
            lines.append(f"  • <code>{cid}</code> — {post_id or '(no post_id)'}")
    else:
        lines.append("✅ Wczoraj opublikowane: 0")
    lines.append("")

    if new_pending:
        lines.append(f"📝 Nowe PENDING dziś (do review): {len(new_pending)}")
        for r in new_pending:
            cid = r.get("campaign_id", "?")
            drive = (r.get("drive_folder") or "").strip()
            if drive:
                lines.append(f'  • <a href="{drive}">{cid}</a>')
            else:
                lines.append(f"  • <code>{cid}</code>")
    else:
        lines.append("📝 Nowe PENDING dziś: 0 (queue gen mógł nie odpalić)")
    lines.append("")

    lines.append(f"📊 APPROVED w kolejce: {approved_count} (ETA empty: ~{eta_days:.1f} dni)")
    lines.append("")

    if failed:
        lines.append(f"⚠️ FAILED rows: {len(failed)}")
        for r in failed[:3]:
            cid = r.get("campaign_id", "?")
            err = (r.get("error_message") or "")[:120].replace("\n", " ")
            lines.append(f"  • <code>{cid}</code> — {err}")
        if len(failed) > 3:
            lines.append(f"  …+{len(failed) - 3} więcej")
        lines.append("")

    if iterations_yesterday:
        lines.append(f"🔁 Wczoraj feedback iterations: {iterations_yesterday}")
    return "\n".join(lines)


async def _run(dry_run: bool) -> int:
    _, all_rows = await _read_all_rows(ADMIN_USER_ID)
    approved_rows = await list_approved_fifo(ADMIN_USER_ID, limit=100)
    pending_rows = await list_pending(ADMIN_USER_ID)

    published_yesterday = _yesterday_published_rows(all_rows)
    new_pending = _new_today_pending(pending_rows)
    failed = _failed_rows(all_rows)
    iters = _yesterday_log_iterations()

    text = _build_message(
        published_yesterday=published_yesterday,
        new_pending=new_pending,
        approved_count=len(approved_rows),
        failed=failed,
        iterations_yesterday=iters,
    )

    print("=== Digest preview ===")
    print(text)
    print("======================")

    if dry_run:
        return 0

    maan = get_user_by_id(MAAN_USER_ID)
    if not maan:
        print(f"ERROR: Maan {MAAN_USER_ID} not found in users", file=sys.stderr)
        return 1
    telegram_id = maan.get("telegram_id")
    if not telegram_id:
        print(f"ERROR: Maan has no telegram_id", file=sys.stderr)
        return 1

    ok = await _send_telegram(int(telegram_id), text)
    if not ok:
        print("ERROR: Telegram delivery failed", file=sys.stderr)
        return 1
    print(f"morning_digest: sent to telegram_id={telegram_id}")
    return 0


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(description="Morning marketing digest (Phase 0.18).")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the message without sending it.",
    )
    args = parser.parse_args()
    return asyncio.run(_run(args.dry_run))


if __name__ == "__main__":
    raise SystemExit(main())
