# OZE-Agent Smoke E2E 500 — status 2026-05-09

## Outcome

The 500-run campaign is blocked by the bot runtime, not by Telethon or the E2E harness.

Fresh probe at 14:58-14:59 Europe/Warsaw sent real Telegram messages to `@OZEAgentTestBot` through Telethon. The bot replied only `Co chcesz zrobić?` and did not produce mutation confirmation cards.

Railway logs for `bot-test` show the root cause:

```text
2026-05-09 12:45:39,351 ERROR shared.claude_ai — call_claude_with_tools(simple): Error code: 400 - ... Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits.
```

This still reproduced during the fresh probe:

```text
2026-05-09 12:58:31,196 ERROR shared.claude_ai — call_claude_with_tools(simple): Error code: 400 - ... Your credit balance is too low to access the Anthropic API.
2026-05-09 12:59:34,789 ERROR shared.claude_ai — call_claude_with_tools(simple): Error code: 400 - ... Your credit balance is too low to access the Anthropic API.
```

## What Ran

- Telethon/Telegram: real messages sent to `@OZEAgentTestBot`.
- MCP server: `oze-e2e` wrapper loaded through stdio.
- Google Drive/Sheets connector: verified CRM spreadsheet metadata and searched cleanup markers.
- Google Calendar connector: verified bot calendar profile and searched cleanup markers.
- Gmail connector: verified connected mailbox and searched Sent for test markers.
- Supabase: runtime query through bot-test env verified schema blockers.
- Vercel/dashboard: verified branch alias `feat/web-bootstrap` through Playwright/system Chrome.
- Railway logs: pulled and counted bot-test logs from campaign start.

## MCP Evidence

`oze-e2e` tools exposed:

```text
e2e_status, list_scenarios, e2e_campaign_plan, run_debug_brief, run_scenario, run_category, e2e_seed_fixtures, e2e_cleanup_run
```

Status:

```text
bot_username: @OZEAgentTestBot
admin_id: 1690210103
scenarios: 51
categories: card_structure, error_path, mutating_core, notes, polish_edge, proactive, read_only, realistic_smoke, routing, rules
```

MCP cleanup:

```text
Sheets: found 0, deleted 0
Calendar: found 0, deleted 0
```

## Logs Summary

Source: `/tmp/oze-railway-bot-test-20260509.log`

Counts since campaign start:

```text
anthropic_credit_errors=34
sheets_append_mentions=76
intent_add_client=87
intent_meeting=38
show_day_plan_text=37
photo_session_missing_table=18
```

First Anthropic blocker:

```text
2026-05-09 12:45:39,351 ERROR shared.claude_ai — call_claude_with_tools(simple): Error code: 400 - ... Your credit balance is too low to access the Anthropic API.
```

## Records Verified In Target Systems

Sheets:

- Spreadsheet: `Agent-OZE CRM - Maan Fathi`
- Spreadsheet ID: `1z0BNmhbOFX6BA5TyZ30T1VuKTBbHYwCmknBOXYbxVO8`
- Metadata verified through Drive connector.
- Cleanup-marker searches for `@e2e-noinbox.local`, `Michał Zieliński`, `Karolina Woźniak` returned no rows after cleanup.

Calendar:

- Calendar account: `lukaszfathioze@gmail.com`
- Calendar ID: `0686f3051722b08915e44f94bcad2ca07aa7ed1583c4c7eeead1f080bdbb915d@group.calendar.google.com`
- Searches for `Karolina Woźniak`, `Michał`, `Zieliński` returned no events after cleanup.

Gmail:

- Gmail connector account: `lukaszfathi97@gmail.com`
- Sent search for `e2e-noinbox.local`, `Michał Zieliński`, `Karolina Woźniak`, `Piotr Malinowski` returned no messages.
- Full offer-send Gmail test cannot run while the bot cannot classify/send because Anthropic is blocked and `offer_templates` is missing in Supabase.

Dashboard:

- URL: `https://oze-agent-git-feat-web-bootstrap-maanbrds-projects.vercel.app/dashboard`
- Latest Vercel deployment: `dpl_AtGSZaVBsVZKepzJ4QZusxmAUpyQ`
- Branch: `feat/web-bootstrap`
- State: `READY`
- Playwright/system Chrome login succeeded.
- Dashboard contains CRM read-only content and the test account.
- Dashboard does not contain `@e2e-noinbox.local`, `Michał Zieliński`, `Karolina Woźniak`, or `E2E-Beta`.
- Screenshot: `/tmp/oze-dashboard-feat-web-bootstrap-final.png`

Supabase:

```text
photo_upload_sessions: ERROR PGRST205 table missing
offer_templates: ERROR PGRST205 table missing
users: OK
```

## Cleanup State

Final cleanup was run through the MCP wrapper and reported zero remaining Sheets rows and zero Calendar events. Independent connector searches confirmed no visible realistic cleanup markers in Sheets/Calendar/dashboard/Gmail.

## Blockers Before Resuming 500

1. Replenish/fix Anthropic billing for the `bot-test` runtime, or switch `bot-test` to a working provider.
2. Apply the test Supabase schema needed by the active product slices:
   - `public.photo_upload_sessions`
   - `public.offer_templates`
3. Resume the 500-run campaign from a clean state.

## Artifacts

- Probe report: `/tmp/oze-e2e-probe-20260509.md`
- Railway log extract: `/tmp/oze-railway-bot-test-20260509.log`
- Dashboard screenshot: `/tmp/oze-dashboard-feat-web-bootstrap-final.png`
