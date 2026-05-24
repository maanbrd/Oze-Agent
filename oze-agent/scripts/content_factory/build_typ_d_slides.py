#!/usr/bin/env python3
"""Build typ-D-AGENT single image post from landing-page card screenshot.

Workflow:
1. Capture mobile-viewport screenshot of agent-oze.pl scenario card (01/02/03/04)
   via puppeteer (or reuse cached /tmp/landing-shots/card_NN.png if present
   and fresh — bypass puppeteer for fast re-builds).
2. Compose source card onto 1080x1350 #0b0d10 canvas (center, leaving bottom
   170px for brand pill).
3. Apply post_brand_overlay.composite_brand (canonical @agentoze bottom-center).
4. Build 7s preview.mp4 (looped slide + audio).
5. Write meta.json + instagram_post.json manifests.

Usage (single scenario):
    python -m scripts.content_factory.build_typ_d_slides --scenario 1

Usage (specific output dir):
    python -m scripts.content_factory.build_typ_d_slides \\
        --scenario 1 \\
        --output-dir ~/marketing-output \\
        --skip-capture   # use cached /tmp/landing-shots/card_01.png

Scenario numbering matches landing-page canonical 01/02/03/04. Picks date stamp
from today (Warsaw). Returns 0 on success, exit code 2 on errors.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image

from scripts.content_factory.post_brand_overlay import composite_brand

REPO_ROOT = Path(__file__).resolve().parents[3]
SHOTS = Path("/tmp/landing-shots")
DEFAULT_OUT_ROOT = Path.home() / "marketing-output"
AUDIO = Path("/tmp/milionerwifi/reel_audio.mp3")
WARSAW = ZoneInfo("Europe/Warsaw")

FINAL_W = 1080
FINAL_H = 1350
BG_COLOR = (11, 13, 16)  # #0b0d10
TARGET_CARD_H = 1180     # leaves 170px bottom strip for brand pill
TOP_MARGIN = 30

PUP_RUNNER = Path("/tmp/pup-runner")
PUP_CAPTURE_SCRIPT = PUP_RUNNER / "capture_mobile_cards.mjs"

SCENARIOS = {
    "01": {
        "slug": "glosowka-po-spotkaniu",
        "headline": "18:40 wsiadasz do auta po trzecim spotkaniu",
        "caption": (
            "18:40. Wsiadasz do auta po trzecim spotkaniu.\n\n"
            "Nagrywasz głosówkę: „Jan Kowalski, Warszawa, dom 160m², dach 40m² południe, "
            "zainteresowany ofertą, follow-up sobota.\"\n\n"
            "Agent zamienia to w kartę klienta. Klikasz „Zapisać\". "
            "Klient w arkuszu, follow-up w kalendarzu. Koniec dnia roboczego.\n\n"
            "@agentoze pamięta każde spotkanie za Ciebie — żebyś mógł skupić się na sprzedaży."
        ),
        "hashtags": ["#handlowiec", "#sprzedaż", "#OZE", "#fotowoltaika", "#agentoze"],
    },
    "02": {
        "slug": "poranny-brief",
        "headline": "7:00 poranna kawa w kuchni",
        "caption": (
            "7:00. Poranna kawa w kuchni.\n\n"
            "Telegram pinguje: „Dziś masz 4 spotkania. 9:30 Kowalski, 11:00 Nowak, "
            "14:00 Wiśniewski, 16:30 Lewandowski.\"\n\n"
            "Otwierasz dzień bez szukania w kalendarzu. Wiesz dokąd jechać, "
            "kogo zadzwonić, co zabrać.\n\n"
            "@agentoze planuje dzień za Ciebie — żebyś poranne minuty spędził w spokoju, "
            "nie szukając kalendarza."
        ),
        "hashtags": ["#handlowiec", "#sprzedaż", "#OZE", "#dyscyplina", "#agentoze"],
    },
    "03": {
        "slug": "zdjecia-dachu",
        "headline": "Po wizycie u klienta",
        "caption": (
            "Wracasz z wizyty. Masz 8 zdjęć dachu w telefonie.\n\n"
            "Wysyłasz je do Telegrama. Agent: „Do którego klienta? Kowalski, Nowak, czy Wiśniewski?\"\n"
            "Klikasz nazwisko. Zdjęcia lądują w folderze Drive klienta, link w arkuszu.\n\n"
            "Bez segregowania, bez nazewnictwa plików, bez „gdzie ja to zapisałem\".\n\n"
            "@agentoze segreguje za Ciebie — żebyś nie tracił 30 min wieczorem na porządki w telefonie."
        ),
        "hashtags": ["#handlowiec", "#sprzedaż", "#OZE", "#fotowoltaika", "#agentoze"],
    },
    "04": {
        "slug": "oferta-pdf",
        "headline": "Oferta wychodzi od razu po spotkaniu",
        "caption": (
            "Wsiadasz do auta i nagrywasz głosówkę: „Oferta dla Kowalskiego — moduły 410W, "
            "falownik 8 kW, magazyn 10 kWh, montaż czerwiec.\"\n\n"
            "Agent generuje PDF, pokazuje podgląd. Klikasz „Wysłać\". "
            "Email wychodzi z Twojego Gmail. Klient ma ofertę zanim wróci do domu.\n\n"
            "@agentoze pisze oferty za Ciebie — żebyś nie pisał emaili wieczorem, "
            "tylko w spokoju odpoczął."
        ),
        "hashtags": ["#handlowiec", "#sprzedaż", "#OZE", "#oferta", "#agentoze"],
    },
}


def _normalize_n(raw: str) -> str:
    """Accept '1', '01', 1 → '01'."""
    s = str(raw).strip().zfill(2)
    if s not in SCENARIOS:
        raise SystemExit(f"unknown scenario {raw!r}; must be 01/02/03/04")
    return s


def _capture_card(n: str) -> Path:
    """Run puppeteer to capture card_NN.png. Reuses cached file if present."""
    out = SHOTS / f"card_{n}.png"
    if out.is_file() and out.stat().st_size > 0:
        return out
    if not PUP_CAPTURE_SCRIPT.is_file():
        raise SystemExit(
            f"cached {out} missing and puppeteer script {PUP_CAPTURE_SCRIPT} not "
            "installed. Run capture once manually then retry."
        )
    SHOTS.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["node", str(PUP_CAPTURE_SCRIPT)],
        cwd=str(PUP_RUNNER),
        check=True,
    )
    if not out.is_file():
        raise SystemExit(f"capture finished but {out} still missing")
    return out


def build(scenario_n: str, out_root: Path, *, skip_capture: bool = False) -> Path:
    n = _normalize_n(scenario_n)
    scenario = SCENARIOS[n]
    date_str = datetime.now(WARSAW).strftime("%Y-%m-%d")
    campaign_id = f"{date_str}-typ-d-{n}-{scenario['slug']}"
    out_dir = out_root / campaign_id
    out_dir.mkdir(parents=True, exist_ok=True)

    if skip_capture:
        source = SHOTS / f"card_{n}.png"
        if not source.is_file():
            raise SystemExit(f"--skip-capture but cache missing: {source}")
    else:
        source = _capture_card(n)

    bg = Image.new("RGB", (FINAL_W, FINAL_H), BG_COLOR)
    src = Image.open(source).convert("RGB")
    sw, sh = src.size
    scale = TARGET_CARD_H / sh
    new_w = int(sw * scale)
    src_scaled = src.resize((new_w, TARGET_CARD_H), Image.LANCZOS)
    paste_x = (FINAL_W - new_w) // 2
    bg.paste(src_scaled, (paste_x, TOP_MARGIN))
    slide_path = out_dir / "slide_01.png"
    bg.save(slide_path, "PNG", quality=95)

    composite_brand(slide_path)

    shutil.copy(REPO_ROOT / "assets/brand/agent-oze-icon.png", out_dir / "brand_agent_oze_icon.png")
    shutil.copy(REPO_ROOT / "assets/brand/agent-oze-logo.png", out_dir / "brand_agent_oze_logo.png")
    shutil.copy(source, out_dir / "raw_source.png")

    preview = out_dir / "preview.mp4"
    if AUDIO.is_file():
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", str(slide_path),
            "-ss", "0", "-t", "7", "-i", str(AUDIO),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
            "-vf", f"scale={FINAL_W}:{FINAL_H}:force_original_aspect_ratio=decrease,"
                   f"pad={FINAL_W}:{FINAL_H}:(ow-iw)/2:(oh-ih)/2:color=0x0b0d10",
            "-c:a", "aac", "-b:a", "192k", "-shortest",
            str(preview),
        ]
        subprocess.run(cmd, check=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

    meta = {
        "campaign_id": campaign_id,
        "typ": "D-AGENT",
        "concept": scenario["headline"],
        "scenario_number": n,
        "language": "pl",
        "generated_at": datetime.now(WARSAW).isoformat(),
        "source": "agent-oze.pl landing page (mobile viewport, scenario card crop)",
        "aspect_ratio": f"{FINAL_W}x{FINAL_H}",
        "brand_overlay_version": "v4_forward",
        "audio_track": str(AUDIO),
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    ig_manifest = {
        "campaign_id": campaign_id,
        "format": "single_image_with_audio_reel",
        "typ": "D-AGENT",
        "platform": "both",
        "media": {
            "image": "slide_01.png",
            "video": "preview.mp4",
            "aspect_ratio": "1080x1350",
            "duration_seconds": 7,
            "audio_track_source": str(AUDIO),
        },
        "caption_ig": scenario["caption"],
        "caption_fb": scenario["caption"],
        "hashtags": scenario["hashtags"],
        "scheduled_at": None,
        "notes": "Typ D-AGENT — landing-page scenario card crop. Brand pill v4 bottom-center.",
    }
    (out_dir / "instagram_post.json").write_text(
        json.dumps(ig_manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return out_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a single typ-D-AGENT post from landing.")
    parser.add_argument("--scenario", required=True, help="Scenario number: 1/01/2/02/...")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUT_ROOT))
    parser.add_argument("--skip-capture", action="store_true",
                        help="Reuse cached /tmp/landing-shots/card_NN.png instead of re-running puppeteer")
    args = parser.parse_args()

    out_dir = build(args.scenario, Path(args.output_dir).expanduser(),
                    skip_capture=args.skip_capture)
    print(f"Done. Output: {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
