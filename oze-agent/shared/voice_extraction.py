"""Structured field extraction for voice transcriptions.

This is a diagnostic adapter: it extracts key CRM fields from the transcript,
but does not mutate Google data and does not replace the normal text path.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from shared.claude_ai import call_claude_with_tools
from shared.email_parsing import normalize_spoken_email_value
from shared.observability import exception_type

logger = logging.getLogger(__name__)

WARSAW = ZoneInfo("Europe/Warsaw")
FALLBACK_EMPTY_INPUT = "empty_input"
FALLBACK_NO_TOOL = "no_tool"
FALLBACK_API_ERROR = "api_error"

FIELD_KEYS = (
    "intent",
    "name",
    "city",
    "phone",
    "email",
    "date",
    "time",
    "product_or_next_action",
)

VOICE_INTENTS = (
    "add_client",
    "show_client",
    "add_note",
    "change_status",
    "add_meeting",
    "show_day_plan",
    "send_offer",
    "general_question",
    "unknown",
)

_EXTRACTION_TOOL = {
    "name": "extract_voice_fields",
    "description": (
        "Extract key CRM fields recovered from a Polish OZE salesperson voice "
        "transcription. Return empty strings for fields not explicitly present."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "intent": {"type": "string", "enum": list(VOICE_INTENTS)},
            "name": {"type": "string"},
            "city": {"type": "string"},
            "phone": {"type": "string"},
            "email": {"type": "string"},
            "date": {"type": "string", "description": "YYYY-MM-DD if present or inferable."},
            "time": {"type": "string", "description": "HH:MM if present."},
            "product_or_next_action": {"type": "string"},
        },
        "additionalProperties": False,
    },
}


def _system_prompt() -> str:
    today = datetime.now(tz=WARSAW).date().isoformat()
    return f"""Jesteś technicznym ekstraktorem pól z polskiej transkrypcji głosówki handlowca OZE.

Zwróć tylko dane jawnie obecne lub jednoznacznie wynikające z tekstu.
Dzisiejsza data w Warszawie: {today}.

Pola:
- intent: add_client, show_client, add_note, change_status, add_meeting, show_day_plan, send_offer, general_question albo unknown
- name: imię i nazwisko klienta, jeśli jest
- city: miejscowość, jeśli jest
- phone: numer telefonu, tylko cyfry
- email: adres email, jeśli jest. Rozumiej polskie dyktowanie: małpa = @, kropka = .
- date: data w YYYY-MM-DD, jeśli użytkownik podał datę względną lub konkretną
- time: godzina w HH:MM, jeśli jest
- product_or_next_action: produkt OZE lub następny krok, jeśli jest

Zasady:
- Nie wymyślaj brakujących danych.
- Produkty normalizuj krótko: PV, Pompa ciepła, Magazyn energii, PV + Magazyn energii.
- Jeśli wiadomość dotyczy wysłania oferty, intent ustaw na send_offer.
- Jeśli wiadomość dotyczy spotkania/telefonu/follow-upu w czasie, intent ustaw na add_meeting."""


def _empty_result(fallback: str, *, model: str | None = None) -> dict:
    return {
        "fields": {},
        "tokens_in": 0,
        "tokens_out": 0,
        "cost_usd": 0.0,
        "model": model,
        "fallback": fallback,
    }


def _clean(value) -> str:
    return str(value or "").strip()


def _digits(value: str) -> str:
    return re.sub(r"\D+", "", value or "")


_PHONE_TOKEN_VALUES = {
    "zero": "0",
    "jeden": "1",
    "jedynka": "1",
    "dwa": "2",
    "dwójka": "2",
    "dwojka": "2",
    "trzy": "3",
    "trójka": "3",
    "trojka": "3",
    "cztery": "4",
    "czwórka": "4",
    "czworka": "4",
    "pięć": "5",
    "piec": "5",
    "piątka": "5",
    "piatka": "5",
    "sześć": "6",
    "szesc": "6",
    "szóstka": "6",
    "szostka": "6",
    "siedem": "7",
    "siódemka": "7",
    "siodemka": "7",
    "osiem": "8",
    "ósemka": "8",
    "osemka": "8",
    "dziewięć": "9",
    "dziewiec": "9",
    "dziewiątka": "9",
    "dziewiatka": "9",
    "sto": "100",
    "dwieście": "200",
    "dwiescie": "200",
    "trzysta": "300",
    "czterysta": "400",
    "pięćset": "500",
    "piecset": "500",
    "sześćset": "600",
    "szescset": "600",
    "siedemset": "700",
    "osiemset": "800",
    "dziewięćset": "900",
    "dziewiecset": "900",
    "dziesięć": "10",
    "dziesiec": "10",
    "dwadzieścia": "20",
    "dwadziescia": "20",
    "trzydzieści": "30",
    "trzydziesci": "30",
    "czterdzieści": "40",
    "czterdziesci": "40",
    "pięćdziesiąt": "50",
    "piecdziesiat": "50",
    "sześćdziesiąt": "60",
    "szescdziesiat": "60",
    "siedemdziesiąt": "70",
    "siedemdziesiat": "70",
    "osiemdziesiąt": "80",
    "osiemdziesiat": "80",
    "dziewięćdziesiąt": "90",
    "dziewiecdziesiat": "90",
}


def _normalize_phone(value: str) -> str:
    digits = _digits(value)
    if len(digits) == 11 and digits.startswith("48"):
        digits = digits[2:]
    if len(digits) == 9:
        return digits

    parts = []
    for token in re.findall(r"[\wąćęłńóśźż]+", (value or "").casefold()):
        part = _PHONE_TOKEN_VALUES.get(token)
        if part:
            parts.append(part)
    spoken_digits = "".join(parts)
    if len(spoken_digits) == 11 and spoken_digits.startswith("48"):
        spoken_digits = spoken_digits[2:]
    return spoken_digits if len(spoken_digits) == 9 else ""


def _normalize_fields(raw: dict) -> dict[str, str]:
    fields: dict[str, str] = {}
    for key in FIELD_KEYS:
        value = _clean(raw.get(key))
        if not value:
            continue
        if key == "phone":
            value = _normalize_phone(value)
            if not value:
                continue
        if key == "email":
            value = normalize_spoken_email_value(value)
            if not value:
                continue
        fields[key] = value
    return fields


async def extract_voice_fields(transcription: str) -> dict:
    """Extract key fields from a voice transcript.

    Never raises. Returned fields are technical metadata for diagnostics and
    benchmarks; the normal confirmed text flow remains the source of behavior.
    """
    if not transcription or not transcription.strip():
        return _empty_result(FALLBACK_EMPTY_INPUT)

    try:
        result = await call_claude_with_tools(
            _system_prompt(),
            transcription,
            tools=[_EXTRACTION_TOOL],
            model_type="simple",
            force_tool="extract_voice_fields",
        )
    except Exception as exc:
        logger.warning(
            "extract_voice_fields: unexpected exception exc_type=%s",
            exception_type(exc),
        )
        return _empty_result(FALLBACK_API_ERROR)

    if result.get("tool_name") != "extract_voice_fields":
        return _empty_result(FALLBACK_NO_TOOL, model=result.get("model"))

    return {
        "fields": _normalize_fields(dict(result.get("tool_input") or {})),
        "tokens_in": int(result.get("tokens_in") or 0),
        "tokens_out": int(result.get("tokens_out") or 0),
        "cost_usd": float(result.get("cost_usd") or 0.0),
        "model": result.get("model"),
        "fallback": None,
    }
