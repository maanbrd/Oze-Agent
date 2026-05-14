"""Deterministic parser for short CRM field-update replies."""

from dataclasses import dataclass
import re

from shared.email_parsing import extract_email_addresses, normalize_spoken_email_text


@dataclass(frozen=True)
class ClientFieldUpdate:
    updates: dict[str, str]


_PHONE_RE = re.compile(r"(?<!\d)(?:\+?48[\s-]?)?(?:\d[\s-]?){9}(?!\d)")
_NOTE_RE = re.compile(
    r"^\s*(?:notatka|notatki)\s*:|^\s*(?:dodaj|dopisz|zapisz)\s+notatk[ęe]\s*:",
    re.IGNORECASE,
)


def _strip_value(text: str, pattern: str) -> str:
    return re.sub(pattern, "", text, count=1, flags=re.IGNORECASE).strip(" :,-.;")


def _normalize_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if len(digits) == 11 and digits.startswith("48"):
        digits = digits[2:]
    return digits if len(digits) == 9 else ""


def _normalize_product(value: str) -> str:
    text = value.strip()
    lower = text.casefold()
    has_pv = bool(re.search(r"\bpv\b|fotowolta", lower))
    has_storage = "magazyn" in lower
    if has_pv and has_storage:
        return "PV + Magazyn energii"
    if has_pv:
        return "PV"
    if has_storage:
        return "Magazyn energii"
    return text


def is_explicit_note_request(message_text: str) -> bool:
    return bool(_NOTE_RE.search(message_text or ""))


def parse_client_field_update(message_text: str) -> ClientFieldUpdate | None:
    text = (message_text or "").strip()
    if not text:
        return None

    # Field updates win over note routing. Only explicit note markers below
    # are excluded after CRM field prefixes fail to match.
    email = next(iter(extract_email_addresses(text)), None)

    if email and re.match(r"^\s*(?:e-?mail|mail)\b", text, re.IGNORECASE):
        return ClientFieldUpdate({"Email": email})

    phone_match = _PHONE_RE.search(text)
    if phone_match and re.match(r"^\s*(?:tel\.?|telefon|nr|numer)\b", text, re.IGNORECASE):
        phone = _normalize_phone(phone_match.group(0))
        if phone:
            return ClientFieldUpdate({"Telefon": phone})

    source_match = re.match(
        r"^\s*(?:źródło\s+pozyskania|zrodlo\s+pozyskania|źródło|zrodlo)\b",
        text,
        re.IGNORECASE,
    )
    if source_match:
        value = text[source_match.end():].strip(" :,-.;")
        return ClientFieldUpdate({"Źródło pozyskania": value}) if value else None

    address_match = re.match(r"^\s*(?:adres|ul\.?|ulica)\b", text, re.IGNORECASE)
    if address_match:
        value = text[address_match.end():].strip(" :,-.;")
        return ClientFieldUpdate({"Adres": value}) if value else None

    product_match = re.match(r"^\s*(?:produkt|temat)\b", text, re.IGNORECASE)
    if product_match:
        value = _strip_value(text, r"^\s*(?:produkt|temat)\b")
        product = _normalize_product(value)
        return ClientFieldUpdate({"Produkt": product}) if product else None

    if is_explicit_note_request(text):
        return None

    # A bare email is a common post-save reply after the bot asked for missing
    # data; keep it deterministic and R1-safe.
    if email and normalize_spoken_email_text(text).strip().casefold() == email.casefold():
        return ClientFieldUpdate({"Email": email})

    return None
