from pathlib import Path

from shared.offers.pdf import build_offer_pdf_context, render_offer_pdf


def test_pdf_context_hides_subsidy_section_when_empty():
    context = build_offer_pdf_context(
        template={
            "name": "PV 6 kWp",
            "product_type": "PV",
            "price_net_pln": 30000,
            "vat_rate": 8,
        },
        seller_profile={"company_name": "Firma OZE"},
        client={"Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa"},
    )

    assert context["subsidy_amount"] is None
    assert context["primary_price"] == "32 400 PLN"


def test_pdf_context_shows_primary_price_after_subsidy():
    context = build_offer_pdf_context(
        template={
            "name": "PV 6 kWp",
            "product_type": "PV",
            "price_net_pln": 30000,
            "vat_rate": 8,
            "subsidy_amount_pln": 10000,
        },
        seller_profile={"company_name": "Firma OZE"},
        client={"Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa"},
    )

    assert context["subsidy_amount"] == "10 000 PLN"
    assert context["primary_price"] == "22 400 PLN"


def test_render_offer_pdf_returns_pdf_bytes():
    pdf = render_offer_pdf(
        template={
            "name": "PV 6 kWp",
            "product_type": "PV",
            "price_net_pln": 30000,
            "vat_rate": 8,
        },
        seller_profile={"company_name": "Firma OZE"},
        client={"Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa"},
    )

    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 200


def test_offer_pdf_uses_short_price_label():
    source = Path("shared/offers/pdf.py").read_text()

    assert "Cena klienta" not in source


def test_reportlab_pdf_uses_generated_pv_storage_watermark():
    source = Path("shared/offers/pdf.py").read_text()

    assert "pv-storage-watermark.png" in source
    assert Path("shared/offers/assets/pv-storage-watermark.png").exists()


def test_reportlab_pdf_registers_polish_capable_fonts():
    source = Path("shared/offers/pdf.py").read_text()

    assert "NotoSans-Regular.ttf" in source
    assert Path("shared/offers/assets/NotoSans-Regular.ttf").exists()
    assert Path("shared/offers/assets/NotoSans-Bold.ttf").exists()


def test_reportlab_pdf_uses_dark_neutral_palette_without_seller_accent():
    source = Path("shared/offers/pdf.py").read_text()

    assert "#151917" in source
    assert "_hex_to_rgb" not in source
    assert 'context["accent_color"]' not in source
