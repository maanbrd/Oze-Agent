from unittest.mock import ANY, AsyncMock, MagicMock, patch
from datetime import datetime, timedelta, timezone

import pytest

from shared.pending import PendingFlowType


def _update(callback_data: str = "set_status:7:Podpisane", telegram_id: int = 123):
    update = MagicMock()
    update.effective_user.id = telegram_id
    update.effective_chat.type = "private"
    update.callback_query.data = callback_data
    update.callback_query.from_user.id = telegram_id
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.callback_query.message.date = datetime.now(tz=timezone.utc)
    return update


@pytest.mark.asyncio
async def test_set_status_callback_without_pending_flow_is_rejected():
    from bot.handlers.buttons import handle_button

    update = _update()
    with patch("bot.handlers.buttons._run_guards", new=AsyncMock(return_value={"id": "user-1"})), \
         patch("bot.handlers.buttons.get_pending_flow", return_value=None), \
         patch("bot.handlers.buttons.update_client", new=AsyncMock()) as update_client:
        await handle_button(update, MagicMock())

    update_client.assert_not_awaited()
    update.callback_query.edit_message_text.assert_awaited_once()
    assert "Nieaktualny" in update.callback_query.edit_message_text.await_args.args[0]


@pytest.mark.asyncio
async def test_stale_save_callback_does_not_confirm_newer_pending_flow():
    from bot.handlers.buttons import handle_button

    update = _update("save:confirm")
    update.callback_query.message.date = datetime.now(tz=timezone.utc) - timedelta(minutes=10)
    flow = {
        "flow_type": "add_client",
        "flow_data": {},
        "updated_at": datetime.now(tz=timezone.utc).isoformat(),
    }

    with patch("bot.handlers.buttons._run_guards", new=AsyncMock(return_value={"id": "user-1"})), \
         patch("bot.handlers.buttons.get_pending_flow", return_value=flow), \
         patch("bot.handlers.buttons.handle_confirm", new=AsyncMock()) as handle_confirm:
        await handle_button(update, MagicMock())

    handle_confirm.assert_not_awaited()
    update.callback_query.edit_message_text.assert_awaited_once()
    assert "Nieaktualny" in update.callback_query.edit_message_text.await_args.args[0]


@pytest.mark.asyncio
async def test_fresh_save_callback_in_same_second_confirms_pending_flow():
    from bot.handlers.buttons import handle_button

    update = _update("save:confirm")
    sent_at = datetime(2026, 5, 25, 15, 55, 27, tzinfo=timezone.utc)
    update.callback_query.message.date = sent_at
    flow = {
        "flow_type": "add_client",
        "flow_data": {},
        "updated_at": sent_at.replace(microsecond=293267).isoformat(),
    }

    claimed = {**flow, "processing_token": "claim-1"}
    with patch("bot.handlers.buttons._run_guards", new=AsyncMock(return_value={"id": "user-1"})), \
         patch("bot.handlers.buttons.get_pending_flow", return_value=flow), \
         patch("bot.handlers.buttons.claim_pending_flow", return_value=claimed), \
         patch("bot.handlers.buttons.handle_confirm", new=AsyncMock()) as handle_confirm:
        await handle_button(update, MagicMock())

    handle_confirm.assert_awaited_once_with(
        update, ANY, {"id": "user-1"}, {}, "", claimed_flow=claimed
    )
    update.callback_query.edit_message_text.assert_not_awaited()


@pytest.mark.asyncio
async def test_duplicate_save_callback_loses_atomic_claim_and_does_not_mutate():
    from bot.handlers.buttons import handle_button

    update = _update("save:confirm")
    flow = {
        "flow_type": "add_client",
        "flow_data": {},
        "updated_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    with patch("bot.handlers.buttons._run_guards", new=AsyncMock(return_value={"id": "user-1"})), \
         patch("bot.handlers.buttons.get_pending_flow", return_value=flow), \
         patch("bot.handlers.buttons.claim_pending_flow", return_value=None), \
         patch("bot.handlers.buttons.handle_confirm", new=AsyncMock()) as handle_confirm:
        await handle_button(update, MagicMock())

    handle_confirm.assert_not_awaited()
    assert "już przetwarzana" in update.callback_query.edit_message_text.await_args.args[0]


@pytest.mark.asyncio
async def test_cancel_callback_uses_canonical_cancel_copy():
    from bot.handlers.buttons import handle_button

    update = _update("cancel:any")
    flow = {
        "flow_type": "add_client",
        "flow_data": {},
        "updated_at": datetime.now(tz=timezone.utc).isoformat(),
    }

    with patch("bot.handlers.buttons._run_guards", new=AsyncMock(return_value={"id": "user-1"})), \
         patch("bot.handlers.buttons.get_pending_flow", return_value=flow), \
         patch("bot.handlers.buttons.delete_pending_flow") as delete_pending:
        await handle_button(update, MagicMock())

    delete_pending.assert_called_once_with(123)
    update.callback_query.edit_message_text.assert_awaited_once_with("❌ Anulowane.")


@pytest.mark.asyncio
async def test_duplicate_merge_callback_shows_r1_card_without_sheets_write():
    from bot.handlers.buttons import handle_button

    update = _update("merge:confirm")
    flow = {
        "flow_type": "add_client_duplicate",
        "flow_data": {
            "duplicate_row": 7,
            "client_data": {
                "Imię i nazwisko": "Jan Kowalski",
                "Miasto": "Warszawa",
                "Telefon": "600100200",
            },
            "client_name": "Jan Kowalski",
            "city": "Warszawa",
        },
    }

    with patch("bot.handlers.buttons._run_guards", new=AsyncMock(return_value={"id": "user-1"})), \
         patch("bot.handlers.buttons.get_pending_flow", return_value=flow), \
         patch("bot.handlers.buttons.update_client", new=AsyncMock()) as update_client, \
         patch("bot.handlers.buttons.delete_pending_flow") as delete_pending, \
         patch("bot.handlers.buttons.save_pending") as save_pending:
        await handle_button(update, MagicMock())

    update_client.assert_not_awaited()
    delete_pending.assert_not_called()
    saved_flow = save_pending.call_args.args[0]
    assert saved_flow.flow_type is PendingFlowType.ADD_CLIENT_DUPLICATE
    assert saved_flow.flow_data["duplicate_row"] == 7
    labels = [
        button.text
        for row in update.callback_query.edit_message_text.await_args.kwargs["reply_markup"].inline_keyboard
        for button in row
    ]
    assert labels == ["✅ Zapisać", "➕ Dopisać", "❌ Anulować"]


@pytest.mark.asyncio
async def test_generic_disambiguation_rejects_row_outside_candidate_allowlist():
    from bot.handlers.buttons import handle_button

    update = _update("select_client:99")
    flow = {
        "flow_type": "disambiguation",
        "flow_data": {
            "intent": "add_note",
            "note_text": "test",
            "candidate_rows": [7, 11],
        },
    }

    with patch("bot.handlers.buttons._run_guards", new=AsyncMock(return_value={"id": "user-1"})), \
         patch("bot.handlers.buttons.get_pending_flow", return_value=flow), \
         patch("bot.handlers.buttons.get_all_clients", new=AsyncMock()) as get_all_clients, \
         patch("bot.handlers.buttons.save_pending") as save_pending, \
         patch("bot.handlers.buttons.delete_pending_flow") as delete_pending:
        await handle_button(update, MagicMock())

    get_all_clients.assert_not_awaited()
    save_pending.assert_not_called()
    delete_pending.assert_called_once_with(123)
    assert "Nieprawidłowy wybór" in update.callback_query.edit_message_text.await_args.args[0]
