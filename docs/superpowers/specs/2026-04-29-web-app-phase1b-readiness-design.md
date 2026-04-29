# Web App Phase 1B Readiness Design

_Date: 29.04.2026_
_Track: Web app Phase 1B_
_Branch: `feat/web-phase-0c`_

## Decision

Phase 1B is a readiness gate for the code-complete web app spine. It does not
add product features, CRM mutation UI, live Stripe mode, company accounts, or
copy polish.

The implementation adds repo-local readiness tooling and a runbook so the team
can verify the web app first in a safe local setup and then against staging
sandbox services.

## Scope

Local readiness proves configuration shape, builds, FastAPI route availability,
protected route behavior, and web UI boundaries. It does not prove Stripe
webhook delivery, because Stripe cannot deliver to localhost without Stripe CLI
or a public tunnel.

Staging readiness proves the full external flow:

- Vercel web preview/staging,
- separate Railway FastAPI service,
- staging Supabase cloud,
- Stripe test-mode Checkout and webhook replay,
- Google OAuth and resource creation,
- Telegram `/start <code>` pairing,
- CRM pages showing explicit `live` or `unavailable` source states.

## Architecture

Next.js remains the browser/session and Stripe Checkout boundary. FastAPI remains
the trusted boundary for service-role Supabase writes and Google operations.

Vercel never receives `SUPABASE_SERVICE_KEY`. Vercel verifies Stripe webhook
signatures and forwards normalized sandbox events to FastAPI with
`BILLING_INTERNAL_SECRET` HMAC.

Railway must run two separate services/processes for readiness:

- bot service: `python -m bot.main`,
- API service: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`.

## Tooling

Add a web checker:

- file: `web/scripts/check-phase1b-env.mjs`,
- package script: `npm run check:phase1b-env`,
- default scope: `local`,
- staging scope: `npm run check:phase1b-env -- --scope=staging`,
- loads `.env.local` / `.env` or an explicit `--env-file=<path>`.

Add a FastAPI checker:

- file: `oze-agent/scripts/verify_phase1b_env.py`,
- command: `PYTHONPATH=. python3 scripts/verify_phase1b_env.py`,
- loads `.env.local` / `.env` or an explicit `--env-file=<path>`.

Add a FastAPI local smoke checker:

- file: `oze-agent/scripts/smoke_phase1b_api.py`,
- command:
  `PYTHONPATH=. python3 scripts/smoke_phase1b_api.py --base-url=http://127.0.0.1:8000`,
- checks `/health` and verifies protected onboarding/dashboard routes fail
  closed without auth.

Add a Supabase migration preflight checker:

- file: `oze-agent/scripts/check_phase1b_migrations.py`,
- command: `PYTHONPATH=. python3 scripts/check_phase1b_migrations.py`,
- checks that Phase 1B auth/RLS and billing migration files contain the required
  auth trigger, RLS policy, Stripe IDs, unique event indexes, and billing outbox.

Add a local readiness orchestrator:

- file: `oze-agent/scripts/run_phase1b_local_readiness.py`,
- command:
  `PYTHONPATH=. python3 scripts/run_phase1b_local_readiness.py --web-env-file=../web/.env.local --api-env-file=.env.local --report=../docs/phase1b-local-readiness-report.md`,
- uses explicit `cwd` values for web (`../web`) and backend (`.`),
- records omitted smoke URLs as `skipped`, but fails smoke when a provided URL
  is unreachable,
- redacts env-file paths and loaded env-file output from reports.

Add a staging manifest preflight:

- file: `oze-agent/scripts/check_phase1b_staging_manifest.py`,
- example: `docs/phase1b-staging-manifest.example.json`,
- command:
  `PYTHONPATH=. python3 scripts/check_phase1b_staging_manifest.py --manifest ../docs/phase1b-staging-manifest.example.json --generate-smoke-id`,
- validates public staging URLs, Stripe test mode, lookup keys, webhook URL,
  Railway API start command, smoke domain, and rejects secrets in the manifest.

Add a smoke report template:

- file: `docs/PHASE1B_SMOKE_REPORT_TEMPLATE.md`.

Add a local route smoke checker:

- file: `web/scripts/smoke-phase1b-local.mjs`,
- package script: `npm run smoke:phase1b-local`,
- checks `/healthz`, public route rendering, anonymous protected redirects,
  onboarding gate wiring, and no CRM mutation forms.

## Safety Rules

Stop immediately if any Stripe response shows `livemode: true`.

Use a fresh smoke account per run:

- email format: `phase1b+YYYYMMDD-HHMM@<staging-test-domain>`,
- Google resource prefix: `P1B Smoke YYYY-MM-DD HHMM`.

Record Supabase user ID, Stripe customer/session/subscription IDs, Stripe event
IDs, Google resource IDs, and Telegram pairing result in the smoke report.

## Verification

Local automated verification:

- `cd web && npm run check:phase1b-env`,
- `cd web && npm run test:invariants && npm run lint && npm run build`,
- `cd web && npm run smoke:phase1b-local -- --base-url=http://127.0.0.1:3000`,
- `cd oze-agent && PYTHONPATH=. python3 scripts/verify_phase1b_env.py`,
- `cd oze-agent && PYTHONPATH=. python3 scripts/check_phase1b_migrations.py`,
- `cd oze-agent && PYTHONPATH=. python3 scripts/smoke_phase1b_api.py --base-url=http://127.0.0.1:8000`,
- `cd oze-agent && PYTHONPATH=. python3 scripts/run_phase1b_local_readiness.py --web-env-file=../web/.env.local --api-env-file=.env.local`,
- `cd oze-agent && PYTHONPATH=. python3 scripts/check_phase1b_staging_manifest.py --manifest ../docs/phase1b-staging-manifest.example.json --generate-smoke-id`,
- `cd oze-agent && PYTHONPATH=. pytest tests/test_billing.py tests/test_onboarding_api.py tests/test_dashboard_api.py tests/test_api_auth.py -q`,
- `cd oze-agent && PYTHONPATH=. pytest -q`.

Staging smoke follows `docs/WEB_PHASE_1B_READINESS.md`.
