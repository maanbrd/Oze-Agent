"""Slice 5.1d.3 — pre-confirm disambiguation for add_meeting.

Covers the two new behaviours:

* `handle_add_meeting` stops at an ambiguity gate instead of saving an
  AddMeetingPayload straight to confirm card when lookup_client returns
  multi. Over-cap multi short-circuits with a "dopisz więcej danych"
  message and saves nothing.

* `_handle_select_client` grew two resume paths — picking a candidate
  (AddMeetingPayload with client_row pre-resolved) and "Żaden z nich"
  (AddMeetingPayload with client_row=None). A row outside the pending
  candidate set must be rejected; a compound status_update.row that
  disagrees with the pick must also be rejected to avoid silent sync to
  the wrong row.

Gate A fallback for legacy pendings (ambiguous_client=True landing
directly in handle_confirm) is covered separately in
test_add_meeting_ambiguous.py and is intentionally not duplicated here.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.handlers.buttons import _handle_select_client
from bot.handlers.text import handle_add_meeting
from shared.pending import PendingFlowType


# ── Fixtures ──────────────────────────────────────────────────────────────────


def _update(telegram_id: int = 123) -> MagicMock:
    upd = MagicMock()
    upd.effective_user.id = telegram_id
    upd.effective_message.reply_text = AsyncMock()
    upd.effective_message.reply_markdown_v2 = AsyncMock()
    return upd


def _query(telegram_id: int = 123) -> MagicMock:
    q = MagicMock()
    q.from_user.id = telegram_id
    q.edit_message_text = AsyncMock()
    q.message.reply_markdown_v2 = AsyncMock()
    return q


def _candidates_two() -> list[dict]:
    return [
        {"row": 7, "full_name": "Mariusz Krzywinski", "city": "Marki", "current_status": "Oferta wysłana"},
        {"row": 11, "full_name": "Mariusz Krzywinski", "city": "Wołomin", "current_status": "Nowy lead"},
    ]


def _enriched_ambiguous(candidates: list[dict]) -> dict:
    return {
        "title": "Spotkanie — Mariusz Krzywinski",
        "location": "",
        "description": "",
        "full_name": "Mariusz Krzywinski",
        "client_found": False,
        "client_row": None,
        "current_status": "",
        "client_city": "",
        "ambiguous_client": True,
        "ambiguous_candidates": candidates,
    }


def _meeting() -> dict:
    return {
        "date": "2027-05-10",
        "time": "14:00",
        "client_name": "Mariusz Krzywinski",
        "location": "",
    }


async def _call_handle_add_meeting(upd: MagicMock, enriched: dict) -> dict:
    """Run handle_add_meeting with extract_meeting_data/_enrich_meeting mocked.

    Returns the mock_save.call_args so each test can assert on save behaviour.
    """
    with patch(
        "bot.handlers.text.extract_meeting_data",
        new=AsyncMock(return_value={"meetings": [_meeting()]}),
    ), patch(
        "bot.handlers.text._enrich_meeting",
        new=AsyncMock(return_value=enriched),
    ), patch(
        "bot.handlers.text.check_conflicts",
        new=AsyncMock(return_value=[]),
    ), patch("bot.handlers.text.save_pending") as mock_save:
        await handle_add_meeting(
            upd,
            MagicMock(),
            {"id": 1, "default_meeting_duration": 60},
            {"entities": {"event_type": "in_person"}},
            "spotkanie z Mariuszem Krzywinskim jutro o 14",
        )
    return mock_save


# ── handle_add_meeting ambiguous branch ──────────────────────────────────────


@pytest.mark.asyncio
async def test_multi_saves_disambiguation_pending_and_skips_confirm_card():
    upd = _update()
    mock_save = await _call_handle_add_meeting(upd, _enriched_ambiguous(_candidates_two()))

    mock_save.assert_called_once()
    saved = mock_save.call_args.args[0]
    assert saved.flow_type is PendingFlowType.ADD_MEETING_DISAMBIGUATION
    assert len(saved.flow_data["candidates"]) == 2
    assert saved.flow_data["client_name"] == "Mariusz Krzywinski"
    # "start" / "end" are ISO strings carrying the already-parsed datetime
    assert saved.flow_data["start"].startswith("2027-05-10T14:00")

    upd.effective_message.reply_text.assert_awaited_once()
    text_arg = upd.effective_message.reply_text.await_args.args[0]
    assert "Mam 2 klientów" in text_arg
    assert "Którego użyć do spotkania?" in text_arg
    # Confirm card must NOT have been sent
    upd.effective_message.reply_markdown_v2.assert_not_called()


def _callback_data_list(reply_text_mock: AsyncMock) -> list[str]:
    keyboard = reply_text_mock.await_args.kwargs["reply_markup"].inline_keyboard
    return [btn.callback_data for row in keyboard for btn in row]


def _button_labels(reply_text_mock: AsyncMock) -> list[str]:
    keyboard = reply_text_mock.await_args.kwargs["reply_markup"].inline_keyboard
    return [btn.text for row in keyboard for btn in row]


@pytest.mark.asyncio
async def test_button_labels_include_name_and_city():
    upd = _update()
    await _call_handle_add_meeting(upd, _enriched_ambiguous(_candidates_two()))

    labels = _button_labels(upd.effective_message.reply_text)
    assert "Mariusz Krzywinski — Marki" in labels
    assert "Mariusz Krzywinski — Wołomin" in labels
    assert "Żaden z nich" in labels

    callbacks = _callback_data_list(upd.effective_message.reply_text)
    assert "select_client:7" in callbacks
    assert "select_client:11" in callbacks
    assert "select_client:none" in callbacks


@pytest.mark.asyncio
async def test_button_labels_fallback_to_name_only_when_no_city():
    upd = _update()
    candidates = [
        {"row": 5, "full_name": "Jan Kowalski", "city": "", "current_status": ""},
        {"row": 9, "full_name": "Jan Kowalski", "city": "Warszawa", "current_status": ""},
    ]
    await _call_handle_add_meeting(upd, _enriched_ambiguous(candidates))

    labels = _button_labels(upd.effective_message.reply_text)
    assert "Jan Kowalski" in labels             # city-less candidate
    assert "Jan Kowalski — Warszawa" in labels
    assert "Żaden z nich" in labels


@pytest.mark.asyncio
async def test_multi_over_cap_sends_fallback_message_and_saves_nothing():
    upd = _update()
    candidates = [
        {"row": 100 + i, "full_name": "Jan Kowalski", "city": f"City{i}", "current_status": ""}
        for i in range(11)
    ]
    mock_save = await _call_handle_add_meeting(upd, _enriched_ambiguous(candidates))

    mock_save.assert_not_called()
    upd.effective_message.reply_text.assert_awaited_once()
    text_arg = upd.effective_message.reply_text.await_args.args[0]
    assert "Znalazłem 11 klientów" in text_arg
    assert "Dopisz więcej danych klienta" in text_arg
    upd.effective_message.reply_markdown_v2.assert_not_called()


# ── _handle_select_client — disambiguation resume ────────────────────────────


def _pending_disambiguation(status_update=None, source_client_data=None):
    return {
        "flow_type": "add_meeting_disambiguation",
        "flow_data": {
            "title": "Spotkanie — Mariusz Krzywinski",
            "start": "2027-05-10T14:00:00+02:00",
            "end": "2027-05-10T15:00:00+02:00",
            "client_name": "Mariusz Krzywinski",
            "location": "",
            "description": "",
            "event_type": "in_person",
            "status_update": status_update,
            "source_client_data": source_client_data,
            "candidates": _candidates_two(),
        },
    }


def _client_row(row: int, status: str = "Oferta wysłana", city: str = "Marki") -> dict:
    return {
        "_row": row,
        "Imię i nazwisko": "Mariusz Krzywinski",
        "Miasto": city,
        "Adres": "ul. Testowa 1",
        "Telefon": "600100200",
        "Status": status,
        "Produkt": "PV",
    }


@pytest.mark.asyncio
async def test_select_candidate_saves_add_meeting_pending_with_enriched_row():
    q = _query()
    with patch(
        "bot.handlers.buttons.get_pending_flow",
        return_value=_pending_disambiguation(),
    ), patch(
        "bot.handlers.buttons.get_all_clients",
        new=AsyncMock(return_value=[_client_row(7, status="Oferta wysłana")]),
    ), patch(
        "bot.handlers.buttons.check_conflicts",
        new=AsyncMock(return_value=[]),
    ), patch("bot.handlers.buttons.save_pending") as mock_save:
        await _handle_select_client(q, MagicMock(), {"id": "u1"}, "7")

    mock_save.assert_called_once()
    saved = mock_save.call_args.args[0]
    assert saved.flow_type is PendingFlowType.ADD_MEETING
    assert saved.flow_data["client_row"] == 7
    assert saved.flow_data["current_status"] == "Oferta wysłana"
    assert saved.flow_data.get("ambiguous_client", False) is False
    q.message.reply_markdown_v2.assert_awaited_once()


@pytest.mark.asyncio
async def test_select_candidate_row_not_in_pending_candidates_rejects():
    """Row 99 exists in the sheet but is NOT a pending candidate — reject."""
    q = _query()
    with patch(
        "bot.handlers.buttons.get_pending_flow",
        return_value=_pending_disambiguation(),
    ), patch(
        "bot.handlers.buttons.get_all_clients",
        new=AsyncMock(return_value=[_client_row(99)]),
    ), patch("bot.handlers.buttons.delete_pending_flow") as mock_delete, \
         patch("bot.handlers.buttons.save_pending") as mock_save:
        await _handle_select_client(q, MagicMock(), {"id": "u1"}, "99")

    mock_save.assert_not_called()
    mock_delete.assert_called_once_with(123)
    q.edit_message_text.assert_awaited_once()
    msg = q.edit_message_text.await_args.args[0]
    assert "Nieprawidłowy wybór" in msg


@pytest.mark.asyncio
async def test_select_candidate_nowy_lead_in_person_recomputes_auto_upgrade():
    """status_update=None in flow_data → recompute from selected client.

    Chosen row=11 has Status='Nowy lead', event_type=in_person →
    _auto_status_update_from_enriched should produce a status_update
    pointing at row=11 with new_value='Spotkanie umówione'.
    """
    q = _query()
    with patch(
        "bot.handlers.buttons.get_pending_flow",
        return_value=_pending_disambiguation(status_update=None),
    ), patch(
        "bot.handlers.buttons.get_all_clients",
        new=AsyncMock(return_value=[_client_row(11, status="Nowy lead", city="Wołomin")]),
    ), patch(
        "bot.handlers.buttons.check_conflicts",
        new=AsyncMock(return_value=[]),
    ), patch("bot.handlers.buttons.save_pending") as mock_save:
        await _handle_select_client(q, MagicMock(), {"id": "u1"}, "11")

    saved = mock_save.call_args.args[0]
    status_update = saved.flow_data["status_update"]
    assert status_update["row"] == 11
    assert status_update["old_value"] == "Nowy lead"
    assert status_update["new_value"] == "Spotkanie umówione"


@pytest.mark.asyncio
async def test_select_candidate_compound_row_mismatch_rejects():
    """Defensive guard: status_update already has row=42 but user picks 7 —
    that's an inconsistent state (change_status confirm should have prevented
    the ambiguous branch from firing). Reject rather than silent-sync wrong row.
    """
    q = _query()
    pending = _pending_disambiguation(
        status_update={"row": 42, "field": "Status", "old_value": "Oferta wysłana",
                       "new_value": "Podpisane", "client_name": "Mariusz Krzywinski", "city": ""},
    )
    with patch(
        "bot.handlers.buttons.get_pending_flow",
        return_value=pending,
    ), patch(
        "bot.handlers.buttons.get_all_clients",
        new=AsyncMock(return_value=[_client_row(7)]),
    ), patch("bot.handlers.buttons.delete_pending_flow") as mock_delete, \
         patch("bot.handlers.buttons.save_pending") as mock_save:
        await _handle_select_client(q, MagicMock(), {"id": "u1"}, "7")

    mock_save.assert_not_called()
    mock_delete.assert_called_once_with(123)
    msg = q.edit_message_text.await_args.args[0]
    assert "Nieprawidłowy wybór" in msg


@pytest.mark.asyncio
async def test_select_candidate_compound_row_empty_fills_from_selection():
    """Compound status_update carried no row (rare edge case) — fill with
    the selected row so K/L/P+F all sync to the same client on confirm.
    """
    q = _query()
    pending = _pending_disambiguation(
        status_update={"row": None, "field": "Status", "old_value": "Oferta wysłana",
                       "new_value": "Podpisane", "client_name": "Mariusz Krzywinski", "city": ""},
    )
    with patch(
        "bot.handlers.buttons.get_pending_flow",
        return_value=pending,
    ), patch(
        "bot.handlers.buttons.get_all_clients",
        new=AsyncMock(return_value=[_client_row(7)]),
    ), patch(
        "bot.handlers.buttons.check_conflicts",
        new=AsyncMock(return_value=[]),
    ), patch("bot.handlers.buttons.save_pending") as mock_save:
        await _handle_select_client(q, MagicMock(), {"id": "u1"}, "7")

    saved = mock_save.call_args.args[0]
    su = saved.flow_data["status_update"]
    assert su["row"] == 7
    assert su["new_value"] == "Podpisane"
    assert saved.flow_data["client_row"] == 7


# ── "Żaden z nich" ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_none_saves_add_meeting_pending_without_client_row():
    q = _query()
    with patch(
        "bot.handlers.buttons.get_pending_flow",
        return_value=_pending_disambiguation(),
    ), patch(
        "bot.handlers.buttons.check_conflicts",
        new=AsyncMock(return_value=[]),
    ), patch("bot.handlers.buttons.save_pending") as mock_save:
        await _handle_select_client(q, MagicMock(), {"id": "u1"}, "none")

    saved = mock_save.call_args.args[0]
    assert saved.flow_type is PendingFlowType.ADD_MEETING
    assert saved.flow_data.get("client_row") is None
    assert saved.flow_data.get("ambiguous_client", False) is False
    assert saved.flow_data["client_name"] == "Mariusz Krzywinski"
    # status_update is dropped when no client is chosen
    assert saved.flow_data.get("status_update") is None
    q.message.reply_markdown_v2.assert_awaited_once()


@pytest.mark.asyncio
async def test_none_preserves_source_client_data_for_not_found_preseed():
    q = _query()
    source = {"Imię i nazwisko": "Mariusz Krzywinski", "Telefon": "600100200"}
    with patch(
        "bot.handlers.buttons.get_pending_flow",
        return_value=_pending_disambiguation(source_client_data=source),
    ), patch(
        "bot.handlers.buttons.check_conflicts",
        new=AsyncMock(return_value=[]),
    ), patch("bot.handlers.buttons.save_pending") as mock_save:
        await _handle_select_client(q, MagicMock(), {"id": "u1"}, "none")

    saved = mock_save.call_args.args[0]
    assert saved.flow_data["client_data"] == source


@pytest.mark.asyncio
async def test_none_without_disambiguation_flow_shows_invalid_choice():
    """'none' sentinel outside the add_meeting_disambiguation flow is an error."""
    q = _query()
    with patch("bot.handlers.buttons.get_pending_flow", return_value=None):
        await _handle_select_client(q, MagicMock(), {"id": "u1"}, "none")

    q.edit_message_text.assert_awaited_once()
    assert "Nieprawidłowy wybór" in q.edit_message_text.await_args.args[0]


# ── Conflict warning recomputation ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_select_candidate_recomputes_conflict_warning():
    q = _query()
    with patch(
        "bot.handlers.buttons.get_pending_flow",
        return_value=_pending_disambiguation(),
    ), patch(
        "bot.handlers.buttons.get_all_clients",
        new=AsyncMock(return_value=[_client_row(7)]),
    ), patch(
        "bot.handlers.buttons.check_conflicts",
        new=AsyncMock(return_value=[{"title": "Inne spotkanie"}]),
    ), patch("bot.handlers.buttons.save_pending"):
        await _handle_select_client(q, MagicMock(), {"id": "u1"}, "7")

    msg = q.message.reply_markdown_v2.await_args.args[0]
    assert "Uwaga" in msg
    assert "Inne spotkanie" in msg


# ── _enrich_meeting multi includes candidates ────────────────────────────────


@pytest.mark.asyncio
async def test_enrich_meeting_multi_includes_candidates():
    from bot.handlers.text import _enrich_meeting
    from shared.clients import ClientLookupResult

    clients = [
        {"_row": 7, "Imię i nazwisko": "Mariusz Krzywinski", "Miasto": "Marki", "Status": "Oferta wysłana"},
        {"_row": 11, "Imię i nazwisko": "Mariusz Krzywinski", "Miasto": "Wołomin", "Status": "Nowy lead"},
    ]
    result = ClientLookupResult(status="multi", clients=clients, normalized_query="mariusz krzywinski")

    with patch(
        "bot.handlers.text.lookup_client",
        new=AsyncMock(return_value=result),
    ):
        enriched = await _enrich_meeting("u1", "Mariusz Krzywinski", "")

    assert enriched["ambiguous_client"] is True
    candidates = enriched["ambiguous_candidates"]
    assert len(candidates) == 2
    rows = {c["row"] for c in candidates}
    assert rows == {7, 11}
    # current_status propagated so disambiguation payload carries it forward
    by_row = {c["row"]: c for c in candidates}
    assert by_row[11]["current_status"] == "Nowy lead"
    assert by_row[7]["city"] == "Marki"
