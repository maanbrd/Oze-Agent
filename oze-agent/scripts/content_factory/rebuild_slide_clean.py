#!/usr/bin/env python3
"""Rebuild slide_01.png from raw_photo.png — used after brand layout changes.

Re-applies:
1. fit_to_4x5 (1080x1350)
2. text overlay (from meta.json overlay config)
3. canonical @agentoze brand pill (bottom-center)

Skips gpt-image-2 call — uses cached raw_photo.png. Useful for re-iterating
brand placement / quote text without burning OpenAI credits.

Usage:
    python -m scripts.content_factory.rebuild_slide_clean \\
        --folder ~/marketing-output/2026-05-23-typ-g-dyscyplina
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image

from scripts.content_factory.generate_cinematic_reel import (
    fit_to_4x5, render_split_corners, render_static_overlay,
)
from scripts.content_factory.post_brand_overlay import composite_brand


def rebuild(folder: Path) -> None:
    raw_path = folder / "raw_photo.png"
    slide_path = folder / "slide_01.png"
    meta_path = folder / "meta.json"

    if not raw_path.is_file():
        raise SystemExit(f"missing raw_photo.png in {folder}")
    if not meta_path.is_file():
        raise SystemExit(f"missing meta.json in {folder}")

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    overlay_cfg = meta["overlay"]
    layout = overlay_cfg.get("layout", "static")

    img = Image.open(raw_path)
    img = fit_to_4x5(img)

    if layout == "split_corners":
        img = render_split_corners(img, overlay_cfg)
    else:
        img = render_static_overlay(img, overlay_cfg)

    img.save(slide_path, "PNG", quality=95)
    composite_brand(slide_path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", required=True)
    args = parser.parse_args()
    rebuild(Path(args.folder).expanduser())
    print(f"rebuilt clean slide → {Path(args.folder) / 'slide_01.png'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
