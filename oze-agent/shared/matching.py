"""Safe client-name matching helpers shared across handlers and services."""

from shared.search import levenshtein_distance, normalize_polish


def first_name_ok(query: str, client: dict) -> bool:
    """Return True if the found client's name safely matches the query.

    For single-word queries: always True (disambiguation handles ambiguity).
    For multi-word queries: every meaningful query token must match a distinct
    token in the stored client name. This prevents "Krzysztof X" from matching
    "Krzysztof Y" just because the first name is shared.
    """
    q_words = [
        normalize_polish(word)
        for word in query.strip().split()
        if len(normalize_polish(word)) > 2
    ]
    if len(q_words) < 2:
        return True

    stored_name = client.get("Imię i nazwisko", "")
    stored_city = client.get("Miasto", client.get("Miejscowość", ""))
    stored_identity = " ".join(p for p in [stored_name, stored_city] if p)
    c_words = [
        normalize_polish(word)
        for word in stored_identity.strip().split()
        if len(normalize_polish(word)) > 2
    ]
    if not c_words:
        return True

    unused = list(c_words)
    for q_word in q_words:
        match_index = next(
            (
                index
                for index, c_word in enumerate(unused)
                if levenshtein_distance(q_word, c_word) <= 2
            ),
            None,
        )
        if match_index is None:
            return False
        unused.pop(match_index)
    return True
