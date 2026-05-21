"""Registry and harness tests for the bot-test core smoke pack."""

from __future__ import annotations

import pytest

from tests_e2e.harness import TelegramE2EHarness
from tests_e2e.scenarios._base import SCENARIOS, list_categories
from tests_e2e.scenarios.core_smoke import (
    _card_text_contains_phone,
    _card_text_contains_product,
    _extract_card_client_name,
)


CORE_SMOKE_SCENARIOS = {
    "sm1_compound_meeting_new_client_preseed",
    "sm2_voice_compound_meeting_new_client_preseed",
    "sm3_phone_field_does_not_force_meeting",
    "sm7_add_meeting_new_client_preseed",
    "sm10_r6_memory_window_expired_requires_client",
}


def test_core_smoke_scenarios_registered_as_opt_in():
    missing = CORE_SMOKE_SCENARIOS - set(SCENARIOS)
    assert not missing, f"missing core_smoke scenarios: {missing}"
    assert "core_smoke" in list_categories()
    for name in CORE_SMOKE_SCENARIOS:
        scenario = SCENARIOS[name]
        assert scenario.category == "core_smoke"
        assert scenario.default_in_run is False
        assert scenario.description


def test_core_smoke_card_text_matchers_tolerate_bot_formatting():
    assert _card_text_contains_phone("Tel. 600 100 200", "600100200")
    assert _card_text_contains_product(
        "PV + Magazyn energii",
        "fotowoltaika i magazyn energii",
    )


def test_core_smoke_extracts_voice_normalized_client_name():
    message = type(
        "Msg",
        (),
        {
            "text": (
                "✅ Dodać spotkanie?\n\n"
                "• Klient: E2E Beta Tester 123456 SM2\n"
                "• Data: 20.05.2026 (środa)"
            )
        },
    )()

    assert _extract_card_client_name(message) == "E2E Beta Tester 123456 SM2"


class _FakeTelegramClient:
    def __init__(self) -> None:
        self.calls = []

    async def send_file(self, entity, path, **kwargs):
        self.calls.append((entity, path, kwargs))


@pytest.mark.asyncio
async def test_harness_send_file_can_send_voice_note():
    harness = TelegramE2EHarness.__new__(TelegramE2EHarness)
    harness._client = _FakeTelegramClient()
    harness._bot_entity = object()
    drained = []

    async def _drain():
        drained.append(True)
        return 0

    harness._drain_inbox = _drain

    await harness.send_file("/tmp/sample.ogg", caption="opis", voice_note=True)

    assert drained == [True]
    [(entity, path, kwargs)] = harness._client.calls
    assert entity is harness._bot_entity
    assert path == "/tmp/sample.ogg"
    assert kwargs == {"caption": "opis", "voice_note": True}
