# Stripe Phase 0C Rollout

_Last updated: 29.04.2026_

This checklist is the source of truth for deploying Stripe in Phase 0C.

Phase 0C stays **sandbox-only** until this checklist passes end to end. Code
being green is not enough: billing needs sandbox keys, a public webhook URL, the
Supabase migration, and a real Checkout smoke.

Status 29.04.2026: implementation is code-complete on `feat/web-phase-0c` /
PR #5, including Next.js webhook verification, FastAPI HMAC ingestion,
idempotent billing writes, onboarding screens, and web invariants. This document
now gates Phase 1B rollout/readiness; do not mark billing live-ready until the
checks below are executed against deployed sandbox services.

---

## Local vs staging readiness

Local Phase 1B checks validate configuration, builds, FastAPI route behavior,
protected web routes, onboarding gates, and the no-CRM-mutation boundary. They do
**not** validate Stripe webhook delivery unless Stripe CLI or a public tunnel is
added in a later plan.

Full Checkout + webhook + replay readiness happens only against deployed
staging/preview services:

- Vercel web app at a public URL,
- separate Railway FastAPI service exposing `/internal/billing/stripe-event`,
- staging Supabase cloud,
- Stripe test-mode webhook endpoint.

Use `docs/WEB_PHASE_1B_READINESS.md` for the full Phase 1B runbook and
`docs/PHASE1B_SMOKE_REPORT_TEMPLATE.md` for run evidence.

---

## Stop conditions

Stop immediately if any Stripe API, MCP, or CLI response includes
`livemode: true`.

Do not create live Agent-OZE prices during Phase 0C. A live product was created
by mistake earlier: `prod_UQ9okOhlFVVSNm` (`Agent-OZE`). Deactivate it or clearly
mark it as unused in the live Stripe Dashboard before any production billing
work.

Do not put `SUPABASE_SERVICE_KEY` in Vercel. Vercel verifies Stripe and forwards
events to FastAPI. FastAPI owns durable Supabase writes.

---

## Stable pricing interface

The app accepts either direct Stripe `price_...` IDs or stable lookup keys in:

- `STRIPE_PRICE_ACTIVATION`
- `STRIPE_PRICE_MONTHLY`
- `STRIPE_PRICE_YEARLY`

Prefer lookup keys:

| Purpose | Amount | Stripe type | Lookup key |
|---|---:|---|---|
| Activation | 19900 PLN | one-time | `agent_oze_activation_199` |
| Monthly plan | 4900 PLN | recurring monthly | `agent_oze_monthly_49` |
| Yearly plan | 35000 PLN | recurring yearly | `agent_oze_yearly_350` |

Stripe Price amounts are not edited in place. To change a price later, create a
new Price, transfer or reassign the same lookup key to the new active Price,
and deactivate or detach the old Price. Ensure exactly one active sandbox Price
resolves for each lookup key before smoke testing.

The current Stripe MCP `create_price` tool does not expose `lookup_key`. If MCP
is used to create prices, assign lookup keys afterwards in the Stripe Dashboard
or through a Stripe API/CLI path that supports lookup-key transfer.

---

## Rollout order

1. **Deploy code to staging or preview**
   - Vercel preview/staging has the Phase 0C web code.
   - Railway/FastAPI is a separate API service, not the Telegram bot service.
   - Railway/FastAPI uses start command:
     `uvicorn api.main:app --host 0.0.0.0 --port $PORT`.
   - Railway/FastAPI has `/internal/billing/stripe-event`.
   - Supabase Auth Phase 0B still signs users in.

2. **Create sandbox Stripe product and prices**
   - Confirm test credentials (`sk_test_...`) and sandbox mode.
   - Create sandbox product `Agent-OZE`.
   - Create the three sandbox prices from the table above.
   - Assign lookup keys and confirm each resolves to one active price.

3. **Set first-pass environment variables**
   - Vercel/web:
     - `STRIPE_SECRET_KEY=sk_test_...`
     - `NEXT_PUBLIC_APP_URL=https://<vercel-preview-or-staging>`
     - `FASTAPI_INTERNAL_BASE_URL=https://<railway-api>`
     - `BILLING_INTERNAL_SECRET=<long random shared secret>`
     - price env vars can stay as lookup keys
   - Railway/FastAPI:
     - same `BILLING_INTERNAL_SECRET`
     - existing `SUPABASE_URL`
     - existing `SUPABASE_SERVICE_KEY`

4. **Run Supabase migration**
   - Run `oze-agent/supabase_migrations/20260428_billing_stripe_0c.sql`.
   - Confirm `users`, `payment_history`, `webhook_log`, and `billing_outbox`
     have the Phase 0C fields/tables.

5. **Run staging manifest preflight and initialize report**
   - Copy `docs/phase1b-staging-manifest.example.json` and fill it with public
     staging URLs and lookup keys only.
   - Do not put `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`,
     `SUPABASE_SERVICE_KEY`, or `BILLING_INTERNAL_SECRET` in the manifest.
   - Run:
     `cd oze-agent && PYTHONPATH=. python3 scripts/check_phase1b_staging_manifest.py --manifest ../docs/phase1b-staging-manifest.example.json --generate-smoke-id`
   - Initialize the report before smoke:
     `cd oze-agent && PYTHONPATH=. python3 scripts/init_phase1b_smoke_report.py --manifest ../docs/phase1b-staging-manifest.example.json --output ../docs/phase1b-smoke-report-YYYYMMDD-HHMM.md --operator Maan`

6. **Create sandbox Stripe webhook endpoint**
   - URL: `https://<web-domain>/api/webhooks/stripe`
   - Minimum events:
     - `checkout.session.completed`
     - `checkout.session.async_payment_succeeded`
     - `invoice.payment_succeeded`
     - `invoice.payment_failed`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
   - Copy `whsec_...` into Vercel as `STRIPE_WEBHOOK_SECRET`.
   - Redeploy/restart Vercel after setting `STRIPE_WEBHOOK_SECRET`.

7. **Run sandbox payment smoke**
   - Sign up through `/rejestracja`.
   - Continue to `/onboarding/platnosc`.
   - Pay with Stripe test card `4242 4242 4242 4242`.
   - Verify in Stripe Dashboard:
     - Checkout Session is complete.
     - Customer exists.
     - Subscription is active.
     - Invoice is paid.
   - Verify in Supabase:
     - `users.subscription_status = active`
     - `users.activation_paid = true`
     - `payment_history` has one Stripe row.
     - `webhook_log.processed = true`
     - `billing_outbox` has one event.
   - Verify `/dashboard` shows active subscription.

8. **Replay/idempotency check**
   - Replay the Stripe webhook event from Dashboard or CLI.
   - Confirm the same `stripe_event_id` does not create duplicate
     `payment_history` or `billing_outbox` rows.
   - Confirm FastAPI logs show accepted HMAC and duplicate-safe processing.

9. **Review gate**
   - Run:
     - `cd web && npm run test:invariants`
     - `cd web && npm run lint && npm run build`
     - `cd oze-agent && PYTHONPATH=. pytest -q`
   - Run an independent cold review focused only on payments, env, webhook retry
     behavior, and idempotency before merge/deploy.

10. **Onboarding continuation smoke**
   - From a paid sandbox user, continue to `/onboarding/google`.
   - Complete Google OAuth and confirm redirect to `/onboarding/google/sukces`.
   - Create/link Sheets, Calendar, and Drive from `/onboarding/zasoby`.
   - Confirm created resource IDs persist in `users`.
   - Open `/onboarding/telegram`, confirm it shows `/start <code>`, send that to
     the bot, and confirm `telegram_id` links to the same user.
   - Confirm `/dashboard`, `/klienci`, and `/kalendarz` show live or unavailable
     CRM source state, never unlabeled demo data for a completed user.

---

## Notes

Hosted Checkout is created server-side, so Phase 0C does **not** need
`NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`. Add a publishable key later only if the app
uses Stripe Elements, Billing Portal client helpers, or client-side Stripe JS.

`BILLING_INTERNAL_SECRET` must be the same long random value in Vercel and
Railway. Rotate it if it is ever pasted into chat or logs.
