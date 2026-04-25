"""Pure unit tests for tests_e2e.card_parser. No Telegram, no Telethon."""

from tests_e2e.card_parser import (
    is_cancel_message,
    is_not_found,
    is_not_understood,
    is_post_mvp_reply,
    is_vision_only_reply,
    parse_card,
)


# ── Header / icon detection ──────────────────────────────────────────────────


def test_parse_add_client_card_header():
    text = "📋 Jan Kowalski, Piłsudskiego 12, Warszawa"
    card = parse_card(text)
    assert card.icon == "📋"
    assert card.header_line == "Jan Kowalski, Piłsudskiego 12, Warszawa"


def test_parse_change_status_card_header():
    text = "📊 Jan Kowalski, Warszawa\nStatus: Oferta wysłana → Spotkanie umówione"
    card = parse_card(text)
    assert card.icon == "📊"
    assert card.status_transition == ("Oferta wysłana", "Spotkanie umówione")


def test_parse_add_meeting_card_in_person_header():
    text = "📅 Spotkanie: Jan Kowalski, Warszawa\nData: 26.04.2026 (Niedziela) 14:00"
    card = parse_card(text)
    assert card.icon == "📅"
    assert card.header_line == "Spotkanie: Jan Kowalski, Warszawa"
    assert card.fields["Data"] == "26.04.2026 (Niedziela) 14:00"


def test_parse_add_meeting_phone_call_header():
    text = "📞 Telefon: Jan Kowalski, Warszawa\nData: 26.04.2026 (Niedziela) 10:00"
    card = parse_card(text)
    assert card.icon == "📞"


def test_parse_add_note_card_flow_a():
    text = '📝 Marek Kowalski, Wyszków:\ndodaj notatkę "ma duży dom"?'
    card = parse_card(text)
    assert card.icon == "📝"
    assert card.header_line == "Marek Kowalski, Wyszków:"


def test_parse_card_without_known_icon_keeps_header():
    text = "Hello world\nProdukt: PV"
    card = parse_card(text)
    assert card.icon is None
    assert card.header_line == "Hello world"
    assert card.fields.get("Produkt") == "PV"


# ── Field extraction ─────────────────────────────────────────────────────────


def test_parse_card_extracts_known_fields():
    text = (
        "📋 Jan Kowalski, Warszawa\n"
        "Produkt: PV\n"
        "Tel. 600 100 200\n"
        "Email: jan@example.pl\n"
        "Status: Nowy lead"
    )
    card = parse_card(text)
    assert card.fields["Produkt"] == "PV"
    assert card.fields["Tel"] == "600 100 200"
    assert card.fields["Email"] == "jan@example.pl"
    assert card.fields["Status"] == "Nowy lead"


def test_parse_card_extracts_missing_list():
    text = (
        "📋 Jan, Warszawa\n"
        "❓ Brakuje: email, źródło leada, adres"
    )
    card = parse_card(text)
    assert card.missing == ["email", "źródło leada", "adres"]


def test_parse_card_missing_list_empty_when_omitted():
    text = "📋 Jan, Warszawa\nProdukt: PV"
    card = parse_card(text)
    assert card.missing == []


def test_parse_card_status_transition_picks_up_compound_form():
    text = (
        "📋 Jan, Warszawa\n"
        "Zapis obejmuje:\n"
        "• Status → Oferta wysłana\n"
        "• Spotkanie: 26.04.2026 (Niedziela) 14:00"
    )
    card = parse_card(text)
    assert len(card.bullets) == 2


def test_parse_card_collects_bullets():
    text = "📝 Jan, Warszawa:\n• Notatka: 'ma duży dom'\n• Calendar: 26.04 14:00"
    card = parse_card(text)
    assert len(card.bullets) == 2
    assert card.bullets[0].startswith("Notatka")


# ── Buttons / read-only detection ────────────────────────────────────────────


def test_three_button_card_detection():
    card = parse_card(
        "📋 Jan, Warszawa",
        button_labels=["✅ Zapisać", "➕ Dopisać", "❌ Anulować"],
    )
    assert card.has_three_button() is True


def test_three_button_card_partial_buttons_fails():
    card = parse_card(
        "📋 Jan, Warszawa",
        button_labels=["✅ Zapisać", "❌ Anulować"],
    )
    assert card.has_three_button() is False


def test_three_button_card_word_only_passes_tolerant():
    # Tolerant mode: word-only labels (no icons) still satisfy the structural
    # check. Codex review #3.
    card = parse_card(
        "📋 Jan, Warszawa",
        button_labels=["Zapisać", "Dopisać", "Anulować"],
    )
    assert card.has_three_button() is True


def test_three_button_card_partial_words_fails():
    card = parse_card(
        "📋 Jan, Warszawa",
        button_labels=["Zapisać", "Anulować"],
    )
    assert card.has_three_button() is False


def test_three_button_card_empty_labels_fails():
    card = parse_card("📋 Jan, Warszawa", button_labels=[])
    assert card.has_three_button() is False


def test_routing_buttons_detection():
    card = parse_card("Ten klient już jest w arkuszu...", ["Nowy", "Aktualizuj"])
    assert card.has_routing_buttons() is True
    assert card.has_three_button() is False


def test_read_only_card_no_buttons():
    card = parse_card("📋 Jan Kowalski — Piłsudskiego 12, Warszawa\nProdukt: PV")
    assert card.is_read_only() is True
    assert card.has_three_button() is False


# ── Marker helpers ───────────────────────────────────────────────────────────


def test_is_cancel_message_accepts_canonical():
    assert is_cancel_message("🫡 Anulowane.") is True
    assert is_cancel_message("⚠️ Anulowane.") is True
    assert is_cancel_message("Anulowane.") is True


def test_is_cancel_message_rejects_unrelated():
    assert is_cancel_message("Coś innego") is False


def test_is_not_found():
    assert is_not_found("Nie znalazłem klienta E2E-Beta-NieIstnieje") is True
    assert is_not_found("Found you") is False


def test_is_not_understood():
    assert is_not_understood("Nie zrozumiałem, powiedz to inaczej.") is True
    assert is_not_understood("OK") is False


def test_is_post_mvp_reply():
    assert is_post_mvp_reply("To feature post-MVP. Wejdzie później.") is True


def test_is_vision_only_reply():
    txt = "Reschedule jest poza aktualnym MVP scope (vision-only)."
    assert is_vision_only_reply(txt) is True


def test_empty_text_returns_empty_card():
    card = parse_card("")
    assert card.icon is None
    assert card.fields == {}
    assert card.missing == []
    assert card.button_labels == []


def test_parse_card_unparsed_lines_for_drift_detection():
    # 'Jakaś dziwna linia' is neither a known field nor a bullet — should
    # surface in unparsed_lines so callers can flag drift.
    text = "📋 Jan, Warszawa\nJakaś dziwna linia bez kropki dwukropka"
    card = parse_card(text)
    assert len(card.unparsed_lines) >= 1
