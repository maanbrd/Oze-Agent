"""Tests for shared/pending/payloads.py."""

import pytest

from shared.pending import (
    PAYLOAD_BY_FLOW_TYPE,
    AddClientDuplicatePayload,
    AddClientPayload,
    AddMeetingPayload,
    AddNotePayload,
    ChangeStatusPayload,
    DisambiguationPayload,
    PendingFlowType,
    R7PromptPayload,
    payload_from_flow_data,
    payload_to_flow_data,
)


# ── PAYLOAD_BY_FLOW_TYPE coverage ─────────────────────────────────────────────


def test_payload_map_covers_every_mvp_flow_type():
    assert set(PAYLOAD_BY_FLOW_TYPE.keys()) == set(PendingFlowType)


def test_payload_map_class_per_type():
    expected = {
        PendingFlowType.ADD_CLIENT: AddClientPayload,
        PendingFlowType.ADD_CLIENT_DUPLICATE: AddClientDuplicatePayload,
        PendingFlowType.ADD_NOTE: AddNotePayload,
        PendingFlowType.CHANGE_STATUS: ChangeStatusPayload,
        PendingFlowType.ADD_MEETING: AddMeetingPayload,
        PendingFlowType.DISAMBIGUATION: DisambiguationPayload,
        PendingFlowType.R7_PROMPT: R7PromptPayload,
    }
    assert PAYLOAD_BY_FLOW_TYPE == expected


# ── Round-trip: payload_from_flow_data → payload_to_flow_data ─────────────────


@pytest.mark.parametrize(
    "flow_type, flow_data, expected_cls",
    [
        (
            PendingFlowType.ADD_CLIENT,
            {"client_data": {"Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa"}},
            AddClientPayload,
        ),
        (
            PendingFlowType.ADD_CLIENT_DUPLICATE,
            {
                "client_data": {"Imię i nazwisko": "Jan", "Miasto": "Warszawa"},
                "duplicate_row": 7,
                "client_name": "Jan Kowalski",
                "city": "Warszawa",
            },
            AddClientDuplicatePayload,
        ),
        (
            PendingFlowType.ADD_NOTE,
            {
                "row": 12,
                "note_text": "dzwonił w sprawie gwarancji",
                "client_name": "Jan Kowalski",
                "city": "Warszawa",
                "old_notes": "poprzednia notatka",
            },
            AddNotePayload,
        ),
        (
            PendingFlowType.CHANGE_STATUS,
            {
                "row": 5,
                "field": "Status",
                "old_value": "Spotkanie umówione",
                "new_value": "Podpisane",
                "client_name": "Jan",
                "city": "Warszawa",
            },
            ChangeStatusPayload,
        ),
        (
            PendingFlowType.ADD_MEETING,
            {
                "title": "Spotkanie z Janem Kowalskim",
                "start": "2026-04-20T10:00:00+02:00",
                "end": "2026-04-20T11:00:00+02:00",
                "location": "Warszawa",
                "description": "Omówienie oferty",
                "client_name": "Jan Kowalski",
            },
            AddMeetingPayload,
        ),
        (
            PendingFlowType.DISAMBIGUATION,
            {"intent": "add_note", "note_text": "test"},
            DisambiguationPayload,
        ),
        (
            PendingFlowType.DISAMBIGUATION,
            {"intent": "change_status", "new_status": "Podpisane"},
            DisambiguationPayload,
        ),
        (
            PendingFlowType.R7_PROMPT,
            {"client_name": "Jan", "city": "Warszawa"},
            R7PromptPayload,
        ),
    ],
)
def test_payload_round_trip(flow_type, flow_data, expected_cls):
    payload = payload_from_flow_data(flow_type, flow_data)
    assert isinstance(payload, expected_cls)
    serialized = payload_to_flow_data(payload)
    # Every input key reappears with the same value.
    for key, value in flow_data.items():
        assert serialized[key] == value


# ── Optional / variant fields ─────────────────────────────────────────────────


def test_add_client_underscore_offer_remaining_preserved():
    flow_data = {
        "client_data": {"Imię i nazwisko": "Jan"},
        "_offer_remaining": ["Anna", "Piotr"],
    }
    payload = payload_from_flow_data(PendingFlowType.ADD_CLIENT, flow_data)
    assert payload._offer_remaining == ["Anna", "Piotr"]
    assert payload_to_flow_data(payload)["_offer_remaining"] == ["Anna", "Piotr"]


def test_add_client_without_offer_remaining_defaults_to_none():
    payload = payload_from_flow_data(
        PendingFlowType.ADD_CLIENT, {"client_data": {"Imię i nazwisko": "Jan"}}
    )
    assert payload._offer_remaining is None


def test_disambiguation_add_note_variant():
    payload = payload_from_flow_data(
        PendingFlowType.DISAMBIGUATION,
        {"intent": "add_note", "note_text": "test"},
    )
    assert isinstance(payload, DisambiguationPayload)
    assert payload.intent == "add_note"
    assert payload.note_text == "test"
    assert payload.new_status is None


def test_disambiguation_change_status_variant():
    payload = payload_from_flow_data(
        PendingFlowType.DISAMBIGUATION,
        {"intent": "change_status", "new_status": "Podpisane"},
    )
    assert isinstance(payload, DisambiguationPayload)
    assert payload.intent == "change_status"
    assert payload.new_status == "Podpisane"
    assert payload.note_text is None


def test_change_status_field_defaults_to_status_literal():
    payload = payload_from_flow_data(
        PendingFlowType.CHANGE_STATUS,
        {"row": 1, "new_value": "Podpisane", "client_name": "Jan"},
    )
    assert payload.field == "Status"


def test_add_note_optional_fields_default_to_empty_string():
    payload = payload_from_flow_data(
        PendingFlowType.ADD_NOTE,
        {"row": 1, "note_text": "hi", "client_name": "Jan"},
    )
    assert payload.city == ""
    assert payload.old_notes == ""


def test_r7_prompt_optional_city_defaults_to_empty_string():
    payload = payload_from_flow_data(
        PendingFlowType.R7_PROMPT, {"client_name": "Jan"}
    )
    assert payload.city == ""


# ── Permissive structure: extra keys silently dropped ─────────────────────────


def test_unknown_keys_in_flow_data_are_silently_dropped():
    flow_data = {
        "client_data": {"Imię i nazwisko": "Jan"},
        "legacy_metadata_key": "ignored",
        "another_unknown": 42,
    }
    payload = payload_from_flow_data(PendingFlowType.ADD_CLIENT, flow_data)
    assert payload.client_data == {"Imię i nazwisko": "Jan"}
    serialized = payload_to_flow_data(payload)
    assert "legacy_metadata_key" not in serialized
    assert "another_unknown" not in serialized


# ── Required fields raise TypeError when missing ──────────────────────────────


def test_add_client_missing_client_data_raises():
    with pytest.raises(TypeError):
        payload_from_flow_data(PendingFlowType.ADD_CLIENT, {})


def test_add_meeting_with_only_required_fields_succeeds():
    # location and description are optional; every required field present.
    payload = payload_from_flow_data(
        PendingFlowType.ADD_MEETING,
        {"title": "x", "start": "y", "end": "z", "client_name": "a"},
    )
    assert payload.location == ""
    assert payload.description == ""


def test_add_meeting_missing_required_title_raises():
    with pytest.raises(TypeError):
        payload_from_flow_data(
            PendingFlowType.ADD_MEETING,
            {"start": "y", "end": "z", "client_name": "a"},
        )


def test_change_status_missing_new_value_raises():
    with pytest.raises(TypeError):
        payload_from_flow_data(
            PendingFlowType.CHANGE_STATUS, {"row": 1, "client_name": "Jan"}
        )


def test_disambiguation_missing_intent_raises():
    with pytest.raises(TypeError):
        payload_from_flow_data(PendingFlowType.DISAMBIGUATION, {"note_text": "x"})
