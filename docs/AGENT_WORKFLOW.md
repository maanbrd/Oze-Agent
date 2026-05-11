# OZE-Agent — Agent Workflow

_Last updated: 04.05.2026_

---

## Current Tracks

### Core Telegram Agent

Primary operational track remains the selective rewrite / stabilization of the
Telegram behavior layer. Agent behavior changes must still follow the docs-first
contract:

`SOURCE_OF_TRUTH.md` → `INTENCJE_MVP.md` → `agent_behavior_spec_v5.md` →
implementation → `TEST_PLAN_CURRENT.md`.

### Offer Generator

The offer generator is now an integrated product slice, not a separate app.

Scope:
- Webapp route: `/oferty`
- Backend API: `oze-agent/api/routes/offers.py`
- Shared business logic: `oze-agent/shared/offers/`
- Telegram send flow: offer list, offer selection, confirmation card, Gmail send,
  Sheets follow-up writes after successful Gmail send
- Supabase system tables: offer templates, seller profile, send attempts

Generator work can touch web, API, shared logic, bot handlers, tests, assets and
Supabase schema in the same slice, but CRM source-of-truth still stays in Google
Sheets / Gmail / Calendar / Drive. Supabase stores only system data and technical
metadata.

Current offer generator commit baseline: `09e0957 feat: add offer generator`.

---

## Roles

### Spec Guardian

**Responsible for:**
- Consistency of `SOURCE_OF_TRUTH.md`
- Consistency of `CURRENT_STATUS.md`
- Consistency of `INTENCJE_MVP.md`
- Consistency of `agent_system_prompt.md`
- Consistency of `agent_behavior_spec_v5.md`
- Separating MVP scope from product vision
- Vision stewardship: `poznaj_swojego_agenta_v5_FINAL.md` stays aligned as Product Vision / UX North Star, not a runtime contract

**Does NOT:** Edit Python code. Make architecture decisions. Implement features.

---

### Architect

**Responsible for:**
- `ARCHITECTURE.md`
- Module boundaries and responsibilities
- Decisions: what to reuse, what to rewrite
- Technical risk identification
- Boundary between core behavior rewrite, deferred flows (multi-meeting), active
  post-MVP slices (voice transcription, photo upload), offer-generator slices,
  and stable wrappers vs behavior layer

**Does NOT:** Change product decisions. Edit spec documents. Implement features without plan approval.

---

### Builder

**Responsible for:**
- Implementing the approved plan from `IMPLEMENTATION_PLAN.md`
- Small, controlled changes per phase
- No off-plan features
- For `/oferty`: matching the existing webapp design exactly, keeping UI
  changes integral to the current app shell, and keeping business logic in
  `shared/offers/` where possible

**Does NOT:** Change SSOT documents without Maan's approval. Skip phases. Add features not in the current phase. Implement POST-MVP or vision-only features without explicit Maan approval — especially `reschedule_meeting`, `cancel_meeting`, `free_slots`, `delete_client`, photo / multi-meeting.

---

### Tester

**Responsible for:**
- `TEST_PLAN_CURRENT.md`
- Manual Telegram tests
- Regression testing
- Reporting drift between code and `.md` specs
- Verifying unified 3-button mutation cards across all mutating intents
- Verifying duplicate resolution via `[Nowy]` / `[Aktualizuj]` (no default-merge)
- Verifying R7 conditional firing per fires / doesn't-fire lists
- Verifying agent does not send pre-meeting reminders
- For offer generator work:
  - backend unit tests in `oze-agent/tests/offers/`
  - web source/UI tests in `web/tests/offer-*.test.mjs`
  - `npm run lint` and `npm run build` in `web/`
  - manual browser check of `http://127.0.0.1:3000/oferty` when UI changes are visible
  - controlled-address Gmail/manual send tests before real customer use

**Does NOT:** Fix bugs directly. Change specs. Skip test scenarios.

---

### Reviewer / Auditor

**Responsible for:**
- Reviewing diffs before commit
- Checking R1 compliance (no writes without confirmation)
- Checking that old patterns don't return, including:
  - `[Tak]` / `[Nie]` used as mutation confirmation
  - default-merge duplicate resolution
  - 2-button `change_status` card
  - agent-side pre-meeting reminders
  - `reschedule_meeting` / `cancel_meeting` / `delete_client` treated as MVP scope
- Verifying alignment with SSOT
- Checking commit scope in a dirty worktree:
  - no `git add .`
  - staged files reviewed by `git diff --cached --name-status`
  - unrelated local changes left untouched unless Maan explicitly asks to include them

**Does NOT:** Implement. Change specs. Make product decisions.

---

## Workflow Sequence — Core Agent

```
Spec → Architecture → Plan → Build → Test → Review
```

Sequential and controlled. No parallel chaos.

1. **Spec Guardian** ensures specs are clean and consistent
2. **Architect** designs module structure and boundaries
3. **Builder** implements the approved phase
4. **Tester** runs test plan against implementation
5. **Reviewer** checks diffs and compliance

If a test fails → Builder fixes → Tester retests → Reviewer re-reviews.

If a spec contradiction is found → Spec Guardian resolves → workflow restarts from affected phase.

---

## Workflow Sequence — Offer Generator

```
Product plan → Data/API contract → Shared logic → Web UI → Telegram send flow → Tests → Review → Commit scope
```

1. Confirm product rules before coding:
   - webapp creates and previews templates only
   - Telegram/Gmail performs real customer send
   - one send command targets one customer
   - no customer PDF archive in MVP
   - seller profile values such as company, logo and email template persist per user
2. Put reusable logic in `oze-agent/shared/offers/`:
   - validation
   - pricing
   - numbering/reorder rules
   - PDF rendering
   - email rendering
   - Gmail MIME construction
   - idempotent send pipeline
3. Keep web UI in `web/components/offers/` and make it visually identical to the existing app:
   - no standalone design language
   - dark app shell consistency
   - no white default panels unless the surrounding app uses them
   - controls should be real working controls, not placeholders
4. API routes stay thin:
   - validate request
   - call repository/shared logic
   - return UI-friendly payload
5. Telegram send flow must preserve R1:
   - show `✅ Wysłać` / `❌ Anulować`
   - no Gmail send before confirmation
   - no Sheets write before Gmail success
   - idempotency key prevents double-send from duplicate callbacks
6. Tests scale with touched surface:
   - pure logic: `pytest tests/offers`
   - Telegram confirmation/send flow: targeted handler/pipeline tests
   - web UI/PDF: `node --test web/tests/offer-*.test.mjs`
   - frontend integrity: `npm run lint`, `npm run build`

If a UI change is requested visually in the browser, prefer a minimal scoped edit,
then re-run the relevant web tests and build. Do not redesign unrelated parts of
the generator.

---

## Commit Workflow

The repository may contain unrelated dirty files. Treat them as user-owned unless
Maan explicitly asks to include them.

Before committing:
- inspect `git status --short`
- stage exact files or exact groups requested by Maan
- inspect `git diff --cached --name-status`
- run verification matching the staged scope
- commit only after verification output is read

If Maan asks to include artifact folders such as `docs/`, `tmp/`, `.agents/`,
`skills-lock.json` or smoke-test reports, include those explicitly and do not
rewrite or normalize them unless asked. These artifacts may fail whitespace checks;
report that fact instead of silently modifying generated files.

---

## Runtime Environments

Production bot:
- Telegram: main OZE-Agent bot
- Railway service: `bot`
- Git branch: `main`
- Current deployed commit after 27.04.2026 hotfix: `961fad1`

Test bot:
- Telegram: `t.me/OZEAgentTestBot`
- Railway service: `bot-test`
- Git branch: `develop`
- Purpose: safe manual testing of agent behavior before promoting changes to production.
- Current deployed commit after 27.04.2026 setup: `961fad1`

Important testing rule:
- `bot-test` uses a separate Telegram token and follows `develop`, but backend integrations may still point to the same Google Sheets / Calendar / Supabase resources as production.
- Use fictional test data unless the environment has been explicitly separated.
- Do not copy Telegram bot tokens into docs, commits, screenshots, or chat logs intended for sharing.

Promotion rule:
- Agent behavior fixes land on `develop` first.
- `bot-test` smoke/regression must pass before promotion.
- Promote to `main` only after Maan confirms the relevant Telegram behavior on `bot-test`.
- Production smoke should be a small subset of the same scenarios after Railway `bot` deploys.

---

## Maan Approves

- Product decisions
- Changes to SSOT hierarchy
- Removal of large code sections
- Starting rewrite of a major module
- Moving to the next implementation phase

No agent role proceeds past a phase boundary without Maan's explicit go.

---

## Communication Rules

- Each role reports findings, not opinions
- Findings reference specific file:line or document:section
- "I think" is replaced by "spec says X, code does Y"
- Ambiguities are escalated to Maan, not resolved silently
