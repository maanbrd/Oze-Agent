"""Claude AI integration for OZE-Agent.

Model routing:
  - COMPLEX (claude-sonnet-4-6): voice parsing, client data extraction, follow-up parsing
  - SIMPLE  (claude-haiku-4-5-20251001): intent classification, confirmations, morning brief

All functions return dicts and never raise — errors return empty/default values.
"""

import json
import logging
from datetime import date
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
    "add_client", "search_client", "edit_client", "add_note", "delete_client",
    "add_meeting", "show_day_plan", "view_meetings", "reschedule_meeting", "cancel_meeting",
    "lejek_sprzedazowy", "filtruj_klientów", "show_pipeline", "change_status",
    "assign_photo", "refresh_columns",
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


# ── Tool use API call ─────────────────────────────────────────────────────────


async def call_claude_with_tools(
    system_prompt: str,
    user_message: str,
    tools: list[dict],
    model_type: str = "complex",
) -> dict:
    """Call Claude with tool use enabled.

    Returns:
        {
            "tool_name": str | None,   # None if Claude responded with text
            "tool_input": dict,
            "text": str | None,        # None if Claude called a tool
            "tokens_in": int, "tokens_out": int, "cost_usd": float, "model": str
        }
    """
    model = MODEL_COMPLEX if model_type == "complex" else MODEL_SIMPLE
    client = anthropic.AsyncAnthropic(api_key=Config.ANTHROPIC_API_KEY)

    try:
        response = await client.messages.create(
            model=model,
            max_tokens=1024,
            system=system_prompt,
            tools=tools,
            messages=[{"role": "user", "content": user_message}],
        )
        tokens_in = response.usage.input_tokens
        tokens_out = response.usage.output_tokens
        cost = (
            tokens_in * COST_PER_MTOK_IN[model_type] / 1_000_000
            + tokens_out * COST_PER_MTOK_OUT[model_type] / 1_000_000
        )
        base = {"tokens_in": tokens_in, "tokens_out": tokens_out, "cost_usd": cost, "model": model}

        for block in response.content:
            if block.type == "tool_use":
                return {**base, "tool_name": block.name, "tool_input": block.input, "text": None}

        # Claude responded with text instead of calling a tool
        text = ""
        for block in response.content:
            if hasattr(block, "text"):
                text = block.text
                break
        return {**base, "tool_name": None, "tool_input": {}, "text": text}

    except Exception as e:
        logger.error("call_claude_with_tools(%s): %s", model_type, e)
        return {
            "tool_name": None, "tool_input": {}, "text": "",
            "tokens_in": 0, "tokens_out": 0, "cost_usd": 0.0, "model": model,
        }


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
- "Jan Nowak Piaseczno 601234567 pompa" → add_client, entities: {{"name": "Jan Nowak", "city": "Piaseczno"}}
- "Stefan Jankowski PV 12kW" → add_client, entities: {{"name": "Stefan Jankowski"}}
- "znajdź Jana Kowalskiego z Warszawy" → search_client, entities: {{"name": "Jan Kowalski", "city": "Warszawa"}}
- "co mam o Janie Mazurze?" → search_client, entities: {{"name": "Jan Mazur"}}
- "umów spotkanie na wtorek" → add_meeting, entities: {{"day": "wtorek"}}
- "spotkanie 22 kwietnia o 17:30 Marki Fiołkowa 24" → add_meeting, entities: {{"date": "22 kwietnia", "time": "17:30", "location": "Marki Fiołkowa 24"}}
- "jutro o 10 jadę do Jana Nowaka ul. Różana 3 Piaseczno" → add_meeting, entities: {{"day": "jutro", "time": "10:00", "name": "Jan Nowak", "location": "ul. Różana 3 Piaseczno"}}
- "spotkanie z Janem Kowalskim pojutrze 15:00" → add_meeting, entities: {{"name": "Jan Kowalski", "day": "pojutrze", "time": "15:00"}}
- WAŻNE: Każda wiadomość zawierająca datę/godzinę + miejsce lub klienta to add_meeting, NIE general_question.
- "co mam dziś?" / "plan na dziś" / "jakie mam spotkania?" → show_day_plan
- "ile mam klientów?" / "pokaż lejek" / "ilu klientów mam" → lejek_sprzedazowy
- "pokaż klientów z Warszawy" → filtruj_klientów, entities: {{"city": "Warszawa"}}
- "kto czeka na ofertę?" → filtruj_klientów, entities: {{"status": "Oferta wysłana"}}
- "klienci z pompą ciepła" → filtruj_klientów, entities: {{"product": "Pompa ciepła"}}
- "wysłałem ofertę Janowi Nowakowi" → change_status, entities: {{"name": "Jan Nowak", "status": "Oferta wysłana"}}
- "Jan Kowalski podpisał" → change_status, entities: {{"name": "Jan Kowalski", "status": "Podpisał"}}
- "Jan Kowalski podpisał kwit" → change_status, entities: {{"name": "Jan Kowalski", "status": "Podpisał"}}
- "Adam Wiśniewski rezygnuje" → change_status, entities: {{"name": "Adam Wiśniewski", "status": "Rezygnuje"}}
- "spadł kwit u Jana Nowaka" → change_status, entities: {{"name": "Jan Nowak", "status": "Rezygnuje"}}
- "Jan Kowalski ma 45 metrów dachu, nie 40" → edit_client, entities: {{"name": "Jan Kowalski"}}
- "Zmień telefon Jana Nowaka na 601234567" → edit_client, entities: {{"name": "Jan Nowak"}}
- "zmień numer Nowaka z Piaseczna na 609888777" → edit_client, entities: {{"name": "Nowak", "city": "Piaseczno"}}
- "zaktualizuj telefon Kowalskiego na 601000222" → edit_client, entities: {{"name": "Kowalski"}}
- "popraw metraż dachu Jana Nowaka na 45" → edit_client, entities: {{"name": "Jan Nowak"}}
- WAŻNE: wiadomości zaczynające się od "zmień", "zaktualizuj", "popraw", "edytuj" + dane klienta → edit_client, NIE add_client, nawet gdy zawierają numer telefonu.
- "dodaj notatkę do Jana Mazura: zadzwoń po 15" → add_note, entities: {{"name": "Jan Mazur"}}
- "Jan Mazur interesuje się też magazynem" → add_note, entities: {{"name": "Jan Mazur"}}
- "odśwież kolumny" / "zaktualizuj kolumny" / "przeładuj arkusz" → refresh_columns
- "tak" / "ok" / "zgadza się" → confirm_yes
- "nie" / "anuluj" → confirm_no lub cancel_flow
- "asdkjfhaskdjfh" / losowe znaki / niezrozumiały tekst → general_question, confidence: 0.1
- WAŻNE: "podpisał", "podpisał kwit/papier/umowę", "klient podpisał" → change_status {{"status": "Podpisał"}}.
- WAŻNE: "wysłałem X", "rezygnuje", "spadł kwit" → change_status, NIE edit_client.
- WAŻNE: Jeśli wiadomość dotyczy zmiany danych ISTNIEJĄCEGO klienta (metraż, telefon, notatki, produkt) → edit_client NIE add_client.

Kontekst poprzednich wiadomości:
{context_str}"""

    result = await call_claude(system_prompt, message, model_type="simple", max_tokens=256)

    raw = result["text"].strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        parsed = json.loads(raw)
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
    system_prompt = f"""Wyciągnij dane klienta z wiadomości. Kolumny arkusza: {json.dumps(user_columns, ensure_ascii=False)}.
Zwróć TYLKO surowy JSON (bez markdown, bez ```):
{{"client_data": {{"kolumna": "wartość"}}, "missing_columns": ["..."], "suggested_followup": {{}}}}

Zasady:
- Parsuj TYLKO tę jedną wiadomość. Ignoruj wszelki wcześniejszy kontekst lub dane.
- NIE dodawaj pól których nie ma w wiadomości
- missing_columns = kolumny z listy BEZ wartości w wiadomości, z wyjątkiem pól systemowych
- NIE wliczaj do missing_columns pól systemowych: "Data pierwszego kontaktu", "Data ostatniego kontaktu", "Status", "Zdjęcia", "Link do zdjęć", "ID kalendarza", "Email", "Dodatkowe info", "Notatki", "Następny krok"

Mapuj slang OZE (zawsze):
- foto / fotowoltaika / fotowoltaikę / PV-ka / panele / pv → "PV"
- pompa / pompeczka / pompa ciepła / pompę → "Pompa ciepła"
- magazyn / magazyn energii → "Magazyn energii"
- klimatyzacja → "Klimatyzacja"
- Jeśli kilka produktów naraz ("magazyn, klima", "PV i pompa"), zapisz WSZYSTKIE w polu Produkt oddzielone przecinkami: np. "PV, Magazyn energii, Klimatyzacja".
- NIE wrzucaj nazw produktów do pola Notatki.

Parsuj bez pytania:
- Metraż domu: "160m2" / "160 metrów" / "dom 160" → szukaj kolumny zawierającej "domu" lub "dom" (np. "Metraż domu (m²)"); jeśli nie ma → pomiń
- Metraż dachu: "dach 40" / "40m2 dachu" → szukaj kolumny zawierającej "dachu" lub "dach" (np. "Metraż dachu (m²)"); jeśli nie ma → pomiń
- Moc: "8kW" / "ósemka" → "8", "szóstka" → "6" → kolumna "Moc" lub "Moc (kW)"; jeśli nie ma → pomiń
- Kierunek: "płd" / "południe" → "południe", "wsch" → "wschód", "zach" → "zachód", "płn" → "północ" → kolumna "Kierunek dachu"; jeśli nie ma → pomiń
- Telefon: tylko cyfry, bez spacji i myślników
- Zużycie prądu / roczne zużycie: "500kWh" / "zużycie 500" → szukaj kolumny zawierającej "zużycie"; jeśli nie ma → pomiń
- Follow-up / następny krok: "zadzwonię za tydzień" / "wracam za 3 dni" / "follow-up w piątek" → oblicz konkretną datę względem {date.today().strftime("%Y-%m-%d")} i zapisz w kolumnie "Następny krok" lub "Data następnego kontaktu"
- Kontekst emocjonalny i sytuacyjny: "żona go przekręciła" / "obiekcje" / "nie był w domu" / "chory" / sytuacja rodzinna → zapisz w polu Notatki
- WAŻNE: Dane techniczne (metraże, moc, kierunek) zapisuj w dedykowanych kolumnach gdy istnieją w arkuszu. Gdy nie istnieją — zapisz w "Dodatkowe info" lub "Notatki" jako tekst (np. "dom: 160m², dach: 40m², moc: 8kW, południe").
- Kolejność słów i interpunkcja nie mają znaczenia — parsuj intencję"""

    result = await call_claude(system_prompt, message, model_type="complex")

    # Strip markdown code fences if model returned them
    raw = result["text"].strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        parsed = json.loads(raw)
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
        {"meetings": [{"client_name": str, "date": str, "time": str,
                       "duration_minutes": int, "location": str}],
         "tokens_in": int, "tokens_out": int, "cost_usd": float}
    """
    system_prompt = f"""Wyciągnij dane spotkań z wiadomości. Dzisiaj: {today}.
Zwróć TYLKO JSON z listą spotkań (nawet jeśli jedno):
{{"meetings": [{{"client_name": "", "date": "YYYY-MM-DD", "time": "HH:MM", "duration_minutes": 60, "location": ""}}]}}
Rozumiej polskie wyrażenia dat i czasu:
- "jutro", "w środę", "za tydzień", "pojutrze", "w przyszłą środę"
- "o 14", "na 14:30", "o czternastej", "na szesnastą"
- "wpół do ósmej" → 07:30, "za kwadrans dziesiąta" → 09:45, "kwadrans po szóstej" → 18:15
Jeśli jedna wiadomość zawiera kilka spotkań (różni klienci lub różne godziny), zwróć wiele obiektów w liście.
Jeśli czegoś brak, zostaw pusty string.
WAŻNE: client_name zapisuj w mianowniku (nominative): "Jan Nowak" nie "Janem Nowakiem", "Mazur" nie "Mazurem", "Anna Kowalska" nie "Anny Kowalskiej"."""

    result = await call_claude(system_prompt, message, model_type="complex", max_tokens=1024)

    raw = result["text"].strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        parsed = json.loads(raw)
        meetings = parsed.get("meetings", [])
    except Exception:
        logger.error("extract_meeting_data: JSON parse failed: %s", result["text"][:200])
        meetings = []

    return {
        "meetings": meetings,
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

    system_prompt = (
        "Jesteś asystentem handlowca OZE. Wygeneruj poranny raport po polsku. "
        "Bądź zwięzły i konkretny. Bez tekstu motywacyjnego. Tylko dane. Format Telegram MarkdownV2. "
        "Używaj emoji funkcjonalnych: 📅 spotkania, ⏰ follow-upy, 📊 pipeline. "
        "Nie używaj: 🎉 🌟 ✨ 💪 🙌 👏 🚀 😊"
    )

    user_message = f"""Spotkania dziś:
{events_str}

Oczekujące follow-upy:
{followups_str}

Pipeline:
{stats_str}"""

    return await call_claude(system_prompt, user_message, model_type="simple", max_tokens=1024)
