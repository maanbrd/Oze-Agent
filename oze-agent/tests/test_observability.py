"""Unit tests for PII-safe observability helpers."""

from shared.observability import (
    exception_type,
    id_hash,
    summarize_client_data,
    summarize_mapping,
)


def test_id_hash_is_stable_and_does_not_include_raw_identifier():
    first = id_hash("user-123@example.com")
    second = id_hash("user-123@example.com")

    assert first == second
    assert first.startswith("h:")
    assert "user-123" not in first
    assert "example.com" not in first


def test_summarize_mapping_reports_keys_without_values():
    summary = summarize_mapping(
        {
            "Imię i nazwisko": "Jan Kowalski",
            "Telefon": "600100200",
            "Email": "jan@example.com",
        }
    )

    assert summary == {
        "field_count": 3,
        "fields": ["Email", "Imię i nazwisko", "Telefon"],
    }
    assert "Jan Kowalski" not in str(summary)
    assert "600100200" not in str(summary)
    assert "jan@example.com" not in str(summary)


def test_summarize_client_data_keeps_row_and_field_names_only():
    summary = summarize_client_data(
        {
            "_row": 42,
            "Imię i nazwisko": "Anna Nowak",
            "Miasto": "Kraków",
            "Notatki": "treść prywatna",
        }
    )

    assert summary == {
        "row": 42,
        "field_count": 3,
        "fields": ["Imię i nazwisko", "Miasto", "Notatki"],
    }
    assert "Anna" not in str(summary)
    assert "Kraków" not in str(summary)
    assert "treść prywatna" not in str(summary)


def test_exception_type_omits_exception_message():
    exc = ValueError("token abc123 and Jan Kowalski")

    assert exception_type(exc) == "ValueError"
    assert "Jan Kowalski" not in exception_type(exc)
