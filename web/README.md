# Agent-OZE Web App

Panel webowy dla Agent-OZE. Web app jest osobnym Next.js appem w monorepo,
deployowanym docelowo na Vercel z root directory `web/`.

Phase 0A zawiera:

- Next.js 16 App Router
- TypeScript
- Tailwind CSS v4
- ESLint
- cinematic landing page po polsku
- statyczne placeholder routes: `/rejestracja`, `/login`, `/regulamin`,
  `/polityka-prywatnosci`
- `/healthz` jako JSON healthcheck

Phase 0B dodaje:

- Supabase SSR Auth przez `@supabase/ssr`
- realne formularze `/login` i `/rejestracja`
- chroniony `/dashboard`
- odświeżanie sesji w `proxy.ts`
- migrację `users.auth_user_id` + trigger profilu + RLS baseline

Phase 0C dodaje:

- onboarding step 1-2: rejestracja + płatność
- Stripe Checkout sandbox (aktywacja + plan miesięczny/roczny)
- webhook Stripe w Next.js z weryfikacją podpisu
- trwały zapis billing state przez FastAPI internal endpoint

## Getting Started

Uruchom lokalnie:

```bash
cd web
npm install
npm run dev
```

Wymagane env dla auth:

```bash
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000
FASTAPI_INTERNAL_BASE_URL=http://localhost:8000
BILLING_INTERNAL_SECRET=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PRICE_ACTIVATION=agent_oze_activation_199
STRIPE_PRICE_MONTHLY=agent_oze_monthly_49
STRIPE_PRICE_YEARLY=agent_oze_yearly_350
```

Stripe price env vars can be either direct `price_...` IDs or stable lookup
keys. Prefer lookup keys for editable pricing: create a new Price in Stripe,
move the same lookup key to the new active Price, and the app will pick it up
without a code change.

Stripe rollout is gated by the canonical checklist in
`../docs/STRIPE_PHASE_0C_ROLLOUT.md`. Do not treat `npm run build` as enough for
billing readiness; sandbox Checkout, webhook delivery, FastAPI writes, and DB
idempotency must be smoked before Phase 0C is marked live.

Adresy:

- `http://localhost:3000` — cinematic landing
- `http://localhost:3000/healthz` — healthcheck JSON
- `http://localhost:3000/rejestracja` — rejestracja Supabase Auth
- `http://localhost:3000/onboarding/platnosc` — wybór planu i Stripe Checkout
- `http://localhost:3000/login` — logowanie Supabase Auth
- `http://localhost:3000/dashboard` — chroniony panel startowy

## Scripts

```bash
npm run lint
npm run build
```

`npm run build` używa webpacka, bo Turbopack w Next.js 16 potrafi panikować w
ograniczonych środowiskach lokalnych przy transformacji CSS. Do świadomego testu
Turbopacka służy `npm run build:turbo`.

## Scope

Web używa Supabase tylko do Auth/session cookies przez publishable/anon key.
Dane biznesowe i Google API mają iść przez FastAPI. Bot w `../oze-agent/`
pozostaje osobnym procesem.

Vercel nie dostaje `SUPABASE_SERVICE_KEY`. Stripe webhook po weryfikacji
podpisu wywołuje FastAPI `/internal/billing/stripe-event` z HMAC
`BILLING_INTERNAL_SECRET`; dopiero FastAPI zapisuje `users`, `payment_history`,
`webhook_log` i `billing_outbox`.

Current hosted Checkout is server-side, so no `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`
is required in Phase 0C. Add it later only for Stripe Elements, Billing Portal,
or client-side Stripe JS.

Landing używa animacji Midjourney dostarczonej przez usera:
`public/media/hero-bg.mp4`. Pliki medialne trzymaj w `public/media/`.

## Development Notes

Przy pracy z Next.js 16, Tailwind v4, shadcn/ui i Supabase SSR używaj Context7
do aktualnych docs. Next 16 ma breaking changes względem starszej wiedzy modeli.
