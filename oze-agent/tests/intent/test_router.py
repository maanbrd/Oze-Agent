"""Unit tests for shared/intent/router.py — Anthropic + DB calls mocked."""

import logging
from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest


def _tool_result(tool_name: str, tool_input: dict, model: str = "claude-haiku-4-5"):
    return {
        "tool_name": tool_name,
        "tool_input": tool_input,
        "text": None,
        "tokens_in": 10,
        "tokens_out": 20,
        "cost_usd": 0.0,
        "model": model,
    }


def _text_result(text: str = "hi", model: str = "claude-haiku-4-5"):
    return {
        "tool_name": None,
        "tool_input": {},
        "text": text,
        "tokens_in": 10,
        "tokens_out": 20,
        "cost_usd": 0.0,
        "model": model,
    }


def _api_error_result(model: str = "claude-haiku-4-5"):
    # Shape that shared.claude_ai.call_claude_with_tools returns on exception.
    return {
        "tool_name": None,
        "tool_input": {},
        "text": "",
        "tokens_in": 0,
        "tokens_out": 0,
        "cost_usd": 0.0,
        "model": model,
    }


def _patches(claude_return, history=None):
    return (
        patch(
            "shared.intent.router.get_conversation_history",
            return_value=history or [],
        ),
        patch(
            "shared.intent.router.call_claude_with_tools",
            new=AsyncMock(return_value=claude_return),
        ),
    )


@pytest.mark.asyncio
async def test_add_client_tool_maps_to_mvp_intent():
    p1, p2 = _patches(
        _tool_result(
            "record_add_client",
            {"name": "Jan Kowalski", "city": "Warszawa"},
        )
    )
    with p1, p2:
        from shared.intent.intents import IntentType, ScopeTier
        from shared.intent.router import classify
        result = await classify("dopisz Jan Kowalski z Warszawy", 123)
    assert result.intent == IntentType.ADD_CLIENT
    assert result.scope_tier == ScopeTier.MVP
    assert result.entities == {"name": "Jan Kowalski", "city": "Warszawa"}
    assert result.confidence == 1.0
    assert result.feature_key is None


@pytest.mark.asyncio
async def test_show_client_tool():
    p1, p2 = _patches(
        _tool_result("record_show_client", {"name": "Nowak"})
    )
    with p1, p2:
        from shared.intent.intents import IntentType, ScopeTier
        from shared.intent.router import classify
        result = await classify("co mam o Nowaku", 1)
    assert result.intent == IntentType.SHOW_CLIENT
    assert result.scope_tier == ScopeTier.MVP
    assert result.entities == {"name": "Nowak"}


@pytest.mark.asyncio
async def test_add_note_tool():
    p1, p2 = _patches(
        _tool_result(
            "record_add_note",
            {"client_name": "Kowalski", "note": "zainteresowany pompą"},
        )
    )
    with p1, p2:
        from shared.intent.intents import IntentType
        from shared.intent.router import classify
        result = await classify("Kowalski chce pompę ciepła", 1)
    assert result.intent == IntentType.ADD_NOTE
    assert result.entities["note"] == "zainteresowany pompą"


@pytest.mark.asyncio
async def test_change_status_tool():
    p1, p2 = _patches(
        _tool_result(
            "record_change_status",
            {"client_name": "Kowalski", "status": "Podpisane"},
        )
    )
    with p1, p2:
        from shared.intent.intents import IntentType, ScopeTier
        from shared.intent.router import classify
        result = await classify("Kowalski podpisał", 1)
    assert result.intent == IntentType.CHANGE_STATUS
    assert result.scope_tier == ScopeTier.MVP
    assert result.entities["status"] == "Podpisane"


@pytest.mark.asyncio
async def test_add_meeting_tool():
    p1, p2 = _patches(
        _tool_result(
            "record_add_meeting",
            {
                "client_name": "Nowak",
                "date_iso": "2026-04-20",
                "event_type": "in_person",
                "time": "10:00",
            },
        )
    )
    with p1, p2:
        from shared.intent.intents import IntentType
        from shared.intent.router import classify
        result = await classify("spotkanie z Nowakiem 20.04", 1)
    assert result.intent == IntentType.ADD_MEETING
    assert result.entities["event_type"] == "in_person"
    assert result.entities["date_iso"] == "2026-04-20"


@pytest.mark.asyncio
async def test_add_meeting_tool_compound_status_update_lives_in_entities():
    """Slice 5.4.3: when classifier emits record_add_meeting with the new
    compound status_update field, the router keeps it inside entities.
    Hoisting to top-level intent_data happens in _intent_result_to_legacy_dict
    (handler-side), not here."""
    p1, p2 = _patches(
        _tool_result(
            "record_add_meeting",
            {
                "client_name": "Wojtek",
                "date_iso": "2026-04-23",
                "time": "14:00",
                "event_type": "in_person",
                "status_update": {"field": "Status", "new_value": "Podpisane"},
            },
        )
    )
    with p1, p2:
        from shared.intent.intents import IntentType
        from shared.intent.router import classify
        result = await classify("Wojtek podpisał, spotkanie jutro o 14", 1)
    assert result.intent == IntentType.ADD_MEETING
    assert result.entities["status_update"] == {
        "field": "Status",
        "new_value": "Podpisane",
    }


@pytest.mark.asyncio
async def test_show_day_plan_tool():
    p1, p2 = _patches(
        _tool_result("record_show_day_plan", {"date_iso": "2026-04-16"})
    )
    with p1, p2:
        from shared.intent.intents import IntentType
        from shared.intent.router import classify
        result = await classify("co mam jutro", 1)
    assert result.intent == IntentType.SHOW_DAY_PLAN
    assert result.entities == {"date_iso": "2026-04-16"}


@pytest.mark.asyncio
async def test_general_question_tool_lifts_reason():
    p1, p2 = _patches(
        _tool_result(
            "record_general_question",
            {"reason": "small talk"},
        )
    )
    with p1, p2:
        from shared.intent.intents import IntentType, ScopeTier
        from shared.intent.router import classify
        result = await classify("jak się masz", 1)
    assert result.intent == IntentType.GENERAL_QUESTION
    assert result.scope_tier == ScopeTier.MVP
    assert result.reason == "small talk"
    assert result.entities == {}


@pytest.mark.asyncio
async def test_out_of_scope_post_mvp_dispatches_by_category():
    p1, p2 = _patches(
        _tool_result(
            "record_out_of_scope",
            {
                "category": "post_mvp_roadmap",
                "feature_key": "edit_client",
                "details": "chce edytować dane klienta",
            },
        )
    )
    with p1, p2:
        from shared.intent.intents import IntentType, ScopeTier
        from shared.intent.router import classify
        result = await classify("chcę edytować klienta", 1)
    assert result.intent == IntentType.POST_MVP_ROADMAP
    assert result.scope_tier == ScopeTier.POST_MVP_ROADMAP
    assert result.feature_key == "edit_client"
    assert result.reason == "chce edytować dane klienta"
    assert result.entities == {}


@pytest.mark.asyncio
async def test_out_of_scope_vision_only_category():
    p1, p2 = _patches(
        _tool_result(
            "record_out_of_scope",
            {"category": "vision_only", "feature_key": "habit_learning"},
        )
    )
    with p1, p2:
        from shared.intent.intents import IntentType, ScopeTier
        from shared.intent.router import classify
        result = await classify("czy uczysz się moich nawyków", 1)
    assert result.intent == IntentType.VISION_ONLY
    assert result.scope_tier == ScopeTier.VISION_ONLY
    assert result.feature_key == "habit_learning"


@pytest.mark.asyncio
async def test_out_of_scope_missing_feature_key_falls_back():
    p1, p2 = _patches(
        _tool_result(
            "record_out_of_scope",
            {"category": "post_mvp_roadmap"},
        )
    )
    with p1, p2:
        from shared.intent.intents import IntentType
        from shared.intent.router import classify
        result = await classify("...", 1)
    assert result.intent == IntentType.GENERAL_QUESTION
    assert result.confidence == 0.0


@pytest.mark.asyncio
async def test_out_of_scope_category_feature_key_mismatch_falls_back():
    p1, p2 = _patches(
        _tool_result(
            "record_out_of_scope",
            {
                "category": "post_mvp_roadmap",
                "feature_key": "reschedule_meeting",
            },
        )
    )
    with p1, p2:
        from shared.intent.intents import IntentType
        from shared.intent.router import classify
        result = await classify("przełóż spotkanie z Kowalskim", 1)
    assert result.intent == IntentType.GENERAL_QUESTION
    assert result.confidence == 0.0


@pytest.mark.asyncio
async def test_multi_meeting_rejection_maps_to_rejected_scope():
    p1, p2 = _patches(
        _tool_result("record_multi_meeting_rejection", {"meeting_count": 3})
    )
    with p1, p2:
        from shared.intent.intents import IntentType, ScopeTier
        from shared.intent.router import classify
        result = await classify("umów mi 3 spotkania", 1)
    assert result.intent == IntentType.MULTI_MEETING
    assert result.scope_tier == ScopeTier.REJECTED
    assert result.entities == {"meeting_count": 3}


@pytest.mark.asyncio
async def test_text_response_falls_back_to_general_question():
    p1, p2 = _patches(_text_result("Cześć!"))
    with p1, p2:
        from shared.intent.intents import IntentType, ScopeTier
        from shared.intent.router import classify
        result = await classify("cześć", 1)
    assert result.intent == IntentType.GENERAL_QUESTION
    assert result.scope_tier == ScopeTier.MVP
    assert result.confidence == 0.0


@pytest.mark.asyncio
async def test_api_error_falls_back_to_general_question():
    p1, p2 = _patches(_api_error_result())
    with p1, p2:
        from shared.intent.intents import IntentType
        from shared.intent.router import classify
        result = await classify("cokolwiek", 1)
    assert result.intent == IntentType.GENERAL_QUESTION
    assert result.confidence == 0.0


@pytest.mark.asyncio
async def test_unknown_tool_name_falls_back():
    p1, p2 = _patches(_tool_result("record_made_up", {"foo": "bar"}))
    with p1, p2:
        from shared.intent.intents import IntentType
        from shared.intent.router import classify
        result = await classify("...", 1)
    assert result.intent == IntentType.GENERAL_QUESTION
    assert result.confidence == 0.0


@pytest.mark.asyncio
async def test_classify_uses_30min_history_window_and_all_tools():
    captured = {}

    async def _capture(**kwargs):
        captured.update(kwargs)
        return _text_result()

    history_mock = [
        {"role": "user", "content": "poprzednia wiadomość", "message_type": "text", "created_at": "x"},
    ]
    with patch(
        "shared.intent.router.get_conversation_history",
        return_value=history_mock,
    ) as hist_mock, patch(
        "shared.intent.router.call_claude_with_tools",
        new=_capture,
    ):
        from shared.intent.router import classify
        from shared.intent.schemas import ALL_TOOLS
        await classify("cześć", 42)

    hist_mock.assert_called_once()
    args, kwargs = hist_mock.call_args
    assert (args and args[0] == 42) or kwargs.get("telegram_id") == 42
    assert kwargs.get("limit") == 10
    assert kwargs.get("since") == timedelta(minutes=30)

    assert captured["tools"] is ALL_TOOLS
    assert captured["model_type"] == "simple"
    assert captured["force_tool"] is True
    sys_prompt = captured["system_prompt"]
    assert "[Nowy]" in sys_prompt
    assert "[Aktualizuj]" in sys_prompt
    assert "R4" not in sys_prompt
    assert "<conversation_history>" in sys_prompt
    assert "poprzednia wiadomość" in sys_prompt


# Slice 5.1d.4 — meeting+client compound preflight. Production bug 27.04.2026:
# voice "Dodaj spotkanie z X jutro 18, telefon 722..., Marki Zielona 28" got
# classified as record_add_client by Haiku because of the rich client data.
# The preflight forces tool=record_add_meeting at the API level whenever the
# message contains both a meeting keyword and a temporal marker.

async def _capture_force_tool(message: str, mock_tool_name: str, mock_input: dict | None = None):
    captured = {}

    async def _capture(**kwargs):
        captured.update(kwargs)
        return _tool_result(mock_tool_name, mock_input or {})

    with patch(
        "shared.intent.router.get_conversation_history",
        return_value=[],
    ), patch(
        "shared.intent.router.call_claude_with_tools",
        new=_capture,
    ):
        from shared.intent.router import classify
        result = await classify(message, 1)
    return result, captured


@pytest.mark.asyncio
async def test_meeting_preflight_forces_add_meeting_for_production_voice_transcription():
    """Exact transcription from prod bug (Maan 27.04.2026 09:14): voice with
    meeting + rich client data must force record_add_meeting, not record_add_client."""
    message = (
        "Dodaj spotkanie z Jurkiem Kluziakiem na jutro na godzinę osiemnastą, "
        "spotkanie na fotowoltaikę i pompę ciepła, numer telefonu 722-236-366, "
        "jest mieszka w Markach na ulicy Zielonej 28."
    )
    result, captured = await _capture_force_tool(
        message,
        "record_add_meeting",
        {
            "client_name": "Jurek Kluziak",
            "date_iso": "2026-04-28",
            "time": "18:00",
            "event_type": "in_person",
        },
    )
    assert captured["force_tool"] == "record_add_meeting"

    from shared.intent.intents import IntentType
    assert result.intent == IntentType.ADD_MEETING


@pytest.mark.asyncio
async def test_add_client_preflight_forces_explicit_add_client_with_history():
    result, captured = await _capture_force_tool(
        "dodaj klienta E2E-Beta-Tester, E2E-Beta-City, 600100200, PV",
        "record_add_client",
        {"name": "E2E-Beta-Tester", "city": "E2E-Beta-City"},
    )
    assert captured["force_tool"] == "record_add_client"

    from shared.intent.intents import IntentType
    assert result.intent == IntentType.ADD_CLIENT


@pytest.mark.asyncio
async def test_note_shorthand_preflight_forces_add_note():
    result, captured = await _capture_force_tool(
        "E2E-Beta-Tester: test note dla R04 — historia",
        "record_add_note",
        {"client_name": "E2E-Beta-Tester", "note": "test note dla R04 — historia"},
    )
    assert captured["force_tool"] == "record_add_note"

    from shared.intent.intents import IntentType
    assert result.intent == IntentType.ADD_NOTE


@pytest.mark.asyncio
async def test_classify_log_redacts_message_content(caplog):
    message = "Dodaj spotkanie z Jurkiem Kluziakiem jutro o 18, telefon 722236366"
    caplog.set_level(logging.INFO, logger="shared.intent.router")

    await _capture_force_tool(
        message,
        "record_add_meeting",
        {"client_name": "Jurek Kluziak", "time": "18:00"},
    )

    assert "message_len=" in caplog.text
    assert "Jurek" not in caplog.text
    assert "722236366" not in caplog.text
    assert "message_prefix" not in caplog.text


@pytest.mark.asyncio
async def test_meeting_preflight_forces_add_meeting_for_simple_meeting():
    result, captured = await _capture_force_tool(
        "spotkanie z Janem jutro 14:00",
        "record_add_meeting",
        {
            "client_name": "Jan",
            "date_iso": "2026-04-28",
            "time": "14:00",
            "event_type": "in_person",
        },
    )
    assert captured["force_tool"] == "record_add_meeting"

    from shared.intent.intents import IntentType
    assert result.intent == IntentType.ADD_MEETING


@pytest.mark.asyncio
async def test_meeting_preflight_forces_add_meeting_for_phone_call():
    result, captured = await _capture_force_tool(
        "telefon do Marka pojutrze o 10",
        "record_add_meeting",
        {
            "client_name": "Marek",
            "date_iso": "2026-04-29",
            "time": "10:00",
            "event_type": "phone_call",
        },
    )
    assert captured["force_tool"] == "record_add_meeting"

    from shared.intent.intents import IntentType
    assert result.intent == IntentType.ADD_MEETING


@pytest.mark.asyncio
async def test_meeting_preflight_does_not_fire_for_pure_add_client():
    """No temporal marker → preflight off → classifier picks normally."""
    result, captured = await _capture_force_tool(
        "Dodaj Jana Kowalskiego z Warszawy 600100200",
        "record_add_client",
        {"name": "Jan Kowalski", "city": "Warszawa", "phone": "600100200"},
    )
    assert captured["force_tool"] is True

    from shared.intent.intents import IntentType
    assert result.intent == IntentType.ADD_CLIENT


@pytest.mark.asyncio
async def test_meeting_preflight_does_not_treat_contact_phone_as_phone_call():
    """A contact field named 'telefon' plus a future follow-up note must not
    force add_meeting unless the text asks for a call/meeting action."""
    result, captured = await _capture_force_tool(
        "Dodaj klienta Jan Kowalski, telefon 600100200, jutro podeślę dane",
        "record_add_client",
        {"name": "Jan Kowalski", "phone": "600100200"},
    )
    assert captured["force_tool"] is True

    from shared.intent.intents import IntentType
    assert result.intent == IntentType.ADD_CLIENT


@pytest.mark.asyncio
async def test_meeting_preflight_does_not_fire_for_status_change_only():
    """Meeting keyword absent, no temporal → preflight off."""
    result, captured = await _capture_force_tool(
        "Wojtek podpisał umowę",
        "record_change_status",
        {"client_name": "Wojtek", "status": "Podpisane"},
    )
    assert captured["force_tool"] is True

    from shared.intent.intents import IntentType
    assert result.intent == IntentType.CHANGE_STATUS


@pytest.mark.asyncio
async def test_meeting_preflight_does_not_fire_for_show_day_plan():
    """Temporal 'jutro' but no meeting keyword → preflight off."""
    result, captured = await _capture_force_tool(
        "co mam jutro?",
        "record_show_day_plan",
        {"date_iso": "2026-04-28"},
    )
    assert captured["force_tool"] is True

    from shared.intent.intents import IntentType
    assert result.intent == IntentType.SHOW_DAY_PLAN
