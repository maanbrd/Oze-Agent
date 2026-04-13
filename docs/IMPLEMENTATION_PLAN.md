# OZE-Agent — Implementation Plan

_Last updated: 13.04.2026_

---

## Phase 0 — Documentation Cleanup

**Goal:** Clean, current documentation as the foundation for rewrite.

**Input:** Existing `docs/` files, old patch-track history.

**Output:**
- `SOURCE_OF_TRUTH.md` — clean project map
- `CURRENT_STATUS.md` — current state board
- `CLAUDE.md` — updated for selective rewrite
- `ARCHITECTURE.md` — module structure and boundaries
- `IMPLEMENTATION_PLAN.md` — this file
- `TEST_PLAN_CURRENT.md` — test plan for new version
- `AGENT_WORKFLOW.md` — multi-agent roles

**Done when:** All active docs are synchronized. No stale references to old patch-track.

**Do NOT:** Touch Python code. Delete archive files. Create new features.

---

## Phase 1 — Infrastructure Audit

**Goal:** Verify which wrappers can be reused as-is.

**Input:** Current `shared/` code, Google API documentation.

**Output:** Audit report per wrapper: reuse / minor fix / rewrite.

**Wrappers to audit:**
- `shared/google_sheets.py` — CRUD, search, headers
- `shared/google_calendar.py` — events CRUD, conflict check
- `shared/google_drive.py` — folder create, photo upload
- `shared/database.py` — Supabase: users, pending, history
- `shared/claude_ai.py` — LLM calls (keep calls, rewrite prompts)
- `shared/google_auth.py` — OAuth flow
- `bot/main.py` — Telegram handler registration

**Done when:** Each wrapper has a verdict: keep / fix / rewrite.

**Do NOT:** Rewrite wrappers. Change behavior logic. Add new features.

---

## Phase 2 — New Behavior Contracts

**Goal:** Ensure spec documents are internally consistent and reflect current decisions.

**Input:** `INTENCJE_MVP.md`, `agent_system_prompt.md`, `agent_behavior_spec_v5.md`.

**Output:** Synchronized specs. Tagged TODOs for any remaining ambiguities.

**Key syncs:**
- Dual-write rules (Sheets + Calendar)
- Duplicate resolution flow (`[Nowy]` / `[Aktualizuj]` vs default-merge)
- Button policies (when 3-button, when 2-button, when binary choice)
- show_client display rules (all filled fields except photos)
- Calendar ↔ Sheets sync (reschedule updates `Data następnego kroku`)

**Done when:** No contradictions between the three spec files.

**Do NOT:** Write Python. Change architecture. Implement features.

---

## Phase 3 — Intent Router Rewrite

**Goal:** Clean intent classifier with structured output.

**Input:** `INTENCJE_MVP.md` (6 intents), `agent_system_prompt.md` (examples).

**Output:** New `shared/intent/` module. Replaces `classify_intent` in `claude_ai.py`.

**Done when:** Router correctly classifies all 6 MVP intents + `general_question` with structured JSON output. Manual test pass.

**Do NOT:** Touch pending flow. Touch mutation pipeline. Add POST-MVP intents.

---

## Phase 4 — Pending Flow + Confirmation Cards

**Goal:** Clean state machine for pending flows. Clean card builders.

**Input:** `INTENCJE_MVP.md` (section 5), `agent_behavior_spec_v5.md` (R1, R3).

**Output:**
- `shared/pending/` — state machine: create, route, cancel, confirm
- `shared/cards/` — card builders: mutation card, read-only card, disambiguation, duplicate resolution

**Done when:** All 4 pending routes work (auto-cancel, Dopisać, auto-doklejanie, compound fusion). Cards render correctly.

**Do NOT:** Touch mutation pipeline internals. Add new card types. Implement voice/photo.

---

## Phase 5 — Mutation Pipeline

**Goal:** Atomic Sheets → Calendar → response pipeline with error handling.

**Input:** `INTENCJE_MVP.md` (sections 4.1–4.6), `ARCHITECTURE.md`.

**Output:**
- `shared/mutations/` — pipeline per intent
- `shared/clients/` — client CRUD with duplicate detection

**Done when:** All 6 intents commit correctly. Dual-write (Sheets + Calendar) works. Error messages are Polish and user-friendly.

**Do NOT:** Touch voice/photo. Add POST-MVP intents. Change card format.

---

## Phase 6 — Voice / Photo Flow

**Goal:** Voice transcription and photo upload flows.

**Input:** Current `bot/handlers/voice.py`, `bot/handlers/photo.py`, `INTENCJE_MVP.md`.

**Output:** Clean voice → text → intent pipeline. Clean photo → Drive → Sheets link pipeline.

**Done when:** Voice messages correctly route through intent classifier. Photos upload to Drive and link in Sheets.

**Do NOT:** Add proactive features. Change intent router. Modify mutation pipeline.

---

## Phase 7 — Proactive Scheduler / Morning Brief

**Goal:** Morning brief, meeting reminders, follow-up nudges.

**Input:** `agent_behavior_spec_v5.md` (proactive rules), `INTENCJE_MVP.md`.

**Output:** Clean scheduler with dedup. Morning brief formatter.

**Done when:** Morning brief sends at configured time. Reminders fire before meetings.

**Do NOT:** Add new intent types. Change core mutation flow.

---

## Phase 8 — Full Test Pass

**Goal:** Complete test coverage against `TEST_PLAN_CURRENT.md`.

**Input:** All previous phases, `TEST_PLAN_CURRENT.md`.

**Output:** Test report. Bug list (if any). Confidence level for beta.

**Done when:** All test scenarios pass. No regressions from previous phases.

**Do NOT:** Add features. Change specs. Rush to deploy.
