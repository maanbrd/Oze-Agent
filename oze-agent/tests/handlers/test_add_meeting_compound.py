"""Slice 5.4.3 — compound status_update normalizer + handler branching.

Covers _normalize_compound_status_update pure-logic (5 cases) and the
ambiguous-safe 3-branch in handle_add_meeting (unique / ambiguous /
not_found).
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.handlers.text import (
    _normalize_compound_status_update,
    handle_add_meeting,
)
from shared.clients import ClientLookupResult
from shared.pending import PendingFlowType


# ── Pure-logic: _normalize_compound_status_update ──────────────────────────


def _enriched_unique(client_row: int = 11) -> dict:
    return {
        "client_row": client_row,
        "current_status": "Oferta wysłana",
        "full_name": "Wojtek Nowak",
        "client_city": "Marki",
    }


def test_normalize_fills_row_old_value_and_identity_from_enriched():
    raw = {"field": "Status", "new_value": "Podpisane"}
    enriched = _enriched_unique(client_row=11)
    filled = _normalize_compound_status_update(raw, enriched)
    assert filled == {
        "field": "Status",
        "new_value": "Podpisane",
        "row": 11,
        "old_value": "Oferta wysłana",
        "client_name": "Wojtek Nowak",
        "city": "Marki",
    }


def test_normalize_does_not_overwrite_existing_fields():
    raw = {
        "field": "Status",
        "new_value": "Podpisane",
        "row": 42,
        "old_value": "Custom previous",
        "client_name": "Custom name",
        "city": "Custom city",
    }
    filled = _normalize_compound_status_update(raw, _enriched_unique(client_row=11))
    assert filled["row"] == 42
    assert filled["old_value"] == "Custom previous"
    assert filled["client_name"] == "Custom name"
    assert filled["city"] == "Custom city"


def test_normalize_returns_none_when_input_is_none():
    assert _normalize_compound_status_update(None, _enriched_unique()) is None


def test_normalize_drops_when_new_value_missing():
    """Malformed classifier output (no new_value) → drop, don't carry half-baked."""
    raw = {"field": "Status"}
    assert _normalize_compound_status_update(raw, _enriched_unique()) is None


def test_normalize_drops_when_no_resolvable_row():
    """not_found scenario: no row in status_update, no client_row in enriched.
    Pipeline can't write status without a row, so drop rather than promise
    a change in confirm card we can't deliver."""
    raw = {"field": "Status", "new_value": "Podpisane"}
    enriched = {"client_row": None, "current_status": "", "full_name": "Nowy Klient", "client_city": ""}
    assert _normalize_compound_status_update(raw, enriched) is None


def test_normalize_uses_status_update_row_when_enriched_has_none():
    """Edge: status_update carries a row but enriched has none → still usable."""
    raw = {"field": "Status", "new_value": "Podpisane", "row": 77}
    enriched = {"client_row": None, "current_status": "", "full_name": "X", "client_city": ""}
    filled = _normalize_compound_status_update(raw, enriched)
    assert filled["row"] == 77
    assert filled["new_value"] == "Podpisane"


# ── handle_add_meeting 3-branch status_update resolution ────────────────────


def _update(telegram_id: int = 123) -> MagicMock:
    upd = MagicMock()
    upd.effective_user.id = telegram_id
    upd.effective_message.reply_text = AsyncMock()
    upd.effective_message.reply_markdown_v2 = AsyncMock()
    return upd


def _extract_meeting(event_type: str = "in_person") -> dict:
    return {
        "meetings": [
            {
                "client_name": "Wojtek",
                "date": "2027-04-23",
                "time": "14:00",
                "location": "",
                "event_type": event_type,
            }
        ],
        "tokens_in": 0,
        "tokens_out": 0,
        "cost_usd": 0,
    }


@pytest.mark.asyncio
async def test_compound_unique_path_normalizes_and_saves_add_meeting_pending():
    """Branch 2: unique client + compound status_update → normalizer fills
    row/old_value/client_name/city, pending saved as ADD_MEETING (not
    disambiguation)."""
    client = {
        "_row": 11,
        "Imię i nazwisko": "Wojtek",
        "Miasto": "Marki",
        "Status": "Oferta wysłana",
    }
    intent_data = {
        "entities": {},
        "status_update": {"field": "Status", "new_value": "Podpisane"},
    }
    upd = _update()
    with patch(
        "bot.handlers.text.extract_meeting_data",
        new=AsyncMock(return_value=_extract_meeting("in_person")),
    ), patch(
        "bot.handlers.text.lookup_client",
        new=AsyncMock(
            return_value=ClientLookupResult(status="unique", clients=[client], normalized_query="wojtek"),
        ),
    ), patch(
        "bot.handlers.text.check_conflicts",
        new=AsyncMock(return_value=[]),
    ), patch("bot.handlers.text.save_pending") as mock_save:
        await handle_add_meeting(
            upd,
            MagicMock(),
            {"id": "u1", "default_meeting_duration": 60},
            intent_data,
            "Wojtek podpisał, spotkanie jutro o 14",
        )

    saved = mock_save.call_args.args[0]
    assert saved.flow_type is PendingFlowType.ADD_MEETING
    fd = saved.flow_data
    # Compound status_update normalized with fields from enriched.
    assert fd["status_update"]["new_value"] == "Podpisane"
    assert fd["status_update"]["row"] == 11
    assert fd["status_update"]["old_value"] == "Oferta wysłana"
    assert fd["status_update"]["client_name"] == "Wojtek"


@pytest.mark.asyncio
async def test_compound_ambiguous_preserves_raw_status_update_in_disambiguation_payload():
    """Branch 1: ambiguous client → raw compound survives into
    ADD_MEETING_DISAMBIGUATION. Normalizer MUST NOT fire yet — without a
    selected row the guard would drop the compound."""
    candidates = [
        {"_row": 7, "Imię i nazwisko": "Wojtek", "Miasto": "Marki", "Status": "Nowy lead"},
        {"_row": 12, "Imię i nazwisko": "Wojtek", "Miasto": "Wołomin", "Status": "Oferta wysłana"},
    ]
    intent_data = {
        "entities": {},
        "status_update": {"field": "Status", "new_value": "Podpisane"},
    }
    upd = _update()
    with patch(
        "bot.handlers.text.extract_meeting_data",
        new=AsyncMock(return_value=_extract_meeting("in_person")),
    ), patch(
        "bot.handlers.text.lookup_client",
        new=AsyncMock(
            return_value=ClientLookupResult(status="multi", clients=candidates, normalized_query="wojtek"),
        ),
    ), patch(
        "bot.handlers.text.check_conflicts",
        new=AsyncMock(return_value=[]),
    ), patch("bot.handlers.text.save_pending") as mock_save:
        await handle_add_meeting(
            upd,
            MagicMock(),
            {"id": "u1", "default_meeting_duration": 60},
            intent_data,
            "Wojtek podpisał, spotkanie jutro o 14",
        )

    saved = mock_save.call_args.args[0]
    assert saved.flow_type is PendingFlowType.ADD_MEETING_DISAMBIGUATION
    # RAW status_update preserved — no row/old_value/client_name/city added.
    assert saved.flow_data["status_update"] == {"field": "Status", "new_value": "Podpisane"}


@pytest.mark.asyncio
async def test_compound_not_found_drops_status_update():
    """Branch 2 (not_found sub-case): compound present but client does not
    exist in Sheets → normalizer guard drops status_update (no row). Pending
    still saved (Calendar event will be created), but no status change
    promised on the confirm card."""
    intent_data = {
        "entities": {},
        "status_update": {"field": "Status", "new_value": "Podpisane"},
    }
    upd = _update()
    with patch(
        "bot.handlers.text.extract_meeting_data",
        new=AsyncMock(return_value=_extract_meeting("in_person")),
    ), patch(
        "bot.handlers.text.lookup_client",
        new=AsyncMock(
            return_value=ClientLookupResult(status="not_found", clients=[], normalized_query="wojtek"),
        ),
    ), patch(
        "bot.handlers.text.check_conflicts",
        new=AsyncMock(return_value=[]),
    ), patch("bot.handlers.text.save_pending") as mock_save:
        await handle_add_meeting(
            upd,
            MagicMock(),
            {"id": "u1", "default_meeting_duration": 60},
            intent_data,
            "Wojtek podpisał, spotkanie jutro o 14",
        )

    saved = mock_save.call_args.args[0]
    assert saved.flow_type is PendingFlowType.ADD_MEETING
    assert saved.flow_data.get("status_update") is None


@pytest.mark.asyncio
async def test_no_compound_unique_path_still_applies_auto_upgrade():
    """Branch 3 regression: when intent_data has no status_update, unique
    in_person + Nowy lead still auto-upgrades to Spotkanie umówione per 5.4
    contract."""
    client = {
        "_row": 11,
        "Imię i nazwisko": "Wojtek",
        "Miasto": "Marki",
        "Status": "Nowy lead",
    }
    intent_data = {"entities": {}}          # no status_update
    upd = _update()
    with patch(
        "bot.handlers.text.extract_meeting_data",
        new=AsyncMock(return_value=_extract_meeting("in_person")),
    ), patch(
        "bot.handlers.text.lookup_client",
        new=AsyncMock(
            return_value=ClientLookupResult(status="unique", clients=[client], normalized_query="wojtek"),
        ),
    ), patch(
        "bot.handlers.text.check_conflicts",
        new=AsyncMock(return_value=[]),
    ), patch("bot.handlers.text.save_pending") as mock_save:
        await handle_add_meeting(
            upd,
            MagicMock(),
            {"id": "u1", "default_meeting_duration": 60},
            intent_data,
            "spotkanie z Wojtkiem jutro o 14",
        )

    saved = mock_save.call_args.args[0]
    fd = saved.flow_data
    assert fd["status_update"]["new_value"] == "Spotkanie umówione"
    assert fd["status_update"]["old_value"] == "Nowy lead"
