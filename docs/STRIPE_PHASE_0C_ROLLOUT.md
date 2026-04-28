# Stripe Phase 0C Rollout

_Last updated: 29.04.2026_

This checklist is the source of truth for deploying Stripe in Phase 0C.

Phase 0C stays **sandbox-only** until this checklist passes end to end. Code
being green is not enough: billing needs sandbox keys, a public webhook URL, the
Supabase migration, and a real Checkout smoke.

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

5. **Create sandbox Stripe webhook endpoint**
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

6. **Run sandbox payment smoke**
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

7. **Replay/idempotency check**
   - Replay the Stripe webhook event from Dashboard or CLI.
   - Confirm `payment_history` and `billing_outbox` are not duplicated.
   - Confirm FastAPI logs show accepted HMAC and duplicate-safe processing.

8. **Review gate**
   - Run:
     - `cd web && npm run lint && npm run build`
     - `cd oze-agent && PYTHONPATH=. pytest -q`
   - Run an independent cold review focused only on payments, env, webhook retry
     behavior, and idempotency before merge/deploy.

---

## Notes

Hosted Checkout is created server-side, so Phase 0C does **not** need
`NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`. Add a publishable key later only if the app
uses Stripe Elements, Billing Portal client helpers, or client-side Stripe JS.

`BILLING_INTERNAL_SECRET` must be the same long random value in Vercel and
Railway. Rotate it if it is ever pasted into chat or logs.
