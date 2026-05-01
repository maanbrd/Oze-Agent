# OZE-Agent — Multi-Agent Workflow

_Last updated: 29.04.2026_

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

## Superpowers Workflow Overlay

For implementation work in this repo, use the repo-local `superpowers/` skills
in addition to the role sequence above.

Required gates for multi-phase work:

1. `using-superpowers`
2. `brainstorming`
3. written design/spec in `docs/superpowers/specs/`
4. `writing-plans` with checklist plan in `docs/superpowers/plans/`
5. `using-git-worktrees` for an isolated implementation worktree when the
   current worktree has user-owned changes or the plan is multi-phase
6. `test-driven-development` or static invariants before production changes
7. `executing-plans` / `subagent-driven-development` only when tasks are safely
   separable
8. `verification-before-completion`
9. intentional development commit and push/PR update

Current web example: `feat/web-phase-0c` / PR #5 implemented Phase
0C/0D/0E/0F/Phase 1 in isolated worktree
`/Users/mansoniasty/workflows/Agent-OZE-phase0c`, with RED/GREEN tests and web
invariants before commits.

---

## Maan Approves

- Product decisions
- Changes to SSOT hierarchy
- Removal of large code sections
- Starting rewrite of a major module
- Moving to the next implementation phase
- Marking a web phase live-ready after code complete; Phase 1B rollout/smoke
  evidence is required first

No agent role proceeds past a phase boundary without Maan's explicit go.

---

## Communication Rules

- Each role reports findings, not opinions
- Findings reference specific file:line or document:section
- "I think" is replaced by "spec says X, code does Y"
- Ambiguities are escalated to Maan, not resolved silently
