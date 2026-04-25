"""Phase 6A — run_morning_brief (scheduler entry + rules).

Mocks Supabase, Calendar, Sheets, and the Telegram Bot to exercise the
full per-user flow without touching any external service.
"""

from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo

import pytest

from shared.proactive.morning_brief import (
    MorningBriefRunResult,
    TERMINAL_STATUSES,
    _fetch_open_next_steps,
    _parse_next_step_date,
    _warsaw_day_bounds,
    run_morning_brief,
)
from shared.errors import ProactiveFetchError

WARSAW = ZoneInfo("Europe/Warsaw")


def _user(
    user_id="u1",
    telegram_id=111,
    last_sent=None,
) -> dict:
    return {
        "id": user_id,
        "telegram_id": telegram_id,
        "last_morning_brief_sent_date": last_sent,
    }


def _today_warsaw() -> date:
    return datetime.now(tz=WARSAW).date()


# ── _parse_next_step_date helper ─────────────────────────────────────────────


def test_parse_next_step_date_iso():
    assert _parse_next_step_date("2026-04-24") == date(2026, 4, 24)


def test_parse_next_step_date_iso_with_time():
    assert _parse_next_step_date("2026-04-24 14:00") == date(2026, 4, 24)


def test_parse_next_step_date_polish_dotted():
    assert _parse_next_step_date("24.04.2026") == date(2026, 4, 24)


def test_parse_next_step_date_excel_serial():
    # 46136 = 2026-04-24 per Excel epoch.
    assert _parse_next_step_date(46136) == date(2026, 4, 24)


def test_parse_next_step_date_empty_returns_none():
    assert _parse_next_step_date("") is None
    assert _parse_next_step_date(None) is None


def test_parse_next_step_date_garbage_returns_none():
    assert _parse_next_step_date("not a date") is None


# ── _fetch_open_next_steps ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_open_next_steps_includes_past_due():
    today = date(2026, 4, 24)
    clients = [
        {
            "Imię i nazwisko": "Jan Kowalski",
            "Status": "Nowy lead",
            "Następny krok": "Telefon",
            "Data następnego kroku": "2026-04-20",
        },
    ]
    with patch(
        "shared.proactive.morning_brief.get_all_clients_or_raise",
        new=AsyncMock(return_value=clients),
    ):
        out = await _fetch_open_next_steps("u1", today)
    assert len(out) == 1
    assert out[0]["name"] == "Jan Kowalski"


@pytest.mark.asyncio
async def test_open_next_steps_includes_due_today():
    today = date(2026, 4, 24)
    clients = [{
        "Imię i nazwisko": "Jan",
        "Status": "Nowy lead",
        "Następny krok": "Telefon",
        "Data następnego kroku": "2026-04-24",
    }]
    with patch(
        "shared.proactive.morning_brief.get_all_clients_or_raise",
        new=AsyncMock(return_value=clients),
    ):
        out = await _fetch_open_next_steps("u1", today)
    assert len(out) == 1


@pytest.mark.asyncio
async def test_open_next_steps_excludes_future():
    today = date(2026, 4, 24)
    clients = [{
        "Imię i nazwisko": "Jan",
        "Status": "Nowy lead",
        "Następny krok": "Telefon",
        "Data następnego kroku": "2026-04-30",
    }]
    with patch(
        "shared.proactive.morning_brief.get_all_clients_or_raise",
        new=AsyncMock(return_value=clients),
    ):
        out = await _fetch_open_next_steps("u1", today)
    assert out == []


@pytest.mark.asyncio
@pytest.mark.parametrize("status", sorted(TERMINAL_STATUSES))
async def test_open_next_steps_excludes_terminal_statuses(status):
    today = date(2026, 4, 24)
    clients = [{
        "Imię i nazwisko": "Jan",
        "Status": status,
        "Następny krok": "Telefon",
        "Data następnego kroku": "2026-04-20",
    }]
    with patch(
        "shared.proactive.morning_brief.get_all_clients_or_raise",
        new=AsyncMock(return_value=clients),
    ):
        out = await _fetch_open_next_steps("u1", today)
    assert out == [], f"{status} should be terminal"


@pytest.mark.asyncio
async def test_open_next_steps_sorted_by_date_ascending():
    today = date(2026, 4, 24)
    clients = [
        {"Imię i nazwisko": "A", "Status": "Nowy lead",
         "Następny krok": "Telefon", "Data następnego kroku": "2026-04-22"},
        {"Imię i nazwisko": "B", "Status": "Nowy lead",
         "Następny krok": "Telefon", "Data następnego kroku": "2026-04-18"},
        {"Imię i nazwisko": "C", "Status": "Nowy lead",
         "Następny krok": "Telefon", "Data następnego kroku": "2026-04-24"},
    ]
    with patch(
        "shared.proactive.morning_brief.get_all_clients_or_raise",
        new=AsyncMock(return_value=clients),
    ):
        out = await _fetch_open_next_steps("u1", today)
    assert [r["name"] for r in out] == ["B", "A", "C"]


@pytest.mark.asyncio
async def test_open_next_steps_skips_rows_without_next_step():
    today = date(2026, 4, 24)
    clients = [{
        "Imię i nazwisko": "Jan",
        "Status": "Nowy lead",
        "Następny krok": "",
        "Data następnego kroku": "2026-04-20",
    }]
    with patch(
        "shared.proactive.morning_brief.get_all_clients_or_raise",
        new=AsyncMock(return_value=clients),
    ):
        out = await _fetch_open_next_steps("u1", today)
    assert out == []


# ── run_morning_brief — dedup, eligibility, rules ────────────────────────────


@pytest.mark.asyncio
async def test_dedup_skips_if_already_sent_today():
    today = _today_warsaw()
    users = [_user(last_sent=today.isoformat())]
    bot = MagicMock()
    bot.send_message = AsyncMock()
    with patch(
        "shared.proactive.morning_brief.get_eligible_users_for_morning_brief",
        return_value=users,
    ), patch(
        "shared.proactive.morning_brief.get_events_for_range_or_raise",
        new=AsyncMock(return_value=[]),
    ), patch(
        "shared.proactive.morning_brief.get_all_clients_or_raise",
        new=AsyncMock(return_value=[]),
    ), patch(
        "shared.proactive.morning_brief.update_last_morning_brief_sent",
    ) as upd:
        result = await run_morning_brief(bot)
    assert result.skipped_deduped == 1
    assert result.sent == 0
    bot.send_message.assert_not_called()
    upd.assert_not_called()


@pytest.mark.asyncio
async def test_dedup_sends_if_last_sent_yesterday():
    today = _today_warsaw()
    yesterday = today - timedelta(days=1)
    users = [_user(last_sent=yesterday.isoformat())]
    bot = MagicMock()
    bot.send_message = AsyncMock()
    with patch(
        "shared.proactive.morning_brief.get_eligible_users_for_morning_brief",
        return_value=users,
    ), patch(
        "shared.proactive.morning_brief.get_events_for_range_or_raise",
        new=AsyncMock(return_value=[]),
    ), patch(
        "shared.proactive.morning_brief.get_all_clients_or_raise",
        new=AsyncMock(return_value=[]),
    ), patch(
        "shared.proactive.morning_brief.update_last_morning_brief_sent",
    ):
        result = await run_morning_brief(bot)
    assert result.sent == 1
    assert result.skipped_deduped == 0
    bot.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_dedup_sends_if_never_sent():
    users = [_user(last_sent=None)]
    bot = MagicMock()
    bot.send_message = AsyncMock()
    with patch(
        "shared.proactive.morning_brief.get_eligible_users_for_morning_brief",
        return_value=users,
    ), patch(
        "shared.proactive.morning_brief.get_events_for_range_or_raise",
        new=AsyncMock(return_value=[]),
    ), patch(
        "shared.proactive.morning_brief.get_all_clients_or_raise",
        new=AsyncMock(return_value=[]),
    ), patch(
        "shared.proactive.morning_brief.update_last_morning_brief_sent",
    ):
        result = await run_morning_brief(bot)
    assert result.sent == 1


@pytest.mark.asyncio
async def test_no_dedup_update_on_send_failure():
    users = [_user(last_sent=None)]
    bot = MagicMock()
    bot.send_message = AsyncMock(side_effect=RuntimeError("Telegram down"))
    with patch(
        "shared.proactive.morning_brief.get_eligible_users_for_morning_brief",
        return_value=users,
    ), patch(
        "shared.proactive.morning_brief.get_events_for_range_or_raise",
        new=AsyncMock(return_value=[]),
    ), patch(
        "shared.proactive.morning_brief.get_all_clients_or_raise",
        new=AsyncMock(return_value=[]),
    ), patch(
        "shared.proactive.morning_brief.update_last_morning_brief_sent",
    ) as upd:
        result = await run_morning_brief(bot)
    assert result.sent == 0
    assert result.skipped_error == 1
    # Critical: the dedup column MUST NOT be bumped on failure — we want
    # the next weekday run to retry this user.
    upd.assert_not_called()


@pytest.mark.asyncio
async def test_error_isolation_one_user_failure_does_not_block_others():
    users = [
        _user(user_id="u1", telegram_id=111, last_sent=None),
        _user(user_id="u2", telegram_id=222, last_sent=None),
        _user(user_id="u3", telegram_id=333, last_sent=None),
    ]
    bot = MagicMock()
    # Middle user's send raises — u1 and u3 must still succeed.
    async def _send(chat_id, text, parse_mode):
        if chat_id == 222:
            raise RuntimeError("per-user outage")
    bot.send_message = AsyncMock(side_effect=_send)
    with patch(
        "shared.proactive.morning_brief.get_eligible_users_for_morning_brief",
        return_value=users,
    ), patch(
        "shared.proactive.morning_brief.get_events_for_range_or_raise",
        new=AsyncMock(return_value=[]),
    ), patch(
        "shared.proactive.morning_brief.get_all_clients_or_raise",
        new=AsyncMock(return_value=[]),
    ), patch(
        "shared.proactive.morning_brief.update_last_morning_brief_sent",
    ):
        result = await run_morning_brief(bot)
    assert result.total_eligible == 3
    assert result.sent == 2
    assert result.skipped_error == 1


@pytest.mark.asyncio
async def test_skips_row_with_missing_telegram_id():
    users = [_user(telegram_id=None)]
    bot = MagicMock()
    bot.send_message = AsyncMock()
    with patch(
        "shared.proactive.morning_brief.get_eligible_users_for_morning_brief",
        return_value=users,
    ):
        result = await run_morning_brief(bot)
    assert result.sent == 0
    assert result.skipped_error == 1
    bot.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_run_morning_brief_returns_correct_counts():
    today = _today_warsaw()
    users = [
        _user(user_id="a", telegram_id=1, last_sent=None),
        _user(user_id="b", telegram_id=2, last_sent=today.isoformat()),
        _user(user_id="c", telegram_id=3, last_sent=None),
    ]
    bot = MagicMock()
    bot.send_message = AsyncMock()
    with patch(
        "shared.proactive.morning_brief.get_eligible_users_for_morning_brief",
        return_value=users,
    ), patch(
        "shared.proactive.morning_brief.get_events_for_range_or_raise",
        new=AsyncMock(return_value=[]),
    ), patch(
        "shared.proactive.morning_brief.get_all_clients_or_raise",
        new=AsyncMock(return_value=[]),
    ), patch(
        "shared.proactive.morning_brief.update_last_morning_brief_sent",
    ):
        result = await run_morning_brief(bot)
    assert result.total_eligible == 3
    assert result.sent == 2
    assert result.skipped_deduped == 1
    assert result.skipped_error == 0


@pytest.mark.asyncio
async def test_rules_empty_day_sends_terminarz_plus_na_dzis():
    users = [_user(last_sent=None)]
    bot = MagicMock()
    bot.send_message = AsyncMock()
    with patch(
        "shared.proactive.morning_brief.get_eligible_users_for_morning_brief",
        return_value=users,
    ), patch(
        "shared.proactive.morning_brief.get_events_for_range_or_raise",
        new=AsyncMock(return_value=[]),
    ), patch(
        "shared.proactive.morning_brief.get_all_clients_or_raise",
        new=AsyncMock(return_value=[]),
    ), patch(
        "shared.proactive.morning_brief.update_last_morning_brief_sent",
    ):
        await run_morning_brief(bot)
    call = bot.send_message.await_args_list[0]
    text = call.kwargs["text"]
    assert text.startswith("Terminarz:")
    assert "Na dziś nie masz spotkań" in text
    # Exactly two lines in the empty case.
    assert text.count("\n") == 1


@pytest.mark.asyncio
async def test_rules_no_events_with_followups_sends_na_dzis_plus_section():
    users = [_user(last_sent=None)]
    clients = [{
        "Imię i nazwisko": "Jan Kowalski",
        "Status": "Nowy lead",
        "Następny krok": "Telefon",
        "Data następnego kroku": _today_warsaw().isoformat(),
    }]
    bot = MagicMock()
    bot.send_message = AsyncMock()
    with patch(
        "shared.proactive.morning_brief.get_eligible_users_for_morning_brief",
        return_value=users,
    ), patch(
        "shared.proactive.morning_brief.get_events_for_range_or_raise",
        new=AsyncMock(return_value=[]),
    ), patch(
        "shared.proactive.morning_brief.get_all_clients_or_raise",
        new=AsyncMock(return_value=clients),
    ), patch(
        "shared.proactive.morning_brief.update_last_morning_brief_sent",
    ):
        await run_morning_brief(bot)
    text = bot.send_message.await_args_list[0].kwargs["text"]
    assert "Terminarz:" in text
    assert "Na dziś nie masz spotkań" in text
    assert "Do dopilnowania dziś:" in text
    assert "Telefon: Jan Kowalski" in text


@pytest.mark.asyncio
async def test_rules_events_only_sends_events_section_only():
    users = [_user(last_sent=None)]
    events = [{
        "event_type": "phone_call",
        "start": "2026-04-24T09:00:00+02:00",
        "title": "Telefon: Jan Kowalski",
    }]
    bot = MagicMock()
    bot.send_message = AsyncMock()
    with patch(
        "shared.proactive.morning_brief.get_eligible_users_for_morning_brief",
        return_value=users,
    ), patch(
        "shared.proactive.morning_brief.get_events_for_range_or_raise",
        new=AsyncMock(return_value=events),
    ), patch(
        "shared.proactive.morning_brief.get_all_clients_or_raise",
        new=AsyncMock(return_value=[]),
    ), patch(
        "shared.proactive.morning_brief.update_last_morning_brief_sent",
    ):
        await run_morning_brief(bot)
    text = bot.send_message.await_args_list[0].kwargs["text"]
    assert "Terminarz:" in text
    assert "Telefon: Jan Kowalski" in text
    assert "Do dopilnowania dziś:" not in text


@pytest.mark.asyncio
async def test_dedup_column_updated_on_successful_send():
    users = [_user(last_sent=None)]
    bot = MagicMock()
    bot.send_message = AsyncMock()
    with patch(
        "shared.proactive.morning_brief.get_eligible_users_for_morning_brief",
        return_value=users,
    ), patch(
        "shared.proactive.morning_brief.get_events_for_range_or_raise",
        new=AsyncMock(return_value=[]),
    ), patch(
        "shared.proactive.morning_brief.get_all_clients_or_raise",
        new=AsyncMock(return_value=[]),
    ), patch(
        "shared.proactive.morning_brief.update_last_morning_brief_sent",
    ) as upd:
        await run_morning_brief(bot)
    upd.assert_called_once_with("u1", _today_warsaw())


@pytest.mark.asyncio
async def test_calendar_error_does_not_send_and_does_not_bump_dedup():
    users = [_user(last_sent=None)]
    bot = MagicMock()
    bot.send_message = AsyncMock()
    with patch(
        "shared.proactive.morning_brief.get_eligible_users_for_morning_brief",
        return_value=users,
    ), patch(
        "shared.proactive.morning_brief.get_events_for_range_or_raise",
        new=AsyncMock(side_effect=ProactiveFetchError("calendar_api_error")),
    ), patch(
        "shared.proactive.morning_brief.get_all_clients_or_raise",
        new=AsyncMock(return_value=[]),
    ), patch(
        "shared.proactive.morning_brief.update_last_morning_brief_sent",
    ) as upd:
        result = await run_morning_brief(bot)

    assert result.sent == 0
    assert result.skipped_error == 1
    bot.send_message.assert_not_called()
    upd.assert_not_called()


@pytest.mark.asyncio
async def test_sheets_error_does_not_send_and_does_not_bump_dedup():
    users = [_user(last_sent=None)]
    bot = MagicMock()
    bot.send_message = AsyncMock()
    with patch(
        "shared.proactive.morning_brief.get_eligible_users_for_morning_brief",
        return_value=users,
    ), patch(
        "shared.proactive.morning_brief.get_events_for_range_or_raise",
        new=AsyncMock(return_value=[]),
    ), patch(
        "shared.proactive.morning_brief.get_all_clients_or_raise",
        new=AsyncMock(side_effect=ProactiveFetchError("sheets_api_error")),
    ), patch(
        "shared.proactive.morning_brief.update_last_morning_brief_sent",
    ) as upd:
        result = await run_morning_brief(bot)

    assert result.sent == 0
    assert result.skipped_error == 1
    bot.send_message.assert_not_called()
    upd.assert_not_called()


def test_warsaw_day_bounds_use_local_midnight():
    start, end = _warsaw_day_bounds(date(2026, 4, 24))

    assert start.isoformat() == "2026-04-24T00:00:00+02:00"
    assert end.isoformat() == "2026-04-25T00:00:00+02:00"


@pytest.mark.asyncio
async def test_run_uses_warsaw_day_bounds_for_calendar_fetch():
    users = [_user(last_sent=None)]
    bot = MagicMock()
    bot.send_message = AsyncMock()
    fetch = AsyncMock(return_value=[])
    with patch(
        "shared.proactive.morning_brief.get_eligible_users_for_morning_brief",
        return_value=users,
    ), patch(
        "shared.proactive.morning_brief._today_warsaw",
        return_value=date(2026, 4, 24),
    ), patch(
        "shared.proactive.morning_brief.get_events_for_range_or_raise",
        new=fetch,
    ), patch(
        "shared.proactive.morning_brief.get_all_clients_or_raise",
        new=AsyncMock(return_value=[]),
    ), patch(
        "shared.proactive.morning_brief.update_last_morning_brief_sent",
        return_value=True,
    ):
        result = await run_morning_brief(bot)

    assert result.sent == 1
    _, start, end = fetch.await_args.args
    assert start.isoformat() == "2026-04-24T00:00:00+02:00"
    assert end.isoformat() == "2026-04-25T00:00:00+02:00"


@pytest.mark.asyncio
async def test_dedup_write_failure_still_counts_as_sent_and_logs(caplog):
    users = [_user(last_sent=None)]
    bot = MagicMock()
    bot.send_message = AsyncMock()
    with patch(
        "shared.proactive.morning_brief.get_eligible_users_for_morning_brief",
        return_value=users,
    ), patch(
        "shared.proactive.morning_brief.get_events_for_range_or_raise",
        new=AsyncMock(return_value=[]),
    ), patch(
        "shared.proactive.morning_brief.get_all_clients_or_raise",
        new=AsyncMock(return_value=[]),
    ), patch(
        "shared.proactive.morning_brief.update_last_morning_brief_sent",
        return_value=False,
    ):
        result = await run_morning_brief(bot)

    assert result.sent == 1
    assert "morning_brief.dedup_write_failed" in caplog.text
    assert "possible_double_send_risk=True" in caplog.text


@pytest.mark.asyncio
async def test_calendar_ok_but_sheets_fails_no_partial_send():
    users = [_user(last_sent=None)]
    bot = MagicMock()
    bot.send_message = AsyncMock()
    events = [{"event_type": "phone_call", "start": "2026-04-24T09:00:00+02:00", "title": "Telefon: Jan"}]
    with patch(
        "shared.proactive.morning_brief.get_eligible_users_for_morning_brief",
        return_value=users,
    ), patch(
        "shared.proactive.morning_brief.get_events_for_range_or_raise",
        new=AsyncMock(return_value=events),
    ), patch(
        "shared.proactive.morning_brief.get_all_clients_or_raise",
        new=AsyncMock(side_effect=ProactiveFetchError("sheets_api_error")),
    ), patch(
        "shared.proactive.morning_brief.update_last_morning_brief_sent",
    ) as upd:
        result = await run_morning_brief(bot)

    assert result.sent == 0
    assert result.skipped_error == 1
    bot.send_message.assert_not_called()
    upd.assert_not_called()


# ── Result dataclass ─────────────────────────────────────────────────────────


def test_result_dataclass_default_zero():
    r = MorningBriefRunResult()
    assert r.sent == 0
    assert r.total_eligible == 0
    assert r.skipped_deduped == 0
    assert r.skipped_error == 0
