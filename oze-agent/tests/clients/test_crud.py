"""Slice 5.1e — thin CRUD wrappers over shared.google_sheets.

These tests cover exactly two invariants:

1. Passthrough — each wrapper forwards arguments to the underlying
   google_sheets function and returns its result unchanged.

2. Dict copy — neither create_client_row nor update_client_row_touching_contact
   mutates the caller's dict. google_sheets.{add_client,update_client} both
   mutate their passed-in dict (add_client injects 'Data pierwszego kontaktu'
   when missing; update_client injects 'Data ostatniego kontaktu'), and
   mutation pipelines downstream will reuse their local dicts — aliasing
   would be a footgun.
"""

from unittest.mock import AsyncMock, patch

import pytest

from shared.clients import (
    create_client_row,
    list_all_clients,
    update_client_row_touching_contact,
)


# ── create_client_row ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_client_row_returns_row_number():
    with patch(
        "shared.clients.crud.add_client",
        new=AsyncMock(return_value=42),
    ):
        row = await create_client_row("u1", {"Imię i nazwisko": "Jan Kowalski"})
    assert row == 42


@pytest.mark.asyncio
async def test_create_client_row_returns_none_on_failure():
    with patch(
        "shared.clients.crud.add_client",
        new=AsyncMock(return_value=None),
    ):
        row = await create_client_row("u1", {"Imię i nazwisko": "Jan"})
    assert row is None


@pytest.mark.asyncio
async def test_create_client_row_does_not_mutate_caller_dict():
    """google_sheets.add_client mutates its dict (adds Data pierwszego kontaktu).
    The wrapper must copy to keep caller state clean."""
    original = {"Imię i nazwisko": "Jan Kowalski"}
    snapshot = dict(original)

    async def _fake_add_client(user_id, data):
        # Simulate sheets' real mutation behaviour
        data["Data pierwszego kontaktu"] = "2026-04-21"
        return 1

    with patch("shared.clients.crud.add_client", new=AsyncMock(side_effect=_fake_add_client)):
        await create_client_row("u1", original)

    assert original == snapshot
    assert "Data pierwszego kontaktu" not in original


# ── update_client_row_touching_contact ───────────────────────────────────────


@pytest.mark.asyncio
async def test_update_client_row_touching_contact_returns_true_on_success():
    with patch(
        "shared.clients.crud.update_client",
        new=AsyncMock(return_value=True),
    ):
        ok = await update_client_row_touching_contact("u1", 7, {"Status": "Podpisane"})
    assert ok is True


@pytest.mark.asyncio
async def test_update_client_row_touching_contact_does_not_mutate_caller_dict():
    """google_sheets.update_client mutates updates (adds Data ostatniego kontaktu).
    Mutation pipelines (Slices 5.2-5.5) will reuse their local updates dict
    across multiple calls — the wrapper must copy."""
    original = {"Status": "Podpisane"}
    snapshot = dict(original)

    async def _fake_update_client(user_id, row, updates):
        updates["Data ostatniego kontaktu"] = "2026-04-21"
        return True

    with patch(
        "shared.clients.crud.update_client",
        new=AsyncMock(side_effect=_fake_update_client),
    ):
        await update_client_row_touching_contact("u1", 7, original)

    assert original == snapshot
    assert "Data ostatniego kontaktu" not in original


@pytest.mark.asyncio
async def test_update_client_row_touching_contact_forwards_row_and_user():
    captured = {}

    async def _capture(user_id, row, updates):
        captured["user_id"] = user_id
        captured["row"] = row
        captured["updates"] = updates
        return True

    with patch(
        "shared.clients.crud.update_client",
        new=AsyncMock(side_effect=_capture),
    ):
        await update_client_row_touching_contact("user-xyz", 11, {"Notatki": "hello"})

    assert captured["user_id"] == "user-xyz"
    assert captured["row"] == 11
    assert captured["updates"] == {"Notatki": "hello"}


# ── list_all_clients ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_all_clients_passes_through():
    rows = [{"_row": 2, "Imię i nazwisko": "Jan"}, {"_row": 3, "Imię i nazwisko": "Anna"}]
    with patch(
        "shared.clients.crud.get_all_clients",
        new=AsyncMock(return_value=rows),
    ):
        result = await list_all_clients("u1")
    assert result == rows
