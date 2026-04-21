"""Structural tests for shared/pending/types.py."""

from shared.pending.types import PendingFlow, PendingFlowType


_EXPECTED_VALUES = {
    PendingFlowType.ADD_CLIENT: "add_client",
    PendingFlowType.ADD_CLIENT_DUPLICATE: "add_client_duplicate",
    PendingFlowType.ADD_NOTE: "add_note",
    PendingFlowType.CHANGE_STATUS: "change_status",
    PendingFlowType.ADD_MEETING: "add_meeting",
    PendingFlowType.ADD_MEETING_DISAMBIGUATION: "add_meeting_disambiguation",
    PendingFlowType.DISAMBIGUATION: "disambiguation",
    PendingFlowType.R7_PROMPT: "r7_prompt",
}


def test_every_member_value_matches_legacy_string():
    for member, expected in _EXPECTED_VALUES.items():
        assert member.value == expected


def test_enum_covers_exactly_the_mvp_types():
    assert {m.value for m in PendingFlowType} == set(_EXPECTED_VALUES.values())


def test_str_enum_equality_with_raw_string():
    assert PendingFlowType.ADD_CLIENT == "add_client"
    assert PendingFlowType.R7_PROMPT == "r7_prompt"


def test_pending_flow_defaults():
    flow = PendingFlow(telegram_id=1, flow_type=PendingFlowType.ADD_CLIENT)
    assert flow.telegram_id == 1
    assert flow.flow_type is PendingFlowType.ADD_CLIENT
    assert flow.flow_data == {}
    assert flow.created_at is None


def test_pending_flow_carries_payload():
    flow = PendingFlow(
        telegram_id=42,
        flow_type=PendingFlowType.ADD_NOTE,
        flow_data={"row": 7, "note_text": "test"},
    )
    assert flow.flow_data == {"row": 7, "note_text": "test"}
