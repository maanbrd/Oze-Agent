"""Owner-facing admin dashboard aggregation.

This module builds aggregate metrics only. Full CRM rows stay in the owner
mirror Sheets/Calendar layer and are not returned by the admin API.
"""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta, timezone
from typing import Any


FUNNEL_LABELS = (
    "Rejestracja",
    "Płatność",
    "Onboarding",
    "Google podpięte",
    "Telegram aktywny",
    "Pierwsze kontakty",
    "Pierwsza oferta",
)


def parse_owner_admin_emails(raw: str | None) -> set[str]:
    return {
        item.strip().lower()
        for item in (raw or "").split(",")
        if item.strip()
    }


def is_owner_admin_email(email: str | None, raw_owner_emails: str | None) -> bool:
    if not email:
        return False
    return email.strip().lower() in parse_owner_admin_emails(raw_owner_emails)


def build_owner_dashboard_payload(
    *,
    users: list[dict[str, Any]],
    interactions: list[dict[str, Any]],
    payment_history: list[dict[str, Any]],
    offers: list[dict[str, Any]],
    offer_attempts: list[dict[str, Any]],
    contact_rows: list[dict[str, Any]] | None = None,
    calendar_rows: list[dict[str, Any]] | None = None,
    metric_snapshots: list[dict[str, Any]] | None = None,
    mirror_runs: list[dict[str, Any]] | None = None,
    monthly_subscription_pln: int,
    admin_usd_pln_rate: float = 4.0,
    owner_spreadsheet_id: str = "",
    owner_calendar_id: str = "",
    now: datetime | None = None,
) -> dict[str, Any]:
    now = _aware_utc(now)
    contact_rows = contact_rows or []
    calendar_rows = calendar_rows or []
    metric_snapshots = metric_snapshots or []
    mirror_runs = mirror_runs or []
    visible_users = [
        user for user in users
        if not user.get("is_deleted") and not user.get("is_suspended")
    ]
    active_users = [
        user for user in visible_users
        if _text(user.get("subscription_status")) == "active"
    ]
    pending_users = [
        user for user in visible_users
        if _text(user.get("subscription_status")) == "pending_payment"
    ]
    canceled_users = [
        user for user in visible_users
        if _text(user.get("subscription_status")) == "canceled"
    ]
    active_user_ids = {_text(user.get("id")) for user in active_users}
    users_with_contacts = {
        _text(row.get("User ID") or row.get("user_id"))
        for row in contact_rows
        if _text(row.get("User ID") or row.get("user_id"))
    }
    users_with_offers = {
        _text(offer.get("user_id"))
        for offer in offers
        if _text(offer.get("user_id"))
    } | {
        _text(attempt.get("user_id"))
        for attempt in offer_attempts
        if _text(attempt.get("user_id"))
    }

    billing = _build_billing_metrics(
        active_users=active_users,
        pending_users=pending_users,
        payment_history=payment_history,
        monthly_subscription_pln=monthly_subscription_pln,
        now=now,
    )
    ai_cost_usd = round(
        sum(
            _float(row.get("cost_usd"))
            for row in interactions
            if _in_current_month(row.get("created_at"), now)
        ),
        4,
    )
    ai_cost_pln = round(ai_cost_usd * admin_usd_pln_rate, 2)
    gross_margin_after_ai = round(billing["mrr_pln"] - ai_cost_pln, 2)
    data_quality = {
        "mrr_pln": billing["mrr_quality"],
        "revenue_pln_month": billing["revenue_quality"],
        "pending_payment_pln": billing["pending_quality"],
        "ai_cost_usd_month": "real",
        "ai_cost_pln_month": "estimated" if ai_cost_usd else "missing",
        "gross_margin_after_ai_pln": (
            "estimated"
            if billing["mrr_quality"] != "missing" and admin_usd_pln_rate > 0
            else "missing"
        ),
        "active_7d_accounts": "real",
    }

    return {
        "business": {
            "mrr_pln": billing["mrr_pln"],
            "revenue_pln_month": billing["revenue_pln_month"],
            "active_paid_accounts": len(active_users),
            "pending_payment_accounts": len(pending_users),
            "pending_payment_pln": billing["pending_payment_pln"],
            "canceled_accounts": len(canceled_users),
            "ai_cost_usd_month": ai_cost_usd,
            "ai_cost_pln_month": ai_cost_pln,
            "estimated_gross_margin_pln": gross_margin_after_ai,
            "gross_margin_after_ai_pln": gross_margin_after_ai,
            "active_7d_accounts": _count_recently_active_users(
                interactions,
                visible_users,
                since=now - timedelta(days=7),
            ),
        },
        "funnel": _build_funnel(
            visible_users=visible_users,
            active_users=active_users,
            users_with_contacts=users_with_contacts,
            users_with_offers=users_with_offers,
        ),
        "oze": _build_oze_metrics(offers, contact_rows),
        "operations": _build_operations_metrics(
            users=visible_users,
            interactions=interactions,
            calendar_rows=calendar_rows,
            payment_history=payment_history,
        ),
        "trends": _build_trends(metric_snapshots, now),
        "sync": _build_sync_status(mirror_runs),
        "data_quality": data_quality,
        "links": {
            "sheets_url": (
                f"https://docs.google.com/spreadsheets/d/{owner_spreadsheet_id}/edit"
                if owner_spreadsheet_id
                else None
            ),
            "calendar_url": (
                "https://calendar.google.com/calendar/u/0/r?cid="
                f"{owner_calendar_id}"
                if owner_calendar_id
                else None
            ),
        },
    }


def build_admin_metric_snapshot(payload: dict[str, Any], snapshot_date: date | str) -> dict[str, Any]:
    if isinstance(snapshot_date, date):
        snapshot_date_value = snapshot_date.isoformat()
    else:
        snapshot_date_value = str(snapshot_date)
    business = payload.get("business", {})
    return {
        "snapshot_date": snapshot_date_value,
        "payload": {
            "business": business,
            "data_quality": payload.get("data_quality", {}),
            "sync": payload.get("sync", {}),
        },
        "mrr_pln": business.get("mrr_pln", 0),
        "revenue_pln_month": business.get("revenue_pln_month", 0),
        "ai_cost_usd_month": business.get("ai_cost_usd_month", 0),
        "ai_cost_pln_month": business.get("ai_cost_pln_month", 0),
        "gross_margin_after_ai_pln": business.get("gross_margin_after_ai_pln", 0),
        "active_paid_accounts": business.get("active_paid_accounts", 0),
        "pending_payment_accounts": business.get("pending_payment_accounts", 0),
        "active_7d_accounts": business.get("active_7d_accounts", 0),
    }


def _build_funnel(
    *,
    visible_users: list[dict[str, Any]],
    active_users: list[dict[str, Any]],
    users_with_contacts: set[str],
    users_with_offers: set[str],
) -> list[dict[str, Any]]:
    total = len(visible_users)
    paid_ids = {_text(user.get("id")) for user in active_users}
    onboarding_ids = {
        _text(user.get("id"))
        for user in visible_users
        if user.get("onboarding_completed")
    }
    google_ids = {
        _text(user.get("id"))
        for user in visible_users
        if user.get("google_sheets_id") and user.get("google_calendar_id")
    }
    telegram_ids = {
        _text(user.get("id"))
        for user in visible_users
        if user.get("telegram_id")
    }
    counts = [
        total,
        len(paid_ids),
        len(onboarding_ids),
        len(google_ids),
        len(telegram_ids),
        len(users_with_contacts),
        len(users_with_offers),
    ]
    return [
        {
            "label": label,
            "count": count,
            "conversion_pct": _percent(count, total),
        }
        for label, count in zip(FUNNEL_LABELS, counts, strict=True)
    ]


def _build_oze_metrics(
    offers: list[dict[str, Any]],
    contact_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    prices = [_float(offer.get("price_net_pln")) for offer in offers]
    nonzero_prices = [price for price in prices if price > 0]
    offer_type_counts = Counter(
        _text(offer.get("product_type") or offer.get("type") or "Nieznany")
        for offer in offers
    )
    city_counts = Counter(
        _text(row.get("Miasto") or row.get("city"))
        for row in contact_rows
        if _text(row.get("Miasto") or row.get("city"))
    )
    status_counts = Counter(
        _text(row.get("Status") or row.get("status") or "Brak statusu")
        for row in contact_rows
    )
    component_counts = _component_counts(offers)

    return {
        "offers_total": len(offers),
        "average_offer_price_pln": (
            round(sum(nonzero_prices) / len(nonzero_prices))
            if nonzero_prices
            else 0
        ),
        "total_pv_kwp": round(sum(_float(offer.get("pv_power_kwp")) for offer in offers), 2),
        "total_storage_kwh": round(
            sum(_float(offer.get("storage_capacity_kwh")) for offer in offers),
            2,
        ),
        "popular_offer_types": _counter_rows(offer_type_counts, len(offers)),
        "top_cities": _counter_rows(city_counts, len(contact_rows), limit=8),
        "crm_statuses": _counter_rows(status_counts, len(contact_rows), limit=8),
        "components": _counter_rows(component_counts, len(offers), limit=10),
    }


def _build_billing_metrics(
    *,
    active_users: list[dict[str, Any]],
    pending_users: list[dict[str, Any]],
    payment_history: list[dict[str, Any]],
    monthly_subscription_pln: int,
    now: datetime,
) -> dict[str, Any]:
    successful_by_user = _latest_payment_by_user(
        payment_history,
        statuses={"paid", "succeeded", "success", "active", "complete", "completed"},
    )
    failed_by_user = _latest_payment_by_user(
        payment_history,
        statuses={"failed", "past_due", "open", "unpaid", "requires_payment_method"},
    )

    mrr_pln = 0.0
    active_missing_real_payment = False
    for user in active_users:
        user_id = _text(user.get("id"))
        payment = successful_by_user.get(user_id)
        amount = _float(payment.get("amount_pln")) if payment else 0.0
        if amount > 0:
            mrr_pln += amount
        else:
            mrr_pln += monthly_subscription_pln
            active_missing_real_payment = True

    pending_payment_pln = 0.0
    pending_missing_real_payment = False
    for user in pending_users:
        user_id = _text(user.get("id"))
        payment = failed_by_user.get(user_id)
        amount = _float(payment.get("amount_pln")) if payment else 0.0
        if amount > 0:
            pending_payment_pln += amount
        else:
            pending_payment_pln += monthly_subscription_pln
            pending_missing_real_payment = True

    revenue_month = round(
        sum(
            _float(row.get("amount_pln"))
            for row in payment_history
            if _payment_is_success(row) and _in_current_month(row.get("created_at"), now)
        ),
        2,
    )
    return {
        "mrr_pln": round(mrr_pln, 2),
        "pending_payment_pln": round(pending_payment_pln, 2),
        "revenue_pln_month": revenue_month,
        "mrr_quality": (
            "missing"
            if not active_users
            else "estimated"
            if active_missing_real_payment
            else "real"
        ),
        "pending_quality": (
            "missing"
            if not pending_users
            else "estimated"
            if pending_missing_real_payment
            else "real"
        ),
        "revenue_quality": "real" if revenue_month > 0 else "missing",
    }


def _build_operations_metrics(
    *,
    users: list[dict[str, Any]],
    interactions: list[dict[str, Any]],
    calendar_rows: list[dict[str, Any]],
    payment_history: list[dict[str, Any]],
) -> dict[str, Any]:
    total = len(users)
    google_sheets = sum(1 for user in users if user.get("google_sheets_id"))
    google_calendar = sum(1 for user in users if user.get("google_calendar_id"))
    telegram = sum(1 for user in users if user.get("telegram_id"))
    pending_payment = sum(
        1 for user in users
        if _text(user.get("subscription_status")) == "pending_payment"
    )

    return {
        "system_status": "brak danych" if total == 0 else "OK",
        "integrations": [
            {"label": "Google Sheets", "ok": google_sheets, "total": total},
            {"label": "Google Calendar", "ok": google_calendar, "total": total},
            {"label": "Telegram", "ok": telegram, "total": total},
            {"label": "Płatności", "ok": total - pending_payment, "total": total},
        ],
        "attention": [
            {
                "label": "Pending payment",
                "count": pending_payment,
                "detail": "konta do odzyskania",
            },
            {
                "label": "Zdarzenia AI",
                "count": len(interactions),
                "detail": "interakcje w logu",
            },
            {
                "label": "Przyszłe spotkania",
                "count": len(calendar_rows),
                "detail": "w mirror calendar",
            },
            {
                "label": "Historia płatności",
                "count": len(payment_history),
                "detail": "zdarzenia rozliczeń",
            },
        ],
    }


def _component_counts(offers: list[dict[str, Any]]) -> Counter:
    counts: Counter = Counter()
    for offer in offers:
        if offer.get("pv_power_kwp") or offer.get("panel_brand") or offer.get("panel_model"):
            counts["Panele fotowoltaiczne"] += 1
        if offer.get("inverter_brand") or offer.get("inverter_model"):
            counts["Inwerter"] += 1
        if (
            offer.get("storage_capacity_kwh")
            or offer.get("storage_brand")
            or offer.get("storage_model")
        ):
            counts["Magazyn energii"] += 1
        if offer.get("construction"):
            counts["Konstrukcja"] += 1
        if offer.get("protections_ac_dc"):
            counts["Zabezpieczenia"] += 1
        if offer.get("installation"):
            counts["Montaż"] += 1
        if offer.get("monitoring_ems"):
            counts["Monitoring"] += 1
    return counts


def _counter_rows(counter: Counter, denominator: int, limit: int = 5) -> list[dict[str, Any]]:
    return [
        {
            "label": label,
            "count": count,
            "share_pct": _percent(count, denominator),
        }
        for label, count in counter.most_common(limit)
    ]


def _count_recently_active_users(
    interactions: list[dict[str, Any]],
    users: list[dict[str, Any]],
    *,
    since: datetime | None = None,
) -> int:
    telegram_to_user = {
        _text(user.get("telegram_id")): _text(user.get("id"))
        for user in users
        if user.get("telegram_id")
    }
    return len({
        telegram_to_user[_text(row.get("telegram_id"))]
        for row in interactions
        if _text(row.get("telegram_id")) in telegram_to_user
        and (since is None or (_parse_datetime(row.get("created_at")) or datetime.min.replace(tzinfo=timezone.utc)) >= since)
    })


def _build_trends(snapshots: list[dict[str, Any]], now: datetime) -> list[dict[str, Any]]:
    cutoff = now.date() - timedelta(days=183)
    rows = []
    for snapshot in snapshots:
        raw_date = _text(snapshot.get("snapshot_date") or snapshot.get("date"))
        parsed_date = _parse_date(raw_date)
        if not parsed_date or parsed_date < cutoff:
            continue
        rows.append({
            "date": parsed_date.isoformat(),
            "mrr_pln": _float(snapshot.get("mrr_pln")),
            "revenue_pln_month": _float(snapshot.get("revenue_pln_month")),
            "ai_cost_usd_month": _float(snapshot.get("ai_cost_usd_month")),
            "ai_cost_pln_month": _float(snapshot.get("ai_cost_pln_month")),
            "gross_margin_after_ai_pln": _float(snapshot.get("gross_margin_after_ai_pln")),
            "active_paid_accounts": int(_float(snapshot.get("active_paid_accounts"))),
            "pending_payment_accounts": int(_float(snapshot.get("pending_payment_accounts"))),
            "active_7d_accounts": int(_float(snapshot.get("active_7d_accounts"))),
        })
    return sorted(rows, key=lambda item: item["date"])


def _build_sync_status(runs: list[dict[str, Any]]) -> dict[str, Any]:
    if not runs:
        return {
            "last_run_at": None,
            "ok": None,
            "skipped": None,
            "contacts": 0,
            "calendar_events": 0,
            "errors": [],
        }
    latest = sorted(
        runs,
        key=lambda row: _parse_datetime(row.get("run_finished_at") or row.get("created_at")) or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )[0]
    return {
        "last_run_at": _text(latest.get("run_finished_at") or latest.get("created_at")) or None,
        "ok": bool(latest.get("ok")),
        "skipped": bool(latest.get("skipped")),
        "contacts": int(_float(latest.get("contacts_count") or latest.get("contacts"))),
        "calendar_events": int(_float(latest.get("calendar_events_count") or latest.get("calendar_events"))),
        "errors": latest.get("errors") if isinstance(latest.get("errors"), list) else [],
    }


def _latest_payment_by_user(
    payment_history: list[dict[str, Any]],
    *,
    statuses: set[str],
) -> dict[str, dict[str, Any]]:
    rows_by_user: dict[str, dict[str, Any]] = {}
    for row in payment_history:
        user_id = _text(row.get("user_id"))
        if not user_id or _text(row.get("status")).lower() not in statuses:
            continue
        existing = rows_by_user.get(user_id)
        current_created = _parse_datetime(row.get("created_at")) or datetime.min.replace(tzinfo=timezone.utc)
        existing_created = (
            _parse_datetime(existing.get("created_at")) if existing else None
        ) or datetime.min.replace(tzinfo=timezone.utc)
        if existing is None or current_created >= existing_created:
            rows_by_user[user_id] = row
    return rows_by_user


def _payment_is_success(row: dict[str, Any]) -> bool:
    return _text(row.get("status")).lower() in {
        "paid",
        "succeeded",
        "success",
        "active",
        "complete",
        "completed",
    }


def _in_current_month(value: Any, now: datetime) -> bool:
    parsed = _parse_datetime(value)
    if not parsed:
        return False
    parsed = _aware_utc(parsed)
    month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    if now.month == 12:
        next_month = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        next_month = datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)
    return month_start <= parsed < next_month


def _parse_datetime(value: Any) -> datetime | None:
    raw = _text(value)
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    return _aware_utc(parsed)


def _parse_date(value: Any) -> date | None:
    raw = _text(value)
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def _aware_utc(value: datetime | None) -> datetime:
    value = value or datetime.now(tz=timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _percent(count: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round((count / denominator) * 100, 1)


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _float(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
