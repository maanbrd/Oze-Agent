"""Slice 5.2 — commit_add_note pipeline.

Covers the dated-entry contract ([DD.MM.YYYY]: text with colon), the
existing-notes merge separator ("; "), the error-taxonomy handoff
(success=False + error_message="google_down"), and the column-J touch
via update_client_row_touching_contact.

Handler integration (reply copy) sits in tests/handlers/ — this file
stays focused on the pipeline surface.
"""

from datetime import date
from unittest.mock import AsyncMock, patch

import pytest

from shared.mutations import commit_add_note


# ── Format: [DD.MM.YYYY]: text ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_empty_existing_notes_writes_single_entry():
    captured = {}

    async def _fake_update(user_id, row, updates):
        captured.update(updates)
        return True

    with patch(
        "shared.mutations.add_note.update_client_row_touching_contact",
        new=AsyncMock(side_effect=_fake_update),
    ):
        result = await commit_add_note(
            "u1", row=7, note_text="zadzwonił w sprawie oferty",
            existing_notes="", today=date(2026, 4, 21),
        )

    assert result.success is True
    assert result.final_notes == "[21.04.2026]: zadzwonił w sprawie oferty"
    assert captured["Notatki"] == "[21.04.2026]: zadzwonił w sprawie oferty"


@pytest.mark.asyncio
async def test_non_empty_existing_notes_appends_with_semicolon_separator():
    captured = {}

    async def _fake_update(user_id, row, updates):
        captured.update(updates)
        return True

    with patch(
        "shared.mutations.add_note.update_client_row_touching_contact",
        new=AsyncMock(side_effect=_fake_update),
    ):
        result = await commit_add_note(
            "u1", row=7, note_text="oddzwonił",
            existing_notes="[15.04.2026]: pierwsza rozmowa",
            today=date(2026, 4, 21),
        )

    assert result.success is True
    assert result.final_notes == (
        "[15.04.2026]: pierwsza rozmowa; [21.04.2026]: oddzwonił"
    )
    assert captured["Notatki"] == result.final_notes


@pytest.mark.asyncio
async def test_colon_after_date_bracket_regression_guard():
    """Contract: `[DD.MM.YYYY]: text` — colon required. If this test starts
    failing, user-visible note history will drift from the documented format.
    """
    with patch(
        "shared.mutations.add_note.update_client_row_touching_contact",
        new=AsyncMock(return_value=True),
    ):
        result = await commit_add_note(
            "u1", row=7, note_text="x",
            existing_notes="", today=date(2026, 4, 21),
        )
    assert result.final_notes is not None
    assert "]:" in result.final_notes
    assert "] :" not in result.final_notes   # no space before colon
    assert result.final_notes.startswith("[21.04.2026]: ")


# ── Sheets failure ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sheets_failure_returns_google_down_error():
    with patch(
        "shared.mutations.add_note.update_client_row_touching_contact",
        new=AsyncMock(return_value=False),
    ):
        result = await commit_add_note(
            "u1", row=7, note_text="x",
            existing_notes="", today=date(2026, 4, 21),
        )
    assert result.success is False
    assert result.error_message == "google_down"
    assert result.final_notes is None


# ── Column J auto-touch via wrapper ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_uses_update_client_row_touching_contact_for_auto_j():
    """Pipeline must route through update_client_row_touching_contact so
    column J (Data ostatniego kontaktu) is bumped automatically. We assert
    by name — this is the contract that keeps the pipeline-tier docs honest.
    """
    with patch(
        "shared.mutations.add_note.update_client_row_touching_contact",
        new=AsyncMock(return_value=True),
    ) as mock_touch:
        await commit_add_note(
            "u-42", row=11, note_text="foo", existing_notes="",
            today=date(2026, 4, 21),
        )

    mock_touch.assert_awaited_once()
    args = mock_touch.await_args.args
    assert args[0] == "u-42"
    assert args[1] == 11
    assert args[2] == {"Notatki": "[21.04.2026]: foo"}
