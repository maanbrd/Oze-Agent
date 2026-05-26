"""Per-update/job request context for safe, short-lived caches."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Iterator, TypeVar


@dataclass
class RequestCache:
    users_by_id: dict[str, dict | None] = field(default_factory=dict)
    users_by_telegram_id: dict[int, dict | None] = field(default_factory=dict)
    all_clients_by_user_id: dict[str, list[dict]] = field(default_factory=dict)


_current_cache: ContextVar[RequestCache | None] = ContextVar("oze_request_cache", default=None)

F = TypeVar("F", bound=Callable[..., Any])


@contextmanager
def request_context() -> Iterator[RequestCache]:
    """Create an isolated cache for one Telegram update or scheduled job."""
    token = _current_cache.set(RequestCache())
    try:
        cache = _current_cache.get()
        assert cache is not None
        yield cache
    finally:
        _current_cache.reset(token)


def current_request_cache() -> RequestCache | None:
    return _current_cache.get()


def with_request_context(handler: F) -> F:
    """Wrap an async PTB handler in a request context."""

    @wraps(handler)
    async def _wrapped(*args, **kwargs):
        with request_context():
            return await handler(*args, **kwargs)

    return _wrapped  # type: ignore[return-value]


def get_cached_user_by_id(user_id: str) -> dict | None:
    cache = current_request_cache()
    if cache is None:
        raise KeyError(user_id)
    if user_id not in cache.users_by_id:
        raise KeyError(user_id)
    return cache.users_by_id[user_id]


def get_cached_user_by_telegram_id(telegram_id: int) -> dict | None:
    cache = current_request_cache()
    if cache is None:
        raise KeyError(telegram_id)
    if telegram_id not in cache.users_by_telegram_id:
        raise KeyError(telegram_id)
    return cache.users_by_telegram_id[telegram_id]


def cache_user(user: dict | None) -> None:
    cache = current_request_cache()
    if cache is None or not user:
        return
    user_id = user.get("id")
    telegram_id = user.get("telegram_id")
    if user_id:
        cache.users_by_id[str(user_id)] = user
    if telegram_id is not None:
        try:
            cache.users_by_telegram_id[int(telegram_id)] = user
        except (TypeError, ValueError):
            pass


def cache_missing_user_by_id(user_id: str) -> None:
    cache = current_request_cache()
    if cache is not None:
        cache.users_by_id[user_id] = None


def cache_missing_user_by_telegram_id(telegram_id: int) -> None:
    cache = current_request_cache()
    if cache is not None:
        cache.users_by_telegram_id[telegram_id] = None


def refresh_cached_user(user_id: str, user: dict | None) -> None:
    cache = current_request_cache()
    if cache is None:
        return
    if user:
        cache_user(user)
        return
    old = cache.users_by_id.pop(user_id, None)
    if old and old.get("telegram_id") is not None:
        try:
            cache.users_by_telegram_id.pop(int(old["telegram_id"]), None)
        except (TypeError, ValueError):
            pass


def get_cached_all_clients(user_id: str) -> list[dict]:
    cache = current_request_cache()
    if cache is None or user_id not in cache.all_clients_by_user_id:
        raise KeyError(user_id)
    return cache.all_clients_by_user_id[user_id]


def cache_all_clients(user_id: str, clients: list[dict]) -> None:
    cache = current_request_cache()
    if cache is not None:
        cache.all_clients_by_user_id[user_id] = clients


def invalidate_all_clients(user_id: str) -> None:
    cache = current_request_cache()
    if cache is not None:
        cache.all_clients_by_user_id.pop(user_id, None)
