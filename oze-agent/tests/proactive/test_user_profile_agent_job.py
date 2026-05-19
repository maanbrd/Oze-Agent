"""PTB JobQueue registration for the user profile agent."""

from datetime import time
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

from bot.scheduler.user_profile_agent_job import (
    JOB_NAME,
    USER_PROFILE_AGENT_TIME,
    register_user_profile_agent,
)

WARSAW = ZoneInfo("Europe/Warsaw")


def test_user_profile_agent_time_is_0215_warsaw():
    assert USER_PROFILE_AGENT_TIME == time(2, 15, tzinfo=WARSAW)


def test_register_user_profile_agent_skips_when_disabled():
    app = MagicMock()
    with patch("bot.scheduler.user_profile_agent_job.Config.USER_PROFILE_AGENT_ENABLED", False):
        register_user_profile_agent(app)
    app.job_queue.run_daily.assert_not_called()


def test_register_user_profile_agent_schedules_daily_when_enabled():
    app = MagicMock()
    with patch("bot.scheduler.user_profile_agent_job.Config.USER_PROFILE_AGENT_ENABLED", True):
        register_user_profile_agent(app)
    app.job_queue.run_daily.assert_called_once()
    _, kwargs = app.job_queue.run_daily.call_args
    assert kwargs["time"] == USER_PROFILE_AGENT_TIME
    assert kwargs["name"] == JOB_NAME


def test_register_user_profile_agent_tolerates_missing_jobqueue():
    app = MagicMock()
    app.job_queue = None
    with patch("bot.scheduler.user_profile_agent_job.Config.USER_PROFILE_AGENT_ENABLED", True):
        register_user_profile_agent(app)
