"""Pure unit tests for tests_e2e.fixtures.

Mocks shared.* and tests_e2e.{sheets,calendar}_verify so no Supabase /
Google calls fire. Verifies seed/cleanup orchestration logic.
"""

from unittest.mock import AsyncMock, patch

import pytest

from tests_e2e.fixtures import (
    CONFLICT_FIXTURE_TITLE,
    FIXTURE_CLIENTS,
    cleanup_synthetic_data,
    seed_fixtures,
)


# ── Static shape ────────────────────────────────────────────────────────────


def test_fixture_clients_count_and_names():
    """Three canonical fixtures: 2 Jan Kowalski (different cities) + 1 Marek."""
    assert len(FIXTURE_CLIENTS) == 3
    names = [c["Imię i nazwisko"] for c in FIXTURE_CLIENTS]
    assert names.count("E2E-Beta-Fixture-Jan-Kowalski") == 2
    assert "E2E-Beta-Fixture-Marek-Nowak" in names


def test_fixture_jan_kowalski_has_distinct_cities():
    jans = [c for c in FIXTURE_CLIENTS if c["Imię i nazwisko"] == "E2E-Beta-Fixture-Jan-Kowalski"]
    cities = {c["Miasto"] for c in jans}
    assert cities == {"Warszawa", "Kraków"}


def test_all_fixture_clients_have_required_fields():
    required = {"Imię i nazwisko", "Miasto", "Telefon", "Produkt", "Status"}
    for c in FIXTURE_CLIENTS:
        missing = required - set(c.keys())
        assert not missing, f"fixture {c.get('Imię i nazwisko')} missing {missing}"


def test_conflict_fixture_title_constant():
    assert CONFLICT_FIXTURE_TITLE == "E2E-Beta-Fixture-Conflict-Slot"


def test_all_fixtures_use_e2e_beta_fixture_prefix():
    """Naming invariant: fixture rows must start with E2E-Beta-Fixture-
    so the per-run cleanup leaves them alone."""
    for c in FIXTURE_CLIENTS:
        assert c["Imię i nazwisko"].startswith("E2E-Beta-Fixture-")


# ── seed_fixtures ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_seed_fixtures_returns_error_when_user_missing():
    with patch("tests_e2e.fixtures.resolve_user_id", new=AsyncMock(return_value=None)):
        report = await seed_fixtures(999)
    assert "error" in report
    assert "telegram_id=999" in report["error"]


@pytest.mark.asyncio
async def test_seed_fixtures_skips_existing_clients():
    """When find_client_row returns an existing row, that fixture is skipped."""
    fake_existing = {"_row": 5, "Imię i nazwisko": "E2E-Beta-Fixture-Jan-Kowalski"}
    add_calls = []

    async def fake_add(uid, data):
        add_calls.append(data["Imię i nazwisko"])
        return 99

    with patch("tests_e2e.fixtures.resolve_user_id", new=AsyncMock(return_value="uuid")), \
         patch("tests_e2e.fixtures.find_client_row",
               new=AsyncMock(return_value=fake_existing)), \
         patch("tests_e2e.fixtures.add_client", new=fake_add), \
         patch("tests_e2e.fixtures.find_event_by_summary_in_window",
               new=AsyncMock(return_value={"id": "x", "title": CONFLICT_FIXTURE_TITLE})), \
         patch("tests_e2e.fixtures.create_event",
               new=AsyncMock(return_value={"id": "x"})):
        report = await seed_fixtures(999)

    # All 3 fixture clients are "existing" → 0 add_client calls.
    assert add_calls == []
    assert len(report["skipped_clients"]) == 3
    assert len(report["seeded_clients"]) == 0
    # Calendar fixture exists too → skipped
    assert len(report["skipped_events"]) == 1
    assert len(report["seeded_events"]) == 0


@pytest.mark.asyncio
async def test_seed_fixtures_creates_when_missing():
    """When nothing exists, seed_fixtures creates all three rows + the event."""
    add_calls = []

    async def fake_add(uid, data):
        add_calls.append((data["Imię i nazwisko"], data["Miasto"]))
        return len(add_calls) + 100  # fake row number

    with patch("tests_e2e.fixtures.resolve_user_id", new=AsyncMock(return_value="uuid")), \
         patch("tests_e2e.fixtures.find_client_row",
               new=AsyncMock(return_value=None)), \
         patch("tests_e2e.fixtures.add_client", new=fake_add), \
         patch("tests_e2e.fixtures.find_event_by_summary_in_window",
               new=AsyncMock(return_value=None)), \
         patch("tests_e2e.fixtures.create_event",
               new=AsyncMock(return_value={"id": "evt-1"})):
        report = await seed_fixtures(999)

    assert len(report["seeded_clients"]) == 3
    assert len(report["skipped_clients"]) == 0
    assert len(report["seeded_events"]) == 1
    assert any("Conflict-Slot" in s for s in report["seeded_events"])


@pytest.mark.asyncio
async def test_seed_fixtures_records_failures():
    """add_client returning None → recorded as failed_clients."""
    with patch("tests_e2e.fixtures.resolve_user_id", new=AsyncMock(return_value="uuid")), \
         patch("tests_e2e.fixtures.find_client_row",
               new=AsyncMock(return_value=None)), \
         patch("tests_e2e.fixtures.add_client", new=AsyncMock(return_value=None)), \
         patch("tests_e2e.fixtures.find_event_by_summary_in_window",
               new=AsyncMock(return_value=None)), \
         patch("tests_e2e.fixtures.create_event",
               new=AsyncMock(return_value=None)):
        report = await seed_fixtures(999)

    assert len(report["failed_clients"]) == 3
    assert len(report["failed_events"]) == 1


# ── cleanup_synthetic_data ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cleanup_returns_error_when_user_missing():
    with patch("tests_e2e.fixtures.resolve_user_id", new=AsyncMock(return_value=None)):
        report = await cleanup_synthetic_data(999)
    assert "error" in report


@pytest.mark.asyncio
async def test_cleanup_default_excludes_fixtures():
    """Default cleanup must NOT delete fixtures (E2E-Beta-Fixture-*).

    Verifies that find_synthetic_rows is called with `include_fixtures=False`.
    """
    captured_kwargs: dict = {}

    async def fake_find_rows(uid, run_id=None, include_fixtures=False):
        captured_kwargs["include_fixtures"] = include_fixtures
        captured_kwargs["run_id"] = run_id
        return []

    with patch("tests_e2e.fixtures.resolve_user_id", new=AsyncMock(return_value="uuid")), \
         patch("tests_e2e.fixtures.find_synthetic_rows", new=fake_find_rows), \
         patch("tests_e2e.fixtures.delete_synthetic_rows",
               new=AsyncMock(return_value=0)), \
         patch("tests_e2e.fixtures.find_synthetic_events",
               new=AsyncMock(return_value=[])), \
         patch("tests_e2e.fixtures.delete_synthetic_events",
               new=AsyncMock(return_value=0)):
        await cleanup_synthetic_data(999)

    assert captured_kwargs["include_fixtures"] is False
    assert captured_kwargs["run_id"] is None


@pytest.mark.asyncio
async def test_cleanup_with_run_id_propagates():
    captured: dict = {}

    async def fake_find(uid, run_id=None, include_fixtures=False):
        captured["run_id"] = run_id
        return []

    with patch("tests_e2e.fixtures.resolve_user_id", new=AsyncMock(return_value="uuid")), \
         patch("tests_e2e.fixtures.find_synthetic_rows", new=fake_find), \
         patch("tests_e2e.fixtures.delete_synthetic_rows",
               new=AsyncMock(return_value=0)), \
         patch("tests_e2e.fixtures.find_synthetic_events",
               new=AsyncMock(return_value=[])), \
         patch("tests_e2e.fixtures.delete_synthetic_events",
               new=AsyncMock(return_value=0)):
        await cleanup_synthetic_data(999, run_id="143052")

    assert captured["run_id"] == "143052"


@pytest.mark.asyncio
async def test_cleanup_full_reset_includes_fixtures():
    captured: dict = {}

    async def fake_find(uid, run_id=None, include_fixtures=False):
        captured["include_fixtures"] = include_fixtures
        return []

    with patch("tests_e2e.fixtures.resolve_user_id", new=AsyncMock(return_value="uuid")), \
         patch("tests_e2e.fixtures.find_synthetic_rows", new=fake_find), \
         patch("tests_e2e.fixtures.delete_synthetic_rows",
               new=AsyncMock(return_value=0)), \
         patch("tests_e2e.fixtures.find_synthetic_events",
               new=AsyncMock(return_value=[])), \
         patch("tests_e2e.fixtures.delete_synthetic_events",
               new=AsyncMock(return_value=0)):
        await cleanup_synthetic_data(999, include_fixtures=True)

    assert captured["include_fixtures"] is True


@pytest.mark.asyncio
async def test_cleanup_returns_counts():
    rows = [{"_row": 1}, {"_row": 2}]
    events = [{"id": "a"}]
    with patch("tests_e2e.fixtures.resolve_user_id", new=AsyncMock(return_value="uuid")), \
         patch("tests_e2e.fixtures.find_synthetic_rows",
               new=AsyncMock(return_value=rows)), \
         patch("tests_e2e.fixtures.delete_synthetic_rows",
               new=AsyncMock(return_value=2)), \
         patch("tests_e2e.fixtures.find_synthetic_events",
               new=AsyncMock(return_value=events)), \
         patch("tests_e2e.fixtures.delete_synthetic_events",
               new=AsyncMock(return_value=1)):
        report = await cleanup_synthetic_data(999)

    assert report["sheets_rows_found"] == 2
    assert report["sheets_deleted"] == 2
    assert report["calendar_events_found"] == 1
    assert report["calendar_deleted"] == 1
