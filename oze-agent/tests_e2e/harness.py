"""Telethon-based E2E harness for OZE-Agent Telegram tests.

Acts as a test Telegram user account that sends commands to the bot and
waits for the bot's replies. Designed as a minimal, stable foundation:
the actual test scenarios (see `tests_e2e/scenarios/`) compose these
primitives.

Usage (low-level):

    async with TelegramE2EHarness(config) as h:
        await h.send("/debug_brief")
        messages = await h.wait_for_messages(count=3, timeout_s=60)

Typing/dependency note: Telethon is imported at runtime so `tests_e2e.report`
and `tests_e2e.config` stay importable in environments without telethon
(e.g. the main bot's runtime, CI units that only test report rendering).
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from telethon import TelegramClient
    from telethon.tl.custom.message import Message

from tests_e2e.config import E2EConfig

logger = logging.getLogger(__name__)


@dataclass
class _ObservedMessage:
    """Thin, test-friendly view of a received Telegram message."""

    id: int
    text: str
    date_iso: str
    raw: Any = None

    @classmethod
    def from_telethon(cls, message: "Message") -> "_ObservedMessage":
        return cls(
            id=message.id,
            text=message.message or "",
            date_iso=message.date.isoformat() if message.date else "",
            raw=message,
        )


class TelegramE2EHarness:
    """Thin Telethon wrapper for E2E tests. Connect, send, observe, disconnect.

    The inbox buffer is populated by a message event handler registered on
    `__aenter__`. Callers `send()` a command, then `wait_for_messages()`
    blocks until N replies arrive (or timeout).
    """

    def __init__(self, config: E2EConfig) -> None:
        self._config = config
        self._client: "TelegramClient | None" = None
        self._bot_entity: Any = None
        self._inbox: asyncio.Queue[_ObservedMessage] = asyncio.Queue()

    async def __aenter__(self) -> "TelegramE2EHarness":
        from telethon import TelegramClient, events

        # Ensure parent directory for session file exists (.sessions/e2e
        # by default — session data must not be committed).
        session_path = Path(self._config.session_path)
        session_path.parent.mkdir(parents=True, exist_ok=True)

        self._client = TelegramClient(
            str(session_path),
            self._config.api_id,
            self._config.api_hash,
        )
        # start() is interactive only on first run — it prompts phone/code
        # and persists to the session file. Subsequent runs are silent.
        await self._client.start()

        self._bot_entity = await self._client.get_entity(self._config.bot_username)

        # Install new-message handler *before* sending anything, so we do
        # not race with the bot's replies.
        @self._client.on(events.NewMessage(from_users=self._bot_entity))
        async def _on_new(event):
            observed = _ObservedMessage.from_telethon(event.message)
            await self._inbox.put(observed)

        logger.info(
            "e2e_harness.connected bot=%s admin_id=%s",
            self._config.bot_username,
            self._config.admin_telegram_id,
        )
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._client is not None:
            await self._client.disconnect()
            self._client = None
        self._bot_entity = None
        logger.info("e2e_harness.disconnected")

    async def _drain_inbox(self) -> None:
        """Discard any buffered messages. Call before a fresh `send()` so
        prior run residue does not pollute the next scenario step."""
        while not self._inbox.empty():
            try:
                self._inbox.get_nowait()
            except asyncio.QueueEmpty:
                break

    async def send(self, text: str) -> None:
        """Send a message/command as the test user to the configured bot."""
        if self._client is None or self._bot_entity is None:
            raise RuntimeError("Harness not connected (use 'async with').")
        await self._drain_inbox()
        await self._client.send_message(self._bot_entity, text)
        logger.info("e2e_harness.sent text=%r", text)

    async def wait_for_messages(
        self,
        count: int,
        timeout_s: float = 30.0,
    ) -> list[_ObservedMessage]:
        """Block until `count` replies arrive or the timeout elapses.

        Returns whatever accumulated — the scenario decides whether fewer
        than `count` is a PASS (dedup path) or a FAIL.
        """
        messages: list[_ObservedMessage] = []
        loop = asyncio.get_event_loop()
        deadline = loop.time() + timeout_s
        while len(messages) < count:
            remaining = deadline - loop.time()
            if remaining <= 0:
                break
            try:
                msg = await asyncio.wait_for(self._inbox.get(), timeout=remaining)
                messages.append(msg)
            except asyncio.TimeoutError:
                break
        logger.info(
            "e2e_harness.waited wanted=%d got=%d timeout=%ss",
            count, len(messages), timeout_s,
        )
        return messages

    async def collect_messages(
        self,
        duration_s: float,
    ) -> list[_ObservedMessage]:
        """Collect every message that arrives in the next `duration_s`.

        Use when you do not know the exact reply count upfront — e.g. the
        bot might send 2 OR 3 messages depending on dedup state.
        """
        messages: list[_ObservedMessage] = []
        deadline = asyncio.get_event_loop().time() + duration_s
        while True:
            remaining = deadline - asyncio.get_event_loop().time()
            if remaining <= 0:
                break
            try:
                msg = await asyncio.wait_for(self._inbox.get(), timeout=remaining)
                messages.append(msg)
            except asyncio.TimeoutError:
                break
        return messages
