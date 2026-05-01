# Phase 1B Smoke Report

_Run date: YYYY-MM-DD HH:MM Europe/Warsaw_
_Branch/commit:_
_Operator:_
_Environment: local / staging_

## Smoke Account

- Email: `phase1b+YYYYMMDD-HHMM@<staging-test-domain>`
- Supabase auth user ID:
- Supabase public user ID:
- Google resource prefix: `P1B Smoke YYYY-MM-DD HHMM`

## Local Readiness

- `cd web && npm run check:phase1b-env`:
- `cd web && npm run test:invariants && npm run lint && npm run build`:
- `cd oze-agent && PYTHONPATH=. python3 scripts/verify_phase1b_env.py`:
- `cd oze-agent && PYTHONPATH=. pytest tests/test_billing.py tests/test_onboarding_api.py tests/test_dashboard_api.py tests/test_api_auth.py -q`:
- `cd oze-agent && PYTHONPATH=. pytest -q`:

## Staging Services

- Vercel URL:
- Railway API URL:
- Railway API start command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
- Railway bot service:
- Supabase project:
- Stripe mode: test

## Stripe Sandbox

- Product ID:
- Activation price ID / lookup key:
- Monthly price ID / lookup key:
- Yearly price ID / lookup key:
- Checkout Session ID:
- Customer ID:
- Subscription ID:
- Invoice ID:
- Webhook event IDs:
- Replay event ID:
- Duplicate rows with same `stripe_event_id`: yes / no

## Supabase Verification

- `users.subscription_status = active`: yes / no
- `users.activation_paid = true`: yes / no
- `payment_history` row:
- `webhook_log.processed = true`:
- `billing_outbox` row:

## Onboarding Continuation

- Google OAuth redirect succeeded: yes / no
- Sheets ID:
- Calendar ID:
- Drive folder ID:
- Telegram pairing code shown: yes / no
- Telegram `/start <code>` consumed: yes / no
- `users.telegram_id` linked: yes / no

## Browser Smoke

- `/rejestracja`:
- `/login`:
- `/onboarding/platnosc`:
- `/onboarding/google`:
- `/onboarding/zasoby`:
- `/onboarding/telegram`:
- `/dashboard`:
- `/klienci`:
- `/kalendarz`:
- Completed user source state is `live` or `unavailable`: yes / no
- CRM mutation forms absent: yes / no

## Issues

- Blockers:
- Follow-ups:
- Cleanup required:

