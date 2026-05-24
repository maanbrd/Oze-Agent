"""Iterate-from-feedback cron — Phase 0.18.

Daily 07:00 Warsaw. Reads ``list_with_feedback(ADMIN_USER_ID)`` (rows where
Maan wrote text into the ``feedback_prompt`` column). For each row:

1. Detects the **scope** of the feedback via keyword classification:
   - ``brand_only`` — only re-runs the @agentoze pill composite + ffmpeg loop.
     Cheap (no OpenAI call) and idempotent.
   - ``caption`` — flags for Maan; does NOT auto-rewrite (too risky on a copy
     change). Captures intent in the log; Maan edits caption cells manually.
   - ``visual_full`` — flags for Maan; visual regen needs prompt synthesis
     that the MVP doesn't do automatically (defer to v2).
   - ``log_only`` — fallback for anything else.
2. Snapshots the prompt into ``feedback_history`` and clears
   ``feedback_prompt`` via ``update_from_feedback``. Row stays PENDING so
   Maan re-reviews next time he opens the Sheet.
3. Appends a verbatim entry to a per-day log file under
   ``~/.claude/projects/.../memory/feedback_log_YYYY-MM-DD.md``.
4. Updates ``MEMORY.md`` index with a one-line pointer to today's log
   (only the first iteration of the day adds the index entry).

This script is a Phase 0.18 MVP. Auto visual/caption regen is intentionally
deferred — better to capture intent reliably and let Maan steer than to
silently mangle copy or burn $0.25 per failed-to-grok feedback.

Usage::

    railway run --service bot --environment production .venv/bin/python3 \\
        scripts/marketing/iterate_from_feedback.py [--dry-run]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

from shared.marketing_sheets import (
    list_with_feedback,
    update_from_feedback,
)

logger = logging.getLogger(__name__)

ADMIN_USER_ID = "ada45bc3-4e05-4e64-9f0d-2d98e138debd"
WARSAW = ZoneInfo("Europe/Warsaw")

MEMORY_DIR = Path(
    "/Users/mansoniasty/.claude/projects/-Users-mansoniasty-workflows-Agent-OZE/memory"
)
MARKETING_OUTPUT_ROOT = Path.home() / "marketing-output"

# Keyword → scope. First scope whose any keyword is present wins.
# Order matters: more specific scopes first.
SCOPE_KEYWORDS: list[tuple[str, list[str]]] = [
    ("brand_only", ["logo", "brand", "@agentoze", "pill", "agentoze"]),
    ("caption", ["caption", "napisz", "opis", "hashtag", "tekst pod"]),
    ("visual_full", ["regen wszystko", "od nowa", "ciemniej", "jasniej",
                     "vibe", "chiaroscuro", "zdjęcie", "zdjecie", "fotka", "obrazek"]),
]


def detect_scope(prompt: str) -> str:
    """Classify feedback prompt by keyword. Returns 'log_only' as default."""
    p = prompt.lower()
    for scope, keywords in SCOPE_KEYWORDS:
        if any(kw in p for kw in keywords):
            return scope
    return "log_only"


def _rebuild_brand_pill(campaign_id: str) -> Optional[str]:
    """Re-apply canonical @agentoze brand pill via the migrated script.

    Returns None on success, or an error message string. The campaign folder
    must exist locally under ~/marketing-output/<campaign_id>/. Assumes
    raw_photo.png + meta.json are present (rebuild_slide_clean reconstructs
    the slide cleanly from raw).
    """
    folder = MARKETING_OUTPUT_ROOT / campaign_id
    if not folder.is_dir():
        return f"local folder missing: {folder}"
    raw = folder / "raw_photo.png"
    if not raw.is_file():
        # Typ D-AGENT doesn't have raw_photo (composed from landing screenshot),
        # so just re-apply composite_brand on slide_01.png in place.
        slide = folder / "slide_01.png"
        if not slide.is_file():
            return f"no raw_photo.png or slide_01.png in {folder}"
        try:
            subprocess.run(
                [
                    sys.executable, "-m",
                    "scripts.content_factory.post_brand_overlay",
                    "--slide", str(slide),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            return f"composite_brand failed: {e.stderr.strip() or e}"
        return None
    # Cinematic types (G/E with raw_photo): rebuild clean from raw.
    try:
        subprocess.run(
            [
                sys.executable, "-m",
                "scripts.content_factory.rebuild_slide_clean",
                "--folder", str(folder),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        return f"rebuild_slide_clean failed: {e.stderr.strip() or e}"
    return None


def _today_log_path() -> Path:
    date = datetime.now(WARSAW).strftime("%Y-%m-%d")
    return MEMORY_DIR / f"feedback_log_{date}.md"


def _append_log_entry(
    *,
    campaign_id: str,
    prompt: str,
    scope: str,
    action: str,
) -> Path:
    """Append a verbatim entry to today's per-day feedback log. Creates the
    file with a header on the first entry of the day. Returns the log path.
    """
    path = _today_log_path()
    is_new = not path.exists()
    timestamp = datetime.now(WARSAW).strftime("%H:%M")
    block = (
        f"## {timestamp} — `{campaign_id}`\n\n"
        f"**Scope:** {scope}\n\n"
        f"**Feedback (verbatim):**\n\n> {prompt.strip()}\n\n"
        f"**Action:** {action}\n\n---\n\n"
    )
    if is_new:
        header = (
            f"# Daily feedback log — {datetime.now(WARSAW).strftime('%Y-%m-%d')}\n\n"
            "Auto-generated by `iterate_from_feedback.py`. Each entry is a "
            "Maan-written feedback_prompt that triggered an iteration cycle. "
            "Use these logs for weekly consolidation (`claude consolidate this "
            "week's feedback logs`) — recurring themes become permanent rules.\n\n"
        )
        path.write_text(header + block, encoding="utf-8")
    else:
        with path.open("a", encoding="utf-8") as f:
            f.write(block)
    return path


def _ensure_memory_index_entry(log_path: Path, iteration_count: int) -> None:
    """Add or update the index line in MEMORY.md for today's log file."""
    memory_md = MEMORY_DIR / "MEMORY.md"
    if not memory_md.is_file():
        return
    date = log_path.stem.replace("feedback_log_", "")
    relative = log_path.name
    line = (
        f"- [Daily feedback log {date}]({relative}) — {iteration_count} "
        f"iteration{'s' if iteration_count != 1 else ''}"
    )
    text = memory_md.read_text(encoding="utf-8").rstrip()
    lines = text.splitlines()
    # Replace existing line for this date, or append.
    prefix = f"- [Daily feedback log {date}]("
    replaced = False
    for i, existing in enumerate(lines):
        if existing.startswith(prefix):
            lines[i] = line
            replaced = True
            break
    if not replaced:
        lines.append(line)
    memory_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


async def _process_row(row: dict, *, dry_run: bool) -> dict:
    """Process one feedback row. Returns a summary dict for logging."""
    campaign_id = row.get("campaign_id", "?")
    prompt = (row.get("feedback_prompt") or "").strip()
    scope = detect_scope(prompt)

    action_summary: str
    if scope == "brand_only":
        if dry_run:
            action_summary = "(dry-run) would re-apply @agentoze brand pill"
        else:
            err = await asyncio.to_thread(_rebuild_brand_pill, campaign_id)
            if err:
                action_summary = f"brand re-apply FAILED: {err}"
            else:
                action_summary = (
                    "re-applied @agentoze brand pill on local slide. "
                    "Manual Drive re-upload still required for the new pixels "
                    "to reach @agentoze IG (no auto-upload in MVP)."
                )
    elif scope == "caption":
        action_summary = (
            "FLAGGED for Maan: caption-scope feedback. Agent does NOT auto-rewrite "
            "copy — Maan edits caption_ig / caption_fb cells directly in Sheet "
            "and the next publish picks up the new text."
        )
    elif scope == "visual_full":
        action_summary = (
            "FLAGGED for Maan: visual-scope feedback. Auto visual regen requires "
            "prompt synthesis (Phase 0.18 deferred to v2). For now: human "
            "regen via generator script + Drive replace."
        )
    else:
        action_summary = (
            "logged only — no keyword match for auto-action. Review log "
            "during weekly consolidation."
        )

    # Snapshot the prompt to feedback_history + clear feedback_prompt cell.
    if not dry_run:
        ok = await update_from_feedback(ADMIN_USER_ID, campaign_id)
        if not ok:
            action_summary += " | WARN: update_from_feedback returned False"

    # Append to per-day log (even in dry-run so we can verify formatting).
    log_path = _append_log_entry(
        campaign_id=campaign_id,
        prompt=prompt,
        scope=scope,
        action=action_summary,
    )

    return {
        "campaign_id": campaign_id,
        "scope": scope,
        "log_path": str(log_path),
        "action": action_summary,
    }


async def _run(dry_run: bool) -> int:
    rows = await list_with_feedback(ADMIN_USER_ID)
    print(f"iterate_from_feedback: found {len(rows)} row(s) with feedback_prompt")
    if not rows:
        return 0

    results = []
    for row in rows:
        try:
            result = await _process_row(row, dry_run=dry_run)
        except Exception as e:
            logger.exception("error processing row %s", row.get("campaign_id"))
            result = {
                "campaign_id": row.get("campaign_id"),
                "scope": "ERROR",
                "action": f"exception: {e}",
            }
        results.append(result)
        print(
            f"  - {result['campaign_id']} [{result['scope']}] → "
            f"{result['action'][:120]}"
        )

    # Update MEMORY.md index with today's log + iteration count.
    log_path = _today_log_path()
    if log_path.exists() and not dry_run:
        _ensure_memory_index_entry(log_path, iteration_count=len(rows))

    print(f"\niterate_from_feedback: processed {len(results)} row(s); log → {log_path}")
    return 0


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(description="Iterate from Maan feedback (Phase 0.18).")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Process feedback + write log, but do not call update_from_feedback or rebuild slides.",
    )
    args = parser.parse_args()
    return asyncio.run(_run(args.dry_run))


if __name__ == "__main__":
    raise SystemExit(main())
