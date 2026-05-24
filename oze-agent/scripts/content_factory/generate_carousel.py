"""Generate Agent-OZE marketing carousel from JSON config.

Reads a carousel config (slides + visual_prompts + copy), calls OpenAI Images API
(gpt-image-2) for each slide, saves PNG locally and optionally uploads the whole
folder to Google Drive `Agent-OZE/Marketing/<campaign_id>/` via the project's
existing Drive wrapper.

Usage (from oze-agent/ directory):
    railway run --service bot --environment production \\
        python -m scripts.content_factory.generate_carousel \\
        --config /tmp/2026-05-19-typ-a.json \\
        [--output-dir ~/marketing-output] \\
        [--owner-user-id ada45bc3-4e05-4e64-9f0d-2d98e138debd] \\
        [--skip-drive]

Required env:
    OPENAI_API_KEY  (from Railway / bot.config.Config)

Drive owner (one of, in this priority order):
    1. ``--owner-user-id`` CLI flag (overrides env)
    2. ``OZE_OWNER_USER_ID`` env var
    If neither is set and ``--skip-drive`` is also absent, the script fails.

    Default future target: admin user ``ada45bc3-4e05-4e64-9f0d-2d98e138debd``
    (admin@agent-oze.pl) so the Marketing Sheet can preview files without
    cross-account access errors.

JSON config format: see ~/.agents/skills/oze-content-factory/examples/carousel_config_example.json
Brand kit + prompt rules: ~/.agents/skills/oze-content-factory/references/
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import io
import json
import logging
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

import openai
from googleapiclient.http import MediaIoBaseUpload
from PIL import Image, ImageDraw, ImageFilter

from bot.config import Config
from shared.google_drive import get_drive_service

logger = logging.getLogger(__name__)


REPO_ROOT = Path(__file__).resolve().parents[3]
BRAND_ASSET_DIR = REPO_ROOT / "assets" / "brand"
BRAND_ICON_PATH = BRAND_ASSET_DIR / "agent-oze-icon.png"
BRAND_LOGO_PATH = BRAND_ASSET_DIR / "agent-oze-logo.png"
BRAND_ASSET_OUTPUT_FILES = {
    BRAND_ICON_PATH: "brand_agent_oze_icon.png",
    BRAND_LOGO_PATH: "brand_agent_oze_logo.png",
}


BRAND_LOCK_PREFIX = """\
Minimalist single-element graphic design for Instagram carousel.
Solid dark near-black background hex #0b0d10.
Bright glowing green accent color hex #3DFF7A with soft 40px glow halo.
Off-white text color hex #e4e4e7 in clean modern system sans-serif typography (Apple-system / Segoe UI / Roboto style — NEVER serif, NEVER script).
Technical, professional, high-contrast aesthetic.
1024x1536 portrait aspect ratio (close to 4:5 Instagram carousel).
Single hero element composition, generous negative space.

ABSOLUTE PROHIBITIONS — DO NOT include any of:
- people, faces, characters, men, women, humans, hands, body parts (unless this is a Type C celebrity-quote slide, then face is embedded separately, NOT generated)
- AI characters, robots, androids, cyborgs, holograms, 3D avatars
- futuristic / sci-fi / cyberpunk / neon city aesthetics
- 3D rendered / Cinema 4D / Blender / Unreal Engine style
- multi-color gradients, rainbow, vibrant non-brand colors
- generic stock photo style or cartoon mascots
- decorative scripts, calligraphy, ornate elements
- emoji or pictographic icons unless explicitly requested
- texture backgrounds — keep background flat solid #0b0d10

REQUIRED elements:
- All visual emphasis through size, weight, position, and #3DFF7A glow
- If icon needed: monoline outline style only (1-2pt stroke, no fill), in #3DFF7A
- Text rendering must be SHARP and READABLE (not stylized into illegibility)
- Official Agent OZE brand mark: bright #3DFF7A glowing ring with a centered #3DFF7A dot on a near-black background
- Never invent alternate Agent OZE logos, symbols, mascots, letters inside the mark, or extra brand colors

SLIDE-SPECIFIC INSTRUCTIONS:
"""


def build_full_prompt(slide_visual_prompt: str) -> str:
    """Combine brand-lock prefix with per-slide visual prompt."""
    return BRAND_LOCK_PREFIX + slide_visual_prompt.strip()


def _download_photo(url: str, cache_path: Path) -> bytes:
    """Download photo from URL to cache_path (idempotent — returns bytes from cache if exists)."""
    if cache_path.exists():
        return cache_path.read_bytes()
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (oze-content-factory)"})
    with urlopen(req, timeout=30) as resp:  # noqa: S310 — trusted URLs from concept-library whitelist
        data = resp.read()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(data)
    return data


def _feather_mask(width: int, height: int, feather_pct: float = 0.06) -> Image.Image:
    """Build an alpha mask with soft fade-out edges (no hard rectangle borders).

    Default feather_pct 0.06 (less aggressive than original 0.10) — keeps photo visible
    while softening edges to blend with dark background.
    """
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    feather_px = max(int(min(width, height) * feather_pct), 4)
    # Fill inner rect fully opaque, leaving feather_px border at 0 alpha
    inner = (feather_px, feather_px, width - feather_px, height - feather_px)
    draw.rectangle(inner, fill=255)
    # Gaussian blur the edges to create gradient fade-out
    blurred = mask.filter(ImageFilter.GaussianBlur(radius=feather_px))
    return blurred


def _vignette_overlay(width: int, height: int, dark_top: int = 0, dark_bottom: int = 220) -> Image.Image:
    """Build a dark gradient overlay used for full-screen photo legibility (dark at bottom for text)."""
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    for y in range(height):
        # Linear interpolation top→bottom
        alpha = int(dark_top + (dark_bottom - dark_top) * (y / max(height - 1, 1)))
        for_row = Image.new("RGBA", (width, 1), (11, 13, 16, alpha))
        overlay.paste(for_row, (0, y))
    return overlay


def apply_photo_overlay(
    slide_path: Path,
    photo_url: str,
    position: str = "center",
    size_pct: float = 0.45,
    mode: str = "rectangle",
    opacity: float = 1.0,
    cache_dir: Path | None = None,
) -> None:
    """Composite an authentic external photo onto a generated slide PNG.

    Used for Type C carousels (cytaty mistrzów sprzedaży) — Slide 1 embeds an
    authentic public-figure portrait (NOT AI-generated). The gpt-image-2 background
    should be generated with empty space reserved in the indicated position.

    Modes (Maan feedback 2026-05-19 — photo musi wyglądać fresh, nie 'kopiuj-wklej'):
      - 'rectangle' (default): hard rectangular paste (legacy)
      - 'feather': soft gradient fade-out edges, no hard borders, optional opacity
      - 'full_screen': photo na cały slide z dark gradient overlay (dark at bottom for text legibility)

    Args:
        slide_path: PNG file to modify in-place.
        photo_url: HTTPS URL to portrait (Wikipedia Commons / press kit / book cover).
        position: One of 'top', 'left', 'right', 'center' (default: 'center'). Ignored when mode='full_screen'.
        size_pct: Photo's longest side as fraction of slide width (default: 0.45). Ignored when mode='full_screen'.
        mode: 'rectangle' | 'feather' | 'full_screen'.
        opacity: 0.0–1.0 photo opacity (default 1.0). Used with 'feather' for blending.
        cache_dir: Where to cache downloaded photos (default: /tmp/oze-content-photos).
    """
    if cache_dir is None:
        cache_dir = Path("/tmp/oze-content-photos")

    photo_filename = photo_url.rsplit("/", 1)[-1].split("?")[0]
    photo_cache = cache_dir / photo_filename
    photo_bytes = _download_photo(photo_url, photo_cache)

    slide = Image.open(slide_path).convert("RGBA")
    photo = Image.open(io.BytesIO(photo_bytes)).convert("RGBA")

    if mode == "full_screen":
        # Scale photo to cover the whole slide (cover-fit, preserving aspect)
        slide_ratio = slide.width / slide.height
        photo_ratio = photo.width / photo.height
        if photo_ratio > slide_ratio:
            new_h = slide.height
            new_w = int(new_h * photo_ratio)
        else:
            new_w = slide.width
            new_h = int(new_w / photo_ratio)
        photo = photo.resize((new_w, new_h), Image.LANCZOS)
        x = (slide.width - new_w) // 2
        y = (slide.height - new_h) // 2

        photo_layer = Image.new("RGBA", slide.size, (0, 0, 0, 0))
        photo_layer.paste(photo, (x, y))

        # Build mask: photo only fills the DARK pixels of slide (luminance < threshold).
        # Bright pixels (text, glow, BrandMark) stay intact — text remains visible over photo.
        slide_rgb = slide.convert("L")  # grayscale for luminance check
        dark_mask = slide_rgb.point(lambda l: 255 if l < 40 else 0).convert("L")
        # Slight blur to feather the mask edges where text meets photo region
        dark_mask = dark_mask.filter(ImageFilter.GaussianBlur(radius=2))

        photo_layer.putalpha(dark_mask)
        slide = Image.alpha_composite(slide, photo_layer)

        # Apply light dark overlay for tonal consistency (subtle, doesn't kill photo)
        vignette = _vignette_overlay(slide.width, slide.height, dark_top=0, dark_bottom=100)
        slide = Image.alpha_composite(slide, vignette)
        slide.convert("RGB").save(slide_path, "PNG")
        return

    # Resize photo for rectangle / feather modes
    target_w = int(slide.width * size_pct)
    ratio = target_w / photo.width
    target_h = int(photo.height * ratio)
    photo = photo.resize((target_w, target_h), Image.LANCZOS)

    if position == "top":
        x = (slide.width - target_w) // 2
        y = int(slide.height * 0.10)
    elif position == "left":
        x = int(slide.width * 0.08)
        y = (slide.height - target_h) // 2
    elif position == "right":
        x = slide.width - target_w - int(slide.width * 0.08)
        y = (slide.height - target_h) // 2
    else:  # center
        x = (slide.width - target_w) // 2
        y = int(slide.height * 0.18)

    if mode == "feather":
        feather_mask = _feather_mask(target_w, target_h, feather_pct=0.12)
        if opacity < 1.0:
            feather_mask = feather_mask.point(lambda v: int(v * opacity))
        photo.putalpha(feather_mask)

    slide.paste(photo, (x, y), photo)
    slide.convert("RGB").save(slide_path, "PNG")


def copy_brand_assets(output_dir: Path) -> dict[str, str]:
    """Copy canonical Agent OZE brand assets into a campaign output folder."""
    copied: dict[str, str] = {}
    for source, output_filename in BRAND_ASSET_OUTPUT_FILES.items():
        if not source.exists():
            raise FileNotFoundError(f"Missing canonical brand asset: {source}")
        target = output_dir / output_filename
        shutil.copy2(source, target)
        copied[source.name] = str(target)
    return copied


def generate_slide_image(
    client: openai.OpenAI,
    prompt: str,
    size: str = "1024x1536",
    model: str = "gpt-image-2",
) -> bytes:
    """Call OpenAI Images API, return PNG bytes.

    Default model is gpt-image-2 (latest GA as of May 2026 — released 2026-04-21,
    verified empirically via client.models.list()). Fallback options: gpt-image-1.5,
    gpt-image-1, gpt-image-1-mini, gpt-image-2-2026-04-21 (pinned version),
    chatgpt-image-latest (alias).
    """
    response = client.images.generate(
        model=model,
        prompt=prompt,
        size=size,
        n=1,
    )
    image_b64 = response.data[0].b64_json
    return base64.b64decode(image_b64)


def validate_config(config: dict) -> list[str]:
    """Return list of validation warnings (empty = OK)."""
    warnings: list[str] = []

    required_top = ["campaign_id", "typ", "concept", "language", "slides"]
    for key in required_top:
        if key not in config:
            warnings.append(f"missing required key: {key}")

    if config.get("language", "").lower() != "pl":
        warnings.append(f"language is {config.get('language')!r}, expected 'pl'")

    if config.get("typ") not in {"A", "B", "C", "D"}:
        warnings.append(f"typ must be A/B/C/D, got {config.get('typ')!r}")

    banned = {
        "storage",
        "follow-up",
        "followup",
        "retrofit",
        "leady",
        "growth hack",
        "AI assistant",
        "AI 24/7",
        "AI rewolucja",
    }
    for slide in config.get("slides", []):
        copy = slide.get("copy", "").lower()
        for term in banned:
            if term.lower() in copy:
                warnings.append(
                    f"slide {slide.get('n')} copy contains banned anglicyzm: {term!r}"
                )

    slides = config.get("slides", [])
    if not slides:
        warnings.append("no slides defined")
    elif not any(s.get("is_cta") for s in slides):
        warnings.append("no slide marked is_cta=true (last slide should be CTA)")

    return warnings


async def upload_folder_to_drive(
    user_id: str, local_folder: Path, drive_root: str = "Agent-OZE/Marketing"
) -> dict:
    """Upload local folder (PNG + meta.json) to Google Drive `Agent-OZE/Marketing/<folder_name>/`.

    Returns dict: {folder_id, folder_url, uploaded_files: [...]}.
    """
    service = await get_drive_service(user_id)
    if not service:
        raise RuntimeError(
            f"Cannot get Drive service for user_id={user_id}. "
            "Verify OZE_OWNER_USER_ID points to a Supabase user with valid Google OAuth tokens."
        )

    def _sync_upload():
        # Find or create root folder "Agent-OZE", then subfolder "Marketing"
        root_parent = None
        for part in drive_root.split("/"):
            query = (
                f"name = '{part}' and mimeType = 'application/vnd.google-apps.folder' "
                f"and trashed = false"
            )
            if root_parent:
                query += f" and '{root_parent}' in parents"
            else:
                query += " and 'root' in parents"
            results = service.files().list(q=query, fields="files(id, name)").execute()
            existing = results.get("files", [])
            if existing:
                root_parent = existing[0]["id"]
            else:
                metadata = {
                    "name": part,
                    "mimeType": "application/vnd.google-apps.folder",
                }
                if root_parent:
                    metadata["parents"] = [root_parent]
                created = service.files().create(body=metadata, fields="id").execute()
                root_parent = created["id"]

        campaign_name = local_folder.name
        existing_q = (
            f"name = '{campaign_name}' and mimeType = 'application/vnd.google-apps.folder' "
            f"and '{root_parent}' in parents and trashed = false"
        )
        existing = service.files().list(q=existing_q, fields="files(id)").execute().get("files", [])
        if existing:
            campaign_folder_id = existing[0]["id"]
        else:
            campaign_metadata = {
                "name": campaign_name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [root_parent],
            }
            campaign_folder = service.files().create(
                body=campaign_metadata, fields="id"
            ).execute()
            campaign_folder_id = campaign_folder["id"]

        uploaded = []
        for file_path in sorted(local_folder.iterdir()):
            if file_path.is_dir():
                continue
            mime = "image/png" if file_path.suffix.lower() == ".png" else "application/json"
            media = MediaIoBaseUpload(
                io.FileIO(str(file_path), "rb"), mimetype=mime, resumable=False
            )
            file_metadata = {"name": file_path.name, "parents": [campaign_folder_id]}
            created_file = service.files().create(
                body=file_metadata, media_body=media, fields="id, name, webViewLink"
            ).execute()
            uploaded.append(
                {
                    "name": created_file["name"],
                    "id": created_file["id"],
                    "url": created_file.get("webViewLink"),
                }
            )

        folder_url = f"https://drive.google.com/drive/folders/{campaign_folder_id}"
        return {
            "folder_id": campaign_folder_id,
            "folder_url": folder_url,
            "uploaded_files": uploaded,
        }

    return await asyncio.to_thread(_sync_upload)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Agent-OZE marketing carousel")
    parser.add_argument("--config", required=True, help="Path to carousel config JSON")
    parser.add_argument(
        "--output-dir",
        default=str(Path.home() / "marketing-output"),
        help="Local output dir (default: ~/marketing-output)",
    )
    parser.add_argument(
        "--owner-user-id",
        default=None,
        help=(
            "Supabase users.id UUID whose Google Drive receives the uploaded "
            "carousel folder. Overrides OZE_OWNER_USER_ID env var. "
            "Recommended default: ada45bc3-4e05-4e64-9f0d-2d98e138debd "
            "(admin@agent-oze.pl)."
        ),
    )
    parser.add_argument(
        "--skip-drive",
        action="store_true",
        help="Skip Drive upload even if --owner-user-id or OZE_OWNER_USER_ID is set",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate config + print prompts without calling OpenAI/Drive",
    )
    parser.add_argument(
        "--model",
        default="gpt-image-2",
        help="OpenAI Images model. Default: gpt-image-2 (latest GA, May 2026). "
        "Alternatives: gpt-image-1, gpt-image-1-mini, dall-e-3.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )

    config_path = Path(args.config).expanduser()
    if not config_path.exists():
        logger.error("Config not found: %s", config_path)
        return 1

    config = json.loads(config_path.read_text(encoding="utf-8"))

    warnings = validate_config(config)
    if warnings:
        logger.warning("Config validation warnings:")
        for w in warnings:
            logger.warning("  - %s", w)
        if any("missing required key" in w or "no slides defined" in w for w in warnings):
            logger.error("Fatal validation errors — aborting.")
            return 2

    campaign_id = config["campaign_id"]
    output_dir = Path(args.output_dir).expanduser() / campaign_id
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Output dir: %s", output_dir)

    if args.dry_run:
        missing_assets = [
            str(path) for path in BRAND_ASSET_OUTPUT_FILES if not path.exists()
        ]
        if missing_assets:
            logger.error(
                "Missing canonical brand assets: %s", ", ".join(missing_assets)
            )
            return 6
        logger.info("Canonical brand assets:")
        for source, output_filename in BRAND_ASSET_OUTPUT_FILES.items():
            logger.info("  %s -> %s", source, output_filename)
        logger.info(
            "=== DRY RUN — printing prompts for %d slides ===", len(config["slides"])
        )
        for slide in config["slides"]:
            logger.info("--- Slide %s ---", slide.get("n"))
            logger.info("Copy: %s", slide.get("copy"))
            logger.info(
                "Full prompt:\n%s\n",
                build_full_prompt(slide.get("visual_prompt", "")),
            )
        logger.info("Dry run complete.")
        return 0

    api_key = (
        Config.OPENAI_API_KEY
        if hasattr(Config, "OPENAI_API_KEY")
        else os.environ.get("OPENAI_API_KEY")
    )
    if not api_key:
        logger.error("OPENAI_API_KEY not set in Config or env")
        return 3

    client = openai.OpenAI(api_key=api_key)
    size = config.get("aspect_ratio", "1024x1536")
    brand_assets = copy_brand_assets(output_dir)
    logger.info("Copied %d brand assets into output dir", len(brand_assets))

    generated_files = []
    for slide in config["slides"]:
        n = slide.get("n")
        visual_prompt = slide.get("visual_prompt", "")
        if not visual_prompt:
            logger.warning("Slide %s has no visual_prompt — skipping", n)
            continue

        full_prompt = build_full_prompt(visual_prompt)
        logger.info(
            "Generating slide %s (model=%s, size=%s)...", n, args.model, size
        )
        try:
            png_bytes = generate_slide_image(
                client, full_prompt, size=size, model=args.model
            )
        except Exception as exc:
            logger.exception("Failed to generate slide %s: %s", n, exc)
            return 4

        slide_filename = (
            f"slide_{n:02d}.png" if isinstance(n, int) else f"slide_{n}.png"
        )
        slide_path = output_dir / slide_filename
        slide_path.write_bytes(png_bytes)
        logger.info(
            "  saved: %s (%.1f KB)", slide_path, slide_path.stat().st_size / 1024
        )

        photo_overlay = slide.get("photo_overlay")
        if photo_overlay and photo_overlay.get("url"):
            variants = photo_overlay.get("variants")
            try:
                if variants:
                    # Multi-variant mode: copy generated base slide into N variants,
                    # apply different photo modes to each. Original slide_NN.png removed.
                    for variant in variants:
                        variant_suffix = variant.get("suffix") or variant["mode"]
                        variant_filename = (
                            f"slide_{n:02d}_{variant_suffix}.png"
                            if isinstance(n, int)
                            else f"slide_{n}_{variant_suffix}.png"
                        )
                        variant_path = output_dir / variant_filename
                        shutil.copy2(slide_path, variant_path)
                        apply_photo_overlay(
                            variant_path,
                            photo_url=photo_overlay["url"],
                            position=variant.get(
                                "position", photo_overlay.get("position", "center")
                            ),
                            size_pct=variant.get(
                                "size_pct", photo_overlay.get("size_pct", 0.45)
                            ),
                            mode=variant["mode"],
                            opacity=variant.get(
                                "opacity", photo_overlay.get("opacity", 1.0)
                            ),
                        )
                        logger.info(
                            "  photo variant applied (mode=%s): %s -> %s",
                            variant["mode"],
                            photo_overlay["url"],
                            variant_filename,
                        )
                    slide_path.unlink()  # remove base (no-photo) slide
                    logger.info("  removed base slide (variants supersede)")
                else:
                    apply_photo_overlay(
                        slide_path,
                        photo_url=photo_overlay["url"],
                        position=photo_overlay.get("position", "center"),
                        size_pct=photo_overlay.get("size_pct", 0.45),
                        mode=photo_overlay.get("mode", "rectangle"),
                        opacity=photo_overlay.get("opacity", 1.0),
                    )
                    logger.info(
                        "  photo overlay applied (mode=%s): %s (%s)",
                        photo_overlay.get("mode", "rectangle"),
                        photo_overlay["url"],
                        photo_overlay.get("attribution", "no attribution"),
                    )
            except Exception as exc:
                logger.exception("Photo overlay failed for slide %s: %s", n, exc)

        generated_files.append(str(slide_path))

    meta = {
        "campaign_id": campaign_id,
        "typ": config["typ"],
        "concept": config["concept"],
        "concept_title": config.get("concept_title"),
        "psychology_principle": config.get("psychology_principle"),
        "source_scenarios": config.get("source_scenarios"),
        "caption_template": config.get("caption_template"),
        "brand_kit_version": config.get("brand_kit_version", "v0"),
        "language": config.get("language", "pl"),
        "aspect_ratio": size,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "model": args.model,
        "brand_assets": {
            "canonical_dir": str(BRAND_ASSET_DIR),
            "icon": {
                "source": str(BRAND_ICON_PATH),
                "file": BRAND_ASSET_OUTPUT_FILES[BRAND_ICON_PATH],
            },
            "logo": {
                "source": str(BRAND_LOGO_PATH),
                "file": BRAND_ASSET_OUTPUT_FILES[BRAND_LOGO_PATH],
            },
            "rule": "Use these files; do not regenerate or invent the Agent OZE logo.",
        },
        "slides": [
            {
                "n": s.get("n"),
                "copy": s.get("copy"),
                "visual_prompt": s.get("visual_prompt"),
                "is_cta": s.get("is_cta", False),
                "file": f"slide_{s.get('n'):02d}.png" if isinstance(s.get("n"), int) else f"slide_{s.get('n')}.png",
            }
            for s in config["slides"]
        ],
        "subjective_perf": None,
    }
    meta_path = output_dir / "meta.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Saved meta: %s", meta_path)

    # Resolve Drive owner: CLI flag > env var. Fail loudly if neither is set
    # unless --skip-drive is in effect (then we just keep local files).
    drive_user = args.owner_user_id or os.environ.get("OZE_OWNER_USER_ID")
    drive_user_source = (
        "--owner-user-id" if args.owner_user_id else
        ("OZE_OWNER_USER_ID env" if drive_user else None)
    )

    if args.skip_drive:
        logger.info("--skip-drive flag set — local files at: %s", output_dir)
    elif not drive_user:
        logger.error(
            "No Drive owner provided: neither --owner-user-id nor "
            "OZE_OWNER_USER_ID env var is set. Pass --owner-user-id "
            "ada45bc3-4e05-4e64-9f0d-2d98e138debd (admin@agent-oze.pl), set "
            "OZE_OWNER_USER_ID, or pass --skip-drive to keep files local only. "
            "Local files at: %s",
            output_dir,
        )
        return 7
    else:
        logger.info(
            "Uploading to Google Drive (user_id=%s, source=%s)...",
            drive_user[:8] + "...",
            drive_user_source,
        )
        try:
            result = asyncio.run(upload_folder_to_drive(drive_user, output_dir))
            logger.info("Drive folder: %s", result["folder_url"])
            logger.info("Uploaded %d files to Drive", len(result["uploaded_files"]))
            drive_meta_path = output_dir / "drive.json"
            drive_meta_path.write_text(
                json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception as exc:
            logger.exception("Drive upload failed: %s", exc)
            logger.info("Local files still available at: %s", output_dir)
            return 5

    print()
    print(f"✓ Campaign {campaign_id} generated: {len(generated_files)} slides")
    print(f"  Local: {output_dir}")
    if drive_user and not args.skip_drive:
        print(
            f"  Drive: see {output_dir / 'drive.json'} for folder URL "
            f"(owner={drive_user[:8]}..., source={drive_user_source})"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
