"""Daily content generator — Phase 0.18 full implementation.

Goal: every morning at 06:00 Warsaw, generate exactly 1 new PENDING row for
Maan to review. Picks type via round-robin C → D-AGENT → G → E, biased by
``uwagi_do_agenta`` directives. Dispatches to the type-specific generator
under ``scripts/content_factory/``, uploads to Drive, pushes the PENDING row
to the marketing_queue Sheet.

MVP type coverage (2026-05-24):
- **D-AGENT**: fully wired. Picks next scenario (01→02→03→04 cyclic) based on
  count of PUBLISHED + APPROVED + PENDING D-AGENT rows.
- **C / G / E**: not wired yet. When rotation lands on them, this script
  logs a skip with explicit hint ("Phase 0.19: wire generator for C/G/E")
  and exits 0 cleanly. Maan generates those types manually until then.

Directive overrides (Maan writes anywhere in col U ``uwagi_do_agenta``):
- ``tylko typ D`` / ``tylko D-AGENT`` → force D-AGENT
- ``tylko typ C`` → force C, etc.
- ``preferuj X`` → bias rotation toward X (additive, not exclusive)

Usage::

    railway run --service bot --environment production .venv/bin/python3 \\
        scripts/marketing/generate_daily.py [--dry-run] [--force-type C|D-AGENT|G|E]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo

from shared.google_drive import get_drive_service
from shared.marketing_sheets import (
    _read_all_rows,
    _row_to_dict,
    get_global_directives,
    push_row,
)

logger = logging.getLogger(__name__)

ADMIN_USER_ID = "ada45bc3-4e05-4e64-9f0d-2d98e138debd"
WARSAW = ZoneInfo("Europe/Warsaw")

TYPES = ["C", "D-AGENT", "G", "E"]
DRIVE_ROOT = "Agent-OZE/Marketing"
MARKETING_OUTPUT_ROOT = Path.home() / "marketing-output"

MIME_BY_EXT = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".mp4": "video/mp4",
    ".json": "application/json",
    ".mp3": "audio/mpeg",
}


# ── type detection from campaign_id ──────────────────────────────────────────
# Examples we need to recognize:
#   2026-05-19-typ-c-pi-cialdini-pomysle           → C
#   2026-05-23-typ-c-carnegie-allcaps-...          → C
#   2026-05-24-typ-d-01-glosowka                   → D-AGENT
#   2026-05-23-typ-g-dyscyplina                    → G
#   2026-05-23-typ-e-7vs21                         → E
_TYPE_RE = re.compile(r"-typ-([a-z])(?:-|$)")


def parse_type_from_campaign_id(cid: str) -> Optional[str]:
    if not cid:
        return None
    m = _TYPE_RE.search(cid.lower())
    if not m:
        return None
    letter = m.group(1).upper()
    if letter == "D":
        return "D-AGENT"
    if letter in {"C", "G", "E"}:
        return letter
    return None


def _parse_scenario_index(cid: str) -> Optional[int]:
    """Extract scenario number from D-AGENT campaign_id like ...-typ-d-01-..."""
    m = re.search(r"-typ-d-(\d{2})-", (cid or "").lower())
    return int(m.group(1)) if m else None


def pick_next_type(recent_rows: list[dict], directives: list[str]) -> str:
    """Round-robin: pick the type LEAST-published in last N rows. Directives
    can force or bias the choice."""
    text = " ".join(directives).lower()

    # Hard directive override: "tylko typ X" / "tylko X"
    for t in TYPES:
        if re.search(rf"tylko\s+(typ\s+)?{re.escape(t.lower())}\b", text):
            print(f"generate_daily: directive override → {t}")
            return t

    counts = {t: 0 for t in TYPES}
    for row in recent_rows:
        t = parse_type_from_campaign_id(row.get("campaign_id"))
        if t:
            counts[t] = counts.get(t, 0) + 1

    # Bias toward "preferuj X" directives (count + 0.5 reverse — picked first on ties)
    bias = {t: 0 for t in TYPES}
    for t in TYPES:
        if re.search(rf"preferuj\s+(typ\s+)?{re.escape(t.lower())}\b", text):
            bias[t] = -1  # negative count = picked first on tie

    return min(TYPES, key=lambda t: (counts[t] + bias[t], TYPES.index(t)))


def pick_next_d_scenario(all_rows_dicts: list[dict]) -> str:
    """Round-robin D-AGENT scenario: pick 01/02/03/04 the least-used so far."""
    counts = {n: 0 for n in ("01", "02", "03", "04")}
    for r in all_rows_dicts:
        t = parse_type_from_campaign_id(r.get("campaign_id"))
        if t != "D-AGENT":
            continue
        n = _parse_scenario_index(r.get("campaign_id", ""))
        if n is not None:
            key = f"{n:02d}"
            counts[key] = counts.get(key, 0) + 1
    return min(counts, key=lambda k: (counts[k], int(k)))


# ── Drive upload helpers ─────────────────────────────────────────────────────

def _upload_folder_sync(service, local_folder: Path) -> dict:
    """Mirror of /tmp/upload_4_typ_d_to_drive.py logic, inline here to avoid
    spinning up an extra subprocess for a 5-file folder."""
    # Resolve / create DRIVE_ROOT path chain.
    root_parent = None
    for part in DRIVE_ROOT.split("/"):
        q = (
            f"name = '{part}' and mimeType = 'application/vnd.google-apps.folder' "
            f"and trashed = false"
        )
        q += f" and '{root_parent}' in parents" if root_parent else " and 'root' in parents"
        results = service.files().list(q=q, fields="files(id)").execute()
        existing = results.get("files", [])
        if existing:
            root_parent = existing[0]["id"]
        else:
            md = {"name": part, "mimeType": "application/vnd.google-apps.folder"}
            if root_parent:
                md["parents"] = [root_parent]
            created = service.files().create(body=md, fields="id").execute()
            root_parent = created["id"]

    campaign_name = local_folder.name
    eq = (
        f"name = '{campaign_name}' and mimeType = 'application/vnd.google-apps.folder' "
        f"and '{root_parent}' in parents and trashed = false"
    )
    existing = service.files().list(q=eq, fields="files(id)").execute().get("files", [])
    if existing:
        campaign_folder_id = existing[0]["id"]
    else:
        md = {
            "name": campaign_name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [root_parent],
        }
        campaign_folder_id = service.files().create(body=md, fields="id").execute()["id"]

    from googleapiclient.http import MediaIoBaseUpload
    import io

    uploaded = []
    for file_path in sorted(local_folder.iterdir()):
        if file_path.is_dir():
            continue
        ext = file_path.suffix.lower()
        mime = MIME_BY_EXT.get(ext, "application/octet-stream")
        media = MediaIoBaseUpload(io.FileIO(str(file_path), "rb"), mimetype=mime, resumable=False)
        md = {"name": file_path.name, "parents": [campaign_folder_id]}
        created = service.files().create(
            body=md, media_body=media, fields="id, name, webViewLink"
        ).execute()
        uploaded.append({
            "name": created["name"],
            "id": created["id"],
            "url": created.get("webViewLink"),
        })

    return {
        "folder_id": campaign_folder_id,
        "folder_url": f"https://drive.google.com/drive/folders/{campaign_folder_id}",
        "uploaded_files": uploaded,
    }


async def upload_campaign_to_drive(local_folder: Path) -> dict:
    service = await get_drive_service(ADMIN_USER_ID)
    if not service:
        raise RuntimeError(f"could not get Drive service for {ADMIN_USER_ID}")
    result = await asyncio.to_thread(_upload_folder_sync, service, local_folder)
    (local_folder / "drive.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return result


# ── Type dispatchers ─────────────────────────────────────────────────────────

def dispatch_d_agent(scenario_n: str, dry_run: bool) -> Optional[Path]:
    """Run build_typ_d_slides --scenario <n>. Returns the produced folder."""
    if dry_run:
        print(f"  [dry-run] would dispatch: build_typ_d_slides --scenario {scenario_n}")
        return None
    cmd = [
        sys.executable, "-m",
        "scripts.content_factory.build_typ_d_slides",
        "--scenario", scenario_n,
        "--output-dir", str(MARKETING_OUTPUT_ROOT),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: build_typ_d_slides exit {result.returncode}", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        return None
    # The script prints "Done. Output: <path>" on the last line.
    out_path: Optional[Path] = None
    for line in reversed(result.stdout.strip().splitlines()):
        if line.startswith("Done. Output:"):
            out_path = Path(line.split(":", 1)[1].strip())
            break
    if not out_path or not out_path.is_dir():
        print(f"  ERROR: could not parse output folder from build_typ_d_slides", file=sys.stderr)
        return None
    return out_path


def dispatch_not_wired(type_label: str) -> None:
    """C / G / E: log skip + hint. Phase 0.19 will wire each."""
    print(
        f"generate_daily: type={type_label} not wired in MVP. "
        f"Phase 0.19 will dispatch this. For today, generate manually via the "
        f"appropriate content_factory script and push_row to Sheet."
    )


# ── Main flow ────────────────────────────────────────────────────────────────

async def _run(dry_run: bool, force_type: Optional[str]) -> int:
    print(f"generate_daily: now={datetime.now(WARSAW).isoformat()} (Warsaw)")

    raw_directives = await get_global_directives(ADMIN_USER_ID)
    # Filter out accidentally-stored JSON (legacy/buggy writes from
    # feedback_history into the wrong cell). True directives are free Polish text.
    directives = [d for d in raw_directives if d and not d.lstrip().startswith(("[", "{"))]
    print(
        f"generate_daily: {len(directives)} directive(s) in uwagi_do_agenta "
        f"(filtered {len(raw_directives) - len(directives)} JSON-shaped noise rows)"
    )
    for d in directives:
        print(f"  - {d}")

    _, all_rows = await _read_all_rows(ADMIN_USER_ID)
    all_dicts = [_row_to_dict(r, i) for i, r in enumerate(all_rows[1:], start=2)]
    # Rotation counts use PUBLISHED rows only — APPROVED/PENDING haven't
    # reached followers yet, shouldn't influence next-type pick. Recent = last 14d.
    published = [r for r in all_dicts if r.get("status") == "PUBLISHED"]
    recent = published[-14:]
    # D-scenario rotation needs the full picture (gen=PENDING also counts so
    # we don't double-pick the same scenario in one week).
    relevant_for_scenario = [
        r for r in all_dicts if r.get("status") in {"PUBLISHED", "APPROVED", "PENDING"}
    ]

    chosen_type = force_type or pick_next_type(recent, directives)
    print(f"generate_daily: chosen type = {chosen_type}")

    out_dir: Optional[Path] = None
    if chosen_type == "D-AGENT":
        scenario_n = pick_next_d_scenario(relevant_for_scenario)
        print(f"generate_daily: D-AGENT scenario rotation → {scenario_n}")
        out_dir = dispatch_d_agent(scenario_n, dry_run)
    else:
        dispatch_not_wired(chosen_type)
        return 0

    if dry_run:
        print("generate_daily: dry-run complete")
        return 0

    if not out_dir:
        print(f"generate_daily: dispatcher returned no folder — aborting", file=sys.stderr)
        return 2

    # Upload to Drive
    print(f"generate_daily: uploading {out_dir.name} to Drive...")
    drive_info = await upload_campaign_to_drive(out_dir)
    folder_url = drive_info["folder_url"]
    slide1_url = ""
    for f in drive_info["uploaded_files"]:
        if f["name"] == "slide_01.png":
            slide1_url = f["url"]
            break
    print(f"  folder: {folder_url}")
    print(f"  slide_01: {slide1_url}")

    # Read manifest for caption + hashtags
    manifest_path = out_dir / "instagram_post.json"
    if not manifest_path.is_file():
        print(f"ERROR: missing manifest {manifest_path}", file=sys.stderr)
        return 3
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    caption_ig = manifest.get("caption_ig") or manifest.get("caption") or ""
    caption_fb = manifest.get("caption_fb") or caption_ig
    hashtags_list = manifest.get("hashtags", [])
    hashtags = ", ".join(hashtags_list) if isinstance(hashtags_list, list) else str(hashtags_list)

    print(f"generate_daily: pushing PENDING row to Sheet...")
    row_num = await push_row(
        ADMIN_USER_ID,
        campaign_id=manifest["campaign_id"],
        platform="both",
        caption_ig=caption_ig,
        caption_fb=caption_fb,
        hashtags=hashtags,
        drive_folder=folder_url,
        thumbnail_url=slide1_url,
        first_comment="",
    )
    if not row_num:
        print(f"ERROR: push_row returned None", file=sys.stderr)
        return 4

    print(f"generate_daily: DONE — row {row_num} = {manifest['campaign_id']}")
    return 0


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(description="Daily 1-post generator (Phase 0.18).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Pick type + scenario, print plan, do not call generators or write Sheet/Drive.")
    parser.add_argument("--force-type", choices=TYPES, default=None,
                        help="Bypass round-robin: force a specific type (e.g. for manual catch-up).")
    args = parser.parse_args()

    return asyncio.run(_run(args.dry_run, args.force_type))


if __name__ == "__main__":
    raise SystemExit(main())
