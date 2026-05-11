"""Offer template readiness validation."""

from dataclasses import dataclass

PRODUCT_PV = "PV"
PRODUCT_STORAGE = "Magazyn energii"
PRODUCT_HYBRID = "PV + Magazyn energii"
PRODUCT_TYPES = {PRODUCT_PV, PRODUCT_STORAGE, PRODUCT_HYBRID}


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    errors: list[str]


def _filled(template: dict, key: str) -> bool:
    value = template.get(key)
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return value != ""


def _positive_number(template: dict, key: str) -> bool:
    try:
        return float(template.get(key) or 0) > 0
    except (TypeError, ValueError):
        return False


def _vat_valid(template: dict) -> bool:
    try:
        return int(template.get("vat_rate")) in (8, 23)
    except (TypeError, ValueError):
        return False


def _requires_pv(product_type: str) -> bool:
    return product_type in (PRODUCT_PV, PRODUCT_HYBRID)


def _requires_storage(product_type: str) -> bool:
    return product_type in (PRODUCT_STORAGE, PRODUCT_HYBRID)


def validate_offer_template(template: dict) -> ValidationResult:
    """Validate whether a template can be published as a ready offer."""
    errors: list[str] = []
    product_type = (template.get("product_type") or "").strip()

    if not _filled(template, "name"):
        errors.append("Brakuje nazwy oferty.")
    if product_type not in PRODUCT_TYPES:
        errors.append("Wybierz typ zestawu: PV, Magazyn energii albo PV + Magazyn energii.")
    if not _positive_number(template, "price_net_pln"):
        errors.append("Brakuje ceny netto zestawu.")
    if not _vat_valid(template):
        errors.append("VAT musi wynosić 8% albo 23%.")

    if _requires_pv(product_type):
        pv_fields = [
            ("pv_power_kwp", "moc PV kWp"),
            ("panel_brand", "panele marka"),
            ("panel_model", "panele model"),
            ("inverter_brand", "falownik marka"),
            ("inverter_model", "falownik model"),
        ]
        for key, label in pv_fields:
            if key == "pv_power_kwp":
                if not _positive_number(template, key):
                    errors.append(f"Brakuje pola PV: {label}.")
            elif not _filled(template, key):
                errors.append(f"Brakuje pola PV: {label}.")

    if _requires_storage(product_type):
        storage_fields = [
            ("storage_capacity_kwh", "pojemność kWh"),
            ("storage_brand", "magazyn marka"),
            ("storage_model", "magazyn model"),
        ]
        for key, label in storage_fields:
            if key == "storage_capacity_kwh":
                if not _positive_number(template, key):
                    errors.append(f"Brakuje pola magazynu: {label}.")
            elif not _filled(template, key):
                errors.append(f"Brakuje pola magazynu: {label}.")

    return ValidationResult(is_valid=not errors, errors=errors)


def has_pdf_minimum(template: dict) -> bool:
    """Return whether preview/test PDF has enough data to be meaningful."""
    product_type = (template.get("product_type") or "").strip()
    return (
        _filled(template, "name")
        and product_type in PRODUCT_TYPES
        and _positive_number(template, "price_net_pln")
        and _vat_valid(template)
    )
