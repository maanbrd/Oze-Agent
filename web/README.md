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
