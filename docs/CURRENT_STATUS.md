# OZE-Agent — Current Status

_Last updated: 14.04.2026_

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
8. Phase 2 Behavior Contract Freeze — **next**
9. Dopiero potem: przepisywać behavior layer zgodnie z `IMPLEMENTATION_PLAN.md`

---

## Phase 2 Behavior Contract Freeze — next

Derived from `docs/PHASE1_AUDIT.md`. Top decisions to freeze before `shared/intent/` / `shared/mutations/` / `shared/clients/` work starts:

1. **Sheets date format** — ISO (`YYYY-MM-DD` writes, formatter renders PL) vs direct PL (`DD.MM.YYYY` writes). Blocker before Phase 5.
2. **Calendar timezone contract** — wrapper assumes naive datetimes are Warsaw (and attaches tzinfo) vs wrapper requires tz-aware datetimes from callers. Also: `get_events_for_date` must use Warsaw-local midnight boundary. Blocker before Phase 5 `add_meeting`.
3. **Calendar reminders policy** — `reminders: {useDefault: True}` (rely on native Google Calendar default) vs `{useDefault: False, overrides: []}` (explicit suppression) vs no-touch-implicit (documented). Maan's direction: agent does not create reminders.
4. **`Następny krok` (column K) enum values** — reconcile inline code hints (`Telefon / Spotkanie / Wysłać ofertę`) with canonical enum in `INTENCJE_MVP.md` / `agent_system_prompt.md` (`phone_call / in_person / doc_followup`).
5. **Voice / photo handler registration scope (`bot/main.py`)** — unregister (fall through to fallback) vs register-to-POST-MVP-stub vs feature flags. Tie to intent router scope tiers from Phase 3.

Full list of 9 decisions + ~32 housekeeping / security items: `docs/PHASE1_AUDIT.md`.

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
