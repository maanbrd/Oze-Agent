"""Claude AI integration for OZE-Agent.

Model routing:
  - COMPLEX (claude-sonnet-4-6): voice parsing, client data extraction, follow-up parsing
  - SIMPLE  (claude-haiku-4-5-20251001): intent classification, confirmations, morning brief

All functions return dicts and never raise — errors return empty/default values.
"""

import json
import logging
from typing import Optional

import anthropic

from bot.config import Config

logger = logging.getLogger(__name__)

MODEL_COMPLEX = "claude-sonnet-4-6"
MODEL_SIMPLE = "claude-haiku-4-5-20251001"

# Cost per million tokens (USD)
COST_PER_MTOK_IN = {"complex": 3.0, "simple": 0.8}
COST_PER_MTOK_OUT = {"complex": 15.0, "simple": 4.0}

VALID_INTENTS = {
    "add_client", "search_client", "edit_client", "delete_client",
    "add_meeting", "view_meetings", "reschedule_meeting", "cancel_meeting",
    "show_pipeline", "change_status", "assign_photo",
    "general_question", "confirm_yes", "confirm_no", "cancel_flow",
}


# ── Core API call ─────────────────────────────────────────────────────────────


async def call_claude(
    system_prompt: str,
    user_message: str,
    model_type: str = "complex",
    max_tokens: int = 2048,
) -> dict:
    """Send a message to Claude and return the response with usage stats.

    Returns:
        {"text": str, "tokens_in": int, "tokens_out": int, "cost_usd": float, "model": str}
    """
    model = MODEL_COMPLEX if model_type == "complex" else MODEL_SIMPLE
    client = anthropic.AsyncAnthropic(api_key=Config.ANTHROPIC_API_KEY)

    try:
        response = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        tokens_in = response.usage.input_tokens
        tokens_out = response.usage.output_tokens
        cost = (
            tokens_in * COST_PER_MTOK_IN[model_type] / 1_000_000
            + tokens_out * COST_PER_MTOK_OUT[model_type] / 1_000_000
        )
        return {
            "text": response.content[0].text,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost_usd": cost,
            "model": model,
        }
    except Exception as e:
        logger.error("call_claude(%s): %s", model_type, e)
        return {"text": "", "tokens_in": 0, "tokens_out": 0, "cost_usd": 0.0, "model": model}


# ── Voice note parsing ────────────────────────────────────────────────────────


async def parse_voice_note(
    transcription: str,
    user_columns: list[str],
    today: str,
    default_duration: int,
) -> dict:
    """Parse a post-meeting voice note into structured client data.

    Returns:
        {"client_data": dict, "missing_columns": list, "suggested_followup": dict,
         "tokens_in": int, "tokens_out": int, "cost_usd": float}
    """
    system_prompt = f"""Jesteś asystentem handlowca OZE w Polsce. Użytkownik nagrał notatkę głosową po spotkaniu.
Transkrypcja: "{transcription}"
Kolumny w arkuszu: {json.dumps(user_columns, ensure_ascii=False)}
Dzisiejsza data: {today}
Nawyki użytkownika: domyślna długość spotkania = {default_duration} min

Wyciągnij WSZYSTKIE dane pasujące do kolumn. Zwróć TYLKO JSON:
{{
  "client_data": {{"kolumna": "wartość", ...}},
  "missing_columns": ["kolumna1", "kolumna2"],
  "suggested_followup": {{
    "action": "opis",
    "deadline": "data jeśli wspomniano",
    "calendar_event_title": "proponowany tytuł"
  }}
}}

Zasady:
- Produkty mapuj na: PV, Pompa ciepła, Magazyn energii, Klimatyzacja
- Tytuły po polsku: "Spotkanie z [imię]", "Wycena dla [nazwisko]"
- NIE dodawaj pól których nie ma w transkrypcji
- missing_columns = kolumny z arkusza BEZ wartości w transkrypcji
- Daty: "do środy", "w przyszłym tygodniu", "za 3 dni"
- Bądź zwięzły. Nie dodawaj komentarzy.
- Jeśli wspomniany adres, zapisz go w formacie: ulica numer, miejscowość"""

    result = await call_claude(system_prompt, "Parsuj notatkę.", model_type="complex")

    try:
        parsed = json.loads(result["text"])
    except Exception:
        logger.error("parse_voice_note: JSON parse failed: %s", result["text"][:200])
        parsed = {"client_data": {}, "missing_columns": [], "suggested_followup": {}}

    return {
        **parsed,
        "tokens_in": result["tokens_in"],
        "tokens_out": result["tokens_out"],
        "cost_usd": result["cost_usd"],
    }


# ── Intent classification ─────────────────────────────────────────────────────


async def classify_intent(
    message: str, context: Optional[list[dict]] = None
) -> dict:
    """Classify user message intent using the SIMPLE model.

    Returns:
        {"intent": str, "entities": dict, "confidence": float}
    """
    intents_list = ", ".join(sorted(VALID_INTENTS))
    context_str = ""
    if context:
        last = context[-3:]
        context_str = "\n".join(f"{m['role']}: {m['content']}" for m in last)

    system_prompt = f"""Klasyfikuj zamiar użytkownika. Zwróć TYLKO JSON:
{{"intent": "<jeden z: {intents_list}>", "entities": {{}}, "confidence": 0.0-1.0}}

Przykłady:
- "dodaj klienta Jana Kowalskiego" → add_client, entities: {{"name": "Jan Kowalski"}}
- "znajdź Kowalskiego z Warszawy" → search_client, entities: {{"name": "Kowalski", "city": "Warszawa"}}
- "umów spotkanie na wtorek" → add_meeting, entities: {{"day": "wtorek"}}
- "tak" / "ok" / "zgadza się" → confirm_yes
- "nie" / "anuluj" → confirm_no lub cancel_flow

Kontekst poprzednich wiadomości:
{context_str}"""

    result = await call_claude(system_prompt, message, model_type="simple", max_tokens=256)

    try:
        parsed = json.loads(result["text"])
        if parsed.get("intent") not in VALID_INTENTS:
            parsed["intent"] = "general_question"
        parsed.setdefault("entities", {})
        parsed.setdefault("confidence", 0.5)
        return parsed
    except Exception:
        logger.error("classify_intent: JSON parse failed: %s", result["text"][:100])
        return {"intent": "general_question", "entities": {}, "confidence": 0.0}


# ── Client data extraction ────────────────────────────────────────────────────


async def extract_client_data(message: str, user_columns: list[str]) -> dict:
    """Extract structured client data from natural language text.

    Returns same format as parse_voice_note.
    """
    system_prompt = f"""Wyciągnij dane klienta z wiadomości tekstowej. Kolumny arkusza: {json.dumps(user_columns, ensure_ascii=False)}.
Zwróć TYLKO JSON:
{{"client_data": {{"kolumna": "wartość"}}, "missing_columns": ["..."], "suggested_followup": {{}}}}
NIE dodawaj pól których nie ma w wiadomości."""

    result = await call_claude(system_prompt, message, model_type="complex")

    try:
        parsed = json.loads(result["text"])
    except Exception:
        logger.error("extract_client_data: JSON parse failed: %s", result["text"][:200])
        parsed = {"client_data": {}, "missing_columns": [], "suggested_followup": {}}

    return {
        **parsed,
        "tokens_in": result["tokens_in"],
        "tokens_out": result["tokens_out"],
        "cost_usd": result["cost_usd"],
    }


# ── Meeting data extraction ───────────────────────────────────────────────────


async def extract_meeting_data(message: str, today: str) -> dict:
    """Parse meeting info from natural language (Polish dates/times).

    Returns:
        {"client_name": str, "date": str, "time": str, "duration_minutes": int,
         "location": str, "tokens_in": int, "tokens_out": int, "cost_usd": float}
    """
    system_prompt = f"""Wyciągnij dane spotkania z wiadomości. Dzisiaj: {today}.
Zwróć TYLKO JSON:
{{"client_name": "", "date": "YYYY-MM-DD", "time": "HH:MM", "duration_minutes": 60, "location": ""}}
Rozumiej polskie wyrażenia dat: "jutro", "w środę", "za tydzień", "o 14", "na 14:30".
Jeśli czegoś brak, zostaw pusty string."""

    result = await call_claude(system_prompt, message, model_type="complex", max_tokens=512)

    try:
        parsed = json.loads(result["text"])
    except Exception:
        logger.error("extract_meeting_data: JSON parse failed: %s", result["text"][:200])
        parsed = {"client_name": "", "date": "", "time": "", "duration_minutes": 60, "location": ""}

    return {
        **parsed,
        "tokens_in": result["tokens_in"],
        "tokens_out": result["tokens_out"],
        "cost_usd": result["cost_usd"],
    }


# ── General bot response ──────────────────────────────────────────────────────


async def generate_bot_response(
    system_context: str,
    user_message: str,
    conversation_history: list[dict],
) -> dict:
    """Generate a conversational bot response.

    Uses SIMPLE model for short exchanges, COMPLEX if the conversation history
    suggests a multi-step flow (> 4 messages).
    """
    model_type = "complex" if len(conversation_history) > 4 else "simple"
    return await call_claude(system_context, user_message, model_type=model_type)


# ── Follow-up response parsing ────────────────────────────────────────────────


async def parse_followup_response(
    transcription: str,
    meetings: list[dict],
    user_columns: list[str],
) -> dict:
    """Parse a bulk follow-up response covering multiple meetings.

    Returns:
        {"updates": [{"event_id": str, "status": str, "notes": str, "next_step": str}],
         "tokens_in": int, "tokens_out": int, "cost_usd": float}
    """
    meetings_desc = "\n".join(
        f"- ID: {m.get('id')}, Tytuł: {m.get('title')}, Koniec: {m.get('end')}"
        for m in meetings
    )
    columns_str = json.dumps(user_columns, ensure_ascii=False)

    system_prompt = f"""Użytkownik opisał wyniki kilku spotkań z dzisiaj. Dopasuj informacje do właściwych spotkań.
Spotkania z dzisiaj:
{meetings_desc}

Kolumny arkusza: {columns_str}

Zwróć TYLKO JSON:
{{
  "updates": [
    {{
      "event_id": "<ID spotkania>",
      "status": "<nowy status z arkusza>",
      "notes": "<notatki>",
      "next_step": "<następny krok>"
    }}
  ]
}}"""

    result = await call_claude(system_prompt, transcription, model_type="complex")

    try:
        parsed = json.loads(result["text"])
    except Exception:
        logger.error("parse_followup_response: JSON parse failed: %s", result["text"][:200])
        parsed = {"updates": []}

    return {
        **parsed,
        "tokens_in": result["tokens_in"],
        "tokens_out": result["tokens_out"],
        "cost_usd": result["cost_usd"],
    }


# ── Morning brief generation ──────────────────────────────────────────────────


async def format_morning_brief(
    events: list[dict],
    followups: list[dict],
    pipeline_stats: dict,
) -> dict:
    """Generate a formatted morning brief message in Polish.

    Returns:
        {"text": str, "tokens_in": int, "tokens_out": int, "cost_usd": float}
    """
    events_str = "\n".join(
        f"- {e.get('start', '')[:16]} {e.get('title', '')} @ {e.get('location', '')}"
        for e in events
    ) or "Brak spotkań"

    followups_str = "\n".join(
        f"- {f.get('event_title', '')}"
        for f in followups
    ) or "Brak"

    stats_str = "\n".join(
        f"  {status}: {count}" for status, count in pipeline_stats.items()
    ) or "Brak danych"

    system_prompt = """Jesteś asystentem handlowca OZE. Wygeneruj poranny raport po polsku.
Bądź zwięzły, przyjazny, motywujący. Użyj emoji. Format Telegram MarkdownV2."""

    user_message = f"""Spotkania dziś:
{events_str}

Oczekujące follow-upy:
{followups_str}

Pipeline:
{stats_str}"""

    return await call_claude(system_prompt, user_message, model_type="simple", max_tokens=1024)
