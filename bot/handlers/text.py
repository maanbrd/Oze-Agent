"""Text message handler — main intent router for OZE-Agent bot."""

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.telegram_helpers import (
    build_confirm_buttons,
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
    message_text = update.message.text.strip()

    await send_typing(context, telegram_id)

    # Check for active pending flow first
    pending_flow = get_pending_flow(telegram_id)
    if pending_flow:
        await _route_pending_flow(update, context, user, pending_flow, message_text)
        return

    # Save message and get history
    save_conversation_message(telegram_id, "user", message_text)
    history = get_conversation_history(telegram_id, limit=10)

    # Classify intent
    intent_data = await classify_intent(message_text, history)
    intent = intent_data.get("intent", "general_question")

    # Route by intent
    handlers = {
        "add_client": handle_add_client,
        "search_client": handle_search_client,
        "edit_client": handle_edit_client,
        "delete_client": handle_delete_client,
        "add_meeting": handle_add_meeting,
        "view_meetings": handle_view_meetings,
        "reschedule_meeting": handle_reschedule_meeting,
        "cancel_meeting": handle_cancel_meeting,
        "show_pipeline": handle_show_pipeline,
        "change_status": handle_change_status,
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
) -> None:
    """Route a reply message based on the active pending flow."""
    flow_type = flow.get("flow_type", "")
    text_lower = message_text.lower().strip()

    is_yes = text_lower in {
        "tak", "tak.", "ok", "okej", "dobrze", "zgadza się", "yes",
        "zapisz tak jak jest", "zapisz", "tak jak jest", "ok zapisz", "dobra", "spoko",
    }
    is_no = text_lower in {
        "nie", "nie.", "anuluj", "stop", "no", "cancel", "nie chcę", "zrezygnuj",
    }

    if is_yes:
        await handle_confirm(update, context, user, {}, message_text)
    elif is_no:
        await handle_cancel_flow(update, context, user, {}, message_text)
    else:
        # User is providing more data for the current flow
        await update.message.reply_text(
            "Odpowiedz *tak* aby potwierdzić lub *nie* aby anulować.",
            parse_mode="MarkdownV2",
        )


# ── Sub-handlers ──────────────────────────────────────────────────────────────


async def handle_add_client(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict,
    intent_data: dict,
    message_text: str,
) -> None:
    """Extract client data, check for duplicates, ask for confirmation."""
    telegram_id = update.effective_user.id
    user_id = user["id"]

    await send_typing(context, telegram_id)

    headers = await get_sheet_headers(user_id)
    result = await extract_client_data(message_text, headers)
    client_data = result.get("client_data", {})
    missing = result.get("missing_columns", [])

    if not client_data:
        await update.message.reply_text(
            "Nie udało mi się wyciągnąć danych klienta. Opisz go ponownie."
        )
        return

    # Duplicate check
    all_clients = await get_all_clients(user_id)
    name = client_data.get("Imię i nazwisko", "")
    city = client_data.get("Miasto", client_data.get("Miejscowość", ""))
    duplicate = detect_potential_duplicate(name, city, all_clients) if name and city else None

    if duplicate:
        save_pending_flow(telegram_id, "add_client_duplicate", {
            "client_data": client_data,
            "duplicate_row": duplicate.get("_row"),
        })
        card = format_client_card(duplicate)
        await update.message.reply_markdown_v2(
            f"⚠️ Znalazłem podobnego klienta:\n\n{card}\n\n"
            f"Czy chcesz dodać nowego klienta pomimo podobieństwa?",
            reply_markup=build_confirm_buttons("duplicate"),
        )
        return

    # Show summary and ask for confirmation
    save_pending_flow(telegram_id, "add_client", {"client_data": client_data})

    sheet_columns = user.get("sheet_columns") or headers
    parts = [client_data[col] for col in sheet_columns if client_data.get(col)]
    summary = ", ".join(parts)
    missing = [col for col in sheet_columns if not client_data.get(col)]
    missing_text = f"\nBrakuje: {', '.join(missing)}." if missing else ""
    msg = escape_markdown_v2(f"Zapisuję klienta: {summary}.{missing_text}\nZapisać?")
    await update.message.reply_markdown_v2(msg, reply_markup=build_confirm_buttons("confirm"))


async def handle_search_client(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict,
    intent_data: dict,
    message_text: str,
) -> None:
    """Search for clients and show results."""
    user_id = user["id"]
    query = intent_data.get("entities", {}).get("name") or message_text

    await send_typing(context, update.effective_user.id)
    results = await search_clients(user_id, query)

    if not results:
        await update.message.reply_text(f"Nie znalazłem klientów pasujących do: '{query}'")
        return

    if len(results) == 1:
        card = format_client_card(results[0])
        await update.message.reply_markdown_v2(card)
        return

    if len(results) >= 50:
        sheets_url = f"https://docs.google.com/spreadsheets/d/{user.get('google_sheets_id', '')}"
        await update.message.reply_text(
            f"Znalazłem {len(results)} klientów. Otwórz arkusz, aby przejrzeć wyniki:\n{sheets_url}"
        )
        return

    # 2–49 results: show numbered list
    lines = [f"Znalazłem {len(results)} klientów. Wybierz:"]
    options = []
    for i, c in enumerate(results[:10], start=1):
        name = c.get("Imię i nazwisko", "?")
        city = c.get("Miasto", c.get("Miejscowość", ""))
        row = c.get("_row", 0)
        label = f"{i}. {name}" + (f" ({city})" if city else "")
        lines.append(label)
        options.append((label, f"select_client:{row}"))

    await update.message.reply_text(
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

    results = await search_clients(user_id, query)
    if not results:
        await update.message.reply_text(f"Nie znalazłem klienta: '{query}'")
        return

    client = results[0]
    headers = await get_sheet_headers(user_id)
    extracted = await extract_client_data(message_text, headers)
    updates = extracted.get("client_data", {})

    if not updates:
        await update.message.reply_text("Nie rozpoznałem co chcesz zmienić. Opisz dokładniej.")
        return

    save_pending_flow(telegram_id, "edit_client", {
        "row": client.get("_row"),
        "updates": updates,
        "old_values": {k: client.get(k, "") for k in updates},
    })

    lines = ["✏️ *Proponowane zmiany:*\n"]
    for field, new_val in updates.items():
        old_val = client.get(field, "")
        lines.append(format_edit_comparison(field, old_val, new_val))

    msg = "\n".join(lines)
    await update.message.reply_markdown_v2(
        msg, reply_markup=build_confirm_buttons("confirm")
    )


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
        await update.message.reply_text(f"Nie znalazłem klienta: '{query}'")
        return

    client = results[0]
    save_pending_flow(telegram_id, "delete_client", {"row": client.get("_row")})

    card = format_client_card(client)
    await update.message.reply_markdown_v2(
        f"🗑️ Usunąć tego klienta?\n\n{card}",
        reply_markup=build_confirm_buttons("confirm"),
    )


async def handle_add_meeting(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict,
    intent_data: dict,
    message_text: str,
) -> None:
    """Extract meeting data, check conflicts, ask for confirmation."""
    telegram_id = update.effective_user.id
    user_id = user["id"]

    today_str = date.today().isoformat()
    meeting = await extract_meeting_data(message_text, today_str)

    if not meeting.get("date") or not meeting.get("time"):
        await update.message.reply_text(
            "Nie rozpoznałem daty lub godziny spotkania. Podaj np. 'jutro o 14:00 z Kowalskim'."
        )
        return

    # Build datetime objects
    try:
        start_dt = datetime.fromisoformat(f"{meeting['date']}T{meeting['time']}:00").replace(tzinfo=timezone.utc)
        duration = meeting.get("duration_minutes", user.get("default_meeting_duration", 60))
        end_dt = start_dt + timedelta(minutes=duration)
    except Exception:
        await update.message.reply_text("Nie rozpoznałem daty lub godziny. Spróbuj ponownie.")
        return

    conflicts = await check_conflicts(user_id, start_dt, end_dt)
    conflict_warning = ""
    if conflicts:
        conflict_warning = f"\n\n⚠️ Uwaga: masz już spotkanie o tej porze: *{escape_markdown_v2(conflicts[0].get('title', ''))}*"

    save_pending_flow(telegram_id, "add_meeting", {
        "title": meeting.get("client_name", "Spotkanie"),
        "start": start_dt.isoformat(),
        "end": end_dt.isoformat(),
        "location": meeting.get("location", ""),
        "client_name": meeting.get("client_name", ""),
    })

    details = {
        "Klient": meeting.get("client_name", ""),
        "Data": meeting["date"],
        "Godzina": meeting["time"],
        "Czas trwania": f"{duration} min",
        "Miejsce": meeting.get("location", ""),
    }
    msg = format_confirmation("add_meeting", details) + conflict_warning
    await update.message.reply_markdown_v2(msg, reply_markup=build_confirm_buttons("confirm"))


async def handle_view_meetings(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict,
    intent_data: dict,
    message_text: str,
) -> None:
    """Show meetings for today, tomorrow, or this week."""
    user_id = user["id"]
    entities = intent_data.get("entities", {})
    day_hint = entities.get("day", "").lower()

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
    await update.message.reply_markdown_v2(schedule)


async def handle_reschedule_meeting(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict,
    intent_data: dict,
    message_text: str,
) -> None:
    """Placeholder — tell user to specify which meeting to reschedule."""
    await update.message.reply_text(
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
    await update.message.reply_text(
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

    await update.message.reply_markdown_v2(msg)


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
        await update.message.reply_text(f"Nie znalazłem klienta: '{query}'")
        return

    client = results[0]
    old_status = client.get("Status", "")

    if not new_status:
        pipeline_statuses = user.get("pipeline_statuses", [])
        if pipeline_statuses:
            options = [(s, f"set_status:{client.get('_row')}:{s}") for s in pipeline_statuses]
            await update.message.reply_text(
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

    await update.message.reply_markdown_v2(
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
        await update.message.reply_text("Nie ma nic do potwierdzenia.")
        return

    flow_type = flow.get("flow_type", "")
    flow_data = flow.get("flow_data", {})

    try:
        if flow_type == "add_client":
            row = await add_client(user_id, flow_data["client_data"])
            if row:
                name = flow_data["client_data"].get("Imię i nazwisko", "klient")
                await update.message.reply_text(f"✅ Klient *{name}* dodany do arkusza \\(wiersz {row}\\)\\.", parse_mode="MarkdownV2")
            else:
                await update.message.reply_markdown_v2(format_error("google_down"))

        elif flow_type == "add_client_duplicate":
            row = await add_client(user_id, flow_data["client_data"])
            if row:
                name = flow_data["client_data"].get("Imię i nazwisko", "klient")
                await update.message.reply_text(f"✅ Klient *{name}* dodany \\(wiersz {row}\\)\\.", parse_mode="MarkdownV2")
            else:
                await update.message.reply_markdown_v2(format_error("google_down"))

        elif flow_type == "edit_client":
            ok = await update_client(user_id, flow_data["row"], flow_data["updates"])
            if ok:
                await update.message.reply_text("✅ Dane klienta zaktualizowane.")
            else:
                await update.message.reply_markdown_v2(format_error("google_down"))

        elif flow_type == "delete_client":
            from shared.google_sheets import delete_client
            ok = await delete_client(user_id, flow_data["row"])
            if ok:
                await update.message.reply_text("✅ Klient usunięty z arkusza.")
            else:
                await update.message.reply_markdown_v2(format_error("google_down"))

        elif flow_type == "add_meeting":
            from datetime import datetime
            start = datetime.fromisoformat(flow_data["start"])
            end = datetime.fromisoformat(flow_data["end"])
            event = await create_event(
                user_id,
                title=flow_data.get("title", "Spotkanie"),
                start=start,
                end=end,
                location=flow_data.get("location"),
            )
            if event:
                client_name = flow_data.get("client_name", "")
                in_sheets = bool(client_name and await search_clients(user_id, client_name))
                if not in_sheets and client_name:
                    save_pending_flow(telegram_id, "offer_add_client", {"client_name": client_name})
                    await update.message.reply_text(
                        f"✅ Spotkanie dodane. Nie mam {client_name} w bazie. Dodać?",
                        reply_markup=build_confirm_buttons("confirm"),
                    )
                    return  # new flow saved — don't fall through to delete
                await update.message.reply_text("✅ Spotkanie dodane do kalendarza.")
            else:
                await update.message.reply_markdown_v2(format_error("calendar_down"))

        elif flow_type == "offer_add_client":
            client_name = flow_data.get("client_name", "")
            await update.message.reply_text(
                f"Podaj dane {client_name} — adres, telefon, produkt."
            )

        elif flow_type == "change_status":
            ok = await update_client(user_id, flow_data["row"], {flow_data["field"]: flow_data["new_value"]})
            if ok:
                await update.message.reply_text(f"✅ Status zmieniony na: {flow_data['new_value']}")
            else:
                await update.message.reply_markdown_v2(format_error("google_down"))

        else:
            await update.message.reply_text("✅ Gotowe.")

    except Exception as e:
        logger.error("handle_confirm(flow_type=%s): %s", flow_type, e)
        await update.message.reply_markdown_v2(format_error("timeout"))
    finally:
        delete_pending_flow(telegram_id)


async def handle_cancel_flow(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict,
    intent_data: dict,
    message_text: str,
) -> None:
    """Cancel and delete the current pending flow."""
    telegram_id = update.effective_user.id
    flow = get_pending_flow(telegram_id)
    if flow:
        delete_pending_flow(telegram_id)
        await update.message.reply_text("❌ Anulowano.")
    else:
        await update.message.reply_text("Nie ma nic do anulowania.")


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
        "Jesteś asystentem handlowca OZE w Polsce. Zarządzasz klientami, spotkaniami i pipeline'm. "
        "Masz pełny dostęp do Google Calendar, Google Sheets i Google Drive użytkownika. "
        "Nigdy nie mów że nie masz dostępu do tych systemów. "
        f"Statusy pipeline: {pipeline_statuses}. "
        "Odpowiadaj BARDZO krótko i konkretnie — maksimum 2 zdania. "
        "Bez pytań zwrotnych. Bez propozycji kolejnych kroków. Tylko fakty."
    )

    result = await generate_bot_response(system_context, message_text, history)
    response_text = result.get("text", "Nie rozumiem. Spróbuj ponownie.")

    save_conversation_message(telegram_id, "assistant", response_text)

    await update.message.reply_text(response_text)

    await increment_interaction(
        telegram_id,
        "general_question",
        result.get("model", ""),
        result.get("tokens_in", 0),
        result.get("tokens_out", 0),
        result.get("cost_usd", 0.0),
    )
