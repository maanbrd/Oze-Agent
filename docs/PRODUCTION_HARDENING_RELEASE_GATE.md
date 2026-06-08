# Agent OZE — Production Hardening Release Gate

This gate prepares a controlled pilot release. It does not deploy, merge, push,
or send real customer email by itself.

## Policy

- Run the full gate on `bot-test` / `develop` first.
- Use only synthetic `E2E-Beta-*` clients and controlled test inboxes.
- Do not run controlled offer-send smoke unless `TELEGRAM_E2E_OFFER_RECIPIENT`
  points to an owned inbox.
- Promote to `main` only after the gate report is green and Maan approves the
  production smoke.
- Production smoke is a small subset on controlled data, not the full mutating
  campaign.

## Preflight

From `oze-agent/`:

```bash
./tests_e2e/run_release_gate.sh
```

The command validates the local E2E environment and prints the canonical command
pack. By default it blocks anything other than:

- `TELEGRAM_E2E_BOT_USERNAME=@OZEAgentTestBot`
- `TELEGRAM_E2E_RAILWAY_SERVICE=bot-test`

For the final controlled production smoke only, use:

```bash
./tests_e2e/run_release_gate.sh --allow-prod-bot
```

## Gate Pack

Run commands in the printed order:

1. `./tests_e2e/run_release_gate.sh pytest-tests`
2. `./tests_e2e/run_release_gate.sh list`
3. `./tests_e2e/run_release_gate.sh google-health --report output/smoke/release-gate/google-health.md`
4. `./tests_e2e/run_release_gate.sh seed`
5. Run every release-gate category printed by `tests_e2e.release_gate`
6. `./tests_e2e/run_release_gate.sh cleanup`

The category pack covers routing, confirmation-card structure, error paths,
read-only flows, R-rules, notes, Polish edge cases, core mutating flows and
photo upload.

## MCP

If the local `oze-e2e` MCP server is active, call:

```text
release_gate_status
```

It validates the same environment safety rules and prints the same command pack
without touching Telegram or Google.

If the MCP namespace is not active in the session, use the CLI commands above.

## Blockers

Stop the release if any of these occurs:

- Google health returns `BLOCKER`
- Telethon preflight authenticates as the wrong user
- any release-gate category returns `FAIL` or `BLOCKER`
- Railway logs expose PII in classifier/flow logs
- a mutation writes to Sheets, Calendar, Drive or Gmail before confirmation
- cleanup cannot identify synthetic E2E rows/events

Document every blocker in `output/smoke/` and add a regression test before the
fix is promoted.
