"""Telegram message formatting helpers for OZE-Agent.

All output uses Telegram MarkdownV2. All user-facing text is in Polish.
"""

import re
from typing import Optional

# ── MarkdownV2 escaping ───────────────────────────────────────────────────────

# Characters that must be escaped in MarkdownV2
_MDV2_SPECIAL = r"\_*[]()~`>#+-=|{}.!"


def escape_markdown_v2(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2."""
    for char in _MDV2_SPECIAL:
        text = text.replace(char, f"\\{char}")
    return text


def _e(text: str) -> str:
    """Shorthand for escape_markdown_v2."""
    return escape_markdown_v2(str(text)) if text else ""


# ── Error messages ────────────────────────────────────────────────────────────

_ERROR_MESSAGES = {
    "google_down": (
        "⚠️ Google Sheets jest chwilowo niedostępny\\. "
        "Twoje dane NIE zostały zapisane\\. "
        "Spróbuj ponownie za kilka minut\\."
    ),
    "calendar_down": (
        "⚠️ Google Calendar jest chwilowo niedostępny\\. "
        "Spotkanie NIE zostało dodane\\. "
        "Spróbuj ponownie za kilka minut\\."
    ),
    "drive_down": (
        "⚠️ Google Drive jest chwilowo niedostępny\\. "
        "Zdjęcie NIE zostało przesłane\\. "
        "Spróbuj ponownie za kilka minut\\."
    ),
    "timeout": (
        "⏱ Przekroczono czas oczekiwania\\. "
        "Spróbuj ponownie\\."
    ),
    "token_expired": (
        "🔑 Integracja Google wymaga ponownej autoryzacji\\. "
        "Otwórz dashboard i autoryzuj ponownie\\."
    ),
    "subscription_expired": (
        "💳 Twoja subskrypcja wygasła\\. "
        "Wykup dostęp, aby kontynuować korzystanie z asystenta\\."
    ),
    "rate_limit": (
        "📊 Osiągnąłeś dzienny limit interakcji\\. "
        "Limit odnawia się o północy\\."
    ),
}


def format_error(error_type: str) -> str:
    """Return a user-friendly Polish error message for MarkdownV2."""
    return _ERROR_MESSAGES.get(
        error_type,
        "❌ Wystąpił nieoczekiwany błąd\\. Spróbuj ponownie\\.",
    )


# ── Add-client confirmation card ─────────────────────────────────────────────

_DIR_ABBR = {
    "południe": "płd.", "wschód": "wsch.", "zachód": "zach.", "północ": "płn.",
}

_MEASUREMENT_FIELDS = {
    "house": ["Metraż domu (m²)", "Metraż domu", "Powierzchnia domu"],
    "roof":  ["Metraż dachu (m²)", "Metraż dachu", "Powierzchnia dachu"],
    "power": ["Moc (kW)", "Moc", "Moc instalacji"],
    "dir":   ["Kierunek dachu"],
}


def _find(client_data: dict, candidates: list[str]) -> str:
    for key in candidates:
        if client_data.get(key):
            return client_data[key]
    return ""


def _fmt_phone(raw: str) -> str:
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 9:
        return f"{digits[:3]} {digits[3:6]} {digits[6:]}"
    if len(digits) == 11 and digits.startswith("48"):
        d = digits[2:]
        return f"+48 {d[:3]} {d[3:6]} {d[6:]}"
    return raw


def format_add_client_card(client_data: dict, missing: list[str]) -> str:
    """Format client data as a confirmation card per agent_system_prompt.md spec.

    Plain text (no MarkdownV2) — use with reply_text().
    Every non-empty field in client_data is visible so the user knows what
    they are confirming.

    Example output:
        📋 Nowak, ul. Różana 3, Piaseczno
        Pompa ciepła 8kW
        Tel. 601 234 567
        Źródło pozyskania: Facebook
        Następny krok: wysłać ofertę
        ❓ Brakuje: metraż domu, metraż dachu, kierunek dachu
        Zapisać czy jeszcze coś dopiszesz?
    """
    lines: list[str] = []
    rendered: set[str] = set()

    # Line 1: 📋 name, [address, ]city
    name = client_data.get("Imię i nazwisko", "")
    address = client_data.get("Adres", "")
    city = client_data.get("Miasto", "")
    loc_parts = [p for p in [address, city] if p]
    header = ", ".join([name] + loc_parts) if name else ", ".join(loc_parts)
    if header:
        lines.append(f"📋 {header}")
    rendered.update(["Imię i nazwisko", "Adres", "Miasto"])

    # Line 2: product [power] [| measurements]
    product = client_data.get("Produkt", "")
    power = _find(client_data, _MEASUREMENT_FIELDS["power"])
    house = _find(client_data, _MEASUREMENT_FIELDS["house"])
    roof = _find(client_data, _MEASUREMENT_FIELDS["roof"])
    direction = _find(client_data, _MEASUREMENT_FIELDS["dir"])

    prod_part = product
    if power:
        prod_part = f"{prod_part} {power}kW" if prod_part else f"{power}kW"

    meas_parts: list[str] = []
    if house:
        meas_parts.append(f"dom {house}m²")
    if roof:
        abbr = _DIR_ABBR.get(direction.lower(), direction)
        meas_parts.append(f"dach {roof}m²" + (f" {abbr}" if abbr else ""))
    elif direction:
        meas_parts.append(direction)

    if prod_part and meas_parts:
        lines.append(f"{prod_part} | {', '.join(meas_parts)}")
    elif prod_part:
        lines.append(prod_part)
    elif meas_parts:
        lines.append(", ".join(meas_parts))

    rendered.add("Produkt")
    for candidates in _MEASUREMENT_FIELDS.values():
        rendered.update(candidates)

    # Line 3: phone
    phone = client_data.get("Telefon", "")
    if phone:
        lines.append(f"Tel. {_fmt_phone(phone)}")
    rendered.add("Telefon")

    # Remaining fields: every non-empty field not already shown above
    for field, value in client_data.items():
        if field not in rendered and value:
            lines.append(f"{field}: {value}")

    # Missing fields
    if missing:
        lines.append(f"❓ Brakuje: {', '.join(missing)}")

    lines.append("Zapisać czy jeszcze coś dopiszesz?")
    return "\n".join(lines)


# ── Client card ───────────────────────────────────────────────────────────────

SKIP_FIELDS = {"_row", "Link do zdjęć", "ID kalendarza"}


def format_client_card(client: dict) -> str:
    """Format a client dict as a Telegram MarkdownV2 card."""
    name = _e(client.get("Imię i nazwisko", "Nieznany klient"))
    lines = [f"👤 *{name}*"]

    priority_fields = [
        ("Miasto", "📍"),
        ("Telefon", "📞"),
        ("Email", "✉️"),
        ("Status", "📋"),
        ("Produkt", "☀️"),
    ]
    shown = {"Imię i nazwisko"}

    for field, emoji in priority_fields:
        value = client.get(field, "")
        if value:
            lines.append(f"{emoji} {_e(field)}: {_e(value)}")
            shown.add(field)

    for field, value in client.items():
        if field in shown or field in SKIP_FIELDS or not value:
            continue
        lines.append(f"• {_e(field)}: {_e(value)}")

    row = client.get("_row")
    if row:
        lines.append(f"\n_Wiersz: {_e(str(row))}_")

    return "\n".join(lines)


# ── Meeting / event formatting ────────────────────────────────────────────────


def format_meeting(event: dict) -> str:
    """Format a single calendar event for display."""
    start = event.get("start", "")
    end = event.get("end", "")
    title = _e(event.get("title", "Spotkanie"))
    location = event.get("location", "")
    description = event.get("description", "")

    time_str = ""
    try:
        # Parse ISO strings — show only HH:MM-HH:MM
        s = start[11:16] if len(start) >= 16 else start
        e = end[11:16] if len(end) >= 16 else end
        time_str = f"{_e(s)}\\-{_e(e)}"
    except Exception:
        time_str = _e(start)

    lines = [f"📅 {time_str} — *{title}*"]
    if location:
        lines.append(f"📍 {_e(location)}")
    if description:
        lines.append(f"📝 {_e(description)}")
    return "\n".join(lines)


def format_daily_schedule(events: list[dict]) -> str:
    """Format a full day's schedule."""
    if not events:
        return "📭 Brak spotkań na dziś\\."
    parts = ["📅 *Plan dnia:*\n"]
    for event in events:
        parts.append(format_meeting(event))
    return "\n\n".join(parts)


# ── Pipeline stats ────────────────────────────────────────────────────────────


def format_pipeline_stats(stats: dict) -> str:
    """Format pipeline status counts."""
    if not stats:
        return "📊 *Pipeline:* brak danych\\."
    lines = ["📊 *Pipeline:*"]
    for status, count in stats.items():
        lines.append(f"• {_e(status)}: {_e(str(count))}")
    return "\n".join(lines)


# ── Morning brief ─────────────────────────────────────────────────────────────


def format_morning_brief(
    events: list[dict],
    followups: list[dict],
    stats: dict,
    free_slots: list,
) -> str:
    """Compose the full morning brief message."""
    parts = ["🌅 *Dzień dobry\\! Oto Twój plan na dziś:*\n"]

    parts.append(format_daily_schedule(events))

    if followups:
        parts.append("\n⏳ *Oczekujące follow\\-upy:*")
        for f in followups:
            parts.append(f"• {_e(f.get('event_title', 'Spotkanie'))}")

    parts.append("\n" + format_pipeline_stats(stats))

    if free_slots:
        slot_strs = []
        for s, e in free_slots[:3]:
            slot_strs.append(f"{s.strftime('%H:%M')}\\-{e.strftime('%H:%M')}")
        parts.append(f"\n🕐 *Wolne sloty:* {', '.join(slot_strs)}")

    return "\n".join(parts)


# ── Meeting reminder ──────────────────────────────────────────────────────────


def format_meeting_reminder(event: dict, client: dict) -> str:
    """Format a pre-meeting reminder with client data."""
    title = _e(event.get("title", "Spotkanie"))
    start = event.get("start", "")
    time_str = _e(start[11:16]) if len(start) >= 16 else _e(start)

    lines = [
        f"🔔 *Przypomnienie o spotkaniu\\!*",
        f"📅 {time_str} — *{title}*",
    ]
    if event.get("location"):
        lines.append(f"📍 {_e(event['location'])}")

    if client:
        lines.append("\n👤 *Dane klienta:*")
        for field in ["Telefon", "Email", "Notatki", "Produkt", "Status"]:
            value = client.get(field, "")
            if value:
                lines.append(f"• {_e(field)}: {_e(value)}")

    return "\n".join(lines)


# ── Confirmation messages ─────────────────────────────────────────────────────


def format_confirmation(action: str, details: dict) -> str:
    """Format a confirmation message for any action."""
    action_labels = {
        "add_client": "Dodać klienta",
        "edit_client": "Zaktualizować dane klienta",
        "delete_client": "Usunąć klienta",
        "add_meeting": "Dodać spotkanie",
        "update_meeting": "Zaktualizować spotkanie",
        "delete_meeting": "Odwołać spotkanie",
        "update_status": "Zmienić status",
    }
    label = _e(action_labels.get(action, action))
    lines = [f"✅ *{label}?*\n"]
    for key, value in details.items():
        if value:
            lines.append(f"• {_e(str(key))}: {_e(str(value))}")
    lines.append("\nOdpowiedz *tak* aby potwierdzić lub *nie* aby anulować\\.")
    return "\n".join(lines)


# ── Edit comparison ───────────────────────────────────────────────────────────


def format_edit_comparison(field: str, old_value: str, new_value: str) -> str:
    """Show field change: 'Telefon: 600111222 → 601234567'."""
    return f"{_e(field)}: {_e(old_value)} → {_e(new_value)}"
