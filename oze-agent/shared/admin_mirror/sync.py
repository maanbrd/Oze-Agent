"""Daily owner-facing operational mirror orchestration."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from bot.config import Config
from shared.admin_mirror.calendar import (
    build_mirror_calendar_event,
    sync_admin_calendar_events,
)
from shared.admin_mirror.data import is_refreshable_user, list_mirror_users, list_table_rows
from shared.admin_mirror.data import log_admin_mirror_run, upsert_admin_metric_snapshot
from shared.admin_mirror.google_io import (
    build_admin_calendar_service,
    build_admin_sheets_service,
    read_tab_values,
    write_workbook,
)
from shared.admin_mirror.rows import (
    AI_USAGE_HEADERS,
    CALENDAR_HEADERS,
    CONTACT_HEADERS,
    OFFER_HEADERS,
    OFFER_SEND_HEADERS,
    PAYMENT_HEADERS,
    USER_HEADERS,
    build_ai_usage_daily_rows,
    build_calendar_row,
    build_contact_row,
    build_offer_rows,
    build_offer_send_rows,
    build_payment_rows,
    build_user_rows,
    count_contacts_by_user,
    merge_contact_snapshot_rows,
)
from shared.admin_dashboard import build_admin_metric_snapshot, build_owner_dashboard_payload
from shared.google_calendar import get_events_for_range_or_raise
from shared.google_sheets import get_all_clients_or_raise

logger = logging.getLogger(__name__)

CONTACTS_TAB = "Kontakty"
USERS_TAB = "Użytkownicy"
AI_USAGE_TAB = "AI usage dzienny"
PAYMENTS_TAB = "Płatności"
OFFERS_TAB = "Oferty"
OFFER_SENDS_TAB = "Wysyłki ofert"
CALENDAR_TAB = "Kalendarz"
FUTURE_EVENT_HORIZON_DAYS = 365


def _config_errors() -> list[str]:
    missing = []
    for name in (
        "ADMIN_MIRROR_GOOGLE_USER_ID",
        "ADMIN_MIRROR_SPREADSHEET_ID",
        "ADMIN_MIRROR_CALENDAR_ID",
    ):
        if not getattr(Config, name, ""):
            missing.append(name)
    return missing


def _table(headers: list[str], rows: list[list]) -> list[list]:
    return [headers, *rows]


async def _fetch_active_user_contacts(user: dict, synced_at: str) -> list[list]:
    clients = await get_all_clients_or_raise(user["id"])
    return [build_contact_row(user, client, synced_at) for client in clients]


async def _fetch_active_user_events(user: dict, now: datetime) -> tuple[list[list], list[dict]]:
    end = now + timedelta(days=FUTURE_EVENT_HORIZON_DAYS)
    events = await get_events_for_range_or_raise(user["id"], now, end)
    calendar_rows = [build_calendar_row(user, event) for event in events]
    mirror_events = [build_mirror_calendar_event(user, event) for event in events]
    return calendar_rows, mirror_events


async def run_admin_mirror(
    *,
    force: bool = False,
    now: datetime | None = None,
    database_client=None,
    sheets_service=None,
    calendar_service=None,
) -> dict:
    """Run the full admin mirror sync.

    `force=True` is intended for controlled manual smoke runs; the scheduler
    uses the env flag.
    """
    if not force and not Config.ADMIN_MIRROR_ENABLED:
        return {"ok": True, "skipped": True, "reason": "disabled"}

    missing = _config_errors()
    if missing:
        logger.error("admin_mirror: missing env config: %s", missing)
        return {"ok": False, "skipped": True, "reason": "missing_config", "missing": missing}

    now = now or datetime.now(tz=timezone.utc)
    run_started_at = now.isoformat()
    synced_at = now.isoformat()
    users = list_mirror_users(database_client)
    active_users = [user for user in users if is_refreshable_user(user)]
    canceled_users = [user for user in users if user.get("subscription_status") == "canceled"]
    canceled_users_by_id = {str(user["id"]): user for user in canceled_users}

    sheets_service = sheets_service or build_admin_sheets_service(Config.ADMIN_MIRROR_GOOGLE_USER_ID)
    calendar_service = calendar_service or build_admin_calendar_service(Config.ADMIN_MIRROR_GOOGLE_USER_ID)
    if not sheets_service or not calendar_service:
        logger.error("admin_mirror: missing admin Google credentials")
        return {"ok": False, "skipped": True, "reason": "admin_google_credentials"}

    existing_contacts = await read_tab_values(
        sheets_service,
        Config.ADMIN_MIRROR_SPREADSHEET_ID,
        CONTACTS_TAB,
    )

    fresh_contact_rows: list[list] = []
    calendar_rows: list[list] = []
    mirror_events: list[dict] = []
    contact_failed_users: dict[str, dict] = {}
    calendar_failed_user_ids: set[str] = set()
    errors: list[dict] = []

    for user in active_users:
        user_id = str(user["id"])
        if user.get("google_sheets_id"):
            try:
                fresh_contact_rows.extend(await _fetch_active_user_contacts(user, synced_at))
            except Exception as exc:
                contact_failed_users[user_id] = user
                errors.append({"user_id": user_id, "area": "contacts", "error": str(exc)})
                logger.exception("admin_mirror.contacts(%s): %s", user_id, exc)

        if user.get("google_calendar_id"):
            try:
                rows, events = await _fetch_active_user_events(user, now)
                calendar_rows.extend(rows)
                mirror_events.extend(events)
            except Exception as exc:
                calendar_failed_user_ids.add(user_id)
                errors.append({"user_id": user_id, "area": "calendar", "error": str(exc)})
                logger.exception("admin_mirror.calendar(%s): %s", user_id, exc)

    active_user_ids = {str(user["id"]) for user in active_users}
    contact_rows = merge_contact_snapshot_rows(
        existing_values=existing_contacts,
        fresh_active_rows=fresh_contact_rows,
        active_user_ids=active_user_ids,
        canceled_users_by_id=canceled_users_by_id,
        preserved_users_by_id=contact_failed_users,
    )
    contact_counts = count_contacts_by_user(contact_rows)

    offers = list_table_rows("offer_templates", database_client)
    offer_attempts = list_table_rows("offer_send_attempts", database_client)
    interactions = list_table_rows("interaction_log", database_client)
    payment_history = list_table_rows("payment_history", database_client)

    tabs = {
        CONTACTS_TAB: _table(CONTACT_HEADERS, contact_rows),
        USERS_TAB: _table(USER_HEADERS, build_user_rows(users, contact_counts, synced_at)),
        AI_USAGE_TAB: _table(AI_USAGE_HEADERS, build_ai_usage_daily_rows(users, interactions)),
        PAYMENTS_TAB: _table(PAYMENT_HEADERS, build_payment_rows(users, payment_history)),
        OFFERS_TAB: _table(OFFER_HEADERS, build_offer_rows(users, offers)),
        OFFER_SENDS_TAB: _table(OFFER_SEND_HEADERS, build_offer_send_rows(users, offer_attempts)),
        CALENDAR_TAB: _table(CALENDAR_HEADERS, calendar_rows),
    }
    await write_workbook(sheets_service, Config.ADMIN_MIRROR_SPREADSHEET_ID, tabs)

    calendar_result = await asyncio.to_thread(
        sync_admin_calendar_events,
        calendar_service,
        Config.ADMIN_MIRROR_CALENDAR_ID,
        mirror_events,
        now=now,
        preserve_source_user_ids=calendar_failed_user_ids,
    )

    result = {
        "ok": True,
        "skipped": False,
        "run_started_at": run_started_at,
        "run_finished_at": now.isoformat(),
        "users": len(users),
        "active_users": len(active_users),
        "canceled_users": len(canceled_users),
        "contacts": len(contact_rows),
        "calendar_events": len(mirror_events),
        "calendar_mirror": calendar_result,
        "errors": errors,
    }
    _persist_admin_run_and_snapshot(
        result=result,
        users=list_table_rows("users", database_client),
        interactions=interactions,
        payment_history=payment_history,
        offers=offers,
        offer_attempts=offer_attempts,
        contact_rows=contact_rows,
        calendar_rows=calendar_rows,
        now=now,
        database_client=database_client,
    )
    logger.info("admin_mirror.run %s", result)
    return result


def _persist_admin_run_and_snapshot(
    *,
    result: dict,
    users: list[dict],
    interactions: list[dict],
    payment_history: list[dict],
    offers: list[dict],
    offer_attempts: list[dict],
    contact_rows: list[list],
    calendar_rows: list[list],
    now: datetime,
    database_client=None,
) -> None:
    try:
        log_admin_mirror_run(
            {
                "run_started_at": result.get("run_started_at"),
                "run_finished_at": result.get("run_finished_at"),
                "ok": result.get("ok", False),
                "skipped": result.get("skipped", False),
                "reason": result.get("reason", ""),
                "users_count": result.get("users", 0),
                "active_users_count": result.get("active_users", 0),
                "canceled_users_count": result.get("canceled_users", 0),
                "contacts_count": result.get("contacts", 0),
                "calendar_events_count": result.get("calendar_events", 0),
                "errors": result.get("errors", []),
                "calendar_mirror": result.get("calendar_mirror", {}),
            },
            database_client,
        )
        payload = build_owner_dashboard_payload(
            users=users,
            interactions=interactions,
            payment_history=payment_history,
            offers=offers,
            offer_attempts=offer_attempts,
            contact_rows=_rows_to_dicts(CONTACT_HEADERS, contact_rows),
            calendar_rows=_rows_to_dicts(CALENDAR_HEADERS, calendar_rows),
            monthly_subscription_pln=Config.MONTHLY_SUBSCRIPTION_PLN,
            admin_usd_pln_rate=Config.ADMIN_USD_PLN_RATE,
            now=now,
        )
        upsert_admin_metric_snapshot(
            build_admin_metric_snapshot(payload, now.date()),
            database_client,
        )
    except Exception as exc:
        logger.warning("admin_mirror.snapshot_log_failed: %s", exc)


def _rows_to_dicts(headers: list[str], rows: list[list]) -> list[dict]:
    mapped = []
    for raw_row in rows:
        mapped.append({
            header: raw_row[index] if index < len(raw_row) else ""
            for index, header in enumerate(headers)
        })
    return mapped
