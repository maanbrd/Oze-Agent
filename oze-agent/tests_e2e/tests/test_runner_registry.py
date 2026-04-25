"""Runner-level tests: scenario registry and selection parsing."""

import pytest

from tests_e2e import runner
from tests_e2e.scenarios._base import SCENARIOS, list_categories, list_scenarios


def test_registry_contains_debug_brief():
    assert "debug_brief" in SCENARIOS


def test_registry_contains_phase7a_scenarios():
    expected = {
        "debug_brief",
        "general_question_unknown",
        "general_question_what_can_you_do",
        "post_mvp_edit_client_rejection",
        "post_mvp_lejek_rejection",
        "vision_only_reschedule",
        "vision_only_free_slots",
        "vision_only_delete_client",
        "unplanned_pre_meeting_reminder",
        "show_day_plan_today",
        "show_client_not_found",
        "add_client_card_then_cancel",
        "add_meeting_card_then_cancel",
        "change_status_invalid_client",
        "add_meeting_past_date_rejection",
        "cancel_one_click_no_loop",
    }
    assert expected.issubset(set(SCENARIOS)), (
        f"missing: {expected - set(SCENARIOS)}"
    )


def test_categories_include_all_phase7a():
    cats = set(list_categories())
    expected = {"proactive", "routing", "read_only", "card_structure",
                "error_path", "rules"}
    assert expected.issubset(cats)


def test_runner_select_default_excludes_opt_in_scenarios():
    """Default `runner` (no args, no --category) excludes opt-in scenarios.

    debug_brief is opt-in (sends a brief); default run skips it. Codex review #2.
    """
    selected = runner._select_scenarios([], None)
    selected_names = {s.name for s in selected}
    assert "debug_brief" not in selected_names
    # All other 15 scenarios should be included.
    assert len(selected_names) == 15
    assert set(SCENARIOS) - selected_names == {"debug_brief"}


def test_runner_select_explicit_debug_brief_works():
    """Opt-in scenarios are still runnable when named explicitly."""
    selected = runner._select_scenarios(["debug_brief"], None)
    assert [s.name for s in selected] == ["debug_brief"]


def test_runner_select_by_name():
    selected = runner._select_scenarios(["debug_brief"], None)
    assert [s.name for s in selected] == ["debug_brief"]


def test_runner_select_by_category():
    selected = runner._select_scenarios([], "routing")
    assert {s.category for s in selected} == {"routing"}
    assert len(selected) >= 8  # S02-S09


def test_runner_select_unknown_name_raises():
    with pytest.raises(SystemExit):
        runner._select_scenarios(["does_not_exist"], None)


def test_runner_select_unknown_category_raises():
    with pytest.raises(SystemExit):
        runner._select_scenarios([], "no_such_category")


def test_runner_select_names_and_category_conflict():
    with pytest.raises(SystemExit):
        runner._select_scenarios(["debug_brief"], "routing")


def test_list_scenarios_filter_by_category():
    routing_only = list_scenarios(category="routing")
    assert all(s.category == "routing" for s in routing_only)
    assert len(routing_only) == 8
