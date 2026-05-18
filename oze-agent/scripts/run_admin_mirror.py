"""Run the owner-facing admin mirror once.

Usage:
  railway run --service bot --environment production python scripts/run_admin_mirror.py --force
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.admin_mirror import run_admin_mirror


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--force",
        action="store_true",
        help="Run even when ADMIN_MIRROR_ENABLED is false.",
    )
    return parser.parse_args()


async def _main() -> int:
    args = _parse_args()
    result = await run_admin_mirror(force=args.force)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
