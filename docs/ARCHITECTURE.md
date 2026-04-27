# OZE-Agent — Architecture

_Last updated: 14.04.2026_

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
| R6 conversation memory | `shared/conversation_format.py`, `shared/active_client.py`, `bot/utils/conversation_reply.py` | Live since 27.04.2026 — 10 messages / 30 min rolling history, assistant replies persisted from handler wrappers, active client derive'owany just-in-time |

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
