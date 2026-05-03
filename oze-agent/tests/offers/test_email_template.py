from pathlib import Path

from shared.offers.email_template import (
    DEFAULT_EMAIL_BODY_TEMPLATE,
    EMAIL_VARIABLES,
    render_email_template,
    validate_email_template,
)
from shared.offers.gmail import build_offer_email_body


def test_render_email_template_replaces_sheet_offer_and_profile_variables():
    rendered = render_email_template(
        "Klient: {{Imię i nazwisko}}\nMiasto: {{Miasto}}\nFirma: {{Firma}}\nOferta: {{Nazwa oferty}}\nCena: {{Cena}}",
        client={"Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa"},
        template={"name": "PV 6 kWp", "price_net_pln": 30000, "vat_rate": 8},
        seller_profile={"company_name": "Firma OZE"},
    )

    assert rendered.body == (
        "Klient: Jan Kowalski\n"
        "Miasto: Warszawa\n"
        "Firma: Firma OZE\n"
        "Oferta: PV 6 kWp\n"
        "Cena: 32 400 PLN"
    )
    assert rendered.missing_variables == []


def test_unknown_email_template_variable_blocks_save():
    result = validate_email_template("Dzień dobry {{PESEL}}")

    assert not result.is_valid
    assert result.unknown_variables == ["PESEL"]


def test_empty_known_variable_returns_warning_without_crashing():
    rendered = render_email_template(
        "Telefon: {{Telefon}}\nStatus: {{Status}}",
        client={"Telefon": "", "Status": "Nowy lead"},
        template={"name": "PV", "price_net_pln": 10000, "vat_rate": 8},
        seller_profile={"company_name": "Firma"},
    )

    assert rendered.body == "Telefon: \nStatus: Nowy lead"
    assert rendered.missing_variables == ["Telefon"]


def test_default_email_template_is_used_when_profile_template_is_empty():
    body = build_offer_email_body(
        template={"name": "PV 6 kWp", "price_net_pln": 30000, "vat_rate": 8},
        seller_profile={"company_name": "Firma OZE", "email_body_template": ""},
        client={"Imię i nazwisko": "Jan Kowalski"},
    )

    assert body == render_email_template(
        DEFAULT_EMAIL_BODY_TEMPLATE,
        client={"Imię i nazwisko": "Jan Kowalski"},
        template={"name": "PV 6 kWp", "price_net_pln": 30000, "vat_rate": 8},
        seller_profile={"company_name": "Firma OZE", "email_body_template": ""},
    ).body


def test_gmail_body_uses_email_template_and_ignores_legacy_signature():
    body = build_offer_email_body(
        template={"name": "Magazyn 10 kWh", "price_net_pln": 20000, "vat_rate": 23},
        seller_profile={
            "company_name": "Magazyny 360",
            "email_signature": "Stary podpis",
            "email_body_template": "Oferta: {{Nazwa oferty}}\nCena: {{Cena}}\n{{Firma}}",
        },
        client={"Imię i nazwisko": "Anna Nowak"},
    )

    assert body == "Oferta: Magazyn 10 kWh\nCena: 24 600 PLN\nMagazyny 360"
    assert "Stary podpis" not in body


def test_email_variables_exclude_technical_sheet_fields():
    tokens = {variable["token"] for variable in EMAIL_VARIABLES}

    assert "{{Imię i nazwisko}}" in tokens
    assert "{{Cena}}" in tokens
    assert "{{_row}}" not in tokens
    assert "{{ID wydarzenia Kalendarz}}" not in tokens
    assert "{{Zdjęcia}}" not in tokens
    assert "{{Link do zdjęć}}" not in tokens


def test_offer_seller_profiles_schema_has_email_body_template_column():
    schema = Path(__file__).parents[2].joinpath("supabase_schema.sql").read_text()

    assert "email_body_template TEXT" in schema
