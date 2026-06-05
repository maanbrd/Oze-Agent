"""Manual publish CLI — Agent-OZE marketing carousel smoke test.

One-off / on-demand publisher for a single ``campaign_id`` from the
``marketing_queue`` Sheet. Used to smoke-test the Meta publishing flow
before the cron is wired up.

Workflow:

1. Read the row by ``campaign_id`` via ``shared.marketing_sheets.get_row``.
2. Validate ``status`` (must be APPROVED in non-dry-run; PENDING tolerated
   only with ``--dry-run``).
3. Resolve image URLs from the row's ``drive_folder`` — accepts either the
   campaign folder URL or the generated ``preview.mp4`` Drive file URL, lists
   ``slide_*.png`` files via Drive, ensures they are publicly accessible
   (Anyone with link), and converts them to direct-download URLs that Meta's
   fetcher can read.
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
import json
import logging
import re
import sys
from dataclasses import dataclass
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
DRIVE_FILE_RE = re.compile(r"/file/d/([A-Za-z0-9_-]+)")
MANIFEST_FILENAMES = ("instagram_post.json", "meta.json")


@dataclass(frozen=True)
class MediaAsset:
    media_type: str  # "video" | "image"
    image_urls: list[str]
    video_url: Optional[str]
    thumbnail_url: Optional[str]


# ── Drive helpers — public sharing + image URL resolution ────────────────────


def _direct_download_url(file_id: str) -> str:
    """Build the Drive direct-download URL that Meta's fetcher can read.

    NB: this only works if the file is shared "Anyone with the link" with
    role=reader. The caller is responsible for ensuring that.
    """
    return f"https://drive.google.com/uc?id={file_id}&export=download"


def _extract_drive_file_id(value: str) -> Optional[str]:
    if not value:
        return None
    match = DRIVE_FILE_RE.search(value)
    if match:
        return match.group(1)
    match = re.search(r"[?&]id=([A-Za-z0-9_-]+)", value)
    if match:
        return match.group(1)
    return None


def _resolve_folder_id_sync(
    service,
    *,
    folder_id: Optional[str],
    file_id: Optional[str],
) -> tuple[Optional[str], Optional[str]]:
    if folder_id:
        return folder_id, None

    if not file_id:
        return None, "could not extract folder ID from drive_folder"

    try:
        file = service.files().get(fileId=file_id, fields="id, name, parents").execute()
    except Exception as e:
        return None, f"Drive file lookup failed for {file_id}: {e}"

    parents = file.get("parents") or []
    if not parents:
        return None, f"preview file {file_id} has no parent folder"
    return parents[0], None


def _parse_drive_review_target(drive_value: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
    folder_id = extract_folder_id(drive_value)
    if folder_id:
        return folder_id, None, None

    file_id = _extract_drive_file_id(drive_value)
    if not file_id:
        return None, None, f"could not extract folder ID from drive_folder={drive_value!r}"
    return None, file_id, None


def _download_json_manifest_sync(service, files: list[dict]) -> Optional[dict]:
    """Read the campaign manifest from Drive if present.

    The manifest is the source of truth for whether a folder publishes as
    carousel or video. ``preview.mp4`` may exist only for review.
    """
    manifest = next(
        (
            f for name in MANIFEST_FILENAMES
            for f in files
            if str(f.get("name") or "").lower() == name
        ),
        None,
    )
    if not manifest:
        return None
    try:
        raw = service.files().get_media(fileId=manifest["id"]).execute()
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        return json.loads(raw)
    except Exception as e:
        logger.warning("could not read Drive manifest %s: %s", manifest.get("name"), e)
        return None


def _publish_type_from_manifest(manifest: Optional[dict]) -> Optional[str]:
    if not manifest:
        return None
    media = manifest.get("media") or {}
    publish_type = str(media.get("publish_type") or "").strip().lower()
    if publish_type in {"carousel", "image"}:
        return "carousel"
    if publish_type in {"video", "reel"}:
        return "video"
    if media.get("video") and not media.get("images"):
        return "video"
    return None


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
    asset, err = await resolve_media_asset(user_id, folder_url)
    if err:
        return None, err
    if not asset or not asset.image_urls:
        return None, "no slide_*.png files found for image publishing"
    return asset.image_urls, None


async def resolve_media_asset(
    user_id: str, drive_value: str
) -> tuple[Optional[MediaAsset], Optional[str]]:
    """Resolve a Drive review target to either a video or image publishing asset.

    The manifest is the source of truth when available. A Type C carousel may
    include ``preview.mp4`` for review while still publishing ``slide_*.png``.
    Legacy folders without a manifest-level publish type keep the old fallback:
    a video file means Reel/video, otherwise ``slide_*.png`` means carousel.
    """
    folder_id, file_id, parse_err = _parse_drive_review_target(drive_value)
    if parse_err:
        return None, parse_err

    service = await get_drive_service(user_id)
    if service is None:
        return None, f"Google Drive service unavailable for user {user_id}"

    def _resolve_sync() -> tuple[Optional[MediaAsset], Optional[str]]:
        resolved_folder_id, folder_err = _resolve_folder_id_sync(
            service,
            folder_id=folder_id,
            file_id=file_id,
        )
        if not resolved_folder_id:
            return None, folder_err

        # Make folder publicly readable (so file URLs derived from it work).
        if not _ensure_anyone_reader_sync(service, resolved_folder_id):
            return None, f"failed to make folder {resolved_folder_id} publicly readable"

        # List media files in the folder. Keep this broad so new formats do not
        # need separate Drive list calls.
        query = (
            f"'{resolved_folder_id}' in parents "
            f"and trashed = false"
        )
        try:
            result = service.files().list(
                q=query,
                fields="files(id, name, mimeType)",
                orderBy="name",
                pageSize=50,
            ).execute()
        except Exception as e:
            return None, f"Drive list failed: {e}"

        files = result.get("files", [])
        manifest = _download_json_manifest_sync(service, files)
        manifest_publish_type = _publish_type_from_manifest(manifest)
        slide_files = [
            f for f in result.get("files", [])
            if SLIDE_FILENAME_RE.match(f.get("name", ""))
        ]
        # Sort by name for canonical order (slide_01..slide_06).
        slide_files.sort(key=lambda f: f["name"].lower())

        image_urls: list[str] = []
        for f in slide_files:
            slide_file_id = f["id"]
            if not _ensure_anyone_reader_sync(service, slide_file_id):
                return None, (
                    f"file {f['name']} ({slide_file_id}) could not be made publicly readable"
                )
            image_urls.append(_direct_download_url(slide_file_id))

        preview = next(
            (
                f for f in files
                if str(f.get("name") or "").lower() == "preview.mp4"
                or str(f.get("mimeType") or "").lower() == "video/mp4"
            ),
            None,
        )
        if manifest_publish_type == "carousel":
            if not image_urls:
                return None, (
                    f"manifest publish_type=carousel but no slide_*.png files found "
                    f"in folder {resolved_folder_id}"
                )
            return (
                MediaAsset(
                    media_type="image",
                    image_urls=image_urls,
                    video_url=None,
                    thumbnail_url=image_urls[0],
                ),
                None,
            )

        if preview and manifest_publish_type in {"video", None}:
            preview_id = preview["id"]
            if not _ensure_anyone_reader_sync(service, preview_id):
                return None, (
                    f"file {preview['name']} ({preview_id}) could not be made publicly readable"
                )
            return (
                MediaAsset(
                    media_type="video",
                    image_urls=image_urls,
                    video_url=_direct_download_url(preview_id),
                    thumbnail_url=image_urls[0] if image_urls else None,
                ),
                None,
            )

        if not image_urls:
            return None, (
                f"no preview.mp4 or slide_*.png files found in folder {resolved_folder_id}"
            )

        return (
            MediaAsset(
                media_type="image",
                image_urls=image_urls,
                video_url=None,
                thumbnail_url=image_urls[0],
            ),
            None,
        )

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


async def publish_media_to_platforms(
    client,
    *,
    platform: str,
    asset: MediaAsset,
    caption_ig: str,
    caption_fb: str,
    first_comment: str,
) -> tuple[dict[str, str], Optional[str]]:
    """Publish a resolved asset to the selected Meta platform(s)."""
    published: dict[str, str] = {}

    if asset.media_type == "video":
        if not asset.video_url:
            return published, "video asset has no video_url"
        if platform in ("instagram", "both"):
            ig_post_id = await client.publish_ig_reel(
                video_url=asset.video_url,
                caption=caption_ig,
                thumbnail_url=asset.thumbnail_url,
                first_comment=first_comment,
            )
            if ig_post_id is None:
                return published, "IG Reel publish returned None"
            published["ig"] = ig_post_id
        if platform in ("facebook", "both"):
            fb_post_id = await client.publish_fb_video(
                video_url=asset.video_url,
                description=caption_fb,
                thumbnail_url=asset.thumbnail_url,
            )
            if fb_post_id is None:
                return published, "FB video publish returned None"
            published["fb"] = fb_post_id
        return published, None

    if platform in ("instagram", "both"):
        ig_post_id = await client.publish_ig_carousel(
            image_urls=asset.image_urls,
            caption=caption_ig,
            first_comment=first_comment,
        )
        if ig_post_id is None:
            return published, "IG carousel publish returned None"
        published["ig"] = ig_post_id
    if platform in ("facebook", "both"):
        fb_post_id = await client.publish_fb_post(
            text=caption_fb,
            image_urls=asset.image_urls,
        )
        if fb_post_id is None:
            return published, "FB publish returned None"
        published["fb"] = fb_post_id
    return published, None


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

    # 1. Resolve media URLs.
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
        print(f"  video: {asset.video_url}")
    print(f"Resolved {len(asset.image_urls)} slide URL(s):")
    for u in asset.image_urls:
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
        print(f"Media path: {'Reel/video' if asset.media_type == 'video' else 'image/carousel'}")
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

    print(f"Publishing {asset.media_type} media to Meta...")
    published, publish_err = await publish_media_to_platforms(
        client,
        platform=platform,
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

    # Persist canonical post_id back to the sheet. Composite ids let the
    # insights cron differentiate IG vs FB metric collection later.
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
