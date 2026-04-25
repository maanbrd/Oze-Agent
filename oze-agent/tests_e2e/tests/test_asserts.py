"""Pure unit tests for tests_e2e.asserts. No Telegram, no Telethon."""

from dataclasses import dataclass, field

from tests_e2e.asserts import (
    assert_cancel_reply,
    assert_field_value,
    assert_missing_field_listed,
    assert_no_banned_phrases,
    assert_no_buttons,
    assert_no_internal_leak,
    assert_pl_date_format,
    assert_routing_card_nowy_aktualizuj,
    assert_three_button_card,
)
from tests_e2e.card_parser import parse_card


# Minimal stand-in for harness._ObservedMessage so we don't need Telethon.
@dataclass
class FakeMessage:
    text: str
    button_labels: list[str] = field(default_factory=list)


# ── 3-button card ────────────────────────────────────────────────────────────


def test_three_button_card_pass():
    msg = FakeMessage(
        "📋 Jan, Warszawa", ["✅ Zapisać", "➕ Dopisać", "❌ Anulować"]
    )
    ok, _ = assert_three_button_card(msg)
    assert ok is True


def test_three_button_card_fail_when_two_buttons():
    msg = FakeMessage("📋 Jan", ["✅ Zapisać", "❌ Anulować"])
    ok, detail = assert_three_button_card(msg)
    assert ok is False
    assert "expected" in detail.lower() or "got" in detail.lower()


def test_three_button_card_fail_when_no_buttons():
    msg = FakeMessage("📋 Jan", [])
    ok, _ = assert_three_button_card(msg)
    assert ok is False


# ── No-buttons (read-only) ───────────────────────────────────────────────────


def test_no_buttons_pass_for_empty_keyboard():
    msg = FakeMessage("📋 Jan Kowalski — Warszawa\nProdukt: PV", [])
    ok, _ = assert_no_buttons(msg)
    assert ok is True


def test_no_buttons_fail_when_buttons_present():
    msg = FakeMessage("📋 Jan", ["✅ Zapisać"])
    ok, _ = assert_no_buttons(msg)
    assert ok is False


# ── Routing buttons ──────────────────────────────────────────────────────────


def test_routing_buttons_pass():
    msg = FakeMessage("Ten klient już jest w arkuszu...", ["Nowy", "Aktualizuj"])
    ok, _ = assert_routing_card_nowy_aktualizuj(msg)
    assert ok is True


def test_routing_buttons_fail_for_three_button():
    msg = FakeMessage("📋 Jan", ["✅ Zapisać", "➕ Dopisać", "❌ Anulować"])
    ok, _ = assert_routing_card_nowy_aktualizuj(msg)
    assert ok is False


# ── PL date format ───────────────────────────────────────────────────────────


def test_pl_date_format_pass_with_canonical():
    text = "Plan na 26.04.2026 (Niedziela)\n14:00 spotkanie"
    ok, _ = assert_pl_date_format(text)
    assert ok is True


def test_pl_date_format_fail_iso_leak():
    text = "Plan na 2026-04-26 14:00"
    ok, detail = assert_pl_date_format(text)
    assert ok is False
    assert "ISO" in detail


def test_pl_date_format_fail_excel_serial_leak():
    text = "Plan na 46137"
    ok, detail = assert_pl_date_format(text)
    assert ok is False
    assert "Excel" in detail


def test_pl_date_format_pass_when_no_dates_at_all():
    text = "Anulowane."
    ok, _ = assert_pl_date_format(text)
    assert ok is True


def test_pl_date_format_fails_when_year_present_but_no_pl_format():
    text = "Spotkanie odbyło się w 2026 roku"
    ok, detail = assert_pl_date_format(text)
    assert ok is False
    assert "DD.MM.YYYY" in detail


# ── Banned phrases ───────────────────────────────────────────────────────────


def test_no_banned_phrases_pass():
    text = "Karta klienta. Status: Oferta wysłana."
    ok, _ = assert_no_banned_phrases(text)
    assert ok is True


def test_no_banned_phrases_fail_oczywiscie():
    text = "Oczywiście! Z przyjemnością pomogę."
    ok, detail = assert_no_banned_phrases(text)
    assert ok is False
    assert "oczywiście" in detail.lower()


def test_no_banned_phrases_fail_corporate_intro():
    text = "Na podstawie Twojej wiadomości przygotowałem..."
    ok, _ = assert_no_banned_phrases(text)
    assert ok is False


def test_no_banned_phrases_fail_closing():
    text = "Daj znać jak coś."
    ok, _ = assert_no_banned_phrases(text)
    assert ok is False


# ── Internal leak ────────────────────────────────────────────────────────────


def test_no_internal_leak_pass():
    text = "📋 Jan Kowalski, Warszawa\nProdukt: PV"
    ok, _ = assert_no_internal_leak(text)
    assert ok is True


def test_no_internal_leak_fail():
    text = "Wiersz: 5\n_row=5"
    ok, detail = assert_no_internal_leak(text)
    assert ok is False
    assert "_row" in detail


# ── Cancel reply ─────────────────────────────────────────────────────────────


def test_cancel_reply_pass_canonical():
    msg = FakeMessage("🫡 Anulowane.")
    ok, _ = assert_cancel_reply(msg)
    assert ok is True


def test_cancel_reply_pass_warning_emoji():
    msg = FakeMessage("⚠️ Anulowane.")
    ok, _ = assert_cancel_reply(msg)
    assert ok is True


def test_cancel_reply_pass_no_emoji():
    msg = FakeMessage("Anulowane.")
    ok, _ = assert_cancel_reply(msg)
    assert ok is True


def test_cancel_reply_fail_no_keyword():
    msg = FakeMessage("Coś innego.")
    ok, _ = assert_cancel_reply(msg)
    assert ok is False


def test_cancel_reply_fail_too_long():
    msg = FakeMessage("Anulowane.\nLinia 2.\nLinia 3.")
    ok, detail = assert_cancel_reply(msg)
    assert ok is False
    assert "too long" in detail


# ── ParsedCard helpers ───────────────────────────────────────────────────────


def test_assert_missing_field_listed_pass():
    card = parse_card("📋 Jan, Warszawa\n❓ Brakuje: email, telefon")
    ok, _ = assert_missing_field_listed(card, "email")
    assert ok is True


def test_assert_missing_field_listed_case_insensitive():
    card = parse_card("📋 Jan, Warszawa\n❓ Brakuje: Email, Telefon")
    ok, _ = assert_missing_field_listed(card, "EMAIL")
    assert ok is True


def test_assert_missing_field_listed_fail():
    card = parse_card("📋 Jan, Warszawa\n❓ Brakuje: telefon")
    ok, detail = assert_missing_field_listed(card, "email")
    assert ok is False
    assert "email" in detail.lower()


def test_assert_field_value_pass():
    card = parse_card("📋 Jan, Warszawa\nProdukt: PV")
    ok, _ = assert_field_value(card, "Produkt", "PV")
    assert ok is True


def test_assert_field_value_fail_when_missing():
    card = parse_card("📋 Jan, Warszawa")
    ok, _ = assert_field_value(card, "Produkt", "PV")
    assert ok is False


def test_assert_field_value_fail_when_value_mismatch():
    card = parse_card("📋 Jan, Warszawa\nProdukt: Pompa ciepła")
    ok, _ = assert_field_value(card, "Produkt", "PV")
    assert ok is False
