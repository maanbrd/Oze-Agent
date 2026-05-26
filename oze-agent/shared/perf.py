"""Small PII-safe timing helpers.

Logs only a stable operation name and elapsed milliseconds. Callers must keep
operation names generic and never include user text, client names, row numbers,
addresses, phone numbers, emails, or IDs.
"""

import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from threading import Lock
from time import perf_counter
from typing import Iterator


@dataclass
class _OperationSamples:
    samples: list[int] = field(default_factory=list)
    last_summary_at: float = field(default_factory=perf_counter)


_lock = Lock()
_samples_by_operation: dict[str, _OperationSamples] = {}
_summary_sample_threshold = 100
_summary_interval_seconds = 300


def _percentile(sorted_values: list[int], percentile: float) -> int:
    if not sorted_values:
        return 0
    index = int((len(sorted_values) - 1) * percentile)
    return sorted_values[index]


def _record_duration(operation: str, duration_ms: int) -> tuple[int, int, int, int, int] | None:
    now = perf_counter()
    with _lock:
        bucket = _samples_by_operation.setdefault(operation, _OperationSamples())
        bucket.samples.append(duration_ms)
        enough_samples = len(bucket.samples) >= _summary_sample_threshold
        enough_time = now - bucket.last_summary_at >= _summary_interval_seconds
        if not enough_samples and not enough_time:
            return None
        values = sorted(bucket.samples)
        summary = (
            len(values),
            _percentile(values, 0.50),
            _percentile(values, 0.95),
            _percentile(values, 0.99),
            values[-1],
        )
        bucket.samples = []
        bucket.last_summary_at = now
        return summary


def reset_perf_aggregator_for_tests() -> None:
    with _lock:
        _samples_by_operation.clear()
        global _summary_sample_threshold, _summary_interval_seconds
        _summary_sample_threshold = 100
        _summary_interval_seconds = 300


def configure_perf_aggregator_for_tests(*, sample_threshold: int, interval_seconds: int) -> None:
    with _lock:
        global _summary_sample_threshold, _summary_interval_seconds
        _summary_sample_threshold = sample_threshold
        _summary_interval_seconds = interval_seconds


@contextmanager
def log_duration(logger: logging.Logger, operation: str) -> Iterator[None]:
    """Log elapsed milliseconds for a generic operation name."""
    start = perf_counter()
    try:
        yield
    finally:
        duration_ms = int((perf_counter() - start) * 1000)
        logger.info("perf op=%s duration_ms=%d", operation, duration_ms)
        summary = _record_duration(operation, duration_ms)
        if summary is not None:
            count, p50, p95, p99, max_ms = summary
            logger.info(
                "perf_summary op=%s count=%d p50_ms=%d p95_ms=%d p99_ms=%d max_ms=%d",
                operation,
                count,
                p50,
                p95,
                p99,
                max_ms,
            )
