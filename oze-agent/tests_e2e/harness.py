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
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from telethon.tl.custom.message import Message

from tests_e2e.config import E2EConfig

logger = logging.getLogger(__name__)


@dataclass
class _ObservedMessage:
    """Thin, test-friendly view of a received Telegram message."""

    id: int
    text: str
    date_iso: str
    button_labels: list[str] = field(default_factory=list)
    raw: Any = None  # underlying Telethon Message — for `click()` and inspection

    @classmethod
    def from_telethon(cls, message: "Message") -> "_ObservedMessage":
        labels: list[str] = []
        # Telethon exposes inline keyboard rows via `message.buttons` (list of
        # lists). Each button has a `.text` attribute. URL-only buttons may
        # not, so guard with getattr.
        try:
            rows = getattr(message, "buttons", None)
            if rows:
                for row in rows:
                    for btn in row:
                        label = getattr(btn, "text", None)
                        if label:
                            labels.append(label)
        except Exception as e:  # pragma: no cover — Telethon edge cases
            logger.debug("button extraction failed for msg %s: %s", message.id, e)

        return cls(
            id=message.id,
            text=message.message or "",
            date_iso=message.date.isoformat() if message.date else "",
            button_labels=labels,
            raw=message,
        )


class HarnessAuthMismatch(RuntimeError):
    """Raised when the authenticated Telethon user is not the configured admin."""


class TelegramE2EHarness:
    """Thin Telethon wrapper for E2E tests. Connect, send, observe, disconnect.

    The inbox buffer is populated by a message event handler registered on
    `__aenter__`. Callers `send()` a command, then `wait_for_messages()`
    blocks until N replies arrive (or timeout).
    """

    def __init__(self, config: E2EConfig) -> None:
        self._config = config
        self._client: Any = None
        self._bot_entity: Any = None
        self._inbox: asyncio.Queue[_ObservedMessage] = asyncio.Queue()
        self._authenticated_user_id: int | None = None
        self._authenticated_username: str | None = None

    # ── Lifecycle ────────────────────────────────────────────────────────────

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

        me = await self._client.get_me()
        self._authenticated_user_id = me.id
        self._authenticated_username = getattr(me, "username", None)

        if self._authenticated_user_id != self._config.admin_telegram_id:
            logger.warning(
                "harness.auth_id_mismatch authenticated=%s admin_id=%s — "
                "scenarios may fail admin checks",
                self._authenticated_user_id,
                self._config.admin_telegram_id,
            )

        self._bot_entity = await self._client.get_entity(self._config.bot_username)

        # Install new-message handler *before* sending anything, so we do
        # not race with the bot's replies.
        @self._client.on(events.NewMessage(from_users=self._bot_entity))
        async def _on_new(event):
            observed = _ObservedMessage.from_telethon(event.message)
            await self._inbox.put(observed)

        logger.info(
            "e2e_harness.connected bot=%s admin_id=%s authenticated_id=%s",
            self._config.bot_username,
            self._config.admin_telegram_id,
            self._authenticated_user_id,
        )
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._client is not None:
            await self._client.disconnect()
            self._client = None
        self._bot_entity = None
        logger.info("e2e_harness.disconnected")

    # ── Identity ────────────────────────────────────────────────────────────

    @property
    def authenticated_user_id(self) -> int | None:
        return self._authenticated_user_id

    @property
    def authenticated_username(self) -> str | None:
        return self._authenticated_username

    def is_authenticated_as_admin(self) -> bool:
        """True when Telethon is logged in as the configured admin id."""
        return (
            self._authenticated_user_id is not None
            and self._authenticated_user_id == self._config.admin_telegram_id
        )

    # ── Inbox ────────────────────────────────────────────────────────────────

    async def _drain_inbox(self) -> int:
        """Discard any buffered messages. Returns count drained."""
        n = 0
        while not self._inbox.empty():
            try:
                self._inbox.get_nowait()
                n += 1
            except asyncio.QueueEmpty:
                break
        return n

    # ── Send ────────────────────────────────────────────────────────────────

    async def send(self, text: str) -> None:
        """Send a message/command as the test user to the configured bot.

        Drains stale inbox before sending so callers see only the bot's
        reply to *this* send.
        """
        if self._client is None or self._bot_entity is None:
            raise RuntimeError("Harness not connected (use 'async with').")
        await self._drain_inbox()
        await self._client.send_message(self._bot_entity, text)
        logger.info("e2e_harness.sent text=%r", text)

    async def click_button(
        self,
        message: _ObservedMessage,
        label: str,
    ) -> None:
        """Click an inline keyboard button on a previously observed message.

        Order: drain inbox first (so the click reply is the only fresh
        message), then click. After this call, use `wait_for_messages`
        / `collect_messages` to read replies.
        """
        if self._client is None:
            raise RuntimeError("Harness not connected (use 'async with').")
        if message.raw is None:
            raise RuntimeError(
                f"Cannot click — message {message.id} has no Telethon ref."
            )
        await self._drain_inbox()
        # Telethon: Message.click(text=...) — find button by exact label.
        try:
            await message.raw.click(text=label)
        except Exception as e:
            # Fallback: try by data if the button is a callback button with
            # that label encoded. In practice .click(text=) handles both
            # paths, but keep a clear log if it ever raises.
            logger.error(
                "click_button failed for label=%r on msg=%s err=%s",
                label, message.id, e,
            )
            raise
        logger.info(
            "e2e_harness.clicked label=%r on msg=%s", label, message.id
        )

    # ── Receive ──────────────────────────────────────────────────────────────

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
        loop = asyncio.get_event_loop()
        deadline = loop.time() + duration_s
        while True:
            remaining = deadline - loop.time()
            if remaining <= 0:
                break
            try:
                msg = await asyncio.wait_for(self._inbox.get(), timeout=remaining)
                messages.append(msg)
            except asyncio.TimeoutError:
                break
        return messages
