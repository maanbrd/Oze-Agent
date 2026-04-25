"""Common assertion helpers for E2E scenarios.

Each helper returns `(ok: bool, detail: str)` so the scenario can wrap
into `result.add(name, ok, detail)` without committing to a specific
outcome shape. Helpers do NOT raise.

Many helpers operate on `_ObservedMessage` (from harness.py). For the few
that operate on plain text, callers can pass `message.text` directly.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from tests_e2e.card_parser import ParsedCard, parse_card

if TYPE_CHECKING:
    from tests_e2e.harness import _ObservedMessage


# ── Card structure ───────────────────────────────────────────────────────────


def assert_three_button_card(message: "_ObservedMessage") -> tuple[bool, str]:
    """Verify the message carries the canonical mutation 3-button keyboard.

    Spec: `[✅ Zapisać] [➕ Dopisać] [❌ Anulować]`. Tolerant — the assertion
    passes if EITHER the icon set (✅/➕/❌) OR the word set
    (Zapisać/Dopisać/Anulować) is present, so emoji-stripping label
    variants still satisfy the structural check.
    """
    card = parse_card(message.text, message.button_labels)
    if card.has_three_button():
        return True, f"3-button card found, labels={message.button_labels}"
    return False, (
        f"3-button mutation card expected (icons ✅/➕/❌ OR words "
        f"Zapisać/Dopisać/Anulować); got button_labels={message.button_labels!r}"
    )


def assert_no_buttons(message: "_ObservedMessage") -> tuple[bool, str]:
    """Verify message has no inline keyboard (read-only intent)."""
    if not message.button_labels:
        return True, "no buttons (read-only)"
    return False, (
        f"expected no buttons (read-only intent); "
        f"got button_labels={message.button_labels!r}"
    )


def assert_routing_card_nowy_aktualizuj(message: "_ObservedMessage") -> tuple[bool, str]:
    """Verify duplicate-resolution card has [Nowy] / [Aktualizuj] buttons."""
    card = parse_card(message.text, message.button_labels)
    if card.has_routing_buttons():
        return True, f"routing buttons present, labels={message.button_labels}"
    return False, (
        f"expected [Nowy] / [Aktualizuj] routing buttons; "
        f"got button_labels={message.button_labels!r}"
    )


# ── Date / format ────────────────────────────────────────────────────────────


# DD.MM.YYYY (Day) — Day uses Polish weekday names from formatting.py.
_PL_WEEKDAY_RE = (
    r"poniedziałek|wtorek|środa|czwartek|piątek|sobota|niedziela|"
    r"Poniedziałek|Wtorek|Środa|Czwartek|Piątek|Sobota|Niedziela"
)
_PL_DATE_PATTERN = re.compile(
    rf"\b\d{{2}}\.\d{{2}}\.\d{{4}}\s*\(\s*({_PL_WEEKDAY_RE})\s*\)"
)
_ISO_DATE_PATTERN = re.compile(r"\b\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2})?\b")
_EXCEL_SERIAL_PATTERN = re.compile(r"\b4[0-9]{4}\b")  # 40000–49999 plausible date serials


def assert_pl_date_format(text: str) -> tuple[bool, str]:
    """All visible dates must be DD.MM.YYYY (Dzień).

    PASS conditions:
    - At least one PL-format date is present, AND
    - No ISO-format date is present, AND
    - No bare Excel serial date is present.

    Returns FAIL with detail if any of the negative patterns appears OR
    if there are zero PL dates and the text *looks* like it should have
    dates (heuristic: contains a 4-digit year).
    """
    iso_hit = _ISO_DATE_PATTERN.search(text)
    excel_hit = _EXCEL_SERIAL_PATTERN.search(text)
    pl_hit = _PL_DATE_PATTERN.search(text)

    if iso_hit:
        return False, f"ISO-format date leaked: {iso_hit.group(0)!r}"
    if excel_hit:
        return False, f"Excel serial date leaked: {excel_hit.group(0)!r}"

    # Heuristic: if no 4-digit year appears at all, treat as "no dates expected".
    has_year = re.search(r"\b\d{4}\b", text)
    if has_year and not pl_hit:
        return False, "year present but no DD.MM.YYYY (Dzień) format found"
    return True, "PL date format OK" if pl_hit else "no dates expected, OK"


# ── Tone / banned phrases ────────────────────────────────────────────────────


_BANNED_PHRASES = (
    "oczywiście",
    "z przyjemnością",
    "na podstawie twojej wiadomości",
    "na podstawie twojego",
    "rozumiem twoją frustrację",
    "rozumiem pana",
    "powodzenia!",
    "daj znać jak coś",
    "czy mogę jeszcze w czymś pomóc",
)


def assert_no_banned_phrases(text: str) -> tuple[bool, str]:
    """Verify response does not contain corporate-bot phrases.

    Match is case-insensitive substring. Returns the offending phrase
    in the detail when failing.
    """
    lo = text.lower()
    for phrase in _BANNED_PHRASES:
        if phrase in lo:
            return False, f"banned phrase present: {phrase!r}"
    return True, "no banned phrases"


# ── Internal-fields leak ─────────────────────────────────────────────────────


_INTERNAL_LEAK_MARKERS = ("_row", "_sheet_id", "google_sheets_id", "spreadsheetId")


def assert_no_internal_leak(text: str) -> tuple[bool, str]:
    """Verify text doesn't expose internal fields (`_row`, sheet ids, etc.)."""
    for marker in _INTERNAL_LEAK_MARKERS:
        if marker in text:
            return False, f"internal field leaked: {marker!r}"
    return True, "no internal fields leaked"


# ── Cancel reply ─────────────────────────────────────────────────────────────


def assert_cancel_reply(message: "_ObservedMessage") -> tuple[bool, str]:
    """Verify the cancel reply: contains 'Anulowane' and is short (1-2 lines).

    Spec calls for 1 line `🫡 Anulowane.` Some code paths emit
    `⚠️ Anulowane.` — same semantic, accepted as PASS. Stricter
    emoji-exact match should use a `known_drift` tag.
    """
    text = message.text
    if "Anulowane" not in text:
        return False, f"expected 'Anulowane' in reply; got {text!r}"
    line_count = len([ln for ln in text.splitlines() if ln.strip()])
    if line_count > 2:
        return False, f"cancel reply too long ({line_count} lines): {text!r}"
    return True, f"cancel reply OK ({line_count} line(s))"


# ── Card field presence ──────────────────────────────────────────────────────


def assert_missing_field_listed(card: ParsedCard, expected_field: str) -> tuple[bool, str]:
    """Verify a specific field appears in the card's '❓ Brakuje:' list."""
    lo_expected = expected_field.lower()
    for m in card.missing:
        if lo_expected in m.lower():
            return True, f"'{expected_field}' present in missing: {card.missing}"
    return False, f"'{expected_field}' NOT in missing list: {card.missing}"


def assert_field_value(
    card: ParsedCard, field_key: str, expected_substring: str
) -> tuple[bool, str]:
    """Verify a parsed card field contains the expected substring."""
    actual = card.fields.get(field_key)
    if actual is None:
        return False, f"field '{field_key}' missing from card. fields={card.fields}"
    if expected_substring.lower() in actual.lower():
        return True, f"field '{field_key}' contains '{expected_substring}'"
    return False, (
        f"field '{field_key}'='{actual}' does NOT contain '{expected_substring}'"
    )
