"""Fixture seeder + per-run cleanup for E2E scenarios.

`seed_fixtures(telegram_id)` — idempotent. Creates a small canonical
set of test clients in Sheets and one Calendar event used by the
multi-match and conflict-detection scenarios. Safe to call multiple
times: existing fixtures are skipped.

`cleanup_synthetic_data(telegram_id, run_id=None)` — purges
`E2E-Beta-*` synthetic data. By default keeps fixtures (so the next
run can reuse them); pass `include_fixtures=True` for full reset.
By default deletes ALL per-run rows; pass `run_id` to scope to one run.

Both functions are exposed via MCP tools `e2e_seed_fixtures` and
`e2e_cleanup_run` (see mcp_server.py).
"""

from __future__ import annotations

import logging
from datetime import datetime, time, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from shared.google_calendar import create_event
from shared.google_sheets import add_client

from tests_e2e.calendar_verify import (
    delete_synthetic_events,
    find_event_by_summary_in_window,
    find_synthetic_events,
)
from tests_e2e.sheets_verify import (
    delete_synthetic_rows,
    find_client_row,
    find_synthetic_rows,
    resolve_user_id,
)

logger = logging.getLogger(__name__)

WARSAW = ZoneInfo("Europe/Warsaw")


# Canonical fixtures — created once, kept across runs unless fully reset.
# Names use `E2E-Beta-Fixture-` prefix so the per-run cleanup can leave
# them in place.
FIXTURE_CLIENTS: tuple[dict, ...] = (
    {
        "Imię i nazwisko": "E2E-Beta-Fixture-Jan-Kowalski",
        "Miasto": "Warszawa",
        "Adres": "ul. Pułaskiego 12",
        "Telefon": "600100201",
        "Email": "jan-warszawa@example.pl",
        "Produkt": "PV",
        "Status": "Nowy lead",
        "Źródło pozyskania": "Polecenie",
    },
    {
        "Imię i nazwisko": "E2E-Beta-Fixture-Jan-Kowalski",
        "Miasto": "Kraków",
        "Adres": "ul. Wawelska 5",
        "Telefon": "600100202",
        "Email": "jan-krakow@example.pl",
        "Produkt": "Pompa ciepła",
        "Status": "Nowy lead",
        "Źródło pozyskania": "FB",
    },
    {
        "Imię i nazwisko": "E2E-Beta-Fixture-Marek-Nowak",
        "Miasto": "Wyszków",
        "Adres": "ul. Kościuszki 22",
        "Telefon": "600100203",
        "Email": "marek@example.pl",
        "Produkt": "PV",
        "Status": "Spotkanie umówione",
        "Notatki": "Klient zainteresowany dużą instalacją 12kW",
        "Źródło pozyskania": "Strona www",
    },
)


CONFLICT_FIXTURE_TITLE = "E2E-Beta-Fixture-Conflict-Slot"


# ── Seed ───────────────────────────────────────────────────────────────────


async def seed_fixtures(telegram_id: int) -> dict:
    """Idempotent: create FIXTURE_CLIENTS in Sheets + one Calendar conflict
    slot for tomorrow 14:00-15:00. Skips anything that already exists.

    Returns a structured report dict for the MCP tool response.
    """
    user_id = await resolve_user_id(telegram_id)
    if not user_id:
        return {"error": f"no Supabase user found for telegram_id={telegram_id}"}

    seeded_clients: list[str] = []
    skipped_clients: list[str] = []
    failed_clients: list[str] = []

    for client_data in FIXTURE_CLIENTS:
        label = f"{client_data['Imię i nazwisko']}, {client_data['Miasto']}"
        existing = await find_client_row(
            user_id,
            client_data["Imię i nazwisko"],
            client_data["Miasto"],
        )
        if existing:
            skipped_clients.append(label)
            continue
        row_n = await add_client(user_id, dict(client_data))
        if row_n:
            seeded_clients.append(f"{label} → row {row_n}")
        else:
            failed_clients.append(label)

    # Calendar conflict fixture — tomorrow 14:00-15:00 Europe/Warsaw
    tmr = (datetime.now(tz=WARSAW) + timedelta(days=1)).date()
    conflict_start = datetime.combine(tmr, time(14, 0), tzinfo=WARSAW)
    conflict_end = datetime.combine(tmr, time(15, 0), tzinfo=WARSAW)
    # Look in a slightly wider window to detect existing fixture event.
    existing_event = await find_event_by_summary_in_window(
        user_id,
        CONFLICT_FIXTURE_TITLE,
        conflict_start - timedelta(hours=1),
        conflict_end + timedelta(hours=1),
    )
    seeded_events: list[str] = []
    skipped_events: list[str] = []
    failed_events: list[str] = []
    label_event = f"{CONFLICT_FIXTURE_TITLE} {tmr} 14:00-15:00"
    if existing_event:
        skipped_events.append(label_event)
    else:
        e = await create_event(
            user_id,
            title=CONFLICT_FIXTURE_TITLE,
            start=conflict_start,
            end=conflict_end,
            description="E2E test fixture for Calendar conflict scenario.",
        )
        if e:
            seeded_events.append(f"{label_event} → {e.get('id', 'unknown')}")
        else:
            failed_events.append(label_event)

    return {
        "user_id": user_id,
        "seeded_clients": seeded_clients,
        "skipped_clients": skipped_clients,
        "failed_clients": failed_clients,
        "seeded_events": seeded_events,
        "skipped_events": skipped_events,
        "failed_events": failed_events,
    }


# ── Cleanup ────────────────────────────────────────────────────────────────


async def cleanup_synthetic_data(
    telegram_id: int,
    run_id: Optional[str] = None,
    *,
    include_fixtures: bool = False,
) -> dict:
    """Delete `E2E-Beta-*` rows + events.

    Defaults: keep fixtures (`E2E-Beta-Fixture-*`), delete all per-run
    synthetic data. Pass `run_id` to scope the delete to one run.
    Pass `include_fixtures=True` for a full reset (rare — useful when
    fixture clients are stale and need to be reseeded).
    """
    user_id = await resolve_user_id(telegram_id)
    if not user_id:
        return {"error": f"no Supabase user found for telegram_id={telegram_id}"}

    rows = await find_synthetic_rows(
        user_id, run_id=run_id, include_fixtures=include_fixtures,
    )
    sheets_deleted = await delete_synthetic_rows(user_id, rows)

    events = await find_synthetic_events(
        user_id, run_id=run_id, include_fixtures=include_fixtures,
    )
    calendar_deleted = await delete_synthetic_events(user_id, events)

    return {
        "user_id": user_id,
        "run_id": run_id,
        "include_fixtures": include_fixtures,
        "sheets_rows_found": len(rows),
        "sheets_deleted": sheets_deleted,
        "calendar_events_found": len(events),
        "calendar_deleted": calendar_deleted,
    }
