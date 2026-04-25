"""Pure-Python parser for OZE-Agent confirmation card text.

Converts a card message body (plain text from the bot) into a structured
`ParsedCard` so scenario assertions don't have to use raw substring
matches. The parser is intentionally lenient — bot wording may drift,
and we want one source of truth for "what does this card contain".

Card shapes covered (see `agent_behavior_spec_v5.md` §10 + INTENCJE_MVP §4):

  - add_client:         "📋 Zapisuję klienta:" / "📋 {name}, {addr}, {city}"
  - add_note Flow A:    "📝 {name}, {city}: dodaj notatkę ..."
  - add_note Flow B:    "📝 {name}, {city}:" + bullets
  - change_status:      "📊 {name}, {city}\\nStatus: {old} → {new}"
  - add_meeting:        "📅 Spotkanie:" / "📞 Telefon:" / "✉️ ..."
  - conflict:           "⚠️ Konflikt:" + body + 3-button
  - duplicate routing:  short text + [Nowy] [Aktualizuj] (no card icon)
  - read-only show_*:   "📋 {name} — {addr}, {city}\\n..." (no card icon prefix line)

The parser does best-effort field extraction and surfaces what it could
not parse via `parsed.unparsed_lines`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

# Icons we consider "card headers". Order matters for detection (longest first).
_CARD_ICONS = ("📋", "📝", "📊", "📅", "📞", "✉️", "⚠️")

# Lines starting with these labels are treated as `key: value` fields.
# Kept loose — bot may add new labels; unmatched lines fall into `notes_lines`.
_KNOWN_FIELD_PREFIXES = (
    "Produkt:", "Tel.", "Telefon:", "Email:", "Status:", "Data:",
    "Adres:", "Typ:", "Notatki:", "Notatka:", "Calendar:",
    "Ostatni kontakt:", "Następny krok:",
)

_MISSING_PREFIX = "❓ Brakuje:"
_STATUS_TRANSITION_RE = re.compile(r"Status:\s*(.+?)\s*→\s*(.+?)\s*$")


@dataclass
class ParsedCard:
    """Structured view of a bot card message."""

    icon: Optional[str] = None
    header_line: str = ""
    fields: dict[str, str] = field(default_factory=dict)
    notes_lines: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    status_transition: Optional[tuple[str, str]] = None
    button_labels: list[str] = field(default_factory=list)
    bullets: list[str] = field(default_factory=list)
    unparsed_lines: list[str] = field(default_factory=list)
    raw_text: str = ""

    def has_three_button(self) -> bool:
        """True iff the card carries the canonical mutation card buttons.

        Tolerant: passes if either the canonical icons (✅ / ➕ / ❌) all
        appear in the labels, OR the canonical Polish words ("zapisać",
        "dopisać", "anulować") all appear. This accommodates word-only
        button label variants that are still spec-compliant.
        """
        if not self.button_labels:
            return False
        joined = "  ".join(self.button_labels).lower()
        icon_match = all(marker in joined for marker in ("✅", "➕", "❌"))
        word_match = all(
            word in joined for word in ("zapisać", "dopisać", "anulować")
        )
        return icon_match or word_match

    def has_routing_buttons(self) -> bool:
        """True iff the card carries [Nowy] / [Aktualizuj] duplicate routing."""
        labels = {lbl.strip().lower() for lbl in self.button_labels}
        return "nowy" in labels and "aktualizuj" in labels

    def is_read_only(self) -> bool:
        """A read-only message has no inline buttons at all."""
        return not self.button_labels


# ── Internal helpers ──────────────────────────────────────────────────────────


def _strip_known_icon(line: str) -> tuple[Optional[str], str]:
    """If the line starts with a known card icon, peel it off and return
    (icon, remainder). Otherwise (None, line)."""
    stripped = line.lstrip()
    for icon in _CARD_ICONS:
        if stripped.startswith(icon):
            rest = stripped[len(icon):].lstrip()
            return icon, rest
    return None, line


def _parse_field_line(line: str) -> Optional[tuple[str, str]]:
    """Match 'Key: value' (with various known prefixes). Allows trailing
    punctuation. Returns (key_normalised, value)."""
    for prefix in _KNOWN_FIELD_PREFIXES:
        if line.startswith(prefix):
            # 'Tel. 600 100 200' has no colon — treat 'Tel.' as the key.
            if prefix.endswith("."):
                key = prefix.rstrip(".")
                value = line[len(prefix):].strip()
                return key, value
            else:
                key = prefix.rstrip(":")
                value = line[len(prefix):].strip()
                return key, value
    return None


def _parse_missing_line(line: str) -> Optional[list[str]]:
    """Extract missing fields list from '❓ Brakuje: a, b, c'."""
    if not line.startswith(_MISSING_PREFIX):
        return None
    payload = line[len(_MISSING_PREFIX):].strip()
    if not payload:
        return []
    return [p.strip() for p in payload.split(",") if p.strip()]


def _parse_status_transition(line: str) -> Optional[tuple[str, str]]:
    """Match 'Status: X → Y' returning (X, Y) or None."""
    m = _STATUS_TRANSITION_RE.search(line)
    if m:
        return m.group(1), m.group(2)
    return None


# ── Public API ────────────────────────────────────────────────────────────────


def parse_card(text: str, button_labels: list[str] | None = None) -> ParsedCard:
    """Parse a bot card message body into a structured ParsedCard.

    `button_labels` — flat list of inline keyboard labels captured by the
    harness. Pass `[]` for read-only messages.
    """
    if button_labels is None:
        button_labels = []
    card = ParsedCard(raw_text=text, button_labels=list(button_labels))

    if not text:
        return card

    raw_lines = [ln.rstrip() for ln in text.splitlines()]
    lines = [ln for ln in raw_lines if ln.strip()]
    if not lines:
        return card

    # First non-empty line: detect icon + header.
    first = lines[0]
    icon, remainder = _strip_known_icon(first)
    card.icon = icon
    card.header_line = remainder.strip()
    consumed_first = True

    for raw_line in lines[1:] if consumed_first else lines:
        line = raw_line.strip()
        # Bullets — common in compound card / Calendar conflict line.
        if line.startswith("•"):
            card.bullets.append(line[1:].strip())
            continue
        # Status transition (may also be a `Status: ` field — we capture both).
        st = _parse_status_transition(line)
        if st:
            card.status_transition = st
        # Missing fields list.
        missing = _parse_missing_line(line)
        if missing is not None:
            card.missing = missing
            continue
        # Known field "Key: value".
        kv = _parse_field_line(line)
        if kv:
            card.fields[kv[0]] = kv[1]
            continue
        # Otherwise treat as free-form notes line.
        card.notes_lines.append(line)
        # Mark anything we couldn't classify so callers can spot drift.
        if not st and not line.startswith(("📋", "📝", "📊", "📅", "📞", "✉️", "⚠️")):
            card.unparsed_lines.append(line)

    return card


# ── Convenience: detect cancel / not-found / vision-only / post-mvp markers ──

CANCEL_TEXT_MARKERS = ("Anulowane", "🫡 Anulowane", "⚠️ Anulowane")
NOT_FOUND_MARKERS = ("Nie znalazłem", "nie znalazłem")
NOT_UNDERSTOOD_MARKERS = ("Nie zrozumiałem", "nie zrozumiałem")
POST_MVP_MARKERS = ("post-MVP", "post mvp", "post-mvp")
VISION_ONLY_MARKERS = ("vision-only", "vision only", "poza aktualnym MVP scope")
PAST_DATE_MARKERS = ("przeszłości", "Data ", "podaj datę przyszłą")


def is_cancel_message(text: str) -> bool:
    return any(m in text for m in CANCEL_TEXT_MARKERS)


def is_not_found(text: str) -> bool:
    return any(m in text for m in NOT_FOUND_MARKERS)


def is_not_understood(text: str) -> bool:
    return any(m in text for m in NOT_UNDERSTOOD_MARKERS)


def is_post_mvp_reply(text: str) -> bool:
    return any(m in text.lower() for m in (m.lower() for m in POST_MVP_MARKERS))


def is_vision_only_reply(text: str) -> bool:
    return any(m in text.lower() for m in (m.lower() for m in VISION_ONLY_MARKERS))
