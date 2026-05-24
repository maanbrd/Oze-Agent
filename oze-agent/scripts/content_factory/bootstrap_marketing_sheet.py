"""Bootstrap the Agent-OZE marketing review queue spreadsheet.

One-time, idempotent. Creates a new Google Sheet with the ``marketing_queue``
tab and operational template, then stores the spreadsheet id in
``users.marketing_sheets_id``. If the user already has an id, prints it and
exits without creating anything.

The sheet must live on the ``admin@agent-oze.pl`` Google account — run the
script with OAuth tokens for THAT account stored on the target Supabase user
row (Maan's row, ``OZE_OWNER_USER_ID``). The Drive scope on the bot's OAuth
flow is ``drive.file`` which only exposes app-created files, so the bootstrap
must be done with credentials that can create files on the admin account.

Usage (from ``oze-agent/``)::

    railway run --service bot --environment production \\
        python -m scripts.content_factory.bootstrap_marketing_sheet \\
        --user-id bd381405-66d2-4544-b817-117f8f8de441
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from shared.database import get_user_by_id
from shared.marketing_sheets import create_marketing_spreadsheet

logger = logging.getLogger(__name__)


def _spreadsheet_url(spreadsheet_id: str) -> str:
    return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"


async def _run(user_id: str, name: str) -> int:
    user = get_user_by_id(user_id)
    if not user:
        print(f"ERROR: user {user_id} not found in Supabase", file=sys.stderr)
        return 1
    if not user.get("google_refresh_token"):
        print(
            f"ERROR: user {user_id} has no Google OAuth refresh token. "
            "Complete OAuth on the admin@agent-oze.pl account first.",
            file=sys.stderr,
        )
        return 1

    existing = user.get("marketing_sheets_id")
    if existing:
        print(f"Marketing sheet already bootstrapped: {existing}")
        print(_spreadsheet_url(existing))
        return 0

    spreadsheet_id = await create_marketing_spreadsheet(user_id, name=name)
    if not spreadsheet_id:
        print("ERROR: create_marketing_spreadsheet returned None", file=sys.stderr)
        return 1

    print(f"Marketing sheet created: {spreadsheet_id}")
    print(_spreadsheet_url(spreadsheet_id))
    return 0


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="One-time bootstrap for the Agent-OZE marketing review queue Sheet.",
    )
    parser.add_argument(
        "--user-id",
        required=True,
        help="Supabase user UUID that will own the spreadsheet "
             "(typically OZE_OWNER_USER_ID = Maan).",
    )
    parser.add_argument(
        "--name",
        default="Agent OZE — Marketing Queue",
        help="Display name for the spreadsheet.",
    )
    args = parser.parse_args()

    return asyncio.run(_run(args.user_id, args.name))


if __name__ == "__main__":
    raise SystemExit(main())
