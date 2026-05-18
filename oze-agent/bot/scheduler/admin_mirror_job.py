"""PTB JobQueue wrapper for the daily owner-facing admin mirror."""

import logging
from datetime import time
from zoneinfo import ZoneInfo

from telegram.ext import Application, ContextTypes

from bot.config import Config
from shared.admin_mirror import run_admin_mirror

logger = logging.getLogger(__name__)

WARSAW = ZoneInfo("Europe/Warsaw")
ADMIN_MIRROR_TIME = time(3, 0, tzinfo=WARSAW)
JOB_NAME = "admin_mirror"


async def _admin_mirror_callback(context: ContextTypes.DEFAULT_TYPE) -> None:
    result = await run_admin_mirror()
    logger.info("admin_mirror.job %s", result)


def register_admin_mirror(app: Application) -> None:
    """Register the daily owner-facing mirror job when enabled."""
    if not Config.ADMIN_MIRROR_ENABLED:
        logger.info("admin_mirror: disabled")
        return

    job_queue = app.job_queue
    if job_queue is None:
        logger.warning(
            "admin_mirror: JobQueue unavailable on Application — "
            "mirror will not be scheduled"
        )
        return

    job_queue.run_daily(
        _admin_mirror_callback,
        time=ADMIN_MIRROR_TIME,
        name=JOB_NAME,
    )
    logger.info("admin_mirror: scheduled daily at %s (Europe/Warsaw)", ADMIN_MIRROR_TIME)
