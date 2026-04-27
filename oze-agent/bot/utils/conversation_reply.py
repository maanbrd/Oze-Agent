"""Telegram reply helpers that persist assistant messages to R6 history."""

import logging
from typing import Any

from shared.database import save_conversation_message

logger = logging.getLogger(__name__)


def _resolve_message(target: Any, method_name: str) -> Any:
    from_user = getattr(target, "from_user", None)
    if isinstance(getattr(from_user, "id", None), int):
        message = getattr(target, "message", None)
        if message is not None:
            return message

    candidates = [
        getattr(target, "effective_message", None),
        getattr(target, "message", None),
        target,
    ]
    for message in candidates:
        method = getattr(message, method_name, None)
        if method is not None and method.__class__.__name__ == "AsyncMock":
            return message
    for message in candidates:
        if message is not None and callable(getattr(message, method_name, None)):
            return message
    return target


def _resolve_telegram_id(target: Any, explicit: int | None = None) -> int | None:
    if explicit is not None:
        return explicit
    for attr in ("effective_user", "from_user"):
        user = getattr(target, attr, None)
        user_id = getattr(user, "id", None)
        if isinstance(user_id, int):
            return user_id
    return None


def _save_assistant(target: Any, text: str, telegram_id: int | None, message_type: str) -> None:
    resolved_id = _resolve_telegram_id(target, telegram_id)
    if resolved_id is None:
        logger.debug("conversation_reply: missing telegram_id; skip history save")
        return
    save_conversation_message(resolved_id, "assistant", text, message_type=message_type)


async def reply_text(
    target: Any,
    text: str,
    *args: Any,
    telegram_id: int | None = None,
    message_type: str = "text",
    save_history: bool = True,
    **kwargs: Any,
) -> Any:
    message = _resolve_message(target, "reply_text")
    sent = await message.reply_text(text, *args, **kwargs)
    if save_history:
        _save_assistant(target, text, telegram_id, message_type)
    return sent


async def reply_markdown_v2(
    target: Any,
    text: str,
    *args: Any,
    telegram_id: int | None = None,
    message_type: str = "text",
    save_history: bool = True,
    **kwargs: Any,
) -> Any:
    message = _resolve_message(target, "reply_markdown_v2")
    sent = await message.reply_markdown_v2(text, *args, **kwargs)
    if save_history:
        _save_assistant(target, text, telegram_id, message_type)
    return sent


async def edit_message_text(
    query: Any,
    text: str,
    *args: Any,
    telegram_id: int | None = None,
    message_type: str = "text",
    save_history: bool = True,
    **kwargs: Any,
) -> Any:
    edited = await query.edit_message_text(text, *args, **kwargs)
    if save_history:
        _save_assistant(query, text, telegram_id, message_type)
    return edited
