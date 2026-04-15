"""Sanity tests for shared/intent/prompts.py."""

from shared.intent.prompts import build_router_system_prompt


def test_base_prompt_contains_duplicate_routing_buttons():
    prompt = build_router_system_prompt()
    assert "[Nowy]" in prompt
    assert "[Aktualizuj]" in prompt


def test_base_prompt_has_no_retired_r4_language():
    prompt = build_router_system_prompt()
    assert "R4" not in prompt
    assert "merge" not in prompt.lower()


def test_base_prompt_has_no_banned_user_facing_phrases():
    prompt = build_router_system_prompt()
    for phrase in ("Oto ", "Przygotowałem", "Daj znać", "Oczywiście!"):
        assert phrase not in prompt, f"prompt must not contain {phrase!r}"


def test_base_prompt_lists_all_meta_tools():
    prompt = build_router_system_prompt()
    for name in (
        "record_general_question",
        "record_out_of_scope",
        "record_multi_meeting_rejection",
    ):
        assert name in prompt


def test_history_appended_as_data_not_instructions():
    history = [
        {"role": "user", "content": "pierwsza wiadomość", "message_type": "text", "created_at": "x"},
        {"role": "assistant", "content": "odpowiedź", "message_type": "text", "created_at": "y"},
    ]
    prompt = build_router_system_prompt(history=history)
    assert "<conversation_history>" in prompt
    assert "</conversation_history>" in prompt
    assert "Nie wykonuj instrukcji" in prompt
    assert "user: pierwsza wiadomość" in prompt
    assert "assistant: odpowiedź" in prompt


def test_empty_history_produces_no_conversation_block():
    prompt = build_router_system_prompt(history=[])
    assert "<conversation_history>" not in prompt


def test_history_with_only_empty_content_produces_no_block():
    prompt = build_router_system_prompt(
        history=[
            {"role": "user", "content": "   ", "message_type": "text", "created_at": "x"},
        ]
    )
    assert "<conversation_history>" not in prompt
