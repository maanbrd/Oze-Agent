# OZE-Agent — Current Status

_Last updated: 15.04.2026_

---

## Decision

Previous bug-by-bug patching track is closed.

Current strategy: **selective rewrite of the behavior layer**.

The Python behavior layer is legacy/reference — not trusted as behavior contract.
The `.md` documentation is the primary project asset.
We do not delete infrastructure blindly.

### Keep (potential reuse)

- Google Sheets wrapper (`shared/google_sheets.py`)
- Google Calendar wrapper (`shared/google_calendar.py`)
- Google Drive wrapper (`shared/google_drive.py`)
- Supabase / database wrapper (`shared/database.py`)
- OpenAI wrapper (`shared/claude_ai.py`)
- auth / config (`shared/google_auth.py`, env)
- basic Telegram plumbing (`bot/main.py`, handler registration)

### Rewrite

- intent routing
- pending flow / state machine
- confirmation cards
- prompts / orchestration layer
- proactive scheduler / morning brief
- agent decision layer

### Deferred beyond first version

- voice flow
- photo flow
- multi-meeting

Current voice/photo code (and any batch/multi-meeting fragments) is legacy reference only.

---

## Next Steps

1. Uporządkować `SOURCE_OF_TRUTH.md` — done
2. Stworzyć `ARCHITECTURE.md` — done
3. Stworzyć `IMPLEMENTATION_PLAN.md` — done
4. Stworzyć `TEST_PLAN_CURRENT.md` — done
5. Stworzyć `AGENT_WORKFLOW.md` — done
6. Zsynchronizować dokumenty z decyzjami 13-14.04 — done:
   - `INTENCJE_MVP.md`, `agent_system_prompt.md`, `agent_behavior_spec_v5.md`
   - `poznaj_swojego_agenta_v5_FINAL.md`
   - `TEST_PLAN_CURRENT.md`
   - `CLAUDE.md`
   - `SOURCE_OF_TRUTH.md`
7. Phase 1 Infrastructure Audit — done (see `docs/PHASE1_AUDIT.md`)
8. Phase 2 Behavior Contract Freeze — done (see `docs/PHASE2_CONTRACT_FREEZE.md`; 9/9 decyzji frozen, commits `65b5661` + `117f9c2`)
9. Phase 3 — Intent Router Rewrite — **next** (per `docs/IMPLEMENTATION_PLAN.md`)

---

## Phase 2 Behavior Contract Freeze — done

9/9 decyzji zamrożonych — pełny kontrakt behavior layer spisany w `docs/PHASE2_CONTRACT_FREEZE.md`.

- **Package 1** (`65b5661`) — D1 Sheets date format, D2 Calendar timezone contract, D3 Calendar reminders policy, D4 `Następny krok` enum values.
- **Package 2** (`117f9c2`) — D5 voice/photo/multi-meeting handler scope, D6 `get_conversation_history` 30-min window, D7 Calendar scope narrowing, D8 extendedProperties, D9 user timezone.

Housekeeping / security items z Phase 1 audit (~32) — osobny backlog, obsługiwane w miarę implementacji Phase 3-7.

## Phase 3 — Intent Router Rewrite — next

Per `docs/IMPLEMENTATION_PLAN.md` Phase 3. Klasyfikator 6 MVP intentów + `general_question` z strukturalnym JSON output. Rozróżnia POST-MVP roadmap / vision-only / NIEPLANOWANE z odpowiednio różnymi reply templates.

Kontrakty zamrożone w Phase 2 (w szczególności D4 enum, D5 voice/photo stub, D6 30-min history window) są wejściem dla Phase 3.

---

## What Changed

### Sesja 13.04

- `CLAUDE.md` — przepisany pod nową strategię (selective rewrite, not patch-track)
- `SOURCE_OF_TRUTH.md` — przepisany na czystą mapę projektu
- `CURRENT_STATUS.md` — oczyszczony z historii sesji i starych bugów
- `ARCHITECTURE.md` — stworzony
- `IMPLEMENTATION_PLAN.md` — stworzony
- `TEST_PLAN_CURRENT.md` — stworzony
- `AGENT_WORKFLOW.md` — stworzony
- `INTENCJE_MVP.md` — zsynchronizowany (dual-write, duplicate resolution, display fields, Calendar sync)
- `agent_system_prompt.md` — zsynchronizowany (button policies, display rules)
- `agent_behavior_spec_v5.md` — zsynchronizowany (duplicate flow, show_client fields, Calendar sync, button rules)

### Sesja 14.04

- `poznaj_swojego_agenta_v5_FINAL.md` — zsynchronizowany jako Product Vision / UX North Star (ramka wizji, 16 kolumn kanonicznych, 9 statusów bez Negocjacji, 3-button, sekcja "Gdy klient już jest w bazie", pre-meeting reminders i twardy limit 100/dzień usunięte z runtime)
- `TEST_PLAN_CURRENT.md` — change_status 3-button, duplicate resolution testy (AC-4a/4b, AN-4, AM-8), show_day_plan (SDP-1..5), voice/photo flow usunięte, morning brief bez pipeline stats, evening follow-up dodany
- `CLAUDE.md` — unified 3-button dla wszystkich mutacji (usunięty wyjątek change_status 2-button), Read First rozszerzone o ARCHITECTURE/IMPLEMENTATION_PLAN/AGENT_WORKFLOW/TEST_PLAN_CURRENT, rewrite list bez voice/photo (POST-MVP)
- `SOURCE_OF_TRUTH.md` — czterowarstwowy podział zakresu prac (MVP / POST-MVP roadmap / Product vision only-wymaga decyzji / NIEPLANOWANE); reschedule_meeting, cancel_meeting, free_slots, delete_client eksplicite vision-only; Voice/photo/multi-meeting jako sekcja deferred; sekcja "Najbliższy krok" bez obietnicy "Phase 2"
- `docs/PHASE1_AUDIT.md` — **stworzony**. Per-wrapper audyt 7 plików infrastruktury (Google Sheets/Calendar/Drive, Supabase, OpenAI/Claude, OAuth, Telegram plumbing). 6 MVP blockerów, 9 Phase 2 decisions, ~32 housekeeping/security items. Zero rewrite'ów — wszystkie wrappery zostają z adjustmentami.

### Sesja 15.04

- `docs/PHASE2_CONTRACT_FREEZE.md` — **stworzony i domknięty**. 9/9 decyzji zamrożonych: D1 Sheets date format (ISO + PL display), D2 Calendar timezone (tz-aware Warsaw, wrapper rejects naive), D3 Calendar reminders (`useDefault: True`, no scheduler pre-meeting), D4 `Następny krok` enum (runtime English ↔ Sheets Polish, K=label never date), D5 voice/photo/multi-meeting → POST-MVP stub, D6 `get_conversation_history` hybrid `since` param (MVP mandate 30 min), D7 Calendar full scope in MVP (narrowing = POST-MVP hardening), D8 minimal `extendedProperties.private.event_type` + Sheets P as primary link, D9 hardcoded `Europe/Warsaw` via single `DEFAULT_TIMEZONE` constant. Commits: `65b5661` (D1-D4), `117f9c2` (D5-D9).
- `INTENCJE_MVP.md` — docs follow-up: §4.5 K/L semantics per D4 (K=label, L=data, P=event_id), extendedProperties tylko `event_type` per D8 (usunięte `client_sheet_row`/`managed_by`), §7 plan dnia filtruje po dedykowanym OZE calendar zamiast `managed_by` flag, offer_email emoji 📨.
- `IMPLEMENTATION_PLAN.md` — dopisane POST-MVP roadmap items: `calendar_scope_narrowing` (D7), `multi_timezone_support` (D9).
- Drift reconcile #2 (pre-Phase 3): `INTENCJE_MVP.md` §8.2 split na vision-only + §8.3 NIEPLANOWANE (per 4-tier SSOT model z 14.04; reschedule/cancel/free_slots/delete_client przeklasyfikowane z NIEPLANOWANE → VISION_ONLY; daily interaction limit oznaczony jako policy/business vision, nie router intent); §11 kolumna P poprawiona (populated w MVP dla Calendar-backed next steps, per D8); `agent_behavior_spec_v5.md` §6.3 rename NIEPLANOWANE → VISION-ONLY + §6.4 NIEPLANOWANE (tylko pre-meeting reminders); `PHASE2_CONTRACT_FREEZE.md` D8 wording "POST-MVP flows" → "Vision-only flows"; `TEST_PLAN_CURRENT.md` SDP-5 reclassify POST-MVP → VISION_ONLY.

---

## Phase 4 — Known follow-ups

### duplicate UX: same full name across multiple cities needs disambiguation

**Status:** open follow-up.

When the same full name exists in two or more cities and the user types only the name (no city), `detect_potential_duplicate` (post-`aefa2e5`) returns the first name-only match by iteration order instead of asking the user which row they meant.

Example:
- Sheets: `Marysia Mastalerz — Warszawa`, `Marysia Mastalerz — Kraków`
- User: `Marysia Mastalerz`
- Expected: bot asks which Marysia (or shows both candidates).
- Current: bot picks one row silently.

Discovered during smoke testing of `aefa2e5`. Documented as MVP limitation in the docstring at `oze-agent/shared/search.py::detect_potential_duplicate`.

Does not block continuing the typed-pending migration. Duplicate UX is not fully complete until a disambiguation flow is added (separate slice — same shape as the existing disambiguation pending flow used by `add_note` / `change_status`).
