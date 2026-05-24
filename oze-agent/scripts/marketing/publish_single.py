"""Manual publish CLI — Agent-OZE marketing carousel smoke test.

One-off / on-demand publisher for a single ``campaign_id`` from the
``marketing_queue`` Sheet. Used to smoke-test the Meta publishing flow
before the cron is wired up.

Workflow:

1. Read the row by ``campaign_id`` via ``shared.marketing_sheets.get_row``.
2. Validate ``status`` (must be APPROVED in non-dry-run; PENDING tolerated
   only with ``--dry-run``).
3. Resolve image URLs from the row's ``drive_folder`` — list ``slide_*.png``
   files via Drive, ensure they are publicly accessible (Anyone with link),
   and convert to direct-download URLs that Meta's fetcher can read.
4. Build the caption (caption_ig / caption_fb with hashtags appended).
5. In ``--dry-run`` mode: print everything and exit.
6. Publish via ``shared.meta_graph.MetaGraphClient`` (IG, FB, or both).
7. Mark the row PUBLISHED (with ``post_id`` and ``published_at``) on success,
   or FAILED with the error message on failure.

Usage (from ``oze-agent/``)::

    railway run --service bot --environment production .venv/bin/python3 \\
        scripts/marketing/publish_single.py \\
        --campaign-id 2026-05-19-typ-c-pi-cialdini-pomysle \\
        [--dry-run] [--platform instagram|facebook|both]
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import re
import sys
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from shared.google_drive import extract_folder_id, get_drive_service
from shared.marketing_sheets import (
    STATUS_APPROVED,
    STATUS_PENDING,
    get_row,
    mark_failed,
    mark_published,
)
from shared.meta_graph import MetaGraphClient

logger = logging.getLogger(__name__)

ADMIN_USER_ID = "ada45bc3-4e05-4e64-9f0d-2d98e138debd"
WARSAW_TZ = ZoneInfo("Europe/Warsaw")

# Filename pattern for canonical carousel slides (slide_01.png .. slide_06.png).
SLIDE_FILENAME_RE = re.compile(r"^slide_\d{2}\.png$", re.IGNORECASE)


# ── Drive helpers — public sharing + image URL resolution ────────────────────


def _direct_download_url(file_id: str) -> str:
    """Build the Drive direct-download URL that Meta's fetcher can read.

    NB: this only works if the file is shared "Anyone with the link" with
    role=reader. The caller is responsible for ensuring that.
    """
    return f"https://drive.google.com/uc?id={file_id}&export=download"


def _ensure_anyone_reader_sync(service, file_id: str) -> bool:
    """Idempotently grant ``Anyone with link, reader`` to a Drive file.

    Returns True if the permission exists (now or already), False on API error.
    """
    try:
        perms = service.permissions().list(
            fileId=file_id, fields="permissions(id,type,role)"
        ).execute()
        for p in perms.get("permissions", []):
            if p.get("type") == "anyone" and p.get("role") in ("reader", "writer"):
                return True
        service.permissions().create(
            fileId=file_id,
            body={"role": "reader", "type": "anyone"},
            fields="id",
        ).execute()
        return True
    except Exception as e:
        logger.error("ensure_anyone_reader(%s): %s", file_id, e)
        return False


async def resolve_slide_urls(
    user_id: str, folder_url: str
) -> tuple[Optional[list[str]], Optional[str]]:
    """Find ``slide_*.png`` files in a Drive folder and return public URLs.

    Returns ``(urls, error_message)``. On success ``error_message`` is None.
    On failure ``urls`` is None and ``error_message`` describes the issue.

    Side effects:
    - Sets ``Anyone with link, reader`` on the folder and every slide PNG.
    """
    folder_id = extract_folder_id(folder_url)
    if not folder_id:
        return None, f"could not extract folder ID from drive_folder={folder_url!r}"

    service = await get_drive_service(user_id)
    if service is None:
        return None, f"Google Drive service unavailable for user {user_id}"

    def _resolve_sync() -> tuple[Optional[list[str]], Optional[str]]:
        # Make folder publicly readable (so file URLs derived from it work).
        if not _ensure_anyone_reader_sync(service, folder_id):
            return None, f"failed to make folder {folder_id} publicly readable"

        # List slide_*.png files in the folder.
        query = (
            f"'{folder_id}' in parents "
            f"and mimeType = 'image/png' "
            f"and trashed = false"
        )
        try:
            result = service.files().list(
                q=query,
                fields="files(id, name)",
                orderBy="name",
                pageSize=50,
            ).execute()
        except Exception as e:
            return None, f"Drive list failed: {e}"

        files = [
            f for f in result.get("files", [])
            if SLIDE_FILENAME_RE.match(f.get("name", ""))
        ]
        if not files:
            return None, (
                f"no slide_*.png files found in folder {folder_id} — expected 6"
            )

        # Sort by name for canonical order (slide_01..slide_06).
        files.sort(key=lambda f: f["name"].lower())

        urls: list[str] = []
        for f in files:
            file_id = f["id"]
            if not _ensure_anyone_reader_sync(service, file_id):
                return None, (
                    f"file {f['name']} ({file_id}) could not be made publicly readable"
                )
            urls.append(_direct_download_url(file_id))
        return urls, None

    return await asyncio.to_thread(_resolve_sync)


# ── Caption building ─────────────────────────────────────────────────────────


def _build_caption(base: str, hashtags: str) -> str:
    """Append hashtags after a blank line if non-empty.

    Hashtags stored in Sheet are CSV ("#a, #b, #c") for readability,
    but IG/FB render comma-separated hashtags as broken links.
    Normalize to space-separated ("#a #b #c") before appending.
    """
    base = (base or "").rstrip()
    tags = (hashtags or "").strip()
    if not tags:
        return base
    normalized = " ".join(tag.strip() for tag in tags.replace(",", " ").split() if tag.strip())
    return f"{base}\n\n{normalized}"


def _now_warsaw_iso() -> str:
    return datetime.now(WARSAW_TZ).strftime("%Y-%m-%d %H:%M")


# ── Main publish flow ────────────────────────────────────────────────────────


async def _run(
    campaign_id: str,
    platform: str,
    dry_run: bool,
) -> int:
    row = await get_row(ADMIN_USER_ID, campaign_id)
    if row is None:
        print(
            f"ERROR: campaign {campaign_id!r} not found in marketing_queue Sheet",
            file=sys.stderr,
        )
        return 2

    status = (row.get("status") or "").strip()
    print(f"Campaign: {campaign_id}")
    print(f"Status:   {status}")
    print(f"Platform: {platform} (row.platform={row.get('platform')!r})")
    print(f"Drive:    {row.get('drive_folder')}")
    print()

    if not dry_run and status != STATUS_APPROVED:
        print(
            f"ERROR: status is {status!r}, not {STATUS_APPROVED!r}. "
            f"Set status=APPROVED in the Sheet before publishing, or re-run "
            f"with --dry-run to preview.",
            file=sys.stderr,
        )
        return 3
    if dry_run and status not in (STATUS_APPROVED, STATUS_PENDING):
        print(
            f"WARN: status is {status!r} (not APPROVED/PENDING). "
            f"Dry-run continuing anyway.",
            file=sys.stderr,
        )

    # 1. Resolve image URLs.
    print("Resolving image URLs from Drive...")
    urls, err = await resolve_slide_urls(ADMIN_USER_ID, row.get("drive_folder", ""))
    if urls is None:
        print(f"ERROR: {err}", file=sys.stderr)
        if not dry_run:
            await mark_failed(
                ADMIN_USER_ID, campaign_id, f"image resolution failed: {err}"
            )
        return 4
    print(f"Resolved {len(urls)} slide URLs:")
    for u in urls:
        print(f"  {u}")
    print()

    caption_ig = _build_caption(row.get("caption_ig", ""), row.get("hashtags", ""))
    caption_fb = _build_caption(row.get("caption_fb", ""), row.get("hashtags", ""))
    first_comment = row.get("first_comment", "") or ""

    if dry_run:
        print("─── DRY RUN ───")
        print()
        print("=== IG caption ===")
        print(caption_ig)
        print()
        print("=== IG first comment ===")
        print(first_comment or "(none)")
        print()
        print("=== FB caption ===")
        print(caption_fb)
        print()
        print(f"Would publish to: {platform}")
        print("(no Meta API calls made)")
        return 0

    # 2. Real publish.
    try:
        client = MetaGraphClient()
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
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

    if platform in ("instagram", "both"):
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
        print(f"  URL hint:    https://www.instagram.com/p/<shortcode>/ (resolve via API if needed)")

    if platform in ("facebook", "both"):
        print("Publishing to Facebook...")
        fb_post_id = await client.publish_fb_carousel(
            image_urls=urls,
            caption=caption_fb,
        )
        if fb_post_id is None:
            err_msg = "FB carousel publish returned None"
            if ig_post_id:
                err_msg = f"{err_msg} (IG already published as {ig_post_id})"
            await mark_failed(ADMIN_USER_ID, campaign_id, err_msg)
            print("ERROR: FB publish failed", file=sys.stderr)
            return 6
        print(f"  FB post_id:  {fb_post_id}")
        print(f"  URL:         https://www.facebook.com/{fb_post_id}")

    # Persist canonical post_id back to the sheet. Composite ids let the
    # insights cron differentiate IG vs FB metric collection later.
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
            f"Update the Sheet manually.",
            file=sys.stderr,
        )
    else:
        print()
        print(f"Sheet updated: status=PUBLISHED, post_id={composite_id}, published_at={published_at}")

    return 0


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Publish a single APPROVED marketing carousel to Meta.",
    )
    parser.add_argument(
        "--campaign-id",
        required=True,
        help="Campaign ID from the marketing_queue Sheet (col A).",
    )
    parser.add_argument(
        "--platform",
        choices=["instagram", "facebook", "both"],
        default="both",
        help="Target platform(s). Default: both.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve URLs and print captions without publishing.",
    )
    args = parser.parse_args()

    return asyncio.run(_run(args.campaign_id, args.platform, args.dry_run))


if __name__ == "__main__":
    raise SystemExit(main())
