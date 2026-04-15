"""Fuzzy search engine for OZE-Agent client lookups.

Pure Python — no external dependencies. Handles Polish diacritics.
"""

POLISH_CHARS = str.maketrans(
    "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ",
    "acelnoszzACELNOSZZ",
)


def normalize_polish(text: str) -> str:
    """Lowercase and transliterate Polish diacritics for comparison."""
    return text.lower().translate(POLISH_CHARS).strip()


def levenshtein_distance(s1: str, s2: str) -> int:
    """Standard Levenshtein edit distance."""
    if s1 == s2:
        return 0
    len1, len2 = len(s1), len(s2)
    if len1 == 0:
        return len2
    if len2 == 0:
        return len1

    prev = list(range(len2 + 1))
    for i in range(1, len1 + 1):
        curr = [i] + [0] * len2
        for j in range(1, len2 + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            curr[j] = min(
                curr[j - 1] + 1,        # insertion
                prev[j] + 1,             # deletion
                prev[j - 1] + cost,      # substitution
            )
        prev = curr
    return prev[len2]


def fuzzy_match(
    query: str, candidates: list[str], threshold: int = 2
) -> list[tuple[str, int]]:
    """Return candidates within `threshold` edit distance, sorted by distance.

    Comparison is done on normalized (lowercase, no diacritics) strings.
    Returns list of (original_candidate, distance) tuples.
    """
    q = normalize_polish(query)
    results = []
    for candidate in candidates:
        c = normalize_polish(candidate)
        # Substring match is distance 0
        if q in c or c in q:
            results.append((candidate, 0))
            continue
        # Word-level match
        words = c.split()
        best_word_dist = min(
            (levenshtein_distance(q, w) for w in words),
            default=999,
        )
        if best_word_dist <= threshold:
            results.append((candidate, best_word_dist))
            continue
        # Full string match
        dist = levenshtein_distance(q, c)
        if dist <= threshold:
            results.append((candidate, dist))

    return sorted(results, key=lambda x: x[1])


def search_clients(clients: list[dict], query: str) -> list[dict]:
    """Search clients across name, city, and phone fields.

    Returns matching clients sorted by relevance (best match first).
    """
    if not query or not clients:
        return []

    SEARCH_FIELDS = ["Imię i nazwisko", "Miasto", "Miejscowość", "Telefon", "Email"]

    scored: list[tuple[dict, int]] = []
    for client in clients:
        best_dist = 999
        for field in SEARCH_FIELDS:
            value = client.get(field, "")
            if not value:
                continue
            matches = fuzzy_match(query, [str(value)], threshold=2)
            if matches:
                best_dist = min(best_dist, matches[0][1])
        if best_dist < 999:
            scored.append((client, best_dist))

    scored.sort(key=lambda x: x[1])
    return [c for c, _ in scored]


def find_best_match(query: str, candidates: list[str]) -> str | None:
    """Return the single best matching candidate or None."""
    results = fuzzy_match(query, candidates, threshold=2)
    return results[0][0] if results else None


def detect_potential_duplicate(
    name: str, city: str, existing_clients: list[dict]
) -> dict | None:
    """Check if a client with a similar full name already exists.

    Match rule: full name (≥2 tokens) within Levenshtein distance 2.
    Same/similar city wins over a name-only match; if no same-city match is
    found, the first name-only match is returned as fallback. Missing city on
    either side is allowed — the name match still wins.

    MVP limitation: when multiple same-name clients exist in different cities
    and the new input has no city, we return the first name-only fallback in
    iteration order. A future slice may turn this into an explicit
    disambiguation flow.
    """
    name_norm = normalize_polish(name)
    # Guard against overmatching first-name-only inputs like "Jan".
    if len(name_norm.split()) < 2:
        return None
    city_norm = normalize_polish(city or "")

    name_only_fallback: dict | None = None
    for client in existing_clients:
        existing_name = normalize_polish(client.get("Imię i nazwisko", ""))
        existing_city = normalize_polish(
            client.get("Miasto", client.get("Miejscowość", ""))
        )
        if levenshtein_distance(name_norm, existing_name) > 2:
            continue
        # Same-city match wins immediately (preserves prior behavior).
        if (
            city_norm
            and existing_city
            and levenshtein_distance(city_norm, existing_city) <= 1
        ):
            return client
        if name_only_fallback is None:
            name_only_fallback = client
    return name_only_fallback
