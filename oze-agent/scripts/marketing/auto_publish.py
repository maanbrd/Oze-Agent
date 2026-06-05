"""Auto-publish FIFO marketing carousel — Agent-OZE 2026-05-22 architecture.

Cron-friendly. Designed to run twice a day from Railway scheduled jobs:

- 07:30 Warsaw (05:30 UTC winter / 05:30 UTC summer — see RAILWAY_SCHEDULED_JOBS.md)
- 19:00 Warsaw (17:00 UTC winter / 17:00 UTC summer)

At each tick:

1. Verify we are within the publish slot window — guards against random manual
   runs while tolerating stale UTC cron config after DST shifts.
2. Pop the oldest APPROVED row via ``list_approved_fifo(limit=1)``.
3. Resolve media URLs from Drive (reuses ``publish_single.resolve_media_asset``).
4. Publish to IG + FB (default; ``--platform`` overrides).
5. Mark row PUBLISHED with composite ``post_id`` (or FAILED + ``error_message``).

Current content contract: Type C carousels only. One APPROVED row is enough
for the next scheduled publish slot; there is no per-type buffer rotation.

Exit codes:

- ``0`` — published OK, OR skipped because outside publish window / queue below guard.
- ``1`` — reserved for legacy queue-empty alert semantics.
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
    publish_media_to_platforms,
    resolve_media_asset,
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

# Canonical publish slots (Warsaw local). Cron should fire ON these times.
# Keep tolerance wide enough to survive a stale UTC cron pinned one hour late
# after DST changes; --force-now is still the preferred cron command.
PUBLISH_SLOTS_WARSAW = [(7, 30), (19, 0)]
WINDOW_MINUTES = 75


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

    # 1. Pop oldest APPROVED row. Current carousel-only contract: each approved
    # row is eligible for the next publish slot. ``--min-approved`` remains as
    # an optional manual guard, but the default is 1.
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

    # 2. Resolve media URLs.
    print("Resolving media URLs from Drive...")
    asset, err = await resolve_media_asset(ADMIN_USER_ID, row.get("drive_folder", ""))
    if asset is None:
        print(f"ERROR: {err}", file=sys.stderr)
        if not dry_run:
            await mark_failed(
                ADMIN_USER_ID, campaign_id, f"media resolution failed: {err}"
            )
        return 4
    print(f"Resolved media type: {asset.media_type}")
    if asset.video_url:
        print(f"Resolved video URL: {asset.video_url}")
    print(f"Resolved {len(asset.image_urls)} slide URL(s)")
    print()

    caption_ig = _build_caption(row.get("caption_ig", ""), row.get("hashtags", ""))
    caption_fb = _build_caption(row.get("caption_fb", ""), row.get("hashtags", ""))
    first_comment = row.get("first_comment", "") or ""

    if dry_run:
        print("─── DRY RUN ───")
        print(f"Would publish campaign {campaign_id} to {effective_platform}")
        print(f"Media path: {'Reel/video' if asset.media_type == 'video' else 'image/carousel'}")
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

    print(f"Publishing {asset.media_type} media to Meta...")
    published, publish_err = await publish_media_to_platforms(
        client,
        platform=effective_platform,
        asset=asset,
        caption_ig=caption_ig,
        caption_fb=caption_fb,
        first_comment=first_comment,
    )
    if publish_err:
        await mark_failed(ADMIN_USER_ID, campaign_id, publish_err)
        print(f"ERROR: {publish_err}", file=sys.stderr)
        return 6
    for key, post_id in published.items():
        print(f"  {key.upper()} post_id: {post_id}")

    # 4. Mark PUBLISHED.
    parts: list[str] = []
    if "ig" in published:
        parts.append(f"ig:{published['ig']}")
    if "fb" in published:
        parts.append(f"fb:{published['fb']}")
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
        default=1,
        help=(
            "Adaptive queue guard: skip publish (clean exit 0) if APPROVED "
            "queue depth < N. Default 1 publishes the next approved carousel "
            "at each scheduled slot."
        ),
    )
    args = parser.parse_args()

    return asyncio.run(_run(args.platform, args.dry_run, args.force_now, args.min_approved))


if __name__ == "__main__":
    raise SystemExit(main())
