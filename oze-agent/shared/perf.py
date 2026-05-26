"""Small PII-safe timing helpers.

Logs only a stable operation name and elapsed milliseconds. Callers must keep
operation names generic and never include user text, client names, row numbers,
addresses, phone numbers, emails, or IDs.
"""

import logging
from contextlib import contextmanager
from time import perf_counter
from typing import Iterator


@contextmanager
def log_duration(logger: logging.Logger, operation: str) -> Iterator[None]:
    """Log elapsed milliseconds for a generic operation name."""
    start = perf_counter()
    try:
        yield
    finally:
        duration_ms = int((perf_counter() - start) * 1000)
        logger.info("perf op=%s duration_ms=%d", operation, duration_ms)
