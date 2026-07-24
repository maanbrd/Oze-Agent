"""Stable client references for Sheets-backed CRM mutations.

Sheets row numbers are location hints, not identity.  A ClientRef captures the
business identity visible at confirmation time and resolves the current row
immediately before a delayed mutation or send.
"""

from __future__ import annotations

import re

from shared.google_sheets import get_all_clients_or_raise
from shared.search import normalize_polish


class ClientIdentityError(RuntimeError):
    """Raised when a stable client reference cannot be resolved safely."""


def _text(value: object) -> str:
    return str(value or "").strip()


def _normal_text(value: object) -> str:
    return " ".join(normalize_polish(_text(value)).split())


def _phone(value: object) -> str:
    return re.sub(r"\D", "", _text(value))


def _email(value: object) -> str:
    return _text(value).lower()


def build_client_ref(row: dict) -> dict:
    """Build a serializable identity snapshot from a Sheets client row."""
    return {
        "version": 1,
        "row_hint": row.get("_row"),
        "name": _normal_text(row.get("Imię i nazwisko")),
        "city": _normal_text(row.get("Miasto", row.get("Miejscowość", ""))),
        "phone": _phone(row.get("Telefon")),
        "email": _email(row.get("Email")),
    }


def _matches_base(row: dict, ref: dict) -> bool:
    name = _normal_text(row.get("Imię i nazwisko"))
    city = _normal_text(row.get("Miasto", row.get("Miejscowość", "")))
    return bool(ref.get("name")) and name == ref.get("name") and city == ref.get("city", "")


def _matches_anchor(row: dict, ref: dict) -> bool:
    phone = ref.get("phone") or ""
    email = ref.get("email") or ""
    if phone and _phone(row.get("Telefon")) != phone:
        return False
    if email and _email(row.get("Email")) != email:
        return False
    return True


async def resolve_client_ref(user_id: str, ref: dict) -> dict:
    """Resolve a ClientRef to exactly one current Sheets row.

    A row hint is deliberately never trusted by itself.  Strong anchors
    (phone/email) must still match when present, and name+city-only references
    must be unique across the live sheet.
    """
    if not isinstance(ref, dict) or not ref.get("name"):
        raise ClientIdentityError("client_identity_invalid")

    rows = await get_all_clients_or_raise(user_id)
    base_matches = [row for row in rows if _matches_base(row, ref)]
    anchored = [row for row in base_matches if _matches_anchor(row, ref)]

    if not anchored:
        raise ClientIdentityError("client_identity_not_found")
    if len(anchored) != 1:
        raise ClientIdentityError("client_identity_ambiguous")
    return anchored[0]
