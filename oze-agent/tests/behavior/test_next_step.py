import pytest

from shared.behavior.next_step import NextStepDecisionKind, classify_next_step_reply


@pytest.mark.parametrize(
    "text",
    ["nie wiem", "Nie wiem jeszcze", "nic", "później", "odłóż", "anuluj", "/cancel"],
)
def test_next_step_close_phrases_are_deterministic(text):
    decision = classify_next_step_reply(text)

    assert decision.kind is NextStepDecisionKind.CLOSE


@pytest.mark.parametrize(
    "text, event_type",
    [
        ("spotkanie", "in_person"),
        ("telefon", "phone_call"),
        ("zadzwoń jutro o 10", "phone_call"),
        ("mail", "offer_email"),
        ("wyślij mail jutro", "offer_email"),
    ],
)
def test_next_step_action_choices_map_to_event_type(text, event_type):
    decision = classify_next_step_reply(text)

    assert decision.kind is NextStepDecisionKind.ACTION
    assert decision.event_type == event_type


def test_next_step_field_update_wins_over_action_words():
    decision = classify_next_step_reply("telefon 525 225 242")

    assert decision.kind is NextStepDecisionKind.FIELD_UPDATE
    assert decision.field_update.updates == {"Telefon": "525225242"}
