"""Email parsing and formatting helpers for offer sending."""

import re
import unicodedata
from dataclasses import dataclass

EMAIL_RE = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)+(?![\w.+-])", re.I)
EMAIL_TOKEN_RE = re.compile(r"\S+@\S+")
VALID_EMAIL_RE = re.compile(r"^[^@\s;<>]+@[^@\s;<>]+\.[^@\s;<>]+$", re.I)


@dataclass(frozen=True)
class RecipientMergeResult:
    recipients: list[str]
    invalid_recipients: list[str]
    new_emails_for_sheets: list[str]


def normalize_email(value: str) -> str:
    return value.strip().strip(".,;:<>[]()").lower()


def is_valid_email(value: str) -> bool:
    return bool(VALID_EMAIL_RE.match(normalize_email(value)))


def extract_email_addresses(text: str) -> list[str]:
    seen: set[str] = set()
    addresses: list[str] = []
    for match in EMAIL_RE.findall(text or ""):
        email = normalize_email(match)
        if email and email not in seen:
            seen.add(email)
            addresses.append(email)
    return addresses


def _split_email_field(value: str) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in re.split(r"[;,\s]+", value) if part.strip()]


def _invalid_email_tokens(text: str) -> list[str]:
    invalid: list[str] = []
    for token in EMAIL_TOKEN_RE.findall(text or ""):
        normalized = normalize_email(token)
        if normalized and not is_valid_email(normalized) and normalized not in invalid:
            invalid.append(normalized)
    return invalid


def merge_offer_recipients(sheet_email_field: str, command_text: str = "") -> RecipientMergeResult:
    """Merge valid Sheets emails and valid command emails, tracking invalids."""
    recipients: list[str] = []
    invalid: list[str] = []
    sheet_valid: set[str] = set()

    for raw in _split_email_field(sheet_email_field):
        email = normalize_email(raw)
        if is_valid_email(email):
            if email not in recipients:
                recipients.append(email)
            sheet_valid.add(email)
        elif email not in invalid:
            invalid.append(email)

    command_valid = extract_email_addresses(command_text)
    for email in _invalid_email_tokens(command_text):
        if email not in invalid:
            invalid.append(email)

    new_for_sheets: list[str] = []
    for email in command_valid:
        if email not in recipients:
            recipients.append(email)
        if email not in sheet_valid and email not in new_for_sheets:
            new_for_sheets.append(email)

    return RecipientMergeResult(
        recipients=recipients,
        invalid_recipients=invalid,
        new_emails_for_sheets=new_for_sheets,
    )


def client_name_parts(client: dict) -> tuple[str, str]:
    full_name = (client.get("Imię i nazwisko") or client.get("name") or "").strip()
    parts = [p for p in re.split(r"\s+", full_name) if p]
    if len(parts) < 2:
        return full_name, ""
    return parts[0], parts[-1]


def salutation_for_client(client: dict) -> str:
    first_name, last_name = client_name_parts(client)
    if not first_name or not last_name:
        return "Dzień dobry"

    first_lower = first_name.lower()
    if first_lower in {"firma", "spółka", "spolka", "państwo", "panstwo"}:
        return "Dzień dobry"
    if last_name.isupper() or any(ch.isdigit() for ch in first_name + last_name):
        return "Dzień dobry"

    male_a_exceptions = {"kuba", "barnaba", "kosma", "bonawentura"}
    if first_lower.endswith("a") and first_lower not in male_a_exceptions:
        return f"Pani {last_name}"
    if first_lower[-1:].isalpha():
        return f"Panie {last_name}"
    return "Dzień dobry"


def sanitize_filename_part(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", ascii_text).strip("-")
    return re.sub(r"-{2,}", "-", cleaned) or "Oferta"
