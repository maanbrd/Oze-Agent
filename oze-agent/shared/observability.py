"""Small PII-safe logging helpers for Agent OZE.

Logs may include stable hashes, row numbers, counts, field names, and exception
classes. They must not include raw client names, phone numbers, emails, message
content, tokens, or offer contents.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any


def id_hash(value: Any, *, length: int = 12) -> str:
    """Return a stable short hash for correlating logs without raw identifiers."""
    text = str(value or "").strip()
    if not text:
        return "h:missing"
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"h:{digest[:length]}"


def _non_empty_keys(data: Mapping[str, Any]) -> list[str]:
    return sorted(str(key) for key, value in data.items() if key != "_row" and value)


def summarize_mapping(data: Mapping[str, Any] | None) -> dict[str, Any]:
    """Summarize a mapping by non-empty keys only, never by values."""
    fields = _non_empty_keys(data or {})
    return {
        "field_count": len(fields),
        "fields": fields,
    }


def summarize_client_data(client: Mapping[str, Any] | None) -> dict[str, Any]:
    """Summarize a client row without exposing CRM values."""
    data = client or {}
    summary = summarize_mapping(data)
    if data.get("_row") is not None:
        summary = {"row": data.get("_row"), **summary}
    return summary


def exception_type(exc: BaseException) -> str:
    """Return only the exception class name; messages can contain PII/secrets."""
    return type(exc).__name__
