"""Polish out-of-scope banner copy.

Frozen text per agent_behavior_spec_v5.md R5 and INTENCJE_MVP.md §8.
Single source of truth — both `banner_for` (new IntentResult) and
`banner_for_legacy` (dispatch-time dict shim) delegate to `_resolve`.
"""

from typing import Optional

from shared.intent.intents import IntentResult, IntentType


REFRESH_COLUMNS_HINT = "Użyj komendy /odswiez_kolumny."

_POST_MVP_DEFAULT = (
    "To feature post-MVP. Zrobisz to w Google Sheets / dashboardzie, "
    "który wejdzie w kolejnej fazie."
)

_VISION_ONLY_DEFAULT = (
    "Poza aktualnym zakresem. Wymaga osobnej decyzji przed wejściem do roadmapy."
)

_UNPLANNED_DEFAULT = (
    "Poza zakresem agenta. Skorzystaj z natywnej funkcji Google Calendar."
)

_MULTI_MEETING = "Obsługuję jedno spotkanie naraz. Dodaj je osobno."

_FEATURE_OVERRIDES: dict[str, str] = {
    "edit_client": (
        "To feature post-MVP. Zmień w Google Sheets bezpośrednio, "
        "albo wejdzie w kolejnej fazie."
    ),
    "pre_meeting_reminders": (
        "Przypomnienia ustawia Google Calendar w swoich ustawieniach."
    ),
    "meeting_non_working_day_warning": (
        "Google Calendar pokazuje dzień tygodnia — sprawdź przy tworzeniu wydarzenia."
    ),
}

_CATEGORY_DEFAULT: dict[IntentType, str] = {
    IntentType.POST_MVP_ROADMAP: _POST_MVP_DEFAULT,
    IntentType.VISION_ONLY: _VISION_ONLY_DEFAULT,
    IntentType.UNPLANNED: _UNPLANNED_DEFAULT,
}


def _resolve(intent: IntentType, feature_key: Optional[str]) -> str:
    if intent is IntentType.MULTI_MEETING:
        return _MULTI_MEETING
    if feature_key and feature_key in _FEATURE_OVERRIDES:
        return _FEATURE_OVERRIDES[feature_key]
    return _CATEGORY_DEFAULT.get(intent, _POST_MVP_DEFAULT)


def banner_for(result: IntentResult) -> str:
    return _resolve(result.intent, result.feature_key)


def banner_for_legacy(intent_data: dict) -> str:
    """Dispatch-time shim: resolve banner copy from the legacy dict shape."""
    intent_str = intent_data.get("intent", "")
    try:
        intent = IntentType(intent_str)
    except ValueError:
        intent = IntentType.GENERAL_QUESTION
    return _resolve(intent, intent_data.get("feature_key"))
