from shared.offers.gmail import build_offer_email_message, deterministic_message_id


def test_offer_message_id_is_deterministic_per_idempotency_key():
    first = deterministic_message_id("attempt-123")
    second = deterministic_message_id("attempt-123")
    other = deterministic_message_id("attempt-456")
    assert first == second
    assert first != other
    assert first.startswith("<oze-offer-") and first.endswith("@agent-oze.local>")

    message = build_offer_email_message(
        ["jan@example.com"],
        {"name": "PV"},
        {"company_name": "Firma"},
        {"Imię i nazwisko": "Jan Kowalski"},
        b"pdf",
        message_id=first,
    )
    assert message["Message-ID"] == first
