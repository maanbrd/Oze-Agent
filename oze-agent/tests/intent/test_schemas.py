"""Structural tests for shared/intent/schemas.py."""

from shared.intent.intents import IntentType
from shared.intent.schemas import (
    ALL_TOOLS,
    EVENT_TYPE_VALUES,
    FEATURE_KEYS,
    FEATURE_KEY_TO_CATEGORY,
    OUT_OF_SCOPE_CATEGORIES,
    POST_MVP_FEATURE_KEYS,
    STATUS_VALUES,
    TOOL_NAME_TO_INTENT,
    UNPLANNED_FEATURE_KEYS,
    VISION_ONLY_FEATURE_KEYS,
)


EXPECTED_TOOLS = {
    "record_add_client",
    "record_show_client",
    "record_add_note",
    "record_change_status",
    "record_add_meeting",
    "record_show_day_plan",
    "record_general_question",
    "record_out_of_scope",
    "record_multi_meeting_rejection",
}


def _by_name() -> dict[str, dict]:
    return {tool["name"]: tool for tool in ALL_TOOLS}


def test_all_tools_have_required_top_level_keys():
    for tool in ALL_TOOLS:
        assert set(tool.keys()) >= {"name", "description", "input_schema"}
        schema = tool["input_schema"]
        assert schema["type"] == "object"
        assert "properties" in schema


def test_all_expected_tools_present_and_no_extras():
    names = {tool["name"] for tool in ALL_TOOLS}
    assert names == EXPECTED_TOOLS


def test_tool_name_to_intent_covers_all_tools_except_out_of_scope():
    # record_out_of_scope dispatches on category, not a 1:1 mapping.
    expected = EXPECTED_TOOLS - {"record_out_of_scope"}
    assert set(TOOL_NAME_TO_INTENT.keys()) == expected
    for value in TOOL_NAME_TO_INTENT.values():
        assert isinstance(value, IntentType)


def test_change_status_enum_matches_frozen_set():
    tool = _by_name()["record_change_status"]
    assert tool["input_schema"]["properties"]["status"]["enum"] == STATUS_VALUES
    assert tool["input_schema"]["required"] == ["client_name", "status"]


def test_add_meeting_event_type_enum_and_required_fields():
    tool = _by_name()["record_add_meeting"]
    props = tool["input_schema"]["properties"]
    assert props["event_type"]["enum"] == EVENT_TYPE_VALUES
    assert tool["input_schema"]["required"] == [
        "client_name",
        "date_iso",
        "event_type",
    ]


def test_out_of_scope_enums_and_required_fields():
    tool = _by_name()["record_out_of_scope"]
    props = tool["input_schema"]["properties"]
    assert props["category"]["enum"] == OUT_OF_SCOPE_CATEGORIES
    assert props["feature_key"]["enum"] == FEATURE_KEYS
    assert tool["input_schema"]["required"] == ["category", "feature_key"]


def test_feature_key_to_category_mapping_is_exhaustive():
    assert set(FEATURE_KEY_TO_CATEGORY) == set(FEATURE_KEYS)
    assert set(FEATURE_KEYS) == (
        set(POST_MVP_FEATURE_KEYS)
        | set(VISION_ONLY_FEATURE_KEYS)
        | set(UNPLANNED_FEATURE_KEYS)
    )
    assert {
        FEATURE_KEY_TO_CATEGORY[key] for key in POST_MVP_FEATURE_KEYS
    } == {"post_mvp_roadmap"}
    assert {
        FEATURE_KEY_TO_CATEGORY[key] for key in VISION_ONLY_FEATURE_KEYS
    } == {"vision_only"}
    assert {
        FEATURE_KEY_TO_CATEGORY[key] for key in UNPLANNED_FEATURE_KEYS
    } == {"unplanned"}


def test_show_client_schema_avoids_unsupported_top_level_anyof():
    tool = _by_name()["record_show_client"]
    assert "anyOf" not in tool["input_schema"]
    assert set(tool["input_schema"]["properties"]) == {"name", "city", "phone"}
    assert "co najmniej jedno" in tool["description"]


def test_multi_meeting_requires_count_min_two():
    tool = _by_name()["record_multi_meeting_rejection"]
    props = tool["input_schema"]["properties"]
    assert props["meeting_count"]["type"] == "integer"
    assert props["meeting_count"]["minimum"] == 2
    assert tool["input_schema"]["required"] == ["meeting_count"]
