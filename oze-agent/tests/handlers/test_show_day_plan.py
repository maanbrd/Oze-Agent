from datetime import datetime, date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.handlers.text import _parse_show_day_date, handle_show_day_plan


def _update() -> MagicMock:
    upd = MagicMock()
    upd.effective_user.id = 123
    return upd


def test_parse_show_day_date_uses_supplied_warsaw_base_date():
    base = date(2026, 6, 9)

    assert _parse_show_day_date("co mam dziś?", base) == date(2026, 6, 9)
    assert _parse_show_day_date("co mam jutro?", base) == date(2026, 6, 10)


@pytest.mark.asyncio
async def test_handle_show_day_plan_uses_warsaw_local_today_for_relative_dates():
    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            assert tz is not None
            return cls(2026, 6, 9, 1, 5, tzinfo=tz)

    reply = AsyncMock()

    with patch("bot.handlers.text.datetime", FixedDateTime), \
         patch("bot.handlers.text.get_events_for_date", new=AsyncMock(return_value=[])) as events_for_date, \
         patch("bot.handlers.text.reply_markdown_v2", new=reply):
        await handle_show_day_plan(
            _update(),
            MagicMock(),
            {"id": 1},
            {},
            "co mam jutro?",
        )

    events_for_date.assert_awaited_once_with(1, date(2026, 6, 10))
    reply.assert_awaited_once()
    assert "10\\.06\\.2026" in reply.await_args.args[1]
