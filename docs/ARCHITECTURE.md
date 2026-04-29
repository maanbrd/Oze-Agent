# OZE-Agent — Architecture

_Last updated: 29.04.2026_

---

## Current State

Two parallel deployment tracks share Supabase (auth + RLS) and Google APIs:

| Track | Code | Hosting | Role |
|---|---|---|---|
| **Bot** (Telegram + FastAPI) | `oze-agent/` | Railway | The only mutation surface for CRM data (R1: confirm-before-write). Voice + text + future photo. |
| **Web app** (Next.js 16) | `web/` | Vercel — `oze-agent.vercel.app` | Read-only dashboard, billing, onboarding wizard, settings. **No web chat in MVP.** |

The current Python behavior layer is **legacy/reference**. Bot rewrite (selective) starts from the `.md` specs. Web app is greenfield.

### Web app architecture (29.04.2026)

- **Auth**: Supabase Auth via `@supabase/ssr` server actions (`web/lib/supabase/server.ts`). Publishable / anon key only on the client; service key never reaches Next.js (G1).
- **Auth boundary**: Next.js owns sessions. Dashboard / business data goes through FastAPI (`oze-agent/api/`) via `Authorization: Bearer <Supabase JWT>`; FastAPI validates JWT against Supabase JWKS. RLS protects browser access; FastAPI uses service key + per-endpoint authorization on JWT subject.
- **Routes implemented on `feat/web-phase-0c`**: `/` landing, `/rejestracja`, `/login`, `/healthz`, legal pages, `/onboarding/platnosc`, `/onboarding/google`, `/onboarding/google/sukces`, `/onboarding/zasoby`, `/onboarding/telegram`, and logged-in app routes `/dashboard`, `/klienci`, `/kalendarz`, `/platnosci`, `/ustawienia`, `/import`, `/instrukcja`, `/faq`.
- **Email confirmation**: currently OFF in Supabase (Auth → Providers → Email) for MVP. Built-in SMTP free-tier rate limit (~2/h) blocks signup with confirmation on. Custom SMTP (Resend) enabled in Phase 7 per `~/.claude/plans/przeczytaj-oba-pliki-md-twinkling-oasis.md`.
- **Billing boundary (Phase 0C)**: Next.js creates Stripe Checkout Sessions and verifies Stripe webhooks, but never stores `SUPABASE_SERVICE_KEY`. Vercel forwards verified Stripe events to FastAPI `/internal/billing/stripe-event` with HMAC (`BILLING_INTERNAL_SECRET`). FastAPI owns durable billing writes (`users`, `payment_history`, `webhook_log`, `billing_outbox`) and only activates access after paid Stripe events.
- **Onboarding boundary (Phase 0F/1)**: Next.js calls FastAPI `/api/onboarding/*` server-side with the Supabase access token. FastAPI resolves `public.users.auth_user_id`, creates/stores system setup metadata, and owns Google operations. Signed OAuth state prevents trusting a public path `user_id`.
- **CRM dashboard boundary (Phase 1)**: Next.js reads CRM data through `web/lib/crm/adapters.ts`, which targets FastAPI `/api/dashboard/crm`. FastAPI reads Google Sheets and Calendar via existing wrappers and returns DTOs plus `source/sourceMessage`. The frontend exposes `live`, `demo`, and `unavailable` source states. Completed users must not silently receive demo CRM as if it were live.
- **CRM mutation boundary**: the web app has no CRM mutation forms. It may show direct Google Sheets/Calendar/Drive links. CRM edits happen in Google directly or through Telegram confirmation flows.

---

## What Stays

These modules are stable infrastructure. Audit before reuse, but don't rewrite without reason.

| Module | File | Role |
|--------|------|------|
| Google Sheets | `shared/google_sheets.py` | CRUD on client spreadsheet |
| Google Calendar | `shared/google_calendar.py` | Event create/read/update/delete |
| Google Drive | `shared/google_drive.py` | Photo folder management |
| Database | `shared/database.py` | Supabase: users, pending state, conversation history |
| AI / LLM | `shared/claude_ai.py` | Intent classification, data extraction, NLP |
| Auth | `shared/google_auth.py` | OAuth token management |
| Telegram plumbing | `bot/main.py` | Handler registration, webhook/polling setup |

---

## Core rewrite

| Component | Current Location | Problem |
|-----------|-----------------|---------|
| Intent router | `shared/claude_ai.py` (classify_intent) | Prompt-based, fragile examples, no structured output |
| Pending flow | `shared/database.py` + `bot/handlers/text.py` | State machine scattered across 1700-line handler file |
| Confirmation cards | `bot/utils/telegram_helpers.py` + inline in handlers | Card building mixed with business logic |
| Mutation pipeline | Inline in `handle_confirm` | Sheets/Calendar writes interleaved with Telegram responses |
| Prompt layer | Hardcoded in `shared/claude_ai.py` | System prompts as string literals, not configurable |
| Proactive scheduler | `bot/scheduler.py` | Morning brief and evening follow-up — scheduler/dedup fragile. No pre-meeting reminders; those belong to native Google Calendar. |

---

## Active post-MVP slices

| Component | Files | Status |
|-----------|-------|--------|
| Voice transcription | `bot/handlers/voice.py`, `shared/voice_postproc.py`, `shared/whisper_stt.py` | Live since 25.04.2026 — Whisper STT + Polish name post-pass (Claude haiku), 2-button confirm card (Zapisz/Anuluj), transcription flows through normal text path via `handle_text(text_override=...)` |
| Global cancel | `bot/handlers/cancel.py` | Live since 25.04.2026 — universal escape hatch for any pending flow |

---

## Deferred flows

| Component | Current Location | Problem |
|-----------|-----------------|---------|
| Photo flow | `bot/handlers/photo.py` | Drive upload, not fully tested |
| Multi-meeting | Handlers / parser fragments (not centralized) | Batch of several meetings in one message |

Current photo code and any batch/multi-meeting fragments are legacy reference only — not the contract. These flows are POST-MVP roadmap candidates.

---

## Proposed Module Structure

```
shared/
  google/              # Stable wrappers (sheets, calendar, drive, auth)
  clients/             # Client CRUD: search, add, update, duplicate detection
  intent/              # Intent router: classify, extract entities
  pending/             # Pending state machine: create, route, cancel, confirm
  cards/               # Card builders: mutation cards, read-only cards, disambiguation
  mutations/           # Mutation pipeline: Sheets write → Calendar write → response
  prompts/             # System prompts: configurable, versioned
  formatting/          # Output formatting: dates, MarkdownV2, schedule

bot/
  handlers/            # Telegram handlers: thin, delegate to shared/
  utils/               # Telegram helpers: buttons, typing indicators
```

`shared/photo/` is a POST-MVP module candidate, not part of the core first-version behavior layer. Voice work currently lives in `shared/voice_postproc.py` + `shared/whisper_stt.py` + `bot/handlers/voice.py` — could be moved into `shared/voice/` if/when refactor is needed.

---

## Boundary Diagram

```
┌─────────────────────────────────┐
│         Telegram UI             │  bot/handlers/, bot/utils/
│  (receive message, send reply)  │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│      Agent Decision Layer       │  shared/intent/, shared/pending/
│  (classify, route, state mgmt)  │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│    Deterministic Services       │  shared/clients/, shared/mutations/,
│  (CRUD, cards, formatting)      │  shared/cards/, shared/formatting/
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│       Infrastructure            │  shared/google/, shared/database.py
│  (Google APIs, Supabase)        │
└─────────────────────────────────┘
```

### Web Boundary Diagram

```
┌─────────────────────────────────┐
│        Browser / Next UI         │  web/app/, web/components/
│  auth, onboarding, read-only CRM │
└──────────────┬──────────────────┘
               │ Supabase session cookie / access token
               ▼
┌─────────────────────────────────┐
│        Next.js Server            │  web/lib/api/*, server actions
│  Stripe Checkout + webhook verify│
└──────────────┬──────────────────┘
               │ Bearer Supabase JWT / HMAC internal billing
               ▼
┌─────────────────────────────────┐
│          FastAPI                 │  api/routes/*
│  service-role writes + Google ops│
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│ Supabase system data + Google CRM│
│ users/billing/onboarding + Sheets│
│ Calendar/Drive                  │
└─────────────────────────────────┘
```

---

## Design Principles

1. **Business logic in `shared/`** — bot handlers are thin dispatchers
2. **CRM source of truth = Google** (Sheets, Calendar, Drive)
3. **System state = Supabase** (users, auth, pending, history)
4. **No writes without confirmation** (R1 absolute)
5. **Intent router is replaceable** — structured output, not fragile prompt examples
6. **Pending state machine is explicit** — not scattered across a 1700-line file
7. **Cards are built by card builders** — not inline in handlers
8. **Mutations are atomic pipelines** — Sheets → Calendar → response, with error handling
9. **Unified 3-button mutation cards** — all mutation intents (`add_client`, `add_note`, `change_status`, `add_meeting`) use the same pattern: `[✅ Zapisać] [➕ Dopisać] [❌ Anulować]`. `❌ Anulować` is one-click.
10. **Duplicate resolution is explicit** — a first name + last name + city match routes through `[Nowy]` / `[Aktualizuj]` before any mutation card. No default merge.
11. **Web app is read-only for CRM** — account/billing/onboarding mutations are allowed; CRM rows/events/notes/statuses are not mutated from web.
12. **Operational UI states are explicit** — web CRM must label live/demo/unavailable data sources and show direct Google links where edits happen.
