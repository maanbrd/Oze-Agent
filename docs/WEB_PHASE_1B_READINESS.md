# Web Phase 1B Readiness Runbook

_Last updated: 29.04.2026_

Phase 1B proves the code-complete web app against safe local checks first and
then staging sandbox services. It is not a feature phase and does not enable live
Stripe mode.

## Stop Conditions

Stop immediately if any Stripe API, dashboard, MCP, or CLI response shows
`livemode: true`.

Do not put `SUPABASE_SERVICE_KEY` in Vercel. FastAPI is the only service that
uses the Supabase service key. The web env checker fails if
`SUPABASE_SERVICE_KEY` is present.

Do not reuse the Telegram bot Railway service as the FastAPI API service. Phase
1B requires a separate Railway API service.

## Local Readiness

Use staging Supabase cloud and Stripe test-mode values, but run Next.js and
FastAPI locally.

Commands:

```bash
cd web
npm run check:phase1b-env
npm run check:phase1b-env -- --env-file=.env.local
npm run test:invariants
npm run lint
npm run build
npm run smoke:phase1b-local -- --base-url=http://127.0.0.1:3000
```

```bash
cd oze-agent
PYTHONPATH=. python3 scripts/run_phase1b_local_readiness.py \
  --web-env-file=../web/.env.local \
  --api-env-file=.env.local \
  --report=../docs/phase1b-local-readiness-report.md
PYTHONPATH=. python3 scripts/verify_phase1b_env.py
PYTHONPATH=. python3 scripts/verify_phase1b_env.py --env-file=.env.local
PYTHONPATH=. python3 scripts/check_phase1b_migrations.py
PYTHONPATH=. uvicorn api.main:app --host 127.0.0.1 --port 8000
PYTHONPATH=. python3 scripts/smoke_phase1b_api.py --base-url=http://127.0.0.1:8000
PYTHONPATH=. pytest tests/test_billing.py tests/test_onboarding_api.py tests/test_dashboard_api.py tests/test_api_auth.py -q
PYTHONPATH=. pytest -q
```

Both env checkers load `.env.local` and `.env` from their current working
directory when those files exist. Use `--env-file=<path>` to point at an
explicit local or staging smoke env file without exporting every value in the
shell.

Use `scripts/run_phase1b_local_readiness.py` as the preferred local preflight.
It orchestrates web checks, FastAPI checks, migration preflight, focused backend
tests, and optional local smoke checks. If `--web-base-url` or `--api-base-url`
is omitted, the matching smoke step is recorded as skipped. If a URL is provided
and the server does not respond, that smoke step fails.

Local smoke confirms route behavior, protected redirects, onboarding gates, app
shell rendering, and the no-CRM-mutation boundary. It does not confirm Stripe
webhook delivery unless a future plan adds Stripe CLI or a public tunnel.

Run `npm run smoke:phase1b-local` while the local Next.js server is running. The
script checks `/healthz`, public route rendering, anonymous protected redirects,
onboarding gate wiring, and the static no-CRM-mutation boundary.

Run `scripts/smoke_phase1b_api.py` while the local FastAPI server is running.
The script checks `/health`, verifies onboarding/dashboard API routes fail
closed without auth, and does not call Google, Stripe, or Supabase.

## Staging Services

Before creating the Stripe webhook or smoke account, create a public-data-only
copy of `docs/phase1b-staging-manifest.example.json`, validate it, and
initialize the smoke report:

```bash
cd oze-agent
PYTHONPATH=. python3 scripts/check_phase1b_staging_manifest.py \
  --manifest ../docs/phase1b-staging-manifest.example.json \
  --generate-smoke-id
PYTHONPATH=. python3 scripts/init_phase1b_smoke_report.py \
  --manifest ../docs/phase1b-staging-manifest.example.json \
  --output ../docs/phase1b-smoke-report-YYYYMMDD-HHMM.md \
  --operator Maan
```

The manifest must not contain secrets such as `STRIPE_SECRET_KEY`, `whsec_...`,
`SUPABASE_SERVICE_KEY`, or `BILLING_INTERNAL_SECRET`.
The initializer fills only public staging fields and leaves runtime smoke IDs
blank for the operator to record during the run.

Vercel/web env:

- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`
- `NEXT_PUBLIC_API_BASE_URL=https://<railway-api>`
- `NEXT_PUBLIC_APP_URL=https://<vercel-preview-or-staging>`
- `FASTAPI_INTERNAL_BASE_URL=https://<railway-api>`
- `BILLING_INTERNAL_SECRET=<same value as Railway API>`
- `STRIPE_SECRET_KEY=sk_test_...`
- `STRIPE_WEBHOOK_SECRET=whsec_...`
- `STRIPE_PRICE_ACTIVATION=agent_oze_activation_199`
- `STRIPE_PRICE_MONTHLY=agent_oze_monthly_49`
- `STRIPE_PRICE_YEARLY=agent_oze_yearly_350`

Railway FastAPI env:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `SUPABASE_JWT_SECRET`
- `BILLING_INTERNAL_SECRET=<same value as Vercel>`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI=https://<railway-api>/auth/google/callback`
- `GOOGLE_OAUTH_STATE_SECRET` or fallback `BILLING_INTERNAL_SECRET`
- `ENCRYPTION_KEY`
- `DASHBOARD_URL=https://<vercel-preview-or-staging>`

Railway FastAPI start command:

```bash
uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

The bot service remains separate and keeps its bot start command.

## Staging Smoke

Use a fresh smoke account:

- email: `phase1b+YYYYMMDD-HHMM@<staging-test-domain>`
- Google resource prefix: `P1B Smoke YYYY-MM-DD HHMM`

Run:

1. Apply Supabase migrations:
   - `oze-agent/supabase_migrations/20260428_web_auth_rls.sql`
   - `oze-agent/supabase_migrations/20260428_billing_stripe_0c.sql`
   - preflight before applying:
     `cd oze-agent && PYTHONPATH=. python3 scripts/check_phase1b_migrations.py`
2. Create or verify Stripe test product and prices with the documented lookup
   keys.
3. Run staging manifest preflight and initialize the smoke report:
   - `cd oze-agent && PYTHONPATH=. python3 scripts/check_phase1b_staging_manifest.py --manifest ../docs/phase1b-staging-manifest.example.json --generate-smoke-id`
   - `cd oze-agent && PYTHONPATH=. python3 scripts/init_phase1b_smoke_report.py --manifest ../docs/phase1b-staging-manifest.example.json --output ../docs/phase1b-smoke-report-YYYYMMDD-HHMM.md --operator Maan`
4. Create Stripe test webhook endpoint:
   - `https://<web-domain>/api/webhooks/stripe`
   - events listed in `docs/STRIPE_PHASE_0C_ROLLOUT.md`.
5. Sign up through `/rejestracja`.
6. Pay through `/onboarding/platnosc` with Stripe test card
   `4242 4242 4242 4242`.
7. Verify Supabase billing state and one row per Stripe event ID.
8. Replay the same Stripe event and confirm no duplicate rows with the same
   `stripe_event_id`.
9. Complete Google OAuth and resource creation.
10. Pair Telegram with `/start <code>`.
11. Open `/dashboard`, `/klienci`, and `/kalendarz`; completed users must see
    `live` or `unavailable`, never silent demo data.

Record runtime IDs and results in the initialized smoke report.
