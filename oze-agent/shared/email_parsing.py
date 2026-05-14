"""Shared email parsing helpers for CRM and offer flows."""

import re

EMAIL_RE = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)+(?![\w.+-])", re.I)
EMAIL_TOKEN_RE = re.compile(r"\S+@\S+")
VALID_EMAIL_RE = re.compile(r"^[^@\s;<>]+@[^@\s;<>]+\.[^@\s;<>]+$", re.I)

_SPOKEN_AT_RE = re.compile(r"\bma[łl]pa\b", re.I)
_SPOKEN_DOT_RE = re.compile(r"\bkropka\b", re.I)


def normalize_email(value: str) -> str:
    return (value or "").strip().strip(".,;:<>[]()").lower()


def normalize_spoken_email_text(text: str) -> str:
    """Convert common Polish spoken email tokens into parseable email text."""
    normalized = text or ""
    normalized = _SPOKEN_AT_RE.sub(" @ ", normalized)
    normalized = _SPOKEN_DOT_RE.sub(" . ", normalized)
    return re.sub(r"\s*([@.])\s*", r"\1", normalized)


def is_valid_email(value: str) -> bool:
    return bool(VALID_EMAIL_RE.match(normalize_email(value)))


def extract_email_addresses(text: str) -> list[str]:
    seen: set[str] = set()
    addresses: list[str] = []
    normalized_text = normalize_spoken_email_text(text or "")
    for match in EMAIL_RE.findall(normalized_text):
        email = normalize_email(match)
        if email and email not in seen:
            seen.add(email)
            addresses.append(email)
    return addresses
