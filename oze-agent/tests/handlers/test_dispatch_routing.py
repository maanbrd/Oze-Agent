"""Pure-routing tests for bot/handlers/text.py dispatch primitives."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from bot.handlers.text import (
    _BANNER_INTENTS,
    _HANDLERS,
    _infer_meeting_event_type,
    _intent_result_to_legacy_dict,
    _is_client_scoped_action_reply,
    _message_with_add_client_context,
    _message_with_r7_client_context,
    _normalize_parsed_event_type,
    _resolve_meeting_event_type,
    handle_banner,
    handle_general,
)
from shared.intent.intents import IntentResult, IntentType, ScopeTier


def test_handlers_table_covers_every_intent_type():
    assert set(_HANDLERS.keys()) == set(IntentType)


def test_every_banner_intent_routes_to_handle_banner():
    assert _BANNER_INTENTS == {
        IntentType.POST_MVP_ROADMAP,
        IntentType.VISION_ONLY,
        IntentType.UNPLANNED,
        IntentType.MULTI_MEETING,
    }
    for intent in _BANNER_INTENTS:
        assert _HANDLERS[intent] is handle_banner


def test_general_question_routes_to_handle_general():
    assert _HANDLERS[IntentType.GENERAL_QUESTION] is handle_general


def test_change_status_remaps_client_name_to_name():
    result = IntentResult(
        intent=IntentType.CHANGE_STATUS,
        scope_tier=ScopeTier.MVP,
        entities={"client_name": "Kowalski", "status": "Podpisane"},
        confidence=1.0,
    )
    legacy = _intent_result_to_legacy_dict(result, "Kowalski podpisał")
    assert legacy["intent"] == "change_status"
    assert legacy["entities"] == {"name": "Kowalski", "status": "Podpisane"}
    assert "client_name" not in legacy["entities"]
    assert legacy["confidence"] == 1.0


def test_add_client_entities_pass_through_unchanged():
    result = IntentResult(
        intent=IntentType.ADD_CLIENT,
        scope_tier=ScopeTier.MVP,
        entities={"name": "Jan Kowalski", "city": "Warszawa"},
        confidence=1.0,
    )
    legacy = _intent_result_to_legacy_dict(result, "...")
    assert legacy["entities"] == {"name": "Jan Kowalski", "city": "Warszawa"}


def test_add_meeting_entities_pass_through_unchanged():
    result = IntentResult(
        intent=IntentType.ADD_MEETING,
        scope_tier=ScopeTier.MVP,
        entities={"client_name": "Nowak", "date_iso": "2026-04-20", "event_type": "in_person"},
        confidence=1.0,
    )
    legacy = _intent_result_to_legacy_dict(result, "...")
    assert legacy["entities"] == {
        "client_name": "Nowak",
        "date_iso": "2026-04-20",
        "event_type": "in_person",
    }
    assert "status_update" not in legacy          # no compound → no top-level hoist


def test_add_meeting_hoists_compound_status_update_to_top_level():
    """Slice 5.4.3: classifier puts status_update inside entities; adapter
    promotes it to top-level so handle_add_meeting's
    intent_data.get("status_update") picks it up without reaching into
    entities."""
    result = IntentResult(
        intent=IntentType.ADD_MEETING,
        scope_tier=ScopeTier.MVP,
        entities={
            "client_name": "Wojtek",
            "date_iso": "2026-04-23",
            "event_type": "in_person",
            "status_update": {"field": "Status", "new_value": "Podpisane"},
        },
        confidence=1.0,
    )
    legacy = _intent_result_to_legacy_dict(result, "Wojtek podpisał, spotkanie jutro o 14")
    assert legacy["status_update"] == {"field": "Status", "new_value": "Podpisane"}
    # status_update stays in entities as well (no destructive pop) so the raw
    # tool-call shape is preserved for debugging / future plumbing.
    assert legacy["entities"]["status_update"] == {"field": "Status", "new_value": "Podpisane"}


def test_add_meeting_no_status_update_leaves_legacy_top_level_unchanged():
    """Regression: non-compound add_meeting stays as before — no stray
    status_update key leaks onto intent_data top-level."""
    result = IntentResult(
        intent=IntentType.ADD_MEETING,
        scope_tier=ScopeTier.MVP,
        entities={"client_name": "Nowak", "date_iso": "2026-04-20", "event_type": "in_person"},
        confidence=1.0,
    )
    legacy = _intent_result_to_legacy_dict(result, "spotkanie z Nowakiem 20.04")
    assert "status_update" not in legacy


def test_change_status_does_not_hoist_status_update():
    """Only ADD_MEETING intent triggers the hoist — CHANGE_STATUS carries its
    own status field, no compound propagation."""
    result = IntentResult(
        intent=IntentType.CHANGE_STATUS,
        scope_tier=ScopeTier.MVP,
        entities={"client_name": "Kowalski", "status": "Podpisane"},
        confidence=1.0,
    )
    legacy = _intent_result_to_legacy_dict(result, "Kowalski podpisał")
    assert "status_update" not in legacy


def test_show_client_entities_pass_through_unchanged():
    result = IntentResult(
        intent=IntentType.SHOW_CLIENT,
        scope_tier=ScopeTier.MVP,
        entities={"name": "Nowak", "phone": "123"},
        confidence=1.0,
    )
    legacy = _intent_result_to_legacy_dict(result, "...")
    assert legacy["entities"] == {"name": "Nowak", "phone": "123"}


def test_legacy_dict_carries_feature_key_and_reason():
    result = IntentResult(
        intent=IntentType.POST_MVP_ROADMAP,
        scope_tier=ScopeTier.POST_MVP_ROADMAP,
        entities={},
        confidence=1.0,
        feature_key="edit_client",
        reason="user wants editing",
    )
    legacy = _intent_result_to_legacy_dict(result, "...")
    assert legacy["feature_key"] == "edit_client"
    assert legacy["reason"] == "user wants editing"


def test_general_question_fallback_resolves_to_handle_general():
    result = IntentResult(
        intent=IntentType.GENERAL_QUESTION,
        scope_tier=ScopeTier.MVP,
        confidence=0.0,
    )
    handler = _HANDLERS.get(result.intent)
    assert handler is handle_general
    legacy = _intent_result_to_legacy_dict(result, "?")
    assert legacy["intent"] == "general_question"
    assert legacy["confidence"] == 0.0


@pytest.mark.asyncio
async def test_handle_general_never_sends_empty_message():
    update = MagicMock()
    update.effective_user.id = 12345
    update.effective_message.reply_text = AsyncMock()
    context = MagicMock()

    with patch("bot.handlers.text.get_conversation_history", return_value=[]), \
         patch("bot.handlers.text.generate_bot_response", new=AsyncMock(return_value={"text": ""})), \
         patch("bot.handlers.text.save_conversation_message"), \
         patch("bot.handlers.text.increment_interaction", new=AsyncMock()):
        await handle_general(update, context, {"id": "uid"}, {}, "x")

    update.effective_message.reply_text.assert_awaited_once_with("Co chcesz zrobić?")


def test_r7_context_injected_when_reply_has_no_client_name():
    text = _message_with_r7_client_context(
        "Spotkanie 18 kwietnia o 14",
        {"client_name": "Jan Kowalski", "city": "Warszawa"},
    )
    assert text == "Spotkanie 18 kwietnia o 14 z Jan Kowalski Warszawa"


def test_r7_context_not_injected_when_reply_mentions_client_name():
    text = _message_with_r7_client_context(
        "Spotkanie z Kowalskim 18 kwietnia o 14",
        {"client_name": "Jan Kowalski", "city": "Warszawa"},
    )
    assert text == "Spotkanie z Kowalskim 18 kwietnia o 14"


def test_r7_context_not_injected_when_reply_has_explicit_with_phrase():
    text = _message_with_r7_client_context(
        "Spotkanie z Nowakiem 18 kwietnia o 14",
        {"client_name": "Jan Kowalski", "city": "Warszawa"},
    )
    assert text == "Spotkanie z Nowakiem 18 kwietnia o 14"


def test_client_data_replies_do_not_route_as_actions():
    assert not _is_client_scoped_action_reply("telefon 123456789")
    assert not _is_client_scoped_action_reply("tel 123 456 789")
    assert not _is_client_scoped_action_reply("adres Krótka 5")
    assert not _is_client_scoped_action_reply("email test@example.com")
    assert not _is_client_scoped_action_reply("produkt PV")


def test_client_action_replies_route_with_pending_context():
    assert _is_client_scoped_action_reply("Spotkanie")
    assert _is_client_scoped_action_reply("spotkanie w piątek o 14")
    assert _is_client_scoped_action_reply("zadzwonić w środę o 14")
    assert _is_client_scoped_action_reply("przygotuj ofertę na środę")
    assert _is_client_scoped_action_reply("w piątek o 14")


def test_infer_meeting_event_type_uses_d4_priority_order():
    assert _infer_meeting_event_type("Zadzwoń do Tomasza Nowickiego w sobotę o 12") == "phone_call"
    assert _infer_meeting_event_type("Wyślij ofertę Janowi Kowalskiemu dzisiaj o godzinie 23") == "offer_email"
    # Slice 5.4.2: "przypomnij" / "follow-up" now fold into phone_call (user
    # calls to remind); doc_followup event_type removed from MVP parser.
    assert _infer_meeting_event_type("Przypomnij Wojtkowi Testowemu o dokumentach jutro o 15") == "phone_call"
    assert _infer_meeting_event_type("Follow-up z Janem jutro o 10") == "phone_call"
    assert _infer_meeting_event_type("Spotkanie telefoniczne z Janem jutro o 10") == "phone_call"
    assert _infer_meeting_event_type("Spotkanie z Janem jutro o 10") == "in_person"


# ── Slice 5.4.2 — runtime normalizer for dropped doc_followup ────────────────


def test_normalize_parsed_event_type_reroutes_doc_followup_to_phone_call():
    """LLM drift guard: parser output doc_followup is rerouted to phone_call
    even if prompt + schema changes fail to fully suppress it."""
    assert _normalize_parsed_event_type("doc_followup") == "phone_call"


def test_normalize_parsed_event_type_passes_valid_values_through():
    for value in ("in_person", "phone_call", "offer_email"):
        assert _normalize_parsed_event_type(value) == value


def test_normalize_parsed_event_type_preserves_none():
    assert _normalize_parsed_event_type(None) is None


def test_resolve_meeting_event_type_applies_normalizer_on_inference():
    """_infer_meeting_event_type no longer returns doc_followup after 5.4.2,
    but if a stale caller passed an inferred value through, normalizer catches."""
    # Neutral message (no follow-up/dokument markers) — the guard on the
    # inferred value is what renormalizes, not re-inference from message_text.
    result = _resolve_meeting_event_type("spotkanie z klientem jutro", "doc_followup")
    assert result == "in_person"  # message infers in_person first; doc_followup fallback never reached


def test_resolve_meeting_event_type_applies_normalizer_on_fallback():
    """When message infers nothing, fallbacks go through normalizer."""
    # Short message with no event markers at all.
    result = _resolve_meeting_event_type("ok", "doc_followup")
    assert result == "phone_call"


def test_add_client_context_injected_for_action_reply():
    text = _message_with_add_client_context(
        "spotkanie w piątek o 14",
        {"Imię i nazwisko": "Anna Testowa", "Miasto": "Zatory"},
    )
    assert text == "spotkanie w piątek o 14 z Anna Testowa Zatory"
