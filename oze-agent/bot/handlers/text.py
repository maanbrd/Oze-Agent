"""Text message handler — main intent router for OZE-Agent bot."""

import logging
import re
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

WARSAW = ZoneInfo("Europe/Warsaw")

from telegram import InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.utils.telegram_helpers import (
    build_mutation_buttons,
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
from shared.mutations import commit_add_meeting, commit_add_note, commit_change_status
from shared.pending import (
    AddClientDuplicatePayload,
    AddClientPayload,
    AddMeetingDisambiguationPayload,
    AddMeetingPayload,
    AddNotePayload,
    ChangeStatusPayload,
    DisambiguationPayload,
    PendingFlow,
    PendingFlowType,
    R7PromptPayload,
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
from shared.clients import lookup_client, suggest_fuzzy_client
from shared.matching import first_name_ok as _first_name_ok
from shared.search import detect_potential_duplicate

logger = logging.getLogger(__name__)

# Fields managed automatically — never show as "missing" to the user
SYSTEM_FIELDS = {
    "Data pierwszego kontaktu", "Data ostatniego kontaktu", "Status",
    "Zdjęcia", "Link do zdjęć", "ID wydarzenia Kalendarz", "Data następnego kroku",
}

# Slice 5.4: constants moved to shared.mutations.add_meeting so the pipeline
# can use them without importing from the handler layer. Aliased back to the
# underscored names for existing call-sites in this module.
from shared.mutations import (
    EVENT_TYPE_TO_NEXT_STEP_LABEL as _EVENT_TYPE_TO_NEXT_STEP_LABEL,
    STATUS_MEETING_AUTO_UPGRADE_FROM as _STATUS_MEETING_AUTO_UPGRADE_FROM,
    STATUS_MEETING_BOOKED as _STATUS_MEETING_BOOKED,
    STATUS_NEW_LEAD as _STATUS_NEW_LEAD,
    commit_add_client,
    commit_update_client_fields,
)
_EVENT_TYPE_DEFAULT_DURATION = {
    "in_person": 60,
    "phone_call": 15,
    "offer_email": 15,
    "doc_followup": 15,
}

# Slice 5.4.1b — first line of Calendar event description when event_type has
# a non-obvious action. in_person skipped: the meeting itself IS the action.
_EVENT_TYPE_DESCRIPTION_PREFIX = {
    "offer_email": "📧 Wyślij ofertę klientowi.",
    "phone_call": "📞 Zadzwoń do klienta.",
    "doc_followup": "📋 Follow-up dokumentowy.",
}


def _default_duration_for_event_type(event_type: Optional[str], user_default: int) -> int:
    if event_type in _EVENT_TYPE_DEFAULT_DURATION:
        return _EVENT_TYPE_DEFAULT_DURATION[event_type]
    return user_default


# Canonical 9-status pipeline per INTENCJE_MVP.md (frozen)
_VALID_STATUSES = [
    _STATUS_NEW_LEAD,
    _STATUS_MEETING_BOOKED,
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
# Event-type words the R7 prompt advertises ("Spotkanie, telefon, mail...").
# R7-only: we widen the meeting-intent check in the r7_prompt branch so a bare
# "telefon" reply routes into handle_add_meeting (which then asks for time via
# its own "Nie rozpoznałem daty lub godziny" path). NOT added to _TEMPORAL_MARKERS
# because the classifier demotion guard at handle_text uses that set and
# "telefon"/"mail" in a client-data message would then falsely stay as add_meeting.
_R7_EVENT_TYPE_MARKERS = {
    "telefon", "telefonicznie", "zadzwonić", "zadzwonic", "dzwonić", "dzwonic",
    "mail", "email", "e-mail", "wysłać", "wyslac",
    "oferta", "ofertę", "oferte",
}
# Slice 5.1d.3: disambiguation caps for ambiguous add_meeting. Above the cap
# we decline to build a giant button list and ask the user for more context
# instead — Telegram UX degrades past ~8-10 inline buttons, and phone queries
# always narrow to unique via lookup_client's phone path.
_AMBIGUOUS_CANDIDATE_CAP = 10
# HH:MM or "o <hour>" / "na <hour>" — require explicit time preposition
# Also matches "wpół" ("wpół do ósmej") and "kwadrans" ("za kwadrans dziesiąta")
_TIME_RE = re.compile(
    r'\d{1,2}:\d{2}'
    r'|\bo\s+\d{1,2}(?:\s|$)'
    r'|\bna\s+\d{1,2}(?:\s|$)'
    r'|\bwpół\b'
    r'|\bkwadrans\b'
)
_PHONE_VALUE_RE = re.compile(r"\b(?:tel|telefon|nr|numer)\b[^\n]*(?:\+?\d[\d\s-]{5,})")
_EMAIL_VALUE_RE = re.compile(r"\b(?:e-?mail|mail)\b[^\n]*\S+@\S+")
_LOOSE_PHONE_RE = re.compile(r"(?<!\d)(?:\+?48[\s-]?)?(?:\d[\s-]?){9}(?!\d)")

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
    legacy = {
        "intent": result.intent.value,
        "entities": entities,
        "confidence": result.confidence,
        "feature_key": result.feature_key,
        "reason": result.reason,
    }
    # Slice 5.4.3: hoist compound status_update from entities to top-level so
    # handle_add_meeting (which reads intent_data.get("status_update")) picks it
    # up without having to reach into entities. Only for ADD_MEETING — other
    # intents never carry status_update.
    if result.intent is IntentType.ADD_MEETING:
        status_update = entities.get("status_update")
        if status_update:
            legacy["status_update"] = status_update
    return legacy


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


def _has_temporal_or_time(text_lower: str) -> bool:
    return (
        any(w in text_lower for w in _TEMPORAL_MARKERS)
        or bool(_TIME_RE.search(text_lower))
    )


def _is_client_data_reply(text_lower: str) -> bool:
    if _PHONE_VALUE_RE.search(text_lower) or _EMAIL_VALUE_RE.search(text_lower):
        return True
    return text_lower.startswith((
        "adres", "ul.", "ulica", "email", "e-mail", "mail", "produkt", "moc",
        "miasto", "miejscowość", "miejscowosc", "notatka", "notatki",
        "źródło", "zrodlo", "data następnego kroku", "data nastepnego kroku",
    ))


def _is_client_scoped_action_reply(message_text: str) -> bool:
    """Detect obvious next-step actions while preserving client-data updates.

    This runs only inside an active add_client pending flow. It is deliberately
    conservative: "telefon 123" stays client data, but "zadzwonić w środę" or
    "spotkanie w piątek o 14" are routed with the pending client's context.
    """
    text_lower = message_text.lower().strip()
    if not text_lower or _is_client_data_reply(text_lower):
        return False

    action_markers = (
        "spotkanie", "umów", "umow", "zadzwoni", "zadzwoń", "zadzwon",
        "dzwonić", "dzwonic", "telefon", "rozmowa", "ofert", "wyślij",
        "wyslij", "przygotuj", "follow-up", "followup", "dokument",
    )
    if any(marker in text_lower for marker in action_markers):
        return True

    return _has_temporal_or_time(text_lower)


def _looks_like_intent_switch_reply(message_text: str) -> bool:
    text_lower = message_text.lower().strip()
    if not text_lower or _is_client_data_reply(text_lower):
        return False

    switch_prefixes = (
        "dodaj klienta", "dodaj nowego", "dopisz klienta",
        "dodaj notatkę", "dodaj notatke", "notatka dla",
        "dopisz notatkę", "dopisz notatke",
        "zmień status", "zmien status", "status ",
        "pokaż", "pokaz", "znajdź", "znajdz", "szukaj",
        "pokaż plan", "pokaz plan", "plan na", "co mam",
        "dodaj spotkanie", "umów", "umow", "spotkanie z",
        "zadzwoń", "zadzwo", "zadzwon", "wyślij ofert", "wyslij ofert",
        "przypomnij", "follow-up", "followup",
    )
    return any(text_lower.startswith(prefix) for prefix in switch_prefixes)


def _infer_meeting_event_type(
    message_text: str,
    default: Optional[str] = "in_person",
) -> Optional[str]:
    text_lower = message_text.lower()
    # Slice 5.4.2: doc_followup markers fold into phone_call — real user speech
    # for document reminders ("przypomnij o fakturze", "follow-up z Janem jutro")
    # is a call to remind, not a separate event type.
    if any(marker in text_lower for marker in (
        "zadzwoń", "zadzwo", "zadzwon", "zadzwonić", "zadzwonic",
        "oddzwoń", "oddzwo", "oddzwon", "telefon", "telefonicz",
        "rozmowa telefoniczna", "call",
        "przypomn", "follow-up", "followup",
    )):
        return "phone_call"
    if any(marker in text_lower for marker in ("ofert", "wycena", "wycen", "mail", "email")):
        return "offer_email"
    if any(marker in text_lower for marker in ("spotkanie", "wizyta", "jadę do", "jade do")):
        return "in_person"
    return default


def _normalize_parsed_event_type(event_type: Optional[str]) -> Optional[str]:
    """Slice 5.4.2 — drop doc_followup from generated inputs.

    Parser (extract_meeting_data) and _infer_meeting_event_type should not
    produce doc_followup after 5.4.2 (prompt + schema + marker folds), but
    LLM drift can still slip a legacy value through. This guard reroutes to
    phone_call on the way out of the parser. Legacy pending flows that
    stored event_type='doc_followup' bypass this guard because they read
    flow_data directly and need to keep rendering correctly.
    """
    if event_type == "doc_followup":
        return "phone_call"
    return event_type


def _resolve_meeting_event_type(message_text: str, *fallbacks: Optional[str]) -> str:
    inferred = _normalize_parsed_event_type(
        _infer_meeting_event_type(message_text, default=None)
    )
    if inferred:
        return inferred
    for fallback in fallbacks:
        fallback = _normalize_parsed_event_type(fallback)
        if fallback:
            return fallback
    return "in_person"


def _message_with_add_client_context(message_text: str, client_data: dict) -> str:
    return _message_with_r7_client_context(
        message_text,
        {
            "client_name": client_data.get("Imię i nazwisko", ""),
            "city": client_data.get("Miasto", client_data.get("Miejscowość", "")),
        },
    )


def _extract_inline_client_facts(message_text: str) -> dict:
    """Extract obvious client facts from a meeting/detail reply without LLM.

    Used only while we already have a pending client context. It preserves data
    like phone/product notes that can appear in the same message as a meeting.
    """
    facts: dict[str, str] = {}
    text = message_text.strip()
    text_lower = text.lower()

    phone_match = _LOOSE_PHONE_RE.search(text)
    if phone_match:
        digits = re.sub(r"\D", "", phone_match.group(0))
        if len(digits) == 11 and digits.startswith("48"):
            digits = digits[2:]
        if len(digits) == 9:
            facts["Telefon"] = digits

    email_match = re.search(r"\b[\w.+-]+@[\w.-]+\.\w+\b", text)
    if email_match:
        facts["Email"] = email_match.group(0)

    product_parts = []
    has_pv = bool(re.search(r"\bpv\b|fotowolta", text_lower))
    has_storage = "magazyn" in text_lower
    if has_pv:
        product_parts.append("PV")
    if has_storage:
        product_parts.append("Magazyn energii")
    if product_parts:
        facts["Produkt"] = " + ".join(product_parts)

    if re.search(r"zużycie|zuzycie|\bkw\b|\bkwh\b|zainteresowan|magazyn", text_lower):
        facts["Notatki"] = text

    address_prefix = re.match(r"\s*(?:adres|ul\.?|ulica)\s+(.+)", text, flags=re.IGNORECASE)
    if address_prefix:
        facts["Adres"] = address_prefix.group(1).strip()

    return facts


_FULL_CLIENT_DATA_FIELDS = {"Telefon", "Email", "Adres", "Miasto", "Miejscowość"}


def _looks_like_full_client_data(client_data: dict) -> bool:
    name = (client_data.get("Imię i nazwisko") or "").strip()
    if not name:
        return False
    return any((client_data.get(field) or "").strip() for field in _FULL_CLIENT_DATA_FIELDS)


def _location_hint_from_client_data(client_data: dict) -> str:
    city = client_data.get("Miasto") or client_data.get("Miejscowość") or ""
    return ", ".join(part for part in [client_data.get("Adres", ""), city] if part)


def _merge_client_context_data(base: dict, extra: dict) -> dict:
    merged = dict(base or {})
    for key, value in (extra or {}).items():
        if not value or key in SYSTEM_FIELDS:
            continue
        if key in {"Imię i nazwisko", "Miasto", "Miejscowość"} and merged.get(key):
            continue
        merged[key] = value
    return merged


def _client_data_summary(client_data: dict) -> str:
    labels = [
        ("Telefon", "Tel."),
        ("Email", "Email"),
        ("Adres", "Adres"),
        ("Produkt", "Produkt"),
        ("Notatki", "Notatki"),
    ]
    parts = [f"{label}: {client_data[key]}" for key, label in labels if client_data.get(key)]
    return "; ".join(parts)


def _calendar_description_for_meeting(flow_data: dict) -> str:
    lines = []
    if flow_data.get("description"):
        lines.append(str(flow_data["description"]).strip())

    client_data = flow_data.get("client_data") or {}
    field_labels = [
        ("Telefon", "Telefon"),
        ("Email", "Email"),
        ("Miasto", "Miejscowość"),
        ("Miejscowość", "Miejscowość"),
        ("Adres", "Adres"),
        ("Produkt", "Produkt"),
        ("Notatki", "Notatki"),
    ]
    details = [f"{label}: {client_data[key]}" for key, label in field_labels if client_data.get(key)]
    if details:
        if lines:
            lines.append("")
        lines.append("Dane klienta:")
        lines.extend(details)

    return "\n".join(lines).strip()


def _format_add_meeting_flow_card(flow_data: dict) -> str:
    start = datetime.fromisoformat(flow_data["start"])
    end = datetime.fromisoformat(flow_data["end"])
    duration = int((end - start).total_seconds() // 60)
    _days_pl = ["poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela"]
    date_display = start.strftime("%d.%m.%Y") + f" ({_days_pl[start.weekday()]})"
    details = {
        "Klient": flow_data.get("client_name", ""),
        "Data": date_display,
        "Godzina": start.strftime("%H:%M"),
        "Czas trwania": f"{duration} min",
        "Miejsce": flow_data.get("location", ""),
        "Opis": flow_data.get("description", ""),
    }
    client_summary = _client_data_summary(flow_data.get("client_data") or {})
    if client_summary:
        details["Dane klienta do zapisu"] = client_summary
    status_update = flow_data.get("status_update") or {}
    if status_update:
        details["Status"] = (
            f"{status_update.get('old_value', '')} → "
            f"{status_update.get('new_value', '')}"
        )
    return format_confirmation("add_meeting", details)


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

        if _is_client_scoped_action_reply(message_text):
            source_client_data = _merge_client_context_data(
                old_client_data,
                _extract_inline_client_facts(message_text),
            )
            action_text = _message_with_add_client_context(message_text, old_client_data)
            await handle_add_meeting(
                update,
                context,
                user,
                {
                    "source_client_data": source_client_data,
                    "entities": {
                        "event_type": _infer_meeting_event_type(message_text),
                    },
                },
                action_text,
            )
            return True

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
    elif flow_type == "add_meeting":
        if _looks_like_intent_switch_reply(message_text):
            telegram_id = update.effective_user.id
            delete_pending_flow(telegram_id)
            await update.effective_message.reply_text("⚠️ Anulowane.")
            return False

        flow_data = flow.get("flow_data", {})
        try:
            if not flow_data.get("client_name"):
                headers = await get_sheet_headers(user["id"])
                result = await extract_client_data(message_text, headers)
                extracted_client_data = {
                    k: v
                    for k, v in _filter_invalid_products(result.get("client_data", {})).items()
                    if v
                }
                if _looks_like_full_client_data(extracted_client_data):
                    client_data = _merge_client_context_data(
                        flow_data.get("client_data") or {},
                        extracted_client_data,
                    )
                    client_name = client_data["Imię i nazwisko"]
                    location_hint = _location_hint_from_client_data(client_data)
                    enriched = await _enrich_meeting(
                        user["id"],
                        client_name,
                        location_hint,
                        event_type=flow_data.get("event_type"),
                    )
                    description = flow_data.get("description") or enriched["description"]
                    status_update = flow_data.get("status_update")
                    if status_update is None:
                        status_update = _auto_status_update_from_enriched(
                            enriched, flow_data.get("event_type")
                        )
                    save_pending(PendingFlow(
                        telegram_id=update.effective_user.id,
                        flow_type=PendingFlowType.ADD_MEETING,
                        flow_data=payload_to_flow_data(AddMeetingPayload(
                            title=enriched["title"],
                            start=flow_data["start"],
                            end=flow_data["end"],
                            client_name=client_name,
                            location=enriched["location"],
                            description=description,
                            client_data=client_data,
                            event_type=flow_data.get("event_type"),
                            status_update=status_update,
                            client_row=enriched.get("client_row"),
                            current_status=enriched.get("current_status") or "",
                            ambiguous_client=enriched.get("ambiguous_client", False),
                        )),
                    ))
                    card = _format_add_meeting_flow_card({
                        **flow_data,
                        "title": enriched["title"],
                        "client_name": client_name,
                        "location": enriched["location"],
                        "description": description,
                        "client_data": client_data,
                        "status_update": status_update,
                    })
                    await update.effective_message.reply_markdown_v2(
                        card,
                        reply_markup=build_mutation_buttons("confirm"),
                    )
                    return True

            client_facts = _extract_inline_client_facts(message_text)
            client_data = flow_data.get("client_data") or {}
            if flow_data.get("client_name"):
                client_data = {
                    "Imię i nazwisko": flow_data.get("client_name", ""),
                    **client_data,
                }

            if client_facts:
                client_data = _merge_client_context_data(client_data, client_facts)
                description = flow_data.get("description", "")
            else:
                existing_description = (flow_data.get("description") or "").strip()
                description = (
                    f"{existing_description}\n{message_text}".strip()
                    if existing_description
                    else message_text
                )

            save_pending(PendingFlow(
                telegram_id=update.effective_user.id,
                flow_type=PendingFlowType.ADD_MEETING,
                flow_data=payload_to_flow_data(AddMeetingPayload(
                    title=flow_data["title"],
                    start=flow_data["start"],
                    end=flow_data["end"],
                    client_name=flow_data.get("client_name", ""),
                    location=flow_data.get("location", ""),
                    description=description,
                    client_data=client_data or None,
                    event_type=flow_data.get("event_type"),
                    status_update=flow_data.get("status_update"),
                    client_row=flow_data.get("client_row"),
                    current_status=flow_data.get("current_status") or "",
                    ambiguous_client=flow_data.get("ambiguous_client", False),
                )),
            ))
            card = _format_add_meeting_flow_card({
                **flow_data,
                "description": description,
                "client_data": client_data,
            })
            await update.effective_message.reply_markdown_v2(
                card,
                reply_markup=build_mutation_buttons("confirm"),
            )
        except Exception as e:
            logger.error("add_meeting augment failed: %s", e)
            await update.effective_message.reply_markdown_v2(format_error("timeout"))
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
        row = flow_data.get("row")
        if row is None:
            logger.error("add_note augment: pending flow_data without row: %s", flow_data)
            delete_pending_flow(telegram_id)
            await update.effective_message.reply_markdown_v2(format_error("timeout"))
            return True
        save_pending(PendingFlow(
            telegram_id=telegram_id,
            flow_type=PendingFlowType.ADD_NOTE,
            flow_data=payload_to_flow_data(AddNotePayload(
                row=row,
                note_text=new_note,
                client_name=flow_data.get("client_name", ""),
                city=flow_data.get("city", ""),
                old_notes=flow_data.get("old_notes", ""),
            )),
        ))

        display_note = new_note[:80] + ("..." if len(new_note) > 80 else "")
        name = flow_data.get("client_name", "")
        c_city = flow_data.get("city", "")
        city_part = f", {c_city}" if c_city else ""
        await update.effective_message.reply_text(
            f"📝 {name}{city_part}:\ndodaj notatkę \"{display_note}\"?",
            reply_markup=build_mutation_buttons("confirm"),
        )
        return True
    elif flow_type == "change_status":
        flow_data = flow.get("flow_data", {})
        client_name = flow_data.get("client_name", "")
        city = flow_data.get("city", "")
        text_has_action = (
            _has_temporal_or_time(text_lower)
            or any(
                marker in text_lower
                for marker in (
                    "spotkanie", "telefon", "zadzw", "rozmowa",
                    "mail", "email", "ofert", "follow", "dokument",
                )
            )
        )
        if not text_has_action:
            await update.effective_message.reply_text(
                "Dopisz następny krok, np. 'telefon jutro o 14' albo 'spotkanie w piątek o 10'."
            )
            return True

        meeting_text = _message_with_r7_client_context(
            message_text,
            {"client_name": client_name, "city": city},
        )
        await handle_add_meeting(
            update,
            context,
            user,
            {
                "entities": {
                    "event_type": _infer_meeting_event_type(message_text),
                },
                "status_update": {
                    "row": flow_data.get("row"),
                    "field": flow_data.get("field", "Status"),
                    "old_value": flow_data.get("old_value", ""),
                    "new_value": flow_data.get("new_value", ""),
                    "client_name": client_name,
                    "city": city,
                },
            },
            meeting_text,
        )
        return True
    elif flow_type == "r7_prompt":
        # R7 next-action response. The pending_flows table uses telegram_id as
        # PK, so any successful downstream save_pending(...) UPSERTs over the
        # R7 row. Strategy: only delete R7 explicitly on cancel or fully-unclear
        # replies. For temporal-but-incomplete replies (e.g. bare "Spotkanie"),
        # leave R7 alive so the next message can still recover client context
        # from flow_data — pending flow is the source of truth, not history.
        telegram_id = update.effective_user.id
        _cancel_single = {"nie", "anuluj", "stop", "nic", "later"}
        _cancel_phrases = {"nie wiem", "odłóż", "odłożyć"}
        text_words = set(text_lower.split())
        if (text_words & _cancel_single) or any(p in text_lower for p in _cancel_phrases):
            delete_pending_flow(telegram_id)
            return True
        # Slice 5.1d.2: accept bare event-type words ("telefon", "mail", "oferta")
        # as meeting intent. handle_add_meeting will ask for time via its own
        # path if one isn't in the message.
        has_meeting_intent = (
            any(w in text_lower for w in _TEMPORAL_MARKERS)
            or bool(_TIME_RE.search(text_lower))
            or any(w in text_lower for w in _R7_EVENT_TYPE_MARKERS)
        )
        if has_meeting_intent:
            r7_data = flow.get("flow_data", {})
            meeting_text = _message_with_r7_client_context(message_text, r7_data)
            entities = {"event_type": _infer_meeting_event_type(message_text)}
            intent_data_r7: dict = {"entities": entities}
            # Slice 5.1d.1: carry the row resolved by the preceding mutation
            # so handle_add_meeting can skip _enrich_meeting's lookup.
            if r7_data.get("client_row") is not None:
                intent_data_r7["r7_client_row"] = r7_data.get("client_row")
                intent_data_r7["r7_current_status"] = r7_data.get("current_status") or ""
                intent_data_r7["r7_client_name"] = r7_data.get("client_name") or ""
                intent_data_r7["r7_city"] = r7_data.get("city") or ""
            await handle_add_meeting(update, context, user, intent_data_r7, meeting_text)
            # If handle_add_meeting succeeded, it already wrote an add_meeting
            # pending flow over R7 (telegram_id PK upsert). If it failed (no
            # date/time), no new flow was saved → R7 stays alive so the user's
            # next reply can re-enter this branch with the same client context.
            return True
        # Slice 5.1d.2: no markers at all — tell the user instead of silently
        # dropping the flow so they know the reply wasn't understood.
        delete_pending_flow(telegram_id)
        await update.effective_message.reply_text(
            "Nie rozumiem. Podaj np. 'spotkanie jutro o 14', 'telefon', "
            "albo napisz 'nic' żeby zakończyć."
        )
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

    result = await lookup_client(user_id, client_name, city)

    if result.status == "not_found":
        city_part = f" ({city})" if city else ""
        await update.effective_message.reply_text(
            f"Nie znalazłem klienta: '{client_name}{city_part}'"
        )
        return

    if result.status == "multi":
        lines = [f"Mam {len(result.clients)} klientów:"]
        options = []
        for i, c in enumerate(result.clients[:10], start=1):
            c_name = c.get("Imię i nazwisko", "?")
            c_city = c.get("Miasto", "")
            c_row = c.get("_row", 0)
            label = f"{i}. {c_name}" + (f" — {c_city}" if c_city else "")
            lines.append(label)
            options.append((label, f"select_client:{c_row}"))
        lines.append("Którego?")
        save_pending(PendingFlow(
            telegram_id=telegram_id,
            flow_type=PendingFlowType.DISAMBIGUATION,
            flow_data=payload_to_flow_data(DisambiguationPayload(
                intent="add_note",
                note_text=note_text,
            )),
        ))
        await update.effective_message.reply_text(
            "\n".join(lines),
            reply_markup=build_choice_buttons(options),
        )
        return

    client = result.clients[0]

    row = client.get("_row")
    old_notes = client.get("Notatki", "")
    name = client.get("Imię i nazwisko", client_name)
    c_city = client.get("Miasto", city)

    if row is None:
        logger.error("handle_add_note: client without _row: %s", client)
        await update.effective_message.reply_markdown_v2(format_error("timeout"))
        return

    save_pending(PendingFlow(
        telegram_id=telegram_id,
        flow_type=PendingFlowType.ADD_NOTE,
        flow_data=payload_to_flow_data(AddNotePayload(
            row=row,
            note_text=note_text,
            client_name=name,
            city=c_city,
            old_notes=old_notes,
        )),
    ))

    display_note = note_text[:80] + ("..." if len(note_text) > 80 else "")
    city_part = f", {c_city}" if c_city else ""
    await update.effective_message.reply_text(
        f"📝 {name}{city_part}:\ndodaj notatkę \"{display_note}\"?",
        reply_markup=build_mutation_buttons("confirm"),
    )


def _build_add_client_duplicate_card(
    telegram_id: int,
    client_data: dict,
    duplicate: dict,
) -> Optional[tuple[PendingFlow, str, InlineKeyboardMarkup]]:
    """Build pending flow + card text + markup for ADD_CLIENT_DUPLICATE.

    Copies the merge/conflict logic used when a single duplicate row is
    identified — callers (single-match in handle_add_client, post-disambiguation
    in _handle_select_client) share one renderer. Returns None when the
    duplicate row lacks `_row` so the caller can reply with a timeout error.
    """
    dup_name = duplicate.get("Imię i nazwisko", "")
    dup_city = duplicate.get("Miasto", "")
    duplicate_row = duplicate.get("_row")
    if duplicate_row is None:
        logger.error("_build_add_client_duplicate_card: duplicate without _row: %s", duplicate)
        return None

    has_conflict = any(
        v and duplicate.get(k) and duplicate.get(k) != v
        for k, v in client_data.items()
        if k not in SYSTEM_FIELDS and k != "Imię i nazwisko"
    )

    if not has_conflict:
        new_data = {k: v for k, v in client_data.items() if v and k not in SYSTEM_FIELDS}
        flow = PendingFlow(
            telegram_id=telegram_id,
            flow_type=PendingFlowType.ADD_CLIENT_DUPLICATE,
            flow_data=payload_to_flow_data(AddClientDuplicatePayload(
                client_data=new_data,
                duplicate_row=duplicate_row,
                client_name=duplicate.get("Imię i nazwisko", ""),
                city=duplicate.get("Miasto", ""),
            )),
        )
        updated_fields = ", ".join(new_data.keys())
        city_part = f" ({dup_city})" if dup_city else ""
        text = f"Mam już {dup_name}{city_part}.\nZaktualizować o: {updated_fields}?"
        return flow, text, build_mutation_buttons("confirm")

    flow = PendingFlow(
        telegram_id=telegram_id,
        flow_type=PendingFlowType.ADD_CLIENT_DUPLICATE,
        flow_data=payload_to_flow_data(AddClientDuplicatePayload(
            client_data=client_data,
            duplicate_row=duplicate_row,
            client_name=duplicate.get("Imię i nazwisko", ""),
            city=duplicate.get("Miasto", ""),
        )),
    )
    dup_addr = duplicate.get("Adres", "")
    dup_prod = duplicate.get("Produkt", "")
    dup_info = ", ".join(p for p in [dup_addr, dup_city, dup_prod] if p)
    text = f"⚠️ Masz już {dup_name} ({dup_info}).\nDodać nowego czy dopisać do istniejącego?"
    return flow, text, build_duplicate_buttons("confirm")


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
        built = _build_add_client_duplicate_card(telegram_id, client_data, duplicate)
        if built is None:
            await update.effective_message.reply_markdown_v2(format_error("timeout"))
            return
        flow, text, markup = built
        save_pending(flow)
        await update.effective_message.reply_text(text, reply_markup=markup)
        return

    # No duplicate → new-client flow
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
    name = entities.get("name")
    phone = entities.get("phone")
    city = entities.get("city") or ""
    query = name or phone or city or message_text
    is_city_only_query = bool(city and not name and not phone)

    await send_typing(context, telegram_id)
    result = await lookup_client(user_id, query, city=city)

    if result.status == "not_found":
        if not result.is_phone_query and not is_city_only_query:
            suggestion = await suggest_fuzzy_client(user_id, query)
            if suggestion is not None:
                candidate = suggestion.candidate
                candidate_name = candidate.get("Imię i nazwisko", "")
                candidate_city = candidate.get("Miasto", "")
                suggestion_text = candidate_name + (f" z {candidate_city}" if candidate_city else "")
                save_pending_flow(telegram_id, "confirm_search", {"row": candidate.get("_row")})
                await update.effective_message.reply_text(
                    f"Nie mam \"{query}\". Chodziło o {suggestion_text}?",
                    reply_markup=build_choice_buttons([
                        ("✅ Tak, pokaż", "confirm:yes"),
                        ("❌ Nie", "cancel:search"),
                    ]),
                )
                return
        await update.effective_message.reply_text(f"Nie mam \"{query}\" w bazie.")
        return

    if result.status == "multi" and len(result.clients) >= 50:
        sheets_url = f"https://docs.google.com/spreadsheets/d/{user.get('google_sheets_id', '')}"
        await update.effective_message.reply_text(
            f"Znalazłem {len(result.clients)} klientów. Otwórz arkusz:\n{sheets_url}"
        )
        return

    if result.status == "unique":
        client = result.clients[0]
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

    lines = [f"Mam {len(result.clients)} klientów:"]
    options = []
    for i, c in enumerate(result.clients[:10], start=1):
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


def _parse_warsaw(date_str: str, time_str: str) -> datetime:
    """Parse date+time strings as Europe/Warsaw and return an aware datetime."""
    naive = datetime.fromisoformat(f"{date_str}T{time_str}:00")
    return naive.replace(tzinfo=WARSAW)


def _build_enriched_from_client(
    client: dict,
    client_name_fallback: str,
    location_hint: str,
    event_type: Optional[str] = None,
) -> dict:
    """Shared formatter — given a resolved Sheets row dict, build the enriched
    result used by handle_add_meeting for the confirmation card and payload."""
    full_name = client.get("Imię i nazwisko") or client_name_fallback
    client_row = client.get("_row")
    current_status = (client.get("Status") or "").strip()
    client_city = client.get("Miasto", client.get("Miejscowość", "")) or ""

    location = location_hint
    addr = client.get("Adres", "")
    if not location:
        location = ", ".join(p for p in [addr, client_city] if p)

    parts = []
    prefix = _EVENT_TYPE_DESCRIPTION_PREFIX.get(event_type)
    if prefix:
        parts.append(prefix)
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

    label = _EVENT_TYPE_TO_NEXT_STEP_LABEL.get(event_type, "Spotkanie")
    title = f"{label} — {full_name}" if full_name else label
    return {
        "title": title,
        "location": location,
        "description": description,
        "full_name": full_name,
        "client_found": True,
        "client_row": client_row,
        "current_status": current_status,
        "client_city": client_city,
        "ambiguous_client": False,
        # Slice 5.1d.3: unique path — no disambiguation needed.
        "ambiguous_candidates": [],
    }


async def _enrich_meeting(
    user_id: str,
    client_name: str,
    location_hint: str,
    known_client_row: Optional[int] = None,
    event_type: Optional[str] = None,
) -> dict:
    """Look up client in Sheets and return enriched title/location/description.

    Returns dict with 'client_found' (bool) and 'ambiguous_client' (bool).
    multi-match sets ambiguous_client=True without silent-picking any row —
    handle_confirm then creates the Calendar event but skips Sheets sync.
    location_hint is NOT passed as city to lookup_client: it represents the
    meeting venue ("telefonicznie", an address), not the client's city.

    When known_client_row is supplied (Slice 5.1d.1 — R7 context carried from
    a prior mutation confirm), we skip lookup_client entirely and fetch only
    that specific row from get_all_clients. Guarantees we hit the exact row
    the user already identified in change_status/add_note/add_client_duplicate.
    """
    if known_client_row is not None:
        all_clients = await get_all_clients(user_id)
        match = next(
            (c for c in all_clients if c.get("_row") == known_client_row),
            None,
        )
        if match is not None:
            return _build_enriched_from_client(match, client_name, location_hint, event_type=event_type)
        # Row vanished (deleted between confirms) — fall through to name lookup.

    full_name = client_name
    location = location_hint
    description = ""
    client_found = False
    client_row: Optional[int] = None
    current_status = ""
    client_city = ""
    ambiguous_client = False
    ambiguous_candidates: list[dict] = []

    if client_name:
        result = await lookup_client(user_id, client_name)
        if result.status == "unique":
            return _build_enriched_from_client(result.clients[0], client_name, location_hint, event_type=event_type)
        elif result.status == "multi":
            ambiguous_client = True
            # Slice 5.1d.3: carry the candidate set so handle_add_meeting can
            # show a disambiguation prompt before any confirm card. Empty
            # list on not_found keeps the caller logic uniform.
            ambiguous_candidates = [
                {
                    "row": c.get("_row"),
                    "full_name": c.get("Imię i nazwisko", ""),
                    "city": c.get("Miasto", c.get("Miejscowość", "")) or "",
                    "current_status": (c.get("Status") or "").strip(),
                }
                for c in result.clients
                if c.get("_row") is not None
            ]

    label = _EVENT_TYPE_TO_NEXT_STEP_LABEL.get(event_type, "Spotkanie")
    title = f"{label} — {full_name}" if full_name else label
    return {
        "title": title,
        "location": location,
        "description": description,
        "full_name": full_name,
        "client_found": client_found,
        "client_row": client_row,
        "current_status": current_status,
        "client_city": client_city,
        "ambiguous_client": ambiguous_client,
        "ambiguous_candidates": ambiguous_candidates,
    }


def _normalize_compound_status_update(
    status_update: Optional[dict],
    enriched: dict,
) -> Optional[dict]:
    """Slice 5.4.3 — fill compound status_update gaps from enriched client dict.

    Classifier emits only {"field": "Status", "new_value": "..."}. The pipeline
    and confirm card need the full shape (row, old_value, client_name, city).
    This helper fills those gaps post-enrichment. Three drop cases:
      1) input is None → nothing to do.
      2) new_value missing → malformed classifier output, drop rather than
         carry a half-baked status update.
      3) no resolvable row (no input.row, no enriched.client_row) → not_found
         scenario; the pipeline cannot write status without a row, and we
         don't want the confirm card to promise a change we can't deliver.

    Callers in the ambiguous-client branch must NOT invoke this — raw
    status_update has to survive intact in the disambiguation payload and be
    normalized only after the user picks a candidate (which provides a row).
    """
    if not status_update:
        return None
    if not status_update.get("new_value"):
        return None
    resolvable_row = status_update.get("row") or enriched.get("client_row")
    if not resolvable_row:
        return None
    filled = dict(status_update)
    filled.setdefault("field", "Status")
    if not filled.get("row"):
        filled["row"] = enriched["client_row"]
    if not filled.get("old_value"):
        filled["old_value"] = enriched.get("current_status") or ""
    if not filled.get("client_name"):
        filled["client_name"] = enriched.get("full_name") or ""
    if not filled.get("city"):
        filled["city"] = enriched.get("client_city") or ""
    return filled


def _auto_status_update_from_enriched(
    enriched: dict,
    event_type: Optional[str],
) -> Optional[dict]:
    """Pre-compute status_update for in_person meetings with existing Nowy-lead clients.

    Lets the card show 'Status: Nowy lead → Spotkanie umówione' before Zapisać
    (per TEST_PLAN_CURRENT AM-7 + agent_behavior_spec_v5 §Auto-przejście).
    """
    if event_type != "in_person" or not enriched.get("client_found"):
        return None
    if enriched.get("ambiguous_client"):
        return None
    current = (enriched.get("current_status") or "").strip()
    if current not in _STATUS_MEETING_AUTO_UPGRADE_FROM:
        return None
    return {
        "row": enriched.get("client_row"),
        "field": "Status",
        "old_value": current,
        "new_value": _STATUS_MEETING_BOOKED,
        "client_name": enriched.get("full_name", ""),
        "city": enriched.get("client_city", ""),
    }


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
        entities = intent_data.get("entities") or {}
        event_type = _resolve_meeting_event_type(
            message_text,
            m.get("event_type"),
            entities.get("event_type"),
        )
        try:
            start_dt = _parse_warsaw(m["date"], m["time"])
            explicit_duration = m.get("duration_minutes")
            duration = (
                explicit_duration if explicit_duration is not None
                else _default_duration_for_event_type(event_type, default_duration)
            )
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

        # Slice 5.1d.1: when arriving from R7 follow-up, the prior mutation
        # already resolved the client — carry that row through instead of
        # re-running lookup_client (which would flip to ambiguous for same-name
        # pairs in different cities).
        r7_client_row = intent_data.get("r7_client_row")
        r7_client_name = intent_data.get("r7_client_name") or ""
        enriched_client_name = m.get("client_name") or r7_client_name
        enriched = await _enrich_meeting(
            user_id,
            enriched_client_name,
            m.get("location", ""),
            known_client_row=r7_client_row,
            event_type=event_type,
        )
        source_client_data = intent_data.get("source_client_data") or None
        raw_status_update = intent_data.get("status_update") or None
        # Slice 5.4.3: 3-branch status_update resolution.
        #   1) Ambiguous client → preserve raw compound in disambiguation payload;
        #      normalize only after user picks a candidate (row becomes known).
        #   2) Unique / not_found with compound → normalize now; drop if no row.
        #   3) No compound → existing 5.4 auto-upgrade path (in_person + Nowy lead).
        ambiguous_candidates_preview = enriched.get("ambiguous_candidates") or []
        if enriched.get("ambiguous_client") and ambiguous_candidates_preview:
            status_update = raw_status_update
        elif raw_status_update:
            status_update = _normalize_compound_status_update(raw_status_update, enriched)
        else:
            status_update = _auto_status_update_from_enriched(enriched, event_type)

        conflicts = await check_conflicts(user_id, start_dt, end_dt)
        conflict_warning = ""
        if conflicts:
            conflict_warning = f"\n\n⚠️ Uwaga: masz już spotkanie o tej porze: *{escape_markdown_v2(conflicts[0].get('title', ''))}*"

        # Slice 5.1d.3: ambiguous client → resolve BEFORE showing the confirm
        # card. Previous behaviour (Gate A) let the user click Zapisać and
        # then skipped Sheets sync; we now surface the candidates upfront.
        # Gate A fallback in handle_confirm stays as a safety net for legacy
        # pendings (flow_data with ambiguous_client=True arriving directly).
        ambiguous_candidates = enriched.get("ambiguous_candidates") or []
        if enriched.get("ambiguous_client") and ambiguous_candidates:
            if len(ambiguous_candidates) > _AMBIGUOUS_CANDIDATE_CAP:
                # No pending saved — user must supply more context and retry.
                await update.effective_message.reply_text(
                    f"Znalazłem {len(ambiguous_candidates)} klientów o tym nazwisku. "
                    "Dopisz więcej danych klienta, np. miasto albo telefon."
                )
                return

            save_pending(PendingFlow(
                telegram_id=telegram_id,
                flow_type=PendingFlowType.ADD_MEETING_DISAMBIGUATION,
                flow_data=payload_to_flow_data(AddMeetingDisambiguationPayload(
                    title=enriched["title"],
                    start=start_dt.isoformat(),
                    end=end_dt.isoformat(),
                    client_name=enriched_client_name,
                    location=enriched["location"],
                    description=enriched["description"],
                    event_type=event_type,
                    status_update=status_update,
                    source_client_data=source_client_data,
                    candidates=ambiguous_candidates,
                )),
            ))
            options = [
                (
                    f"{c['full_name']} — {c['city']}" if c.get("city") else c["full_name"],
                    f"select_client:{c['row']}",
                )
                for c in ambiguous_candidates
            ]
            options.append(("Żaden z nich", "select_client:none"))
            await update.effective_message.reply_text(
                f"Mam {len(ambiguous_candidates)} klientów o tym nazwisku. Którego użyć do spotkania?",
                reply_markup=build_choice_buttons(options),
            )
            return

        save_pending(PendingFlow(
            telegram_id=telegram_id,
            flow_type=PendingFlowType.ADD_MEETING,
            flow_data=payload_to_flow_data(AddMeetingPayload(
                title=enriched["title"],
                start=start_dt.isoformat(),
                end=end_dt.isoformat(),
                client_name=enriched["full_name"],
                location=enriched["location"],
                description=enriched["description"],
                client_data=source_client_data,
                event_type=event_type,
                status_update=status_update,
                client_row=enriched.get("client_row"),
                current_status=enriched.get("current_status") or "",
                ambiguous_client=enriched.get("ambiguous_client", False),
            )),
        ))

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
        client_summary = _client_data_summary(source_client_data or {})
        if client_summary:
            details["Dane klienta do zapisu"] = client_summary
        if status_update:
            details["Status"] = (
                f"{status_update.get('old_value', '')} → "
                f"{status_update.get('new_value', '')}"
            )
        msg = format_confirmation("add_meeting", details) + conflict_warning
        await update.effective_message.reply_markdown_v2(msg, reply_markup=build_mutation_buttons("confirm"))

    else:
        # Multiple meetings — build all, check conflicts, confirm as a batch
        flow_meetings = []
        conflict_warnings = []
        router_event_type = (intent_data.get("entities") or {}).get("event_type")
        # Prefer parser-provided per-item event_type. The raw-message fallback
        # applies to the whole batch and can flatten mixed messages, so it is
        # intentionally only a fallback.
        batch_fallback_event_type = _resolve_meeting_event_type(message_text, router_event_type)

        for m in meetings:
            if not m.get("date") or not m.get("time"):
                continue
            event_type = m.get("event_type") or batch_fallback_event_type
            try:
                start_dt = _parse_warsaw(m["date"], m["time"])
                explicit_duration = m.get("duration_minutes")
                duration = (
                    explicit_duration if explicit_duration is not None
                    else _default_duration_for_event_type(event_type, default_duration)
                )
                end_dt = start_dt + timedelta(minutes=duration)
            except Exception:
                continue

            enriched = await _enrich_meeting(
                user_id,
                m.get("client_name", ""),
                m.get("location", ""),
                event_type=event_type,
            )

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
                "event_type": event_type,
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
    name_query = (entities.get("name") or "").strip()
    city = (entities.get("city") or "").strip()
    search_query = name_query or message_text
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

    client = None
    if name_query:
        result = await lookup_client(user_id, name_query, city)

        if result.status == "not_found":
            await update.effective_message.reply_text(
                f"Nie znalazłem klienta: '{name_query}'"
            )
            return

        if result.status == "multi":
            lines = [f"Mam {len(result.clients)} klientów:"]
            options = []
            for i, c in enumerate(result.clients[:10], start=1):
                c_name = c.get("Imię i nazwisko", "?")
                c_city = c.get("Miasto", "")
                c_row = c.get("_row", 0)
                label = f"{i}. {c_name}" + (f" — {c_city}" if c_city else "")
                lines.append(label)
                options.append((label, f"select_client:{c_row}"))
            lines.append("Którego?")
            save_pending(PendingFlow(
                telegram_id=telegram_id,
                flow_type=PendingFlowType.DISAMBIGUATION,
                flow_data=payload_to_flow_data(DisambiguationPayload(
                    intent="change_status",
                    new_status=new_status,
                )),
            ))
            await update.effective_message.reply_text(
                "\n".join(lines),
                reply_markup=build_choice_buttons(options),
            )
            return

        client = result.clients[0]
    else:
        # Legacy R1-safe fallback when the LLM did not extract an entity name.
        # We still rely on search_clients for multi disambiguation / single
        # confirmation card (no lookup_client here — its strict filter would
        # reject whole-message queries that routinely matched fuzzily before).
        results = await search_clients(user_id, search_query)
        if not results:
            await update.effective_message.reply_text(
                f"Nie znalazłem klienta: '{search_query}'"
            )
            return

        if len(results) > 1:
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
            save_pending(PendingFlow(
                telegram_id=telegram_id,
                flow_type=PendingFlowType.DISAMBIGUATION,
                flow_data=payload_to_flow_data(DisambiguationPayload(
                    intent="change_status",
                    new_status=new_status,
                )),
            ))
            await update.effective_message.reply_text(
                "\n".join(lines),
                reply_markup=build_choice_buttons(options),
            )
            return

        client = results[0]

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

    row = client.get("_row")
    if row is None:
        logger.error("handle_change_status: client without _row: %s", client)
        await update.effective_message.reply_markdown_v2(format_error("timeout"))
        return
    save_pending(PendingFlow(
        telegram_id=telegram_id,
        flow_type=PendingFlowType.CHANGE_STATUS,
        flow_data=payload_to_flow_data(ChangeStatusPayload(
            row=row,
            new_value=new_status,
            client_name=client.get("Imię i nazwisko", ""),
            old_value=old_status,
            city=client.get("Miasto", ""),
        )),
    ))

    await update.effective_message.reply_markdown_v2(
        f"Zmienić status klienta *{escape_markdown_v2(client.get('Imię i nazwisko', ''))}*?\n"
        + format_edit_comparison("Status", old_status, new_status),
        reply_markup=build_mutation_buttons("confirm"),
    )


# ── Slice 5.7: per-branch confirm helpers (Opcja B) ─────────────────────────
#
# Each _confirm_* helper owns a single pipeline-backed flow_type. Returns
# skip_delete: bool so the caller (handle_confirm) can keep the
# delete_pending_flow cleanup in exactly one place. Helpers are pure
# block-moves — copy and flow-control semantics match pre-5.7 behavior 1:1.
# edit_client / delete_client / add_meetings (plural) stay inline in
# handle_confirm: those paths are POST-MVP / vision-only and out of this
# slice's scope.


async def _confirm_add_client(update, telegram_id, user_id, flow_data) -> bool:
    remaining = flow_data.get("_offer_remaining", [])
    result = await commit_add_client(user_id, flow_data["client_data"])
    if not result.success:
        await update.effective_message.reply_markdown_v2(
            format_error(result.error_message or "google_down")
        )
        return False

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
        return True

    await update.effective_message.reply_text("✅ Zapisane.")
    await send_next_action_prompt(
        update, telegram_id, name, city,
        client_row=result.row,
        current_status=flow_data["client_data"].get("Status") or "",
    )
    return True  # r7_prompt flow created inside send_next_action_prompt


async def _confirm_add_client_duplicate(update, telegram_id, user_id, flow_data) -> bool:
    duplicate_row = flow_data.get("duplicate_row")
    if duplicate_row:
        update_result = await commit_update_client_fields(
            user_id, duplicate_row, flow_data["client_data"]
        )
        if not update_result.success:
            await update.effective_message.reply_markdown_v2(
                format_error(update_result.error_message or "google_down")
            )
            return False
        name = flow_data.get("client_name", "klient")
        city = flow_data.get("city", "")
        await update.effective_message.reply_text("✅ Dane zaktualizowane.")
        await send_next_action_prompt(
            update, telegram_id, name, city,
            client_row=duplicate_row,
            current_status=flow_data["client_data"].get("Status") or "",
        )
        return True

    # Fallback: no duplicate_row → fresh add (mirrors pre-5.5 behavior:
    # only "✅ Zapisane.", no R7, no batch).
    add_result = await commit_add_client(user_id, flow_data["client_data"])
    if add_result.success:
        await update.effective_message.reply_text("✅ Zapisane.")
    else:
        await update.effective_message.reply_markdown_v2(
            format_error(add_result.error_message or "google_down")
        )
    return False


async def _confirm_add_note(update, user_id, flow_data) -> bool:
    result = await commit_add_note(
        user_id,
        flow_data["row"],
        flow_data["note_text"],
        flow_data.get("old_notes", ""),
        date.today(),
    )
    if result.success:
        await update.effective_message.reply_text("✅ Notatka dodana.")
    else:
        await update.effective_message.reply_markdown_v2(format_error("google_down"))
    # Per spec (INTENCJE_MVP.md §4.3): clean note is a closed act — no R7.
    return False


async def _confirm_change_status(update, telegram_id, user_id, flow_data) -> bool:
    result = await commit_change_status(
        user_id,
        flow_data["row"],
        flow_data["new_value"],
        date.today(),
    )
    if not result.success:
        await update.effective_message.reply_markdown_v2(format_error("google_down"))
        return False

    await update.effective_message.reply_text(
        f"✅ Status zmieniony na: {flow_data['new_value']}"
    )
    # R7 fires for every plain change_status (INTENCJE_MVP §4.4). A future
    # compound change_status + add_meeting flow can suppress it by setting
    # flow_data["compound_add_meeting"]; that path does not reach this branch
    # today, but the guard documents the contract.
    if not flow_data.get("compound_add_meeting"):
        await send_next_action_prompt(
            update, telegram_id,
            flow_data.get("client_name", "klient"),
            flow_data.get("city", ""),
            client_row=flow_data.get("row"),
            current_status=flow_data.get("new_value") or "",
        )
    return True


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
            skip_delete = await _confirm_add_client(update, telegram_id, user_id, flow_data)

        elif flow_type == "add_client_duplicate":
            skip_delete = await _confirm_add_client_duplicate(update, telegram_id, user_id, flow_data)

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
            client_data = flow_data.get("client_data") or {}
            client_name = flow_data.get("client_name") or client_data.get("Imię i nazwisko", "")
            event_type = flow_data.get("event_type") or "in_person"
            correct_label = _EVENT_TYPE_TO_NEXT_STEP_LABEL.get(event_type, "Spotkanie")
            title = flow_data.get("title") or correct_label
            # Legacy override: pre-5.4.1 pendings stored title="Spotkanie — X" even
            # for phone_call/offer_email. Rewrite bare generic labels and the
            # "{generic_label} — {client_name}" pattern so Calendar title matches
            # event_type. Custom titles (not matching either shape) pass through.
            # Slice 5.4.1c: tolerate ASCII dash "-" too — test fixtures and some
            # pre-5.4.1 flows stored "Spotkanie - Jan" without em-dash.
            if client_name:
                stripped = title.strip()
                generic_labels = set(_EVENT_TYPE_TO_NEXT_STEP_LABEL.values())
                is_overridable = stripped in generic_labels or any(
                    stripped in (f"{lbl} — {client_name}", f"{lbl} - {client_name}")
                    for lbl in generic_labels
                )
                if is_overridable:
                    title = f"{correct_label} — {client_name}"
            status_update = flow_data.get("status_update") or None
            ambiguous_client = flow_data.get("ambiguous_client", False)
            enriched_client_row = flow_data.get("client_row")
            current_status_hint = (flow_data.get("current_status") or "").strip()
            event_description = _calendar_description_for_meeting(flow_data)

            result = await commit_add_meeting(
                user_id,
                title=title,
                start=start,
                end=end,
                event_type=event_type,
                location=flow_data.get("location") or "",
                description=event_description or "",
                client_row=enriched_client_row,
                today=date.today(),
                client_current_status=current_status_hint,
                status_update=status_update,
            )

            if not result.success:
                # Calendar failure — pipeline made no Sheets writes.
                await update.effective_message.reply_markdown_v2(
                    format_error(result.error_message or "calendar_down")
                )
            elif not result.sheets_attempted and ambiguous_client:
                # Gate A fallback — stays in handler because the pipeline
                # doesn't know about the disambiguation UX.
                await update.effective_message.reply_text(
                    f"✅ Spotkanie dodane do kalendarza. Klient '{client_name}' ma "
                    f"≥2 wpisy w arkuszu — nie synchronizuję, uściślij przy add_note/change_status."
                )
            elif not result.sheets_attempted and client_name:
                # Not-found: pre-seed ADD_CLIENT draft from the meeting context.
                # Covers new flow_data (ambiguous_client=False, client_row=None)
                # AND legacy pendings without the new fields — no second
                # search_clients lookup (silent-pick regression guard).
                draft_client_data = dict(client_data)
                draft_client_data.setdefault("Imię i nazwisko", client_name)
                if event_type == "in_person":
                    draft_client_data.setdefault("Status", _STATUS_MEETING_BOOKED)
                save_pending(PendingFlow(
                    telegram_id=telegram_id,
                    flow_type=PendingFlowType.ADD_CLIENT,
                    flow_data=payload_to_flow_data(AddClientPayload(
                        client_data=draft_client_data,
                    )),
                ))
                sheet_columns = user.get("sheet_columns") or await get_sheet_headers(user_id)
                missing = [
                    col for col in sheet_columns
                    if col and not draft_client_data.get(col) and col not in SYSTEM_FIELDS
                ]
                card = format_add_client_card(draft_client_data, missing)
                await update.effective_message.reply_text(
                    f"✅ Spotkanie dodane.\n{card}",
                    reply_markup=build_mutation_buttons("confirm"),
                )
                skip_delete = True
            elif result.sheets_attempted and not result.sheets_synced:
                # Partial: Calendar event created, Sheets sync failed.
                await update.effective_message.reply_text(
                    "✅ Spotkanie dodane do kalendarza. Nie udało się zaktualizować arkusza."
                )
            elif result.status_updated:
                await update.effective_message.reply_text(
                    f"✅ Spotkanie dodane do kalendarza. Status klienta: {result.status_new_value}."
                )
            else:
                await update.effective_message.reply_text("✅ Spotkanie dodane do kalendarza.")

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
                    event_type=fm.get("event_type"),
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
            skip_delete = await _confirm_change_status(update, telegram_id, user_id, flow_data)

        elif flow_type == "add_note":
            skip_delete = await _confirm_add_note(update, user_id, flow_data)

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
    client_row: Optional[int] = None,
    current_status: Optional[str] = None,
) -> None:
    """R7: send open-ended next-action prompt after a committed mutation.

    Saves an r7_prompt pending flow. The user's reply is handled in
    _route_pending_flow: temporal → add_meeting, otherwise → close silently.

    client_row / current_status carry the row resolved by the preceding mutation
    so the R7 follow-up can sync directly without re-entering lookup_client
    (Slice 5.1d.1).
    """
    name_city = f"{client_name} ({city})" if city else client_name
    save_pending(PendingFlow(
        telegram_id=telegram_id,
        flow_type=PendingFlowType.R7_PROMPT,
        flow_data=payload_to_flow_data(R7PromptPayload(
            client_name=client_name,
            city=city,
            client_row=client_row,
            current_status=current_status,
        )),
    ))
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
