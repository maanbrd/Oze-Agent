# Agent-OZE Web App

Panel webowy dla Agent-OZE. Web app jest osobnym Next.js appem w monorepo,
deployowanym docelowo na Vercel z root directory `web/`.

Aktualny web app zawiera:

- Next.js 16 App Router
- TypeScript
- Tailwind CSS v4
- ESLint
- cinematic landing page po polsku
- statyczne placeholder routes: `/rejestracja`, `/login`, `/regulamin`,
  `/polityka-prywatnosci`
- `/healthz` jako JSON healthcheck
- `/oferty` — generator szablonów ofert PV / magazyn energii / PV + magazyn,
  seller profile, logo, treść emaila, preview i testowy PDF

## Getting Started

Wymagane env dla lokalnego auth/onboardingu:

```bash
cd web
npm run env:pull
```

Nie uruchamiaj bezpośrednio `vercel env pull .env.local`, bo nadpisuje lokalny
plik bez kopii. `npm run env:pull` robi backup aktualnego `web/.env.local` w
`/tmp/agent-oze-env-backups/` i dopiero potem pobiera env z Vercela. Jeśli
potrzebujesz pliku tymczasowego zamiast nadpisania lokalnego env, użyj:

```bash
node scripts/pull-vercel-env-safe.mjs preview /tmp/oze-agent-preview.env
```

Jeśli wpisujesz wartości ręcznie, lokalny `web/.env.local` musi zawierać:

```bash
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=...
FASTAPI_INTERNAL_BASE_URL=...
```

`NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` jest preferowane. Starszy
`NEXT_PUBLIC_SUPABASE_ANON_KEY` działa jako fallback. Po stronie serwera web app
akceptuje też istniejące `SUPABASE_URL` i `SUPABASE_KEY` z preview env.
`web/.env.local` jest gitignored i nie wolno go commitować.

Płatność wymaga dodatkowo Stripe:

```bash
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...     # wymagane dla webhooka po płatności
STRIPE_PRICE_ACTIVATION=price_...   # albo puste: użyje lookup key agent_oze_activation_199
STRIPE_PRICE_MONTHLY=price_...      # albo puste: użyje lookup key agent_oze_monthly_49
STRIPE_PRICE_YEARLY=price_...       # albo puste: użyje lookup key agent_oze_yearly_350
```

Jeśli ceny nie istnieją w Stripe, utwórz aktywne Prices albo wpisz istniejące
`price_...` do `STRIPE_PRICE_*`.

Jeśli Stripe działał lokalnie i nagle przestał po pullu envów, najpierw sprawdź
backup w `/tmp/agent-oze-env-backups/`. Puste wartości w stylu
`STRIPE_SECRET_KEY=""` i `STRIPE_WEBHOOK_SECRET=""` są traktowane jak brak
aktywnej konfiguracji.

Uruchom lokalnie:

```bash
cd web
npm install
npm run dev
```

Adresy:

- `http://localhost:3000` — cinematic landing
- `http://localhost:3000/healthz` — healthcheck JSON
- `http://localhost:3000/rejestracja` — placeholder onboardingu
- `http://localhost:3000/login` — placeholder logowania
- `http://localhost:3000/oferty` — generator ofert

## Scripts

```bash
npm run lint
npm run build
```

`npm run build` używa webpacka, bo Turbopack w Next.js 16 potrafi panikować w
ograniczonych środowiskach lokalnych przy transformacji CSS. Do świadomego testu
Turbopacka służy `npm run build:turbo`.

## Scope

Generator ofert komunikuje się z backendem FastAPI w `../oze-agent/` dla
szablonów, profilu, logo, zmiennych emaila i testowego PDF. Webapp nie wysyła
ofert do klientów; realna wysyłka idzie przez Telegram + Gmail.

Landing używa animacji Midjourney dostarczonej przez usera:
`public/media/hero-bg.mp4`. Pliki medialne trzymaj w `public/media/`.

## Development Notes

Przy pracy z Next.js 16, Tailwind v4, shadcn/ui i Supabase SSR używaj Context7
do aktualnych docs. Next 16 ma breaking changes względem starszej wiedzy modeli.
