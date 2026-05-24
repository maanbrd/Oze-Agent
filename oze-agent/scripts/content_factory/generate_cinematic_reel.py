#!/usr/bin/env python3
"""Cinematic Type G/E reel generator for Agent OZE.

Generates 1 photo (1080x1350, 4:5 IG portrait) via OpenAI gpt-image-2,
then composites text overlay + subtle Agent OZE logo via Pillow.
Built specifically for milionerwifi-style relatable cinematic content
that requires people/faces — bypasses the no-people BRAND_LOCK_PREFIX
in the standard generate_carousel.py.

Usage:
    python3 /tmp/generate_cinematic_reel.py \
        --config /tmp/2026-05-23-typ-g-dyscyplina.json \
        --output-dir /Users/mansoniasty/marketing-output

Config schema (JSON):
{
  "campaign_id": "2026-05-23-typ-g-dyscyplina",
  "typ": "G",                  # G=static cinematic, E=split-screen
  "concept": "...",
  "language": "pl",
  "visual_prompt": "<full prompt for gpt-image-2 — generates background photo WITHOUT text>",
  "overlay": {
    "text": "„Sprzedaż to nie talent. To dyscyplina.”",
    "position": "bottom_third",   # bottom_third | corners (for split-screen E)
    "left_text": "7:00",          # only for split-screen layouts
    "right_text": "21:00"         # only for split-screen layouts
  },
  "caption": "...",
  "hashtags": ["#handlowiec", "..."]
}
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

import openai
from PIL import Image, ImageDraw, ImageFilter, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[3]
BRAND_LOGO_PATH = REPO_ROOT / "assets" / "brand" / "agent-oze-logo.png"
BRAND_ICON_PATH = REPO_ROOT / "assets" / "brand" / "agent-oze-icon.png"

# Canonical brand pill (bottom-center @agentoze). composite_logo() below is
# kept as legacy helper but no longer wired into the main() flow.
from scripts.content_factory.post_brand_overlay import composite_brand

# Final output dimensions (4:5 Instagram portrait)
FINAL_W = 1080
FINAL_H = 1350

# gpt-image-2 supports 1024x1536 portrait; we'll scale/crop to 1080x1350
GEN_SIZE = "1024x1536"

# Font paths (macOS)
FONT_SERIF_BOLD = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"
FONT_SERIF_BOLD_ITALIC = "/System/Library/Fonts/Supplemental/Georgia Bold Italic.ttf"
FONT_SANS = "/System/Library/Fonts/Helvetica.ttc"


def generate_photo(client: openai.OpenAI, prompt: str) -> bytes:
    """Generate cinematic photo via gpt-image-2."""
    resp = client.images.generate(
        model="gpt-image-2",
        prompt=prompt,
        size=GEN_SIZE,
        n=1,
    )
    return base64.b64decode(resp.data[0].b64_json)


def fit_to_4x5(img: Image.Image) -> Image.Image:
    """Crop/scale image to exactly 1080x1350 (4:5)."""
    src_w, src_h = img.size
    target_ratio = FINAL_W / FINAL_H
    src_ratio = src_w / src_h

    if src_ratio > target_ratio:
        # Source wider — crop sides
        new_w = int(src_h * target_ratio)
        offset = (src_w - new_w) // 2
        img = img.crop((offset, 0, offset + new_w, src_h))
    else:
        # Source taller — crop top/bottom
        new_h = int(src_w / target_ratio)
        offset = (src_h - new_h) // 2
        img = img.crop((0, offset, src_w, offset + new_h))

    return img.resize((FINAL_W, FINAL_H), Image.LANCZOS)


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """Word-wrap text to fit max_width."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = font.getbbox(test)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_text_shadow(
    draw: ImageDraw.ImageDraw,
    pos: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill=(255, 255, 255),
    shadow_offset=3,
    shadow_color=(0, 0, 0, 200),
) -> None:
    """Draw text with subtle drop shadow for legibility on photo backgrounds."""
    x, y = pos
    # Shadow
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=shadow_color)
    # Main text
    draw.text((x, y), text, font=font, fill=fill)


def apply_bottom_third_gradient(img: Image.Image) -> Image.Image:
    """Darken bottom 1/3 with vertical gradient for text legibility."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gradient_start_y = int(img.height * 0.55)  # gradient starts here
    for y in range(gradient_start_y, img.height):
        # 0 alpha at start, 180 alpha at bottom
        t = (y - gradient_start_y) / (img.height - gradient_start_y)
        alpha = int(180 * t)
        for_row = Image.new("RGBA", (img.width, 1), (0, 0, 0, alpha))
        overlay.paste(for_row, (0, y))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def apply_split_corner_shadow(img: Image.Image) -> Image.Image:
    """Subtle dark vignettes in all four corners for split-screen corner text."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    # Top vignette
    for y in range(0, int(img.height * 0.15)):
        t = 1.0 - (y / int(img.height * 0.15))
        alpha = int(140 * t)
        for_row = Image.new("RGBA", (img.width, 1), (0, 0, 0, alpha))
        overlay.paste(for_row, (0, y))
    # Bottom vignette
    grad_start = int(img.height * 0.85)
    for y in range(grad_start, img.height):
        t = (y - grad_start) / (img.height - grad_start)
        alpha = int(140 * t)
        for_row = Image.new("RGBA", (img.width, 1), (0, 0, 0, alpha))
        overlay.paste(for_row, (0, y))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def composite_logo(
    img: Image.Image, logo_path: Path, position: str = "bottom_right", width_pct: float = 0.08
) -> Image.Image:
    """Composite subtle Agent OZE logo onto image."""
    logo = Image.open(logo_path).convert("RGBA")
    target_w = int(img.width * width_pct)
    ratio = target_w / logo.width
    target_h = int(logo.height * ratio)
    logo = logo.resize((target_w, target_h), Image.LANCZOS)

    # Apply slight opacity (90% — keep it readable but subtle)
    alpha = logo.split()[-1]
    alpha = alpha.point(lambda v: int(v * 0.85))
    logo.putalpha(alpha)

    margin = int(img.width * 0.025)
    if position == "bottom_right":
        x = img.width - target_w - margin
        y = img.height - target_h - margin
    elif position == "bottom_center":
        x = (img.width - target_w) // 2
        y = img.height - target_h - margin
    else:
        x = margin
        y = img.height - target_h - margin

    base = img.convert("RGBA")
    base.paste(logo, (x, y), logo)
    return base.convert("RGB")


def render_static_overlay(img: Image.Image, overlay_cfg: dict) -> Image.Image:
    """Render Type G overlay: quote text in bottom third, white serif with shadow."""
    img = apply_bottom_third_gradient(img)
    draw = ImageDraw.Draw(img)

    text = overlay_cfg["text"]
    max_text_width = int(img.width * 0.86)

    # Try font sizes from large to smaller until text fits in ~3 lines
    for font_size in (66, 62, 58, 54, 50, 46):
        font = ImageFont.truetype(FONT_SERIF_BOLD_ITALIC, font_size)
        lines = wrap_text(text, font, max_text_width)
        if len(lines) <= 3:
            break

    line_height = int(font_size * 1.18)
    total_h = line_height * len(lines)
    # Start text near bottom — bottom of last line at ~88% of image height
    start_y = int(img.height * 0.88) - total_h

    for i, line in enumerate(lines):
        bbox = font.getbbox(line)
        line_w = bbox[2] - bbox[0]
        x = (img.width - line_w) // 2
        y = start_y + i * line_height
        draw_text_shadow(draw, (x, y), line, font, fill=(245, 245, 245), shadow_offset=3)

    return img


def render_split_corners(img: Image.Image, overlay_cfg: dict) -> Image.Image:
    """Render Type E split-screen overlay: large time labels in top corners."""
    img = apply_split_corner_shadow(img)
    draw = ImageDraw.Draw(img)

    left_text = overlay_cfg.get("left_text", "")
    right_text = overlay_cfg.get("right_text", "")

    font = ImageFont.truetype(FONT_SERIF_BOLD, 96)
    margin = int(img.width * 0.055)
    top_y = int(img.height * 0.045)

    # Left top
    if left_text:
        draw_text_shadow(
            draw, (margin, top_y), left_text, font, fill=(245, 245, 245), shadow_offset=4
        )
    # Right top
    if right_text:
        bbox = font.getbbox(right_text)
        right_w = bbox[2] - bbox[0]
        x = img.width - right_w - margin
        draw_text_shadow(
            draw, (x, top_y), right_text, font, fill=(245, 245, 245), shadow_offset=4
        )

    return img


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", default=str(Path.home() / "marketing-output"))
    parser.add_argument("--dry-run", action="store_true", help="Skip OpenAI call")
    args = parser.parse_args()

    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    campaign_id = config["campaign_id"]
    out_dir = Path(args.output_dir).expanduser() / campaign_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # Copy brand assets
    shutil.copy2(BRAND_LOGO_PATH, out_dir / "brand_agent_oze_logo.png")
    shutil.copy2(BRAND_ICON_PATH, out_dir / "brand_agent_oze_icon.png")

    visual_prompt = config["visual_prompt"]
    overlay_cfg = config["overlay"]
    layout = overlay_cfg.get("layout", "static")  # static | split_corners

    if args.dry_run:
        print(f"[dry-run] Campaign: {campaign_id}")
        print(f"[dry-run] Visual prompt:\n{visual_prompt}\n")
        print(f"[dry-run] Overlay: {overlay_cfg}")
        return 0

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set", file=sys.stderr)
        return 2

    client = openai.OpenAI(api_key=api_key)
    print(f"Generating photo via gpt-image-2 ({GEN_SIZE})...")
    png_bytes = generate_photo(client, visual_prompt)

    raw_path = out_dir / "raw_photo.png"
    raw_path.write_bytes(png_bytes)
    print(f"  saved raw: {raw_path} ({len(png_bytes)/1024:.1f} KB)")

    img = Image.open(io.BytesIO(png_bytes))
    img = fit_to_4x5(img)

    # Render overlay (quote text only — brand pill is added next via composite_brand)
    if layout == "split_corners":
        img = render_split_corners(img, overlay_cfg)
    else:
        img = render_static_overlay(img, overlay_cfg)

    slide_path = out_dir / "slide_01.png"
    img.save(slide_path, "PNG", quality=95)

    # Brand pill (bottom-center @agentoze) — canonical placement per memory
    composite_brand(slide_path)
    print(f"  saved final: {slide_path}")

    # Write meta.json
    meta = {
        "campaign_id": campaign_id,
        "typ": config["typ"],
        "concept": config["concept"],
        "language": config.get("language", "pl"),
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "model": "gpt-image-2",
        "aspect_ratio": f"{FINAL_W}x{FINAL_H}",
        "layout": layout,
        "visual_prompt": visual_prompt,
        "overlay": overlay_cfg,
        "caption": config.get("caption"),
        "hashtags": config.get("hashtags", []),
        "audio_track": config.get("audio_track"),
        "slides": [{"n": 1, "file": "slide_01.png"}],
    }
    (out_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"\nDone. Output: {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
