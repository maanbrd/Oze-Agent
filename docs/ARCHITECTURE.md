# OZE-Agent — Architecture

_Last updated: 13.04.2026_

---

## Current State

The current Python behavior layer is **legacy/reference**. We do not trust it as the behavior contract. We can recover stable fragments from it, but the rewrite starts from the `.md` specs.

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

## What Gets Rewritten

| Component | Current Location | Problem |
|-----------|-----------------|---------|
| Intent router | `shared/claude_ai.py` (classify_intent) | Prompt-based, fragile examples, no structured output |
| Pending flow | `shared/database.py` + `bot/handlers/text.py` | State machine scattered across 1700-line handler file |
| Confirmation cards | `bot/utils/telegram_helpers.py` + inline in handlers | Card building mixed with business logic |
| Mutation pipeline | Inline in `handle_confirm` | Sheets/Calendar writes interleaved with Telegram responses |
| Prompt layer | Hardcoded in `shared/claude_ai.py` | System prompts as string literals, not configurable |
| Voice flow | `bot/handlers/voice.py` | Whisper → text → re-route, fragile |
| Photo flow | `bot/handlers/photo.py` | Drive upload, not fully tested |
| Proactive scheduler | `bot/scheduler.py` | Morning brief, reminders — in-memory dedup, fragile |

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
