"""Unit tests for read-only Google health checks."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from tests_e2e import google_health


class _Executable:
    def __init__(self, payload=None, exc=None):
        self.payload = payload or {}
        self.exc = exc

    def execute(self):
        if self.exc:
            raise self.exc
        return self.payload


class _SheetsValues:
    def get(self, spreadsheetId, range):
        assert spreadsheetId == "sheet-1"
        assert range == "A1:ZZ1"
        return _Executable({"values": [["Imię i nazwisko", "Miasto"]]})


class _SheetsService:
    def spreadsheets(self):
        return self

    def values(self):
        return _SheetsValues()


class _CalendarEvents:
    def list(self, calendarId, timeMin, timeMax, singleEvents, orderBy):
        assert calendarId == "calendar-1"
        assert singleEvents is True
        assert orderBy == "startTime"
        return _Executable({"items": []})


class _CalendarService:
    def events(self):
        return _CalendarEvents()


class _DriveAbout:
    def get(self, fields):
        assert fields == "user"
        return _Executable({"user": {"emailAddress": "tester@example.com"}})


class _DriveService:
    def about(self):
        return _DriveAbout()


@pytest.mark.asyncio
async def test_google_health_passes_when_all_services_are_readable():
    user = {
        "google_sheets_id": "sheet-1",
        "google_calendar_id": "calendar-1",
        "google_drive_folder_id": "drive-root",
    }

    with patch("tests_e2e.google_health.resolve_user_id", new=AsyncMock(return_value="user-1")), \
         patch("tests_e2e.google_health.get_user_by_id", return_value=user), \
         patch("tests_e2e.google_health.get_google_credentials", return_value=object()), \
         patch("tests_e2e.google_health._get_sheets_service_sync", return_value=_SheetsService()), \
         patch("tests_e2e.google_health._get_calendar_service_sync", return_value=_CalendarService()), \
         patch("tests_e2e.google_health._get_drive_service_sync", return_value=_DriveService()):
        result = await google_health.run_google_health(123)

    assert result.ok is True
    assert {check.name for check in result.checks} == {
        "supabase_user",
        "google_credentials",
        "sheets_read",
        "calendar_read",
        "drive_read",
    }
    rendered = google_health.render_markdown(result)
    assert "sheet-1" not in rendered
    assert "calendar-1" not in rendered
    assert "user-1" not in rendered
    assert google_health._fingerprint("sheet-1") in rendered
    assert google_health._fingerprint("calendar-1") in rendered
    assert google_health._fingerprint("user-1") in rendered


@pytest.mark.asyncio
async def test_google_health_blocks_when_user_cannot_be_resolved():
    with patch("tests_e2e.google_health.resolve_user_id", new=AsyncMock(return_value=None)):
        result = await google_health.run_google_health(123)

    assert result.ok is False
    assert result.checks[0].name == "supabase_user"
    assert result.checks[0].tag == "blocker"


@pytest.mark.asyncio
async def test_google_health_reports_missing_google_ids_as_blockers():
    with patch("tests_e2e.google_health.resolve_user_id", new=AsyncMock(return_value="user-1")), \
         patch("tests_e2e.google_health.get_user_by_id", return_value={}), \
         patch("tests_e2e.google_health.get_google_credentials", return_value=object()):
        result = await google_health.run_google_health(123)

    assert result.ok is False
    blockers = [check.name for check in result.checks if check.tag == "blocker"]
    assert "sheets_read" in blockers
    assert "calendar_read" in blockers


@pytest.mark.asyncio
async def test_google_health_reports_service_exception_as_blocker():
    failing_sheets = Mock()
    failing_sheets.spreadsheets.side_effect = RuntimeError("sheets down")

    with patch("tests_e2e.google_health.resolve_user_id", new=AsyncMock(return_value="user-1")), \
         patch("tests_e2e.google_health.get_user_by_id", return_value={"google_sheets_id": "sheet-1"}), \
         patch("tests_e2e.google_health.get_google_credentials", return_value=object()), \
         patch("tests_e2e.google_health._get_sheets_service_sync", return_value=failing_sheets), \
         patch("tests_e2e.google_health._get_calendar_service_sync", return_value=None), \
         patch("tests_e2e.google_health._get_drive_service_sync", return_value=None):
        result = await google_health.run_google_health(123)

    assert result.ok is False
    sheets = next(check for check in result.checks if check.name == "sheets_read")
    assert sheets.tag == "blocker"
    assert "sheets down" in sheets.detail


def test_safe_exception_detail_redacts_raw_and_url_encoded_ids():
    detail = google_health._safe_exception_detail(
        RuntimeError("missing cal%40group.calendar.google.com / cal@group.calendar.google.com"),
        "cal@group.calendar.google.com",
    )

    assert "cal@group.calendar.google.com" not in detail
    assert "cal%40group.calendar.google.com" not in detail
    assert google_health._fingerprint("cal@group.calendar.google.com") in detail
