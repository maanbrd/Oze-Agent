"""Client domain module — lookup + CRUD wrappers."""

from .find import (
    ClientLookupResult,
    FuzzySuggestion,
    lookup_client,
    suggest_fuzzy_client,
)

__all__ = [
    "ClientLookupResult",
    "FuzzySuggestion",
    "lookup_client",
    "suggest_fuzzy_client",
]
