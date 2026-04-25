"""Sanity checks executed before any scenario runs.

Catches misconfiguration that would otherwise produce confusing per-scenario
failures (Telethon authenticated as the wrong user, bot username mismatch,
prod bot offline, leftover pending residue from a prior run).
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from tests_e2e.harness import TelegramE2EHarness

logger = logging.getLogger(__name__)


@dataclass
class PreflightResult:
    ok: bool
    findings: list[str]

    def fail(self, msg: str) -> None:
        self.ok = False
        self.findings.append(msg)

    def info(self, msg: str) -> None:
        self.findings.append(msg)


async def run_preflight(harness: TelegramE2EHarness) -> PreflightResult:
    """Verify the harness can drive scenarios safely.

    Checks:
    1. Telethon authenticated as the admin id from config.
    2. Bot entity username matches config (case-insensitive, '@' optional).
    3. Drain any leftover messages in the inbox.
    4. Send a known no-op trigger ('ping') and confirm bot replies within
       30s with a fallback ("Nie zrozumiałem"-class) text. If the bot is
       silent — abort the suite as a blocker.
    """
    result = PreflightResult(ok=True, findings=[])

    # 1. Identity — HARD blocker. Per Codex review: a mismatched login means
    # scenarios run as the wrong account, which can spam unrelated chats and
    # invalidate every admin-gated assertion. Abort before any send.
    if harness.is_authenticated_as_admin():
        result.info(
            f"identity OK — authenticated as admin "
            f"id={harness.authenticated_user_id} "
            f"username={harness.authenticated_username!r}"
        )
    else:
        result.fail(
            f"identity MISMATCH (BLOCKER) — Telethon authenticated as "
            f"id={harness.authenticated_user_id}, "
            f"config admin_id={harness._config.admin_telegram_id}. "
            f"Aborting suite — scenarios MUST run as the configured admin."
        )
        # Short-circuit further checks so we don't ping the bot from a
        # wrong account.
        return result

    # 2. Bot username — bot_entity is set on __aenter__.
    cfg_bot = harness._config.bot_username.lstrip("@").lower()
    bot_entity = getattr(harness, "_bot_entity", None)
    bot_username = getattr(bot_entity, "username", None) if bot_entity else None
    if bot_username and bot_username.lower() != cfg_bot:
        result.fail(
            f"bot username MISMATCH — config={cfg_bot!r}, "
            f"telegram returned={bot_username!r}"
        )
    else:
        result.info(f"bot username OK — {bot_username!r}")

    # 3. Drain stale messages.
    drained = await harness._drain_inbox()
    if drained:
        result.info(f"drained {drained} stale message(s) from inbox")

    # 4. Liveness ping. The bot's fallback handler should reply to any
    #    plain text it doesn't classify. We expect SOMETHING within 30s.
    try:
        await harness.send("ping")
        replies = await harness.wait_for_messages(count=1, timeout_s=30.0)
        if not replies:
            result.fail(
                "bot offline — no reply to 'ping' within 30s. "
                "Aborting suite as a blocker."
            )
        else:
            text = replies[0].text[:120]
            result.info(f"bot responded to liveness ping, text={text!r}")
            # Drain any extra messages the bot may emit after the ping.
            await asyncio.sleep(0.5)
            await harness._drain_inbox()
    except Exception as e:
        result.fail(f"liveness ping failed with exception: {e}")

    # Stamp timing for traceability.
    result.info(f"preflight completed at {datetime.now(tz=timezone.utc).isoformat()}")

    return result
