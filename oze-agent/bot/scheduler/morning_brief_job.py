"""PTB JobQueue wrapper for the Phase 6 morning brief.

Registers a daily 07:00 Europe/Warsaw, Monday–Friday job that invokes
`shared.proactive.morning_brief.run_morning_brief`. All brief logic
lives in the shared module; this file exists only to bridge the PTB
Application object to the scheduler.
"""

import logging
from datetime import time
from zoneinfo import ZoneInfo

from telegram.ext import Application, ContextTypes

from shared.proactive.morning_brief import run_morning_brief

logger = logging.getLogger(__name__)

WARSAW = ZoneInfo("Europe/Warsaw")
MORNING_BRIEF_TIME = time(7, 0, tzinfo=WARSAW)
# PTB convention: Mon=0 .. Sun=6. Weekdays only.
WEEKDAYS = (0, 1, 2, 3, 4)
JOB_NAME = "morning_brief"


async def _morning_brief_callback(context: ContextTypes.DEFAULT_TYPE) -> None:
    result = await run_morning_brief(context.bot)
    logger.info("morning_brief.run %s", result)


def register_morning_brief(app: Application) -> None:
    """Register the daily morning brief job on the Application's JobQueue."""
    job_queue = app.job_queue
    if job_queue is None:
        logger.warning(
            "morning_brief: JobQueue unavailable on Application — "
            "brief will not be scheduled"
        )
        return
    job_queue.run_daily(
        _morning_brief_callback,
        time=MORNING_BRIEF_TIME,
        days=WEEKDAYS,
        name=JOB_NAME,
    )
    logger.info(
        "morning_brief: scheduled daily at %s (Europe/Warsaw), days=%s",
        MORNING_BRIEF_TIME, WEEKDAYS,
    )
