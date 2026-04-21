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

from shared.google_sheets import (
    _digits_only,
    _is_phone_query,
    get_all_clients,
    search_clients,
)
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


def _phone_variants(value: str) -> set[str]:
    """Return exact phone representations considered equivalent.

    Polish numbers may be stored with or without the +48 prefix. This keeps
    that equivalence without allowing arbitrary substring matches.
    """
    digits = _digits_only(value)
    if not digits:
        return set()

    variants = {digits}
    if digits.startswith("48") and len(digits) == 11:
        variants.add(digits[2:])
    elif len(digits) == 9:
        variants.add(f"48{digits}")
    return variants


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


async def _lookup_phone_clients(user_id: str, query: str) -> list[dict]:
    query_variants = _phone_variants(query)
    if not query_variants:
        return []

    matches: list[dict] = []
    for client in await get_all_clients(user_id):
        stored_variants = _phone_variants(client.get("Telefon", ""))
        if query_variants & stored_variants:
            matches.append(client)
    return matches


def _best_name_fuzzy_distance(query: str, stored_name: str) -> Optional[int]:
    """Return fuzzy distance only when the stored name itself matches query."""
    query_norm = normalize_polish(query)
    stored_norm = normalize_polish(stored_name)
    if not query_norm or not stored_norm:
        return None

    q_tokens = _meaningful_tokens(query)
    stored_tokens = stored_norm.split()
    if not q_tokens or not stored_tokens:
        return None

    if len(q_tokens) == 1:
        best_token_distance = min(
            levenshtein_distance(q_tokens[0], token) for token in stored_tokens
        )
        if best_token_distance <= 2:
            return best_token_distance
        return None

    token_distances = [
        min(levenshtein_distance(q_token, token) for token in stored_tokens)
        for q_token in q_tokens
    ]
    if all(distance <= 2 for distance in token_distances):
        return sum(token_distances)

    full_distance = levenshtein_distance(query_norm, stored_norm)
    if full_distance <= 2:
        return full_distance
    return None


async def lookup_client(
    user_id: str,
    query: str,
    city: str = "",
) -> ClientLookupResult:
    """Resolve a client query to unique / multi / not_found.

    Rules (Phase 5 plan, Slice 5.1a):
      * Phone query (≥7 digits, ≤4 non-digit chars) → exact digit match,
        accepting only explicit +48/no-prefix equivalence. No fuzzy ever for phones.
      * Name query ≥2 meaningful tokens → accept exact OR first_name_ok matches.
      * Name query 1 token + city given → accept first_name_ok matches whose
        city matches. City mismatch keeps candidates (cross-city warning
        contract preserved) but does not widen the acceptance rule.
      * Name query 1 token without city → require the token to appear as a
        full stored-name token (literal substring on tokenized name). Pure
        fuzzy-only hits fall to `not_found`.
      * Multi-client hits → status=multi regardless of whether city narrows.
    """
    normalized = normalize_polish(query)
    is_phone = _is_phone_query(query)

    if is_phone:
        clients = await _lookup_phone_clients(user_id, query)
        if not clients:
            status = "not_found"
        elif len(clients) == 1:
            status = "unique"
        else:
            status = "multi"
        return ClientLookupResult(
            status=status,
            clients=clients,
            normalized_query=normalized,
            is_phone_query=True,
        )

    raw = await search_clients(user_id, query)
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

    best_row: Optional[dict] = None
    best_distance = 10**6
    for row in raw:
        distance = _best_name_fuzzy_distance(
            name_query,
            row.get("Imię i nazwisko", ""),
        )
        if distance is None:
            continue
        if distance < best_distance:
            best_distance = distance
            best_row = row

    if best_row is None:
        return None
    return FuzzySuggestion(candidate=best_row, distance=best_distance)
