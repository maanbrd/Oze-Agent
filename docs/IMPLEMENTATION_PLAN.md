# OZE-Agent — Implementation Plan

_Last updated: 28.04.2026_

This file owns the **bot track** phasing (selective behavior-layer rewrite). The **web app track** has its own multi-phase plan tracked separately at `~/.claude/plans/przeczytaj-oba-pliki-md-twinkling-oasis.md`; the snapshot below is current as of 28.04.2026.

---

## Web app track snapshot (28.04.2026)

| Phase | Status | Output |
|---|---|---|
| **0A** Web bootstrap (Next.js 16 scaffold, landing, placeholder routes, `/healthz`) | ✅ DONE — PR #1 merged 28.04 | `web/` live on Vercel `oze-agent.vercel.app` |
| **0B** Supabase Auth + RLS baseline | ✅ DONE — PR #2 + #3 merged 28.04 | `/rejestracja` → `auth.users` + `public.users` via `on_auth_user_created` trigger; `/dashboard` reads claims; signup verified live (with email confirmation off — see §config note) |
| **0C** Stripe sandbox + onboarding wizard step 1-2 | 🔧 implementation branch | Stripe Checkout sandbox, verified webhook → FastAPI HMAC boundary, idempotent billing writes + outbox, onboarding steps 1-2 |
| **0D** Railway billing service + Google OAuth + Telegram pairing | ⏳ later | Full 5-step onboarding wizard |
| **1+** | not started | Read-only data layer, dashboard, klienci, kalendarz, płatności, landing polish |

**Config note (28.04.2026):** Supabase Auth → Providers → Email → `Confirm email` is **OFF**. Reason: built-in SMTP free-tier hits `over_email_send_rate_limit` (~2/h) which rolls back signup. Custom SMTP (Resend) is part of Phase 7 of the master plan; until then, signup creates session immediately without confirmation email. Re-enable once Resend SMTP is wired in Supabase project.

---

## Phase 0 — Documentation Cleanup

**Goal:** Clean, current documentation as the foundation for rewrite.

**Input:** Existing `docs/` files, old patch-track history.

**Output — full set of active documents, synchronized per 13-14.04 decisions:**

- `SOURCE_OF_TRUTH.md`
- `CURRENT_STATUS.md`
- `CLAUDE.md`
- `ARCHITECTURE.md`
- `IMPLEMENTATION_PLAN.md` — this file
- `TEST_PLAN_CURRENT.md`
- `AGENT_WORKFLOW.md`
- `INTENCJE_MVP.md`
- `agent_system_prompt.md`
- `agent_behavior_spec_v5.md`
- `poznaj_swojego_agenta_v5_FINAL.md` (Product Vision / UX North Star)

**Done when:** All active docs synchronized with 13-14.04 decisions. No stale references to the old patch-track.

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

Photo/multi-meeting handlers and their current code are legacy reference only — not a blocker for core MVP audit. They will be revisited when deferred flows are scheduled. Voice transcription went live 25.04.2026 (post-Phase 7 slice) — see `CURRENT_STATUS.md`.

---

## Phase 2 — Behavior Contract Freeze

**Goal:** Confirm that behavior contracts are frozen and consistent before writing new Python. This is a verification gate, not a documentation-writing phase.

**Input:** `INTENCJE_MVP.md`, `agent_system_prompt.md`, `agent_behavior_spec_v5.md`, `TEST_PLAN_CURRENT.md`, `ARCHITECTURE.md`.

**Output:** Sign-off that the four spec files are internally consistent and match `ARCHITECTURE.md`. Any remaining ambiguities captured as tagged TODOs with owner.

**Key checks:**

- Unified 3-button mutation cards: `[✅ Zapisać] [➕ Dopisać] [❌ Anulować]`. `❌ Anulować` is one-click.
- `[Tak]` / `[Nie]` only for non-mutation binary questions.
- `[Nowy]` / `[Aktualizuj]` is a routing decision for duplicate resolution only.
- Duplicate resolution via `[Nowy]` / `[Aktualizuj]`, no default-merge.
- Calendar ↔ Sheets sync only for agent-owned mutations (primarily `add_meeting`). Manual reschedule in Google Calendar is not observed by the bot. `reschedule_meeting` is not MVP.
- show_client display rules per `INTENCJE_MVP.md` §5.5 (all filled fields except photos, link, event ID).
- R7 (next_action_prompt) conditional firing per `INTENCJE_MVP.md` §5.1.

**Done when:** No contradictions between the four spec files. Behavior layer can be implemented against a frozen contract.

**Do NOT:** Write Python. Change architecture. Add new features. Introduce POST-MVP intents into MVP scope.

---

## Phase 3 — Intent Router Rewrite

**Goal:** Clean intent classifier with structured output.

**Input:** `INTENCJE_MVP.md` (6 intents), `agent_system_prompt.md` (examples).

**Output:** New `shared/intent/` module. Replaces `classify_intent` in `claude_ai.py`.

**Done when:** Router correctly classifies all 6 MVP intents + `general_question` with structured JSON output. Out-of-MVP requests are distinguished per `SOURCE_OF_TRUTH.md` §4, and the agent replies accordingly without hallucinating or misrouting:

- **POST-MVP roadmap** (e.g. `edit_client`, `multi-meeting`, `photo_upload`, CSV/Excel import, dashboard) → "to feature post-MVP".
- **Vision-only** (e.g. `reschedule_meeting`, `cancel_meeting`, `free_slots`, `delete_client`) → "to poza aktualnym zakresem; wymaga osobnej decyzji".
- **NIEPLANOWANE** (e.g. agent-side pre-meeting reminders) → short refusal with a pointer to the native alternative (e.g. reminders handled by Google Calendar).

Manual test pass.

**Do NOT:** Add POST-MVP or vision-only intents into MVP runtime. Touch pending flow. Touch mutation pipeline.

---

## Phase 4 — Pending Flow + Confirmation Cards

**Goal:** Clean state machine for pending flows. Clean card builders.

**Input:** `INTENCJE_MVP.md` (section 5), `agent_behavior_spec_v5.md` (R1, R3).

**Output:**
- `shared/pending/` — state machine: create, route, cancel, confirm. Auto-cancel on unrelated input + re-route as a new input.
- `shared/cards/` — card builders:
  - mutation cards (unified 3-button: `[✅ Zapisać] [➕ Dopisać] [❌ Anulować]`)
  - read-only cards (no buttons)
  - disambiguation lists
  - duplicate resolution (`[Nowy]` / `[Aktualizuj]`, no default-merge)
  - conflict cards — same unified 3-button pattern as other mutations

**Done when:**
- Unified 3-button works across all mutation intents.
- `❌ Anulować` is one-click (no "Na pewno?" loop).
- Duplicate resolution always asks `[Nowy]` / `[Aktualizuj]` explicitly.
- All 4 pending routes (auto-cancel, Dopisać, auto-doklejanie, compound fusion) work.
- Cards render correctly.

**Do NOT:** Touch mutation pipeline internals. Add new card types. Implement photo.

---

## Phase 5 — Mutation Pipeline

**Goal:** Atomic Sheets → Calendar → response pipelines with error handling, with a clear split between mutating and read-only intents.

**Input:** `INTENCJE_MVP.md` (sections 4.1–4.6), `ARCHITECTURE.md`.

**Output:**
- `shared/mutations/` — pipeline per mutating intent (`add_client`, `add_note`, `change_status`, `add_meeting`)
- `shared/clients/` — client CRUD with duplicate detection; also serves read-only `show_client`
- Read-only handlers for `show_client` and `show_day_plan` reuse existing modules (`shared/clients/`, `shared/cards/`, `shared/formatting/`) — no new module

**Done when:**
- All mutating MVP intents commit correctly.
- Read-only intents return correctly formatted results (no writes, no buttons).
- Sheets/Calendar writes follow `INTENCJE_MVP.md` §4:
  - `add_meeting` creates a Calendar event.
  - `add_client` creates a Calendar event only if the user provides a follow-up / next-action that maps to a scheduled item; otherwise no Calendar event.
  - A plain `add_note` with no time component does not create a Calendar event.
  - `change_status` triggers R7 (next_action_prompt); it does not create a status event in Calendar.
- R1 enforced: no writes before confirmation.
- Error messages in Polish, user-friendly.

**Do NOT:** Touch photo. Add POST-MVP intents. Change card format.

---

## Phase 6 — Proactive Scheduler / Morning Brief

**Goal:** Morning brief at 07:00 Europe/Warsaw, Monday–Friday, with deduplication.

**Input:** `agent_behavior_spec_v5.md` (proactive rules), `INTENCJE_MVP.md` §4.6 (show_day_plan format).

**Output:**
- `shared/proactive/morning_brief.py` — scheduler entry, eligibility filter, dedup, per-user error isolation.
- `bot/scheduler/morning_brief_job.py` — PTB `JobQueue.run_daily` wrapper (07:00 Warsaw, weekdays).
- `format_morning_brief_short` in `shared/formatting.py` — deterministic, MDV2-escaped, `Akcja: Klient` template.
- Dedup column `users.last_morning_brief_sent_date` (migration in `supabase_schema.sql`).

**Done when:**
- Morning brief sends at 07:00 Europe/Warsaw, Mon–Fri, to every eligible user.
- Content: Terminarz (Calendar events) + "Do dopilnowania dziś" (Sheets K/L ≤ today, non-terminal status).
- Empty state: `Terminarz:\nNa dziś nie masz spotkań.` — brief is always sent on weekdays.
- Dedup prevents double-send on the same Warsaw date; send failure does NOT bump the dedup column (retry next weekday).
- Per-user exceptions are isolated.

**Do NOT (out of MVP):**
- Evening follow-up (post-meeting check-in via `pending_followups`) — POST-MVP roadmap.
- Pipeline stats, free slots, attendee lists — explicitly excluded from the brief.
- Per-user custom brief time (`users.morning_brief_hour` stays untouched; MVP hardcodes 07:00) — POST-MVP.
- Per-user timezone (D9; MVP hardcodes Europe/Warsaw) — POST-MVP.
- Pre-meeting reminders — NIEPLANOWANE (Google Calendar native).
- Polish declension in brief lines — POST-MVP "polish pass"; MVP uses nominative.

---

---

## Phase 7 — Full Test Pass

**Goal:** Complete test coverage against `TEST_PLAN_CURRENT.md`.

**Input:** All previous phases, `TEST_PLAN_CURRENT.md`.

**Output:** Test report. Bug list (if any). Confidence level for beta.

**Done when:** All scenarios in `TEST_PLAN_CURRENT.md` pass:

- R1 (no write before confirmation)
- Unified 3-button mutation cards
- Duplicate resolution `[Nowy]` / `[Aktualizuj]`
- R7 conditional firing (fires / doesn't fire lists)
- Read-only formatting (show_client, show_day_plan)
- Dual-write rules per intent (per Phase 5)
- Proactive scheduler (morning brief + evening follow-up)

**Do NOT:** Treat photo / multi-meeting test failures as MVP blockers — those flows are POST-MVP. Add features. Change specs. Rush to deploy. (Voice transcription went live 25.04.2026 — its tests **are** MVP blockers.)

---

## Active post-MVP slices (live)

- **Voice transcription** — Whisper STT + Polish name post-pass (Claude haiku) + 2-button confirm card (Zapisz/Anuluj). Live since 25.04.2026 (post-Phase 7 slice). Confirmed transcription flows through normal text path via `handle_text(text_override=...)`. Voice acts as input adapter — no separate voice intent type. Files: `bot/handlers/voice.py`, `shared/voice_postproc.py`, `shared/whisper_stt.py`, `bot/handlers/cancel.py`.

---

## Deferred POST-MVP Flows

These flows are out of scope for the first version of the behavior layer. Current Python code for these is legacy reference only — not a contract.

- **Photo upload** — Drive upload and Sheets link.
- **Multi-meeting** — batch of several meetings in one message.

**Rules:**
- Not blockers for MVP rewrite.
- Existing handlers may remain as-is during MVP; they are not audited or rewritten in phases 1-7.
- Will be scheduled separately after MVP stabilizes.

---

## Scope Guardrails — POST-MVP vs vision-only

Derived from `SOURCE_OF_TRUTH.md` §4. This plan must not silently promote vision-only items to roadmap.

**POST-MVP roadmap** (scheduled after MVP stabilizes):

- `edit_client`, `multi-meeting`, `photo_upload`, CSV/Excel import, full dashboard.
- `calendar_scope_narrowing` (per D7) — migrate from full `calendar` scope to `calendar.events`, with redesigned onboarding (user-created calendar + paste ID, or scope downgrade flow). Security hardening; not MVP blocker.
- `multi_timezone_support` (per D9) — add `users.timezone` column, read in domain layer via shared helper instead of `DEFAULT_TIMEZONE` constant, UI/command to change timezone, DST coverage cross-country. Scheduled when real non-PL user demand arrives.
- `evening_followup` — post-meeting check-in via `pending_followups` table. Shipped infra (Phase 5.3) but no runtime scheduler yet.
- `brief_pipeline_stats` — status-count dashboard optionally appended to morning brief.
- `per_user_brief_time` — respect existing `users.morning_brief_hour` column (currently hardcoded 07:00).
- `morning_brief_polish_pass` — Polish declension / humanization of brief lines (MVP ships with `Akcja: Klient` nominative template).
- `brief_persistent_jobstore` — APScheduler with SQLAlchemyJobStore so a missed 07:00 run retrofires after bot restart (PTB JobQueue does not).

**Product vision only / requires separate Maan decision** (described in `poznaj_swojego_agenta_v5_FINAL.md`, but **not approved as roadmap**):

- `reschedule_meeting`, `cancel_meeting`, `free_slots`, `delete_client`, habit learning (e.g. default meeting duration), flexible columns / refresh columns, daily interaction budget.

**NIEPLANOWANE** (permanently out of scope):

- Agent-side pre-meeting reminders — handled by native Google Calendar.

Do not implement vision-only items without an explicit decision from Maan.
