# OZE-Agent — Multi-Agent Workflow

_Last updated: 27.04.2026_

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
- Boundary between core behavior rewrite, deferred flows (photo / multi-meeting), active post-MVP slices (voice transcription — live since 25.04.2026), and stable wrappers vs behavior layer

**Does NOT:** Change product decisions. Edit spec documents. Implement features without plan approval.

---

### Builder

**Responsible for:**
- Implementing the approved plan from `IMPLEMENTATION_PLAN.md`
- Small, controlled changes per phase
- No off-plan features

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

**Does NOT:** Implement. Change specs. Make product decisions.

---

## Workflow Sequence

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
