# Phase 7 E2E Harness

Minimal Telethon-based end-to-end tests for OZE-Agent. The harness acts as
a real Telegram user account, sends commands to the live (prod or staging)
bot, and verifies the bot's replies.

This is separate from `tests/` (unit/integration tests that mock external
services).

---

## Why Telethon, not Bot API

The Telegram Bot API cannot read messages sent *to* the bot from a user's
perspective. For black-box E2E we need a real user client, so the harness
uses Telethon under a dedicated test Telegram account.

---

## Why also an MCP server

`tests_e2e/mcp_server.py` is a **thin wrapper** over the same scenarios
the CLI runs. Register it in Claude Code's MCP config and an agent can
call `run_debug_brief` as a tool — same logic, different driver.

If you are adding a new check, put it in a scenario module, not in
`mcp_server.py`.

---

## Setup (one-time, per test account)

### 1. Create (or reuse) a test Telegram account

Do **not** use the bot owner's personal account. Register a separate
number (or use a second Telegram slot). That account must also be
configured as the bot's `ADMIN_TELEGRAM_ID` if you want to exercise
admin-gated commands like `/debug_brief`.

### 2. Get Telethon API credentials for that account

1. Log in at <https://my.telegram.org/apps>.
2. Create an application — you receive `api_id` and `api_hash`.
3. Save them — these are per-account, not per-bot.

### 3. Install dependencies

```bash
cd oze-agent
pip install -r tests_e2e/requirements-e2e.txt
```

### 4. Configure environment

```bash
cp tests_e2e/.env.example tests_e2e/.env
# edit tests_e2e/.env — fill every required value
```

Required variables (also documented in `.env.example`):

| Name | Purpose |
|---|---|
| `TELEGRAM_E2E_API_ID` | Telethon app id (from my.telegram.org) |
| `TELEGRAM_E2E_API_HASH` | Telethon app hash |
| `TELEGRAM_E2E_BOT_USERNAME` | Bot to test, e.g. `@OzeAgentBot` |
| `TELEGRAM_E2E_ADMIN_ID` | Numeric Telegram id of the test user |
| `TELEGRAM_E2E_SESSION` | Path prefix for the Telethon session file |
| `TELEGRAM_E2E_REPORT` | (Optional) override for the report file path |
| `TELEGRAM_E2E_SUPABASE_USER_ID` | (Optional) Supabase UUID for local Sheets/Calendar verification when Supabase env cannot resolve `TELEGRAM_E2E_ADMIN_ID` |

The harness reads plain env (no `.env` auto-load) — use `set -a; source
tests_e2e/.env; set +a` or your favourite dotenv runner when invoking.

### 5. First run (interactive — one-time)

```bash
set -a; source tests_e2e/.env; set +a
python -m tests_e2e.runner debug_brief
```

Telethon will prompt for the test account's phone number and the SMS OTP
code. After login a `.session` file is written at
`$TELEGRAM_E2E_SESSION.session` — keep it private. Subsequent runs are
fully non-interactive.

### 6. Subsequent runs

```bash
set -a; source tests_e2e/.env; set +a

# Run all scenarios
python -m tests_e2e.runner

# Run one scenario
python -m tests_e2e.runner debug_brief

# Custom report path
python -m tests_e2e.runner debug_brief --report /tmp/e2e.md
```

Exit codes:

- `0` — all scenarios PASS
- `1` — at least one FAIL
- `2` — misconfiguration / harness connect failure

---

## What the debug_brief scenario checks

Two runs of `/debug_brief` on the same Warsaw day.

**First run** — expect three messages:

1. Ack: `"Uruchamiam morning brief debug..."`
2. The actual brief — must start with `Terminarz:`.
3. Summary: `"Debug brief zakończony: total_eligible=… sent=… …"`.

**Second run** — dedup kicks in for the brief itself:

1. Ack message fires regardless of dedup.
2. Brief is *not* sent (dedup on `users.last_morning_brief_sent_date`).
3. Summary fires with `skipped_deduped >= 1`.

Failing any of these records a PASS/FAIL line in the markdown report at
`TELEGRAM_E2E_REPORT` (default `test_results_e2e.md` in cwd).

---

## Safety notes

- The harness never deletes data. If you want to clean Sheets/Calendar
  between runs, do it manually.
- Use E2E test data with the `E2E-Beta-` prefix in the client name
  (convention — lets you `grep` or filter).
- Do **not** run the harness against the prod bot if real users are
  active — `/debug_brief` itself only messages the admin, but future
  scenarios may touch Sheets/Calendar owned by the test account.
  Strongly recommended: point at a staging bot with its own
  Sheets/Calendar once non-trivial mutations are added.
- Session files contain auth tokens. `tests_e2e/.sessions/` is
  gitignored — keep it that way.
- **Do NOT start a second bot instance sharing the prod
  `TELEGRAM_BOT_TOKEN`.** Telegram polling will reject `getUpdates` with
  a 409 conflict and the prod bot will break.

---

## Adding a new scenario

1. Create `tests_e2e/scenarios/<name>.py` with an async
   `run_<name>_scenario(harness) -> ScenarioResult` function. Follow the
   pattern in `debug_brief.py`.
2. Register it in `tests_e2e/runner.py::SCENARIOS`.
3. If you want it available over MCP, add a `@mcp.tool()` in
   `tests_e2e/mcp_server.py::_build_server`.

Planned next scenarios (per `docs/TEST_PLAN_CURRENT.md`):

- `add_client` (AC-1..AC-6b)
- `add_note` (AN-1..AN-4)
- `change_status` (R7 firing, 3-button card)
- `add_meeting` (AM-1..AM-8)
- `show_day_plan` (SDP)
- `duplicate_resolution` ([Nowy] / [Aktualizuj])
- `R1_no_write_before_confirmation` (R1-1..R1-4)

---

## File map

```
tests_e2e/
├── README.md              # this file
├── .env.example           # env template (.env is gitignored)
├── requirements-e2e.txt   # Telethon + optional MCP SDK
├── __init__.py
├── config.py              # E2EConfig.from_env()
├── harness.py             # TelegramE2EHarness (Telethon wrapper)
├── report.py              # ScenarioResult + markdown writer
├── runner.py              # CLI: python -m tests_e2e.runner
├── mcp_server.py          # FastMCP wrapper (optional)
├── scenarios/
│   ├── __init__.py
│   └── debug_brief.py     # first scenario
└── tests/                 # pytest smoke for the harness itself
    ├── __init__.py
    └── test_report.py
```
