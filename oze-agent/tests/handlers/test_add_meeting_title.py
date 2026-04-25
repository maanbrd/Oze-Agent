"""Slice 5.4.1 — Calendar event title per event_type.

Verifies that `_enrich_meeting` builds the Calendar event title from the
`EVENT_TYPE_TO_NEXT_STEP_LABEL` mapping so phone_call / offer_email /
doc_followup events are no longer labelled "Spotkanie — ..." in Calendar.
"""

from unittest.mock import AsyncMock, patch

import pytest

from bot.handlers.text import _enrich_meeting
from shared.clients import ClientLookupResult


def _patched_lookup(result: ClientLookupResult):
    return patch(
        "bot.handlers.text.lookup_client",
        new=AsyncMock(return_value=result),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "event_type, expected_prefix",
    [
        ("in_person", "Spotkanie"),
        ("phone_call", "Telefon"),
        ("offer_email", "Wysłać ofertę"),
        ("doc_followup", "Follow-up dokumentowy"),
        (None, "Spotkanie"),
        ("unknown_value", "Spotkanie"),
    ],
)
async def test_enrich_meeting_title_prefix_follows_event_type(event_type, expected_prefix):
    client = {"_row": 7, "Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa"}
    result = ClientLookupResult(status="unique", clients=[client], normalized_query="jan kowalski")

    with _patched_lookup(result):
        enriched = await _enrich_meeting("u1", "Jan Kowalski", "", event_type=event_type)

    assert enriched["title"] == f"{expected_prefix} — Jan Kowalski"


@pytest.mark.asyncio
async def test_enrich_meeting_title_pure_label_when_no_client_name():
    """Without a client name the title is the bare label — no trailing ` — `."""
    result = ClientLookupResult(status="not_found", clients=[], normalized_query="")

    with _patched_lookup(result):
        enriched = await _enrich_meeting("u1", "", "", event_type="phone_call")

    assert enriched["title"] == "Telefon"


@pytest.mark.asyncio
async def test_enrich_meeting_title_uses_event_type_on_not_found_fallback():
    """not_found branch uses the fallback title path in _enrich_meeting itself
    (not _build_enriched_from_client) — make sure event_type is honoured there too."""
    result = ClientLookupResult(status="not_found", clients=[], normalized_query="piotr nowy")

    with _patched_lookup(result):
        enriched = await _enrich_meeting("u1", "Piotr Nowy", "", event_type="offer_email")

    assert enriched["title"] == "Wysłać ofertę — Piotr Nowy"


@pytest.mark.asyncio
async def test_enrich_meeting_title_uses_event_type_on_ambiguous_fallback():
    """multi-match keeps ambiguous_client=True; title still honours event_type."""
    clients = [
        {"_row": 7, "Imię i nazwisko": "Mariusz Krzywinski", "Miasto": "Marki"},
        {"_row": 11, "Imię i nazwisko": "Mariusz Krzywinski", "Miasto": "Wołomin"},
    ]
    result = ClientLookupResult(status="multi", clients=clients, normalized_query="mariusz krzywinski")

    with _patched_lookup(result):
        enriched = await _enrich_meeting("u1", "Mariusz Krzywinski", "", event_type="phone_call")

    assert enriched["ambiguous_client"] is True
    assert enriched["title"] == "Telefon — Mariusz Krzywinski"


@pytest.mark.asyncio
async def test_enrich_meeting_title_uses_event_type_when_known_row_resolves():
    """known_client_row path short-circuits lookup_client; event_type still flows through."""
    all_clients = [
        {"_row": 7, "Imię i nazwisko": "Anna Testowa", "Miasto": "Zatory"},
    ]

    with patch(
        "bot.handlers.text.get_all_clients",
        new=AsyncMock(return_value=all_clients),
    ), patch(
        "bot.handlers.text.lookup_client",
        new=AsyncMock(side_effect=AssertionError("lookup_client must NOT be called when row is known")),
    ):
        enriched = await _enrich_meeting(
            "u1",
            "Anna Testowa",
            "",
            known_client_row=7,
            event_type="offer_email",
        )

    assert enriched["title"] == "Wysłać ofertę — Anna Testowa"


# ── Slice 5.4.1b — description prefix per event_type ─────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "event_type, expected_prefix",
    [
        ("offer_email", "📧 Wyślij ofertę klientowi."),
        ("phone_call", "📞 Zadzwoń do klienta."),
        ("doc_followup", "📋 Follow-up dokumentowy."),
    ],
)
async def test_enrich_meeting_description_prefix_per_event_type(event_type, expected_prefix):
    """Description starts with the event_type-aware action reminder when set."""
    client = {"_row": 7, "Imię i nazwisko": "Jan Kowalski", "Telefon": "600123456"}
    result = ClientLookupResult(status="unique", clients=[client], normalized_query="jan kowalski")

    with _patched_lookup(result):
        enriched = await _enrich_meeting("u1", "Jan Kowalski", "", event_type=event_type)

    assert enriched["description"].startswith(expected_prefix)
    assert "Tel: 600123456" in enriched["description"]


@pytest.mark.asyncio
@pytest.mark.parametrize("event_type", ["in_person", None])
async def test_enrich_meeting_description_no_prefix_for_in_person_or_none(event_type):
    """in_person / None → no action prefix; description starts with client data
    (face-to-face meeting action is obvious from the event itself)."""
    client = {"_row": 7, "Imię i nazwisko": "Jan Kowalski", "Telefon": "600123456"}
    result = ClientLookupResult(status="unique", clients=[client], normalized_query="jan kowalski")

    with _patched_lookup(result):
        enriched = await _enrich_meeting("u1", "Jan Kowalski", "", event_type=event_type)

    assert enriched["description"].startswith("Tel: 600123456")
    for prefix in ("📧", "📞", "📋"):
        assert prefix not in enriched["description"]
