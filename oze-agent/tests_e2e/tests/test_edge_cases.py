"""Unit checks for the edge_case E2E campaign registry and helpers."""

from __future__ import annotations

import pytest

from tests_e2e.scenarios import list_scenarios
from tests_e2e.scenarios import edge_cases


EXPECTED_EDGE_CASE_SCENARIOS = {
    "stale_save_button_rejected",
    "duplicate_same_name_two_cities_show_client",
    "duplicate_add_note_requires_city_or_choice",
    "pending_dopisac_then_unrelated_command",
    "multi_intent_status_plus_meeting",
    "relative_date_next_friday",
    "past_date_no_card",
    "active_client_pronoun_not_silent_write",
    "offer_missing_email_no_send",
    "offer_two_emails_single_attempt",
    "offer_invalid_extra_email_skipped",
    "photo_session_three_files",
    "photo_session_switch_client",
}


def test_edge_case_category_registers_expected_scenarios():
    scenarios = list_scenarios("edge_case")

    assert {scenario.name for scenario in scenarios} == EXPECTED_EDGE_CASE_SCENARIOS
    assert all(scenario.default_in_run is False for scenario in scenarios)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Nieaktualny przycisk. Wpisz polecenie jeszcze raz.", True),
        ("Ten klient ma kilka wpisów. Którego?", True),
        ("Nie znalazłem klienta.", False),
    ],
)
def test_disambiguation_reply_detection(text, expected):
    assert edge_cases._looks_like_disambiguation(text) is expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Podaj email klienta, żebym mógł wysłać ofertę.", True),
        ("Brakuje adresu email klienta.", True),
        ("Wysyłam ofertę. Dam znać po zakończeniu.", False),
    ],
)
def test_missing_email_reply_detection(text, expected):
    assert edge_cases._looks_like_missing_email_offer_reply(text) is expected


def test_next_friday_helper_returns_future_friday():
    start = edge_cases.date(2026, 5, 27)  # Wednesday

    result = edge_cases._next_named_weekday(start, target_weekday=4, force_next=True)

    assert result == edge_cases.date(2026, 6, 5)
