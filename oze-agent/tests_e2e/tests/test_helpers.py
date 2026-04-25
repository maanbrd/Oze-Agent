"""Pure unit tests for tests_e2e.scenarios._helpers.

Covers the synchronous helpers that don't need a live Telegram. Async
helpers (`reset_pending`, `close_post_save_followup`,
`click_save_and_collect`) are integration-tested via real scenarios.
"""

from datetime import date

from tests_e2e.scenarios._helpers import (
    _has_co_dalej,
    e2e_beta_name,
    find_card_message,
    find_routing_button_label,
    find_save_button_label,
    fmt_pl_date,
    is_save_confirmation,
    today_warsaw,
    tomorrow_warsaw,
    yesterday_warsaw,
)


# ── Save-confirmation marker matching ──────────────────────────────────────


def test_is_save_confirmation_recognizes_zapisane():
    """Bot's canonical save reply form is `✅ Zapisane.` — observed
    25.04.2026 in 7B.1 first smoke run, originally caused 8 blockers."""
    assert is_save_confirmation("✅ Zapisane.") is True
    assert is_save_confirmation("Zapisane!") is True


def test_is_save_confirmation_recognizes_zapisalem():
    """Spec-suggested 1st-person form."""
    assert is_save_confirmation("Zapisałem klienta E2E-Beta-Tester.") is True


def test_is_save_confirmation_recognizes_zapisano():
    assert is_save_confirmation("✅ Zapisano klienta.") is True


def test_is_save_confirmation_recognizes_dodano():
    assert is_save_confirmation("Dodano spotkanie.") is True


def test_is_save_confirmation_recognizes_meeting_specific():
    assert is_save_confirmation("Spotkanie umówione: ...") is True


def test_is_save_confirmation_recognizes_spotkanie_dodane():
    """Bot's actual meeting-save reply is `✅ Spotkanie dodane do kalendarza.`
    Added 25.04.2026 after 2nd 7B.1 smoke run revealed this wording."""
    assert is_save_confirmation("✅ Spotkanie dodane do kalendarza.") is True
    assert is_save_confirmation(
        "✅ Spotkanie dodane do kalendarza. Status klienta: Podpisane."
    ) is True


def test_is_save_confirmation_recognizes_status_specific():
    assert is_save_confirmation("Status zmieniony.") is True


def test_is_save_confirmation_rejects_co_dalej():
    """The 'Co dalej' follow-up must NOT count as save confirm."""
    assert is_save_confirmation("Co dalej — Jan Kowalski (Warszawa)?") is False


def test_is_save_confirmation_rejects_nie_rozumiem():
    assert is_save_confirmation("Nie rozumiem. Podaj np. 'spotkanie jutro o 14'.") is False


def test_is_save_confirmation_rejects_empty():
    assert is_save_confirmation("") is False


def test_is_save_confirmation_rejects_card_text():
    """The card itself ('📋 ... Zapisać / dopisać') must not count."""
    card_text = (
        "📋 Jan Kowalski, Warszawa\n"
        "PV\nTel. 600 100 200\nZapisać / dopisać / anulować?"
    )
    assert is_save_confirmation(card_text) is False


# ── Co-dalej detection ──────────────────────────────────────────────────────


class _FakeMsg:
    """Minimal stand-in for _ObservedMessage — only `.text` is needed."""

    def __init__(self, text: str) -> None:
        self.text = text


def test_has_co_dalej_detects_canonical_form():
    msgs = [_FakeMsg("✅ Zapisane."), _FakeMsg("Co dalej — Jan (Warszawa)?")]
    assert _has_co_dalej(msgs) is True


def test_has_co_dalej_returns_false_when_absent():
    msgs = [_FakeMsg("✅ Zapisane."), _FakeMsg("OK.")]
    assert _has_co_dalej(msgs) is False


def test_has_co_dalej_handles_empty_list():
    assert _has_co_dalej([]) is False


# ── Card / button picking helpers ───────────────────────────────────────────


def test_find_card_message_picks_msg_with_buttons():
    a = _FakeMsg("typing...")
    a.button_labels = []
    b = _FakeMsg("📋 Jan, Warszawa")
    b.button_labels = ["✅ Zapisać", "➕ Dopisać", "❌ Anulować"]
    assert find_card_message([a, b]) is b


def test_find_card_message_returns_none_when_no_buttons():
    a = _FakeMsg("just text")
    a.button_labels = []
    assert find_card_message([a]) is None


def test_find_save_button_label_matches_icon():
    assert find_save_button_label(["✅ Zapisać", "➕ Dopisać", "❌ Anulować"]) == "✅ Zapisać"


def test_find_save_button_label_matches_word_only():
    assert find_save_button_label(["Zapisać", "Dopisać", "Anulować"]) == "Zapisać"


def test_find_save_button_label_returns_none_when_absent():
    assert find_save_button_label(["Nowy", "Aktualizuj"]) is None


def test_find_save_button_label_handles_empty():
    assert find_save_button_label([]) is None


def test_find_routing_button_label_case_insensitive():
    labels = ["Nowy", "Aktualizuj"]
    assert find_routing_button_label(labels, "nowy") == "Nowy"
    assert find_routing_button_label(labels, "AKTUALIZUJ") == "Aktualizuj"


def test_find_routing_button_label_returns_none_when_absent():
    assert find_routing_button_label(["✅ Zapisać"], "nowy") is None


# ── Date helpers ────────────────────────────────────────────────────────────


def test_today_warsaw_returns_a_date():
    assert isinstance(today_warsaw(), date)


def test_tomorrow_is_one_day_after_today():
    assert (tomorrow_warsaw() - today_warsaw()).days == 1


def test_yesterday_is_one_day_before_today():
    assert (today_warsaw() - yesterday_warsaw()).days == 1


def test_fmt_pl_date_format():
    d = date(2026, 4, 26)  # Niedziela
    formatted = fmt_pl_date(d)
    assert formatted == "26.04.2026 (Niedziela)"


def test_fmt_pl_date_uses_correct_weekday():
    d = date(2026, 4, 27)  # Poniedziałek
    assert fmt_pl_date(d) == "27.04.2026 (Poniedziałek)"


# ── Synthetic name generation ───────────────────────────────────────────────


def test_e2e_beta_name_contains_marker_prefix():
    name = e2e_beta_name()
    assert name.startswith("E2E-Beta-Tester-")


def test_e2e_beta_name_with_suffix():
    name = e2e_beta_name("B01")
    assert name.startswith("E2E-Beta-Tester-")
    assert name.endswith("-B01")


def test_e2e_beta_name_two_calls_differ_or_same():
    """Names use HHMMSS — two calls in the same second yield same; otherwise differ."""
    n1 = e2e_beta_name()
    n2 = e2e_beta_name()
    # Either identical (same second) or different (different second). Both valid.
    assert n1 == n2 or n1 != n2  # tautology — just verifying call doesn't crash
