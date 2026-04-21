"""Low-level client resolver implementing R4 unique-match semantics.

`lookup_client` filters raw `search_clients` output (which is fuzzy) down to
exact / first_name_ok / phone-exact candidates. Single fuzzy-only matches
never count as `unique` — they fall through to `not_found` so that
`suggest_fuzzy_client` can ask "Chodziło o…?" in show_client.

See /Users/mansoniasty/.claude/plans/eventual-pondering-church.md Slice 5.1a
for the full rule table.
"""

from dataclasses import dataclass
from typing import Literal, Optional

from shared.google_sheets import _is_phone_query, search_clients
from shared.matching import first_name_ok
from shared.search import levenshtein_distance, normalize_polish


@dataclass
class ClientLookupResult:
    status: Literal["unique", "multi", "not_found"]
    clients: list[dict]
    normalized_query: str
    is_phone_query: bool = False


@dataclass
class FuzzySuggestion:
    candidate: dict
    distance: int


def _meaningful_tokens(query: str) -> list[str]:
    return [t for t in normalize_polish(query).split() if len(t) > 2]


def _stored_name_tokens(row: dict) -> list[str]:
    return normalize_polish(row.get("Imię i nazwisko", "")).split()


def _stored_city_norm(row: dict) -> str:
    return normalize_polish(row.get("Miasto", row.get("Miejscowość", "")))


def _is_exact_name_match(query_norm: str, row: dict) -> bool:
    return normalize_polish(row.get("Imię i nazwisko", "")) == query_norm


def _is_literal_single_token_match(q_tokens: list[str], row: dict) -> bool:
    """Query is a single meaningful token — require it to appear verbatim as
    a full token in the stored name. 'Jan' matches 'Jan Kowalski' but 'Kowal'
    does not match 'Kowalski' (that would be fuzzy-only)."""
    if len(q_tokens) != 1:
        return False
    return q_tokens[0] in _stored_name_tokens(row)


async def lookup_client(
    user_id: str,
    query: str,
    city: str = "",
) -> ClientLookupResult:
    """Resolve a client query to unique / multi / not_found.

    Rules (Phase 5 plan, Slice 5.1a):
      * Phone query (≥7 digits, ≤4 non-digit chars) → exact digit match via
        `search_clients` phone path. No fuzzy ever for phones.
      * Name query ≥2 meaningful tokens → accept exact OR first_name_ok matches.
      * Name query 1 token + city given → accept first_name_ok matches whose
        city matches. City mismatch keeps candidates (cross-city warning
        contract preserved) but does not widen the acceptance rule.
      * Name query 1 token without city → require the token to appear as a
        full stored-name token (literal substring on tokenized name). Pure
        fuzzy-only hits fall to `not_found`.
      * Multi-client hits → status=multi regardless of whether city narrows.
    """
    raw = await search_clients(user_id, query)
    normalized = normalize_polish(query)
    is_phone = _is_phone_query(query)

    if is_phone:
        # search_clients phone path is already exact (digits compare)
        if not raw:
            status = "not_found"
        elif len(raw) == 1:
            status = "unique"
        else:
            status = "multi"
        return ClientLookupResult(
            status=status,
            clients=raw,
            normalized_query=normalized,
            is_phone_query=True,
        )

    q_tokens = _meaningful_tokens(query)
    city_norm = normalize_polish(city)

    # Filter fuzzy-only hits out of `raw`.
    candidates: list[dict] = []
    for row in raw:
        if _is_exact_name_match(normalized, row):
            candidates.append(row)
            continue
        if len(q_tokens) >= 2 and first_name_ok(query, row):
            candidates.append(row)
            continue
        if _is_literal_single_token_match(q_tokens, row):
            candidates.append(row)
            continue

    # City narrowing: preserve cross-city warning when narrowing empties.
    if city_norm and candidates:
        same_city = [
            row for row in candidates
            if _stored_city_norm(row) == city_norm
        ]
        if same_city:
            candidates = same_city

    if not candidates:
        status = "not_found"
    elif len(candidates) == 1:
        status = "unique"
    else:
        status = "multi"

    return ClientLookupResult(
        status=status,
        clients=candidates,
        normalized_query=normalized,
        is_phone_query=False,
    )


async def suggest_fuzzy_client(
    user_id: str,
    name_query: str,
) -> Optional[FuzzySuggestion]:
    """Return the closest fuzzy candidate for a name query, if any.

    Use ONLY from `show_client` after `lookup_client` returned `not_found`.
    Do NOT call for phone queries — phone fuzzy suggestions are unsafe per
    INTENCJE_MVP (one-digit typo yields a different person).
    """
    if _is_phone_query(name_query):
        return None

    raw = await search_clients(user_id, name_query)
    if not raw:
        return None

    query_norm = normalize_polish(name_query)
    best_row: Optional[dict] = None
    best_distance = 10**6
    for row in raw:
        stored_norm = normalize_polish(row.get("Imię i nazwisko", ""))
        if not stored_norm:
            continue
        dist = levenshtein_distance(query_norm, stored_norm)
        if dist < best_distance:
            best_distance = dist
            best_row = row

    if best_row is None:
        return None
    return FuzzySuggestion(candidate=best_row, distance=best_distance)
