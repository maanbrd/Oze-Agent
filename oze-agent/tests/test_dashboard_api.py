from types import SimpleNamespace

import pytest


class _FakeQuery:
    def __init__(self, data):
        self.data = data

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def execute(self):
        return SimpleNamespace(data=self.data)


class _FakeSupabase:
    def __init__(self, users):
        self.users = users

    def table(self, name):
        assert name == "users"
        return _FakeQuery(self.users)


@pytest.mark.asyncio
async def test_dashboard_crm_uses_google_resource_ids(monkeypatch):
    from api.auth import AuthUser
    from api.routes import dashboard

    user = {
        "id": "user-1",
        "auth_user_id": "auth-1",
        "google_sheets_id": "sheet-1",
        "google_calendar_id": "cal-1",
        "google_drive_folder_id": "drive-1",
    }
    monkeypatch.setattr(dashboard, "get_supabase_client", lambda: _FakeSupabase([user]))
    async def fake_sheet_clients(user_id, sheet_id):
        return [
            {
                "id": "sheet-row-1",
                "fullName": "Jan Testowy",
                "city": "Marki",
                "status": "Nowy lead",
                "sheetsUrl": "https://docs.google.com/spreadsheets/d/sheet-1",
            }
        ]

    async def fake_calendar_events(user_id, calendar_id):
        return [
            {
                "id": "event-1",
                "clientName": "Jan Testowy",
                "startsAt": "2026-04-30T10:00:00+02:00",
                "calendarUrl": "https://calendar.google.com/calendar",
            }
        ]

    monkeypatch.setattr(dashboard, "_fetch_sheet_clients", fake_sheet_clients, raising=False)
    monkeypatch.setattr(dashboard, "_fetch_calendar_events", fake_calendar_events, raising=False)

    result = await dashboard.get_dashboard_crm(
        AuthUser(user_id="auth-1", email="jan@example.pl", claims={})
    )

    assert result["clients"][0]["sheetsUrl"].startswith("https://docs.google.com")
    assert result["events"][0]["calendarUrl"].startswith("https://calendar.google.com")
    assert result["source"] == "live"
    assert "Google" in result["sourceMessage"]
