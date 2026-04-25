"""Pytest checks for the mutating_core scenario registry.

Pure registry assertions — these do NOT actually run any scenario (those
require a live Telegram and a real bot). The unit tests just verify
shape: names registered, all `default_in_run=False` (so they never run
in the default sweep), all in the same category.
"""

from tests_e2e.scenarios._base import SCENARIOS, list_scenarios

PHASE_7B1_SCENARIOS = {
    "add_client_minimal_save",
    "add_client_full_save",
    "add_client_missing_fields_fillin_save",
    "add_client_with_followup_meeting_save",
    # Renamed 25.04.2026 from `add_client_dup_nowy_save` after 2nd smoke
    # run revealed bot does NOT serve a separate [Nowy]/[Aktualizuj] routing
    # card — duplicate handling is integrated into the standard 3-button
    # mutation card via ➕ Dopisać. Scenario now tests the "click ✅ Zapisać"
    # path (create new), with the form divergence logged as known_drift.
    "add_client_dup_save_create_new",
    "add_meeting_in_person_save",
    "add_meeting_phone_call_save",
    "add_meeting_relative_date_save",
    "add_meeting_compound_change_status_save",
    "change_status_simple_save",
}

# Phase 7B-final added 6 more mutating_core scenarios.
PHASE_7B_FINAL_MUTATING = {
    "add_meeting_offer_email_save",
    "add_meeting_doc_followup_save",
    "add_meeting_calendar_conflict_warning",
    "add_client_dup_dopisac_update_path",
    "change_status_rezygnacja_save",
    "change_status_status_first_compound_save",
}

ALL_MUTATING_CORE = PHASE_7B1_SCENARIOS | PHASE_7B_FINAL_MUTATING


def test_phase7b1_all_scenarios_registered():
    missing = PHASE_7B1_SCENARIOS - set(SCENARIOS)
    assert not missing, f"missing 7B.1 scenarios: {missing}"


def test_phase7b1_count_is_ten():
    assert len(PHASE_7B1_SCENARIOS) == 10
    in_registry = PHASE_7B1_SCENARIOS & set(SCENARIOS)
    assert len(in_registry) == 10


def test_phase7b1_scenarios_in_mutating_core_category():
    for name in PHASE_7B1_SCENARIOS:
        scen = SCENARIOS[name]
        assert scen.category == "mutating_core", (
            f"{name} should be in 'mutating_core', got {scen.category!r}"
        )


def test_phase7b1_all_scenarios_are_opt_in():
    """7B.1 scenarios COMMIT to Sheets/Calendar — must NEVER run by default."""
    for name in PHASE_7B1_SCENARIOS:
        scen = SCENARIOS[name]
        assert scen.default_in_run is False, (
            f"{name} writes to Sheets/Calendar — must have "
            f"default_in_run=False, got {scen.default_in_run}"
        )


def test_phase7b1_scenarios_have_descriptions():
    for name in PHASE_7B1_SCENARIOS:
        scen = SCENARIOS[name]
        assert scen.description, f"{name} has no description"


def test_mutating_core_category_matches_expected_set():
    """The mutating_core category should equal the union of 7B.1 + 7B-final."""
    in_category = {s.name for s in list_scenarios(category="mutating_core")}
    assert in_category == ALL_MUTATING_CORE, (
        f"unexpected mutating_core members; "
        f"got {in_category}, expected {ALL_MUTATING_CORE}"
    )


def test_phase7b_final_scenarios_registered():
    missing = PHASE_7B_FINAL_MUTATING - set(SCENARIOS)
    assert not missing, f"missing 7B-final mutating_core scenarios: {missing}"


def test_phase7b_final_scenarios_are_opt_in():
    """7B-final mutating scenarios must NEVER run by default."""
    for name in PHASE_7B_FINAL_MUTATING:
        scen = SCENARIOS[name]
        assert scen.default_in_run is False, (
            f"{name} writes to Sheets/Calendar — must have default_in_run=False"
        )


def test_default_runner_excludes_all_mutating_scenarios():
    """Belt-and-suspenders: default `runner` selection must NEVER include
    a mutating_core scenario, even if `default_in_run` regresses to True."""
    default_names = {s.name for s in list_scenarios(only_default=True)}
    overlap = default_names & ALL_MUTATING_CORE
    assert not overlap, (
        f"mutating scenarios leaked into default selection: {overlap}"
    )
