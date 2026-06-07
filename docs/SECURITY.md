# Security — Agent-OZE

Runbook for the security hardening done against the *"Bezpieczeństwo SaaS na
Cloudflare: Top 10"* audit. Our stack is **Vercel** (web, `agent-oze.pl`) +
**Railway** (FastAPI + Telegram bot) + **Supabase** — **no Cloudflare** — so the
10 Cloudflare mechanisms were mapped onto our real stack. This file is the
operator checklist for the parts that are **not** code (DNS/registrar, env vars,
staged rollouts) plus the accepted-risk decisions.

## Status of the 10 audit mechanisms

| # | Mechanism | Decision |
|---|-----------|----------|
| 1 | Origin isolation (CF Tunnel) | N/A — Railway/Vercel manage the origin |
| 2 | Positive API schema | ✅ Pydantic models on onboarding routes + 1 MB/6 MB body cap |
| 3 | Rate limiting | ⚖️ **Accepted risk** — no per-user cap (see below) |
| 4 | WAF + SQLi defense | ✅ App-layer only (Supabase SDK, parameterized); no WAF (no CF) |
| 5 | Bot / credential stuffing | Supabase Auth throttle; small paid audience — no extra work |
| 6 | Zero Trust admin | Email allowlist (1 owner) + tightened CORS allowlists |
| 7 | DLP/SWG/CASB | N/A — enterprise endpoint security, out of scope |
| 8 | HTTP security headers + HSTS | ✅ Shipped (CSP Report-Only → enforce; HSTS staged) |
| 9 | DNSSEC | ⏳ **Operator action** at the DNS provider (below) |
| 10 | Multi-tenant isolation | ✅ RLS deny-all defense-in-depth migration |

---

## Deploy actions required (do these when shipping)

### 1. Telegram webhook secret (Item 2) — **required before next bot deploy**
The bot now refuses to start in webhook mode without a secret (fail-closed).
- Generate: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- Set `TELEGRAM_WEBHOOK_SECRET` on Railway (bot service) to that value.
- `run_webhook` registers the webhook with the token and validates the
  `X-Telegram-Bot-Api-Secret-Token` header on every update, so forged posts to
  `…/webhooks/telegram` are rejected.

### 2. Web security headers rollout (Item 8) — **staged, do not skip Report-Only**
Controlled by env vars on Vercel (web project). Defaults are safe (Report-Only,
1-day HSTS), so a deploy with no new vars already adds the static headers.
1. **Deploy as-is.** CSP goes out as `Content-Security-Policy-Report-Only`.
2. Open a preview/prod page, watch the browser console + (optionally) a report
   endpoint for CSP violations. Tune `lib/security-headers.mjs` until clean.
3. Set `CSP_ENFORCE=true` to switch to the enforcing `Content-Security-Policy`.
4. Raise HSTS gradually: `HSTS_MAX_AGE=15552000` (180d) →
   `HSTS_INCLUDE_SUBDOMAINS=true` (only when every `agent-oze.pl` subdomain is
   HTTPS) → `HSTS_PRELOAD=true`, then submit at https://hstspreload.org.
   ⚠️ `preload` is hard to undo — do it last, after weeks of stable HSTS.
- Verify externally on https://securityheaders.com against the preview URL.

### 3. RLS defense-in-depth migration (Item 10) — **staging first**
File: `oze-agent/supabase_migrations/20260607_rls_defense_in_depth.sql`.
- Apply to **staging** Supabase first. Confirm: backend (service_role) reads/
  writes still work, and the anon/publishable key cannot `select` the sensitive
  tables. `service_role` has `BYPASSRLS`, so the backend is unaffected.
- Then apply to production. `tests/test_rls_defense_in_depth.py` (guardrail G4)
  keeps the deny-all complete as the schema evolves.

---

## Accepted risks

### Rate limiting on expensive ops (Item 3) — **no code, by decision**
The audit flagged unbounded expensive operations (Whisper STT, offer-PDF, Claude
calls). On 2026-06-07 the owner chose **not** to add rate limiting, because:
- The per-user daily cap was deliberately removed on 2026-04-25 (a paying
  salesperson must never be blocked mid-work) — see
  `bot/utils/telegram_helpers.py` (`DAILY_LIMIT = 99999`).
- A **paid Stripe subscription is the abuse boundary**: only active subscribers
  can use the bot, which bounds cost/abuse to known, billed users.
- Audience is small (low tens of users), so runaway-cost risk is low.

**Revisit if**: the bot opens to a free tier, audience grows materially, or a
single account is seen burning disproportionate OpenAI/Anthropic spend. At that
point prefer FastAPI-side, fail-open, generous per-user/day caps on the HTTP
expensive endpoints (test-PDF, resource creation) rather than a bot-side refusal.

---

## Secret hygiene (Item 8 / guardrail G7)

No committed secrets were found — `.env*.local` are gitignored
(`web/.gitignore`) and never entered git history (verified). So **no rotation is
required**; this is not a `docs/SECRETS_AUDIT.md` incident.

Local hygiene recommendation:
- `web/.env.production.local` should **not** sit on disk populated with prod-ish
  keys (CLAUDE.md: "Nie twórz `.env` ze skopiowanymi prod kluczami").
- Pull on demand instead: `npm run env:pull` (`web/scripts/pull-vercel-env-safe.mjs`)
  and delete the file after use; keep production secrets only in Vercel/Railway.
- If a secret is ever exposed: rotate it and log the event in
  `docs/SECRETS_AUDIT.md` (G7).

---

## DNS / domain hardening (Item 9) — operator actions at the DNS provider

`agent-oze.pl` is the production domain (homepage, Stripe webhook, Google-
verified). These are registrar/DNS-console steps, not code:

- **DNSSEC**: enable signing for `agent-oze.pl` at the DNS provider; publish the
  resulting DS record at the registrar. Verify with
  `dig +dnssec agent-oze.pl` / https://dnssec-analyzer.verisignlabs.com.
- **CAA records**: restrict who may issue certs. Allow the platform CAs:
  - `0 issue "letsencrypt.org"`  (Vercel / Railway certs)
  - `0 issue "pki.goog"`         (Google Trust Services, used by some platforms)
  - `0 iodef "mailto:<owner-email>"`  (issuance-problem reports)
  Confirm Vercel's current ACME CA before locking CAA, or issuance can break.
- **HSTS preload**: only after step 2 above is enforced and stable in prod.

---

## What's already solid (no action)

- **SQLi (#4)**: all DB access via the Supabase SDK (parameterized); no raw SQL
  string-building, no shell-command construction from user input.
- **Stripe webhook (#5/billing)**: HMAC signature + timestamp window + idempotent
  outbox (`oze-agent/api/routes/billing.py`).
- **Token encryption**: Google OAuth tokens encrypted at rest with Fernet
  (`oze-agent/shared/encryption.py`). Key rotation remains future work (Phase 3).
- **Logging**: PII is hashed (`id_hash`); tokens/secrets are never logged.
- **Auth**: Supabase JWT validation with JWKS + HS256 fallback
  (`oze-agent/api/auth.py`).
