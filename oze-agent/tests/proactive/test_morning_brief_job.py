"""Phase 6A — PTB JobQueue registration for the morning brief."""

from datetime import time
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

from bot.scheduler.morning_brief_job import (
    JOB_NAME,
    MORNING_BRIEF_TIME,
    WEEKDAYS,
    register_morning_brief,
)

WARSAW = ZoneInfo("Europe/Warsaw")


def test_morning_brief_time_is_0700_warsaw():
    assert MORNING_BRIEF_TIME == time(7, 0, tzinfo=WARSAW)


def test_weekdays_mon_to_fri_ptb_convention():
    # PTB uses Mon=0 .. Sun=6; MVP constraint: weekdays only.
    assert WEEKDAYS == (0, 1, 2, 3, 4)


def test_register_morning_brief_schedules_mon_fri_0700():
    app = MagicMock()
    register_morning_brief(app)
    app.job_queue.run_daily.assert_called_once()
    _, kwargs = app.job_queue.run_daily.call_args
    assert kwargs["time"] == MORNING_BRIEF_TIME
    assert kwargs["days"] == WEEKDAYS
    assert kwargs["name"] == JOB_NAME


def test_register_morning_brief_tolerates_missing_jobqueue():
    # Some PTB configurations (or tests) run without a JobQueue.
    # The registration helper must degrade quietly, not crash startup.
    app = MagicMock()
    app.job_queue = None
    register_morning_brief(app)  # must not raise
