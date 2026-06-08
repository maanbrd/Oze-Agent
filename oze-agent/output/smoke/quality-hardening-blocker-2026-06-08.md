# Agent OZE Quality Hardening Blocker - 2026-06-08

## Status

Blocked at Stage 3: Live Environment Preflight.

The repository hardening code was implemented, tested, committed, and pushed on
`codex/agent-production-hardening`. Railway CLI access was later restored and
the worktree was linked to `AgentOZE / production / bot-test`, but live Google
verification still blocks release because the E2E user's configured Calendar ID
is not accessible to the bot runtime OAuth account.

## Completed Before Blocker

- Created hardening worktree:
  `/Users/mansoniasty/.config/superpowers/worktrees/Agent-OZE/agent-production-hardening`
- Branch: `codex/agent-production-hardening`
- Base: `origin/develop`
- Commit: `70f471b chore(e2e): add production hardening release gate`
- Push: `origin/codex/agent-production-hardening`
- Local backend verification:
  `cd oze-agent && PYTHONPATH=. pytest -q`
  Result: `869 passed`
- Release gate command registry:
  `./tests_e2e/run_release_gate.sh --commands-only`
  Result: canonical 14-step gate pack printed.
- Local release preflight with copied gitignored Telethon session/env and explicit
  `TELEGRAM_E2E_RAILWAY_SERVICE=bot-test`:
  Result: OK.

## Blocking Checks

### Google health with Railway runtime env after CLI login

Command:

```bash
set -a; source tests_e2e/.env; set +a
TELEGRAM_E2E_RAILWAY_SERVICE=bot-test \
  railway run --service bot-test --environment production -- \
  ./tests_e2e/run_release_gate.sh google-health --report output/smoke/release-gate/google-health.md
```

Result:

```text
Overall: BLOCKER
supabase_user: pass
google_credentials: pass
sheets_read: pass
calendar_read: blocker - Google Calendar API returned 404 Not Found
drive_read: pass
```

Additional read-only diagnostic:

```text
configured_calendar_present=False
accessible_calendar_count=4
configured_calendar_hash=0eaa638a3657
```

Interpretation:

The E2E user's `google_calendar_id` exists in Supabase config, but the runtime
Google OAuth account cannot see that calendar. This is a runtime configuration
blocker, not a repository code blocker.

### Google health without Railway runtime env

Command:

```bash
./tests_e2e/run_release_gate.sh google-health --report output/smoke/release-gate/google-health.md
```

Result:

```text
Overall: BLOCKER
supabase_user: no Supabase user found for telegram_id=1690210103
```

Interpretation:

The local gitignored E2E env has Telethon credentials, but it does not include
the Supabase runtime variables or `TELEGRAM_E2E_SUPABASE_USER_ID` needed by the
read-only Google verifier.

### Railway CLI runtime access

Commands:

```bash
railway whoami
railway status
```

Results:

```text
Warning: failed to refresh OAuth token: Token refresh failed: invalid_grant: grant request is invalid. Please run `railway login` again.
Unauthorized. Please run `railway login` again.
```

```text
Warning: failed to refresh OAuth token: Token refresh failed: invalid_grant: grant request is invalid. Please run `railway login` again.
No linked project found. Run railway link to connect to a project
```

Interpretation:

This was the initial blocker. It was resolved after Railway login by linking:

```bash
railway link --project 1501c9a2-db5b-46fd-9e5f-fa4b0d33a9f7 --environment production --service bot-test
```

## Stop Condition Triggered

This matches the plan stop conditions:

- Google health `BLOCKER`.
- E2E cleanup cannot be trusted while the configured Calendar target is missing.

No deploy, merge to `develop`, merge to `main`, production promotion, Telegram
live E2E, Railway log review, or Gmail/send smoke was run after this blocker.

## Required Human/Environment Action

Restore Calendar configuration before continuing Stage 3:

1. Update the E2E user's `google_calendar_id` to a calendar visible to the bot
   runtime OAuth account, or
2. Recreate/share the intended dedicated OZE calendar with the runtime OAuth
   account and update Supabase accordingly.

After access is restored, resume with:

```bash
cd /Users/mansoniasty/.config/superpowers/worktrees/Agent-OZE/agent-production-hardening/oze-agent
TELEGRAM_E2E_RAILWAY_SERVICE=bot-test ./tests_e2e/run_release_gate.sh google-health --report output/smoke/release-gate/google-health.md
```
