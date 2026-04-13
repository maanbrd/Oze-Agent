# OZE-Agent — Multi-Agent Workflow

_Last updated: 13.04.2026_

---

## Roles

### Spec Guardian

**Responsible for:**
- Consistency of `SOURCE_OF_TRUTH.md`
- Consistency of `INTENCJE_MVP.md`
- Consistency of `agent_system_prompt.md`
- Separating MVP scope from product vision

**Does NOT:** Edit Python code. Make architecture decisions. Implement features.

---

### Architect

**Responsible for:**
- `ARCHITECTURE.md`
- Module boundaries and responsibilities
- Decisions: what to reuse, what to rewrite
- Technical risk identification

**Does NOT:** Change product decisions. Edit spec documents. Implement features without plan approval.

---

### Builder

**Responsible for:**
- Implementing the approved plan from `IMPLEMENTATION_PLAN.md`
- Small, controlled changes per phase
- No off-plan features

**Does NOT:** Change SSOT documents without Maan's approval. Skip phases. Add features not in the current phase.

---

### Tester

**Responsible for:**
- `TEST_PLAN_CURRENT.md`
- Manual Telegram tests
- Regression testing
- Reporting drift between code and `.md` specs

**Does NOT:** Fix bugs directly. Change specs. Skip test scenarios.

---

### Reviewer / Auditor

**Responsible for:**
- Reviewing diffs before commit
- Checking R1 compliance (no writes without confirmation)
- Checking that old patterns don't return (`[Tak][Nie]` as mutation confirm, etc.)
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
