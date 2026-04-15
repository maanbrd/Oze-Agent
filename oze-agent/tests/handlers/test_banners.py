"""Banner copy tests for bot/handlers/banners.py."""

import pytest

from bot.handlers.banners import (
    REFRESH_COLUMNS_HINT,
    banner_for,
    banner_for_legacy,
)
from shared.intent.intents import IntentResult, IntentType, ScopeTier
from shared.intent.schemas import (
    FEATURE_KEYS,
    POST_MVP_FEATURE_KEYS,
    UNPLANNED_FEATURE_KEYS,
    VISION_ONLY_FEATURE_KEYS,
)


_BANNED_PHRASES = ("Oto ", "Przygotowałem", "Daj znać", "Oczywiście", "Czy mogę jeszcze")


def _result(intent: IntentType, feature_key: str | None = None) -> IntentResult:
    scope = {
        IntentType.POST_MVP_ROADMAP: ScopeTier.POST_MVP_ROADMAP,
        IntentType.VISION_ONLY: ScopeTier.VISION_ONLY,
        IntentType.UNPLANNED: ScopeTier.UNPLANNED,
        IntentType.MULTI_MEETING: ScopeTier.REJECTED,
    }[intent]
    return IntentResult(intent=intent, scope_tier=scope, feature_key=feature_key)


@pytest.mark.parametrize("feature_key", POST_MVP_FEATURE_KEYS)
def test_post_mvp_feature_keys_have_non_empty_banner(feature_key):
    text = banner_for(_result(IntentType.POST_MVP_ROADMAP, feature_key))
    assert text and text.strip()


@pytest.mark.parametrize("feature_key", VISION_ONLY_FEATURE_KEYS)
def test_vision_only_feature_keys_have_non_empty_banner(feature_key):
    text = banner_for(_result(IntentType.VISION_ONLY, feature_key))
    assert text and text.strip()


@pytest.mark.parametrize("feature_key", UNPLANNED_FEATURE_KEYS)
def test_unplanned_feature_keys_have_non_empty_banner(feature_key):
    text = banner_for(_result(IntentType.UNPLANNED, feature_key))
    assert text and text.strip()


def test_multi_meeting_rejection_banner_non_empty():
    text = banner_for(_result(IntentType.MULTI_MEETING))
    assert text and text.strip()


def test_edit_client_verbatim_copy():
    text = banner_for(_result(IntentType.POST_MVP_ROADMAP, "edit_client"))
    assert text == (
        "To feature post-MVP. Zmień w Google Sheets bezpośrednio, "
        "albo wejdzie w kolejnej fazie."
    )


def test_pre_meeting_reminders_verbatim_copy():
    text = banner_for(_result(IntentType.UNPLANNED, "pre_meeting_reminders"))
    assert text == "Przypomnienia ustawia Google Calendar w swoich ustawieniach."


def test_multi_meeting_verbatim_copy():
    text = banner_for(_result(IntentType.MULTI_MEETING))
    assert text == "Obsługuję jedno spotkanie naraz. Dodaj je osobno."


def test_post_mvp_default_used_for_unmapped_feature_key():
    text = banner_for(_result(IntentType.POST_MVP_ROADMAP, "filter_clients"))
    assert text == (
        "To feature post-MVP. Zrobisz to w Google Sheets / dashboardzie, "
        "który wejdzie w kolejnej fazie."
    )


def test_vision_only_default_used_for_unmapped_feature_key():
    text = banner_for(_result(IntentType.VISION_ONLY, "reschedule_meeting"))
    assert text == (
        "Poza aktualnym zakresem. Wymaga osobnej decyzji przed wejściem do roadmapy."
    )


def test_unplanned_default_uses_native_alternative_tone():
    text = banner_for(_result(IntentType.UNPLANNED))
    assert text == (
        "Poza zakresem agenta. Skorzystaj z natywnej funkcji Google Calendar."
    )


@pytest.mark.parametrize("feature_key", FEATURE_KEYS)
def test_no_banner_contains_banned_phrases(feature_key):
    intent = {
        **{k: IntentType.POST_MVP_ROADMAP for k in POST_MVP_FEATURE_KEYS},
        **{k: IntentType.VISION_ONLY for k in VISION_ONLY_FEATURE_KEYS},
        **{k: IntentType.UNPLANNED for k in UNPLANNED_FEATURE_KEYS},
    }[feature_key]
    text = banner_for(_result(intent, feature_key))
    for phrase in _BANNED_PHRASES:
        assert phrase not in text, f"{feature_key!r} banner contains {phrase!r}"


def test_multi_meeting_banner_no_banned_phrases():
    text = banner_for(_result(IntentType.MULTI_MEETING))
    for phrase in _BANNED_PHRASES:
        assert phrase not in text


def test_refresh_columns_hint_constant():
    assert REFRESH_COLUMNS_HINT == "Użyj komendy /odswiez_kolumny."


def test_banner_for_legacy_matches_banner_for():
    cases = [
        (IntentType.POST_MVP_ROADMAP, "edit_client"),
        (IntentType.VISION_ONLY, "habit_learning"),
        (IntentType.UNPLANNED, "pre_meeting_reminders"),
        (IntentType.MULTI_MEETING, None),
    ]
    for intent, fkey in cases:
        new_api = banner_for(_result(intent, fkey))
        legacy = banner_for_legacy({"intent": intent.value, "feature_key": fkey})
        assert new_api == legacy


def test_banner_for_legacy_handles_unknown_intent_string():
    text = banner_for_legacy({"intent": "totally_unknown", "feature_key": None})
    assert text and text.strip()
