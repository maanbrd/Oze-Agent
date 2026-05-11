# OZE-Agent — Implementation Plan

_Last updated: 04.05.2026_

---

## Current Track — Agent Stabilization Before Web App

**Decision 27.04.2026:** finish stabilizing the Telegram agent before treating
the web app as launch-ready. The web app can continue later as a support
surface, but the product's core value is the agent in Telegram.

**Current deployed state:**
- `main` → Railway service `bot` → production Telegram bot.
- `develop` → Railway service `bot-test` → `t.me/OZEAgentTestBot`.
- Both branches currently point to `961fad1`.
- `bot-test` has a separate Telegram token, but may still write to the same
  Google Sheets / Calendar / Supabase resources as production.

**Active implementation policy:**
- All agent fixes land on `develop` first and are tested through `bot-test`.
- Promote `develop` → `main` only after the relevant smoke/regression cases pass.
- Use fictional data on `bot-test` until backend resources are split.
- Do not continue web app feature work as the primary track until the core agent
  flows are stable enough for repeatable manual tests.

**Immediate planned work:**
- Build a compact regression pack of real salesperson commands for `bot-test`.
- Harden the high-risk flows: add_client, add_meeting, voice → transcript →
  add_meeting, add_meeting → preseed add_client, duplicate/disambiguation,
  R7 next-action prompts, show_day_plan, `/cancel`.
- Add focused tests for each production bug before promoting fixes to `main`.
- Plan separate staging Google/Supabase resources before destructive testing.
- Run a controlled offer-generator smoke on fictional clients and controlled
  addresses before any real customer send.

## Offer Generator Slice — baseline implemented

Baseline commit: `09e0957 feat: add offer generator`.

Scope delivered:
- `/oferty` in the existing webapp, visually integrated with the dark app shell.
- Ready offers/drafts, manual ready-offer ordering, delete, duplicate-as-draft,
  validation gates and test PDF.
- Seller profile persistence: company, logo and global email body template.
  `Akcent` and `Podpis maila` are no longer active UI fields.
- Email template editor with natural writing + draggable/removable variable chips.
- Shared backend logic in `oze-agent/shared/offers/`: validation, pricing, PDF,
  email renderer, Gmail MIME sender, idempotent send pipeline.
- FastAPI offers route and Supabase system tables/bucket.
- Telegram send flow: list offers, select offer, resolve one client, confirm
  `✅ Wysłać` / `❌ Anulować`, Gmail send, then best-effort Sheets follow-up writes.

Current remaining work for this slice:
1. Manual `/oferty` browser smoke after deploy: create/publish/reorder/delete,
   duplicate, logo upload, email chips, test PDF.
2. Controlled Gmail Sent check with a non-customer address.
3. Telegram text send flow: `jakie mam oferty?`, send with number, no number,
   wrong number, missing email, multiple emails, email from command.
4. Telegram voice → transcript → send offer smoke.
5. Verify Supabase Storage bucket `offer-logos` and deployed env vars in staging/production.
6. Verify partial Sheets failure messaging after Gmail success.

---

## Deployed Hotfixes After Original Phase Plan

- `e744d84` — Unicode separator normalization and non-empty Telegram fallback replies.
- `bfa4061` — defensive stripping of secret env whitespace.
- `8b0be20` — carry client data from meeting text through add_meeting into add_client drafts.
- `961fad1` — deterministic meeting preflight for compound meeting+client messages, safe redacted classifier logs, and specific Anthropic tool forcing.

Current full test baseline after `961fad1`: `821 passed`.

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

Photo upload was revisited after the core MVP audit as an active post-MVP slice. Multi-meeting handlers and their current code remain legacy reference only. Voice transcription went live 25.04.2026 (post-Phase 7 slice) — see `CURRENT_STATUS.md`.

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

## Phase 3 — Intent Router Rewrite — done

**Goal:** Clean intent classifier with structured output.

**Input:** `INTENCJE_MVP.md` (6 intents), `agent_system_prompt.md` (examples).

**Output:** New `shared/intent/` module. Replaces `classify_intent` in `claude_ai.py`.

**Done when:** Router correctly classifies all 6 MVP intents + `general_question` with structured JSON output. Out-of-MVP requests are distinguished per `SOURCE_OF_TRUTH.md` §4, and the agent replies accordingly without hallucinating or misrouting:

- **POST-MVP roadmap** (e.g. `edit_client`, `multi-meeting`, CSV/Excel import, dashboard) → "to feature post-MVP". `photo_upload` is now an active post-MVP slice.
- **Vision-only** (e.g. `reschedule_meeting`, `cancel_meeting`, `free_slots`, `delete_client`) → "to poza aktualnym zakresem; wymaga osobnej decyzji".
- **NIEPLANOWANE** (e.g. agent-side pre-meeting reminders) → short refusal with a pointer to the native alternative (e.g. reminders handled by Google Calendar).

Manual test pass.

**Do NOT:** Add POST-MVP or vision-only intents into MVP runtime. Touch pending flow. Touch mutation pipeline.

---

## Phase 4 — Pending Flow + Confirmation Cards — done

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

**Do NOT:** Touch mutation pipeline internals. Add new card types. Implement photo in this phase.

---

## Phase 5 — Mutation Pipeline — done

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

**Do NOT:** Touch photo in this phase. Add POST-MVP intents. Change card format.

---

## Phase 6 — Proactive Scheduler / Morning Brief — implemented / deployed

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

**Current status 27.04.2026:** broad automated suite is green, but manual
Telegram regression is now run through `bot-test` first. Treat Phase 7 as the
active stabilization loop rather than a one-time final pass.

**Done when:** All scenarios in `TEST_PLAN_CURRENT.md` pass on `bot-test`, then
the relevant subset passes on production after promotion:

- R1 (no write before confirmation)
- Unified 3-button mutation cards
- Duplicate resolution `[Nowy]` / `[Aktualizuj]`
- R7 conditional firing (fires / doesn't fire lists)
- Read-only formatting (show_client, show_day_plan)
- Dual-write rules per intent (per Phase 5)
- Proactive scheduler (morning brief + evening follow-up)
- Offer-generator send flow on controlled test data before customer use

**Do NOT:** Treat multi-meeting test failures as MVP blockers. Photo upload is an active post-MVP slice and should be tested when touched. Add unrelated features. Change specs. Rush to deploy. (Voice transcription went live 25.04.2026 — its tests **are** MVP blockers. Offer generator is a separate approved product slice and has its own smoke gate.)

---

## Active post-MVP slices (live)

- **Voice transcription** — Whisper STT + Polish name post-pass (Claude haiku) + 2-button confirm card (Zapisz/Anuluj). Live since 25.04.2026 (post-Phase 7 slice). Confirmed transcription flows through normal text path via `handle_text(text_override=...)`. Voice acts as input adapter — no separate voice intent type. Files: `bot/handlers/voice.py`, `shared/voice_postproc.py`, `shared/whisper_stt.py`, `bot/handlers/cancel.py`.
- **Photo upload** — Telegram photo/image → R1 Drive card → Google Drive folder + Sheets N/O update + 15-minute active client photo session.

## Approved product slice outside the 6 bot intents

- **Offer generator** — implemented baseline, see section above. It is not a
  seventh CRM intent in `INTENCJE_MVP.md`; it is an adjacent product flow with
  web setup and Telegram/Gmail send. Future-dated "wyślę ofertę..." phrases
  still route to `add_meeting(offer_email)`.

---

## Deferred POST-MVP Flows

These flows are out of scope for the first version of the behavior layer. Current Python code for these is legacy reference only — not a contract.

- **Multi-meeting** — batch of several meetings in one message.

**Rules:**
- Not blockers for MVP rewrite.
- Existing handlers may remain as-is during MVP; they are not audited or rewritten in phases 1-7.
- Will be scheduled separately after MVP stabilizes.

---

## Scope Guardrails — POST-MVP vs vision-only

Derived from `SOURCE_OF_TRUTH.md` §4. This plan must not silently promote vision-only items to roadmap.

**POST-MVP roadmap** (scheduled after MVP stabilizes):

- `edit_client`, `multi-meeting`, CSV/Excel import, full dashboard. (`photo_upload` moved to active post-MVP slice.)
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
