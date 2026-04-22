"""Anthropic tool schemas for the intent router.

Six MVP intent tools (from INTENCJE_MVP.md) plus three meta-tools
(record_general_question, record_out_of_scope, record_multi_meeting_rejection)
from PHASE2_CONTRACT_FREEZE.md D5–D9.
"""

from .intents import IntentType


STATUS_VALUES = [
    "Nowy lead",
    "Spotkanie umówione",
    "Spotkanie odbyte",
    "Oferta wysłana",
    "Podpisane",
    "Zamontowana",
    "Rezygnacja z umowy",
    "Nieaktywny",
    "Odrzucone",
]

# Slice 5.4.2: doc_followup dropped from router — real user speech for document
# reminders maps to phone_call (call to remind) or add_note (just record it).
# Downstream legacy tolerates doc_followup in flow_data / Calendar metadata.
EVENT_TYPE_VALUES = ["in_person", "phone_call", "offer_email"]

OUT_OF_SCOPE_CATEGORIES = ["post_mvp_roadmap", "vision_only", "unplanned"]

POST_MVP_FEATURE_KEYS = [
    "edit_client",
    "filter_clients",
    "pipeline_dashboard",
    "multi_meeting",
    "voice_input",
    "photo_upload",
    "csv_import",
    "full_dashboard",
]

VISION_ONLY_FEATURE_KEYS = [
    "reschedule_meeting",
    "cancel_meeting",
    "free_slots",
    "delete_client",
    "habit_learning",
    "flexible_columns",
]

UNPLANNED_FEATURE_KEYS = [
    "pre_meeting_reminders",
    "meeting_non_working_day_warning",
]

FEATURE_KEYS = (
    POST_MVP_FEATURE_KEYS
    + VISION_ONLY_FEATURE_KEYS
    + UNPLANNED_FEATURE_KEYS
)

FEATURE_KEY_TO_CATEGORY = {
    **{key: "post_mvp_roadmap" for key in POST_MVP_FEATURE_KEYS},
    **{key: "vision_only" for key in VISION_ONLY_FEATURE_KEYS},
    **{key: "unplanned" for key in UNPLANNED_FEATURE_KEYS},
}


_ADD_CLIENT = {
    "name": "record_add_client",
    "description": (
        "Dodaj nowego klienta do CRM. Użyj gdy użytkownik podaje imię i nazwisko "
        "nowego klienta (opcjonalnie z miastem, telefonem, produktem). Frazy typu "
        "'dodaj', 'dopisz', 'nowy klient' + osoba/miasto bez treści notatki to add_client."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Imię i nazwisko klienta."},
            "city": {"type": "string"},
            "phone": {"type": "string"},
            "product": {"type": "string"},
            "notes": {"type": "string"},
        },
        "required": ["name"],
    },
}

_SHOW_CLIENT = {
    "name": "record_show_client",
    "description": (
        "Pokaż informacje o istniejącym kliencie. Wymagane co najmniej jedno "
        "z pól: name, city, phone. Użyj dla fraz typu 'co mam o X', 'pokaż X', "
        "'znajdź X'."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "city": {"type": "string"},
            "phone": {"type": "string"},
        },
    },
}

_ADD_NOTE = {
    "name": "record_add_note",
    "description": (
        "Dopisz notatkę do istniejącego klienta. Użyj gdy użytkownik przekazuje "
        "konkretną treść notatki o kliencie bez elementu czasowego / bez zmiany statusu. "
        "Nie używaj jeśli pole note miałoby być puste — wtedy wybierz inne narzędzie."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "client_name": {"type": "string"},
            "note": {"type": "string"},
            "city": {"type": "string"},
        },
        "required": ["client_name", "note"],
    },
}

_CHANGE_STATUS = {
    "name": "record_change_status",
    "description": (
        "Zmień status klienta. Użyj gdy użytkownik opisuje zmianę etapu "
        "(np. podpisanie umowy, rezygnacja, wysyłka oferty)."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "client_name": {"type": "string"},
            "status": {"type": "string", "enum": STATUS_VALUES},
            "city": {"type": "string"},
        },
        "required": ["client_name", "status"],
    },
}

_ADD_MEETING = {
    "name": "record_add_meeting",
    "description": (
        "Zaplanuj pojedyncze spotkanie, rozmowę telefoniczną, wysyłkę oferty "
        "lub follow-up po dokumentach. Dla ≥2 spotkań użyj "
        "record_multi_meeting_rejection. Jeśli użytkownik mówi po prostu 'spotkanie', "
        "ustaw event_type=in_person."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "client_name": {"type": "string"},
            "date_iso": {
                "type": "string",
                "description": "Data w formacie ISO YYYY-MM-DD.",
            },
            "event_type": {"type": "string", "enum": EVENT_TYPE_VALUES},
            "time": {
                "type": "string",
                "description": "Godzina w formacie HH:MM (24h), jeśli podana.",
            },
            "duration_minutes": {"type": "integer"},
            "location": {"type": "string"},
        },
        "required": ["client_name", "date_iso", "event_type"],
    },
}

_SHOW_DAY_PLAN = {
    "name": "record_show_day_plan",
    "description": (
        "Pokaż plan dnia z Kalendarza. Użyj gdy użytkownik pyta co ma na dziś, "
        "jutro lub dany dzień."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "date_iso": {
                "type": "string",
                "description": "Data w formacie ISO YYYY-MM-DD; pomiń dla dziś.",
            },
        },
    },
}

_GENERAL_QUESTION = {
    "name": "record_general_question",
    "description": (
        "Pytanie ogólne nie wymagające operacji CRM (small talk, pytanie do "
        "asystenta, prośba o wyjaśnienie)."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "reason": {
                "type": "string",
                "description": "Krótki opis o co pyta użytkownik.",
            },
        },
    },
}

_OUT_OF_SCOPE = {
    "name": "record_out_of_scope",
    "description": (
        "Użytkownik prosi o funkcję która nie jest w MVP. Zawsze podaj category "
        "oraz feature_key."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "category": {"type": "string", "enum": OUT_OF_SCOPE_CATEGORIES},
            "feature_key": {"type": "string", "enum": FEATURE_KEYS},
            "details": {"type": "string"},
        },
        "required": ["category", "feature_key"],
    },
}

_MULTI_MEETING_REJECTION = {
    "name": "record_multi_meeting_rejection",
    "description": (
        "Użytkownik prosi o ≥2 spotkania w jednej wiadomości. W MVP obsługujemy "
        "tylko pojedyncze spotkanie — odrzucamy."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "meeting_count": {"type": "integer", "minimum": 2},
        },
        "required": ["meeting_count"],
    },
}


ALL_TOOLS: list[dict] = [
    _ADD_CLIENT,
    _SHOW_CLIENT,
    _ADD_NOTE,
    _CHANGE_STATUS,
    _ADD_MEETING,
    _SHOW_DAY_PLAN,
    _GENERAL_QUESTION,
    _OUT_OF_SCOPE,
    _MULTI_MEETING_REJECTION,
]


# record_out_of_scope is intentionally absent — it dispatches to 3 IntentTypes
# via its `category` field and is handled explicitly in router._to_intent_result.
TOOL_NAME_TO_INTENT: dict[str, IntentType] = {
    "record_add_client": IntentType.ADD_CLIENT,
    "record_show_client": IntentType.SHOW_CLIENT,
    "record_add_note": IntentType.ADD_NOTE,
    "record_change_status": IntentType.CHANGE_STATUS,
    "record_add_meeting": IntentType.ADD_MEETING,
    "record_show_day_plan": IntentType.SHOW_DAY_PLAN,
    "record_general_question": IntentType.GENERAL_QUESTION,
    "record_multi_meeting_rejection": IntentType.MULTI_MEETING,
}
