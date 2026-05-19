"""Daily admin-only agent that profiles how each user works with OZE-Agent."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from shared.claude_ai import call_claude
from shared.database import log_interaction

from .store import (
    get_current_profile_state,
    insert_profile_run,
    list_new_conversation_messages,
    list_profile_agent_users,
    upsert_current_profile,
)

logger = logging.getLogger(__name__)

INTERACTION_TYPE = "user_profile_agent"
MODEL_TYPE = "simple"
MAX_MESSAGE_CHARS = 1800
MAX_PROFILE_CHARS = 8000
REQUIRED_PROFILE_SECTIONS = (
    "Podsumowanie użytkownika",
    "Styl komunikacji",
    "Typowe workflow",
    "Typowe komendy i frazy",
    "Zauważone preferencje",
    "Najczęstsze problemy / tarcia",
    "Sygnały, gdzie agent może źle działać",
    "Cenne przykłady z rozmów",
    "Wnioski agenta profilującego",
    "Poziom pewności / co wymaga dalszych danych",
)


@dataclass(frozen=True)
class ProfileDraft:
    profile_markdown: str
    insights_json: dict[str, Any]


@dataclass
class UserProfileAgentRunResult:
    users_total: int = 0
    updated: int = 0
    skipped_no_messages: int = 0
    failed: int = 0


def parse_profile_response(text: str) -> ProfileDraft | None:
    """Parse the model's JSON-only profile response."""
    raw = _strip_json_fence(text)
    try:
        payload = json.loads(raw)
    except Exception:
        logger.warning("user_profile_agent.parse_failed")
        return None

    profile_markdown = str(payload.get("profile_markdown") or "").strip()
    insights_json = payload.get("insights_json")
    if not profile_markdown or not isinstance(insights_json, dict):
        return None
    return ProfileDraft(profile_markdown=profile_markdown, insights_json=insights_json)


async def run_user_profile_agent() -> UserProfileAgentRunResult:
    """Run the daily profile agent for active users.

    This is observation-only: it never talks to Telegram users and never mutates
    Google CRM resources.
    """
    result = UserProfileAgentRunResult()
    users = list_profile_agent_users()
    result.users_total = len(users)

    for user in users:
        try:
            await _run_for_user(user)
            result.updated += 1
        except NoNewMessages:
            result.skipped_no_messages += 1
        except Exception as exc:
            result.failed += 1
            logger.exception("user_profile_agent.user_failed(%s): %s", user.get("id"), exc)
            _safe_insert_failed_run(user, exc)

    logger.info("user_profile_agent.run %s", result)
    return result


async def _run_for_user(user: dict[str, Any]) -> None:
    user_id = str(user["id"])
    telegram_id = int(user["telegram_id"])
    current_profile = get_current_profile_state(user_id)
    since = (current_profile or {}).get("last_analyzed_message_at")
    messages = list_new_conversation_messages(telegram_id, since=since)
    if not messages:
        raise NoNewMessages()

    model_response = await call_claude(
        _system_prompt(),
        _user_prompt(user=user, current_profile=current_profile, messages=messages),
        model_type=MODEL_TYPE,
        max_tokens=3072,
    )
    draft = parse_profile_response(model_response.get("text", ""))
    if draft is None:
        raise ValueError("Profile model response did not contain profile_markdown + insights_json")

    last_message_at = _last_message_at(messages)
    run_at = _now_iso()
    metrics = {
        "model": model_response.get("model"),
        "tokens_in": int(model_response.get("tokens_in") or 0),
        "tokens_out": int(model_response.get("tokens_out") or 0),
        "cost_usd": float(model_response.get("cost_usd") or 0.0),
    }
    current_payload = {
        "user_id": user_id,
        "telegram_id": telegram_id,
        "profile_markdown": draft.profile_markdown,
        "insights_json": draft.insights_json,
        "last_analyzed_message_at": last_message_at,
        "last_run_at": run_at,
        "status": "ok",
        "error": None,
        "analyzed_messages_count": len(messages),
        **metrics,
    }
    upsert_current_profile(current_payload)
    insert_profile_run({
        "user_id": user_id,
        "telegram_id": telegram_id,
        "status": "ok",
        "profile_markdown": draft.profile_markdown,
        "insights_json": draft.insights_json,
        "messages_count": len(messages),
        "analyzed_from": messages[0].get("created_at"),
        "analyzed_to": last_message_at,
        **metrics,
    })
    log_interaction(
        telegram_id,
        INTERACTION_TYPE,
        str(metrics["model"] or ""),
        metrics["tokens_in"],
        metrics["tokens_out"],
        metrics["cost_usd"],
    )


def _system_prompt() -> str:
    sections = "\n".join(f"- {section}" for section in REQUIRED_PROFILE_SECTIONS)
    return f"""Jesteś oddzielnym, wewnętrznym agentem analitycznym Agent OZE.
Tworzysz admin-only profil pracy użytkownika na podstawie historii rozmów.

Zasady:
- Nie piszesz do użytkownika i nie wykonujesz żadnych mutacji CRM.
- Profil nie steruje jeszcze agentem Telegramowym.
- Dane mogą zawierać realne dane klientów, bo profil jest wyłącznie owner-admin.
- Nie oceniaj człowieka personalnie. Opisuj wzorce pracy, ryzyka i tarcia produktu.
- Zwróć WYŁĄCZNIE JSON, bez komentarza i bez markdown fence.

JSON:
{{
  "profile_markdown": "markdown po polsku z sekcjami v1",
  "insights_json": {{
    "communication_style": [],
    "workflows": [],
    "common_commands": [],
    "preferences": [],
    "friction_points": [],
    "agent_improvement_opportunities": [],
    "confidence": "low|medium|high"
  }}
}}

Sekcje profilu Markdown:
{sections}"""


def _user_prompt(
    *,
    user: dict[str, Any],
    current_profile: dict[str, Any] | None,
    messages: list[dict[str, Any]],
) -> str:
    current = (current_profile or {}).get("profile_markdown") or ""
    if len(current) > MAX_PROFILE_CHARS:
        current = current[:MAX_PROFILE_CHARS].rstrip() + "\n..."
    return (
        f"Użytkownik: {user.get('name')} <{user.get('email')}> "
        f"telegram_id={user.get('telegram_id')}\n\n"
        "Aktualny profil do zaktualizowania:\n"
        f"{current or '(brak wcześniejszego profilu)'}\n\n"
        "Nowe wiadomości od ostatniej analizy:\n"
        f"{_format_messages(messages)}"
    )


def _format_messages(messages: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for row in messages:
        content = str(row.get("content") or "").replace("\n", " ").strip()
        if len(content) > MAX_MESSAGE_CHARS:
            content = content[:MAX_MESSAGE_CHARS].rstrip() + "..."
        if not content:
            continue
        lines.append(
            f"- [{row.get('created_at')}] {row.get('role')} "
            f"({row.get('message_type') or 'text'}): {content}"
        )
    return "\n".join(lines)


def _strip_json_fence(text: str) -> str:
    stripped = (text or "").strip()
    match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", stripped, flags=re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else stripped


def _last_message_at(messages: list[dict[str, Any]]) -> str | None:
    created = [str(row.get("created_at")) for row in messages if row.get("created_at")]
    return max(created) if created else None


def _safe_insert_failed_run(user: dict[str, Any], exc: Exception) -> None:
    try:
        insert_profile_run({
            "user_id": str(user.get("id")),
            "telegram_id": int(user.get("telegram_id") or 0),
            "status": "failed",
            "error": str(exc)[:1000],
            "messages_count": 0,
            "created_at": _now_iso(),
        })
    except Exception as insert_exc:
        logger.warning("user_profile_agent.failed_run_log_failed(%s): %s", user.get("id"), insert_exc)


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


class NoNewMessages(Exception):
    """Raised internally when a user has no new conversation rows to analyze."""
