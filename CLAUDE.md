# Current Project: OZE-Agent

AI-powered sales assistant for B2C renewable energy salespeople in Poland. Telegram bot + FastAPI backend.

Current project owner: Maan  
User-facing language: Polish  
Code/comments language: English

---

## Current Strategy

The previous bug-by-bug patching track is closed.

Current strategy:

**Selective rewrite of the behavior layer.**

The strongest part of this project is the documentation in `docs/`.
The current Python behavior layer is useful as reference, but not trusted as the final behavior contract.

### Keep where stable

- Google Sheets wrapper
- Google Calendar wrapper
- Google Drive wrapper
- Supabase / database wrapper
- OpenAI wrapper
- auth / config
- basic Telegram plumbing

### Rewrite or redesign

- intent routing
- pending flow
- confirmation cards
- prompts
- voice flow
- photo flow
- proactive scheduler / morning brief
- agent decision layer

Do not delete large parts of the codebase without explicit approval from Maan.

---

## Read First

At the start of every session, read:

1. `docs/SOURCE_OF_TRUTH.md`
2. `docs/CURRENT_STATUS.md`

Then read task-specific docs:

- Intent logic / Sheets schema / mutation contracts:
  - `docs/INTENCJE_MVP.md`

- Bot tone / response format / prompt behavior:
  - `docs/agent_system_prompt.md`

- Behavioral rules / acceptance tests:
  - `docs/agent_behavior_spec_v5.md`

- Product vision / UX direction:
  - `docs/poznaj_swojego_agenta_v5_FINAL.md`

Do not start from `docs/archive/`.

Files in `docs/archive/` are historical artifacts, not current instructions.

---

## Source of Truth

If documents conflict, follow the hierarchy in:

`docs/SOURCE_OF_TRUTH.md`

Do not resolve product contradictions silently in code.

If the conflict affects implementation behavior, stop and report it to Maan before coding.

---

## Non-Negotiable Product Rules

### R1 — Confirmation before write

The agent must never write to Google Sheets, Calendar, or Drive without explicit user confirmation.

Mutation cards use:

- `✅ Zapisać`
- `➕ Dopisać`
- `❌ Anulować`

`❌ Anulować` is one-click cancel.

`change_status` cards use 2 buttons only: `✅ Zapisać` + `❌ Anulować` (no Dopisać).

`[Nowy]` / `[Aktualizuj]` is allowed for duplicate resolution (routing decision, not mutation confirmation).

`[Tak]` / `[Nie]` is allowed for simple binary questions, but NEVER as mutation confirmation.

`[Zapisz bez]` is retired.

### Data ownership

CRM data lives in Google:

- Sheets
- Calendar
- Drive

System data lives in Supabase:

- users
- auth
- config
- pending state
- conversation history
- technical metadata

Never store CRM source-of-truth data in Supabase.

### User-facing behavior

All user-facing bot messages must be in Polish.

The agent should sound like a concise Polish sales assistant, not a generic chatbot.

Avoid meta phrases such as:

- `Oto...`
- `Przygotowałem...`
- `Daj znać...`
- `Czy mogę jeszcze w czymś pomóc?`

### Client identity

Client identity should use:

- first name
- last name
- city, when available

Never rely on last name alone.

### Dates

User-facing dates must use:

`DD.MM.YYYY (Dzień tygodnia)`

Never expose raw ISO dates, Excel serials, row numbers, internal IDs, or technical metadata to the user.

---

## Working Rules

Before changing code:

1. Read the relevant docs.
2. Inspect the existing implementation.
3. Identify whether the task is:
   - infrastructure fix
   - behavior-layer rewrite
   - documentation cleanup
   - test/update only
4. Keep edits scoped.
5. Do not change unrelated files.
6. Do not touch archive files unless explicitly asked.
7. Do not create new architecture without checking `SOURCE_OF_TRUTH.md`.

If Maan asks for analysis or audit only, do not edit files.

If Maan asks for a proposal, provide the proposed content first and wait for approval.

If Maan asks to implement, implement and verify.

---

## Testing

For code changes, use tests appropriate to the scope:

- unit tests for pure logic
- integration tests for wrappers / handlers where available
- manual Telegram test plan for user-facing behavior

If tests cannot be run locally, explain why and provide exact manual test steps.

Do not claim behavior works unless it was tested or the limitation is clearly stated.

---

## Repository Map

- `bot/` — Telegram bot handlers and user interaction
- `api/` — FastAPI backend
- `shared/` — shared business logic, wrappers, services
- `tests/` — automated tests
- `docs/` — active project documentation
- `docs/archive/` — historical documents only

Business logic should live in `shared/` where possible.
Bot and API layers should call shared logic instead of duplicating it.

---

## Documentation Rules

Keep active documentation short and current.

Do not add long historical logs to active docs.
Historical reports, old plans, old audits, and obsolete session briefs belong in `docs/archive/`.

Active docs have these roles:

- `SOURCE_OF_TRUTH.md` — hierarchy and strategy
- `CURRENT_STATUS.md` — current state and next step
- `INTENCJE_MVP.md` — current intent contracts
- `agent_system_prompt.md` — runtime response style
- `agent_behavior_spec_v5.md` — behavior rules and acceptance tests
- `poznaj_swojego_agenta_v5_FINAL.md` — product vision, not runtime contract

---

## What Not To Do

Do not:

- use archived docs as implementation instructions
- continue the old patch-track unless Maan explicitly reopens it
- implement POST-MVP features accidentally
- add new product behavior just because it seems useful
- silently resolve product contradictions in code
- commit changes unless Maan explicitly asks for commits
- rewrite stable wrappers without a clear reason
- expose technical internals to the Telegram user

---

## Current Next Step

Follow `docs/CURRENT_STATUS.md`.

At the current stage, the expected direction is:

1. clean active documentation
2. create `ARCHITECTURE.md`
3. create `IMPLEMENTATION_PLAN.md`
4. create `TEST_PLAN_CURRENT.md`
5. then start selective rewrite of the behavior layer
