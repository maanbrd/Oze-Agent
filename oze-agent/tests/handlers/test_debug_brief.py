from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.handlers.debug import debug_brief_command
from shared.proactive.morning_brief import MorningBriefRunResult


def _update(user_id: int):
    update = MagicMock()
    update.effective_user.id = user_id
    update.effective_message.reply_text = AsyncMock()
    return update


@pytest.mark.asyncio
async def test_debug_brief_rejects_non_admin():
    update = _update(111)
    context = MagicMock()

    with patch("bot.handlers.debug.Config.ADMIN_TELEGRAM_ID", "999"), patch(
        "bot.handlers.debug.run_morning_brief", new=AsyncMock()
    ) as run:
        await debug_brief_command(update, context)

    run.assert_not_called()
    update.effective_message.reply_text.assert_awaited_once_with("Brak dostępu.")


@pytest.mark.asyncio
async def test_debug_brief_runs_for_admin():
    update = _update(999)
    context = MagicMock()
    context.bot = MagicMock()
    result = MorningBriefRunResult(total_eligible=1, sent=1)

    with patch("bot.handlers.debug.Config.ADMIN_TELEGRAM_ID", "999"), patch(
        "bot.handlers.debug.run_morning_brief", new=AsyncMock(return_value=result)
    ) as run:
        await debug_brief_command(update, context)

    run.assert_awaited_once_with(context.bot)
    replies = update.effective_message.reply_text.await_args_list
    assert replies[0].args[0] == "Uruchamiam morning brief debug..."
    assert "sent=1" in replies[1].args[0]


@pytest.mark.asyncio
async def test_debug_brief_rejects_when_admin_id_missing():
    update = _update(999)
    context = MagicMock()

    with patch("bot.handlers.debug.Config.ADMIN_TELEGRAM_ID", ""), patch(
        "bot.handlers.debug.run_morning_brief", new=AsyncMock()
    ) as run:
        await debug_brief_command(update, context)

    run.assert_not_called()
    update.effective_message.reply_text.assert_awaited_once_with("Brak dostępu.")
