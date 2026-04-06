"""Step A.21: Create Google Sheets, Calendar, and Drive folder for beta user."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.database import update_user
from shared.google_calendar import create_calendar
from shared.google_drive import create_root_folder
from shared.google_sheets import create_spreadsheet

USER_ID = "bd381405-66d2-4544-b817-117f8f8de441"


async def setup() -> None:
    sheet_id = await create_spreadsheet(USER_ID, "OZE Klienci")
    print(f"Spreadsheet: {sheet_id}")

    cal_id = await create_calendar(USER_ID, "OZE Spotkania")
    print(f"Calendar: {cal_id}")

    folder_id = await create_root_folder(USER_ID)
    print(f"Drive folder: {folder_id}")

    update_user(USER_ID, {
        "google_sheets_id": sheet_id,
        "google_sheets_name": "OZE Klienci",
        "google_calendar_id": cal_id,
        "google_calendar_name": "OZE Spotkania",
        "google_drive_folder_id": folder_id,
        "onboarding_completed": True,
    })
    print("✅ Beta user setup complete")


asyncio.run(setup())
