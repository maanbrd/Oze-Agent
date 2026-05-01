# Phase 1B Smoke Report

_Run date: 2026-04-29 20:46 Europe/Warsaw_
_Branch/commit: feat/web-phase-0c / 458748f_
_Operator: Maan_
_Environment: staging_

## Smoke Account

- Email: `phase1b+1777628027119@agent-oze.test`
- Supabase auth user ID: `ddcfd2aa-a55d-47ea-af04-3b3cd99f43e7`
- Supabase public user ID: `14f0f370-c121-4cf6-9252-e4c2aa2a80be`
- Google resource prefix: `P1B Smoke 2026-05-01`

## Local Readiness

- `cd web && npm run check:phase1b-env`: blocked locally; staging env is configured in Vercel Preview, but not loaded into the local shell.
- `cd web && npm run test:invariants && npm run lint && npm run build`: pass on 2026-04-29 15:16 Europe/Warsaw.
- `cd web && npm run test:invariants`: pass on 2026-05-01.
- `cd web && npm run lint`: pass on 2026-05-01.
- `cd web && npm run build`: pass on 2026-05-01.
- `cd oze-agent && PYTHONPATH=. .venv/bin/python scripts/verify_phase1b_env.py`: blocked locally; Railway staging env is configured, but not loaded into the local shell.
- Backend pytest results from bare `python3` are not accepted for Phase 1B because local `python3` is Python 3.14; backend verification must use Python 3.13 from `.venv/bin/python`.
- `cd oze-agent && PYTHONPATH=. .venv/bin/python -m pytest tests/test_google_auth.py tests/handlers/test_start_handler.py -q`: 6 passed on 2026-05-01 using Python 3.13.
- `cd oze-agent && PYTHONPATH=. .venv/bin/python -m pytest tests/test_phase1b_local_readiness.py tests/test_google_auth.py tests/handlers/test_start_handler.py -q`: 13 passed on 2026-05-01 using Python 3.13.
- `cd oze-agent && PYTHONPATH=. .venv/bin/python -m pytest tests/test_billing.py tests/test_onboarding_api.py tests/test_dashboard_api.py tests/test_api_auth.py -q`: 19 passed on 2026-05-01 using Python 3.13.
- `cd oze-agent && PYTHONPATH=. .venv/bin/python -m pytest -q`: 894 passed on 2026-05-01 using Python 3.13.

## Staging Services

- Vercel URL: https://oze-agent-git-feat-web-phase-0c-maanbrds-projects.vercel.app
- Vercel preview with anonymous onboarding redirect fix: https://oze-agent-2ylsi554h-maanbrds-projects.vercel.app
- Vercel preview with login `next` sanitizer and expanded form smoke: https://oze-agent-f3gedmvl1-maanbrds-projects.vercel.app
- Vercel preview with failed-login `next` preservation and external-link hardening: https://oze-agent-a0yye9azf-maanbrds-projects.vercel.app
- Vercel preview with dashboard Warsaw-date readiness fix: https://oze-agent-qliq44fmr-maanbrds-projects.vercel.app
- Vercel preview with authenticated payment-return readiness fix: https://oze-agent-pxz61tgbp-maanbrds-projects.vercel.app
- Vercel preview with authenticated Google-success readiness fix: https://oze-agent-88p1mes5f-maanbrds-projects.vercel.app
- Vercel preview with onboarding action error-handling fix: https://oze-agent-cybne6mzc-maanbrds-projects.vercel.app
- Vercel preview with trusted external redirect allowlist fix: https://oze-agent-5vtrcjksk-maanbrds-projects.vercel.app
- Vercel preview with Stripe webhook FastAPI timeout guard: https://oze-agent-9k76wno5m-maanbrds-projects.vercel.app
- Vercel inspect URL for fixed preview: https://vercel.com/maanbrds-projects/oze-agent/8DBg4N6PXrpMmYGXcmMuusZcoWTg
- Vercel inspect URL for latest preview: https://vercel.com/maanbrds-projects/oze-agent/DrzAG5Agm9xScsS2XSMBmEditA8F
- Vercel inspect URL for latest preview: https://vercel.com/maanbrds-projects/oze-agent/6byaNNKgRwdTsWGVQC4wKYjmMP9n
- Vercel inspect URL for latest preview: https://vercel.com/maanbrds-projects/oze-agent/5EUH5YDL4jB5G5LNmUDJEr2UaB7x
- Vercel inspect URL for latest preview: https://vercel.com/maanbrds-projects/oze-agent/GZL7m9cxbz7UCdypnZCCTz9Z5EyG
- Vercel inspect URL for latest preview: https://vercel.com/maanbrds-projects/oze-agent/GcZaKvi4g5JBWzgB5JMW7zU1VuBe
- Vercel inspect URL for latest preview: https://vercel.com/maanbrds-projects/oze-agent/5QA5C7Lszq7UfZkKSaazQJaE5GUG
- Vercel inspect URL for latest preview: https://vercel.com/maanbrds-projects/oze-agent/EFGSi2pdByf7aRF8oyyHWCm5w3bQ
- Vercel inspect URL for latest preview: https://vercel.com/maanbrds-projects/oze-agent/HNnZLbDkHDDnXFwRt3zhv4r7pcUq
- Staging alias update: `oze-agent-git-feat-web-phase-0c-maanbrds-projects.vercel.app` now points to the fixed preview deployment.
- Staging alias update: `oze-agent-git-feat-web-phase-0c-maanbrds-projects.vercel.app` now points to the login sanitizer preview deployment.
- Staging alias update: `oze-agent-git-feat-web-phase-0c-maanbrds-projects.vercel.app` now points to the failed-login/links hardening preview deployment.
- Staging alias update: `oze-agent-git-feat-web-phase-0c-maanbrds-projects.vercel.app` now points to the dashboard Warsaw-date readiness preview deployment.
- Staging alias update: `oze-agent-git-feat-web-phase-0c-maanbrds-projects.vercel.app` now points to the authenticated payment-return readiness preview deployment.
- Staging alias update: `oze-agent-git-feat-web-phase-0c-maanbrds-projects.vercel.app` now points to the authenticated Google-success readiness preview deployment.
- Staging alias update: `oze-agent-git-feat-web-phase-0c-maanbrds-projects.vercel.app` now points to the onboarding action error-handling preview deployment.
- Staging alias update: `oze-agent-git-feat-web-phase-0c-maanbrds-projects.vercel.app` now points to the trusted external redirect allowlist preview deployment.
- Staging alias update: `oze-agent-git-feat-web-phase-0c-maanbrds-projects.vercel.app` now points to the Stripe webhook FastAPI timeout guard preview deployment.
- Railway API URL: https://api-staging-staging-7359.up.railway.app
- Railway API start command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
- Railway bot service: existing production bot service remains separate from `api-staging`.
- Supabase project: https://dadjuohzlusjhhpgeivc.supabase.co
- Stripe mode: test

## Stripe Sandbox

- Product ID: `prod_UQQV4JkFzD1you` monthly, `prod_UQQXdhrCeIUJxv` yearly, activation product shown in Stripe as Agent-OZE aktywacja.
- Activation price ID / lookup key: agent_oze_activation_199
- Monthly price ID / lookup key: agent_oze_monthly_49
- Yearly price ID / lookup key: agent_oze_yearly_350
- Checkout Session ID: `cs_test_b1XrquiFr3GwOvGjayh97IF3eO0IHlCgtQJedXBZBkO82PF9ZMVKehq3t0`
- Customer ID: `cus_UR79g8MjIzgEkq`
- Subscription ID: `sub_1TSEv2FzlMN5xVVk7yXagDAL`
- Invoice ID: `in_1TSEv0FzlMN5xVVk5DCpTD03`
- Webhook event IDs: `evt_1TSEv4FzlMN5xVVkfraPUBtc` (`checkout.session.completed`), `evt_1TSEv5FzlMN5xVVkl1gVFbmH` (`invoice.payment_succeeded`)
- Replay event ID: `evt_1TSEv5FzlMN5xVVkl1gVFbmH`; Stripe replay/resend uses the same event ID. Supabase `payment_history`, `billing_outbox`, and `webhook_log` counts remained `1` for this `stripe_event_id` after replay.
- Duplicate rows with same `stripe_event_id`: no

## Supabase Verification

- `users.subscription_status = active`: yes
- `users.activation_paid = true`: yes
- `payment_history` row: invoice row `3b4cb4a8-917e-4c1b-936d-dc7a74932471`, amount `248` PLN, status `paid`, type `stripe_invoice`, invoice `in_1TSEv0FzlMN5xVVk5DCpTD03`, event `evt_1TSEv5FzlMN5xVVkl1gVFbmH`; checkout row `3649dcba-e6a5-44b0-b046-af8d0c6c5fa4`.
- `webhook_log.processed = true`: yes, invoice webhook row `04a8e887-0c70-4975-b09e-ae901f6ac310`, duplicate `false`; checkout webhook row `4c22d74f-94e1-4e1c-be4d-986258d4dd14`.
- `billing_outbox` row: invoice outbox row `7ab27bc5-6d35-42cd-8497-023fe6f325a5`, event_type `billing_invoice_paid`, processed `false`; checkout outbox row `78ffed8b-a049-488d-b553-12c214f6dc45`.

## Onboarding Continuation

- Google OAuth redirect succeeded: yes
- Sheets ID: `1-5uTVVTa0MpxyxzVALoiOyzqhJS-_BE8ySp3MstTCOU`
- Calendar ID: `b313ac8b744820614f8f8a83f88b50f5d785be78bd5fd70eb86067045f4f4872@group.calendar.google.com`
- Drive folder ID: `1WR_9KIfyfIvdZciFKJxIqP4ObWncjyA1`
- Telegram pairing code shown: yes
- Telegram `/start <code>` consumed: yes
- `users.telegram_id` linked: yes

## Browser Smoke

- `/rejestracja`: pass; smoke account created earlier in staging.
- `/login`: pass for `phase1b+1777628027119@agent-oze.test`.
- `/onboarding/platnosc`: pass; monthly checkout completed with Stripe test card.
- `/onboarding/google`: pass; operator completed Google OAuth and Supabase verification confirms token persistence.
- `/onboarding/zasoby`: pass; Sheets, Calendar, and Drive IDs persisted in Supabase.
- `/onboarding/telegram`: pass; pairing code was shown, bot consumed `/start <code>`, and completed account returns to dashboard with completion banner.
- `/onboarding/google`, `/onboarding/zasoby`, `/onboarding/telegram`: fixed preview smoke pass on 01.05.2026; anonymous sessions redirect to `/login?next=...`.
- `/login?next=//example.com/phish`: fixed preview and staging alias smoke pass on 01.05.2026; hidden login `next` falls back to `/dashboard`.
- `/rejestracja`: Browser Use form-fill pass on 01.05.2026 without submit; synthetic smoke values filled, required form controls usable, submit button enabled.
- Browser Use verification on fixed preview: `/onboarding/telegram` lands on `/login?next=/onboarding/telegram`, title `Logowanie | Agent-OZE`, and no fallback `------` / `/start KOD` is visible.
- Browser Use verification on staging alias: `/onboarding/telegram` lands on `/login?next=/onboarding/telegram`, title `Logowanie | Agent-OZE`, and no fallback `------` / `/start KOD` is visible.
- `/dashboard`: pass for completed user; live Google source state visible.
- `/klienci`: pass for completed user; no CRM mutation forms observed.
- `/kalendarz`: pass for completed user; no CRM mutation forms observed.
- Completed user source state is `live` or `unavailable`: yes
- CRM mutation forms absent: yes

## Issues

- Blockers: brak
- Follow-ups: Stripe MCP still lists no test products/prices, while Stripe Dashboard and real Checkout confirm the test catalog exists; use Dashboard/Checkout evidence for this smoke. Versioning remains the next readiness gate: package local/no-git deploy changes into commits, push `feat/web-phase-0c`, redeploy from that SHA, and repeat the smoke on the staging alias.
- Fixed in preview: `web/lib/api/account.ts` adds `requireCurrentAccount(nextPath)`; `/onboarding/google`, `/onboarding/zasoby`, and `/onboarding/telegram` call it before rendering; `web/scripts/smoke-phase1b-local.mjs` now checks anonymous redirects for all three routes.
- Fixed in preview: `web/lib/routes.ts` adds `safeLocalPath(...)`; `/login` and login server action reject protocol-relative/external `next` targets; `web/scripts/smoke-phase1b-local.mjs` now checks login form fields, sanitized `next`, and registration form fields.
- Fixed in preview: failed login preserves the sanitized `next` target so onboarding users can retry login without losing `/onboarding/...`; external `_blank` links use `noopener noreferrer`; events without `calendarUrl` no longer render dead `href="#"` links.
- Fixed in preview: dashboard readiness no longer hardcodes `2026-04-29`; dashboard uses the current Europe/Warsaw date key for due-today and calendar sections.
- Fixed in preview: `/onboarding/sukces` and `/onboarding/anulowano` no longer show payment return state to anonymous users; `/onboarding/sukces` no longer claims activation until the profile has `subscription_status = active`.
- Fixed in preview: `/onboarding/google/sukces` no longer shows Google success state to anonymous users and no longer claims success until onboarding status confirms Google tokens.
- Fixed in preview: Google OAuth, Google resource creation, Telegram code generation, and account update server actions now redirect back with Polish user-facing messages instead of surfacing raw Next.js error pages on API failures.
- Fixed in preview: Stripe Checkout and Google OAuth server actions now validate external redirect targets; Stripe is limited to `https://checkout.stripe.com` and Google OAuth to `https://accounts.google.com`.
- Fixed in preview: Stripe webhook forwarding to FastAPI now has an 8s timeout guard and returns controlled `502` JSON when FastAPI is unavailable.
- Fixed in preview: dashboard CRM fetch failures now preserve source-state UI instead of crashing; completed users get an `unavailable` CRM state and incomplete/anonymous contexts keep demo data.
- Fixed in preview: web account and onboarding API fetches now have 8s timeout guards; `/api/me` failures return a controlled Polish account error, and onboarding gate links sanitize backend-provided `nextStep`.
- Fixed in preview: Google Workspace links rendered from profile/CRM data are constrained to trusted Google origins and resource IDs in quick links are URL-encoded before rendering.
- Fixed in preview: dashboard/calendar date grouping and labels now use Europe/Warsaw helpers instead of a hardcoded `+02:00` daylight-saving offset.
- Fixed in preview: `/healthz` now exposes Phase 1B web readiness markers, and smoke asserts them to catch stale/stuck deploys.
- Added local verification: `npm run test:routes` covers `safeLocalPath(...)` and `trustedExternalUrl(...)` behavior for protocol-relative, `javascript:`, non-HTTPS, allowed Stripe/Google/Workspace origins, disallowed lookalike origins, and empty inputs.
- Fixed in preview: `safeLocalPath(...)` now rejects control characters and backslashes before URL parsing; route tests reproduced the previous CR/LF normalization issue.
- Added local verification: `npm run test:dates` covers Europe/Warsaw date keys and DST-sensitive labels/times.
- Readiness runner update: `scripts/run_phase1b_local_readiness.py` now runs `npm run test:web-units` before lint/build.
- Readiness preflight hardened locally: `npm run check:phase1b-env -- --scope=staging` now validates URL syntax and blocks non-HTTPS staging Supabase/API/app URLs.
- Applied to staging on 01.05.2026: `oze-agent/supabase_migrations/20260501_web_auth_function_hardening.sql` revokes direct RPC execution of `public.handle_new_auth_user()` from public browser roles. Verification query on `information_schema.routine_privileges` returned no direct privileges for this function after apply.
- Smoke coverage expanded locally: anonymous redirect checks now cover all current protected app routes: `/dashboard`, `/klienci`, `/kalendarz`, `/platnosci`, `/ustawienia`, `/import`, `/instrukcja`, and `/faq`.
- Verification: `npm run smoke:phase1b-local -- --base-url=https://oze-agent-2ylsi554h-maanbrds-projects.vercel.app` passed on 01.05.2026.
- Verification: `npm run smoke:phase1b-local -- --base-url=https://oze-agent-f3gedmvl1-maanbrds-projects.vercel.app` passed on 01.05.2026.
- Verification: `npm run smoke:phase1b-local -- --base-url=https://oze-agent-a0yye9azf-maanbrds-projects.vercel.app` passed on 01.05.2026.
- Verification: `npm run smoke:phase1b-local -- --base-url=https://oze-agent-qliq44fmr-maanbrds-projects.vercel.app` passed on 01.05.2026.
- Verification: `npm run smoke:phase1b-local -- --base-url=https://oze-agent-git-feat-web-phase-0c-maanbrds-projects.vercel.app` passed after alias update on 01.05.2026.
- Verification: `npm run test:invariants` passed after protected-route smoke expansion on 01.05.2026.
- Verification: `npm run lint` passed after protected-route smoke expansion on 01.05.2026.
- Verification: `npm run build` passed after protected-route smoke expansion on 01.05.2026.
- Verification: `npm run smoke:phase1b-local -- --base-url=https://oze-agent-git-feat-web-phase-0c-maanbrds-projects.vercel.app` passed with expanded protected-route coverage on 01.05.2026.
- Browser Use verification on staging alias: `/login?next=//example.com/phish` renders hidden `next` value `/dashboard` on 01.05.2026.
- Verification: `npm run test:invariants`, `npm run lint`, and `npm run build` passed after authenticated payment-return fix on 01.05.2026.
- Verification: `npm run smoke:phase1b-local -- --base-url=https://oze-agent-pxz61tgbp-maanbrds-projects.vercel.app` passed on 01.05.2026.
- Browser Use verification on preview: anonymous `/onboarding/sukces` redirects to `/login?next=/onboarding/platnosc` on 01.05.2026.
- Verification: `npm run smoke:phase1b-local -- --base-url=https://oze-agent-git-feat-web-phase-0c-maanbrds-projects.vercel.app` passed after alias update to payment-return preview on 01.05.2026.
- Browser Use verification on staging alias: anonymous `/onboarding/sukces` redirects to `/login?next=/onboarding/platnosc` on 01.05.2026.
- Verification: `npm run test:invariants`, `npm run lint`, and `npm run build` passed after authenticated Google-success fix on 01.05.2026.
- Verification: `npm run smoke:phase1b-local -- --base-url=https://oze-agent-88p1mes5f-maanbrds-projects.vercel.app` passed on 01.05.2026.
- Browser Use verification on preview: anonymous `/onboarding/google/sukces` redirects to `/login?next=/onboarding/google/sukces` on 01.05.2026.
- Verification: `npm run smoke:phase1b-local -- --base-url=https://oze-agent-git-feat-web-phase-0c-maanbrds-projects.vercel.app` passed after alias update to Google-success preview on 01.05.2026.
- Browser Use verification on staging alias: anonymous `/onboarding/google/sukces` redirects to `/login?next=/onboarding/google/sukces` on 01.05.2026.
- Verification: `npm run test:invariants`, `npm run lint`, and `npm run build` passed after onboarding action error-handling fix on 01.05.2026.
- Verification: `npm run smoke:phase1b-local -- --base-url=https://oze-agent-cybne6mzc-maanbrds-projects.vercel.app` passed on 01.05.2026.
- Verification: `npm run smoke:phase1b-local -- --base-url=https://oze-agent-git-feat-web-phase-0c-maanbrds-projects.vercel.app` passed after alias update to onboarding action error-handling preview on 01.05.2026.
- Verification: `npm run test:invariants`, `npm run lint`, and `npm run build` passed after trusted external redirect allowlist fix on 01.05.2026.
- Verification: `npm run smoke:phase1b-local -- --base-url=https://oze-agent-5vtrcjksk-maanbrds-projects.vercel.app` passed on 01.05.2026.
- Verification: `npm run smoke:phase1b-local -- --base-url=https://oze-agent-git-feat-web-phase-0c-maanbrds-projects.vercel.app` passed after alias update to trusted external redirect allowlist preview on 01.05.2026.
- Verification: `npm run test:invariants`, `npm run lint`, and `npm run build` passed after Stripe webhook FastAPI timeout guard on 01.05.2026.
- Verification: `npm run smoke:phase1b-local -- --base-url=https://oze-agent-9k76wno5m-maanbrds-projects.vercel.app` passed on 01.05.2026.
- Verification: `npm run smoke:phase1b-local -- --base-url=https://oze-agent-git-feat-web-phase-0c-maanbrds-projects.vercel.app` passed after alias update to Stripe webhook timeout guard preview on 01.05.2026.
- Verification: `npm run smoke:phase1b-local -- --base-url=https://oze-agent-6t3nels8n-maanbrds-projects.vercel.app` passed on 01.05.2026.
- Verification: `npm run smoke:phase1b-local -- --base-url=https://oze-agent-git-feat-web-phase-0c-maanbrds-projects.vercel.app` passed after alias update to CRM fetch fallback preview on 01.05.2026.
- Vercel preview with CRM fetch fallback fix: `https://oze-agent-6t3nels8n-maanbrds-projects.vercel.app`; inspect URL: `https://vercel.com/maanbrds-projects/oze-agent/FD1A6YsFHDu77nh7KhmjaBmGVj17`.
- Verification: `npm run test:invariants`, `npm run lint`, and `npm run build` passed after web API timeout/gate sanitizer fix on 01.05.2026.
- Verification: `npm run smoke:phase1b-local -- --base-url=https://oze-agent-3ko79scxg-maanbrds-projects.vercel.app` passed on 01.05.2026.
- Verification: `npm run smoke:phase1b-local -- --base-url=https://oze-agent-git-feat-web-phase-0c-maanbrds-projects.vercel.app` passed after alias update to web API timeout/gate sanitizer preview on 01.05.2026.
- Vercel preview with web API timeout/gate sanitizer fix: `https://oze-agent-3ko79scxg-maanbrds-projects.vercel.app`; inspect URL: `https://vercel.com/maanbrds-projects/oze-agent/8WGqAnHw6dzHf5dpJKXhZN1jY8MJ`.
- Verification: `npm run test:invariants`, `npm run lint`, and `npm run build` passed after Google Workspace link hardening on 01.05.2026.
- Verification: `npm run smoke:phase1b-local -- --base-url=https://oze-agent-iib9qklkz-maanbrds-projects.vercel.app` passed on 01.05.2026.
- Verification: `npm run smoke:phase1b-local -- --base-url=https://oze-agent-git-feat-web-phase-0c-maanbrds-projects.vercel.app` passed after alias update to Google Workspace link hardening preview on 01.05.2026.
- Vercel preview with Google Workspace link hardening: `https://oze-agent-iib9qklkz-maanbrds-projects.vercel.app`; inspect URL: `https://vercel.com/maanbrds-projects/oze-agent/GTqvnCEET1vhcrCawQzw672ERVv9`.
- Verification: `npm run test:invariants`, `npm run lint`, and `npm run build` passed after Warsaw date/time UI fix on 01.05.2026.
- Verification: `npm run smoke:phase1b-local -- --base-url=https://oze-agent-3xm01t0e6-maanbrds-projects.vercel.app` passed on 01.05.2026.
- Verification: `npm run smoke:phase1b-local -- --base-url=https://oze-agent-git-feat-web-phase-0c-maanbrds-projects.vercel.app` passed after alias update to Warsaw date/time UI fix on 01.05.2026.
- Vercel preview with Warsaw date/time UI fix: `https://oze-agent-3xm01t0e6-maanbrds-projects.vercel.app`; inspect URL: `https://vercel.com/maanbrds-projects/oze-agent/CQFG5eQ1SsNoBYrCArCEvpEjzk5J`.
- Browser Use verification on staging alias after Warsaw/date deploy: `/onboarding/telegram` lands on `/login?next=/onboarding/telegram`, title `Logowanie | Agent-OZE`, and no fallback `------` / `/start KOD` is visible on 01.05.2026.
- Claude Code read-only review on health readiness diff returned no blocking regressions on 01.05.2026; non-blocking follow-up noted broad `target="_blank"` invariant ordering and suggested route helper behavior tests.
- Verification: `npm run test:invariants`, `npm run lint`, and `npm run build` passed after health readiness marker fix on 01.05.2026.
- Verification: `npm run smoke:phase1b-local -- --base-url=https://oze-agent-eju0nzvpd-maanbrds-projects.vercel.app` passed on 01.05.2026.
- Verification: `npm run smoke:phase1b-local -- --base-url=https://oze-agent-git-feat-web-phase-0c-maanbrds-projects.vercel.app` passed after alias update to health readiness marker fix on 01.05.2026.
- Vercel preview with health readiness marker fix: `https://oze-agent-eju0nzvpd-maanbrds-projects.vercel.app`; inspect URL: `https://vercel.com/maanbrds-projects/oze-agent/6ApgmKALZc5WTuKcQLKSMa3LQUbc`.
- Verification: `npm run test:routes`, `npm run test:invariants`, `npm run lint`, and `npm run build` passed after adding route helper behavior tests on 01.05.2026.
- Verification: `npm run smoke:phase1b-local -- --base-url=https://oze-agent-30uuav25e-maanbrds-projects.vercel.app` passed on 01.05.2026.
- Verification: `npm run smoke:phase1b-local -- --base-url=https://oze-agent-git-feat-web-phase-0c-maanbrds-projects.vercel.app` passed after alias update to route helper behavior test preview on 01.05.2026.
- Vercel preview with route helper behavior tests: `https://oze-agent-30uuav25e-maanbrds-projects.vercel.app`; inspect URL: `https://vercel.com/maanbrds-projects/oze-agent/3tzHZib4veTYh9naQyrtwNBKsuoC`.
- Verification: `npm run test:invariants`, `npm run lint`, and `npm run build` passed after tightening the `target="_blank"` invariant noted by Claude Code on 01.05.2026.
- Verification: `npm run smoke:phase1b-local -- --base-url=https://oze-agent-1b03hjwgp-maanbrds-projects.vercel.app` passed on 01.05.2026.
- Verification: `npm run smoke:phase1b-local -- --base-url=https://oze-agent-git-feat-web-phase-0c-maanbrds-projects.vercel.app` passed after alias update to tightened invariant preview on 01.05.2026.
- Vercel preview with tightened invariant fix: `https://oze-agent-1b03hjwgp-maanbrds-projects.vercel.app`; inspect URL: `https://vercel.com/maanbrds-projects/oze-agent/3dymPqqHBuwb7gn6q1AntKiTERpt`.
- Claude Code read-only next-slice review was run via `claude -p` and logged to `tmp/claude-reviews/20260501-1116-next-slice.md`; it returned no blocking findings and recommended web helper unit tests on 01.05.2026.
- Verification: `npm run test:web-units`, `npm run test:invariants`, `npm run lint`, `npm run build`, and `PYTHONPATH=. .venv/bin/python -m pytest tests/test_phase1b_local_readiness.py -q` passed after web unit readiness integration on 01.05.2026.
- Verification: `npm run smoke:phase1b-local -- --base-url=https://oze-agent-jh3n69m67-maanbrds-projects.vercel.app` passed on 01.05.2026.
- Verification: `npm run smoke:phase1b-local -- --base-url=https://oze-agent-git-feat-web-phase-0c-maanbrds-projects.vercel.app` passed after alias update to web unit readiness preview on 01.05.2026.
- Vercel preview with web unit readiness integration: `https://oze-agent-jh3n69m67-maanbrds-projects.vercel.app`; inspect URL: `https://vercel.com/maanbrds-projects/oze-agent/Gdf2zwKVRB3tPCzTTRWRXCYx8XaD`.
- Verification: `PYTHONPATH=. .venv/bin/python -m pytest tests/test_phase1b_local_readiness.py tests/test_phase1b_smoke_report_validate.py tests/test_phase1b_migrations.py tests/test_google_auth.py tests/handlers/test_start_handler.py tests/test_billing.py tests/test_onboarding_api.py tests/test_dashboard_api.py tests/test_api_auth.py -q` passed on 01.05.2026, 49 passed.
- Verification: synthetic HTTPS staging env passed `npm run check:phase1b-env -- --scope=staging` on 01.05.2026.
- Verification: synthetic HTTP staging env failed `npm run check:phase1b-env -- --scope=staging` with non-HTTPS URL errors on 01.05.2026.
- Verification: `PYTHONPATH=. .venv/bin/python scripts/check_phase1b_migrations.py` passed after adding the auth function hardening migration on 01.05.2026.
- Verification: `PYTHONPATH=. .venv/bin/python -m pytest tests/test_phase1b_migrations.py -q` passed after adding the auth function hardening migration on 01.05.2026.
- Verification: `PYTHONPATH=. .venv/bin/python -m pytest tests/test_phase1b_local_readiness.py tests/test_phase1b_smoke_report_validate.py tests/test_phase1b_migrations.py tests/test_google_auth.py tests/handlers/test_start_handler.py -q` passed on 01.05.2026, 30 passed.
- Verification: `PYTHONPATH=. .venv/bin/python scripts/check_phase1b_staging_manifest.py --manifest ../docs/phase1b-staging-manifest.json --generate-smoke-id` passed on 01.05.2026.
- Verification: `PYTHONPATH=. python3 scripts/run_phase1b_local_readiness.py --report /tmp/phase1b-python-runtime-check.md` failed fast on 01.05.2026 because local `python3` is Python 3.14, and no later readiness steps were run.
- Verification: `PYTHONPATH=. .venv/bin/python scripts/validate_phase1b_smoke_report.py --report ../docs/phase1b-smoke-report-20260429-1455.md` fails as expected until operator fills Google resource IDs, Telegram pairing evidence, completed-user source-state evidence, and clears blockers.
- Deployment note: direct Vercel CLI deploy from the git worktree is blocked by Vercel team commit-author attribution for `mansoniasty@MBP-Maan.home`; the fixed preview was deployed from a temporary no-git source copy, with no repo secrets copied.
- Browser Use authenticated signup smoke on 01.05.2026 created a staging test account and reached `/onboarding/platnosc`; first blocker was authenticated payment render/profile fetch. Fixed code-side with `normalizeFastApiBaseUrl(...)`, FastAPI profile fetch diagnostics, and Supabase RLS read-only profile fallback.
- Vercel staging env fix on 01.05.2026: generic Preview `FASTAPI_INTERNAL_BASE_URL`, `NEXT_PUBLIC_API_BASE_URL`, and `NEXT_PUBLIC_APP_URL` were corrected for no-git deploys. Browser Use then verified `/onboarding/platnosc` no longer shows the profile/API fallback warning and renders payment buttons with the FastAPI profile path.
- Historical blocker on 01.05.2026: Stripe checkout could not start on the no-git Preview deployment because the generic Preview Stripe server key was empty at runtime. Branch-scoped Preview env appeared complete in `vercel env ls`, but the local preview-env pull returned empty Stripe values, so the values had to be re-entered in Vercel before payment smoke could continue.
- Resolved on 01.05.2026: after Vercel Stripe/Billing env update and redeploy, Browser Use opened Stripe Checkout from `/onboarding/platnosc`; the operator entered sandbox card details manually. Supabase verification for `phase1b+1777628027119@agent-oze.test` shows `subscription_status=active`, `subscription_plan=monthly`, `activation_paid=true`, and Stripe checkout/subscription references present.
- Browser Use verification on 01.05.2026: after payment, `/onboarding/google` renders the Google step and the "Połącz konto Google" action navigates to Google OAuth login with the expected Railway callback URL and scopes. Smoke is paused at Google login/consent; no Google credentials or OAuth consent were entered by Codex.
- Resolved on 01.05.2026: operator completed Google OAuth and Telegram pairing. Supabase verification for `phase1b+1777628027119@agent-oze.test` shows payment active, Google token present, Sheets/Calendar/Drive IDs present, Telegram linked, and `onboarding_completed=true`.
- Browser Use verification on 01.05.2026: `/onboarding/telegram` shows "Telegram połączony." and a dashboard link. `/dashboard` loads without demo/unavailable fallback, shows source "Google Sheets i Calendar", and exposes direct Sheets/Calendar/Drive links.
- Claude Code read-only review of the FastAPI base URL/payment blocker slice returned no blocking findings on 01.05.2026; follow-ups implemented: CRM dashboard fetch timeout and encoded `next` in `requireCurrentAccount`.
- Verification: `npm run test:web-units`, `npm run test:invariants`, `npm run lint`, and `npm run build` passed after the FastAPI base URL/profile fallback changes on 01.05.2026.
- Verification: `npm run test:invariants`, `npm run lint`, `npm run build`, and `npm run smoke:phase1b-local -- --base-url=https://oze-agent-git-feat-web-phase-0c-maanbrds-projects.vercel.app` passed after the Claude review follow-ups and encoded-redirect smoke fix on 01.05.2026.
- Verification: `npm run smoke:phase1b-local -- --base-url=https://oze-agent-git-feat-web-phase-0c-maanbrds-projects.vercel.app`, `npm run test:invariants`, `npm run lint`, and `npm run build` passed after end-to-end onboarding completion on 01.05.2026.
- Vercel preview with latest deployed code/env smoke state: `https://oze-agent-azmdfbu7i-maanbrds-projects.vercel.app`; staging alias points there as of 01.05.2026.
- UX follow-up on 01.05.2026: Telegram completion now explicitly shows `Rejestracja ukończona`, auto-returns to `/dashboard?onboarding=complete`, and dashboard shows the completed account/payment/Google/Telegram banner.
- Claude Code read-only review of the Telegram completion UX slice returned no blockers on 01.05.2026; one copy-alignment follow-up was implemented.
- Verification: `npm run test:invariants`, `npm run lint`, and `npm run build` passed after the Telegram completion UX fix on 01.05.2026.
- Vercel preview with Telegram completion UX fix: `https://oze-agent-5skafwfy9-maanbrds-projects.vercel.app`; staging alias points there as of 01.05.2026.
- Browser Use verification on staging alias on 01.05.2026: logged-in completed account sees `Rejestracja ukończona` on `/onboarding/telegram`, then lands on `/dashboard?onboarding=complete` with the completion banner.
- Verification: `npm run smoke:phase1b-local -- --base-url=https://oze-agent-git-feat-web-phase-0c-maanbrds-projects.vercel.app` passed after alias update to the Telegram completion UX preview on 01.05.2026.
- Browser Use verification on staging alias on 01.05.2026: completed account `phase1b+1777628027119@agent-oze.test` loaded `/dashboard`, `/klienci`, `/kalendarz`, `/platnosci`, and `/ustawienia`; no login redirect, no demo fallback, no CRM mutation forms, and billing status showed `active` / `monthly` / `opłacona`.
- Verification: `PYTHONPATH=. .venv/bin/python scripts/validate_phase1b_smoke_report.py --report ../docs/phase1b-smoke-report-20260429-1455.md` passed after filling completed onboarding evidence on 01.05.2026.
- Readiness validator hardening on 01.05.2026: the validator now rejects missing invoice evidence and required items described as absent from staging.
- Current validation status on 01.05.2026: `PYTHONPATH=. .venv/bin/python scripts/validate_phase1b_smoke_report.py --report ../docs/phase1b-smoke-report-20260429-1455.md` fails until Stripe invoice evidence is filled.
- Supabase staging migration apply on 01.05.2026: Management API migration returned `HTTP 200`; follow-up SQL verification returned no `PUBLIC`/`anon`/`authenticated` execute privilege rows for `public.handle_new_auth_user()`.
- Fixed in Railway staging on 01.05.2026: FastAPI billing invoice handler now resolves Stripe 2026 invoice payloads where subscription/user metadata live under `parent.subscription_details`; replayed `evt_1TSEv5FzlMN5xVVkl1gVFbmH` returned Railway HTTP 200 and produced invoice `payment_history` + `billing_invoice_paid` outbox evidence.
- Cleanup required: n/a
