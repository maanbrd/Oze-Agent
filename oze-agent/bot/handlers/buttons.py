"""Inline button callback handler for OZE-Agent."""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.handlers.text import (
    handle_cancel_flow,
    handle_confirm,
    _run_guards,
)
from bot.utils.telegram_helpers import (
    build_choice_buttons,
    build_mutation_buttons,
    is_private_chat,
)
from shared.database import (
    delete_pending_flow,
    get_pending_flow,
    increment_daily_interaction_count,
)
from shared.pending import (
    AddClientPayload,
    AddNotePayload,
    ChangeStatusPayload,
    PendingFlow,
    PendingFlowType,
    R7PromptPayload,
    payload_to_flow_data,
    save as save_pending,
)
from shared.formatting import escape_markdown_v2, format_client_card, format_edit_comparison
from shared.google_sheets import get_all_clients, update_client

logger = logging.getLogger(__name__)


async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route inline button presses by callback_data format 'action:value'."""
    query = update.callback_query
    await query.answer()  # Remove loading indicator

    if not await is_private_chat(update):
        return

    user = await _run_guards(update)
    if not user:
        return

    telegram_id = update.effective_user.id
    data = query.data or ""

    if ":" not in data:
        logger.warning("handle_button: unexpected callback_data=%s", data)
        return

    action, _, value = data.partition(":")

    if action == "save":
        # R1: commit the pending flow
        await handle_confirm(update, context, user, {}, "")

    elif action == "append":
        # R1: keep pending flow open, prompt user for more data
        flow = get_pending_flow(telegram_id)
        if flow:
            await query.message.reply_text("Co chcesz dopisać?")
        else:
            await query.edit_message_text("Brak aktywnego wpisu.")

    elif action == "cancel":
        # R1: one-click cancel — delete pending flow immediately
        flow = get_pending_flow(telegram_id)
        if flow:
            delete_pending_flow(telegram_id)
        await query.edit_message_text("Anulowane.")

    elif action == "merge":
        # R4: update existing client with new data from duplicate flow
        await _handle_duplicate_merge(query, telegram_id, user["id"])

    elif action == "new":
        # R4: create new client record despite detected duplicate
        flow = get_pending_flow(telegram_id)
        if flow and flow.get("flow_type") == "add_client_duplicate":
            save_pending(PendingFlow(
                telegram_id=telegram_id,
                flow_type=PendingFlowType.ADD_CLIENT,
                flow_data=payload_to_flow_data(AddClientPayload(
                    client_data=flow["flow_data"]["client_data"],
                )),
            ))
        await handle_confirm(update, context, user, {}, "")

    elif action == "confirm":
        # Legacy fallback — kept for backward compat with cached messages
        if value == "yes":
            await handle_confirm(update, context, user, {}, "")
        else:
            await handle_cancel_flow(update, context, user, {}, "")

    elif action == "borrow":
        if value == "yes":
            from datetime import date, timedelta
            tomorrow = date.today() + timedelta(days=1)
            increment_daily_interaction_count(telegram_id, tomorrow)
            await query.edit_message_text("✅ Pożyczono 1 interakcję z jutra.")
        else:
            await query.edit_message_text("❌ Brak dodatkowych interakcji na dziś.")

    elif action == "select_client":
        await _handle_select_client(query, context, user, value)

    elif action == "edit":
        await _handle_edit_choice(query, telegram_id, user["id"], value)

    elif action == "voice_confirm":
        if value == "yes":
            flow = get_pending_flow(telegram_id)
            if flow and flow.get("flow_type") == "voice_transcription":
                transcription = flow["flow_data"]["transcription"]
                delete_pending_flow(telegram_id)
                # Simulate text message and re-route
                update.callback_query.message.text = transcription
                from bot.handlers.text import handle_text
                await handle_text(update, context)
        else:
            delete_pending_flow(telegram_id)
            await query.edit_message_text("❌ Nagranie anulowane. Spróbuj ponownie.")

    elif action == "set_status":
        # value format: "{row}:{status}"
        parts = value.split(":", 1)
        if len(parts) == 2:
            row, new_status = int(parts[0]), parts[1]
            ok = await update_client(user["id"], row, {"Status": new_status})
            if ok:
                await query.edit_message_text(f"✅ Status zmieniony na: {new_status}")
            else:
                await query.edit_message_text("❌ Nie udało się zmienić statusu.")

    elif action == "phone":
        await _handle_phone_choice(query, telegram_id, user["id"], value)

    else:
        logger.warning("handle_button: unhandled action=%s value=%s", action, value)


async def _handle_select_client(query, context, user: dict, row_str: str) -> None:
    """Show full client card, or resume pending disambiguation flow (change_status / add_note)."""
    try:
        row = int(row_str)
    except ValueError:
        await query.edit_message_text("❌ Nieprawidłowy wybór.")
        return

    clients = await get_all_clients(user["id"])
    client = next((c for c in clients if c.get("_row") == row), None)
    if not client:
        await query.edit_message_text("Nie znaleziono klienta.")
        return

    telegram_id = query.from_user.id
    flow = get_pending_flow(telegram_id)

    if flow and flow.get("flow_type") == "disambiguation":
        intent = flow["flow_data"].get("intent")
        delete_pending_flow(telegram_id)

        if intent == "change_status":
            new_status = flow["flow_data"].get("new_status", "")
            old_status = client.get("Status", "")
            if not new_status:
                pipeline_statuses = user.get("pipeline_statuses", [])
                if pipeline_statuses:
                    options = [(s, f"set_status:{client.get('_row')}:{s}") for s in pipeline_statuses]
                    await query.edit_message_text(
                        f"Wybierz nowy status dla {client.get('Imię i nazwisko', 'klienta')}:",
                        reply_markup=build_choice_buttons(options),
                    )
                else:
                    await query.edit_message_text("Podaj nowy status dla klienta.")
                return
            row = client.get("_row")
            if row is None:
                logger.error("buttons change_status: client without _row: %s", client)
                await query.edit_message_text("❌ Wystąpił błąd. Spróbuj ponownie.")
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
            await query.edit_message_text(
                f"Zmienić status klienta *{escape_markdown_v2(client.get('Imię i nazwisko', ''))}*?\n"
                + format_edit_comparison("Status", old_status, new_status),
                parse_mode="MarkdownV2",
                reply_markup=build_mutation_buttons("confirm"),
            )
            return

        elif intent == "add_note":
            note_text = flow["flow_data"].get("note_text", "")
            old_notes = client.get("Notatki", "")
            name = client.get("Imię i nazwisko", "")
            c_city = client.get("Miasto", "")
            row = client.get("_row")
            if row is None:
                logger.error("buttons add_note: client without _row: %s", client)
                await query.edit_message_text("❌ Wystąpił błąd. Spróbuj ponownie.")
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
            await query.edit_message_text(
                f"📝 {name}{city_part}:\ndodaj notatkę \"{display_note}\"?",
                reply_markup=build_mutation_buttons("confirm"),
            )
            return

    card = format_client_card(client)
    await query.edit_message_text(card, parse_mode="MarkdownV2")


async def _handle_phone_choice(query, telegram_id: int, user_id: str, value: str) -> None:
    """Handle keep-or-replace choice for phone/email field edits."""
    flow = get_pending_flow(telegram_id)
    if not flow or flow.get("flow_type") != "edit_client_phone_choice":
        await query.edit_message_text("Brak aktywnej edycji.")
        return

    flow_data = flow["flow_data"]
    row = flow_data["row"]
    field = flow_data["field"]
    old_val = flow_data["old_value"]
    new_val = flow_data["new_value"]
    other = flow_data.get("other_updates", {})

    if value == "keep_both":
        updates = {field: f"{old_val} / {new_val}", **other}
        label = "Oba numery zachowane"
    else:  # replace
        updates = {field: new_val, **other}
        label = "Numer zastąpiony"

    ok = await update_client(user_id, row, updates)
    delete_pending_flow(telegram_id)

    if ok:
        await query.edit_message_text(f"✅ {label}.")
    else:
        await query.edit_message_text("❌ Nie udało się zaktualizować. Sprawdź połączenie z Google.")


async def _handle_duplicate_merge(query, telegram_id: int, user_id: str) -> None:
    """R4: update existing client row with new data from the duplicate detection flow."""
    flow = get_pending_flow(telegram_id)
    if not flow or flow.get("flow_type") != "add_client_duplicate":
        await query.edit_message_text("Brak aktywnego duplikatu.")
        return

    flow_data = flow["flow_data"]
    duplicate_row = flow_data.get("duplicate_row")
    new_data = {k: v for k, v in flow_data.get("client_data", {}).items() if v}

    if not duplicate_row:
        await query.edit_message_text("Brak wiersza do aktualizacji.")
        return

    delete_pending_flow(telegram_id)
    ok = await update_client(user_id, duplicate_row, new_data)
    if ok:
        client_name = flow_data.get("client_name", "")
        city = flow_data.get("city", "")
        name_city = f"{client_name} ({city})" if city else (client_name or "klient")
        save_pending(PendingFlow(
            telegram_id=telegram_id,
            flow_type=PendingFlowType.R7_PROMPT,
            flow_data=payload_to_flow_data(R7PromptPayload(
                client_name=client_name,
                city=city,
                client_row=duplicate_row,
                current_status=new_data.get("Status") or "",
            )),
        ))
        await query.edit_message_text("✅ Dane zaktualizowane.")
        await query.message.reply_text(
            f"Co dalej — {name_city}? Spotkanie, telefon, mail, odłożyć na później?",
            reply_markup=build_choice_buttons([("❌ Anuluj / nic", "cancel:r7")]),
        )
    else:
        await query.edit_message_text("❌ Nie udało się zaktualizować. Sprawdź połączenie z Google.")


async def _handle_edit_choice(query, telegram_id: int, user_id: str, value: str) -> None:
    """Handle edit mode choices: replace or keep_both."""
    flow = get_pending_flow(telegram_id)
    if not flow or flow.get("flow_type") != "edit_client":
        await query.edit_message_text("Brak aktywnej edycji.")
        return

    flow_data = flow["flow_data"]
    row = flow_data.get("row")
    updates = flow_data.get("updates", {})
    old_values = flow_data.get("old_values", {})

    if value == "keep_both":
        # Append new value to old value with semicolon
        merged = {
            k: f"{old_values.get(k, '')}; {v}" if old_values.get(k) else v
            for k, v in updates.items()
        }
        ok = await update_client(user_id, row, merged)
    else:
        ok = await update_client(user_id, row, updates)

    delete_pending_flow(telegram_id)

    if ok:
        await query.edit_message_text("✅ Dane zaktualizowane.")
    else:
        await query.edit_message_text("❌ Nie udało się zaktualizować. Sprawdź połączenie z Google.")
