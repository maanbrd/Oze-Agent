"""Handler flow tests for bot/handlers/voice.py + voice button callbacks +
voice correction routing in text.py.

Mocks Telegram + Whisper + Claude + pending flow store. Tests focus on
flow shape and routing correctness — full Telegram integration is out
of scope for unit tests.

Per plan v5: test #11 (slash-command bypass) lives in
test_cancel_command.py — slash-commands never reach handle_text.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── Test fixtures (mocked Telegram Update) ─────────────────────────────────


def _make_voice_update(telegram_id: int = 12345):
    update = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = telegram_id
    update.message = MagicMock()
    update.message.voice = MagicMock()
    update.message.voice.file_id = "test_voice_file_id"
    update.message.audio = None
    update.message.reply_text = AsyncMock()
    update.message.reply_markdown_v2 = AsyncMock()
    return update


def _make_callback_update(telegram_id: int = 12345, callback_data: str = "voice_confirm:yes"):
    update = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = telegram_id
    update.callback_query = MagicMock()
    update.callback_query.from_user = update.effective_user
    update.callback_query.data = callback_data
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.callback_query.message = MagicMock()
    update.callback_query.message.text = "transcript card text"
    update.effective_message = update.callback_query.message
    return update


def _make_context():
    context = MagicMock()
    context.bot = MagicMock()
    fake_file = MagicMock()
    fake_file.download_as_bytearray = AsyncMock(return_value=bytearray(b"fake-audio"))
    context.bot.get_file = AsyncMock(return_value=fake_file)
    return context


def _whisper_result(text: str, confidence: float = 0.9, duration: float = 5.0) -> dict:
    return {"text": text, "confidence": confidence, "duration_seconds": duration}


def _postproc_result(corrected: str, fallback: str | None = None, cost: float = 0.0001) -> dict:
    return {"corrected": corrected, "changes": [], "cost_usd": cost, "fallback": fallback}


# ── 1. handle_voice flow integration ───────────────────────────────────────


@pytest.mark.asyncio
async def test_high_confidence_does_not_fast_path_to_handle_text():
    """Vision: ALWAYS show transcript regardless of confidence. The old
    confidence ≥ 0.85 fast path that called handle_text directly is gone."""
    update = _make_voice_update()
    ctx = _make_context()

    with patch("bot.handlers.voice.is_private_chat", new=AsyncMock(return_value=True)), \
         patch("bot.handlers.voice._run_guards", new=AsyncMock(return_value={"id": "uid"})), \
         patch("bot.handlers.voice.send_processing_stage", new=AsyncMock()), \
         patch("bot.handlers.voice.transcribe_voice",
               new=AsyncMock(return_value=_whisper_result("dodaj klienta Jan", confidence=0.95))), \
         patch("bot.handlers.voice.normalize_polish_names",
               new=AsyncMock(return_value=_postproc_result("dodaj klienta Jan"))), \
         patch("bot.handlers.voice.increment_interaction", new=AsyncMock()), \
         patch("bot.handlers.voice.save_pending_flow") as mock_save_pending, \
         patch("bot.handlers.text.handle_text", new=AsyncMock()) as mock_handle_text:
        from bot.handlers.voice import handle_voice
        await handle_voice(update, ctx)

    # Pending was saved → user MUST click ✅ Tak before bot processes.
    mock_save_pending.assert_called_once()
    args, kwargs = mock_save_pending.call_args
    assert args[1] == "voice_transcription"
    # handle_text NOT invoked directly from handle_voice.
    mock_handle_text.assert_not_called()


@pytest.mark.asyncio
async def test_low_confidence_creates_same_pending_card_flow():
    update = _make_voice_update()
    ctx = _make_context()
    with patch("bot.handlers.voice.is_private_chat", new=AsyncMock(return_value=True)), \
         patch("bot.handlers.voice._run_guards", new=AsyncMock(return_value={"id": "uid"})), \
         patch("bot.handlers.voice.send_processing_stage", new=AsyncMock()), \
         patch("bot.handlers.voice.transcribe_voice",
               new=AsyncMock(return_value=_whisper_result("Jan", confidence=0.4))), \
         patch("bot.handlers.voice.normalize_polish_names",
               new=AsyncMock(return_value=_postproc_result("Jan"))), \
         patch("bot.handlers.voice.increment_interaction", new=AsyncMock()), \
         patch("bot.handlers.voice.save_pending_flow") as mock_save_pending:
        from bot.handlers.voice import handle_voice
        await handle_voice(update, ctx)
    mock_save_pending.assert_called_once()


@pytest.mark.asyncio
async def test_postproc_corrected_text_goes_to_card():
    """Whisper raw 'Jan Kowalsky' → Claude haiku corrects to 'Jan Kowalski'
    → card and pending payload BOTH carry the corrected text."""
    update = _make_voice_update()
    ctx = _make_context()
    with patch("bot.handlers.voice.is_private_chat", new=AsyncMock(return_value=True)), \
         patch("bot.handlers.voice._run_guards", new=AsyncMock(return_value={"id": "uid"})), \
         patch("bot.handlers.voice.send_processing_stage", new=AsyncMock()), \
         patch("bot.handlers.voice.transcribe_voice",
               new=AsyncMock(return_value=_whisper_result("Jan Kowalsky", confidence=0.9))), \
         patch("bot.handlers.voice.normalize_polish_names",
               new=AsyncMock(return_value=_postproc_result("Jan Kowalski"))), \
         patch("bot.handlers.voice.increment_interaction", new=AsyncMock()), \
         patch("bot.handlers.voice.save_pending_flow") as mock_save_pending:
        from bot.handlers.voice import handle_voice
        await handle_voice(update, ctx)

    # Pending data must contain the CORRECTED, not the raw, transcription.
    saved_data = mock_save_pending.call_args.args[2]
    assert saved_data["transcription"] == "Jan Kowalski"
    # Card also reflects corrected text.
    md_call = update.message.reply_markdown_v2.call_args
    assert "Jan Kowalski" in md_call.args[0]


@pytest.mark.asyncio
async def test_postproc_fallback_does_not_crash():
    """Claude haiku failure → handle_voice continues with raw Whisper text."""
    update = _make_voice_update()
    ctx = _make_context()
    fallback = _postproc_result("Jan raw", fallback="api_error", cost=0.0)
    with patch("bot.handlers.voice.is_private_chat", new=AsyncMock(return_value=True)), \
         patch("bot.handlers.voice._run_guards", new=AsyncMock(return_value={"id": "uid"})), \
         patch("bot.handlers.voice.send_processing_stage", new=AsyncMock()), \
         patch("bot.handlers.voice.transcribe_voice",
               new=AsyncMock(return_value=_whisper_result("Jan raw"))), \
         patch("bot.handlers.voice.normalize_polish_names",
               new=AsyncMock(return_value=fallback)), \
         patch("bot.handlers.voice.increment_interaction", new=AsyncMock()), \
         patch("bot.handlers.voice.save_pending_flow") as mock_save_pending:
        from bot.handlers.voice import handle_voice
        await handle_voice(update, ctx)
    # Card still rendered; pending saved; no crash.
    mock_save_pending.assert_called_once()
    update.message.reply_markdown_v2.assert_awaited_once()


@pytest.mark.asyncio
async def test_cost_log_fires_after_transcribe():
    """Whisper + Claude cost logged ZARAZ — independent of user click."""
    update = _make_voice_update()
    ctx = _make_context()
    with patch("bot.handlers.voice.is_private_chat", new=AsyncMock(return_value=True)), \
         patch("bot.handlers.voice._run_guards", new=AsyncMock(return_value={"id": "uid"})), \
         patch("bot.handlers.voice.send_processing_stage", new=AsyncMock()), \
         patch("bot.handlers.voice.transcribe_voice",
               new=AsyncMock(return_value=_whisper_result("Jan", duration=60))), \
         patch("bot.handlers.voice.normalize_polish_names",
               new=AsyncMock(return_value=_postproc_result("Jan", cost=0.0002))), \
         patch("bot.handlers.voice.save_pending_flow"), \
         patch("bot.handlers.voice.increment_interaction", new=AsyncMock()) as mock_inc:
        from bot.handlers.voice import handle_voice
        await handle_voice(update, ctx)

    mock_inc.assert_awaited_once()
    args = mock_inc.call_args.args
    # Expect (telegram_id, "voice_transcription", "whisper-1+haiku", 0, 0, total_cost)
    assert args[1] == "voice_transcription"
    assert args[2] == "whisper-1+haiku"
    # whisper_cost = (60/60) * 0.006 = 0.006; postproc_cost = 0.0002; total = 0.0062
    assert args[5] == pytest.approx(0.0062, rel=0.01)


@pytest.mark.asyncio
async def test_markdownv2_escape_for_special_chars():
    """Transcripts with `(`, `)`, `.`, `_`, `*` etc. must be escaped before
    rendering in MarkdownV2 mode — otherwise Telegram rejects the message."""
    update = _make_voice_update()
    ctx = _make_context()
    text_with_specials = "Jan Kowalski (Warszawa). Tel: 600-100-200!"
    with patch("bot.handlers.voice.is_private_chat", new=AsyncMock(return_value=True)), \
         patch("bot.handlers.voice._run_guards", new=AsyncMock(return_value={"id": "uid"})), \
         patch("bot.handlers.voice.send_processing_stage", new=AsyncMock()), \
         patch("bot.handlers.voice.transcribe_voice",
               new=AsyncMock(return_value=_whisper_result(text_with_specials))), \
         patch("bot.handlers.voice.normalize_polish_names",
               new=AsyncMock(return_value=_postproc_result(text_with_specials))), \
         patch("bot.handlers.voice.increment_interaction", new=AsyncMock()), \
         patch("bot.handlers.voice.save_pending_flow"):
        from bot.handlers.voice import handle_voice
        await handle_voice(update, ctx)

    md_text = update.message.reply_markdown_v2.call_args.args[0]
    # Reserved MarkdownV2 chars must be escaped — verify a sample.
    assert "\\(" in md_text  # opening paren escaped
    assert "\\)" in md_text  # closing paren escaped
    assert "\\." in md_text  # period escaped
    assert "\\!" in md_text  # exclamation escaped


@pytest.mark.asyncio
async def test_card_has_four_buttons():
    """Always-show card carries Tak / Popraw / Ponów / Anuluj."""
    update = _make_voice_update()
    ctx = _make_context()
    with patch("bot.handlers.voice.is_private_chat", new=AsyncMock(return_value=True)), \
         patch("bot.handlers.voice._run_guards", new=AsyncMock(return_value={"id": "uid"})), \
         patch("bot.handlers.voice.send_processing_stage", new=AsyncMock()), \
         patch("bot.handlers.voice.transcribe_voice",
               new=AsyncMock(return_value=_whisper_result("Jan"))), \
         patch("bot.handlers.voice.normalize_polish_names",
               new=AsyncMock(return_value=_postproc_result("Jan"))), \
         patch("bot.handlers.voice.increment_interaction", new=AsyncMock()), \
         patch("bot.handlers.voice.save_pending_flow"):
        from bot.handlers.voice import handle_voice
        await handle_voice(update, ctx)

    md_call = update.message.reply_markdown_v2.call_args
    keyboard = md_call.kwargs["reply_markup"]
    # Flatten button rows; verify all 4 callback values present.
    callback_data = []
    for row in keyboard.inline_keyboard:
        for btn in row:
            callback_data.append(btn.callback_data)
    assert "voice_confirm:yes" in callback_data
    assert "voice_confirm:correct" in callback_data
    assert "voice_confirm:retry" in callback_data
    assert "voice_confirm:cancel" in callback_data


@pytest.mark.asyncio
async def test_voice_overwrites_existing_pending():
    """Two voices in a row — second voice's transcription replaces first
    via save_pending_flow upsert (one active flow per telegram_id)."""
    update = _make_voice_update()
    ctx = _make_context()
    with patch("bot.handlers.voice.is_private_chat", new=AsyncMock(return_value=True)), \
         patch("bot.handlers.voice._run_guards", new=AsyncMock(return_value={"id": "uid"})), \
         patch("bot.handlers.voice.send_processing_stage", new=AsyncMock()), \
         patch("bot.handlers.voice.transcribe_voice",
               new=AsyncMock(side_effect=[
                   _whisper_result("Jan stary"),
                   _whisper_result("Marek nowy"),
               ])), \
         patch("bot.handlers.voice.normalize_polish_names",
               new=AsyncMock(side_effect=[
                   _postproc_result("Jan stary"),
                   _postproc_result("Marek nowy"),
               ])), \
         patch("bot.handlers.voice.increment_interaction", new=AsyncMock()), \
         patch("bot.handlers.voice.save_pending_flow") as mock_save:
        from bot.handlers.voice import handle_voice
        await handle_voice(update, ctx)
        await handle_voice(update, ctx)

    # save_pending_flow called twice — second call overrides first.
    assert mock_save.call_count == 2
    second_data = mock_save.call_args_list[1].args[2]
    assert second_data["transcription"] == "Marek nowy"


# ── 2. voice_confirm callback variants ─────────────────────────────────────


@pytest.mark.asyncio
async def test_voice_confirm_yes_routes_to_handle_text_with_exact_text():
    """Click ✅ Tak → bot mutates message.text to transcription, calls handle_text.
    Test #17: verify the EXACT text payload."""
    update = _make_callback_update(callback_data="voice_confirm:yes")
    ctx = MagicMock()
    flow = {
        "flow_type": "voice_transcription",
        "flow_data": {"transcription": "dodaj klienta Jan Kowalski"},
    }

    with patch("bot.handlers.buttons.is_private_chat", new=AsyncMock(return_value=True)), \
         patch("bot.handlers.buttons._run_guards", new=AsyncMock(return_value={"id": "uid"})), \
         patch("bot.handlers.buttons.get_pending_flow", return_value=flow), \
         patch("bot.handlers.buttons.delete_pending_flow") as mock_delete, \
         patch("bot.handlers.text.handle_text", new=AsyncMock()) as mock_handle:
        from bot.handlers.buttons import handle_button
        await handle_button(update, ctx)

    mock_delete.assert_called_once_with(12345)
    mock_handle.assert_awaited_once()
    # Mutated message text MUST equal the saved transcription.
    assert update.callback_query.message.text == "dodaj klienta Jan Kowalski"


@pytest.mark.asyncio
async def test_voice_confirm_correct_sets_awaiting_flag():
    """Click 📝 Popraw → pending flow gets `awaiting_text_correction=True`."""
    update = _make_callback_update(callback_data="voice_confirm:correct")
    ctx = MagicMock()
    flow = {
        "flow_type": "voice_transcription",
        "flow_data": {"transcription": "Jan Kowalski"},
    }
    with patch("bot.handlers.buttons.is_private_chat", new=AsyncMock(return_value=True)), \
         patch("bot.handlers.buttons._run_guards", new=AsyncMock(return_value={"id": "uid"})), \
         patch("bot.handlers.buttons.get_pending_flow", return_value=flow), \
         patch("bot.handlers.buttons.save_pending_flow") as mock_save, \
         patch("bot.handlers.buttons.delete_pending_flow") as mock_delete:
        from bot.handlers.buttons import handle_button
        await handle_button(update, ctx)

    mock_delete.assert_not_called()  # we DON'T delete — flag is set
    mock_save.assert_called_once()
    saved_data = mock_save.call_args.args[2]
    assert saved_data["awaiting_text_correction"] is True
    assert saved_data["transcription"] == "Jan Kowalski"


@pytest.mark.asyncio
async def test_voice_confirm_retry_clears_pending():
    """Click 🎤 Ponów → pending deleted, retry prompt shown."""
    update = _make_callback_update(callback_data="voice_confirm:retry")
    ctx = MagicMock()
    flow = {"flow_type": "voice_transcription", "flow_data": {"transcription": "x"}}
    with patch("bot.handlers.buttons.is_private_chat", new=AsyncMock(return_value=True)), \
         patch("bot.handlers.buttons._run_guards", new=AsyncMock(return_value={"id": "uid"})), \
         patch("bot.handlers.buttons.get_pending_flow", return_value=flow), \
         patch("bot.handlers.buttons.delete_pending_flow") as mock_delete:
        from bot.handlers.buttons import handle_button
        await handle_button(update, ctx)
    mock_delete.assert_called_once_with(12345)
    update.callback_query.edit_message_text.assert_awaited_once()
    msg = update.callback_query.edit_message_text.call_args.args[0]
    assert "Nagraj ponownie" in msg or "ponown" in msg.lower()


@pytest.mark.asyncio
async def test_voice_confirm_cancel_clears_pending():
    update = _make_callback_update(callback_data="voice_confirm:cancel")
    ctx = MagicMock()
    flow = {"flow_type": "voice_transcription", "flow_data": {"transcription": "x"}}
    with patch("bot.handlers.buttons.is_private_chat", new=AsyncMock(return_value=True)), \
         patch("bot.handlers.buttons._run_guards", new=AsyncMock(return_value={"id": "uid"})), \
         patch("bot.handlers.buttons.get_pending_flow", return_value=flow), \
         patch("bot.handlers.buttons.delete_pending_flow") as mock_delete:
        from bot.handlers.buttons import handle_button
        await handle_button(update, ctx)
    mock_delete.assert_called_once_with(12345)
    update.callback_query.edit_message_text.assert_awaited_once_with("❌ Anulowane.")


@pytest.mark.asyncio
async def test_voice_confirm_no_alias_acts_as_cancel():
    """Back-compat: legacy `voice_confirm:no` callbacks behave same as `:cancel`."""
    update = _make_callback_update(callback_data="voice_confirm:no")
    ctx = MagicMock()
    flow = {"flow_type": "voice_transcription", "flow_data": {"transcription": "x"}}
    with patch("bot.handlers.buttons.is_private_chat", new=AsyncMock(return_value=True)), \
         patch("bot.handlers.buttons._run_guards", new=AsyncMock(return_value={"id": "uid"})), \
         patch("bot.handlers.buttons.get_pending_flow", return_value=flow), \
         patch("bot.handlers.buttons.delete_pending_flow") as mock_delete:
        from bot.handlers.buttons import handle_button
        await handle_button(update, ctx)
    mock_delete.assert_called_once_with(12345)
    update.callback_query.edit_message_text.assert_awaited_once_with("❌ Anulowane.")


# ── 3. _route_pending_flow voice_transcription branch ──────────────────────


@pytest.mark.xfail(
    reason="text.py voice_transcription branch lands in Stage 4 of fragmented voice deploy; "
    "test xfailed in Stage 3 to keep suite green during incremental rollout.",
    strict=False,
)
@pytest.mark.asyncio
async def test_text_correction_falls_through_for_classify():
    """User types correction text after clicking 📝 Popraw → branch in
    _route_pending_flow deletes pending and returns False → caller falls
    through to normal classify+dispatch."""
    update = MagicMock()
    update.effective_user.id = 12345
    update.effective_message.reply_text = AsyncMock()
    flow = {
        "flow_type": "voice_transcription",
        "flow_data": {
            "transcription": "Jan Kowalski",
            "awaiting_text_correction": True,
        },
    }
    with patch("bot.handlers.text.delete_pending_flow") as mock_delete:
        from bot.handlers.text import _route_pending_flow
        consumed = await _route_pending_flow(
            update, MagicMock(), {"id": "uid"}, flow,
            "dodaj klienta Marek Nowak z Wyszkowa",
        )

    # Auto-cancel + fall-through (False = caller will run classify normally).
    assert consumed is False
    mock_delete.assert_called_once_with(12345)
    # No "anulowane" reply — the correction is just delivered to classify.
    update.effective_message.reply_text.assert_not_awaited()


@pytest.mark.xfail(
    reason="text.py voice_transcription branch lands in Stage 4 of fragmented voice deploy; "
    "test xfailed in Stage 3 to keep suite green during incremental rollout.",
    strict=False,
)
@pytest.mark.asyncio
async def test_anuluj_in_correction_mode_cancels():
    """User types 'anuluj' in correction mode → R3 manual override:
    pending deleted, "Anulowane" reply, NOT classified as add_client."""
    update = MagicMock()
    update.effective_user.id = 12345
    update.effective_message.reply_text = AsyncMock()
    flow = {
        "flow_type": "voice_transcription",
        "flow_data": {
            "transcription": "x",
            "awaiting_text_correction": True,
        },
    }
    with patch("bot.handlers.text.delete_pending_flow") as mock_delete:
        from bot.handlers.text import _route_pending_flow
        consumed = await _route_pending_flow(
            update, MagicMock(), {"id": "uid"}, flow, "anuluj",
        )

    # Consumed = True → caller does NOT fall through to classify.
    assert consumed is True
    mock_delete.assert_called_once_with(12345)
    update.effective_message.reply_text.assert_awaited_once_with("❌ Anulowane.")


@pytest.mark.asyncio
async def test_voice_pending_without_awaiting_falls_through_to_legacy():
    """Voice pending exists but awaiting_text_correction is FALSE — branch
    falls through (does NOT auto-cancel). The legacy is_yes/is_no logic
    further down handles the user's text in the generic confirmation way."""
    update = MagicMock()
    update.effective_user.id = 12345
    update.effective_message.reply_text = AsyncMock()
    flow = {
        "flow_type": "voice_transcription",
        "flow_data": {"transcription": "x"},  # no awaiting_text_correction
    }
    # Sending plain "tak" → should be picked up by generic is_yes branch
    # → handle_confirm called. Mock that.
    with patch("bot.handlers.text.delete_pending_flow"), \
         patch("bot.handlers.text.handle_confirm", new=AsyncMock()) as mock_confirm:
        from bot.handlers.text import _route_pending_flow
        consumed = await _route_pending_flow(
            update, MagicMock(), {"id": "uid"}, flow, "tak",
        )

    # The legacy is_yes path handles it (consumed=True via handle_confirm).
    assert consumed is True
    mock_confirm.assert_awaited_once()


# ── 4. PII redaction ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pii_redaction_in_voice_logger():
    """Voice handler's logger calls must NOT contain raw transcription
    or change pairs. Only safe summary fields allowed."""
    update = _make_voice_update()
    ctx = _make_context()
    sensitive = "Jan Kowalski mieszka w Warszawie tel 600100200"

    with patch("bot.handlers.voice.is_private_chat", new=AsyncMock(return_value=True)), \
         patch("bot.handlers.voice._run_guards", new=AsyncMock(return_value={"id": "uid"})), \
         patch("bot.handlers.voice.send_processing_stage", new=AsyncMock()), \
         patch("bot.handlers.voice.transcribe_voice",
               new=AsyncMock(return_value=_whisper_result(sensitive))), \
         patch("bot.handlers.voice.normalize_polish_names",
               new=AsyncMock(return_value=_postproc_result(sensitive))), \
         patch("bot.handlers.voice.increment_interaction", new=AsyncMock()), \
         patch("bot.handlers.voice.save_pending_flow"), \
         patch("bot.handlers.voice.logger") as mock_logger:
        from bot.handlers.voice import handle_voice
        await handle_voice(update, ctx)

    # Inspect ALL logger calls. None should contain the sensitive content.
    all_call_repr = []
    for call in mock_logger.mock_calls:
        # call is (name, args, kwargs); we look at the formatted string.
        all_call_repr.append(repr(call))
    full_log_text = " ".join(all_call_repr)
    assert "Kowalski" not in full_log_text
    assert "Warszawie" not in full_log_text
    assert "600100200" not in full_log_text
