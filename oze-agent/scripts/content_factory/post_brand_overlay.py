#!/usr/bin/env python3
"""Agent OZE branded overlay — BOTTOM CENTER pill "@agentoze [icon]".

Migrated 2026-05-24 from /tmp/post_brand_overlay_v2.py with v4 forward constants
locked in by Maan after 3 iterations:

- v1 (icon LEFT, white handle, large) → REJECTED
- v2 (icon RIGHT, green handle, larger) → "logo blizej, mniejsze, dyskretniej"
- v3 (icon RIGHT, green handle, smaller, lower pill) → APPROVED for current files
- v4 forward default (bottom 3.2% margin, "troche wyzej" than v3) → THIS

See memory: feedback-brand-placement-bottom-center-agentoze for full iteration
history and rationale. Constants below MUST NOT drift back to earlier values
without explicit Maan approval.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[3]
BRAND_ICON_PATH = REPO_ROOT / "assets" / "brand" / "agent-oze-icon.png"

# macOS Arial Bold; tested at 30px renders @agentoze cleanly. Fallback to default
# load_default() if Arial absent (e.g. Railway container — needs ttf installed).
FONT_SANS_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

# v4 forward constants (locked-in 2026-05-24)
ICON_PX = 52
HANDLE = "@agentoze"
HANDLE_FONT_PX = 30
HANDLE_COLOR = (61, 255, 122, 255)  # #3DFF7A — Agent OZE neon green
GAP_PX = 8
BOTTOM_MARGIN_PCT = 0.032  # "troche wyzej" than 0.022 (v3)
PAD_X = 22
PAD_Y = 10
BACKDROP_ALPHA = 110


def composite_brand(slide_path: Path) -> None:
    """Composite @agentoze pill bottom-center onto an existing slide PNG, in place."""
    img = Image.open(slide_path).convert("RGB")
    W, H = img.size

    icon = Image.open(BRAND_ICON_PATH).convert("RGBA")
    ratio = ICON_PX / icon.width
    icon = icon.resize((ICON_PX, int(icon.height * ratio)), Image.LANCZOS)

    try:
        font = ImageFont.truetype(FONT_SANS_BOLD, HANDLE_FONT_PX)
    except OSError:
        font = ImageFont.load_default()
    bbox = font.getbbox(HANDLE)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    content_w = ICON_PX + GAP_PX + tw
    content_h = max(ICON_PX, th)
    backdrop_w = content_w + PAD_X * 2
    backdrop_h = content_h + PAD_Y * 2

    bx = (W - backdrop_w) // 2
    by = H - backdrop_h - int(H * BOTTOM_MARGIN_PCT)

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    backdrop = Image.new("RGBA", (backdrop_w + 12, backdrop_h + 12), (0, 0, 0, 0))
    bd_draw = ImageDraw.Draw(backdrop)
    bd_draw.rounded_rectangle(
        [6, 6, backdrop_w + 6, backdrop_h + 6],
        radius=backdrop_h // 2,
        fill=(5, 6, 7, BACKDROP_ALPHA),
    )
    backdrop = backdrop.filter(ImageFilter.GaussianBlur(radius=2))
    overlay.paste(backdrop, (bx - 6, by - 6), backdrop)

    draw = ImageDraw.Draw(overlay)
    text_x = bx + PAD_X
    text_y = by + (backdrop_h - th) // 2 - bbox[1]
    draw.text((text_x + 1, text_y + 1), HANDLE, font=font, fill=(0, 0, 0, 200))
    draw.text((text_x, text_y), HANDLE, font=font, fill=HANDLE_COLOR)

    icon_x = text_x + tw + GAP_PX
    icon_y = by + (backdrop_h - icon.height) // 2
    overlay.paste(icon, (icon_x, icon_y), icon)

    final = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    final.save(slide_path, "PNG", quality=95)


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply @agentoze brand pill to a slide.")
    parser.add_argument("--slide", required=True, help="Path to slide PNG (modified in place).")
    args = parser.parse_args()
    composite_brand(Path(args.slide))
    print(f"branded overlay applied → {args.slide}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
