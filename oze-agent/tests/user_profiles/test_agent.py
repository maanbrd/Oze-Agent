from __future__ import annotations

import pytest


def test_parse_profile_response_accepts_json_with_markdown_and_insights():
    from shared.user_profiles.agent import parse_profile_response

    draft = parse_profile_response(
        """
        ```json
        {
          "profile_markdown": "# Profil użytkownika\\n\\n## Podsumowanie\\nCzęsto dyktuje krótkie wiadomości.",
          "insights_json": {
            "communication_style": ["krótkie wiadomości"],
            "friction_points": ["brakuje miasta"],
            "confidence": "medium"
          }
        }
        ```
        """
    )

    assert draft is not None
    assert "## Podsumowanie" in draft.profile_markdown
    assert draft.insights_json["communication_style"] == ["krótkie wiadomości"]
    assert draft.insights_json["confidence"] == "medium"


def test_parse_profile_response_rejects_missing_markdown():
    from shared.user_profiles.agent import parse_profile_response

    assert parse_profile_response('{"insights_json": {"confidence": "low"}}') is None


@pytest.mark.asyncio
async def test_run_user_profile_agent_skips_users_without_new_messages(monkeypatch):
    from shared.user_profiles import agent

    called = {"model": False, "upsert": False}

    monkeypatch.setattr(
        agent,
        "list_profile_agent_users",
        lambda: [{"id": "user-1", "telegram_id": 123, "name": "Jan", "email": "jan@example.pl"}],
    )
    monkeypatch.setattr(
        agent,
        "get_current_profile_state",
        lambda user_id: {"last_analyzed_message_at": "2026-05-18T20:00:00+00:00"},
    )
    monkeypatch.setattr(agent, "list_new_conversation_messages", lambda telegram_id, since=None: [])

    async def fake_call(*_args, **_kwargs):
        called["model"] = True
        return {"text": ""}

    monkeypatch.setattr(agent, "call_claude", fake_call)
    monkeypatch.setattr(agent, "upsert_current_profile", lambda payload: called.__setitem__("upsert", True))

    result = await agent.run_user_profile_agent()

    assert result.users_total == 1
    assert result.skipped_no_messages == 1
    assert result.updated == 0
    assert called == {"model": False, "upsert": False}


@pytest.mark.asyncio
async def test_run_user_profile_agent_updates_profile_and_logs_cost(monkeypatch):
    from shared.user_profiles import agent

    writes = {"current": None, "run": None, "interaction": None}

    monkeypatch.setattr(
        agent,
        "list_profile_agent_users",
        lambda: [{"id": "user-1", "telegram_id": 123, "name": "Jan", "email": "jan@example.pl"}],
    )
    monkeypatch.setattr(agent, "get_current_profile_state", lambda user_id: None)
    monkeypatch.setattr(
        agent,
        "list_new_conversation_messages",
        lambda telegram_id, since=None: [
            {
                "role": "user",
                "content": "Dodaj klienta Jan Nowak Warszawa",
                "message_type": "text",
                "created_at": "2026-05-18T20:00:00+00:00",
            },
            {
                "role": "assistant",
                "content": "Karta zapisu",
                "message_type": "text",
                "created_at": "2026-05-18T20:00:05+00:00",
            },
        ],
    )

    async def fake_call(*_args, **_kwargs):
        return {
            "text": '{"profile_markdown": "# Profil użytkownika\\n\\n## Wnioski agenta profilującego\\nCzęsto dodaje leady.", "insights_json": {"workflows": ["add_client"], "confidence": "high"}}',
            "tokens_in": 100,
            "tokens_out": 50,
            "cost_usd": 0.001,
            "model": "claude-haiku-4-5-20251001",
        }

    monkeypatch.setattr(agent, "call_claude", fake_call)
    monkeypatch.setattr(agent, "upsert_current_profile", lambda payload: writes.__setitem__("current", payload))
    monkeypatch.setattr(agent, "insert_profile_run", lambda payload: writes.__setitem__("run", payload))
    monkeypatch.setattr(
        agent,
        "log_interaction",
        lambda telegram_id, interaction_type, model, tokens_in, tokens_out, cost: writes.__setitem__(
            "interaction",
            {
                "telegram_id": telegram_id,
                "interaction_type": interaction_type,
                "model": model,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "cost": cost,
            },
        ),
    )

    result = await agent.run_user_profile_agent()

    assert result.users_total == 1
    assert result.updated == 1
    assert writes["current"]["user_id"] == "user-1"
    assert writes["current"]["telegram_id"] == 123
    assert writes["current"]["last_analyzed_message_at"] == "2026-05-18T20:00:05+00:00"
    assert writes["current"]["insights_json"]["workflows"] == ["add_client"]
    assert writes["run"]["status"] == "ok"
    assert writes["run"]["messages_count"] == 2
    assert writes["interaction"]["interaction_type"] == "user_profile_agent"


@pytest.mark.asyncio
async def test_run_user_profile_agent_isolates_user_errors(monkeypatch):
    from shared.user_profiles import agent

    users = [
        {"id": "user-bad", "telegram_id": 111, "name": "Bad", "email": "bad@example.pl"},
        {"id": "user-ok", "telegram_id": 222, "name": "Ok", "email": "ok@example.pl"},
    ]
    runs = []

    monkeypatch.setattr(agent, "list_profile_agent_users", lambda: users)
    monkeypatch.setattr(agent, "get_current_profile_state", lambda user_id: None)

    def fake_messages(telegram_id, since=None):
        if telegram_id == 111:
            raise RuntimeError("db timeout")
        return [
            {
                "role": "user",
                "content": "co mam dziś",
                "message_type": "text",
                "created_at": "2026-05-18T21:00:00+00:00",
            }
        ]

    async def fake_call(*_args, **_kwargs):
        return {
            "text": '{"profile_markdown": "# Profil użytkownika\\n\\n## Podsumowanie\\nPyta o plan dnia.", "insights_json": {"confidence": "medium"}}',
            "tokens_in": 1,
            "tokens_out": 1,
            "cost_usd": 0.0,
            "model": "claude-haiku-4-5-20251001",
        }

    monkeypatch.setattr(agent, "list_new_conversation_messages", fake_messages)
    monkeypatch.setattr(agent, "call_claude", fake_call)
    monkeypatch.setattr(agent, "upsert_current_profile", lambda payload: None)
    monkeypatch.setattr(agent, "insert_profile_run", lambda payload: runs.append(payload))
    monkeypatch.setattr(agent, "log_interaction", lambda *_args, **_kwargs: None)

    result = await agent.run_user_profile_agent()

    assert result.users_total == 2
    assert result.failed == 1
    assert result.updated == 1
    assert {run["user_id"] for run in runs} == {"user-bad", "user-ok"}
