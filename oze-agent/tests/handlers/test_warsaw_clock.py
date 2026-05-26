from datetime import date, datetime, timezone

import bot.handlers.text as text_handler


def test_today_warsaw_uses_business_timezone(monkeypatch):
    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            value = datetime(2026, 5, 26, 22, 30, tzinfo=timezone.utc)
            if tz is not None:
                return value.astimezone(tz)
            return value.replace(tzinfo=None)

    monkeypatch.setattr(text_handler, "datetime", FixedDateTime)

    assert text_handler._today_warsaw() == date(2026, 5, 27)
