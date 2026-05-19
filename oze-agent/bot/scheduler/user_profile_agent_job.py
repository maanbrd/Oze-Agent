"""PTB JobQueue wrapper for the daily user profile agent."""

from __future__ import annotations

import logging
from datetime import time
from zoneinfo import ZoneInfo

from telegram.ext import Application, ContextTypes

from bot.config import Config
from shared.user_profiles import run_user_profile_agent

logger = logging.getLogger(__name__)

WARSAW = ZoneInfo("Europe/Warsaw")
USER_PROFILE_AGENT_TIME = time(2, 15, tzinfo=WARSAW)
JOB_NAME = "user_profile_agent"


async def _user_profile_agent_callback(context: ContextTypes.DEFAULT_TYPE) -> None:
    result = await run_user_profile_agent()
    logger.info("user_profile_agent.job %s", result)


def register_user_profile_agent(app: Application) -> None:
    """Register the daily profile agent when enabled."""
    if not Config.USER_PROFILE_AGENT_ENABLED:
        logger.info("user_profile_agent: disabled")
        return

    job_queue = app.job_queue
    if job_queue is None:
        logger.warning(
            "user_profile_agent: JobQueue unavailable on Application — "
            "profile agent will not be scheduled"
        )
        return

    job_queue.run_daily(
        _user_profile_agent_callback,
        time=USER_PROFILE_AGENT_TIME,
        name=JOB_NAME,
    )
    logger.info("user_profile_agent: scheduled daily at %s (Europe/Warsaw)", USER_PROFILE_AGENT_TIME)
