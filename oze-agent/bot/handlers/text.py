"""Text message handler — main intent router for OZE-Agent bot."""

import logging
import re
from datetime import date, datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

WARSAW = ZoneInfo("Europe/Warsaw")

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.telegram_helpers import (
    build_confirm_buttons,
    build_choice_buttons,
    build_save_buttons,
    check_interaction_limit,
    check_subscription_active,
    check_user_registered,
    increment_interaction,
    is_private_chat,
    send_rate_limit_message,
    send_subscription_expired_message,
    send_typing,
    send_unregistered_message,
)
from shared.claude_ai import (
    call_claude_with_tools,
    classify_intent,
    extract_client_data,
    extract_meeting_data,
    generate_bot_response,
)
from shared.database import (
    delete_pending_flow,
    get_conversation_history,
    get_pending_flow,
    save_conversation_message,
    save_pending_flow,
    update_pending_followup,
)
from shared.formatting import (
    format_add_client_card,
    format_client_card,
    format_confirmation,
    format_daily_schedule,
    format_edit_comparison,
    format_error,
    format_pipeline_stats,
    escape_markdown_v2,
)
from shared.google_calendar import (
    check_conflicts,
    create_event,
    get_events_for_date,
    get_events_for_range,
    get_free_slots,
)
from shared.google_sheets import (
    add_client,
    get_all_clients,
    get_pipeline_stats,
    get_sheet_headers,
    search_clients,
    update_client,
)
from shared.search import detect_potential_duplicate

logger = logging.getLogger(__name__)

# Fields managed automatically — never show as "missing" to the user
SYSTEM_FIELDS = {
    "Data pierwszego kontaktu", "Data ostatniego kontaktu", "Status",
    "Zdjęcia", "Link do zdjęć", "ID kalendarza", "Email",
    "Dodatkowe info", "Notatki", "Następny krok",
}

# Regex: 7+ consecutive digits after stripping spaces/hyphens/dots (phone number)
# 7 catches Polish 8-digit numbers entered without leading country code
_PHONE_RE = re.compile(r'\d{7,}')
# Words that indicate lookup/question intent — not new client data
_LOOKUP_WORDS = {"szukaj", "znajdź", "pokaż", "zmień", "edytuj", "usuń", "odwołaj",
                 "zaktualizuj", "popraw", "zmiana", "aktualizuj", "nowy", "numer",
                 "telefon", "adres", "metraż", "dach", "dom"}
# Words that indicate a genuine meeting intent (date/time markers)
_TEMPORAL_MARKERS = {
    "jutro", "pojutrze", "dziś", "dzisiaj", "wczoraj",
    "poniedziałek", "wtorek", "środę", "środa", "czwartek",
    "piątek", "sobotę", "sobota", "niedzielę", "niedziela",
    "tydzień", "następny", "przyszły", "spotkanie",
    "wpół", "kwadrans",  # Polish quarter-hour time expressions
}
# HH:MM or "o <hour>" / "na <hour>" — require explicit time preposition
# Also matches "wpół" ("wpół do ósmej") and "kwadrans" ("za kwadrans dziesiąta")
_TIME_RE = re.compile(
    r'\d{1,2}:\d{2}'
    r'|\bo\s+\d{1,2}(?:\s|$)'
    r'|\bna\s+\d{1,2}(?:\s|$)'
    r'|\bwpół\b'
    r'|\bkwadrans\b'
)


def _contains_phone(text: str) -> bool:
    """Return True if text contains a 7+ digit phone-like number."""
    digits_only = re.sub(r'[\s\-\.]', '', text)
    return bool(_PHONE_RE.search(digits_only))


# ── Guards ─────────────────────────────────────────────────────────────────────


async def _run_guards(update: Update) -> Optional[dict]:
    """Run standard checks. Returns user dict or None (and sends error if None)."""
    telegram_id = update.effective_user.id

    user = await check_user_registered(telegram_id)
    if not user:
        await send_unregistered_message(update)
        return None

    if not await check_subscription_active(user):
        await send_subscription_expired_message(update)
        return None

    limit = await check_interaction_limit(telegram_id)
    if not limit["allowed"]:
        await send_rate_limit_message(update, limit["count"], limit["can_borrow"])
        return None

    return user


# ── Main handler ──────────────────────────────────────────────────────────────


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Main text message handler — classify intent and route to sub-handler."""
    if not await is_private_chat(update):
        return

    user = await _run_guards(update)
    if not user:
        return

    telegram_id = update.effective_user.id
    message_text = update.effective_message.text.strip()

    await send_typing(context, telegram_id)

    # Check for active pending flow first
    pending_flow = get_pending_flow(telegram_id)
    if pending_flow:
        consumed = await _route_pending_flow(update, context, user, pending_flow, message_text)
        if consumed:
            return
        # Flow was auto-cancelled — fall through to process the new message normally

    text_lower = message_text.lower()
    words = set(text_lower.split())

    # "zapisz" keyword with other content → parse client data and save immediately
    if "zapisz" in words and len(words) > 1:
        await handle_add_client(update, context, user, {}, message_text, save_immediately=True)
        await increment_interaction(telegram_id, "add_client", "local", 0, 0, 0.0)
        return

    # Phone number in message (not a question, not a lookup command) → add_client
    if (
        _contains_phone(message_text)
        and "?" not in message_text
        and not any(w in words for w in _LOOKUP_WORDS)
    ):
        await handle_add_client(update, context, user, {}, message_text)
        await increment_interaction(telegram_id, "add_client", "local", 0, 0, 0.0)
        return

    # Save message and get history
    save_conversation_message(telegram_id, "user", message_text)
    history = get_conversation_history(telegram_id, limit=3)

    # Classify intent
    intent_data = await classify_intent(message_text, history)
    intent = intent_data.get("intent", "general_question")

    # Low-confidence classification → fall back to general (prevents garbage → add_client)
    if (
        intent_data.get("confidence", 1.0) < 0.5
        and intent not in {"confirm_yes", "confirm_no", "cancel_flow"}
    ):
        intent = "general_question"

    # Guard: Claude said add_meeting but message has no date/time markers
    # → reclassify as add_client (avoids history contamination from past meeting attempts)
    if intent == "add_meeting":
        msg_lower = message_text.lower()
        has_temporal = (
            any(w in msg_lower for w in _TEMPORAL_MARKERS)
            or bool(_TIME_RE.search(msg_lower))
        )
        if not has_temporal:
            intent = "add_client"

    # Route by intent
    handlers = {
        "add_client": handle_add_client,
        "search_client": handle_search_client,
        "edit_client": handle_edit_client_v2,
        "add_note": handle_edit_client_v2,         # note triggers in handle_edit_client_v2
        "delete_client": handle_delete_client,
        "add_meeting": handle_add_meeting,
        "show_day_plan": handle_view_meetings,     # spec v5 name
        "view_meetings": handle_view_meetings,
        "reschedule_meeting": handle_reschedule_meeting,
        "cancel_meeting": handle_cancel_meeting,
        "lejek_sprzedazowy": handle_show_pipeline, # spec v5 rename
        "show_pipeline": handle_show_pipeline,     # backwards compat
        "filtruj_klientów": handle_filter_clients, # new
        "change_status": handle_change_status,
        "refresh_columns": handle_refresh_columns,
        "confirm_yes": handle_confirm,
        "confirm_no": handle_cancel_flow,
        "cancel_flow": handle_cancel_flow,
        "general_question": handle_general,
    }

    handler = handlers.get(intent, handle_general)
    await handler(update, context, user, intent_data, message_text)

    await increment_interaction(
        telegram_id, intent, "claude-haiku-4-5-20251001", 0, 0, 0.0
    )


# ── Pending flow router ───────────────────────────────────────────────────────


async def _route_pending_flow(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict,
    flow: dict,
    message_text: str,
) -> bool:
    """Route a reply message based on the active pending flow.

    Returns True if the message was consumed by the flow, False if the flow was
    auto-cancelled and the message should be processed normally by handle_text.
    """
    flow_type = flow.get("flow_type", "")
    text_lower = message_text.lower().strip()

    is_yes = text_lower in {
        "tak", "tak.", "ok", "okej", "dobrze", "zgadza się", "yes",
        "zapisz tak jak jest", "zapisz", "tak jak jest", "ok zapisz", "dobra", "spoko",
    }
    # "zapisz" as a word in a longer message (e.g. "adres Długa 12 zapisz") → confirm
    if not is_yes and "zapisz" in set(text_lower.split()):
        is_yes = True
    is_no = text_lower in {
        "nie", "nie.", "anuluj", "stop", "no", "cancel", "nie chcę", "zrezygnuj",
    }

    if is_yes:
        await handle_confirm(update, context, user, {}, message_text)
        return True
    elif is_no:
        await handle_cancel_flow(update, context, user, {}, message_text)
        return True
    elif flow_type == "add_client":
        # User is augmenting an in-progress add_client flow with more data
        telegram_id = update.effective_user.id
        user_id = user["id"]
        old_flow_data = flow.get("flow_data", {})
        old_client_data = old_flow_data.get("client_data", {})

        headers = await get_sheet_headers(user_id)
        result = await extract_client_data(message_text, headers)
        new_data = {k: v for k, v in result.get("client_data", {}).items() if v}
        logger.info("augment add_client: new_data=%s", new_data)

        if not new_data:
            # Claude extracted nothing — re-show existing card unchanged
            sheet_columns = user.get("sheet_columns") or headers
            missing = [col for col in sheet_columns if col and not old_client_data.get(col) and col not in SYSTEM_FIELDS]
            card = format_add_client_card(old_client_data, missing)
            await update.effective_message.reply_text(card, reply_markup=build_save_buttons("confirm"))
            return True

        # If the new message names a different client → start fresh, don't merge
        old_name = old_client_data.get("Imię i nazwisko", "").strip()
        new_name = new_data.get("Imię i nazwisko", "").strip()
        if old_name and new_name and old_name.lower() != new_name.lower():
            sheet_columns = user.get("sheet_columns") or headers
            missing = [col for col in sheet_columns if col and not new_data.get(col) and col not in SYSTEM_FIELDS]
            save_pending_flow(telegram_id, "add_client", {"client_data": new_data})
            card = format_add_client_card(new_data, missing)
            await update.effective_message.reply_text(card, reply_markup=build_save_buttons("confirm"))
            return True

        merged = {**old_client_data, **new_data}
        logger.info("augment add_client: merged=%s", merged)
        sheet_columns = user.get("sheet_columns") or headers
        missing = [col for col in sheet_columns if col and not merged.get(col) and col not in SYSTEM_FIELDS]
        logger.info("augment add_client: missing=%s", missing)

        if not missing:
            delete_pending_flow(telegram_id)
            row = await add_client(user_id, merged)
            if row:
                name = merged.get("Imię i nazwisko", "klient")
                offer_remaining = old_flow_data.get("_offer_remaining", [])
                if offer_remaining:
                    next_client = offer_remaining[0]
                    new_remaining = offer_remaining[1:]
                    save_pending_flow(telegram_id, "add_client", {
                        "client_data": {"Imię i nazwisko": next_client},
                        "_offer_remaining": new_remaining,
                    })
                    await update.effective_message.reply_text(
                        f"✅ {name} dodany. Podaj dane {next_client} — adres, telefon, produkt."
                    )
                else:
                    await update.effective_message.reply_text("✅ Zapisane.")
            else:
                await update.effective_message.reply_markdown_v2(format_error("google_down"))
            return True

        # User is correcting/adding data (possibly after tapping [Nie]) — clear cancel flag, re-show card
        new_flow_data: dict = {"client_data": merged}
        if old_flow_data.get("_offer_remaining"):
            new_flow_data["_offer_remaining"] = old_flow_data["_offer_remaining"]
        save_pending_flow(telegram_id, "add_client", new_flow_data)
        card = format_add_client_card(merged, missing)
        await update.effective_message.reply_text(card, reply_markup=build_save_buttons("confirm"))
        return True
    else:
        # New message arrived during a non-add_client pending flow → auto-cancel, process message normally
        telegram_id = update.effective_user.id
        delete_pending_flow(telegram_id)
        await update.effective_message.reply_text("⚠️ Anulowane.")
        return False


# ── Sub-handlers ──────────────────────────────────────────────────────────────


async def handle_add_client(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict,
    intent_data: dict,
    message_text: str,
    save_immediately: bool = False,
) -> None:
    """Extract client data, check for duplicates, show confirmation card.

    If save_immediately=True (triggered by "zapisz" keyword), skip confirmation
    and write to Sheets directly.
    """
    telegram_id = update.effective_user.id
    user_id = user["id"]

    await send_typing(context, telegram_id)

    headers = await get_sheet_headers(user_id)
    # Strip "zapisz" from the message before extraction so it isn't mis-parsed
    clean_message = re.sub(r'\bZapisz\b|\bzapisz\b', '', message_text).strip()
    result = await extract_client_data(clean_message, headers)
    client_data = result.get("client_data", {})

    if not client_data:
        await update.effective_message.reply_text("Co chcesz zrobić?")
        return

    # save_immediately: write without showing card
    if save_immediately:
        row = await add_client(user_id, client_data)
        if row:
            await update.effective_message.reply_text("✅ Zapisane.")
        else:
            await update.effective_message.reply_markdown_v2(format_error("google_down"))
        return

    # Duplicate check
    all_clients = await get_all_clients(user_id)
    name = client_data.get("Imię i nazwisko", "")
    city = client_data.get("Miasto", "")
    duplicate = detect_potential_duplicate(name, city, all_clients) if name and city else None

    if duplicate:
        save_pending_flow(telegram_id, "add_client_duplicate", {
            "client_data": client_data,
            "duplicate_row": duplicate.get("_row"),
        })
        dup_name = duplicate.get("Imię i nazwisko", "")
        dup_city = duplicate.get("Miasto", "")
        dup_addr = duplicate.get("Adres", "")
        dup_prod = duplicate.get("Produkt", "")
        dup_info = ", ".join(p for p in [dup_addr, dup_city, dup_prod] if p)
        await update.effective_message.reply_text(
            f"⚠️ Masz już {dup_name} ({dup_info}).\nDodać nowego czy zaktualizować?",
            reply_markup=build_choice_buttons([
                ("Nowy", "duplicate:add_anyway"),
                ("Aktualizuj", "duplicate:no"),
            ]),
        )
        return

    # Always compute missing from actual sheet column names (never trust Claude's guesses)
    sheet_columns = user.get("sheet_columns") or headers
    missing = [col for col in sheet_columns if col and not client_data.get(col) and col not in SYSTEM_FIELDS]

    save_pending_flow(telegram_id, "add_client", {"client_data": client_data})

    card = format_add_client_card(client_data, missing)
    await update.effective_message.reply_text(card, reply_markup=build_save_buttons("confirm"))


async def handle_search_client(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict,
    intent_data: dict,
    message_text: str,
) -> None:
    """Search for clients and show results."""
    telegram_id = update.effective_user.id
    user_id = user["id"]
    query = intent_data.get("entities", {}).get("name") or message_text

    await send_typing(context, telegram_id)
    results = await search_clients(user_id, query)

    if not results:
        await update.effective_message.reply_text(f"Nie mam \"{query}\" w bazie.")
        return

    if len(results) == 1:
        client = results[0]
        client_name = client.get("Imię i nazwisko", "")
        query_lower = query.lower().strip()
        name_lower = client_name.lower().strip()

        # If the query is not literally present in the name (or vice versa), it's a typo match.
        # Ask the user to confirm instead of silently showing the wrong person's data.
        is_exact = query_lower in name_lower or name_lower in query_lower
        if not is_exact:
            city = client.get("Miasto", "")
            suggestion = client_name + (f" z {city}" if city else "")
            save_pending_flow(telegram_id, "confirm_search", {"row": client.get("_row")})
            await update.effective_message.reply_text(
                f"Nie mam \"{query}\". Chodziło o {suggestion}?",
                reply_markup=build_confirm_buttons("confirm"),
            )
            return

        try:
            card = format_client_card(client)
            await update.effective_message.reply_markdown_v2(card)
        except Exception as e:
            logger.error("format_client_card failed: %s", e)
            name = client.get("Imię i nazwisko", "?")
            city = client.get("Miasto", "")
            await update.effective_message.reply_text(
                f"Błąd formatowania karty dla {name}{' (' + city + ')' if city else ''}. Sprawdź logi."
            )
        return

    if len(results) >= 50:
        sheets_url = f"https://docs.google.com/spreadsheets/d/{user.get('google_sheets_id', '')}"
        await update.effective_message.reply_text(
            f"Znalazłem {len(results)} klientów. Otwórz arkusz:\n{sheets_url}"
        )
        return

    # 2–49 results: numbered list
    lines = [f"Mam {len(results)} klientów:"]
    options = []
    for i, c in enumerate(results[:10], start=1):
        name = c.get("Imię i nazwisko", "?")
        city = c.get("Miasto", c.get("Miejscowość", ""))
        row = c.get("_row", 0)
        label = f"{i}. {name}" + (f" — {city}" if city else "")
        lines.append(label)
        options.append((label, f"select_client:{row}"))
    lines.append("Którego?")

    await update.effective_message.reply_text(
        "\n".join(lines),
        reply_markup=build_choice_buttons(options),
    )


async def handle_edit_client(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict,
    intent_data: dict,
    message_text: str,
) -> None:
    """Find client and propose field update."""
    user_id = user["id"]
    telegram_id = update.effective_user.id
    entities = intent_data.get("entities", {})
    query = entities.get("name") or message_text

    logger.info("handle_edit_client: query=%r", query)
    results = await search_clients(user_id, query)
    if not results:
        await update.effective_message.reply_text(f"Nie znalazłem klienta: '{query}'")
        return

    client = results[0]
    client_name = client.get("Imię i nazwisko", "klient")
    headers = await get_sheet_headers(user_id)
    logger.info("handle_edit_client: client=%r headers=%s", client_name, len(headers))
    extracted = await extract_client_data(message_text, headers)
    updates = extracted.get("client_data", {})
    logger.info("handle_edit_client: updates=%s", updates)

    # Strip "Imię i nazwisko" if AI echoed the search key back as an update
    client_name_lower = client_name.lower()
    updates = {
        k: v for k, v in updates.items()
        if not (
            k == "Imię i nazwisko"
            and (
                v.lower() == client_name_lower
                or v.lower() in client_name_lower
                or client_name_lower in v.lower()
            )
        )
    }
    logger.info("handle_edit_client: after name-echo filter updates=%s", updates)

    msg_lower = message_text.lower()

    # Note-append detection via keyword triggers
    NOTE_TRIGGERS = [
        "dodaj informacje", "dodaj informację", "dodaj że", "dodaj ze",
        "dodaj notatkę", "dodaj notatke", "dopisz", "zanotuj",
        "interesuje się też", "interesuje sie tez",
        "interesuje go też", "interesuje go tez",
    ]
    note_trigger_found = any(t in msg_lower for t in NOTE_TRIGGERS)

    if note_trigger_found and "Notatki" not in updates:
        content = message_text
        for trigger in NOTE_TRIGGERS:
            content = re.sub(re.escape(trigger), "", content, flags=re.IGNORECASE)
        for word in query.split():
            if len(word) > 2:
                content = re.sub(r'\b' + re.escape(word) + r'\b', "", content, flags=re.IGNORECASE)
        content = re.sub(r'\b(do|ze|że|ku|od|też|tez|dla|i|a)\b', "", content, flags=re.IGNORECASE)
        content = re.sub(r'[,.:]+', " ", content)
        content = " ".join(content.split()).strip()
        if content:
            updates["Notatki"] = content
            logger.info("handle_edit_client: note-append detected, content=%r", content)

    # Keyword fallback for measurements when AI missed the field
    if not updates:
        roof_col = next((h for h in headers if "dachu" in h.lower()), None)
        if roof_col and any(kw in msg_lower for kw in ["dachu", "dach"]):
            nie_idx = msg_lower.find("nie ")
            search_text = message_text[:nie_idx] if nie_idx != -1 else message_text
            nums = re.findall(r'\d+(?:[.,]\d+)?', search_text)
            if nums:
                updates[roof_col] = nums[-1]
                logger.info("handle_edit_client: roof fallback matched col=%r val=%r", roof_col, nums[-1])
        elif not updates:
            house_col = next(
                (h for h in headers if "domu" in h.lower() or ("metraż" in h.lower() and "dachu" not in h.lower())),
                None,
            )
            if house_col and any(kw in msg_lower for kw in ["domu", "dom", "metraż"]):
                nums = re.findall(r'\d+(?:[.,]\d+)?', message_text)
                if nums:
                    updates[house_col] = nums[0]
                    logger.info("handle_edit_client: house fallback matched col=%r val=%r", house_col, nums[0])

    if not updates:
        # Detect which keyword was mentioned and report missing column
        if any(kw in msg_lower for kw in ["dachu", "dach", "metraż"]):
            await update.effective_message.reply_text(
                "Nie mam kolumny 'Metraż dachu' w arkuszu. Dodaj ją lub napisz 'odśwież kolumny'."
            )
        else:
            await update.effective_message.reply_text("Nie rozpoznałem co chcesz zmienić. Opisz dokładniej.")
        return

    # For phone/email fields: if client already has a value, offer replace or keep-both
    CONTACT_FIELDS = {"Telefon", "Email"}
    ambiguous = {f for f in updates if f in CONTACT_FIELDS and client.get(f)}
    if ambiguous:
        field = next(iter(ambiguous))
        old_val = client.get(field, "")
        new_val = updates[field]
        other_updates = {k: v for k, v in updates.items() if k != field}
        save_pending_flow(telegram_id, "edit_client_phone_choice", {
            "row": client.get("_row"),
            "field": field,
            "old_value": old_val,
            "new_value": new_val,
            "other_updates": other_updates,
        })
        field_label = field.lower()
        await update.effective_message.reply_text(
            f"{client_name} — {field_label}:\n"
            f"Stary: {old_val}\n"
            f"Nowy: {new_val}\n"
            f"Zamienić czy dodać drugi?",
            reply_markup=build_choice_buttons([
                ("Zamień", "phone:replace"),
                ("Dodaj drugi", "phone:keep_both"),
            ]),
        )
        return

    # Detect note-append intent
    is_note_append = "Notatki" in updates and (
        note_trigger_found
        or any(kw in msg_lower for kw in ("dodaj", "dopisz", "też", "tez"))
    )
    append_fields = ["Notatki"] if is_note_append else []

    save_pending_flow(telegram_id, "edit_client", {
        "row": client.get("_row"),
        "updates": updates,
        "old_values": {k: client.get(k, "") for k in updates},
        "append_fields": append_fields,
    })

    # Build plain-text confirmation card
    if len(updates) == 1:
        field, new_val = next(iter(updates.items()))
        old_val = client.get(field, "")
        field_label = field.lower()
        if is_note_append:
            msg = f"{client_name} — {field_label}:\nDodaję: \"{new_val}\"\nZapisać?"
        else:
            msg = f"{client_name} — {field_label}:\nByło: {old_val}\nBędzie: {new_val}\nZmienić?"
    else:
        lines = [f"Zmiany dla {client_name}:"]
        for field, new_val in updates.items():
            old_val = client.get(field, "")
            lines.append(f"{field}: {old_val} → {new_val}")
        lines.append("Zmienić?")
        msg = "\n".join(lines)

    await update.effective_message.reply_text(msg, reply_markup=build_confirm_buttons("confirm"))


async def handle_edit_client_v2(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict,
    intent_data: dict,
    message_text: str,
) -> None:
    """Find client and update via Claude tool use — no regex fallbacks."""
    user_id = user["id"]
    telegram_id = update.effective_user.id
    entities = intent_data.get("entities", {})
    query = entities.get("name") or message_text

    logger.info("handle_edit_client_v2: query=%r msg=%r", query, message_text)
    results = await search_clients(user_id, query)
    if not results:
        await update.effective_message.reply_text(f"Nie znalazłem klienta: '{query}'")
        return

    client = results[0]
    client_name = client.get("Imię i nazwisko", "klient")
    headers = await get_sheet_headers(user_id)
    logger.info("handle_edit_client_v2: client=%r headers=%d", client_name, len(headers))

    client_data_str = "\n".join(
        f"  {h}: {client.get(h, '')}" for h in headers if client.get(h)
    )
    headers_str = ", ".join(headers)

    system_prompt = f"""Jesteś asystentem handlowca OZE. Pomagasz edytować dane klientów w arkuszu.

Klient: {client_name}
Aktualne dane:
{client_data_str}

Dostępne kolumny (użyj DOKŁADNIE tych nazw):
{headers_str}

Zasady:
- Użyj dokładnych nazw kolumn z listy, nigdy nie wymyślaj własnych.
- Jeśli użytkownik mówi o metrażu dachu, field_name to kolumna z listy zawierająca słowo "dach".
- Jeśli użytkownik chce dodać informację ("interesuje się też X", "dodaj że", "dopisz"), użyj append_client_note.
- Jeśli użytkownik wyraźnie zmienia wartość ("zmień X na Y", "ma Y nie Z"), użyj update_client_field.
- Nie zmieniaj "Imię i nazwisko" chyba że użytkownik wprost prosi o zmianę nazwiska.
- Zawsze wywołaj jedno z narzędzi. Jeśli nie wiesz co zmienić, użyj request_clarification."""

    tools = [
        {
            "name": "update_client_field",
            "description": "Zastępuje wartość pola klienta nową wartością.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "client_name": {"type": "string", "description": "Nazwa klienta"},
                    "field_name": {"type": "string", "description": "Dokładna nazwa kolumny z listy"},
                    "new_value": {"type": "string", "description": "Nowa wartość"},
                    "old_value_hint": {"type": "string", "description": "Stara wartość wspomniana przez użytkownika"},
                },
                "required": ["client_name", "field_name", "new_value"],
            },
        },
        {
            "name": "append_client_note",
            "description": "Dodaje tekst do kolumny Notatki bez usuwania poprzednich notatek.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "client_name": {"type": "string", "description": "Nazwa klienta"},
                    "note_text": {"type": "string", "description": "Tekst notatki do dodania"},
                },
                "required": ["client_name", "note_text"],
            },
        },
        {
            "name": "request_clarification",
            "description": "Prosi użytkownika o wyjaśnienie gdy nie wiadomo co zmienić.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string", "description": "Krótkie wyjaśnienie po polsku co jest niejasne"},
                },
                "required": ["reason"],
            },
        },
    ]

    result = await call_claude_with_tools(system_prompt, message_text, tools, model_type="complex")
    tool_name = result.get("tool_name")
    tool_input = result.get("tool_input", {})
    logger.info("handle_edit_client_v2: tool=%r input=%s", tool_name, tool_input)

    if tool_name == "update_client_field":
        field_name = tool_input.get("field_name", "")
        new_value = tool_input.get("new_value", "")
        old_value_hint = tool_input.get("old_value_hint", "")
        old_value = client.get(field_name, old_value_hint)

        save_pending_flow(telegram_id, "edit_client", {
            "row": client.get("_row"),
            "updates": {field_name: new_value},
            "old_values": {field_name: old_value},
            "append_fields": [],
        })
        logger.info(
            "handle_edit_client_v2: flow saved row=%s updates=%s append=[]",
            client.get("_row"), {field_name: new_value},
        )

        field_label = field_name.lower()
        msg = (
            f"{client_name} — {field_label}:\n"
            f"Było: {old_value}\n"
            f"Będzie: {new_value}\n"
            f"Zmienić?"
        )
        await update.effective_message.reply_text(msg, reply_markup=build_confirm_buttons("confirm"))

    elif tool_name == "append_client_note":
        note_text = tool_input.get("note_text", "")
        old_notes = client.get("Notatki", "")

        save_pending_flow(telegram_id, "edit_client", {
            "row": client.get("_row"),
            "updates": {"Notatki": note_text},
            "old_values": {"Notatki": old_notes},
            "append_fields": ["Notatki"],
        })
        logger.info(
            "handle_edit_client_v2: flow saved row=%s note_append=%r",
            client.get("_row"), note_text,
        )

        msg = (
            f"{client_name} — notatki:\n"
            f"Dodaję: \"{note_text}\"\n"
            f"Zapisać?"
        )
        await update.effective_message.reply_text(msg, reply_markup=build_confirm_buttons("confirm"))

    elif tool_name == "request_clarification":
        reason = tool_input.get("reason", "Nie rozumiem co chcesz zmienić. Opisz dokładniej.")
        await update.effective_message.reply_text(reason)

    else:
        text = result.get("text") or "Nie rozpoznałem co chcesz zmienić. Opisz dokładniej."
        logger.warning("handle_edit_client_v2: no tool called, text=%r", text[:100])
        await update.effective_message.reply_text(text)


async def handle_delete_client(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict,
    intent_data: dict,
    message_text: str,
) -> None:
    """Find client and confirm deletion."""
    user_id = user["id"]
    telegram_id = update.effective_user.id
    query = intent_data.get("entities", {}).get("name") or message_text

    results = await search_clients(user_id, query)
    if not results:
        await update.effective_message.reply_text(f"Nie znalazłem klienta: '{query}'")
        return

    client = results[0]
    save_pending_flow(telegram_id, "delete_client", {"row": client.get("_row")})

    try:
        card = format_client_card(client)
        await update.effective_message.reply_markdown_v2(
            f"🗑️ Usunąć tego klienta?\n\n{card}",
            reply_markup=build_confirm_buttons("confirm"),
        )
    except Exception as e:
        logger.error("format_client_card failed: %s", e)
        name = client.get("Imię i nazwisko", "?")
        city = client.get("Miasto", "")
        await update.effective_message.reply_text(
            f"Błąd formatowania karty dla {name}{' (' + city + ')' if city else ''}. Sprawdź logi."
        )


def _parse_warsaw(date_str: str, time_str: str) -> datetime:
    """Parse date+time strings as Europe/Warsaw and return an aware datetime."""
    naive = datetime.fromisoformat(f"{date_str}T{time_str}:00")
    return naive.replace(tzinfo=WARSAW)


async def _enrich_meeting(user_id: str, client_name: str, location_hint: str) -> dict:
    """Look up client in Sheets and return enriched title/location/description."""
    full_name = client_name
    location = location_hint
    description = ""

    if client_name:
        results = await search_clients(user_id, client_name)
        if results:
            client = results[0]
            full_name = client.get("Imię i nazwisko", client_name)

            addr = client.get("Adres", "")
            city = client.get("Miasto", client.get("Miejscowość", ""))
            if not location:
                location = ", ".join(p for p in [addr, city] if p)

            parts = []
            if client.get("Telefon"):
                parts.append(f"Tel: {client['Telefon']}")
            prod = client.get("Produkt", "")
            power = client.get("Moc (kW)", client.get("Moc", ""))
            if prod:
                parts.append(f"Produkt: {prod}" + (f" {power} kW" if power else ""))
            if client.get("Notatki"):
                parts.append(f"Notatki: {client['Notatki']}")
            if client.get("Następny krok"):
                parts.append(f"Następny krok: {client['Następny krok']}")
            description = "\n".join(parts)

    title = f"Spotkanie z {full_name}" if full_name else "Spotkanie"
    return {"title": title, "location": location, "description": description, "full_name": full_name}


async def handle_add_meeting(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict,
    intent_data: dict,
    message_text: str,
) -> None:
    """Extract meeting data (single or multiple), check conflicts, ask for confirmation."""
    telegram_id = update.effective_user.id
    user_id = user["id"]

    today_str = date.today().isoformat()
    meeting_result = await extract_meeting_data(message_text, today_str)
    meetings = meeting_result.get("meetings", [])

    if not meetings:
        await update.effective_message.reply_text(
            "Nie rozpoznałem daty lub godziny spotkania. Podaj np. 'jutro o 14:00 z Kowalskim'."
        )
        return

    default_duration = user.get("default_meeting_duration", 60)

    if len(meetings) == 1:
        # Single meeting — original flow with format_confirmation card
        m = meetings[0]
        if not m.get("date") or not m.get("time"):
            await update.effective_message.reply_text(
                "Nie rozpoznałem daty lub godziny spotkania. Podaj np. 'jutro o 14:00 z Kowalskim'."
            )
            return
        try:
            start_dt = _parse_warsaw(m["date"], m["time"])
            duration = m.get("duration_minutes") or default_duration
            end_dt = start_dt + timedelta(minutes=duration)
        except Exception:
            await update.effective_message.reply_text("Nie rozpoznałem daty lub godziny. Spróbuj ponownie.")
            return

        enriched = await _enrich_meeting(user_id, m.get("client_name", ""), m.get("location", ""))

        conflicts = await check_conflicts(user_id, start_dt, end_dt)
        conflict_warning = ""
        if conflicts:
            conflict_warning = f"\n\n⚠️ Uwaga: masz już spotkanie o tej porze: *{escape_markdown_v2(conflicts[0].get('title', ''))}*"

        save_pending_flow(telegram_id, "add_meeting", {
            "title": enriched["title"],
            "start": start_dt.isoformat(),
            "end": end_dt.isoformat(),
            "location": enriched["location"],
            "description": enriched["description"],
            "client_name": enriched["full_name"],
        })

        _DAYS_PL = ["poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela"]
        try:
            _d = datetime.fromisoformat(m["date"]).date()
            date_display = _d.strftime("%d.%m.%Y") + f" ({_DAYS_PL[_d.weekday()]})"
        except Exception:
            date_display = m["date"]

        details = {
            "Klient": enriched["full_name"],
            "Data": date_display,
            "Godzina": m["time"],
            "Czas trwania": f"{duration} min",
            "Miejsce": enriched["location"],
        }
        msg = format_confirmation("add_meeting", details) + conflict_warning
        await update.effective_message.reply_markdown_v2(msg, reply_markup=build_confirm_buttons("confirm"))

    else:
        # Multiple meetings — build all, check conflicts, confirm as a batch
        flow_meetings = []
        conflict_warnings = []

        for m in meetings:
            if not m.get("date") or not m.get("time"):
                continue
            try:
                start_dt = _parse_warsaw(m["date"], m["time"])
                duration = m.get("duration_minutes") or default_duration
                end_dt = start_dt + timedelta(minutes=duration)
            except Exception:
                continue

            enriched = await _enrich_meeting(user_id, m.get("client_name", ""), m.get("location", ""))

            conflicts = await check_conflicts(user_id, start_dt, end_dt)
            if conflicts:
                conflict_warnings.append(f"⚠️ Konflikt {enriched['full_name']}: {conflicts[0].get('title', '')}")

            flow_meetings.append({
                "title": enriched["title"],
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
                "location": enriched["location"],
                "description": enriched["description"],
                "client_name": enriched["full_name"],
            })

        if not flow_meetings:
            await update.effective_message.reply_text("Nie udało się rozpoznać dat spotkań. Spróbuj ponownie.")
            return

        save_pending_flow(telegram_id, "add_meetings", {"meetings": flow_meetings})

        lines = [f"📅 Dodać {len(flow_meetings)} spotkań:"]
        for fm in flow_meetings:
            start = datetime.fromisoformat(fm["start"])
            loc = f", {fm['location']}" if fm.get("location") else ""
            lines.append(f"• {fm.get('client_name', '?')} — {start.strftime('%d.%m %H:%M')}{loc}")
        lines.extend(conflict_warnings)
        msg = escape_markdown_v2("\n".join(lines))
        await update.effective_message.reply_markdown_v2(msg, reply_markup=build_confirm_buttons("confirm"))


async def handle_view_meetings(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict,
    intent_data: dict,
    message_text: str,
) -> None:
    """Show meetings for today, tomorrow, or this week. Detects free-slot queries."""
    user_id = user["id"]
    entities = intent_data.get("entities", {})
    day_hint = entities.get("day", "").lower()
    msg_lower = message_text.lower()

    # Free slot detection
    wants_free = any(kw in msg_lower for kw in [
        "wolne okna", "wolny czas", "kiedy wolny", "wolne terminy",
        "kiedy mogę", "wolna godzina", "kiedy mam czas",
    ])
    if wants_free:
        today = date.today()
        if "jutro" in day_hint or "jutro" in msg_lower:
            target = today + timedelta(days=1)
        else:
            target = today
        slots = await get_free_slots(user_id, target)
        if not slots:
            await update.effective_message.reply_text(
                f"Brak wolnych okien na {target.strftime('%d.%m')} (9:00–18:00)."
            )
        else:
            lines = [f"🕐 Wolne okna na {target.strftime('%d.%m')}:"]
            for slot_start, slot_end in slots[:8]:
                lines.append(f"• {slot_start.strftime('%H:%M')}–{slot_end.strftime('%H:%M')}")
            await update.effective_message.reply_text("\n".join(lines))
        return

    today = date.today()
    if "jutro" in day_hint or "tomorrow" in day_hint:
        target = today + timedelta(days=1)
        events = await get_events_for_date(user_id, target)
    elif "tydzień" in day_hint or "week" in day_hint:
        start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
        end = start + timedelta(days=7)
        events = await get_events_for_range(user_id, start, end)
    else:
        events = await get_events_for_date(user_id, today)

    schedule = format_daily_schedule(events)
    await update.effective_message.reply_markdown_v2(schedule)


async def handle_reschedule_meeting(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict,
    intent_data: dict,
    message_text: str,
) -> None:
    """Placeholder — tell user to specify which meeting to reschedule."""
    await update.effective_message.reply_text(
        "Podaj nazwę lub datę spotkania które chcesz przełożyć, oraz nowy termin."
    )


async def handle_cancel_meeting(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict,
    intent_data: dict,
    message_text: str,
) -> None:
    """Placeholder — tell user to specify which meeting to cancel."""
    await update.effective_message.reply_text(
        "Podaj nazwę lub datę spotkania które chcesz odwołać."
    )


async def handle_show_pipeline(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict,
    intent_data: dict,
    message_text: str,
) -> None:
    """Show pipeline statistics."""
    user_id = user["id"]
    stats = await get_pipeline_stats(user_id)
    dashboard_url = user.get("dashboard_url", "")

    msg = format_pipeline_stats(stats)
    if dashboard_url:
        msg += f"\n\n[Otwórz dashboard]({escape_markdown_v2(dashboard_url)})"

    await update.effective_message.reply_markdown_v2(msg)


async def handle_filter_clients(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict,
    intent_data: dict,
    message_text: str,
) -> None:
    """Filter clients by city, status, or product."""
    user_id = user["id"]
    telegram_id = update.effective_user.id
    entities = intent_data.get("entities", {})
    city_filter = entities.get("city", "").strip().lower()
    status_filter = entities.get("status", "").strip().lower()
    product_filter = entities.get("product", "").strip().lower()

    await send_typing(context, telegram_id)
    clients = await get_all_clients(user_id)
    if not clients:
        await update.effective_message.reply_text("Brak klientów w bazie.")
        return

    filtered = clients
    if city_filter:
        filtered = [c for c in filtered if city_filter in c.get("Miasto", "").lower()]
    if status_filter:
        filtered = [c for c in filtered if status_filter in c.get("Status", "").lower()]
    if product_filter:
        filtered = [c for c in filtered if product_filter in c.get("Produkt", "").lower()]

    if not filtered:
        await update.effective_message.reply_text("Brak klientów spełniających kryteria.")
        return

    lines = [f"Mam {len(filtered)} klientów:"]
    for c in filtered[:20]:
        name = c.get("Imię i nazwisko", "?")
        city = c.get("Miasto", "")
        status = c.get("Status", "")
        line = f"• {name}" + (f" — {city}" if city else "") + (f" ({status})" if status else "")
        lines.append(line)
    if len(filtered) > 20:
        lines.append(f"...i {len(filtered) - 20} więcej")

    await update.effective_message.reply_text("\n".join(lines))


async def handle_change_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict,
    intent_data: dict,
    message_text: str,
) -> None:
    """Find client and propose status change."""
    user_id = user["id"]
    telegram_id = update.effective_user.id
    entities = intent_data.get("entities", {})
    query = entities.get("name") or message_text
    new_status = entities.get("status", "")

    results = await search_clients(user_id, query)
    if not results:
        await update.effective_message.reply_text(f"Nie znalazłem klienta: '{query}'")
        return

    client = results[0]
    old_status = client.get("Status", "")

    if not new_status:
        pipeline_statuses = user.get("pipeline_statuses", [])
        if pipeline_statuses:
            options = [(s, f"set_status:{client.get('_row')}:{s}") for s in pipeline_statuses]
            await update.effective_message.reply_text(
                f"Wybierz nowy status dla {client.get('Imię i nazwisko', 'klienta')}:",
                reply_markup=build_choice_buttons(options),
            )
            return

    save_pending_flow(telegram_id, "change_status", {
        "row": client.get("_row"),
        "field": "Status",
        "old_value": old_status,
        "new_value": new_status,
    })

    await update.effective_message.reply_markdown_v2(
        f"Zmienić status klienta *{escape_markdown_v2(client.get('Imię i nazwisko', ''))}*?\n"
        + format_edit_comparison("Status", old_status, new_status),
        reply_markup=build_confirm_buttons("confirm"),
    )


async def handle_confirm(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict,
    intent_data: dict,
    message_text: str,
) -> None:
    """Execute the pending flow action."""
    telegram_id = update.effective_user.id
    user_id = user["id"]

    flow = get_pending_flow(telegram_id)
    if not flow:
        await update.effective_message.reply_text("Nie ma nic do potwierdzenia.")
        return

    flow_type = flow.get("flow_type", "")
    flow_data = flow.get("flow_data", {})

    if flow_data.get("_cancelling"):
        delete_pending_flow(telegram_id)
        await update.effective_message.reply_text("🫡 Anulowane.")
        return

    # skip_delete: set True when we save a new flow inside the handler so the
    # finally block doesn't immediately delete it (delete_pending_flow removes
    # ALL flows for this telegram_id, including the one we just saved).
    skip_delete = False

    try:
        if flow_type == "add_client":
            remaining = flow_data.get("_offer_remaining", [])
            row = await add_client(user_id, flow_data["client_data"])
            if row:
                name = flow_data["client_data"].get("Imię i nazwisko", "klient")
                if remaining:
                    next_client = remaining[0]
                    new_remaining = remaining[1:]
                    save_pending_flow(telegram_id, "add_client", {
                        "client_data": {"Imię i nazwisko": next_client},
                        "_offer_remaining": new_remaining,
                    })
                    await update.effective_message.reply_text(
                        f"✅ {name} dodany. Podaj dane {next_client} — adres, telefon, produkt."
                    )
                    skip_delete = True
                else:
                    await update.effective_message.reply_text("✅ Zapisane.")
            else:
                await update.effective_message.reply_markdown_v2(format_error("google_down"))

        elif flow_type == "add_client_duplicate":
            row = await add_client(user_id, flow_data["client_data"])
            if row:
                await update.effective_message.reply_text("✅ Zapisane.")
            else:
                await update.effective_message.reply_markdown_v2(format_error("google_down"))

        elif flow_type == "edit_client":
            updates = flow_data["updates"]
            append_fields = flow_data.get("append_fields", [])
            old_values = flow_data.get("old_values", {})
            # For append fields: prepend existing value so nothing is lost
            final_updates = {}
            for field, new_val in updates.items():
                if field in append_fields and old_values.get(field):
                    final_updates[field] = f"{old_values[field]}; {new_val}"
                else:
                    final_updates[field] = new_val
            ok = await update_client(user_id, flow_data["row"], final_updates)
            if ok:
                await update.effective_message.reply_text("✅ Zapisane.")
            else:
                await update.effective_message.reply_markdown_v2(format_error("google_down"))

        elif flow_type == "delete_client":
            from shared.google_sheets import delete_client
            ok = await delete_client(user_id, flow_data["row"])
            if ok:
                await update.effective_message.reply_text("✅ Klient usunięty z arkusza.")
            else:
                await update.effective_message.reply_markdown_v2(format_error("google_down"))

        elif flow_type == "add_meeting":
            start = datetime.fromisoformat(flow_data["start"])
            end = datetime.fromisoformat(flow_data["end"])
            event = await create_event(
                user_id,
                title=flow_data.get("title", "Spotkanie"),
                start=start,
                end=end,
                location=flow_data.get("location") or None,
                description=flow_data.get("description") or None,
            )
            if event:
                client_name = flow_data.get("client_name", "")
                in_sheets = bool(client_name and await search_clients(user_id, client_name))
                if not in_sheets and client_name:
                    save_pending_flow(telegram_id, "offer_add_client", {"client_name": client_name})
                    await update.effective_message.reply_text(
                        f"✅ Spotkanie dodane. Nie mam {client_name} w bazie. Dodać?",
                        reply_markup=build_confirm_buttons("confirm"),
                    )
                    skip_delete = True
                else:
                    await update.effective_message.reply_text("✅ Spotkanie dodane do kalendarza.")
            else:
                await update.effective_message.reply_markdown_v2(format_error("calendar_down"))

        elif flow_type == "add_meetings":
            created = []
            failed = []
            for fm in flow_data.get("meetings", []):
                start = datetime.fromisoformat(fm["start"])
                end = datetime.fromisoformat(fm["end"])
                event = await create_event(
                    user_id,
                    title=fm.get("title", "Spotkanie"),
                    start=start, end=end,
                    location=fm.get("location") or None,
                    description=fm.get("description") or None,
                )
                if event:
                    created.append(fm)
                else:
                    failed.append(fm.get("client_name", "?"))

            missing_from_sheets = []
            for fm in created:
                name = fm.get("client_name", "")
                if name and not await search_clients(user_id, name):
                    missing_from_sheets.append(name)

            msg_parts = [f"✅ Dodano {len(created)} spotkań."]
            if failed:
                msg_parts.append(f"❌ Nie udało się: {', '.join(failed)}.")
            if missing_from_sheets:
                names_str = ", ".join(missing_from_sheets)
                save_pending_flow(telegram_id, "offer_add_clients", {"names": missing_from_sheets})
                msg_parts.append(f"Nie mam w bazie: {names_str}. Dodać?")
                await update.effective_message.reply_text(
                    "\n".join(msg_parts),
                    reply_markup=build_confirm_buttons("confirm"),
                )
                skip_delete = True
            else:
                await update.effective_message.reply_text("\n".join(msg_parts))

        elif flow_type == "offer_add_client":
            client_name = flow_data.get("client_name", "")
            if client_name:
                save_pending_flow(telegram_id, "add_client", {
                    "client_data": {"Imię i nazwisko": client_name},
                })
                await update.effective_message.reply_text(
                    f"Podaj dane {client_name} — adres, telefon, produkt."
                )
                skip_delete = True
            else:
                await update.effective_message.reply_text("Brak klienta do dodania.")

        elif flow_type == "offer_add_clients":
            names = flow_data.get("names", [])
            if names:
                first = names[0]
                new_remaining = names[1:]
                save_pending_flow(telegram_id, "add_client", {
                    "client_data": {"Imię i nazwisko": first},
                    "_offer_remaining": new_remaining,
                })
                await update.effective_message.reply_text(
                    f"Podaj dane {first} — adres, telefon, produkt."
                )
                skip_delete = True
            else:
                await update.effective_message.reply_text("Brak klientów do dodania.")

        elif flow_type == "change_status":
            ok = await update_client(user_id, flow_data["row"], {flow_data["field"]: flow_data["new_value"]})
            if ok:
                await update.effective_message.reply_text(f"✅ Status zmieniony na: {flow_data['new_value']}")
            else:
                await update.effective_message.reply_markdown_v2(format_error("google_down"))

        elif flow_type == "confirm_search":
            row = flow_data.get("row")
            all_clients = await get_all_clients(user_id)
            client = next((c for c in all_clients if c.get("_row") == row), None)
            if client:
                try:
                    card = format_client_card(client)
                    await update.effective_message.reply_markdown_v2(card)
                except Exception as e:
                    logger.error("format_client_card failed: %s", e)
                    name = client.get("Imię i nazwisko", "?")
                    city = client.get("Miasto", "")
                    await update.effective_message.reply_text(
                        f"Błąd formatowania karty dla {name}{' (' + city + ')' if city else ''}. Sprawdź logi."
                    )
            else:
                await update.effective_message.reply_text("Nie znalazłem tego klienta.")

        else:
            await update.effective_message.reply_text("✅ Gotowe.")

    except Exception as e:
        logger.error("handle_confirm(flow_type=%s): %s", flow_type, e)
        await update.effective_message.reply_markdown_v2(format_error("timeout"))
    finally:
        if not skip_delete:
            delete_pending_flow(telegram_id)


async def handle_cancel_flow(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict,
    intent_data: dict,
    message_text: str,
) -> None:
    """Cancel flow: ask once, delete on confirm."""
    telegram_id = update.effective_user.id
    flow = get_pending_flow(telegram_id)
    if not flow:
        return

    flow_data = flow.get("flow_data", {})

    if flow_data.get("_cancelling"):
        # User tapped [Nie] on the "Anulować?" question — keep flow, re-show card silently
        flow_data.pop("_cancelling")
        save_pending_flow(telegram_id, flow["flow_type"], flow_data)
        if flow["flow_type"] == "add_client":
            user_id = user["id"]
            headers = await get_sheet_headers(user_id)
            sheet_columns = user.get("sheet_columns") or headers
            client_data = flow_data.get("client_data", {})
            missing = [col for col in sheet_columns if col and not client_data.get(col) and col not in SYSTEM_FIELDS]
            card = format_add_client_card(client_data, missing)
            await update.effective_message.reply_text(card, reply_markup=build_save_buttons("confirm"))
        return

    # First cancel request: set flag, ask with buttons
    flow_data["_cancelling"] = True
    save_pending_flow(telegram_id, flow["flow_type"], flow_data)
    await update.effective_message.reply_text(
        "Anulować?",
        reply_markup=build_confirm_buttons("confirm"),
    )


async def handle_refresh_columns(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict,
    intent_data: dict,
    message_text: str,
) -> None:
    """Force-refresh sheet column headers from Google Sheets and update Supabase cache."""
    user_id = user["id"]
    headers = await get_sheet_headers(user_id)  # already updates Supabase on success
    if headers:
        cols = ", ".join(headers)
        await update.effective_message.reply_text(f"✅ Odświeżono kolumny. Mam teraz: {cols}.")
    else:
        await update.effective_message.reply_markdown_v2(format_error("google_down"))


async def handle_general(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict,
    intent_data: dict,
    message_text: str,
) -> None:
    """Handle general questions via Claude."""
    telegram_id = update.effective_user.id
    history = get_conversation_history(telegram_id, limit=10)

    pipeline_statuses = user.get("pipeline_statuses", [])
    system_context = (
        "Jesteś asystentem handlowca OZE w Polsce. Zarządzasz klientami, spotkaniami i lejkiem. "
        "Masz pełny dostęp do Google Calendar, Google Sheets i Google Drive użytkownika. "
        f"Statusy lejka: {pipeline_statuses}. "
        "Odpowiadaj BARDZO krótko — maksimum 2 zdania. "
        "Ton: konkretny, bez entuzjazmu, bez formalności. "
        "NIGDY nie używaj: 'Oczywiście', 'Z przyjemnością', 'Świetnie', 'Czekam na polecenia', "
        "'Czy mogę w czymś pomóc', 'Mam nadzieję', 'Nie ma problemu', 'Rozumiem Twoją frustrację'. "
        "Jeśli wiadomość to dane klienta (imię, miasto, telefon, produkt) — odpowiedz 'Co chcesz zrobić?' "
        "Jeśli wiadomość jest niezrozumiała (losowe znaki, brak sensu) — odpowiedz 'Co chcesz zrobić?' "
        "Bez propozycji. Tylko odpowiedź na to co zostało zapytane."
    )

    result = await generate_bot_response(system_context, message_text, history)
    response_text = result.get("text", "Nie rozumiem. Spróbuj ponownie.")

    save_conversation_message(telegram_id, "assistant", response_text)

    await update.effective_message.reply_text(response_text)

    await increment_interaction(
        telegram_id,
        "general_question",
        result.get("model", ""),
        result.get("tokens_in", 0),
        result.get("tokens_out", 0),
        result.get("cost_usd", 0.0),
    )
