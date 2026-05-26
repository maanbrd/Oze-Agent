"""Pure tests for post-campaign app smoke configuration."""

from types import SimpleNamespace

import pytest

from tests_e2e import post_campaign_checks as checks
from tests_e2e.harness import _ObservedMessage


def test_post_campaign_cli_accepts_photo_and_offer_run_counts():
    args = checks._parse_args([
        "--photo-runs",
        "3",
        "--offer-runs",
        "2",
        "--report",
        "/tmp/report.md",
    ])

    assert args.photo_runs == 3
    assert args.offer_runs == 2
    assert args.report == "/tmp/report.md"


def test_offer_runs_require_controlled_recipient(monkeypatch):
    args = checks._parse_args(["--photo-runs", "0", "--offer-runs", "1"])
    monkeypatch.delenv(checks.OFFER_RECIPIENT_ENV, raising=False)

    error = checks.validate_post_campaign_args(args)

    assert error == f"{checks.OFFER_RECIPIENT_ENV} is required when --offer-runs > 0"


def test_zero_runs_are_rejected():
    args = checks._parse_args(["--photo-runs", "0", "--offer-runs", "0"])

    error = checks.validate_post_campaign_args(args)

    assert error == "at least one post-campaign app run is required"


def test_ready_offer_numbers_accepts_numbered_template_dicts():
    ready = [
        {"number": 1, "name": "PV"},
        {"number": "2", "name": "Magazyn"},
    ]

    assert checks._ready_offer_numbers(ready) == [1, 2]


def test_offer_smoke_client_name_avoids_offer_trigger_word():
    name = checks._offer_smoke_client_name("211559")

    assert name == "E2E Beta Klient 211559"
    assert "oferta" not in name.lower()


def test_find_matching_card_ignores_wrong_button_card():
    voice_card = _ObservedMessage(
        id=1,
        text="🎙 Transkrypcja:\n\nDodaj spotkanie z E2E Beta Tester",
        date_iso="",
        button_labels=["✅ Zapisz", "❌ Anuluj"],
    )
    add_client_card = _ObservedMessage(
        id=2,
        text="📋 E2E Beta Klient 211559, Opole\nZapisać / dopisać / anulować?",
        date_iso="",
        button_labels=["✅ Zapisać", "➕ Dopisać", "❌ Anulować"],
    )

    match = checks._find_matching_card_message(
        [voice_card, add_client_card],
        required_buttons=("✅ Zapisać", "❌ Anulować"),
        text_markers=("E2E Beta Klient 211559",),
    )

    assert match == add_client_card


def test_cleanup_offer_attempts_deletes_only_matching_client():
    calls = []

    class FakeQuery:
        def __init__(self, table_name, op):
            self.table_name = table_name
            self.op = op
            self.filters = []

        def delete(self):
            calls.append(("delete", self.table_name))
            return FakeQuery(self.table_name, "delete")

        def eq(self, key, value):
            self.filters.append((key, value))
            return self

        def execute(self):
            calls.append((self.op, self.table_name, tuple(self.filters)))
            return SimpleNamespace(data=[])

    class FakeClient:
        def table(self, table_name):
            calls.append(("table", table_name))
            return FakeQuery(table_name, "select")

    class FakeRepo:
        client = FakeClient()

    checks._cleanup_offer_attempts_for_client(
        FakeRepo(),
        user_id="user-1",
        name="E2E Beta Klient 211559",
        city="Opole",
    )

    assert calls == [
        ("table", "offer_send_attempts"),
        ("delete", "offer_send_attempts"),
        (
            "delete",
            "offer_send_attempts",
            (
                ("user_id", "user-1"),
                ("client_name", "E2E Beta Klient 211559"),
                ("client_city", "Opole"),
            ),
        ),
    ]


@pytest.mark.asyncio
async def test_post_campaign_cleanup_preserves_fixtures_by_default(monkeypatch):
    calls = []

    async def fake_cleanup(telegram_id, **kwargs):
        calls.append((telegram_id, kwargs))
        return {"cleanup_safe": True}

    monkeypatch.setattr(checks, "cleanup_synthetic_data", fake_cleanup)

    report = await checks.cleanup_post_campaign_data(
        SimpleNamespace(admin_telegram_id=1690210103)
    )

    assert report == {"cleanup_safe": True}
    assert calls == [(1690210103, {})]
