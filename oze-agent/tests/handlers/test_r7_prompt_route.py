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
async def test_r7_forwards_resolved_client_row_to_add_meeting():
    """Slice 5.1d.1: R7 flow_data carries client_row + current_status from the
    prior mutation confirm. _route_pending_flow must pass them through to
    handle_add_meeting via intent_data so _enrich_meeting can skip lookup_client."""
    upd = _update()
    flow = {
        "flow_type": "r7_prompt",
        "flow_data": {
            "client_name": "Mariusz Krzywinski",
            "city": "Wołomin",
            "client_row": 11,
            "current_status": "Podpisane",
        },
    }
    with patch("bot.handlers.text.delete_pending_flow"), \
         patch("bot.handlers.text.handle_add_meeting", new=AsyncMock()) as mock_meeting:
        consumed = await _route_pending_flow(
            upd, MagicMock(), {}, flow, "telefon jutro o 12"
        )

    assert consumed is True
    mock_meeting.assert_awaited_once()
    args, _ = mock_meeting.call_args
    intent_data = args[3]
    assert intent_data["r7_client_row"] == 11
    assert intent_data["r7_current_status"] == "Podpisane"
    assert intent_data["r7_client_name"] == "Mariusz Krzywinski"
    assert intent_data["r7_city"] == "Wołomin"
    assert intent_data["entities"]["event_type"] == "phone_call"


@pytest.mark.asyncio
async def test_r7_without_resolved_row_omits_propagation_keys():
    """Legacy R7 pending without client_row must not leak missing keys —
    handle_add_meeting keeps its original lookup behavior."""
    upd = _update()
    with patch("bot.handlers.text.delete_pending_flow"), \
         patch("bot.handlers.text.handle_add_meeting", new=AsyncMock()) as mock_meeting:
        await _route_pending_flow(upd, MagicMock(), {}, _flow(), "telefon jutro o 12")

    args, _ = mock_meeting.call_args
    intent_data = args[3]
    assert "r7_client_row" not in intent_data
    assert "r7_current_status" not in intent_data
    assert "r7_client_name" not in intent_data


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
async def test_r7_unclear_reply_deletes_flow_and_sends_feedback():
    """No markers at all → drop R7, but tell the user what we expected.

    Slice 5.1d.2: the previous contract silently consumed off-topic replies,
    which produced a typing-indicator-then-nothing UX on Telegram. Now the
    handler replies with an example of valid follow-ups before dropping R7.
    """
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
    upd.effective_message.reply_text.assert_awaited_once()
    feedback = upd.effective_message.reply_text.await_args.args[0]
    assert "Nie rozumiem" in feedback
    assert "spotkanie" in feedback.lower()
    assert "nic" in feedback.lower()


@pytest.mark.asyncio
@pytest.mark.parametrize("text", ["telefon", "mail", "oferta", "e-mail", "zadzwonić"])
async def test_r7_bare_event_type_word_routes_to_add_meeting(text):
    """Slice 5.1d.2: a bare event-type word from the R7 prompt options must
    route to handle_add_meeting (which then asks for time), not silent-delete.

    The R7 prompt advertises "Spotkanie, telefon, mail, odłożyć na później?",
    so users answering with just "telefon" were being silently dropped before
    this fix because _TEMPORAL_MARKERS did not include event-type words.
    """
    upd = _update()
    with patch("bot.handlers.text.delete_pending_flow") as mock_delete, \
         patch(
             "bot.handlers.text.handle_add_meeting", new=AsyncMock()
         ) as mock_meeting:
        consumed = await _route_pending_flow(upd, MagicMock(), {}, _flow(), text)
    assert consumed is True
    mock_delete.assert_not_called()
    mock_meeting.assert_awaited_once()
    upd.effective_message.reply_text.assert_not_called()
