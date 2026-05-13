from shared.behavior.action_type import (
    action_label,
    calendar_title,
    confirmation_heading,
    description_prefix,
    schedule_entry_suffix,
    success_message,
)


def test_phone_copy_never_uses_meeting_wording():
    assert action_label("phone_call") == "Telefon"
    assert confirmation_heading("phone_call") == "✅ Dodać telefon?"
    assert success_message("phone_call") == "✅ Telefon dodany do kalendarza."
    assert calendar_title("phone_call", "Zbigniew Borek") == "Telefon — Zbigniew Borek"
    assert schedule_entry_suffix("phone_call") == "telefon"


def test_in_person_copy_stays_meeting_wording():
    assert action_label("in_person") == "Spotkanie"
    assert confirmation_heading("in_person") == "✅ Dodać spotkanie?"
    assert success_message("in_person") == "✅ Spotkanie dodane do kalendarza."
    assert calendar_title("in_person", "Zbigniew Borek") == "Spotkanie — Zbigniew Borek"
    assert schedule_entry_suffix("in_person") == "spotkanie"


def test_description_prefixes_are_type_specific():
    assert description_prefix("in_person") == ""
    assert description_prefix("phone_call") == "📞 Zadzwoń do klienta."
    assert description_prefix("offer_email") == "📧 Wyślij ofertę klientowi."
