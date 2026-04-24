"""Shared exception types for OZE-Agent."""


class ProactiveFetchError(Exception):
    """Raised when proactive jobs cannot trust fetched external data.

    Strict fetch variants use this to distinguish a legitimate empty response
    from missing config, auth failures, or API outages.
    """
