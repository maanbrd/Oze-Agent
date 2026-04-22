"""Handler integration for confirm -> add_client pipelines.

Pipeline-surface tests live in tests/mutations/test_add_client.py. This
file verifies the handler wiring: exact reply copy, R7 behavior, and
skip_delete/delete_pending_flow semantics for add_client and duplicate
merge confirm paths.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.handlers.text import handle_confirm
from shared.mutations import AddClientResult, UpdateClientFieldsResult


def _update(telegram_id: int = 123) -> MagicMock:
    upd = MagicMock()
    upd.effective_user.id = telegram_id
    upd.effective_message.reply_text = AsyncMock()
    upd.effective_message.reply_markdown_v2 = AsyncMock()
    return upd


def _pending_add_client(extra: dict | None = None) -> dict:
    data = {
        "client_data": {
            "Imię i nazwisko": "Jan Kowalski",
            "Miasto": "Warszawa",
            "Telefon": "600111222",
        },
    }
    if extra:
        data.update(extra)
    return {"flow_type": "add_client", "flow_data": data}


def _pending_add_client_duplicate(extra: dict | None = None) -> dict:
    data = {
        "duplicate_row": 7,
        "client_name": "Jan Kowalski",
        "city": "Warszawa",
        "client_data": {
            "Telefon": "600111222",
            "Status": "Nowy lead",
        },
    }
    if extra:
        data.update(extra)
    return {"flow_type": "add_client_duplicate", "flow_data": data}


@pytest.mark.asyncio
async def test_add_client_success_replies_and_fires_r7_keeps_pending():
    upd = _update()
    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value=_pending_add_client(),
    ), patch(
        "bot.handlers.text.commit_add_client",
        new=AsyncMock(return_value=AddClientResult(success=True, row=42)),
    ) as mock_pipeline, patch(
        "bot.handlers.text.send_next_action_prompt",
        new=AsyncMock(),
    ) as mock_r7, patch("bot.handlers.text.delete_pending_flow") as mock_delete:
        await handle_confirm(upd, MagicMock(), {"id": "u1"}, {}, "")

    mock_pipeline.assert_awaited_once_with(
        "u1",
        {
            "Imię i nazwisko": "Jan Kowalski",
            "Miasto": "Warszawa",
            "Telefon": "600111222",
        },
    )
    upd.effective_message.reply_text.assert_awaited_once_with("✅ Zapisane.")
    upd.effective_message.reply_markdown_v2.assert_not_called()
    mock_r7.assert_awaited_once()
    args = mock_r7.await_args.args
    assert args[1] == 123
    assert args[2] == "Jan Kowalski"
    assert args[3] == "Warszawa"
    assert mock_r7.await_args.kwargs["client_row"] == 42
    assert mock_r7.await_args.kwargs["current_status"] == ""
    mock_delete.assert_not_called()


@pytest.mark.asyncio
async def test_add_client_failure_replies_google_down_and_deletes_pending():
    upd = _update()
    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value=_pending_add_client(),
    ), patch(
        "bot.handlers.text.commit_add_client",
        new=AsyncMock(return_value=AddClientResult(success=False, error_message="google_down")),
    ), patch(
        "bot.handlers.text.format_error",
        return_value="ESCAPED_ERROR",
    ) as mock_error, patch(
        "bot.handlers.text.send_next_action_prompt",
        new=AsyncMock(),
    ) as mock_r7, patch("bot.handlers.text.delete_pending_flow") as mock_delete:
        await handle_confirm(upd, MagicMock(), {"id": "u1"}, {}, "")

    mock_error.assert_called_once_with("google_down")
    upd.effective_message.reply_markdown_v2.assert_awaited_once_with("ESCAPED_ERROR")
    upd.effective_message.reply_text.assert_not_called()
    mock_r7.assert_not_called()
    mock_delete.assert_called_once_with(123)


@pytest.mark.asyncio
async def test_add_client_duplicate_success_updates_and_fires_r7_keeps_pending():
    upd = _update()
    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value=_pending_add_client_duplicate(),
    ), patch(
        "bot.handlers.text.commit_update_client_fields",
        new=AsyncMock(return_value=UpdateClientFieldsResult(success=True)),
    ) as mock_pipeline, patch(
        "bot.handlers.text.send_next_action_prompt",
        new=AsyncMock(),
    ) as mock_r7, patch("bot.handlers.text.delete_pending_flow") as mock_delete:
        await handle_confirm(upd, MagicMock(), {"id": "u1"}, {}, "")

    mock_pipeline.assert_awaited_once_with(
        "u1",
        7,
        {"Telefon": "600111222", "Status": "Nowy lead"},
    )
    upd.effective_message.reply_text.assert_awaited_once_with("✅ Dane zaktualizowane.")
    upd.effective_message.reply_markdown_v2.assert_not_called()
    mock_r7.assert_awaited_once()
    args = mock_r7.await_args.args
    assert args[1] == 123
    assert args[2] == "Jan Kowalski"
    assert args[3] == "Warszawa"
    assert mock_r7.await_args.kwargs["client_row"] == 7
    assert mock_r7.await_args.kwargs["current_status"] == "Nowy lead"
    mock_delete.assert_not_called()


@pytest.mark.asyncio
async def test_add_client_duplicate_failure_replies_google_down_and_deletes_pending():
    upd = _update()
    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value=_pending_add_client_duplicate(),
    ), patch(
        "bot.handlers.text.commit_update_client_fields",
        new=AsyncMock(return_value=UpdateClientFieldsResult(success=False, error_message="google_down")),
    ), patch(
        "bot.handlers.text.format_error",
        return_value="ESCAPED_ERROR",
    ) as mock_error, patch(
        "bot.handlers.text.send_next_action_prompt",
        new=AsyncMock(),
    ) as mock_r7, patch("bot.handlers.text.delete_pending_flow") as mock_delete:
        await handle_confirm(upd, MagicMock(), {"id": "u1"}, {}, "")

    mock_error.assert_called_once_with("google_down")
    upd.effective_message.reply_markdown_v2.assert_awaited_once_with("ESCAPED_ERROR")
    upd.effective_message.reply_text.assert_not_called()
    mock_r7.assert_not_called()
    mock_delete.assert_called_once_with(123)


@pytest.mark.asyncio
async def test_add_client_duplicate_without_row_fallback_adds_and_deletes_pending():
    """Legacy fallback mirrors pre-5.5 behavior: only "✅ Zapisane.", no R7."""
    upd = _update()
    pending = _pending_add_client_duplicate({"duplicate_row": None})
    with patch(
        "bot.handlers.text.get_pending_flow",
        return_value=pending,
    ), patch(
        "bot.handlers.text.commit_add_client",
        new=AsyncMock(return_value=AddClientResult(success=True, row=43)),
    ) as mock_pipeline, patch(
        "bot.handlers.text.send_next_action_prompt",
        new=AsyncMock(),
    ) as mock_r7, patch("bot.handlers.text.delete_pending_flow") as mock_delete:
        await handle_confirm(upd, MagicMock(), {"id": "u1"}, {}, "")

    mock_pipeline.assert_awaited_once_with(
        "u1",
        {"Telefon": "600111222", "Status": "Nowy lead"},
    )
    upd.effective_message.reply_text.assert_awaited_once_with("✅ Zapisane.")
    upd.effective_message.reply_markdown_v2.assert_not_called()
    mock_r7.assert_not_called()
    mock_delete.assert_called_once_with(123)
