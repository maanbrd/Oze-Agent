"""Inline button callback handler for OZE-Agent."""

import logging
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from bot.handlers.text import (
    _EVENT_TYPE_TO_NEXT_STEP_LABEL,
    _auto_status_update_from_enriched,
    _build_enriched_from_client,
    _client_data_summary,
    _client_updates_for_empty_fields,
    _normalize_compound_status_update,
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
    AddMeetingPayload,
    AddNotePayload,
    ChangeStatusPayload,
    PendingFlow,
    PendingFlowType,
    R7PromptPayload,
    payload_to_flow_data,
    save as save_pending,
)
from shared.formatting import (
    escape_markdown_v2,
    format_client_card,
    format_confirmation,
    format_edit_comparison,
)
from shared.google_calendar import check_conflicts
from shared.google_sheets import get_all_clients, update_client

logger = logging.getLogger(__name__)

_DAYS_PL = ["poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela"]


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
        flow = get_pending_flow(telegram_id)
        is_voice_flow = bool(
            flow and flow.get("flow_type") == "voice_transcription"
        )

        if value == "yes":
            if is_voice_flow:
                transcription = flow["flow_data"]["transcription"]
                delete_pending_flow(telegram_id)
                # Feed transcription into text router via text_override —
                # Message.text is read-only in PTB ≥21, can't assign to it.
                from bot.handlers.text import handle_text
                await handle_text(update, context, text_override=transcription)

        elif value in ("cancel", "no"):
            # `:no` is a back-compat alias for `:cancel`.
            if is_voice_flow:
                delete_pending_flow(telegram_id)
                await query.edit_message_text("❌ Anulowane.")

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
    """Show full client card, or resume pending disambiguation flow.

    Slice 5.1d.3 added the `add_meeting_disambiguation` branch plus the
    `"none"` sentinel ("Żaden z nich") — both flow through here because
    the underlying UX (list of candidate buttons) is the same shape as
    add_note / change_status disambiguation.
    """
    telegram_id = query.from_user.id
    flow = get_pending_flow(telegram_id)

    if row_str == "none":
        if flow and flow.get("flow_type") == "add_meeting_disambiguation":
            await _resume_add_meeting_skip_client(query, telegram_id, flow["flow_data"])
        else:
            await query.edit_message_text("❌ Nieprawidłowy wybór.")
        return

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

    if flow and flow.get("flow_type") == "add_meeting_disambiguation":
        await _resume_add_meeting_disambiguation(
            query, telegram_id, client, flow["flow_data"], row
        )
        return

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


async def _send_add_meeting_confirmation_card(
    query,
    enriched: dict,
    start_iso: str,
    end_iso: str,
    source_client_data: dict | None,
    status_update: dict | None,
) -> None:
    """Slice 5.1d.3: render the same add_meeting confirm card handle_add_meeting
    produces, so the disambiguation-resume and skip-client paths stay visually
    identical to the unique path. Kept local to buttons.py to avoid a wider
    refactor of text.py's inline card builder in this slice.
    """
    start_dt = datetime.fromisoformat(start_iso)
    end_dt = datetime.fromisoformat(end_iso)
    duration = int((end_dt - start_dt).total_seconds() / 60)

    conflicts = await check_conflicts(query.from_user.id, start_dt, end_dt)
    conflict_warning = ""
    if conflicts:
        conflict_warning = (
            "\n\n⚠️ Uwaga: masz już spotkanie o tej porze: "
            f"*{escape_markdown_v2(conflicts[0].get('title', ''))}*"
        )

    date_display = start_dt.strftime("%d.%m.%Y") + f" ({_DAYS_PL[start_dt.weekday()]})"

    details = {
        "Klient": enriched.get("full_name", ""),
        "Data": date_display,
        "Godzina": start_dt.strftime("%H:%M"),
        "Czas trwania": f"{duration} min",
        "Miejsce": enriched.get("location", ""),
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
    await query.message.reply_markdown_v2(
        msg, reply_markup=build_mutation_buttons("confirm")
    )


def _resolve_status_update_on_disambiguation(
    enriched: dict,
    event_type: str | None,
    flow_status_update: dict | None,
    selected_row: int,
) -> dict | None:
    """Slice 5.1d.3 + 5.4.3: resolve status_update after the user picks a
    candidate during add_meeting disambiguation.

    - flow_status_update is None → recompute auto-upgrade from the chosen
      client (same rule as the unique path in handle_add_meeting).
    - flow_status_update present → delegate to _normalize_compound_status_update
      so row / old_value / client_name / city get filled from the chosen
      candidate's enriched dict. Normalizer also drops malformed compound
      (missing new_value) or unresolvable row, keeping the confirm card
      coherent with what pipeline can write. Row-mismatch between compound
      and selected_row is guarded separately upstream.
    """
    if flow_status_update is None:
        return _auto_status_update_from_enriched(enriched, event_type)
    return _normalize_compound_status_update(flow_status_update, enriched)


async def _resume_add_meeting_disambiguation(
    query,
    telegram_id: int,
    client: dict,
    flow_data: dict,
    selected_row: int,
) -> None:
    """Resume the add_meeting flow after the user picked a candidate.

    Writes an AddMeetingPayload (upsert over the disambiguation pending via
    telegram_id PK) and shows the standard confirm card. Rejects clicks for
    rows outside the pending candidate set — old buttons, tampered callbacks,
    or a stale pending must not let us sync a meeting to the wrong client.
    """
    valid_rows = {c.get("row") for c in flow_data.get("candidates", [])}
    if selected_row not in valid_rows:
        logger.warning(
            "add_meeting_disambiguation: selected row %s not in pending candidates %s",
            selected_row, sorted(r for r in valid_rows if r is not None),
        )
        await query.edit_message_text("❌ Nieprawidłowy wybór. Spróbuj ponownie.")
        delete_pending_flow(telegram_id)
        return

    # Defense in depth: if a compound status_update already nailed a row
    # (change_status confirm upstream), disambiguation should not have fired.
    # Treat a mismatch as an inconsistent state rather than overwriting.
    compound_row = (flow_data.get("status_update") or {}).get("row")
    if compound_row and compound_row != selected_row:
        logger.warning(
            "add_meeting_disambiguation: selected row %s != compound status_update.row %s",
            selected_row, compound_row,
        )
        await query.edit_message_text("❌ Nieprawidłowy wybór. Spróbuj ponownie.")
        delete_pending_flow(telegram_id)
        return

    enriched = _build_enriched_from_client(
        client,
        flow_data.get("client_name", ""),
        flow_data.get("location", ""),
        event_type=flow_data.get("event_type"),
    )
    status_update = _resolve_status_update_on_disambiguation(
        enriched,
        flow_data.get("event_type"),
        flow_data.get("status_update"),
        selected_row,
    )

    source_client_data = flow_data.get("source_client_data") or None
    client_updates = _client_updates_for_empty_fields(source_client_data or {}, client)
    save_pending(PendingFlow(
        telegram_id=telegram_id,
        flow_type=PendingFlowType.ADD_MEETING,
        flow_data=payload_to_flow_data(AddMeetingPayload(
            title=enriched["title"],
            start=flow_data["start"],
            end=flow_data["end"],
            client_name=enriched["full_name"],
            location=enriched["location"],
            description=enriched["description"],
            client_data=source_client_data,
            client_updates=client_updates,
            event_type=flow_data.get("event_type"),
            status_update=status_update,
            client_row=enriched.get("client_row"),
            current_status=enriched.get("current_status") or "",
            ambiguous_client=False,
        )),
    ))
    await _send_add_meeting_confirmation_card(
        query,
        enriched,
        flow_data["start"],
        flow_data["end"],
        source_client_data,
        status_update,
    )


async def _resume_add_meeting_skip_client(
    query,
    telegram_id: int,
    flow_data: dict,
) -> None:
    """Resume the add_meeting flow when the user clicks "Żaden z nich".

    Writes an AddMeetingPayload with client_row=None and preserved
    source_client_data (may be None). Confirm will hit the not_found path —
    Calendar event created + ADD_CLIENT draft pre-seeded from client_name
    (plus any source_client_data the user already provided).
    """
    client_name = flow_data.get("client_name", "")
    event_type = flow_data.get("event_type")
    label = _EVENT_TYPE_TO_NEXT_STEP_LABEL.get(event_type, "Spotkanie")
    enriched_no_client = {
        "title": flow_data.get("title") or (f"{label} — {client_name}" if client_name else label),
        "location": flow_data.get("location", ""),
        "description": "",
        "full_name": client_name,
        "client_found": False,
        "client_row": None,
        "current_status": "",
        "client_city": "",
        "ambiguous_client": False,
        "ambiguous_candidates": [],
    }

    source_client_data = flow_data.get("source_client_data") or None
    save_pending(PendingFlow(
        telegram_id=telegram_id,
        flow_type=PendingFlowType.ADD_MEETING,
        flow_data=payload_to_flow_data(AddMeetingPayload(
            title=enriched_no_client["title"],
            start=flow_data["start"],
            end=flow_data["end"],
            client_name=client_name,
            location=enriched_no_client["location"],
            description="",
            client_data=source_client_data,
            event_type=flow_data.get("event_type"),
            status_update=None,
            client_row=None,
            current_status="",
            ambiguous_client=False,
        )),
    ))
    await _send_add_meeting_confirmation_card(
        query,
        enriched_no_client,
        flow_data["start"],
        flow_data["end"],
        source_client_data,
        None,
    )
