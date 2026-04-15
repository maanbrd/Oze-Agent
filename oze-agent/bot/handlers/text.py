"""Text message handler — main intent router for OZE-Agent bot."""

import logging
import re
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

WARSAW = ZoneInfo("Europe/Warsaw")

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.telegram_helpers import (
    build_mutation_buttons,
    build_confirm_cancel_buttons,
    build_duplicate_buttons,
    build_choice_buttons,
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
    extract_client_data,
    extract_meeting_data,
    extract_note_data,
    generate_bot_response,
)
from shared.intent import IntentResult, IntentType, ScopeTier, classify
from shared.pending import (
    AddClientDuplicatePayload,
    AddClientPayload,
    PendingFlow,
    PendingFlowType,
    payload_to_flow_data,
    save as save_pending,
)
from bot.handlers.banners import banner_for_legacy
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
    escape_markdown_v2,
)
from shared.google_calendar import (
    check_conflicts,
    create_event,
    get_events_for_date,
    get_events_for_range,
)
from shared.google_sheets import (
    add_client,
    get_all_clients,
    get_sheet_headers,
    search_clients,
    update_client,
)
from shared.search import detect_potential_duplicate

logger = logging.getLogger(__name__)

# Fields managed automatically — never show as "missing" to the user
SYSTEM_FIELDS = {
    "Data pierwszego kontaktu", "Data ostatniego kontaktu", "Status",
    "Zdjęcia", "Link do zdjęć", "ID wydarzenia Kalendarz", "Data następnego kroku",
}

# Canonical 9-status pipeline per INTENCJE_MVP.md (frozen)
_VALID_STATUSES = [
    "Nowy lead",
    "Spotkanie umówione",
    "Spotkanie odbyte",
    "Oferta wysłana",
    "Podpisane",
    "Zamontowana",
    "Rezygnacja z umowy",
    "Nieaktywny",
    "Odrzucone",
]
_VALID_STATUSES_LOWER = {s.lower() for s in _VALID_STATUSES}

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

_BANNER_INTENTS = frozenset({
    IntentType.POST_MVP_ROADMAP,
    IntentType.VISION_ONLY,
    IntentType.UNPLANNED,
    IntentType.MULTI_MEETING,
})


def _intent_result_to_legacy_dict(result: IntentResult, message_text: str) -> dict:
    entities = dict(result.entities)
    if result.intent is IntentType.CHANGE_STATUS and "client_name" in entities:
        entities["name"] = entities.pop("client_name")
    return {
        "intent": result.intent.value,
        "entities": entities,
        "confidence": result.confidence,
        "feature_key": result.feature_key,
        "reason": result.reason,
    }


def _message_with_r7_client_context(message_text: str, flow_data: dict) -> str:
    client_name = (flow_data.get("client_name") or "").strip()
    if not client_name:
        return message_text

    text_lower = message_text.lower()
    name_parts = [p for p in re.split(r"\s+", client_name.lower()) if len(p) > 2]
    if any(part in text_lower for part in name_parts):
        return message_text
    if re.search(r"\bz\s+\S+", text_lower):
        return message_text

    city = (flow_data.get("city") or "").strip()
    context = client_name
    if city and city.lower() not in text_lower:
        context = f"{context} {city}"
    return f"{message_text} z {context}"


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

    # Pre-check: "statusy" command → return formatted list, skip LLM
    if message_text.lower().strip() in ("statusy", "lista statusów", "jakie są statusy", "pokaż statusy"):
        statuses_text = "📋 Dostępne statusy lejka:\n" + "\n".join(f"• {s}" for s in _VALID_STATUSES)
        await update.effective_message.reply_text(statuses_text)
        await increment_interaction(telegram_id, "show_statuses", "none", 0, 0, 0.0)
        return

    # Check for active pending flow first
    pending_flow = get_pending_flow(telegram_id)
    if pending_flow:
        consumed = await _route_pending_flow(update, context, user, pending_flow, message_text)
        if consumed:
            return
        # Flow was auto-cancelled — fall through to process the new message normally

    # Save message and get history
    save_conversation_message(telegram_id, "user", message_text)

    # Classify intent via the structured router (shared.intent.classify pulls
    # its own 30-min history window internally).
    result = await classify(message_text, telegram_id)

    # Defensive temporal guard — schema requires date_iso for add_meeting,
    # but the LLM can still hallucinate. Demote to add_client without markers.
    if result.intent is IntentType.ADD_MEETING:
        msg_lower = message_text.lower()
        has_temporal = (
            any(w in msg_lower for w in _TEMPORAL_MARKERS)
            or bool(_TIME_RE.search(msg_lower))
        )
        if not has_temporal:
            result = replace(
                result,
                intent=IntentType.ADD_CLIENT,
                scope_tier=ScopeTier.MVP,
            )

    intent_data = _intent_result_to_legacy_dict(result, message_text)

    handler = _HANDLERS.get(result.intent, handle_general)
    await handler(update, context, user, intent_data, message_text)

    await increment_interaction(
        telegram_id, result.intent.value, "claude-haiku-4-5-20251001", 0, 0, 0.0
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
        # If the message starts with a search/action verb, auto-cancel and re-process
        _search_prefixes = (
            "pokaż", "znajdź", "szukaj", "plan na", "co mam", "zmień status",
            "zmień", "dodaj notatkę", "notatka", "spotkanie z", "umów spotkanie",
            "kto ma numer", "kto to",
        )
        if any(text_lower.startswith(p) for p in _search_prefixes):
            telegram_id = update.effective_user.id
            delete_pending_flow(telegram_id)
            await update.effective_message.reply_text("⚠️ Anulowane.")
            return False

        # User is augmenting an in-progress add_client flow with more data
        telegram_id = update.effective_user.id
        user_id = user["id"]
        old_flow_data = flow.get("flow_data", {})
        old_client_data = old_flow_data.get("client_data", {})

        headers = await get_sheet_headers(user_id)
        result = await extract_client_data(message_text, headers)
        new_data = {k: v for k, v in _filter_invalid_products(result.get("client_data", {})).items() if v}
        logger.info("augment add_client: new_data=%s", new_data)

        if not new_data:
            # Claude extracted nothing — re-show existing card unchanged
            sheet_columns = user.get("sheet_columns") or headers
            missing = [col for col in sheet_columns if col and not old_client_data.get(col) and col not in SYSTEM_FIELDS]
            card = format_add_client_card(old_client_data, missing)
            await update.effective_message.reply_text(card, reply_markup=build_mutation_buttons("confirm"))
            return True

        # If the new message names a different client → start fresh, don't merge
        old_name = old_client_data.get("Imię i nazwisko", "").strip()
        new_name = new_data.get("Imię i nazwisko", "").strip()
        if old_name and new_name and old_name.lower() != new_name.lower():
            sheet_columns = user.get("sheet_columns") or headers
            missing = [col for col in sheet_columns if col and not new_data.get(col) and col not in SYSTEM_FIELDS]
            save_pending(PendingFlow(
                telegram_id=telegram_id,
                flow_type=PendingFlowType.ADD_CLIENT,
                flow_data=payload_to_flow_data(AddClientPayload(client_data=new_data)),
            ))
            card = format_add_client_card(new_data, missing)
            await update.effective_message.reply_text(card, reply_markup=build_mutation_buttons("confirm"))
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
                    save_pending(PendingFlow(
                        telegram_id=telegram_id,
                        flow_type=PendingFlowType.ADD_CLIENT,
                        flow_data=payload_to_flow_data(AddClientPayload(
                            client_data={"Imię i nazwisko": next_client},
                            _offer_remaining=new_remaining,
                        )),
                    ))
                    await update.effective_message.reply_text(
                        f"✅ {name} dodany. Podaj dane {next_client} — adres, telefon, produkt."
                    )
                else:
                    await update.effective_message.reply_text("✅ Zapisane.")
            else:
                await update.effective_message.reply_markdown_v2(format_error("google_down"))
            return True

        # User is correcting/adding data (possibly after tapping [Nie]) — clear cancel flag, re-show card
        offer_remaining = old_flow_data.get("_offer_remaining") or None
        save_pending(PendingFlow(
            telegram_id=telegram_id,
            flow_type=PendingFlowType.ADD_CLIENT,
            flow_data=payload_to_flow_data(AddClientPayload(
                client_data=merged,
                _offer_remaining=offer_remaining,
            )),
        ))
        card = format_add_client_card(merged, missing)
        await update.effective_message.reply_text(card, reply_markup=build_mutation_buttons("confirm"))
        return True
    elif flow_type == "add_note":
        telegram_id = update.effective_user.id
        # If the message starts with a known action prefix, auto-cancel and re-process
        _search_prefixes = (
            "pokaż", "znajdź", "szukaj", "plan na", "co mam", "zmień status",
            "zmień", "dodaj notatkę", "notatka", "spotkanie z", "umów spotkanie",
            "kto ma numer", "kto to",
        )
        if any(text_lower.startswith(p) for p in _search_prefixes):
            delete_pending_flow(telegram_id)
            await update.effective_message.reply_text("⚠️ Anulowane.")
            return False

        # User is appending more text after clicking Dopisać on add_note
        flow_data = flow.get("flow_data", {})
        existing_note = flow_data.get("note_text", "")
        new_note = f"{existing_note} {message_text}".strip() if existing_note else message_text
        new_flow_data = {**flow_data, "note_text": new_note}
        save_pending_flow(telegram_id, "add_note", new_flow_data)

        display_note = new_note[:80] + ("..." if len(new_note) > 80 else "")
        name = flow_data.get("client_name", "")
        c_city = flow_data.get("city", "")
        city_part = f", {c_city}" if c_city else ""
        await update.effective_message.reply_text(
            f"📝 {name}{city_part}:\ndodaj notatkę \"{display_note}\"?",
            reply_markup=build_mutation_buttons("confirm"),
        )
        return True
    elif flow_type == "r7_prompt":
        # R7 next-action response: temporal marker → add_meeting, otherwise close
        telegram_id = update.effective_user.id
        delete_pending_flow(telegram_id)
        _cancel_single = {"nie", "anuluj", "stop", "nic", "later"}
        _cancel_phrases = {"nie wiem", "odłóż", "odłożyć"}
        text_words = set(text_lower.split())
        if (text_words & _cancel_single) or any(p in text_lower for p in _cancel_phrases):
            return True
        has_temporal = (
            any(w in text_lower for w in _TEMPORAL_MARKERS)
            or bool(_TIME_RE.search(text_lower))
        )
        if has_temporal:
            meeting_text = _message_with_r7_client_context(
                message_text, flow.get("flow_data", {})
            )
            await handle_add_meeting(update, context, user, {}, meeting_text)
        # Otherwise: unclear reply → consume silently (don't re-classify as add_client)
        return True
    else:
        # New message arrived during a non-add_client pending flow → auto-cancel, process message normally
        telegram_id = update.effective_user.id
        delete_pending_flow(telegram_id)
        await update.effective_message.reply_text("⚠️ Anulowane.")
        return False


# ── Sub-handlers ──────────────────────────────────────────────────────────────


async def handle_banner(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict,
    intent_data: dict,
    message_text: str,
) -> None:
    """R5 / out-of-scope banner — copy resolved from intent + feature_key."""
    await update.effective_message.reply_text(banner_for_legacy(intent_data))


async def handle_add_note(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict,
    intent_data: dict,
    message_text: str,
) -> None:
    """Add note to existing client — R1 card, append to Notatki with date prefix."""
    telegram_id = update.effective_user.id
    user_id = user["id"]

    await send_typing(context, telegram_id)

    result = await extract_note_data(message_text)
    client_name = result.get("client_name", "")
    city = result.get("city", "")
    note_text = result.get("note", "")

    if not client_name or not note_text:
        await update.effective_message.reply_text(
            "Podaj imię i nazwisko klienta, miasto i treść notatki.\n"
            "Np.: 'dodaj notatkę do Jana Kowalskiego z Warszawy: dzwonił w sprawie gwarancji'"
        )
        return

    query = f"{client_name} {city}".strip()
    results = await search_clients(user_id, query)
    if not results:
        city_part = f" ({city})" if city else ""
        await update.effective_message.reply_text(
            f"Nie znalazłem klienta: '{client_name}{city_part}'"
        )
        return

    if len(results) > 1:
        # Exact full-name match short-circuits disambiguation (bug-F2-2)
        client = _find_exact_name_match(client_name, results)
        if not client:
            client = next((r for r in results if _first_name_ok(query, r)), None)
        if not client:
            lines = [f"Mam {len(results)} klientów:"]
            options = []
            for i, c in enumerate(results[:10], start=1):
                c_name = c.get("Imię i nazwisko", "?")
                c_city = c.get("Miasto", "")
                c_row = c.get("_row", 0)
                label = f"{i}. {c_name}" + (f" — {c_city}" if c_city else "")
                lines.append(label)
                options.append((label, f"select_client:{c_row}"))
            lines.append("Którego?")
            save_pending_flow(telegram_id, "disambiguation", {
                "intent": "add_note",
                "note_text": note_text,
            })
            await update.effective_message.reply_text(
                "\n".join(lines),
                reply_markup=build_choice_buttons(options),
            )
            return
    else:
        client = next((r for r in results if _first_name_ok(query, r)), None)
        if not client:
            city_part = f" ({city})" if city else ""
            await update.effective_message.reply_text(
                f"Nie znalazłem '{client_name}{city_part}' w bazie."
            )
            return

    row = client.get("_row")
    old_notes = client.get("Notatki", "")
    name = client.get("Imię i nazwisko", client_name)
    c_city = client.get("Miasto", city)

    save_pending_flow(telegram_id, "add_note", {
        "row": row,
        "note_text": note_text,
        "client_name": name,
        "city": c_city,
        "old_notes": old_notes,
    })

    display_note = note_text[:80] + ("..." if len(note_text) > 80 else "")
    city_part = f", {c_city}" if c_city else ""
    await update.effective_message.reply_text(
        f"📝 {name}{city_part}:\ndodaj notatkę \"{display_note}\"?",
        reply_markup=build_mutation_buttons("confirm"),
    )


async def handle_add_client(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict,
    intent_data: dict,
    message_text: str,
) -> None:
    """Extract client data, check for duplicates, show R1 confirmation card."""
    telegram_id = update.effective_user.id
    user_id = user["id"]

    await send_typing(context, telegram_id)

    headers = await get_sheet_headers(user_id)
    result = await extract_client_data(message_text, headers)
    client_data = _filter_invalid_products(result.get("client_data", {}))

    if not client_data:
        await update.effective_message.reply_text("Co chcesz zrobić?")
        return

    # Duplicate check
    all_clients = await get_all_clients(user_id)
    name = client_data.get("Imię i nazwisko", "")
    city = client_data.get("Miasto", "")
    duplicate = detect_potential_duplicate(name, city, all_clients) if name else None

    if duplicate:
        dup_name = duplicate.get("Imię i nazwisko", "")
        dup_city = duplicate.get("Miasto", "")
        # Detect field conflicts: new data has a different non-empty value than existing
        has_conflict = any(
            v and duplicate.get(k) and duplicate.get(k) != v
            for k, v in client_data.items()
            if k not in SYSTEM_FIELDS and k != "Imię i nazwisko"
        )
        if not has_conflict:
            # Default merge path: show R1 confirmation card (R1 rule — no silent writes)
            new_data = {k: v for k, v in client_data.items() if v and k not in SYSTEM_FIELDS}
            duplicate_row = duplicate.get("_row")
            if duplicate_row is None:
                logger.error("handle_add_client: duplicate without _row: %s", duplicate)
                await update.effective_message.reply_markdown_v2(format_error("timeout"))
                return
            save_pending(PendingFlow(
                telegram_id=telegram_id,
                flow_type=PendingFlowType.ADD_CLIENT_DUPLICATE,
                flow_data=payload_to_flow_data(AddClientDuplicatePayload(
                    client_data=new_data,
                    duplicate_row=duplicate_row,
                    client_name=duplicate.get("Imię i nazwisko", ""),
                    city=duplicate.get("Miasto", ""),
                )),
            ))
            updated_fields = ", ".join(new_data.keys())
            city_part = f" ({dup_city})" if dup_city else ""
            await update.effective_message.reply_text(
                f"Mam już {dup_name}{city_part}.\nZaktualizować o: {updated_fields}?",
                reply_markup=build_mutation_buttons("confirm"),
            )
            return
        # Conflict: ask user to choose
        duplicate_row = duplicate.get("_row")
        if duplicate_row is None:
            logger.error("handle_add_client: duplicate without _row: %s", duplicate)
            await update.effective_message.reply_markdown_v2(format_error("timeout"))
            return
        save_pending(PendingFlow(
            telegram_id=telegram_id,
            flow_type=PendingFlowType.ADD_CLIENT_DUPLICATE,
            flow_data=payload_to_flow_data(AddClientDuplicatePayload(
                client_data=client_data,
                duplicate_row=duplicate_row,
                client_name=duplicate.get("Imię i nazwisko", ""),
                city=duplicate.get("Miasto", ""),
            )),
        ))
        dup_addr = duplicate.get("Adres", "")
        dup_prod = duplicate.get("Produkt", "")
        dup_info = ", ".join(p for p in [dup_addr, dup_city, dup_prod] if p)
        await update.effective_message.reply_text(
            f"⚠️ Masz już {dup_name} ({dup_info}).\nDodać nowego czy dopisać do istniejącego?",
            reply_markup=build_duplicate_buttons("confirm"),
        )
        return

    # Always compute missing from actual sheet column names (never trust Claude's guesses)
    sheet_columns = user.get("sheet_columns") or headers
    missing = [col for col in sheet_columns if col and not client_data.get(col) and col not in SYSTEM_FIELDS]

    save_pending(PendingFlow(
        telegram_id=telegram_id,
        flow_type=PendingFlowType.ADD_CLIENT,
        flow_data=payload_to_flow_data(AddClientPayload(client_data=client_data)),
    ))

    card = format_add_client_card(client_data, missing)
    await update.effective_message.reply_text(card, reply_markup=build_mutation_buttons("confirm"))


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
    entities = intent_data.get("entities", {})
    query = entities.get("name") or entities.get("phone") or message_text

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
        # Exception: phone-number queries are inherently exact matches (matched on digits).
        _query_digits = re.sub(r"\D", "", query)
        _is_phone = len(_query_digits) >= 7 and len(query.strip()) <= len(_query_digits) + 4
        is_exact = query_lower in name_lower or name_lower in query_lower or _is_phone
        if not is_exact:
            city = client.get("Miasto", "")
            suggestion = client_name + (f" z {city}" if city else "")
            save_pending_flow(telegram_id, "confirm_search", {"row": client.get("_row")})
            await update.effective_message.reply_text(
                f"Nie mam \"{query}\". Chodziło o {suggestion}?",
                reply_markup=build_choice_buttons([
                    ("✅ Tak, pokaż", "confirm:yes"),
                    ("❌ Nie", "cancel:search"),
                ]),
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

    # 2–49 results: try exact/first-name match before disambiguation
    # Only use first-name guard when query has 2+ words (i.e., includes a first name).
    # Single-word queries like "Kowalski" must go to disambiguation.
    client = _find_exact_name_match(query, results)
    if not client and len(query.strip().split()) >= 2:
        client = next((r for r in results if _first_name_ok(query, r)), None)
    if client:
        try:
            card = format_client_card(client)
            await update.effective_message.reply_markdown_v2(card)
        except Exception as e:
            logger.error("format_client_card failed: %s", e)
            cname = client.get("Imię i nazwisko", "?")
            ccity = client.get("Miasto", "")
            await update.effective_message.reply_text(
                f"Błąd formatowania karty dla {cname}{' (' + ccity + ')' if ccity else ''}. Sprawdź logi."
            )
        return

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

    await update.effective_message.reply_text(msg, reply_markup=build_mutation_buttons("confirm"))


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
        await update.effective_message.reply_text(msg, reply_markup=build_mutation_buttons("confirm"))

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
        await update.effective_message.reply_text(msg, reply_markup=build_mutation_buttons("confirm"))

    elif tool_name == "request_clarification":
        reason = tool_input.get("reason", "Nie rozumiem co chcesz zmienić. Opisz dokładniej.")
        await update.effective_message.reply_text(reason)

    else:
        text = result.get("text") or "Nie rozpoznałem co chcesz zmienić. Opisz dokładniej."
        logger.warning("handle_edit_client_v2: no tool called, text=%r", text[:100])
        await update.effective_message.reply_text(text)


def _filter_invalid_products(client_data: dict) -> dict:
    """Remove non-OZE products (e.g. 'klimatyzacja') from Produkt.

    Also normalizes Notatki when the LLM puts klimatyzacja there directly.
    Valid OZE products: PV, Pompa ciepła, Magazyn energii, PV + Magazyn energii.
    """
    _INVALID_KEYWORDS = {"klimatyzacj", "klima"}
    product = client_data.get("Produkt", "")
    existing_notes = client_data.get("Notatki", "")

    parts = [p.strip() for p in product.split(",")] if product else []
    valid_parts = [p for p in parts if not any(kw in p.lower() for kw in _INVALID_KEYWORDS)]
    invalid_parts = [p for p in parts if any(kw in p.lower() for kw in _INVALID_KEYWORDS)]

    notes_has_klima = any(kw in existing_notes.lower() for kw in _INVALID_KEYWORDS) if existing_notes else False

    if not invalid_parts and not notes_has_klima:
        return client_data

    client_data = dict(client_data)

    if invalid_parts:
        client_data["Produkt"] = ", ".join(valid_parts)

    labels = invalid_parts if invalid_parts else ["klimatyzacja"]
    standard_note = "Produkt nieobsługiwany: " + ", ".join(labels)

    if notes_has_klima:
        # LLM wrote klimatyzacja in Notatki — replace with standard wording
        client_data["Notatki"] = standard_note
    else:
        client_data["Notatki"] = f"{existing_notes} {standard_note}".strip() if existing_notes else standard_note

    return client_data


def _find_exact_name_match(name_query: str, results: list) -> dict | None:
    """Return the first result whose stored full name exactly matches name_query.

    Comparison is normalized (lowercase, no diacritics). Returns None when no
    exact match exists — caller should fall back to disambiguation.
    """
    from shared.search import normalize_polish
    q_norm = normalize_polish(name_query.strip())
    for r in results:
        stored_norm = normalize_polish(r.get("Imię i nazwisko", "").strip())
        if stored_norm == q_norm:
            return r
    return None


def _first_name_ok(query: str, client: dict) -> bool:
    """Return True if the found client's first name matches the query's first name.

    For single-word queries: always True (no first-name check possible).
    For multi-word queries: first word of query must be within edit-distance 2
    of first word of the client's stored name.
    """
    from shared.search import levenshtein_distance, normalize_polish
    q_words = query.strip().split()
    if len(q_words) < 2:
        return True  # single word — no first-name check
    q_first = normalize_polish(q_words[0])
    stored_name = client.get("Imię i nazwisko", "")
    c_words = stored_name.strip().split()
    if not c_words:
        return True
    c_first = normalize_polish(c_words[0])
    return levenshtein_distance(q_first, c_first) <= 2


def _parse_warsaw(date_str: str, time_str: str) -> datetime:
    """Parse date+time strings as Europe/Warsaw and return an aware datetime."""
    naive = datetime.fromisoformat(f"{date_str}T{time_str}:00")
    return naive.replace(tzinfo=WARSAW)


async def _enrich_meeting(user_id: str, client_name: str, location_hint: str) -> dict:
    """Look up client in Sheets and return enriched title/location/description.

    Returns dict with extra key 'client_found' (bool) indicating if the client
    was identified in Sheets. When client_name is provided but not found,
    the caller should warn the user (per INTENCJE_MVP.md R4).
    """
    full_name = client_name
    location = location_hint
    description = ""
    client_found = False

    if client_name:
        results = await search_clients(user_id, client_name)
        # If first name doesn't match, client stays None — meeting is created with
        # the original typed name and no Sheets enrichment (better than wrong client).
        client = next((r for r in results if _first_name_ok(client_name, r)), None)
        if client:
            client_found = True
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

    title = f"Spotkanie — {full_name}" if full_name else "Spotkanie"
    return {"title": title, "location": location, "description": description, "full_name": full_name, "client_found": client_found}


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

        # Temporal guard: reject past dates
        if start_dt < datetime.now(WARSAW):
            _DAYS_PL_TG = ["poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela"]
            date_display = start_dt.strftime("%d.%m.%Y") + f" ({_DAYS_PL_TG[start_dt.weekday()]})"
            await update.effective_message.reply_text(
                f"Data {date_display} o {start_dt.strftime('%H:%M')} jest w przeszłości. Podaj datę przyszłą."
            )
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
        await update.effective_message.reply_markdown_v2(msg, reply_markup=build_mutation_buttons("confirm"))

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
        await update.effective_message.reply_markdown_v2(msg, reply_markup=build_mutation_buttons("confirm"))


_DAY_NAME_TO_WEEKDAY = {
    "poniedziałek": 0, "poniedzialek": 0,
    "wtorek": 1,
    "środę": 2, "środa": 2, "srode": 2, "sroda": 2,
    "czwartek": 3,
    "piątek": 4, "piatek": 4,
    "sobotę": 5, "sobota": 5, "sobote": 5,
    "niedzielę": 6, "niedziela": 6, "niedziele": 6,
}

_MONTH_NAME_TO_NUM = {
    "stycznia": 1, "lutego": 2, "marca": 3, "kwietnia": 4, "maja": 5,
    "czerwca": 6, "lipca": 7, "sierpnia": 8, "września": 9,
    "wrzesnia": 9, "października": 10, "pazdziernika": 10,
    "listopada": 11, "grudnia": 12,
}

_DATE_DD_MONTH_RE = re.compile(
    r"(\d{1,2})\s+(" + "|".join(_MONTH_NAME_TO_NUM.keys()) + r")"
)
_DATE_DD_MM_RE = re.compile(r"(\d{1,2})\.(\d{1,2})(?:\.(\d{4}))?")


def _parse_show_day_date(message_text: str, today: date) -> date | None:
    """Parse a target date from a show_day_plan message. Returns None for week-range queries."""
    text = message_text.lower()

    # Week range
    if re.search(r"\b(ten\s+)?tydzień\b|\bweek\b|\btygodniu\b", text):
        return None  # caller handles as range

    # Relative words
    if re.search(r"\bpojutrze\b", text):
        return today + timedelta(days=2)
    if re.search(r"\bjutro\b|\btomorrow\b", text):
        return today + timedelta(days=1)
    if re.search(r"\bdziś\b|\bdzisiaj\b|\btoday\b", text):
        return today

    # Day names (next occurrence)
    for name, weekday in _DAY_NAME_TO_WEEKDAY.items():
        if name in text:
            delta = (weekday - today.weekday()) % 7
            if delta == 0:
                delta = 7  # "na poniedziałek" when today IS Monday → next week
            return today + timedelta(days=delta)

    # "DD miesiąc" e.g. "15 kwietnia"
    m = _DATE_DD_MONTH_RE.search(text)
    if m:
        day_num = int(m.group(1))
        month_num = _MONTH_NAME_TO_NUM[m.group(2)]
        year = today.year
        try:
            candidate = date(year, month_num, day_num)
            if candidate < today:
                candidate = date(year + 1, month_num, day_num)
            return candidate
        except ValueError:
            pass

    # "DD.MM" or "DD.MM.YYYY"
    m = _DATE_DD_MM_RE.search(text)
    if m:
        d_num, mo_num = int(m.group(1)), int(m.group(2))
        yr = int(m.group(3)) if m.group(3) else today.year
        try:
            return date(yr, mo_num, d_num)
        except ValueError:
            pass

    return today  # default: today


async def handle_show_day_plan(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict,
    intent_data: dict,
    message_text: str,
) -> None:
    """Show meetings for a given day (or 7-day range). Read-only — no free slots."""
    user_id = user["id"]
    today = date.today()

    target = _parse_show_day_date(message_text, today)

    if target is None:
        # Week range
        start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
        end = start + timedelta(days=7)
        events = await get_events_for_range(user_id, start, end)
    else:
        events = await get_events_for_date(user_id, target)

    schedule = format_daily_schedule(events, target or today)
    await update.effective_message.reply_markdown_v2(schedule)


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

    _STATUS_MAPPING = {
        "rezygnuje": "Rezygnacja z umowy",
        "rezygnacja": "Rezygnacja z umowy",
        "odpada": "Odrzucone",
        "spadła": "Rezygnacja z umowy",
        "spadł": "Rezygnacja z umowy",
        "nieaktywny": "Nieaktywny",
        "zamontowana": "Zamontowana",
        "zamontowane": "Zamontowana",
        "zamontowali": "Zamontowana",
        "gotowe": "Zamontowana",
    }
    if new_status:
        new_status = _STATUS_MAPPING.get(new_status.lower(), new_status)

    results = await search_clients(user_id, query)
    if not results:
        await update.effective_message.reply_text(f"Nie znalazłem klienta: '{query}'")
        return

    if len(results) > 1:
        # Exact full-name match short-circuits disambiguation (bug-F2-2)
        name_hint = entities.get("name") or ""
        client = _find_exact_name_match(name_hint or query, results)
        if not client:
            client = next((r for r in results if _first_name_ok(query, r)), None)
        if not client:
            lines = [f"Mam {len(results)} klientów:"]
            options = []
            for i, c in enumerate(results[:10], start=1):
                c_name = c.get("Imię i nazwisko", "?")
                c_city = c.get("Miasto", "")
                c_row = c.get("_row", 0)
                label = f"{i}. {c_name}" + (f" — {c_city}" if c_city else "")
                lines.append(label)
                options.append((label, f"select_client:{c_row}"))
            lines.append("Którego?")
            save_pending_flow(telegram_id, "disambiguation", {
                "intent": "change_status",
                "new_status": new_status,
            })
            await update.effective_message.reply_text(
                "\n".join(lines),
                reply_markup=build_choice_buttons(options),
            )
            return
    else:
        client = next((r for r in results if _first_name_ok(query, r)), None)
        if not client:
            await update.effective_message.reply_text(
                f"Nie znalazłem '{query}' w bazie."
            )
            return

    old_status = client.get("Status", "")

    # No-op guard: new status == current status
    if new_status and old_status and old_status.lower() == new_status.lower():
        name = client.get("Imię i nazwisko", "klient")
        await update.effective_message.reply_text(
            f"Status klienta {name} jest już: {old_status}."
        )
        return

    if not new_status:
        options = [(s, f"set_status:{client.get('_row')}:{s}") for s in _VALID_STATUSES]
        await update.effective_message.reply_text(
            f"Wybierz nowy status dla {client.get('Imię i nazwisko', 'klienta')}:",
            reply_markup=build_choice_buttons(options),
        )
        return

    # Whitelist validation
    if new_status not in _VALID_STATUSES:
        matched = next((s for s in _VALID_STATUSES if s.lower() == new_status.lower()), None)
        if matched:
            new_status = matched
        else:
            await update.effective_message.reply_text(
                f"Nie znam statusu \"{new_status}\".\n"
                f"Dostępne: {', '.join(_VALID_STATUSES)}"
            )
            return

    save_pending_flow(telegram_id, "change_status", {
        "row": client.get("_row"),
        "field": "Status",
        "old_value": old_status,
        "new_value": new_status,
        "client_name": client.get("Imię i nazwisko", ""),
        "city": client.get("Miasto", ""),
    })

    await update.effective_message.reply_markdown_v2(
        f"Zmienić status klienta *{escape_markdown_v2(client.get('Imię i nazwisko', ''))}*?\n"
        + format_edit_comparison("Status", old_status, new_status),
        reply_markup=build_confirm_cancel_buttons("confirm"),
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
        if message_text:  # From text input: inform user. From button (empty ""): silent return.
            await update.effective_message.reply_text("Nie ma nic do potwierdzenia.")
        return

    flow_type = flow.get("flow_type", "")
    flow_data = flow.get("flow_data", {})

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
                city = flow_data["client_data"].get("Miasto", "")
                if remaining:
                    next_client = remaining[0]
                    new_remaining = remaining[1:]
                    save_pending(PendingFlow(
                        telegram_id=telegram_id,
                        flow_type=PendingFlowType.ADD_CLIENT,
                        flow_data=payload_to_flow_data(AddClientPayload(
                            client_data={"Imię i nazwisko": next_client},
                            _offer_remaining=new_remaining,
                        )),
                    ))
                    await update.effective_message.reply_text(
                        f"✅ {name} dodany. Podaj dane {next_client} — adres, telefon, produkt."
                    )
                    skip_delete = True
                else:
                    await update.effective_message.reply_text("✅ Zapisane.")
                    skip_delete = True  # r7_prompt flow created below
                    await send_next_action_prompt(update, telegram_id, name, city)
            else:
                await update.effective_message.reply_markdown_v2(format_error("google_down"))

        elif flow_type == "add_client_duplicate":
            duplicate_row = flow_data.get("duplicate_row")
            if duplicate_row:
                ok = await update_client(user_id, duplicate_row, flow_data["client_data"])
                if ok:
                    name = flow_data.get("client_name", "klient")
                    city = flow_data.get("city", "")
                    await update.effective_message.reply_text("✅ Dane zaktualizowane.")
                    skip_delete = True
                    await send_next_action_prompt(update, telegram_id, name, city)
                else:
                    await update.effective_message.reply_markdown_v2(format_error("google_down"))
            else:
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
                        reply_markup=build_mutation_buttons("confirm"),
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
                    reply_markup=build_mutation_buttons("confirm"),
                )
                skip_delete = True
            else:
                await update.effective_message.reply_text("\n".join(msg_parts))

        elif flow_type == "offer_add_client":
            client_name = flow_data.get("client_name", "")
            if client_name:
                save_pending(PendingFlow(
                    telegram_id=telegram_id,
                    flow_type=PendingFlowType.ADD_CLIENT,
                    flow_data=payload_to_flow_data(AddClientPayload(
                        client_data={"Imię i nazwisko": client_name},
                    )),
                ))
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
                save_pending(PendingFlow(
                    telegram_id=telegram_id,
                    flow_type=PendingFlowType.ADD_CLIENT,
                    flow_data=payload_to_flow_data(AddClientPayload(
                        client_data={"Imię i nazwisko": first},
                        _offer_remaining=new_remaining,
                    )),
                ))
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
                skip_delete = True
                await send_next_action_prompt(
                    update, telegram_id,
                    flow_data.get("client_name", "klient"),
                    flow_data.get("city", ""),
                )
            else:
                await update.effective_message.reply_markdown_v2(format_error("google_down"))

        elif flow_type == "add_note":
            today_str = date.today().strftime("%d.%m.%Y")
            old_notes = flow_data.get("old_notes", "")
            new_entry = f"[{today_str}]: {flow_data['note_text']}"
            final_notes = f"{old_notes}; {new_entry}" if old_notes else new_entry
            ok = await update_client(user_id, flow_data["row"], {
                "Notatki": final_notes,
                "Data ostatniego kontaktu": date.today().strftime("%Y-%m-%d"),
            })
            if ok:
                await update.effective_message.reply_text("✅ Notatka dodana.")
            else:
                await update.effective_message.reply_markdown_v2(format_error("google_down"))
            # Per spec (INTENCJE_MVP.md §4.3): clean note is a closed act — no R7

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
    """R1 one-click cancel: delete pending flow immediately, no confirmation loop."""
    telegram_id = update.effective_user.id
    flow = get_pending_flow(telegram_id)
    if flow:
        delete_pending_flow(telegram_id)
    await update.effective_message.reply_text("Anulowane.")


async def send_next_action_prompt(
    update: Update,
    telegram_id: int,
    client_name: str,
    city: str,
) -> None:
    """R7: send open-ended next-action prompt after a committed mutation.

    Saves an r7_prompt pending flow. The user's reply is handled in
    _route_pending_flow: temporal → add_meeting, otherwise → close silently.
    """
    name_city = f"{client_name} ({city})" if city else client_name
    save_pending_flow(telegram_id, "r7_prompt", {"client_name": client_name, "city": city})
    await update.effective_message.reply_text(
        f"Co dalej — {name_city}? Spotkanie, telefon, mail, odłożyć na później?",
        reply_markup=build_choice_buttons([("❌ Anuluj / nic", "cancel:r7")]),
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


async def handle_refresh_columns_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """CommandHandler adapter for /odswiez_kolumny."""
    if not await is_private_chat(update):
        return
    user = await _run_guards(update)
    if not user:
        return
    telegram_id = update.effective_user.id
    await handle_refresh_columns(
        update, context, user, {}, update.effective_message.text or ""
    )
    await increment_interaction(
        telegram_id, "refresh_columns", "none", 0, 0, 0.0
    )


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

    system_context = (
        "Jesteś asystentem handlowca OZE (odnawialne źródła energii) w Polsce. "
        "Pomagasz zarządzać klientami (CRM w Google Sheets) i spotkaniami (Google Calendar). "
        "Oferowane produkty: PV (fotowoltaika), Pompa ciepła, Magazyn energii, PV + Magazyn energii. "
        f"Statusy lejka sprzedaży: {', '.join(_VALID_STATUSES)}. "
        "Odpowiadaj BARDZO krótko — maksimum 2 zdania. "
        "Ton: konkretny, bez entuzjazmu, bez formalności. "
        "NIGDY nie używaj: 'Oczywiście', 'Z przyjemnością', 'Świetnie', 'Czekam na polecenia', "
        "'Czy mogę w czymś pomóc', 'Mam nadzieję', 'Nie ma problemu', 'Rozumiem Twoją frustrację'. "
        "NIGDY nie sugeruj sprawdzania zewnętrznych plików ani folderów — odpowiedz na podstawie wiedzy. "
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


# IntentType → handler dispatch table. Defined at the bottom of the module
# so every referenced handler function already exists at import time.
_HANDLERS = {
    IntentType.ADD_CLIENT:       handle_add_client,
    IntentType.SHOW_CLIENT:      handle_search_client,
    IntentType.ADD_NOTE:         handle_add_note,
    IntentType.CHANGE_STATUS:    handle_change_status,
    IntentType.ADD_MEETING:      handle_add_meeting,
    IntentType.SHOW_DAY_PLAN:    handle_show_day_plan,
    IntentType.GENERAL_QUESTION: handle_general,
    IntentType.POST_MVP_ROADMAP: handle_banner,
    IntentType.VISION_ONLY:      handle_banner,
    IntentType.UNPLANNED:        handle_banner,
    IntentType.MULTI_MEETING:    handle_banner,
}
