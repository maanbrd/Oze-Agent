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
```

Adresy:

- `http://localhost:3000` — cinematic landing
- `http://localhost:3000/healthz` — healthcheck JSON
- `http://localhost:3000/rejestracja` — rejestracja Supabase Auth
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

Landing używa animacji Midjourney dostarczonej przez usera:
`public/media/hero-bg.mp4`. Pliki medialne trzymaj w `public/media/`.

## Development Notes

Przy pracy z Next.js 16, Tailwind v4, shadcn/ui i Supabase SSR używaj Context7
do aktualnych docs. Next 16 ma breaking changes względem starszej wiedzy modeli.
