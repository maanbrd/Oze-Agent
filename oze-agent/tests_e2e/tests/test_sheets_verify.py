"""Pure unit tests for tests_e2e.sheets_verify.

Mocks `shared.google_sheets` so tests run without Supabase / Google.
"""

from unittest.mock import AsyncMock, patch

import pytest

from tests_e2e.sheets_verify import (
    assert_row_field,
    assert_row_field_equals,
    delete_synthetic_rows,
    find_client_row,
    find_synthetic_rows,
    resolve_user_id,
)


# ── resolve_user_id ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_resolve_user_id_returns_supabase_uuid():
    fake_user = {"id": "uuid-1234", "telegram_id": 999}
    with patch("tests_e2e.sheets_verify.get_user_by_telegram_id", return_value=fake_user):
        uid = await resolve_user_id(999)
    assert uid == "uuid-1234"


@pytest.mark.asyncio
async def test_resolve_user_id_uses_env_override(monkeypatch):
    monkeypatch.setenv("TELEGRAM_E2E_SUPABASE_USER_ID", "uuid-from-env")
    with patch("tests_e2e.sheets_verify.get_user_by_telegram_id") as get_user:
        uid = await resolve_user_id(999)

    assert uid == "uuid-from-env"
    get_user.assert_not_called()


@pytest.mark.asyncio
async def test_resolve_user_id_none_when_user_missing():
    with patch("tests_e2e.sheets_verify.get_user_by_telegram_id", return_value=None):
        uid = await resolve_user_id(42)
    assert uid is None


# ── find_client_row ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_find_client_row_exact_match_with_city():
    rows = [
        {"Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa", "_row": 5},
        {"Imię i nazwisko": "Jan Kowalski", "Miasto": "Kraków", "_row": 6},
    ]
    with patch("tests_e2e.sheets_verify.get_all_clients", new=AsyncMock(return_value=rows)):
        row = await find_client_row("uid", "Jan Kowalski", "Warszawa")
    assert row is not None
    assert row["_row"] == 5


@pytest.mark.asyncio
async def test_find_client_row_case_insensitive():
    rows = [{"Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa", "_row": 5}]
    with patch("tests_e2e.sheets_verify.get_all_clients", new=AsyncMock(return_value=rows)):
        row = await find_client_row("uid", "jan kowalski", "WARSZAWA")
    assert row is not None


@pytest.mark.asyncio
async def test_find_client_row_no_city_picks_first_name_match():
    rows = [
        {"Imię i nazwisko": "Jan Kowalski", "Miasto": "Kraków", "_row": 5},
    ]
    with patch("tests_e2e.sheets_verify.get_all_clients", new=AsyncMock(return_value=rows)):
        row = await find_client_row("uid", "Jan Kowalski")
    assert row is not None
    assert row["Miasto"] == "Kraków"


@pytest.mark.asyncio
async def test_find_client_row_returns_none_when_no_match():
    with patch("tests_e2e.sheets_verify.get_all_clients", new=AsyncMock(return_value=[])):
        row = await find_client_row("uid", "Nieistniejący")
    assert row is None


# ── assert_row_field / assert_row_field_equals ─────────────────────────────


def test_assert_row_field_substring_match():
    row = {"Notatki": "Klient ma duży dom i lubi PV-kę"}
    ok, _ = assert_row_field(row, "Notatki", "ma duży dom")
    assert ok is True


def test_assert_row_field_case_insensitive():
    row = {"Status": "Spotkanie umówione"}
    ok, _ = assert_row_field(row, "Status", "SPOTKANIE")
    assert ok is True


def test_assert_row_field_negative_when_missing():
    row = {"Notatki": "puste"}
    ok, detail = assert_row_field(row, "Notatki", "duży dom")
    assert ok is False
    assert "does NOT contain" in detail


def test_assert_row_field_handles_missing_key():
    ok, detail = assert_row_field({}, "Email", "x")
    assert ok is False
    assert "''" in detail or "empty" in detail.lower() or "not contain" in detail.lower()


def test_assert_row_field_equals_strict_match():
    row = {"Status": "Podpisane"}
    ok, _ = assert_row_field_equals(row, "Status", "Podpisane")
    assert ok is True


def test_assert_row_field_equals_case_insensitive_trim():
    row = {"Status": "  Podpisane  "}
    ok, _ = assert_row_field_equals(row, "Status", "podpisane")
    assert ok is True


def test_assert_row_field_equals_substring_does_not_match():
    row = {"Status": "Spotkanie umówione"}
    ok, _ = assert_row_field_equals(row, "Status", "Spotkanie")
    assert ok is False  # substring isn't enough for `_equals`


# ── find_synthetic_rows ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_find_synthetic_rows_excludes_non_e2e():
    rows = [
        {"Imię i nazwisko": "E2E-Beta-Tester-143052-B01", "Miasto": "X", "_row": 1},
        {"Imię i nazwisko": "Real Client Name", "Miasto": "Y", "_row": 2},
        {"Imię i nazwisko": "E2E-Beta-Fixture-Jan-Kowalski", "Miasto": "Z", "_row": 3},
    ]
    with patch("tests_e2e.sheets_verify.get_all_clients", new=AsyncMock(return_value=rows)):
        out = await find_synthetic_rows("uid")
    names = [r["Imię i nazwisko"] for r in out]
    assert "Real Client Name" not in names
    assert "E2E-Beta-Tester-143052-B01" in names
    # Fixture excluded by default
    assert "E2E-Beta-Fixture-Jan-Kowalski" not in names


@pytest.mark.asyncio
async def test_find_synthetic_rows_include_fixtures_true():
    rows = [
        {"Imię i nazwisko": "E2E-Beta-Fixture-Jan-Kowalski", "_row": 3},
    ]
    with patch("tests_e2e.sheets_verify.get_all_clients", new=AsyncMock(return_value=rows)):
        out = await find_synthetic_rows("uid", include_fixtures=True)
    assert len(out) == 1


@pytest.mark.asyncio
async def test_find_synthetic_rows_run_id_filter():
    rows = [
        {"Imię i nazwisko": "E2E-Beta-Tester-143052-B01", "_row": 1},
        {"Imię i nazwisko": "E2E-Beta-Tester-150000-B02", "_row": 2},
    ]
    with patch("tests_e2e.sheets_verify.get_all_clients", new=AsyncMock(return_value=rows)):
        out = await find_synthetic_rows("uid", run_id="143052")
    assert len(out) == 1
    assert "143052" in out[0]["Imię i nazwisko"]


# ── delete_synthetic_rows ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_synthetic_rows_iterates_descending():
    """Must delete from highest _row downward to avoid index shifts."""
    rows = [
        {"_row": 5, "Imię i nazwisko": "A"},
        {"_row": 10, "Imię i nazwisko": "B"},
        {"_row": 3, "Imię i nazwisko": "C"},
    ]
    deleted_order = []

    async def fake_delete(uid, rn):
        deleted_order.append(rn)
        return True

    with patch("tests_e2e.sheets_verify.delete_client", new=fake_delete):
        n = await delete_synthetic_rows("uid", rows)
    assert n == 3
    assert deleted_order == [10, 5, 3]


@pytest.mark.asyncio
async def test_delete_synthetic_rows_skips_rows_without_index():
    rows = [{"Imię i nazwisko": "A"}]  # no _row
    with patch("tests_e2e.sheets_verify.delete_client", new=AsyncMock(return_value=True)):
        n = await delete_synthetic_rows("uid", rows)
    assert n == 0


@pytest.mark.asyncio
async def test_delete_synthetic_rows_counts_only_successful():
    rows = [{"_row": 1}, {"_row": 2}]
    results = [True, False]

    async def fake_delete(uid, rn):
        return results.pop(0)

    with patch("tests_e2e.sheets_verify.delete_client", new=fake_delete):
        n = await delete_synthetic_rows("uid", rows)
    assert n == 1
