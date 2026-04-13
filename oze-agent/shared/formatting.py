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

# Short display labels for verbose field names shown in extra-fields section
_FIELD_LABEL = {
    "Źródło pozyskania": "Źródło",
    "Miejscowość": "Miejscowość",
    "Następny krok": "Następny krok",
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


def _fmt_followup(val: str) -> str:
    """Convert ISO datetime '2026-04-12 16:00' or '2026-04-12T16:00' to '12.04.2026 (niedziela) 16:00'."""
    if not val:
        return ""
    try:
        val_clean = str(val).replace("T", " ")
        if " " in val_clean:
            date_part, time_part = val_clean.split(" ", 1)
            from datetime import datetime as _dt
            dt = _dt.fromisoformat(date_part)
            return dt.strftime("%d.%m.%Y") + f" ({_DAYS_PL[dt.weekday()]}) {time_part}"
        return _fmt_date(val)
    except Exception:
        return str(val)


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

    # Line 2: product (tech specs go to Notatki per 16-col schema)
    product = client_data.get("Produkt", "")
    if product:
        lines.append(product)
    rendered.add("Produkt")

    # Line 3: phone
    phone = client_data.get("Telefon", "")
    if phone:
        lines.append(f"Tel. {_fmt_phone(phone)}")
    rendered.add("Telefon")

    # Remaining fields: every non-empty field not already shown above
    _FOLLOWUP_FIELDS = {"Następny krok", "Data następnego kroku"}
    for field, value in client_data.items():
        if field not in rendered and value:
            label = _FIELD_LABEL.get(field, field)
            display = _fmt_followup(value) if field in _FOLLOWUP_FIELDS else value
            lines.append(f"{label}: {display}")

    # Missing fields (filter out any empty strings from sheet header gaps)
    missing_clean = [col for col in missing if col and col.strip()]
    if missing_clean:
        lines.append(f"❓ Brakuje: {', '.join(missing_clean)}")

    lines.append("Zapisać / dopisać / anulować?")
    return "\n".join(lines)


# ── Client card ───────────────────────────────────────────────────────────────

SKIP_FIELDS = {"_row", "Link do zdjęć", "ID wydarzenia Kalendarz", "Wiersz"}

_DATE_FIELDS = {"Data pierwszego kontaktu", "Data ostatniego kontaktu", "Data następnego kroku"}


_DAYS_PL = ["poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela"]


def _fmt_date(serial) -> str:
    """Convert Excel serial date or ISO string to DD.MM.YYYY (dzień tygodnia)."""
    from datetime import datetime as _datetime, timedelta as _timedelta
    try:
        n = int(serial)
        if n > 40000:  # plausible Excel date (2009+)
            dt = _datetime(1899, 12, 30) + _timedelta(days=n)
            return dt.strftime("%d.%m.%Y") + f" ({_DAYS_PL[dt.weekday()]})"
    except (TypeError, ValueError):
        pass
    # Handle ISO string "YYYY-MM-DD" or "YYYY-MM-DD HH:MM" or "YYYY-MM-DDTHH:MM"
    if serial and isinstance(serial, str) and len(serial) >= 10 and serial[4:5] == "-":
        try:
            from datetime import datetime as _datetime2
            date_part = str(serial)[:10]
            time_part = str(serial)[11:16] if len(serial) > 10 else ""
            dt = _datetime2.fromisoformat(date_part)
            result = dt.strftime("%d.%m.%Y") + f" ({_DAYS_PL[dt.weekday()]})"
            if time_part:
                result += f" {time_part}"
            return result
        except Exception:
            pass
    return str(serial) if serial else ""


def _is_excel_serial(val) -> bool:
    """Return True if val looks like an Excel date serial (integer 40000–60000)."""
    try:
        n = int(val)
        return 40000 < n < 60000
    except (TypeError, ValueError):
        return False


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
        if field in _DATE_FIELDS or _is_excel_serial(value):
            display_value = _fmt_date(value)
        else:
            display_value = value
        lines.append(f"• {_e(field)}: {_e(display_value)}")

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


def _parse_client_from_title(title: str) -> str:
    """Extract client name from event title like 'Spotkanie — Jan Kowalski'."""
    if "—" in title:
        return title.split("—", 1)[1].strip()
    if "-" in title:
        return title.split("-", 1)[1].strip()
    return title


def _parse_product_from_description(description: str) -> str:
    """Extract 'Produkt: X' from event description."""
    for line in description.split("\n"):
        if line.startswith("Produkt:"):
            return line.split(":", 1)[1].strip()
    return ""


def format_schedule_entry(event: dict) -> str:
    """Format a single calendar event as a compact schedule line (MarkdownV2).

    Output per INTENCJE_MVP.md §4.6:
        09:00 🤝 Jan Kowalski \\(Warszawa\\) — spotkanie
              Kościuszki 15, Warszawa • Produkt: PV
    """
    start = event.get("start", "")
    title = event.get("title", "Spotkanie")
    location = event.get("location", "")
    description = event.get("description", "")

    # Time HH:MM
    time_str = start[11:16] if len(start) >= 16 else "??:??"

    # Client name from title
    client = _parse_client_from_title(title)

    # City from location (first part or full)
    city = ""
    address = ""
    if location:
        parts = [p.strip() for p in location.split(",")]
        if len(parts) >= 2:
            address = location
            city = parts[-1]  # last part is usually city
        else:
            city = location

    # Build main line
    city_part = f" \\({_e(city)}\\)" if city else ""
    main_line = f"{_e(time_str)} 🤝 {_e(client)}{city_part} — spotkanie"

    # Build detail line (address + product) for in-person meetings
    details = []
    if address:
        details.append(_e(address))
    product = _parse_product_from_description(description)
    if product:
        details.append(f"Produkt: {_e(product)}")

    if details:
        detail_line = "      " + " • ".join(details)
        return f"{main_line}\n{detail_line}"
    return main_line


def format_daily_schedule(events: list[dict], target_date=None) -> str:
    """Format a full day's schedule per INTENCJE_MVP.md §4.6.

    Header: 📅 Plan na DD.MM.YYYY (Dzień tygodnia)
    Empty:  Na DD.MM.YYYY nic nie masz w kalendarzu.
    """
    from datetime import date as _date
    if target_date is None:
        target_date = _date.today()

    date_str = target_date.strftime("%d.%m.%Y")
    day_name = _DAYS_PL[target_date.weekday()]
    header = f"{_e(date_str)} \\({_e(day_name)}\\)"

    if not events:
        return f"Na {header} nic nie masz w kalendarzu\\."

    lines = [f"📅 *Plan na {header}:*\n"]
    for event in events:
        lines.append(format_schedule_entry(event))
    return "\n".join(lines)


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
    return "\n".join(lines)


# ── Edit comparison ───────────────────────────────────────────────────────────


def format_edit_comparison(field: str, old_value: str, new_value: str) -> str:
    """Show field change: 'Telefon: 600111222 → 601234567'."""
    return f"{_e(field)}: {_e(old_value)} → {_e(new_value)}"
