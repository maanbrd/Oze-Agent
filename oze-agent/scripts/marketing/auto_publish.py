"""Auto-publish FIFO marketing carousel — Agent-OZE 2026-05-22 architecture.

Cron-friendly. Designed to run twice a day from Railway scheduled jobs:

- 07:30 Warsaw (05:30 UTC winter / 05:30 UTC summer — see RAILWAY_SCHEDULED_JOBS.md)
- 19:00 Warsaw (17:00 UTC winter / 17:00 UTC summer)

At each tick:

1. Verify we are within ±30 min of a publish slot — guards against cron drift
   and accidental manual runs at random times.
2. Pop the oldest APPROVED row via ``list_approved_fifo(limit=1)``.
3. Resolve slide URLs from Drive (reuses ``publish_single.resolve_slide_urls``).
4. Publish to IG + FB (default; ``--platform`` overrides).
5. Mark row PUBLISHED with composite ``post_id`` (or FAILED + ``error_message``).

Exit codes:

- ``0`` — published OK, OR skipped because outside publish window (cron OK).
- ``1`` — queue empty at a publish slot (Railway will log + can alert).
- ``2..6`` — publish errors (sheet update, Drive resolution, Meta API).

Usage (from ``oze-agent/``)::

    railway run --service bot --environment production .venv/bin/python3 \\
        scripts/marketing/auto_publish.py [--dry-run] [--platform both|instagram|facebook]
        [--force-now]   # skip window check (for manual catch-up)

The script is intentionally idempotent at the row level — if it FAILED a
row, the next tick will pick the SAME row again (still APPROVED) unless
Maan manually flips status. To skip a stuck row, set status=REJECTED in
the sheet.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from scripts.marketing.publish_single import (
    _build_caption,
    _now_warsaw_iso,
    resolve_slide_urls,
)
from shared.marketing_sheets import (
    list_approved_fifo,
    mark_failed,
    mark_published,
)
from shared.meta_graph import MetaGraphClient

logger = logging.getLogger(__name__)

ADMIN_USER_ID = "ada45bc3-4e05-4e64-9f0d-2d98e138debd"
WARSAW_TZ = ZoneInfo("Europe/Warsaw")

# Canonical publish slots (Warsaw local). Cron should fire ON these times;
# the window tolerance below covers small drift (Railway cron precision,
# manual --force-now overrides at adjacent minutes, etc.).
PUBLISH_SLOTS_WARSAW = [(7, 30), (19, 0)]
WINDOW_MINUTES = 30


def _within_publish_window(now: datetime) -> Optional[tuple[int, int]]:
    """Return the matched (hour, minute) slot if ``now`` is within ±WINDOW_MINUTES.

    Returns None if outside any window.
    """
    for hour, minute in PUBLISH_SLOTS_WARSAW:
        slot = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        delta = abs((now - slot).total_seconds()) / 60.0
        if delta <= WINDOW_MINUTES:
            return (hour, minute)
    return None


async def _run(
    platform: str,
    dry_run: bool,
    force_now: bool,
    min_approved: int,
) -> int:
    now = datetime.now(WARSAW_TZ)
    print(f"auto_publish: now={now.isoformat()} (Warsaw)")

    matched_slot = _within_publish_window(now)
    if matched_slot is None and not force_now:
        print(
            f"auto_publish: outside publish window "
            f"(slots={PUBLISH_SLOTS_WARSAW}, tolerance=±{WINDOW_MINUTES} min). "
            f"Skipping. Use --force-now to override."
        )
        return 0
    if force_now and matched_slot is None:
        print("auto_publish: --force-now set, ignoring window check")
    else:
        print(f"auto_publish: matched slot {matched_slot[0]:02d}:{matched_slot[1]:02d}")

    # 1. Pop oldest APPROVED row. Adaptive guard: skip if APPROVED queue depth
    # < min_approved (default 2). Phase 0.18 daily loop: while generate is
    # 1/day, publish is 2/day FIFO — keep at least 1 buffer to avoid running
    # the queue dry between Maan's reviews. Skip is exit 0 (clean), not error.
    queue = await list_approved_fifo(ADMIN_USER_ID, limit=max(min_approved, 1))
    if len(queue) < min_approved:
        print(
            f"auto_publish: skipped — APPROVED queue depth={len(queue)} < "
            f"min={min_approved}. Letting buffer rebuild."
        )
        return 0
    if not queue:
        # Queue empty at a real publish slot is an operational miss — return
        # a distinct exit code so Railway logs/alerts surface it. Not a raise:
        # we still want subsequent ticks to retry without manual reset.
        print(
            "auto_publish: ERROR — queue empty at publish slot. "
            "No APPROVED rows in marketing_queue Sheet.",
            file=sys.stderr,
        )
        return 1

    row = queue[0]
    campaign_id = row.get("campaign_id") or ""
    row_platform = (row.get("platform") or "").strip() or "both"
    effective_platform = platform if platform != "auto" else row_platform

    print(f"auto_publish: picked campaign {campaign_id!r} (sheet row {row.get('_row')})")
    print(f"auto_publish: platform={effective_platform} (row.platform={row_platform!r})")
    print(f"auto_publish: drive_folder={row.get('drive_folder')}")
    print()

    # 2. Resolve image URLs.
    print("Resolving image URLs from Drive...")
    urls, err = await resolve_slide_urls(ADMIN_USER_ID, row.get("drive_folder", ""))
    if urls is None:
        print(f"ERROR: {err}", file=sys.stderr)
        if not dry_run:
            await mark_failed(
                ADMIN_USER_ID, campaign_id, f"image resolution failed: {err}"
            )
        return 4
    print(f"Resolved {len(urls)} slide URLs")
    print()

    caption_ig = _build_caption(row.get("caption_ig", ""), row.get("hashtags", ""))
    caption_fb = _build_caption(row.get("caption_fb", ""), row.get("hashtags", ""))
    first_comment = row.get("first_comment", "") or ""

    if dry_run:
        print("─── DRY RUN ───")
        print(f"Would publish campaign {campaign_id} to {effective_platform}")
        print()
        print("=== IG caption ===")
        print(caption_ig[:400] + ("…" if len(caption_ig) > 400 else ""))
        print()
        print("=== FB caption ===")
        print(caption_fb[:400] + ("…" if len(caption_fb) > 400 else ""))
        return 0

    # 3. Publish.
    try:
        client = MetaGraphClient()
    except ValueError as e:
        print(f"ERROR: MetaGraphClient init failed: {e}", file=sys.stderr)
        await mark_failed(
            ADMIN_USER_ID, campaign_id, f"MetaGraphClient init failed: {e}"
        )
        return 5

    if not await client.verify_token():
        await mark_failed(
            ADMIN_USER_ID, campaign_id, "Meta page token invalid or expired"
        )
        print("ERROR: Meta page token invalid", file=sys.stderr)
        return 5

    ig_post_id: Optional[str] = None
    fb_post_id: Optional[str] = None

    if effective_platform in ("instagram", "both"):
        print("Publishing to Instagram...")
        ig_post_id = await client.publish_ig_carousel(
            image_urls=urls,
            caption=caption_ig,
            first_comment=first_comment,
        )
        if ig_post_id is None:
            await mark_failed(
                ADMIN_USER_ID, campaign_id, "IG carousel publish returned None"
            )
            print("ERROR: IG publish failed", file=sys.stderr)
            return 6
        print(f"  IG media_id: {ig_post_id}")

    if effective_platform in ("facebook", "both"):
        print("Publishing to Facebook...")
        fb_post_id = await client.publish_fb_post(
            text=caption_fb,
            image_urls=urls,
        )
        if fb_post_id is None:
            err_msg = "FB publish returned None"
            if ig_post_id:
                err_msg = f"{err_msg} (IG already published as {ig_post_id})"
            await mark_failed(ADMIN_USER_ID, campaign_id, err_msg)
            print("ERROR: FB publish failed", file=sys.stderr)
            return 6
        print(f"  FB post_id:  {fb_post_id}")

    # 4. Mark PUBLISHED.
    parts: list[str] = []
    if ig_post_id:
        parts.append(f"ig:{ig_post_id}")
    if fb_post_id:
        parts.append(f"fb:{fb_post_id}")
    composite_id = "|".join(parts) if parts else ""
    published_at = _now_warsaw_iso()

    ok = await mark_published(
        ADMIN_USER_ID,
        campaign_id,
        post_id=composite_id,
        published_at=published_at,
    )
    if not ok:
        print(
            f"WARN: publish succeeded ({composite_id}) but mark_published failed. "
            f"Sheet must be updated manually for campaign {campaign_id}.",
            file=sys.stderr,
        )
    else:
        print()
        print(f"OK: campaign={campaign_id} status=PUBLISHED post_id={composite_id} published_at={published_at}")

    return 0


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="FIFO auto-publisher for Agent-OZE marketing queue.",
    )
    parser.add_argument(
        "--platform",
        choices=["instagram", "facebook", "both", "auto"],
        default="auto",
        help="Target platform(s). 'auto' (default) reads the row's platform column.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve URLs and print captions without publishing.",
    )
    parser.add_argument(
        "--force-now",
        action="store_true",
        help="Skip the publish-window check (for manual catch-up runs).",
    )
    parser.add_argument(
        "--min-approved",
        type=int,
        default=2,
        help=(
            "Adaptive queue guard: skip publish (clean exit 0) if APPROVED "
            "queue depth < N. Phase 0.18 default 2 protects buffer while "
            "generate is 1/day and publish is 2/day."
        ),
    )
    args = parser.parse_args()

    return asyncio.run(_run(args.platform, args.dry_run, args.force_now, args.min_approved))


if __name__ == "__main__":
    raise SystemExit(main())
