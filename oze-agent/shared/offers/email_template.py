"""Email body templates for offer sending."""

import re
from dataclasses import dataclass, field

from .pricing import calculate_price, format_pln

DEFAULT_EMAIL_BODY_TEMPLATE = """Dzień dobry,

przesyłam ofertę: {{Nazwa oferty}}.
Cena: {{Cena}}.

W razie pytań jestem do dyspozycji.

{{Firma}}"""

EMAIL_VARIABLES = [
    {"token": "{{Imię i nazwisko}}", "label": "Imię i nazwisko", "source": "Sheets"},
    {"token": "{{Miasto}}", "label": "Miasto", "source": "Sheets"},
    {"token": "{{Email}}", "label": "Email", "source": "Sheets"},
    {"token": "{{Telefon}}", "label": "Telefon", "source": "Sheets"},
    {"token": "{{Produkt}}", "label": "Produkt", "source": "Sheets"},
    {"token": "{{Status}}", "label": "Status", "source": "Sheets"},
    {"token": "{{Następny krok}}", "label": "Następny krok", "source": "Sheets"},
    {"token": "{{Data następnego kroku}}", "label": "Data następnego kroku", "source": "Sheets"},
    {"token": "{{Firma}}", "label": "Firma", "source": "Profil"},
    {"token": "{{Nazwa oferty}}", "label": "Nazwa oferty", "source": "Oferta"},
    {"token": "{{Cena}}", "label": "Cena", "source": "Oferta"},
]

TOKEN_RE = re.compile(r"{{\s*([^{}]+?)\s*}}")
ALLOWED_VARIABLES = {item["label"] for item in EMAIL_VARIABLES}


@dataclass(frozen=True)
class EmailTemplateValidation:
    is_valid: bool
    unknown_variables: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RenderedEmailTemplate:
    body: str
    missing_variables: list[str] = field(default_factory=list)


def extract_email_template_variables(template_text: str) -> list[str]:
    seen: set[str] = set()
    variables: list[str] = []
    for match in TOKEN_RE.finditer(template_text or ""):
        variable = match.group(1).strip()
        if variable and variable not in seen:
            seen.add(variable)
            variables.append(variable)
    return variables


def validate_email_template(template_text: str) -> EmailTemplateValidation:
    unknown = [variable for variable in extract_email_template_variables(template_text) if variable not in ALLOWED_VARIABLES]
    return EmailTemplateValidation(is_valid=not unknown, unknown_variables=unknown)


def _template_price(template: dict) -> str:
    price = calculate_price(
        template.get("price_net_pln") or 0,
        template.get("vat_rate") or 8,
        template.get("subsidy_amount_pln"),
    )
    return format_pln(price.client_price_pln)


def _value_for_variable(variable: str, *, client: dict, template: dict, seller_profile: dict) -> str:
    if variable == "Firma":
        return str(seller_profile.get("company_name") or "").strip()
    if variable == "Nazwa oferty":
        return str(template.get("name") or "").strip()
    if variable == "Cena":
        return _template_price(template)
    if variable == "Produkt":
        return str(client.get("Produkt") or template.get("product_type") or "").strip()
    return str(client.get(variable) or "").strip()


def render_email_template(
    template_text: str | None,
    *,
    client: dict,
    template: dict,
    seller_profile: dict | None,
) -> RenderedEmailTemplate:
    source = (template_text or DEFAULT_EMAIL_BODY_TEMPLATE).strip()
    profile = seller_profile or {}
    missing: list[str] = []

    def replace(match: re.Match[str]) -> str:
        variable = match.group(1).strip()
        if variable not in ALLOWED_VARIABLES:
            return match.group(0)
        value = _value_for_variable(variable, client=client, template=template, seller_profile=profile)
        if not value and variable not in missing:
            missing.append(variable)
        return value

    return RenderedEmailTemplate(body=TOKEN_RE.sub(replace, source), missing_variables=missing)
