"""PDF rendering for offer templates."""

from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path

from .pricing import calculate_price, format_pln

DISCLAIMER = (
    "Oferta ma charakter informacyjny. Szczegóły techniczne, dostępność "
    "komponentów i warunki realizacji wymagają potwierdzenia z handlowcem."
)
PDF_DARK_BACKGROUND = "#151917"
PDF_TEXT_WHITE = "#f4f6f4"
PDF_MUTED = "#aeb4b0"
PDF_QUIET = "#747a76"
PDF_RULE = "#343a36"
OFFER_ASSETS_DIR = Path(__file__).with_name("assets")
OFFER_WATERMARK_PATH = OFFER_ASSETS_DIR / "pv-storage-watermark.png"
OFFER_FONT_REGULAR_PATH = OFFER_ASSETS_DIR / "NotoSans-Regular.ttf"
OFFER_FONT_BOLD_PATH = OFFER_ASSETS_DIR / "NotoSans-Bold.ttf"
TEST_CLIENT = {
    "Imię i nazwisko": "Jan Testowy",
    "Miasto": "Warszawa",
}
_DAYS_PL = [
    "Poniedziałek",
    "Wtorek",
    "Środa",
    "Czwartek",
    "Piątek",
    "Sobota",
    "Niedziela",
]


def _display_date(value: date | None = None) -> str:
    current = value or date.today()
    return f"{current:%d.%m.%Y} ({_DAYS_PL[current.weekday()]})"


def _client_display(client: dict) -> dict:
    name = (client.get("Imię i nazwisko") or client.get("name") or "").strip()
    parts = name.split()
    return {
        "first_name": parts[0] if parts else "",
        "last_name": parts[-1] if len(parts) > 1 else "",
        "full_name": name,
        "city": client.get("Miasto") or client.get("city") or "",
    }


def build_offer_pdf_context(
    template: dict,
    seller_profile: dict | None,
    client: dict | None = None,
    today: date | None = None,
) -> dict:
    profile = seller_profile or {}
    client_data = _client_display(client or TEST_CLIENT)
    pricing = calculate_price(
        template.get("price_net_pln"),
        template.get("vat_rate"),
        template.get("subsidy_amount_pln"),
    )
    return {
        "template_name": template.get("name") or "Oferta",
        "product_type": template.get("product_type") or "",
        "company_name": profile.get("company_name") or "OZE Agent",
        "logo_path": profile.get("logo_path") or None,
        "logo_bytes": profile.get("logo_bytes") or None,
        "client": client_data,
        "date": _display_date(today),
        "net_price": format_pln(pricing.net_price_pln),
        "vat_rate": f"{pricing.vat_rate}%",
        "gross_price": format_pln(pricing.gross_price_pln),
        "subsidy_amount": (
            format_pln(pricing.subsidy_amount_pln)
            if pricing.subsidy_amount_pln is not None
            else None
        ),
        "primary_price": format_pln(pricing.client_price_pln),
        "components": _component_lines(template),
        "optional_terms": _optional_terms(template),
        "disclaimer": DISCLAIMER,
    }


def _component_lines(template: dict) -> list[str]:
    lines: list[str] = []
    if template.get("pv_power_kwp"):
        lines.append(f"Moc instalacji PV: {template['pv_power_kwp']} kWp")
    panel = " ".join(part for part in [template.get("panel_brand"), template.get("panel_model")] if part)
    if panel:
        lines.append(f"Panele: {panel}")
    inverter = " ".join(part for part in [template.get("inverter_brand"), template.get("inverter_model")] if part)
    if inverter:
        lines.append(f"Falownik: {inverter}")
    if template.get("storage_capacity_kwh"):
        lines.append(f"Pojemność magazynu: {template['storage_capacity_kwh']} kWh")
    storage = " ".join(part for part in [template.get("storage_brand"), template.get("storage_model")] if part)
    if storage:
        lines.append(f"Magazyn energii: {storage}")
    optional = [
        ("Konstrukcja", "construction"),
        ("Zabezpieczenia AC/DC", "protections_ac_dc"),
        ("Montaż", "installation"),
        ("Monitoring/EMS", "monitoring_ems"),
        ("Gwarancja", "warranty"),
    ]
    for label, key in optional:
        if template.get(key):
            lines.append(f"{label}: {template[key]}")
    return lines


def _optional_terms(template: dict) -> list[str]:
    labels = [
        ("Warunki płatności", "payment_terms"),
        ("Termin realizacji", "implementation_time"),
        ("Ważność oferty", "validity"),
    ]
    return [f"{label}: {template[key]}" for label, key in labels if template.get(key)]


def _reportlab_font_names() -> tuple[str, str]:
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        if OFFER_FONT_REGULAR_PATH.exists() and OFFER_FONT_BOLD_PATH.exists():
            registered = set(pdfmetrics.getRegisteredFontNames())
            if "OZENotoSans" not in registered:
                pdfmetrics.registerFont(TTFont("OZENotoSans", str(OFFER_FONT_REGULAR_PATH)))
            if "OZENotoSans-Bold" not in registered:
                pdfmetrics.registerFont(TTFont("OZENotoSans-Bold", str(OFFER_FONT_BOLD_PATH)))
            return "OZENotoSans", "OZENotoSans-Bold"
    except Exception:
        pass
    return "Helvetica", "Helvetica-Bold"


def render_offer_pdf(
    template: dict,
    seller_profile: dict | None,
    client: dict | None = None,
    today: date | None = None,
) -> bytes:
    context = build_offer_pdf_context(template, seller_profile, client, today)
    try:
        return _render_reportlab_pdf(context)
    except Exception:
        return _render_minimal_pdf(context)


def _render_reportlab_pdf(context: dict) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=22 * mm,
        rightMargin=22 * mm,
        topMargin=20 * mm,
        bottomMargin=18 * mm,
    )

    def draw_offer_background(canvas, _doc):
        canvas.saveState()
        try:
            canvas.setFillColor(colors.HexColor(PDF_DARK_BACKGROUND))
            canvas.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)
            if OFFER_WATERMARK_PATH.exists():
                if hasattr(canvas, "setFillAlpha"):
                    canvas.setFillAlpha(0.2)
                canvas.drawImage(
                    str(OFFER_WATERMARK_PATH),
                    0,
                    0,
                    width=A4[0],
                    height=A4[1],
                    preserveAspectRatio=False,
                    mask="auto",
                )
        except Exception:
            pass
        finally:
            canvas.restoreState()

    text_white = colors.HexColor(PDF_TEXT_WHITE)
    muted = colors.HexColor(PDF_MUTED)
    quiet = colors.HexColor(PDF_QUIET)
    regular_font_name, bold_font_name = _reportlab_font_names()
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleOZE", parent=styles["Title"], fontName=bold_font_name, fontSize=24, leading=29, textColor=text_white))
    styles.add(ParagraphStyle(name="H2OZE", parent=styles["Heading2"], fontName=bold_font_name, fontSize=13, leading=17, textColor=text_white, spaceBefore=12, spaceAfter=6))
    styles.add(ParagraphStyle(name="BodyOZE", parent=styles["BodyText"], fontName=regular_font_name, fontSize=10.5, leading=15, textColor=text_white))
    styles.add(ParagraphStyle(name="MutedOZE", parent=styles["BodyText"], fontName=regular_font_name, fontSize=10.5, leading=15, textColor=muted))
    styles.add(ParagraphStyle(name="QuietOZE", parent=styles["BodyText"], fontName=regular_font_name, fontSize=9, leading=13, textColor=quiet))
    styles.add(ParagraphStyle(name="PriceOZE", parent=styles["Title"], fontName=bold_font_name, fontSize=28, leading=32, textColor=text_white))

    story = []
    if context.get("logo_bytes"):
        try:
            from reportlab.platypus import Image

            story.extend([Image(BytesIO(context["logo_bytes"]), width=42 * mm, height=18 * mm, kind="proportional"), Spacer(1, 8)])
        except Exception:
            pass
    story.extend([
        Paragraph(context["company_name"], styles["BodyOZE"]),
        Spacer(1, 8),
        Paragraph(context["template_name"], styles["TitleOZE"]),
        Spacer(1, 14),
        Paragraph("Cena", styles["MutedOZE"]),
        Paragraph(context["primary_price"], styles["PriceOZE"]),
        Spacer(1, 10),
    ])

    client = context["client"]
    rows = [
        ["Klient", client["full_name"]],
        ["Miasto", client["city"]],
        ["Data", context["date"]],
    ]
    story.append(_table(rows, Table, TableStyle, colors, mm, regular_font_name, bold_font_name))
    story.extend([Spacer(1, 12), Paragraph("Cena", styles["H2OZE"])])
    price_rows = [
        ["Cena netto", context["net_price"]],
        ["VAT", context["vat_rate"]],
        ["Cena brutto", context["gross_price"]],
    ]
    if context["subsidy_amount"]:
        price_rows.append(["Szacowane dofinansowanie", context["subsidy_amount"]])
        price_rows.append(["Cena po dopłacie", context["primary_price"]])
    story.append(_table(price_rows, Table, TableStyle, colors, mm, regular_font_name, bold_font_name))

    if context["components"]:
        story.extend([Spacer(1, 12), Paragraph("Zakres zestawu", styles["H2OZE"])])
        for line in context["components"]:
            story.append(Paragraph(f"• {line}", styles["BodyOZE"]))
    if context["optional_terms"]:
        story.extend([Spacer(1, 12), Paragraph("Warunki", styles["H2OZE"])])
        for line in context["optional_terms"]:
            story.append(Paragraph(f"• {line}", styles["BodyOZE"]))

    story.extend([Spacer(1, 20), Paragraph(context["disclaimer"], styles["QuietOZE"])])
    doc.build(story, onFirstPage=draw_offer_background, onLaterPages=draw_offer_background)
    return buffer.getvalue()


def _table(rows, Table, TableStyle, colors, mm, regular_font_name: str, bold_font_name: str):
    table = Table(rows, colWidths=[78 * mm, 76 * mm])
    table.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor(PDF_RULE)),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor(PDF_MUTED)),
        ("TEXTCOLOR", (1, 0), (-1, -1), colors.HexColor(PDF_TEXT_WHITE)),
        ("FONTNAME", (0, 0), (0, -1), bold_font_name),
        ("FONTNAME", (1, 0), (-1, -1), regular_font_name),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("LEADING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def _render_minimal_pdf(context: dict) -> bytes:
    def _text(value: str, x: int, y: int, size: int = 10, font: str = "F1") -> str:
        safe = (
            value.encode("latin-1", "replace")
            .decode("latin-1")
            .replace("(", "[")
            .replace(")", "]")
        )
        return f"BT /{font} {size} Tf {x} {y} Td ({safe}) Tj ET"

    lines = [
        _text(context["company_name"], 48, 760, 11, "F2"),
        _text(context["template_name"], 48, 716, 22, "F2"),
        _text("Cena", 392, 735, 9, "F2"),
        _text(context["primary_price"], 392, 708, 20, "F2"),
        _text("Klient", 48, 625, 9, "F2"),
        _text(context["client"]["full_name"], 165, 625, 10),
        _text("Miasto", 48, 604, 9, "F2"),
        _text(context["client"]["city"], 165, 604, 10),
        _text("Data", 48, 583, 9, "F2"),
        _text(context["date"], 165, 583, 10),
        _text("Cena netto", 48, 535, 9, "F2"),
        _text(context["net_price"], 300, 535, 10),
        _text("VAT", 48, 514, 9, "F2"),
        _text(context["vat_rate"], 300, 514, 10),
        _text("Cena brutto", 48, 493, 9, "F2"),
        _text(context["gross_price"], 300, 493, 10),
    ]
    y = 472
    if context["subsidy_amount"]:
        lines.extend([
            _text("Szacowane dofinansowanie", 48, y, 9, "F2"),
            _text(context["subsidy_amount"], 300, y, 10),
        ])
        y -= 21
    for item in context["components"][:12]:
        lines.append(_text(f"- {item}", 58, y, 9))
        y -= 15
    lines.append(_text(context["disclaimer"], 48, 62, 8))
    stream = "\n".join(lines)
    objects = [
        "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj",
        "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj",
        "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> /Contents 6 0 R >> endobj",
        "4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj",
        "5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >> endobj",
        f"6 0 obj << /Length {len(stream.encode('latin-1'))} >> stream\n{stream}\nendstream endobj",
    ]
    body = "\n".join(objects)
    return f"%PDF-1.4\n{body}\n%%EOF\n".encode("latin-1")
