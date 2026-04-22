"""Slice 5.5 + 5.5a — commit_add_client / commit_update_client_fields.

Covers the thin pipeline surface: success returns row (add) or success
flag (update); Sheets failure (None / False) maps to
error_message="google_down". No user-facing copy is asserted here —
that sits in handler tests.
"""

from unittest.mock import AsyncMock, patch

import pytest

from shared.mutations import commit_add_client, commit_update_client_fields


# ── commit_add_client ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_commit_add_client_success():
    with patch(
        "shared.mutations.add_client.create_client_row",
        new=AsyncMock(return_value=42),
    ):
        result = await commit_add_client(
            "u1",
            {"Imię i nazwisko": "Jan Kowalski", "Miasto": "Warszawa"},
        )
    assert result.success is True
    assert result.row == 42
    assert result.error_message is None


@pytest.mark.asyncio
async def test_commit_add_client_sheets_fail_returns_google_down():
    with patch(
        "shared.mutations.add_client.create_client_row",
        new=AsyncMock(return_value=None),
    ):
        result = await commit_add_client(
            "u1",
            {"Imię i nazwisko": "Jan Kowalski"},
        )
    assert result.success is False
    assert result.row is None
    assert result.error_message == "google_down"


# ── commit_update_client_fields ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_commit_update_client_fields_success():
    with patch(
        "shared.mutations.add_client.update_client_row_touching_contact",
        new=AsyncMock(return_value=True),
    ):
        result = await commit_update_client_fields(
            "u1", 7, {"Telefon": "600111222"}
        )
    assert result.success is True
    assert result.error_message is None


@pytest.mark.asyncio
async def test_commit_update_client_fields_fail_returns_google_down():
    with patch(
        "shared.mutations.add_client.update_client_row_touching_contact",
        new=AsyncMock(return_value=False),
    ):
        result = await commit_update_client_fields(
            "u1", 7, {"Telefon": "600111222"}
        )
    assert result.success is False
    assert result.error_message == "google_down"
