"""Pure row builders for the owner-facing Google Sheets mirror."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Iterable

from shared.google_sheets import DEFAULT_COLUMNS

OWNER_CONTACT_COLUMNS = [
    "Użytkownik",
    "Email użytkownika",
    "Telefon użytkownika",
    "Status subskrypcji",
    "User ID",
    "Źródłowy arkusz",
    "Źródłowy wiersz",
    "Data syncu",
]

CONTACT_HEADERS = OWNER_CONTACT_COLUMNS + DEFAULT_COLUMNS

USER_HEADERS = [
    "Użytkownik",
    "Email",
    "Telefon",
    "User ID",
    "Telegram ID",
    "Status subskrypcji",
    "Plan",
    "Aktywacja opłacona",
    "Okres do",
    "Onboarding ukończony",
    "Google Sheets ID",
    "Google Calendar ID",
    "Google Drive Folder ID",
    "Liczba kontaktów",
    "Data rejestracji",
    "Ostatnia aktualizacja",
    "Data syncu",
]

AI_USAGE_HEADERS = [
    "Data",
    "Użytkownik",
    "Email użytkownika",
    "User ID",
    "Telegram ID",
    "Interakcje",
    "Tokeny input",
    "Tokeny output",
    "Koszt USD",
    "Modele",
    "Typy akcji",
]

PAYMENT_HEADERS = [
    "Użytkownik",
    "Email użytkownika",
    "User ID",
    "Status subskrypcji",
    "Plan",
    "Okres do",
    "Stripe customer ID",
    "Stripe subscription ID",
    "Stripe checkout session ID",
    "Kwota PLN",
    "Typ",
    "Status płatności",
    "Stripe event ID",
    "Stripe invoice ID",
    "Waluta",
    "Data płatności",
]

OFFER_HEADERS = [
    "Użytkownik",
    "Email użytkownika",
    "User ID",
    "Oferta ID",
    "Oferta",
    "Status",
    "Typ produktu",
    "Cena netto PLN",
    "VAT",
    "Dotacja PLN",
    "PV kWp",
    "Magazyn kWh",
    "Panel",
    "Inwerter",
    "Magazyn",
    "Konstrukcja",
    "Zabezpieczenia",
    "Montaż",
    "Monitoring / EMS",
    "Gwarancja",
    "Warunki płatności",
    "Termin realizacji",
    "Ważność",
    "Sort order",
    "Utworzono",
    "Zaktualizowano",
]

OFFER_SEND_HEADERS = [
    "Użytkownik",
    "Email użytkownika",
    "User ID",
    "Próba ID",
    "Klient",
    "Miasto",
    "Wiersz klienta",
    "Odbiorcy",
    "Niepoprawni odbiorcy",
    "Oferta ID",
    "Oferta",
    "Numer oferty",
    "Status",
    "Gmail message ID",
    "Błąd",
    "Wysłano",
    "Utworzono",
    "Zaktualizowano",
]

CALENDAR_HEADERS = [
    "Użytkownik",
    "Email użytkownika",
    "User ID",
    "Źródłowy kalendarz",
    "Źródłowe wydarzenie ID",
    "Tytuł",
    "Typ",
    "Start",
    "Koniec",
    "Lokalizacja",
    "Opis",
]


def _text(value) -> str:
    return "" if value is None else str(value)


def _date_key(value: str | None) -> str:
    if not value:
        return ""
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return str(value)[:10]


def _user_name(user: dict) -> str:
    return _text(user.get("name") or user.get("email") or user.get("id"))


def _owner_prefix(user: dict) -> list:
    return [
        _user_name(user),
        _text(user.get("email")),
        _text(user.get("phone")),
        _text(user.get("subscription_status")),
        _text(user.get("id")),
    ]


def _brand_model(brand, model) -> str:
    return " ".join(part for part in [_text(brand).strip(), _text(model).strip()] if part)


def _join_values(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(_text(item) for item in value if _text(item))
    return _text(value)


def _user_maps(users: Iterable[dict]) -> tuple[dict[str, dict], dict[int, dict]]:
    by_id = {_text(user.get("id")): user for user in users if user.get("id")}
    by_telegram = {
        int(user["telegram_id"]): user
        for user in users
        if user.get("telegram_id") is not None
    }
    return by_id, by_telegram


def build_contact_row(user: dict, client: dict, synced_at: str) -> list:
    return [
        *_owner_prefix(user),
        _text(user.get("google_sheets_id")),
        client.get("_row", ""),
        synced_at,
        *[_text(client.get(column)) for column in DEFAULT_COLUMNS],
    ]


def merge_contact_snapshot_rows(
    *,
    existing_values: list[list],
    fresh_active_rows: list[list],
    active_user_ids: set[str],
    canceled_users_by_id: dict[str, dict],
    preserved_users_by_id: dict[str, dict] | None = None,
) -> list[list]:
    """Replace fresh active users and keep last snapshots for canceled/failing users."""
    preserved_users_by_id = preserved_users_by_id or {}
    preserve_ids = set(canceled_users_by_id) | set(preserved_users_by_id)
    user_id_idx = CONTACT_HEADERS.index("User ID")
    status_idx = CONTACT_HEADERS.index("Status subskrypcji")

    out = list(fresh_active_rows)
    if not existing_values or existing_values[0] != CONTACT_HEADERS:
        return out

    for row in existing_values[1:]:
        padded = row + [""] * (len(CONTACT_HEADERS) - len(row))
        user_id = _text(padded[user_id_idx])
        if user_id not in preserve_ids:
            continue
        if user_id in active_user_ids and user_id not in preserved_users_by_id:
            continue

        user = canceled_users_by_id.get(user_id) or preserved_users_by_id.get(user_id) or {}
        padded[status_idx] = _text(user.get("subscription_status")) or padded[status_idx]
        out.append(padded[:len(CONTACT_HEADERS)])
    return out


def build_user_rows(users: list[dict], contact_counts: dict[str, int], synced_at: str) -> list[list]:
    rows = []
    for user in sorted(users, key=lambda item: (_user_name(item).lower(), _text(item.get("email")).lower())):
        rows.append([
            _user_name(user),
            _text(user.get("email")),
            _text(user.get("phone")),
            _text(user.get("id")),
            user.get("telegram_id") or "",
            _text(user.get("subscription_status")),
            _text(user.get("subscription_plan")),
            bool(user.get("activation_paid")),
            _text(user.get("subscription_current_period_end") or user.get("subscription_expires_at")),
            bool(user.get("onboarding_completed")),
            _text(user.get("google_sheets_id")),
            _text(user.get("google_calendar_id")),
            _text(user.get("google_drive_folder_id")),
            contact_counts.get(_text(user.get("id")), 0),
            _text(user.get("created_at")),
            _text(user.get("updated_at")),
            synced_at,
        ])
    return rows


def build_ai_usage_daily_rows(users: list[dict], interactions: list[dict]) -> list[list]:
    _, users_by_telegram = _user_maps(users)
    grouped: dict[tuple[str, int], dict] = {}

    for item in interactions:
        telegram_id = item.get("telegram_id")
        if telegram_id is None:
            continue
        try:
            telegram_id_int = int(telegram_id)
        except (TypeError, ValueError):
            continue
        user = users_by_telegram.get(telegram_id_int)
        if not user:
            continue
        day = _date_key(item.get("created_at"))
        if not day:
            continue
        bucket = grouped.setdefault(
            (day, telegram_id_int),
            {
                "user": user,
                "count": 0,
                "tokens_in": 0,
                "tokens_out": 0,
                "cost": 0.0,
                "models": set(),
                "types": set(),
            },
        )
        bucket["count"] += 1
        bucket["tokens_in"] += int(item.get("tokens_in") or 0)
        bucket["tokens_out"] += int(item.get("tokens_out") or 0)
        bucket["cost"] += float(item.get("cost_usd") or 0.0)
        if item.get("model_used"):
            bucket["models"].add(_text(item.get("model_used")))
        if item.get("interaction_type"):
            bucket["types"].add(_text(item.get("interaction_type")))

    rows = []
    for (day, telegram_id), bucket in sorted(grouped.items()):
        user = bucket["user"]
        rows.append([
            day,
            _user_name(user),
            _text(user.get("email")),
            _text(user.get("id")),
            telegram_id,
            bucket["count"],
            bucket["tokens_in"],
            bucket["tokens_out"],
            round(bucket["cost"], 6),
            ", ".join(sorted(bucket["models"])),
            ", ".join(sorted(bucket["types"])),
        ])
    return rows


def build_payment_rows(users: list[dict], payment_history: list[dict]) -> list[list]:
    users_by_id, _ = _user_maps(users)
    history_by_user: dict[str, list[dict]] = defaultdict(list)
    for payment in payment_history:
        user_id = _text(payment.get("user_id"))
        if user_id in users_by_id:
            history_by_user[user_id].append(payment)

    rows = []
    for user in sorted(users, key=lambda item: (_user_name(item).lower(), _text(item.get("email")).lower())):
        history = history_by_user.get(_text(user.get("id"))) or [{}]
        for payment in history:
            rows.append([
                _user_name(user),
                _text(user.get("email")),
                _text(user.get("id")),
                _text(user.get("subscription_status")),
                _text(user.get("subscription_plan")),
                _text(user.get("subscription_current_period_end") or user.get("subscription_expires_at")),
                _text(user.get("stripe_customer_id")),
                _text(user.get("stripe_subscription_id")),
                _text(user.get("stripe_checkout_session_id")),
                payment.get("amount_pln") or "",
                _text(payment.get("type")),
                _text(payment.get("status")),
                _text(payment.get("stripe_event_id")),
                _text(payment.get("stripe_invoice_id")),
                _text(payment.get("currency")),
                _text(payment.get("created_at")),
            ])
    return rows


def build_offer_rows(users: list[dict], offers: list[dict]) -> list[list]:
    users_by_id, _ = _user_maps(users)
    rows = []
    for offer in sorted(offers, key=lambda item: (_text(item.get("user_id")), _text(item.get("name")).lower())):
        user = users_by_id.get(_text(offer.get("user_id")))
        if not user:
            continue
        rows.append([
            _user_name(user),
            _text(user.get("email")),
            _text(user.get("id")),
            _text(offer.get("id")),
            _text(offer.get("name")),
            _text(offer.get("status")),
            _text(offer.get("product_type")),
            offer.get("price_net_pln") or "",
            offer.get("vat_rate") or "",
            offer.get("subsidy_amount_pln") or "",
            offer.get("pv_power_kwp") or "",
            offer.get("storage_capacity_kwh") or "",
            _brand_model(offer.get("panel_brand"), offer.get("panel_model")),
            _brand_model(offer.get("inverter_brand"), offer.get("inverter_model")),
            _brand_model(offer.get("storage_brand"), offer.get("storage_model")),
            _text(offer.get("construction")),
            _text(offer.get("protections_ac_dc")),
            _text(offer.get("installation")),
            _text(offer.get("monitoring_ems")),
            _text(offer.get("warranty")),
            _text(offer.get("payment_terms")),
            _text(offer.get("implementation_time")),
            _text(offer.get("validity")),
            offer.get("sort_order") or "",
            _text(offer.get("created_at")),
            _text(offer.get("updated_at")),
        ])
    return rows


def build_offer_send_rows(users: list[dict], attempts: list[dict]) -> list[list]:
    users_by_id, _ = _user_maps(users)
    rows = []
    for attempt in sorted(attempts, key=lambda item: _text(item.get("created_at"))):
        user = users_by_id.get(_text(attempt.get("user_id")))
        if not user:
            continue
        rows.append([
            _user_name(user),
            _text(user.get("email")),
            _text(user.get("id")),
            _text(attempt.get("id") or attempt.get("idempotency_key")),
            _text(attempt.get("client_name")),
            _text(attempt.get("client_city")),
            attempt.get("client_row") or "",
            _join_values(attempt.get("recipients")),
            _join_values(attempt.get("invalid_recipients")),
            _text(attempt.get("offer_template_id")),
            _text(attempt.get("offer_template_name")),
            attempt.get("offer_number") or "",
            _text(attempt.get("status")),
            _text(attempt.get("gmail_message_id")),
            _text(attempt.get("error")),
            _text(attempt.get("sent_at")),
            _text(attempt.get("created_at")),
            _text(attempt.get("updated_at")),
        ])
    return rows


def build_calendar_row(user: dict, event: dict) -> list:
    return [
        _user_name(user),
        _text(user.get("email")),
        _text(user.get("id")),
        _text(user.get("google_calendar_id")),
        _text(event.get("id")),
        _text(event.get("title")),
        _text(event.get("event_type")),
        _text(event.get("start")),
        _text(event.get("end")),
        _text(event.get("location")),
        _text(event.get("description")),
    ]


def count_contacts_by_user(contact_rows: list[list]) -> dict[str, int]:
    user_id_idx = CONTACT_HEADERS.index("User ID")
    counts: dict[str, int] = defaultdict(int)
    for row in contact_rows:
        if len(row) > user_id_idx and row[user_id_idx]:
            counts[_text(row[user_id_idx])] += 1
    return dict(counts)
