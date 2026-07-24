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
    lookup_client_by_row,
    suggest_fuzzy_client,
)
from .identity import ClientIdentityError, build_client_ref, resolve_client_ref

__all__ = [
    "ClientLookupResult",
    "ClientIdentityError",
    "FuzzySuggestion",
    "create_client_row",
    "build_client_ref",
    "list_all_clients",
    "lookup_client",
    "lookup_client_by_row",
    "resolve_client_ref",
    "suggest_fuzzy_client",
    "update_client_row_touching_contact",
]
