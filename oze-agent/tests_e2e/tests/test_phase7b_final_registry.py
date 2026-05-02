"""Pytest registry tests for Phase 7B-final scenarios.

Validates that the new scenario modules (notes, polish_edge) plus the
extensions to read_only / mutating_core / rules all registered properly,
all use `default_in_run=False`, and the total scenario count + categories
match the plan target.
"""

from tests_e2e.scenarios._base import SCENARIOS, list_categories, list_scenarios

# ── New stand-alone categories ─────────────────────────────────────────────

PHASE_7B_FINAL_NOTES = {
    "add_note_pure_short_save",
    "add_note_pure_bullets_save",
    "add_note_compound_phone_save",
}

PHASE_7B_FINAL_POLISH_EDGE = {
    "polish_slang_pv_pompeczka_parsing",
    "polish_relative_time_wpol",
}

# ── Extensions to existing categories ──────────────────────────────────────

PHASE_7B_FINAL_READ_ONLY_ADDITIONS = {
    "show_client_existing_just_created",
    "show_client_existing_with_history",
    "show_day_plan_tomorrow",
    "show_day_plan_empty_distant_day",
    "show_day_plan_with_just_added_meeting",
    "show_client_multi_match_disambig",
}

PHASE_7B_FINAL_RULES_ADDITIONS = {
    "r3_auto_cancel_pending_on_unrelated_input",
    "r3_explicit_dopisac_with_text_append",
    "r6_active_client_implicit_reference",
    "r7_next_action_prompt_after_add_client",
    "r8_frustration_calm_response",
}

# Total new from 7B-final = 22 (3 notes + 2 polish + 6 read_only + 6 mutating + 5 rules)
ALL_PHASE_7B_FINAL_NEW = (
    PHASE_7B_FINAL_NOTES
    | PHASE_7B_FINAL_POLISH_EDGE
    | PHASE_7B_FINAL_READ_ONLY_ADDITIONS
    | PHASE_7B_FINAL_RULES_ADDITIONS
    | {  # 6 from mutating_core (asserted separately in test_mutating_core.py)
        "add_meeting_offer_email_save",
        "add_meeting_doc_followup_save",
        "add_meeting_calendar_conflict_warning",
        "add_client_dup_dopisac_update_path",
        "change_status_rezygnacja_save",
        "change_status_status_first_compound_save",
    }
)


# ── notes category ────────────────────────────────────────────────────────


def test_notes_scenarios_registered():
    missing = PHASE_7B_FINAL_NOTES - set(SCENARIOS)
    assert not missing, f"missing notes scenarios: {missing}"


def test_notes_category_exists():
    assert "notes" in list_categories()


def test_notes_scenarios_in_notes_category():
    for n in PHASE_7B_FINAL_NOTES:
        assert SCENARIOS[n].category == "notes", f"{n} not in notes"


def test_notes_scenarios_are_opt_in():
    for n in PHASE_7B_FINAL_NOTES:
        assert SCENARIOS[n].default_in_run is False, (
            f"{n} writes Sheets — must be default_in_run=False"
        )


# ── polish_edge category ──────────────────────────────────────────────────


def test_polish_edge_scenarios_registered():
    missing = PHASE_7B_FINAL_POLISH_EDGE - set(SCENARIOS)
    assert not missing, f"missing polish_edge scenarios: {missing}"


def test_polish_edge_category_exists():
    assert "polish_edge" in list_categories()


def test_polish_edge_scenarios_in_polish_edge_category():
    for n in PHASE_7B_FINAL_POLISH_EDGE:
        assert SCENARIOS[n].category == "polish_edge", f"{n} not in polish_edge"


def test_polish_edge_scenarios_are_opt_in():
    for n in PHASE_7B_FINAL_POLISH_EDGE:
        assert SCENARIOS[n].default_in_run is False


# ── read_only extensions ──────────────────────────────────────────────────


def test_read_only_7b_final_additions_registered():
    missing = PHASE_7B_FINAL_READ_ONLY_ADDITIONS - set(SCENARIOS)
    assert not missing, f"missing read_only additions: {missing}"


def test_read_only_7b_final_additions_in_read_only_category():
    for n in PHASE_7B_FINAL_READ_ONLY_ADDITIONS:
        assert SCENARIOS[n].category == "read_only", (
            f"{n} should be in read_only, got {SCENARIOS[n].category}"
        )


def test_read_only_7b_final_additions_are_opt_in():
    """Setup-then-show scenarios still WRITE during setup → opt-in."""
    for n in PHASE_7B_FINAL_READ_ONLY_ADDITIONS:
        assert SCENARIOS[n].default_in_run is False, (
            f"{n} runs add_client during setup → must be opt-in"
        )


# ── rules extensions ──────────────────────────────────────────────────────


def test_rules_7b_final_additions_registered():
    missing = PHASE_7B_FINAL_RULES_ADDITIONS - set(SCENARIOS)
    assert not missing, f"missing rules additions: {missing}"


def test_rules_7b_final_additions_in_rules_category():
    for n in PHASE_7B_FINAL_RULES_ADDITIONS:
        assert SCENARIOS[n].category == "rules", (
            f"{n} should be in rules, got {SCENARIOS[n].category}"
        )


def test_rules_7b_final_additions_are_opt_in():
    for n in PHASE_7B_FINAL_RULES_ADDITIONS:
        assert SCENARIOS[n].default_in_run is False, (
            f"{n} runs mutating ops or context state → must be opt-in"
        )


# ── Aggregate invariants ──────────────────────────────────────────────────


def test_phase7b_final_total_count_is_22():
    """22 new scenarios across: notes(3) + polish_edge(2) + read_only(6) +
    mutating_core(6) + rules(5)."""
    assert len(ALL_PHASE_7B_FINAL_NEW) == 22


def test_all_phase7b_final_new_scenarios_registered():
    missing = ALL_PHASE_7B_FINAL_NEW - set(SCENARIOS)
    assert not missing, f"missing 7B-final scenarios: {missing}"


def test_all_phase7b_final_new_scenarios_have_descriptions():
    for n in ALL_PHASE_7B_FINAL_NEW:
        assert SCENARIOS[n].description, f"{n} has no description"


def test_total_scenario_count_after_phase7b_final():
    """Plan target plus opt-in photo flow smoke scenario."""
    assert len(SCENARIOS) == 49, (
        f"expected 49 total scenarios after adding photo_flow_smoke; got {len(SCENARIOS)}: "
        f"{sorted(SCENARIOS.keys())}"
    )


def test_categories_after_phase7b_final():
    """8-9 categories expected (mutating_core, notes, read_only, routing,
    card_structure, error_path, rules, polish_edge, proactive)."""
    cats = set(list_categories())
    expected = {
        "mutating_core", "notes", "read_only", "routing", "card_structure",
        "error_path", "rules", "polish_edge", "proactive",
    }
    assert expected.issubset(cats), f"missing categories: {expected - cats}"


def test_default_runner_excludes_all_new_7b_final():
    """All 22 new scenarios commit / interact with state — must never
    run in the default runner sweep."""
    default_names = {s.name for s in list_scenarios(only_default=True)}
    overlap = default_names & ALL_PHASE_7B_FINAL_NEW
    assert not overlap, f"7B-final scenarios leaked into default: {overlap}"
