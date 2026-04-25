"""Pytest checks for the Phase 7B.1 mutating-core scenario registry.

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


def test_mutating_core_category_contains_only_phase7b1_for_now():
    """Sanity: as 7B.2/7B.3 add more, this test will need updating."""
    in_category = {s.name for s in list_scenarios(category="mutating_core")}
    assert in_category == PHASE_7B1_SCENARIOS, (
        f"unexpected mutating_core members; "
        f"got {in_category}, expected {PHASE_7B1_SCENARIOS}"
    )


def test_default_runner_excludes_all_7b1_scenarios():
    """Belt-and-suspenders: default `runner` selection must NEVER include
    a mutating_core scenario, even if `default_in_run` regresses to True."""
    default_names = {s.name for s in list_scenarios(only_default=True)}
    overlap = default_names & PHASE_7B1_SCENARIOS
    assert not overlap, (
        f"7B.1 mutating scenarios leaked into default selection: {overlap}"
    )
