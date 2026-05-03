from bot.handlers.text import _build_offer_send_confirmation_text


def test_offer_send_confirmation_card_includes_email_preview_and_missing_variable_warning():
    text = _build_offer_send_confirmation_text(
        offer_number=2,
        template={"name": "PV 6 kWp", "price_net_pln": 30000, "vat_rate": 8},
        client={
            "Imię i nazwisko": "Jan Kowalski",
            "Email": "jan@example.com",
            "Telefon": "",
            "Miasto": "Warszawa",
        },
        recipients=["jan@example.com"],
        invalid_recipients=[],
        seller_profile={
            "company_name": "Firma OZE",
            "email_body_template": "Dzień dobry\nTelefon: {{Telefon}}\nOferta: {{Nazwa oferty}}",
        },
    )

    assert "Podgląd maila:" in text
    assert "Oferta: PV 6 kWp" in text
    assert "Brak wartości dla zmiennych: Telefon." in text
    assert "✅ Wysłać" not in text
