from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from tests_e2e import google_health


class _Exec:
    def __init__(self, data):
        self._data = data

    def execute(self):
        return self._data


class _ExecRaise:
    def __init__(self, error: Exception):
        self._error = error

    def execute(self):
        raise self._error


class _Values:
    def get(self, **_kwargs):
        return _Exec({"values": [["Imię i nazwisko", "Telefon"]]})


class _Spreadsheets:
    def values(self):
        return _Values()


class _SheetsService:
    def spreadsheets(self):
        return _Spreadsheets()


class _Events:
    def list(self, **_kwargs):
        return _Exec({"items": []})


class _CalendarService:
    def events(self):
        return _Events()


class _Files:
    def get(self, **_kwargs):
        return _Exec({"id": "drive-root", "name": "OZE Klienci"})


class _DriveService:
    def files(self):
        return _Files()


@pytest.mark.asyncio
async def test_google_health_passes_when_all_google_reads_work():
    user = {
        "google_sheets_id": "sheet-1",
        "google_calendar_id": "calendar-1",
        "google_drive_folder_id": "drive-root",
    }

    with patch("tests_e2e.google_health.resolve_user_id", return_value="user-1"), \
         patch("tests_e2e.google_health.get_user_by_id", return_value=user), \
         patch("tests_e2e.google_health.get_google_credentials", return_value=object()), \
         patch("tests_e2e.google_health._get_sheets_service_sync", return_value=_SheetsService()), \
         patch("tests_e2e.google_health._get_calendar_service_sync", return_value=_CalendarService()), \
         patch("tests_e2e.google_health._get_drive_service_sync", return_value=_DriveService()):
        report = await google_health.check_google_health(1690210103)

    assert report.ok is True
    assert [check.tag for check in report.checks] == ["pass", "pass", "pass", "pass", "pass"]


@pytest.mark.asyncio
async def test_google_health_blocks_when_credentials_do_not_refresh():
    with patch("tests_e2e.google_health.resolve_user_id", return_value="user-1"), \
         patch("tests_e2e.google_health.get_user_by_id", return_value={}), \
         patch("tests_e2e.google_health.get_google_credentials", return_value=None):
        report = await google_health.check_google_health(1690210103)

    assert report.ok is False
    assert report.checks[1].name == "google_credentials_refresh"
    assert report.checks[1].tag == "blocker"


@pytest.mark.asyncio
async def test_google_health_marks_invalid_scope_as_reauth_blocker():
    user = {
        "google_sheets_id": "sheet-1",
        "google_calendar_id": "calendar-1",
        "google_drive_folder_id": "drive-root",
    }
    failing_sheets = SimpleNamespace(
        spreadsheets=lambda: SimpleNamespace(
            values=lambda: SimpleNamespace(
                get=lambda **_kwargs: _ExecRaise(RuntimeError("invalid_scope: Bad Request"))
            )
        )
    )

    with patch("tests_e2e.google_health.resolve_user_id", return_value="user-1"), \
         patch("tests_e2e.google_health.get_user_by_id", return_value=user), \
         patch("tests_e2e.google_health.get_google_credentials", return_value=object()), \
         patch("tests_e2e.google_health._get_sheets_service_sync", return_value=failing_sheets):
        report = await google_health.check_google_health(1690210103)

    assert report.ok is False
    assert any(check.tag == "blocker" and "invalid_scope" in check.detail for check in report.checks)
