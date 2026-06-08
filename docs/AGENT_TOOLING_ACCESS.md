# Agent OZE — Tooling Access Memory

_Last updated: 08.06.2026_

This file records available operational tools for Agent OZE hardening and
release work. Future agents must check these tools before declaring a blocker.

## Available Tooling

### Local E2E / Telethon

- Telethon E2E lives in `oze-agent/tests_e2e/`.
- Primary release entrypoint:
  `cd oze-agent && ./tests_e2e/run_release_gate.sh`
- Canonical gate pack:
  `cd oze-agent && ./tests_e2e/run_release_gate.sh --commands-only`
- Scenario runner:
  `cd oze-agent && python -m tests_e2e.runner --list`
- MCP server fallback:
  `cd oze-agent && ./tests_e2e/run_mcp_server.sh`
- If the `oze-e2e` MCP namespace is not loaded, use the CLI wrapper as the
  canonical execution path. Do not stop only because the namespace is absent.

### Google Connectors / MCP

- Google Calendar connector is available through Codex tools.
- Google Drive connector is available and includes Docs/Sheets/Slides access.
- These connectors are valid for additional verification and discovery.
- Connector OAuth is not automatically the same as the bot runtime OAuth.
  Runtime-critical gates must still pass through bot runtime checks, especially:
  `railway run --service bot-test --environment production -- ./tests_e2e/run_release_gate.sh google-health`.

### Supabase

- Supabase project data is available to the bot runtime through Railway env.
- Project wrapper:
  `oze-agent/shared/database.py`
- If Supabase MCP is not exposed in the current tool namespace, do not stop
  immediately. Use `railway run` with the project wrappers for controlled
  read/write config operations.
- System config such as `users.google_calendar_id` lives in Supabase.
- CRM source-of-truth data must not be moved into Supabase.

### Railway CLI

- Railway CLI is available locally.
- Agent OZE Railway project:
  `AgentOZE`
- Key services:
  - `bot-test` — test Telegram bot / pre-production gate
  - `bot` — production Telegram bot
  - `api` — backend API service
- If `railway status` says the project is not linked, link explicitly:
  `railway link --project 1501c9a2-db5b-46fd-9e5f-fa4b0d33a9f7 --environment production --service bot-test`
- Use Railway runtime env instead of local `.env` for secrets:
  `railway run --service bot-test --environment production -- <command>`
- Use `railway logs`, `railway restart`, and `railway redeploy` for release
  checks where appropriate.

### Vercel

- Vercel connector is available for web app deployments, logs, project checks,
  and protected deployment inspection.
- Use it for `web/` verification when the hardening slice touches the Next.js
  app or offer-generator web surface.

## Operating Rule

Do not declare a tool/access blocker until all applicable paths have been
checked:

1. `tool_search` for connector/MCP namespaces.
2. Local CLI fallback (`tests_e2e`, Railway CLI, project wrappers).
3. Railway project link and runtime env.
4. Existing gitignored E2E env/session copied from the main checkout when
   needed.
5. Runtime read-only health check through `bot-test`.

## Valid Stop Conditions

Stop only for a real blocker, not for first-attempt tool absence:

- Credentials are missing, expired, or invalid after discovery/fallback checks.
- Google health returns `BLOCKER` after runtime config has been verified.
- E2E cleanup cannot identify/delete only synthetic `E2E-*` fixtures.
- A write would bypass R1 confirmation.
- Logs expose PII that must be fixed before promotion.
- A merge conflict requires changing product behavior.
- A requested smoke would send to a real customer or uncontrolled Gmail address.

## Reminder From 08.06.2026

The Calendar health blocker was resolved by using Railway runtime access to
inspect calendars visible to the bot OAuth account and updating the E2E user's
`google_calendar_id` in Supabase to the dedicated calendar:
`Agent OZE - Wszystkie spotkania`.

Lesson: if Calendar MCP/connector exists but does not expose the exact operation
needed, use Railway runtime + Google wrapper diagnostics before stopping.
