"""Derive the R6 active client from recent conversation history."""

import re
from datetime import timedelta

from shared.clients import lookup_client
from shared.database import get_conversation_history
from shared.google_sheets import get_all_clients
from shared.search import normalize_polish

HISTORY_LIMIT = 10
HISTORY_SINCE = timedelta(minutes=30)

_NAME_RE = re.compile(
    r"\b[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]{2,}\s+"
    r"[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż-]{2,}\b"
)


def _known_client_mentions(content: str, clients: list[dict]) -> list[str]:
    normalized_content = normalize_polish(content)
    mentions: list[str] = []
    for client in clients:
        name = (client.get("Imię i nazwisko") or "").strip()
        if not name:
            continue
        if normalize_polish(name) in normalized_content:
            mentions.append(name)
    return mentions


def _regex_mentions(content: str) -> list[str]:
    seen = set()
    mentions: list[str] = []
    for match in _NAME_RE.finditer(content):
        name = match.group(0).strip()
        key = normalize_polish(name)
        if key in seen:
            continue
        seen.add(key)
        mentions.append(name)
    return mentions


async def _resolve_unique(user_id: str, candidates: list[str]) -> dict | None:
    unique_rows: dict[int, dict] = {}
    for candidate in candidates:
        result = await lookup_client(user_id, candidate)
        if result.status != "unique":
            continue
        row = result.clients[0]
        row_id = row.get("_row")
        if row_id is None:
            continue
        unique_rows[row_id] = row
    if len(unique_rows) == 1:
        return next(iter(unique_rows.values()))
    return None


async def derive_active_client(telegram_id: int, user_id: str) -> dict | None:
    """Return the most recent unambiguous client from the R6 rolling window."""
    history = get_conversation_history(
        telegram_id,
        limit=HISTORY_LIMIT,
        since=HISTORY_SINCE,
    )
    if not history:
        return None

    clients = await get_all_clients(user_id)
    if not clients:
        return None

    # Pass 1: prefer exact mentions of known client names in visible bot cards
    # and confirmations. They usually carry the normalized Sheets name.
    for message in reversed(history):
        if message.get("role") != "assistant":
            continue
        content = message.get("content") or ""
        resolved = await _resolve_unique(user_id, _known_client_mentions(content, clients))
        if resolved is not None:
            return resolved

    # Pass 2: exact known-name mentions from user messages.
    for message in reversed(history):
        if message.get("role") != "user":
            continue
        content = message.get("content") or ""
        resolved = await _resolve_unique(user_id, _known_client_mentions(content, clients))
        if resolved is not None:
            return resolved

    # Pass 3: conservative full-name regex fallback.
    for message in reversed(history):
        content = message.get("content") or ""
        resolved = await _resolve_unique(user_id, _regex_mentions(content))
        if resolved is not None:
            return resolved

    return None
