"""Client domain module — lookup + CRUD wrappers."""

from .crud import (
    create_client_row,
    list_all_clients,
    update_client_row_touching_contact,
)
from .find import (
    ClientLookupResult,
    FuzzySuggestion,
    lookup_client,
    suggest_fuzzy_client,
)

__all__ = [
    "ClientLookupResult",
    "FuzzySuggestion",
    "create_client_row",
    "list_all_clients",
    "lookup_client",
    "suggest_fuzzy_client",
    "update_client_row_touching_contact",
]
