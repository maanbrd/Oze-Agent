"""Owner-facing admin dashboard aggregation.

This module builds aggregate metrics only. Full CRM rows stay in the owner
mirror Sheets/Calendar layer and are not returned by the admin API.
"""

from __future__ import annotations

from collections import Counter, defaultdict
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
    monthly_subscription_pln: int,
    owner_spreadsheet_id: str = "",
    owner_calendar_id: str = "",
) -> dict[str, Any]:
    contact_rows = contact_rows or []
    calendar_rows = calendar_rows or []
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

    mrr_pln = len(active_users) * monthly_subscription_pln
    pending_payment_pln = len(pending_users) * monthly_subscription_pln
    ai_cost_usd = round(sum(_float(row.get("cost_usd")) for row in interactions), 4)

    return {
        "business": {
            "mrr_pln": mrr_pln,
            "active_paid_accounts": len(active_users),
            "pending_payment_accounts": len(pending_users),
            "pending_payment_pln": pending_payment_pln,
            "canceled_accounts": len(canceled_users),
            "ai_cost_usd_month": ai_cost_usd,
            "estimated_gross_margin_pln": mrr_pln,
            "active_7d_accounts": _count_recently_active_users(interactions, visible_users),
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
    })


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
