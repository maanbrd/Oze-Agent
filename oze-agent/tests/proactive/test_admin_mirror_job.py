"""PTB JobQueue registration for the owner-facing admin mirror."""

from datetime import time
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

from bot.scheduler.admin_mirror_job import (
    ADMIN_MIRROR_TIME,
    JOB_NAME,
    register_admin_mirror,
)

WARSAW = ZoneInfo("Europe/Warsaw")


def test_admin_mirror_time_is_0300_warsaw():
    assert ADMIN_MIRROR_TIME == time(3, 0, tzinfo=WARSAW)


def test_register_admin_mirror_skips_when_disabled():
    app = MagicMock()
    with patch("bot.scheduler.admin_mirror_job.Config.ADMIN_MIRROR_ENABLED", False):
        register_admin_mirror(app)
    app.job_queue.run_daily.assert_not_called()


def test_register_admin_mirror_schedules_daily_when_enabled():
    app = MagicMock()
    with patch("bot.scheduler.admin_mirror_job.Config.ADMIN_MIRROR_ENABLED", True):
        register_admin_mirror(app)
    app.job_queue.run_daily.assert_called_once()
    _, kwargs = app.job_queue.run_daily.call_args
    assert kwargs["time"] == ADMIN_MIRROR_TIME
    assert kwargs["name"] == JOB_NAME
