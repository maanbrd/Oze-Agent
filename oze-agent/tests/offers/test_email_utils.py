from shared.offers.email_utils import (
    extract_email_addresses,
    merge_offer_recipients,
    salutation_for_client,
    sanitize_filename_part,
)


def test_extract_email_addresses_from_free_text():
    assert extract_email_addresses("wyślij na jan@example.com i anna.nowak@firma.pl") == [
        "jan@example.com",
        "anna.nowak@firma.pl",
    ]


def test_merge_offer_recipients_keeps_valid_unique_and_flags_invalid():
    result = merge_offer_recipients(
        sheet_email_field="jan@example.com; bledny@@x; ANNA@example.com",
        command_text="wyślij też na anna@example.com i nowy@firma.pl",
    )

    assert result.recipients == ["jan@example.com", "anna@example.com", "nowy@firma.pl"]
    assert result.invalid_recipients == ["bledny@@x"]
    assert result.new_emails_for_sheets == ["nowy@firma.pl"]


def test_merge_offer_recipients_uses_command_email_when_sheet_empty():
    result = merge_offer_recipients("", "kontakt: klient@example.com")

    assert result.recipients == ["klient@example.com"]
    assert result.new_emails_for_sheets == ["klient@example.com"]


def test_salutation_uses_polish_name_heuristic_or_neutral_fallback():
    assert salutation_for_client({"Imię i nazwisko": "Anna Kowalska"}) == "Pani Kowalska"
    assert salutation_for_client({"Imię i nazwisko": "Jan Kowalski"}) == "Panie Kowalski"
    assert salutation_for_client({"Imię i nazwisko": "Firma ABC"}) == "Dzień dobry"


def test_sanitize_filename_part_removes_unsafe_characters():
    assert sanitize_filename_part("Jan / Kowalski: PV 8 kWp") == "Jan-Kowalski-PV-8-kWp"
