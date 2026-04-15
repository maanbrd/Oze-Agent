"""Pure-routing tests for bot/handlers/text.py dispatch primitives."""

from bot.handlers.text import (
    _BANNER_INTENTS,
    _HANDLERS,
    _intent_result_to_legacy_dict,
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
