# Phase 5 — Session Audit (planowanie 21.04.2026)

_Session: plan implementacji Phase 5 (Mutation Pipeline)_
_Baseline HEAD: bee2df6 ("docs: park duration mismatch and resume disambiguation slice")_
_Zatwierdzony plan: [/Users/mansoniasty/.claude/plans/eventual-pondering-church.md](/Users/mansoniasty/.claude/plans/eventual-pondering-church.md)_

**Completion update (22.04.2026):** Phase 5 Mutation Pipeline refactor COMPLETE.
Final bundled commit closes 5.5 + 5.5a + 5.6 + 5.7: add_client pipeline,
duplicate update pipeline, read-only audit (confirmed no-op), and narrowed
`handle_confirm` cleanup with per-flow helpers. Commit hash intentionally not
recorded here because this docs update is part of the same bundled commit.

---

## 1. Cel sesji

Zaplanowanie szczegółowej implementacji Phase 5 z [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md): uporządkowane pipeline'y mutacji z partial-result semantics i error handlingiem + jasny split mutation vs read-only. Ordering jest per-intent, nie globalny: np. `add_meeting` idzie Calendar → Sheets, a `add_client` z follow-up idzie Sheets → Calendar → Sheets.

Zgodnie z [CLAUDE.md](../CLAUDE.md): "Jeśli Maan prosi o propozycję, dostarcz proponowaną treść i czekaj na akceptację" — plan przeszedł przez iteracyjny review przed zatwierdzeniem.

---

## 2. Punkt wyjścia

**Stan po poprzedniej sesji (17.04.2026):**
- [bot/handlers/text.py](../oze-agent/bot/handlers/text.py) — ~2500 linii, handler + pipeline inline (`handle_confirm` linie ~2164-2400, 9 `flow_type` branchy)
- Duplicate detection: [shared/search.py::detect_duplicate_candidates](../oze-agent/shared/search.py) (zrobione w poprzedniej slice)
- Silent-pick fixes dla `handle_search_client`, `handle_add_note`, `handle_change_status` (17.04)
- `shared/mutations/`, `shared/clients/`, `shared/cards/` — **nie istnieją**
- `_first_name_ok` → żyje w handler layer
- `_find_exact_name_match` → istnieje w baseline HEAD `bee2df6`, ale aktualny dirty diff usuwa go jako część silent-pick cleanup

---

## 3. Rundy review Codexa

Plan przeszedł 4 rundy iteracyjnego review. Każda runda wymuszała rzetelne guardy przed implementacją.

### Runda 1 — 8 uwag strukturalnych

1. **Slice 5.1 był za szeroki** — "Foundation: shared/clients" mieszało pure extraction z migracją 4 handlerów
2. **Nie importować `_first_name_ok` z text.py do shared/clients** — odwraca warstwy
3. **`find_client` miał za dużo UX-trybów naraz** — fuzzy_suggest pasuje do show_client, ale nie do add_note/change_status
4. **Ordering "Sheets → Calendar" był sprzeczny z add_meeting** — realne jest Calendar → Sheets; słowo "atomic" niepoprawne dla cross-service
5. **Brakowało batch `add_meetings`** — ani pipeline, ani explicit out-of-scope
6. **handle_confirm miał więcej branchy niż plan obejmuje** — edit_client, delete_client, offer_*, add_client_duplicate
7. **Date format:** plan "[DD.MM.YYYY] text", obecny kod "[DD.MM.YYYY]: text" z dwukropkiem
8. **`update_client` ukryty side effect** — zawsze touchuje J column

**Reakcja:** Split Slice 5.1 na pre-foundation 5.0 + 5.1a/b/c/d/e; ordering per-intent; batch out of scope; date format fix.

### Runda 2 — 7 uwag semantycznych

1. **`lookup_client` fuzzy awareness + phone query** — `search_clients` JEST fuzzy; single fuzzy match nie może być `unique`; phone lookup wymaga osobnego kontraktu
2. **`_enrich_meeting` migration nie jest zero-behavior-change** — multi-match ≠ not_found; ambiguous_client flag
3. **`commit_add_meeting` API brakowało `current_status`** — pipeline nie ma skąd wiedzieć czy in_person+"Nowy lead" → auto-upgrade
4. **R7 zero regression** — nie wprowadzać fantomowej `_status_triggers_r7`
5. **Copy 1:1** — "✅ Notatka zapisana" było hallucynacją; obecny kod to "✅ Notatka dodana"
6. **`raw_update_client_row` nie eksportować jako NotImplemented** — runtime bug
7. **CRUD wrappers: kopiować dict przed forwardem** — `update_client` mutuje callera

**Reakcja:** `lookup_client` unique = exact/first_name_ok (nie fuzzy); `ambiguous_client` flag; `client_current_status` param; R7 zero-regression; copy weryfikacja text.py; raw skip; dict copy guard.

### Runda 3 — 7 uwag implementacyjnych

1. **`handle_search_client` branch `len(results) >= 50`** (text.py:1197) — odsyła do Sheets link, nie disambiguation; MUSI być zachowany 1:1
2. **Phone exact path na digits compare, nie `search_clients`** — zero Levenshtein/fuzzy
3. **5.1d jako osobna bramka** — nie blokuje reszty Phase 5 jeśli Maan odrzuci
4. **Konflikt raw_update_client_row w 5.5** — used w add_client followup, ale out of scope
5. **`commit_change_status` `old_status` — pipeline nie ma źródła** — handler ma w flow_data
6. **Copy add_meeting musi być spisana 1:1** — 4 warianty w text.py:2282/2327/2329/2331
7. **Baseline refresh z aktualnego HEAD** — plan musi zacząć od `git status`, nie starego snapshot'u

**Reakcja:** 50+ branch w testach 5.1b; phone digits-compare; 5.1d Gate A/B; 5.5 używa `update_client_row_touching_contact` zamiast raw; `old_status` usunięty z ChangeStatusResult; 4 copy warianty udokumentowane; pre-implementation baseline refresh section.

### Runda 4 — 8 ostatnich guardów

1. **`lookup_client` single-token fuzzy trap** — `first_name_ok` nie może sam wyznaczać unique przy single-token bez miasta; literal substring required
2. **Baseline 1 commit ≠ >3 commity** — re-audit wymagany nawet przy 1 commitie w plikach Phase 5 lub dirty worktree
3. **Slice 5.0 nie zakładać że `test_first_name_ok.py` istnieje** — weryfikacja przed slicem
4. **5.1d ambiguous_client to świadoma zmiana zachowania**, nie zero regression
5. **`commit_add_client` F/J mirror** — obecny `add_client` w google_sheets.py ustawia TYLKO I (Data pierwszego kontaktu); dodanie F/J byłoby behavior change vs spec compliance — osobny slice
6. **`today` param vs J side effect** — `today` kontroluje tylko note prefix, NIE J; J jest automatycznie przez update_client
7. **Error taxonomy spójna** — zero nowych error key w Phase 5 (`format_error("google_down")` zachowany)
8. **Pipeline test D8** — test extendedProperties w `tests/test_google_calendar.py`, nie w pipeline test

**Reakcja:** Unique rule 4-punktowa z regression testami ("Kowalsky" → not_found); re-audit trigger zaostrzony; pre-slice audyt 5.0; 5.1d explicit behavior change; commit_add_client mirror; today param semantics jawnie; zero nowych error key; D8 w osobnym test pliku.

---

## 4. Finalny plan (po 4 rundach)

**Zatwierdzony przez Maana:** 21.04.2026

### Struktura 12 slice'ów

**Pre-foundation:**
- **Slice 5.0** — `_first_name_ok` → `shared/matching.py` (≈30 min)

**Foundation (shared/clients/):**
- **Slice 5.1a** — `shared/clients/find.py` z `lookup_client` + `suggest_fuzzy_client` (≈2h)
- **Slice 5.1b** — migracja `handle_search_client` (≈2h)
- **Slice 5.1c** — migracja `handle_add_note` + `handle_change_status` (≈2h)
- **Slice 5.1d** — migracja `_enrich_meeting` (≈1.5h) **[DECISION GATE]**
- **Slice 5.1e** — `shared/clients/crud.py` z touching wrapper (≈1.5h)

**Mutations (shared/mutations/):**
- **Slice 5.2** — `commit_add_note` (≈3h)
- **Slice 5.3** — `commit_change_status` + R7 isolation (≈3h)
- **Slice 5.4** — `commit_add_meeting` (≈6h, największa)
- ~~**Slice 5.5** — `commit_add_client` + 5.5a `commit_update_client_fields` (≈4h)~~ ✅

**Cleanup:**
- ~~**Slice 5.6** — read-only refactor show_client + show_day_plan (≈2h)~~ ✅ confirmed no-op
- ~~**Slice 5.7** — `handle_confirm` narrowed cleanup (≈2h)~~ ✅

**Estimate total:** ~29h pracy. Każda slice committable i deployable samodzielnie.

### Kluczowe decyzje produktowe

1. **Batch `add_meetings`** — out of scope Phase 5 (POST-MVP roadmap); inline preserved z scope tag komentarzem
2. **`edit_client`, `delete_client`** — inline preserved (POST-MVP / vision-only)
3. **5.1d ambiguous_client** — wymaga explicit decyzji Maana; Gate A (implementujemy) lub Gate B (NO-OP, reszta Phase 5 leci)
4. **`commit_add_client` F/J mirror** — Phase 5 mirroruje obecne zachowanie (auto-I only); spec §4.1 compliance w osobnej slice
5. **Zero nowego error key** — `format_error("google_down")` zachowany; partial add_meeting używa istniejącej inline copy

### Niezmiennikowe kontrakty

- R1 (no writes before confirmation) — assertion w testach pipeline
- Unified 3-button card — format/kopie bez zmian
- Sheets column contracts A-P per D1/D4/D8
- Calendar extendedProperties tylko `event_type` per D8
- Note format `[DD.MM.YYYY]: text` z dwukropkiem (text.py:2429)
- R7 behavior: plain change_status ZAWSZE odpala R7, compound skipuje
- Copy 1:1 dla wszystkich mutations (spisane per pipeline w planie)

---

## 5. Baseline refresh (21.04.2026)

**Wykonane kroki per plan Pre-implementation:**

```
HEAD: bee2df6 ("docs: park duration mismatch and resume disambiguation slice")
Test files: 28
Collected tests: 319 (`.venv/bin/python -m pytest --collect-only -q`)
Nowe symbole Phase 5 (`lookup_client`, `commit_add_note`, `shared.matching`, ...): brak ✅
Istniejący symbol do migracji: `_first_name_ok` w `bot/handlers/text.py`
```

**Dirty worktree detection (Re-audit trigger odpalony):**

Modified:
- `oze-agent/bot/handlers/text.py` (silent-pick fixes z 17.04)
- `oze-agent/shared/claude_ai.py` (F7b prompt fix)
- `oze-agent/shared/search.py` (`detect_duplicate_candidates` centralization)
- `oze-agent/tests/handlers/test_change_status.py` (+2 tests)
- `oze-agent/tests/test_search.py` (+7 tests dla detect_duplicate_candidates)

Untracked:
- `oze-agent/tests/handlers/test_add_note_disambiguation.py` (nowy)
- `oze-agent/tests/handlers/test_search_client_disambiguation.py` (nowy)
- `oze-agent/tests/test_claude_ai_prompt.py` (nowy, F7b guard)
- `docs/phase5_audit.md` (ten audit)

Untracked non-Phase / nie commitować ślepo:
- `.DS_Store`
- `.claude/`
- `docs/archive/`

Deleted (doc cleanup):
- `docs/CODE_AUDIT_11-04-2026.md`
- `docs/NEXT_SESSION_PROMPT.md`
- `docs/TEST_PLAN_11-04-2026.md`
- `docs/implementation_guide_2.md`

**Re-audyt kolizji z Slice 5.0:**

- `_first_name_ok` **implementacja** w text.py niezmieniona (dirty zmiany w tym obszarze dotyczą wywołań — silent-pick fix zmienił `next(...)` na `[r for r in results if _first_name_ok(...)]`)
- `_find_exact_name_match` istnieje w HEAD `bee2df6`, ale aktualny dirty diff usuwa helper jako część silent-pick cleanup. Jeśli dirty changes zostaną skomitowane przed Phase 5, Slice 5.0 migruje tylko `_first_name_ok`.
- `shared/search.py` dirty = `detect_duplicate_candidates` (osobny moduł, zero kolizji)
- `test_first_name_ok.py` importuje z `bot.handlers.text._first_name_ok` → po Slice 5.0 zmieni import na `shared.matching`

**Werdykt:** Dirty zmiany NIE kolidują z Slice 5.0. Bezpieczne kontynuowanie.

---

## 6. Status (22.04.2026)

**Phase 5 COMPLETE.**

Final bundled commit closes the remaining cleanup slices:

1. ✅ **5.5** — `shared/mutations/add_client.commit_add_client` (Sheets-only, `google_down` taxonomy)
2. ✅ **5.5a** — `commit_update_client_fields` for duplicate merge updates via touch-contact wrapper
3. ✅ **5.6** — read-only audit: `show_client` / `show_day_plan` already use facade-backed read paths, so no-op
4. ✅ **5.7** — narrowed `handle_confirm` cleanup with per-flow helpers for simpler pipeline-backed flows

Preserved out-of-scope paths: `add_meetings` plural, `edit_client`, and
`delete_client` remain inline (POST-MVP / vision-only). Phase 5 intentionally
keeps `commit_add_client` F/J behavior as a mirror of current Sheets behavior
(auto-I only); spec §4.1 auto-status compliance remains POST-MVP.

**Next:** restart/deploy final bot build and run manual smoke for add_client,
duplicate update, batch add_clients, Sheets failure, show_client, and
show_day_plan.

---

## 7. Pliki powiązane

- **Plan:** [/Users/mansoniasty/.claude/plans/eventual-pondering-church.md](/Users/mansoniasty/.claude/plans/eventual-pondering-church.md)
- **Phase 5 spec:** [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)
- **Architektura:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Source of Truth:** [SOURCE_OF_TRUTH.md](SOURCE_OF_TRUTH.md)
- **Intent contracts:** [INTENCJE_MVP.md](INTENCJE_MVP.md)
