"""Routing tests for the r7_prompt branch of _route_pending_flow.

Covers the contract that pending_flow is the source of truth for client
context: an incomplete temporal reply must not delete the R7 flow, so the
follow-up message can recover the same client.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.handlers.text import _route_pending_flow


def _flow(client_name: str = "Karol Łukaszewicz", city: str = "Janki") -> dict:
    return {
        "flow_type": "r7_prompt",
        "flow_data": {"client_name": client_name, "city": city},
    }


def _update(telegram_id: int = 123) -> MagicMock:
    upd = MagicMock()
    upd.effective_user.id = telegram_id
    upd.effective_message.reply_text = AsyncMock()
    upd.effective_message.reply_markdown_v2 = AsyncMock()
    return upd


@pytest.mark.asyncio
async def test_r7_bare_spotkanie_keeps_flow_alive():
    """Bare 'Spotkanie' (temporal marker, no time) must NOT delete R7."""
    upd = _update()
    with patch("bot.handlers.text.delete_pending_flow") as mock_delete, \
         patch(
             "bot.handlers.text.handle_add_meeting", new=AsyncMock()
         ) as mock_meeting:
        consumed = await _route_pending_flow(upd, MagicMock(), {}, _flow(), "Spotkanie")
    assert consumed is True
    mock_delete.assert_not_called()
    # handle_add_meeting was invoked with the R7-context-enriched message.
    mock_meeting.assert_awaited_once()
    args, _ = mock_meeting.call_args
    assert args[3]["entities"]["event_type"] == "in_person"
    assert "Karol Łukaszewicz" in args[4]
    assert "Janki" in args[4]


@pytest.mark.asyncio
async def test_r7_followup_with_time_keeps_client_context():
    """After a bare 'Spotkanie' kept R7 alive, the next message 'w piątek o 14'
    must still route through the r7 branch with the original client context."""
    upd = _update()
    with patch("bot.handlers.text.delete_pending_flow") as mock_delete, \
         patch(
             "bot.handlers.text.handle_add_meeting", new=AsyncMock()
         ) as mock_meeting:
        consumed = await _route_pending_flow(
            upd, MagicMock(), {}, _flow(), "w piątek o 14"
        )
    assert consumed is True
    mock_delete.assert_not_called()
    mock_meeting.assert_awaited_once()
    args, _ = mock_meeting.call_args
    assert args[3]["entities"]["event_type"] == "in_person"
    # _message_with_r7_client_context appended client name + city
    assert "Karol Łukaszewicz" in args[4]
    assert "Janki" in args[4]
    assert "w piątek o 14" in args[4]


@pytest.mark.asyncio
async def test_r7_complete_meeting_phrase_routes_to_add_meeting():
    """A complete temporal+time phrase should still route to add_meeting with
    R7 context. handle_add_meeting will internally upsert add_meeting flow,
    replacing R7 by telegram_id PK — we just verify the branch routed."""
    upd = _update()
    with patch("bot.handlers.text.delete_pending_flow") as mock_delete, \
         patch(
             "bot.handlers.text.handle_add_meeting", new=AsyncMock()
         ) as mock_meeting:
        consumed = await _route_pending_flow(
            upd, MagicMock(), {}, _flow(), "spotkanie jutro o 14"
        )
    assert consumed is True
    mock_delete.assert_not_called()
    mock_meeting.assert_awaited_once()
    args, _ = mock_meeting.call_args
    assert args[3]["entities"]["event_type"] == "in_person"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "message_text, expected_event_type",
    [
        ("spotkanie z Kowalskim, zadzwoń wcześniej", "phone_call"),
        ("zadzwonić w piątek o 10", "phone_call"),
        ("wysłać ofertę w środę", "offer_email"),
        ("follow-up dokumentowy w poniedziałek", "doc_followup"),
    ],
)
async def test_r7_infers_event_type_for_temporal_replies(message_text, expected_event_type):
    upd = _update()
    with patch("bot.handlers.text.delete_pending_flow") as mock_delete, \
         patch(
             "bot.handlers.text.handle_add_meeting", new=AsyncMock()
         ) as mock_meeting:
        consumed = await _route_pending_flow(upd, MagicMock(), {}, _flow(), message_text)
    assert consumed is True
    mock_delete.assert_not_called()
    args, _ = mock_meeting.call_args
    assert args[3]["entities"]["event_type"] == expected_event_type


@pytest.mark.asyncio
@pytest.mark.parametrize("text", ["nic", "later", "nie wiem", "odłóż", "odłożyć"])
async def test_r7_specific_cancel_phrase_deletes_flow(text):
    """R7-branch-specific cancel phrases (not caught by the global is_no
    short-circuit at the top of _route_pending_flow)."""
    upd = _update()
    with patch("bot.handlers.text.delete_pending_flow") as mock_delete, \
         patch(
             "bot.handlers.text.handle_add_meeting", new=AsyncMock()
         ) as mock_meeting:
        consumed = await _route_pending_flow(upd, MagicMock(), {}, _flow(), text)
    assert consumed is True
    mock_delete.assert_called_once_with(123)
    mock_meeting.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("text", ["nie", "anuluj", "stop"])
async def test_r7_global_cancel_phrase_routes_through_cancel_flow(text):
    """Global is_no words (nie/anuluj/stop) hit the early short-circuit at
    the top of _route_pending_flow, so they never reach the r7 branch.
    handle_cancel_flow is responsible for deleting the pending flow."""
    upd = _update()
    with patch("bot.handlers.text.handle_cancel_flow", new=AsyncMock()) as mock_cancel, \
         patch(
             "bot.handlers.text.handle_add_meeting", new=AsyncMock()
         ) as mock_meeting:
        consumed = await _route_pending_flow(upd, MagicMock(), {}, _flow(), text)
    assert consumed is True
    mock_cancel.assert_awaited_once()
    mock_meeting.assert_not_called()


@pytest.mark.asyncio
async def test_r7_unclear_reply_deletes_flow():
    """No temporal markers at all → drop R7 (consume silently)."""
    upd = _update()
    with patch("bot.handlers.text.delete_pending_flow") as mock_delete, \
         patch(
             "bot.handlers.text.handle_add_meeting", new=AsyncMock()
         ) as mock_meeting:
        consumed = await _route_pending_flow(
            upd, MagicMock(), {}, _flow(), "lol ok dzięki"
        )
    assert consumed is True
    mock_delete.assert_called_once_with(123)
    mock_meeting.assert_not_called()
