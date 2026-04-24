"""Phase 6B — format_morning_brief_short.

Pure formatter tests. No declension, no LLM — the output is a deterministic
'Akcja: Klient' template with the 'Terminarz:' header always present.
"""

from datetime import date

from shared.formatting import format_morning_brief_short


def _event(event_type: str, start: str, title: str) -> dict:
    return {"event_type": event_type, "start": start, "title": title}


def _followup(name: str, next_step: str, due: date) -> dict:
    return {
        "name": name,
        "next_step": next_step,
        "next_step_date": due,
        "status": "Nowy lead",
    }


# ── Header always present ────────────────────────────────────────────────────


def test_empty_day_has_terminarz_header():
    out = format_morning_brief_short([], [])
    assert out.startswith("Terminarz:")


def test_empty_day_says_na_dzis_nie_masz_spotkan():
    out = format_morning_brief_short([], [])
    assert "Na dziś nie masz spotkań" in out
    # Two lines only: header + empty-state line.
    assert out.count("\n") == 1


def test_followups_only_starts_with_terminarz_and_na_dzis():
    items = [_followup("Jan Kowalski", "Telefon", date(2026, 4, 24))]
    out = format_morning_brief_short([], items)
    first_two = out.split("\n")[:2]
    assert first_two[0] == "Terminarz:"
    assert "Na dziś nie masz spotkań" in first_two[1]


def test_events_only_no_followups_section():
    ev = [_event("phone_call", "2026-04-24T09:00:00+02:00", "Telefon: Jan Kowalski")]
    out = format_morning_brief_short(ev, [])
    assert "Do dopilnowania dziś" not in out


def test_events_and_followups_both_sections():
    ev = [_event("in_person", "2026-04-24T11:30:00+02:00", "Spotkanie: Marta Nowak")]
    items = [_followup("Ewa Lis", "Wysłać ofertę", date(2026, 4, 23))]
    out = format_morning_brief_short(ev, items)
    assert "Terminarz:" in out
    assert "Do dopilnowania dziś:" in out


# ── Event label mapping ──────────────────────────────────────────────────────


def test_event_phone_call_label():
    ev = [_event("phone_call", "2026-04-24T09:00:00+02:00", "Telefon: Jan Kowalski")]
    out = format_morning_brief_short(ev, [])
    assert "Telefon: Jan Kowalski" in out


def test_event_in_person_label():
    ev = [_event("in_person", "2026-04-24T11:30:00+02:00", "Spotkanie: Marta Nowak")]
    out = format_morning_brief_short(ev, [])
    assert "Spotkanie: Marta Nowak" in out


def test_event_offer_email_label():
    ev = [_event("offer_email", "2026-04-24T15:00:00+02:00", "Wysłać ofertę: Piotr Zieliński")]
    out = format_morning_brief_short(ev, [])
    # Sheets enum "Wysłać ofertę" but brief uses shortened "Oferta" label.
    assert "Oferta: Piotr Zieliński" in out


def test_event_doc_followup_label_legacy():
    # doc_followup was removed from the MVP classifier in 5.4.2 but legacy
    # Calendar events may still carry the tag — mapping is preserved.
    ev = [_event("doc_followup", "2026-04-24T10:00:00+02:00", "Follow-up: Jan Kowalski")]
    out = format_morning_brief_short(ev, [])
    assert "Follow" in out and "Jan Kowalski" in out


def test_event_unknown_type_falls_back_to_title():
    ev = [_event("", "2026-04-24T10:00:00+02:00", "Nieznany event")]
    out = format_morning_brief_short(ev, [])
    assert "Nieznany event" in out


# ── Followup label mapping ───────────────────────────────────────────────────


def test_followup_telefon_label():
    items = [_followup("Tadek Sprawdzony", "Telefon", date(2026, 4, 24))]
    out = format_morning_brief_short([], items)
    assert "Telefon: Tadek Sprawdzony" in out


def test_followup_wyslac_oferte_label():
    items = [_followup("Ewa Lis", "Wysłać ofertę", date(2026, 4, 24))]
    out = format_morning_brief_short([], items)
    assert "Oferta: Ewa Lis" in out


def test_followup_spotkanie_label():
    items = [_followup("Anna Kozak", "Spotkanie", date(2026, 4, 24))]
    out = format_morning_brief_short([], items)
    assert "Spotkanie: Anna Kozak" in out


def test_followup_dokumentowy_maps_to_followup_label():
    items = [_followup("Jan Kowalski", "Follow-up dokumentowy", date(2026, 4, 24))]
    out = format_morning_brief_short([], items)
    assert "Follow\\-up: Jan Kowalski" in out
    assert "Do zrobienia: Jan Kowalski" not in out


def test_followup_unknown_enum_fallback():
    items = [_followup("Marian Nowicki", "Cokolwiek innego", date(2026, 4, 24))]
    out = format_morning_brief_short([], items)
    assert "Do zrobienia: Marian Nowicki" in out


def test_followup_past_due_rendered_no_date_suffix():
    # Overdue item from last week — still shown, but no date appears in line.
    items = [_followup("Jan Kowalski", "Telefon", date(2026, 4, 17))]
    out = format_morning_brief_short([], items)
    assert "Telefon: Jan Kowalski" in out
    assert "17.04" not in out
    assert "2026-04-17" not in out


# ── MDV2 escaping ────────────────────────────────────────────────────────────


def test_mdv2_escapes_dot_in_client_name():
    items = [_followup("Anna J. Kowalska", "Telefon", date(2026, 4, 24))]
    out = format_morning_brief_short([], items)
    # Dot escape per MDV2.
    assert "Anna J\\. Kowalska" in out


def test_mdv2_escapes_underscore_in_client_name():
    items = [_followup("test_user", "Telefon", date(2026, 4, 24))]
    out = format_morning_brief_short([], items)
    assert "test\\_user" in out


def test_empty_state_dot_escaped():
    out = format_morning_brief_short([], [])
    assert "Na dziś nie masz spotkań\\." in out


# ── Event time rendering ─────────────────────────────────────────────────────


def test_event_time_in_warsaw_timezone_converts_utc():
    # 07:00 UTC in late April = 09:00 Europe/Warsaw (CEST).
    ev = [_event("phone_call", "2026-04-24T07:00:00Z", "Telefon: Jan Kowalski")]
    out = format_morning_brief_short(ev, [])
    assert "09:00" in out


def test_event_time_hhmm_preserved_for_warsaw_start():
    ev = [_event("phone_call", "2026-04-24T09:00:00+02:00", "Telefon: Jan Kowalski")]
    out = format_morning_brief_short(ev, [])
    assert "09:00" in out


# ── Regression lock: no declension applied ───────────────────────────────────


def test_nominative_preserved_no_declension_applied():
    items = [_followup("Jan Kowalski", "Telefon", date(2026, 4, 24))]
    out = format_morning_brief_short([], items)
    # Regression guard — the alt template MUST NOT decline the name.
    assert "Jan Kowalski" in out
    assert "Jana Kowalskiego" not in out
