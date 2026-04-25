"""Slice 5.3 — commit_change_status pipeline.

Covers the single Sheets write (column F) with automatic J touch via
update_client_row_touching_contact, and the error-taxonomy handoff
(success=False + error_message="google_down"). Handler-layer R7
behaviour sits in tests/handlers/test_change_status_confirm.py.
"""

from datetime import date
from unittest.mock import AsyncMock, patch

import pytest

from shared.mutations import ChangeStatusResult, commit_change_status


@pytest.mark.asyncio
async def test_success_writes_status_column_and_returns_true():
    captured = {}

    async def _fake_update(user_id, row, updates):
        captured.update(updates)
        return True

    with patch(
        "shared.mutations.change_status.update_client_row_touching_contact",
        new=AsyncMock(side_effect=_fake_update),
    ):
        result = await commit_change_status(
            "u1", row=7, new_status="Podpisane", today=date(2026, 4, 21),
        )

    assert isinstance(result, ChangeStatusResult)
    assert result.success is True
    assert result.error_message is None
    assert captured == {"Status": "Podpisane"}


@pytest.mark.asyncio
async def test_sheets_failure_returns_google_down():
    with patch(
        "shared.mutations.change_status.update_client_row_touching_contact",
        new=AsyncMock(return_value=False),
    ):
        result = await commit_change_status(
            "u1", row=7, new_status="Podpisane", today=date(2026, 4, 21),
        )
    assert result.success is False
    assert result.error_message == "google_down"


@pytest.mark.asyncio
async def test_uses_update_client_row_touching_contact_for_auto_j():
    """Pipeline must route through the touching wrapper so column J
    (Data ostatniego kontaktu) is bumped automatically — no duplicate
    stamping in handler code."""
    with patch(
        "shared.mutations.change_status.update_client_row_touching_contact",
        new=AsyncMock(return_value=True),
    ) as mock_touch:
        await commit_change_status(
            "u-42", row=11, new_status="Spotkanie umówione", today=date(2026, 4, 21),
        )

    mock_touch.assert_awaited_once()
    args = mock_touch.await_args.args
    assert args[0] == "u-42"
    assert args[1] == 11
    assert args[2] == {"Status": "Spotkanie umówione"}


def test_result_does_not_carry_old_status():
    """Handler already has old_value in flow_data for the comparison card;
    pipeline result intentionally stays minimal. If this ever grows an
    old_status field we'd have two sources of truth for the same string.
    """
    import dataclasses

    fields = {f.name for f in dataclasses.fields(ChangeStatusResult)}
    assert fields == {"success", "error_message"}
