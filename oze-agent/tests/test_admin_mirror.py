from datetime import datetime, timezone

import pytest


def _user(**overrides):
    base = {
        "id": "user-1",
        "name": "Łukasz Fathi",
        "email": "lukasz@example.com",
        "phone": "+48794757420",
        "telegram_id": 123,
        "subscription_status": "active",
        "subscription_plan": "monthly",
        "activation_paid": True,
        "google_sheets_id": "sheet-1",
        "google_calendar_id": "cal-1",
        "google_drive_folder_id": "drive-1",
        "onboarding_completed": True,
        "created_at": "2026-05-01T10:00:00+00:00",
        "updated_at": "2026-05-17T10:00:00+00:00",
        "is_suspended": False,
        "is_deleted": False,
    }
    base.update(overrides)
    return base


def test_contact_row_has_owner_columns_and_full_crm_schema():
    from shared.admin_mirror.rows import CONTACT_HEADERS, build_contact_row
    from shared.google_sheets import DEFAULT_COLUMNS

    synced_at = "2026-05-17T03:00:00+02:00"
    client = {
        "Imię i nazwisko": "Jan Kowalski",
        "Telefon": "600100200",
        "Email": "jan@example.com",
        "Miasto": "Warszawa",
        "Status": "Oferta wysłana",
        "Notatki": "decyzja po weekendzie",
        "_row": 7,
    }

    row = build_contact_row(_user(), client, synced_at)

    assert CONTACT_HEADERS[:8] == [
        "Użytkownik",
        "Email użytkownika",
        "Telefon użytkownika",
        "Status subskrypcji",
        "User ID",
        "Źródłowy arkusz",
        "Źródłowy wiersz",
        "Data syncu",
    ]
    assert CONTACT_HEADERS[8:] == DEFAULT_COLUMNS
    assert row[:8] == [
        "Łukasz Fathi",
        "lukasz@example.com",
        "+48794757420",
        "active",
        "user-1",
        "sheet-1",
        7,
        synced_at,
    ]
    assert row[8:13] == [
        "Jan Kowalski",
        "600100200",
        "jan@example.com",
        "Warszawa",
        "",
    ]
    assert "conversation_history" not in CONTACT_HEADERS


def test_snapshot_merge_replaces_active_rows_and_preserves_canceled_rows():
    from shared.admin_mirror.rows import CONTACT_HEADERS, merge_contact_snapshot_rows

    old_active = [
        "Active User",
        "active@example.com",
        "",
        "active",
        "active-user",
        "sheet-active",
        2,
        "old-sync",
    ] + ["Old Active"] + [""] * (len(CONTACT_HEADERS) - 9)
    old_canceled = [
        "Canceled User",
        "canceled@example.com",
        "",
        "active",
        "canceled-user",
        "sheet-canceled",
        3,
        "old-sync",
    ] + ["Canceled Client"] + [""] * (len(CONTACT_HEADERS) - 9)
    fresh_active = [
        "Active User",
        "active@example.com",
        "",
        "active",
        "active-user",
        "sheet-active",
        4,
        "new-sync",
    ] + ["New Active"] + [""] * (len(CONTACT_HEADERS) - 9)

    merged = merge_contact_snapshot_rows(
        existing_values=[CONTACT_HEADERS, old_active, old_canceled],
        fresh_active_rows=[fresh_active],
        active_user_ids={"active-user"},
        canceled_users_by_id={"canceled-user": _user(id="canceled-user", subscription_status="canceled")},
    )

    assert merged == [
        fresh_active,
        [
            "Canceled User",
            "canceled@example.com",
            "",
            "canceled",
            "canceled-user",
            "sheet-canceled",
            3,
            "old-sync",
        ] + ["Canceled Client"] + [""] * (len(CONTACT_HEADERS) - 9),
    ]


def test_offer_rows_include_component_columns():
    from shared.admin_mirror.rows import OFFER_HEADERS, build_offer_rows

    rows = build_offer_rows(
        [_user()],
        [
            {
                "id": "offer-1",
                "user_id": "user-1",
                "name": "PV 6,2 kWp — dom",
                "status": "ready",
                "product_type": "PV",
                "price_net_pln": 27020,
                "vat_rate": 8,
                "pv_power_kwp": 6.2,
                "storage_capacity_kwh": 10,
                "panel_brand": "JA Solar",
                "panel_model": "DeepBlue",
                "inverter_brand": "Sofar",
                "inverter_model": "HYD",
                "storage_brand": "Pylontech",
                "storage_model": "Force H2",
                "construction": "dach skośny",
                "protections_ac_dc": "AC/DC",
                "installation": "montaż standardowy",
                "monitoring_ems": "aplikacja",
                "warranty": "10 lat",
                "payment_terms": "50/50",
                "implementation_time": "30 dni",
                "validity": "14 dni",
                "created_at": "2026-05-10T10:00:00+00:00",
                "updated_at": "2026-05-11T10:00:00+00:00",
            }
        ],
    )

    assert "PV kWp" in OFFER_HEADERS
    assert "Magazyn kWh" in OFFER_HEADERS
    assert "Panel" in OFFER_HEADERS
    assert "Inwerter" in OFFER_HEADERS
    assert "Magazyn" in OFFER_HEADERS
    row = rows[0]
    assert row[OFFER_HEADERS.index("Oferta")] == "PV 6,2 kWp — dom"
    assert row[OFFER_HEADERS.index("PV kWp")] == 6.2
    assert row[OFFER_HEADERS.index("Magazyn kWh")] == 10
    assert row[OFFER_HEADERS.index("Panel")] == "JA Solar DeepBlue"
    assert row[OFFER_HEADERS.index("Inwerter")] == "Sofar HYD"
    assert row[OFFER_HEADERS.index("Magazyn")] == "Pylontech Force H2"


def test_ai_usage_rows_aggregate_daily_without_raw_conversation_content():
    from shared.admin_mirror.rows import AI_USAGE_HEADERS, build_ai_usage_daily_rows

    rows = build_ai_usage_daily_rows(
        [_user()],
        [
            {
                "telegram_id": 123,
                "interaction_type": "classify",
                "model_used": "claude-haiku",
                "tokens_in": 100,
                "tokens_out": 20,
                "cost_usd": 0.01,
                "created_at": "2026-05-17T08:00:00+00:00",
            },
            {
                "telegram_id": 123,
                "interaction_type": "extract",
                "model_used": "claude-sonnet",
                "tokens_in": 200,
                "tokens_out": 50,
                "cost_usd": 0.04,
                "created_at": "2026-05-17T09:00:00+00:00",
            },
        ],
    )

    assert "Treść rozmowy" not in AI_USAGE_HEADERS
    assert rows == [[
        "2026-05-17",
        "Łukasz Fathi",
        "lukasz@example.com",
        "user-1",
        123,
        2,
        300,
        70,
        0.05,
        "claude-haiku, claude-sonnet",
        "classify, extract",
    ]]


def test_user_filter_refreshes_active_and_keeps_canceled_only():
    from shared.admin_mirror.data import is_mirror_user, is_refreshable_user

    active = _user(subscription_status="active")
    canceled = _user(id="user-2", subscription_status="canceled")
    pending = _user(id="user-3", subscription_status="pending_payment")
    suspended = _user(id="user-4", subscription_status="active", is_suspended=True)
    deleted = _user(id="user-5", subscription_status="active", is_deleted=True)

    assert is_mirror_user(active) is True
    assert is_refreshable_user(active) is True
    assert is_mirror_user(canceled) is True
    assert is_refreshable_user(canceled) is False
    assert is_mirror_user(pending) is False
    assert is_mirror_user(suspended) is False
    assert is_mirror_user(deleted) is False


class _Execute:
    def __init__(self, value=None):
        self.value = value if value is not None else {}

    def execute(self):
        return self.value


class _MirrorEvents:
    def __init__(self):
        self.inserted = []
        self.updated = []
        self.deleted = []
        self.list_kwargs = None
        self._existing = [
            {
                "id": "existing-1",
                "summary": "[Old] Spotkanie",
                "start": {"dateTime": "2026-05-18T10:00:00+02:00"},
                "end": {"dateTime": "2026-05-18T11:00:00+02:00"},
                "extendedProperties": {
                    "private": {
                        "oze_admin_mirror": "true",
                        "admin_mirror_key": "user-1:cal-1:event-1",
                    }
                },
            },
            {
                "id": "stale-1",
                "summary": "[Stale] Telefon",
                "start": {"dateTime": "2026-05-18T12:00:00+02:00"},
                "end": {"dateTime": "2026-05-18T12:15:00+02:00"},
                "extendedProperties": {
                    "private": {
                        "oze_admin_mirror": "true",
                        "admin_mirror_key": "user-old:cal-old:event-old",
                    }
                },
            },
        ]

    def list(self, **kwargs):
        self.list_kwargs = kwargs
        return _Execute({"items": self._existing})

    def insert(self, **kwargs):
        self.inserted.append(kwargs)
        return _Execute({"id": "inserted-1", **kwargs["body"]})

    def update(self, **kwargs):
        self.updated.append(kwargs)
        return _Execute({"id": kwargs["eventId"], **kwargs["body"]})

    def delete(self, **kwargs):
        self.deleted.append(kwargs)
        return _Execute({})


class _MirrorCalendarService:
    def __init__(self):
        self._events = _MirrorEvents()

    def events(self):
        return self._events


def test_calendar_mirror_updates_existing_inserts_new_and_deletes_stale():
    from shared.admin_mirror.calendar import build_mirror_calendar_event, sync_admin_calendar_events

    service = _MirrorCalendarService()
    desired = [
        build_mirror_calendar_event(
            _user(),
            {
                "id": "event-1",
                "title": "Spotkanie — Jan Kowalski",
                "description": "źródłowy opis",
                "location": "Warszawa",
                "start": "2026-05-18T10:00:00+02:00",
                "end": "2026-05-18T11:00:00+02:00",
                "event_type": "in_person",
            },
        ),
        build_mirror_calendar_event(
            _user(),
            {
                "id": "event-2",
                "title": "Telefon — Anna Nowak",
                "description": "",
                "location": "",
                "start": "2026-05-19T12:00:00+02:00",
                "end": "2026-05-19T12:15:00+02:00",
                "event_type": "phone_call",
            },
        ),
    ]

    result = sync_admin_calendar_events(
        service,
        "admin-cal",
        desired,
        now=datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc),
    )

    assert result == {"created": 1, "updated": 1, "deleted": 1}
    assert service.events().list_kwargs["calendarId"] == "admin-cal"
    assert len(service.events().updated) == 1
    assert service.events().updated[0]["eventId"] == "existing-1"
    assert service.events().updated[0]["body"]["summary"] == "[Łukasz Fathi] Spotkanie — Jan Kowalski"
    assert len(service.events().inserted) == 1
    inserted_private = service.events().inserted[0]["body"]["extendedProperties"]["private"]
    assert inserted_private["admin_mirror_key"] == "user-1:cal-1:event-2"
    assert service.events().deleted == [{"calendarId": "admin-cal", "eventId": "stale-1"}]
