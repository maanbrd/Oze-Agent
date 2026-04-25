# OZE-Agent — Source of Truth

_Last updated: 24.04.2026_
_Owner: Maan_

Ten plik jest główną mapą projektu OZE-Agent.

Jeśli dwa dokumenty mówią co innego, wygrywa hierarchia z sekcji 5.
Jeśli dokument jest w `docs/archive/`, nie jest źródłem prawdy.

---

## 1. Aktualna decyzja strategiczna

Poprzednia ścieżka łatania błędów jest zamknięta.

Nie próbujemy już naprawiać obecnej warstwy zachowania błąd po błędzie.
Obecna strategia to **selective rewrite**.

### Zostaje

- Google Sheets wrapper
- Google Calendar wrapper
- Google Drive wrapper, jeśli obecny kod jest stabilny
- Supabase / database wrapper
- OpenAI wrapper
- auth / config
- podstawowy Telegram plumbing

### Do przepisania w ramach selective rewrite

- intent routing
- pending flow
- confirmation cards
- prompts
- proactive scheduler / morning brief
- warstwa decyzyjna agenta

### Odłożone poza pierwszą wersję behavior layer

- voice flow
- photo flow
- multi-meeting

Obecny kod voice/photo oraz ewentualne fragmenty batch/multi-meeting traktujemy jako legacy reference, nie kontrakt.

Kolejność przepisywania w ramach selective rewrite (w tym czy proactive scheduler/morning brief wchodzi w pierwszej rundzie, czy później) jest decyzją `IMPLEMENTATION_PLAN.md`, nie SSOT.

Największą wartością projektu są aktualne pliki `.md`, nie obecna implementacja behavior layer.

---

## 2. Aktywne dokumenty

| Plik | Status | Do czego służy |
|---|---|---|
| `SOURCE_OF_TRUTH.md` | aktywny | mapa projektu, hierarchia prawdy, aktualna strategia |
| `CURRENT_STATUS.md` | aktywny | krótki stan bieżący i najbliższy krok |
| `INTENCJE_MVP.md` | aktywny | kontrakt intencji MVP, Sheets schema, mutacje |
| `agent_system_prompt.md` | aktywny | ton agenta, zakazane frazy, wzorce odpowiedzi |
| `agent_behavior_spec_v5.md` | aktywny, zsynchronizowany 14.04 | reguły zachowania, testy akceptacyjne, scenariusze |
| `poznaj_swojego_agenta_v5_FINAL.md` | aktywny jako Product Vision / UX North Star, zsynchronizowany 14.04 | opis produktu, nie kontrakt implementacyjny |
| `ARCHITECTURE.md` | aktywny | architektura nowej wersji behavior layer |
| `IMPLEMENTATION_PLAN.md` | aktywny | kolejność przepisywania agenta |
| `TEST_PLAN_CURRENT.md` | aktywny | aktualny plan testów dla nowej wersji |
| `AGENT_WORKFLOW.md` | aktywny | multi-agent roles i workflow sequence |

---

## 3. Archive

Wszystkie pliki w `docs/archive/` są historyczne.

Można do nich zajrzeć dla kontekstu, ale nie wolno ich traktować jako aktualnych instrukcji implementacyjnych.

Szczególnie nieaktywne są:

- `implementation_guide_2.md`
- `protokol_testowania_v1.md`
- `CLAUDE_CODE_TASK.md`
- stare raporty testowe
- stare audyty
- stare briefy sesyjne

Jeśli aktywny dokument odwołuje się do pliku z `archive/`, to aktywny dokument wymaga poprawy.

---

## 4. Kanoniczne decyzje produktowe

### R1 — żadnych zapisów bez potwierdzenia

Agent nigdy nie zapisuje do Sheets, Calendar ani Drive bez świadomego potwierdzenia użytkownika.

Każda mutacja musi przejść przez kartę potwierdzenia, chyba że dokument intencji wyraźnie definiuje inny bezpieczny flow.

### Karty mutacyjne

Standardowa karta mutacyjna ma trzy akcje:

- `✅ Zapisać`
- `➕ Dopisać`
- `❌ Anulować`

`❌ Anulować` jest one-click cancel.
Nie ma drugiego pytania „na pewno?”.

`[Nowy]` / `[Aktualizuj]` dopuszczalne przy duplicate resolution (routing decision).
`[Tak]` / `[Nie]` dopuszczalne przy prostych pytaniach binarnych (nie jako potwierdzenie zapisu).
`[Zapisz bez]` retired.

### Google vs Supabase

Dane CRM użytkownika żyją w Google:

- Sheets
- Calendar
- Drive

Dane systemowe żyją w Supabase:

- użytkownicy
- auth
- konfiguracja
- pending state
- historia rozmowy
- techniczne metadane

Nie mieszamy tych dwóch światów.

### Sheets schema

Kanoniczny schemat arkusza jest w `INTENCJE_MVP.md`.

Jeśli kod albo inny dokument opisuje inne kolumny, wygrywa `INTENCJE_MVP.md`.

### Zakres prac — warstwy

**MVP** (kontrakt w `INTENCJE_MVP.md`):

- 6 intencji MVP: `add_client`, `show_client`, `add_note`, `change_status`, `add_meeting`, `show_day_plan`
- `general_question` (catch-all dla pytań poza 6 intencjami)

**POST-MVP roadmap** (realnie planowane po MVP, wymaga tylko harmonogramu):

- `edit_client`
- `multi-meeting` (batch kilku spotkań w jednej wiadomości)
- `voice_input`
- `photo_upload` (Drive)
- import CSV / Excel
- pełny dashboard
- `evening_followup` — post-meeting check-in przez `pending_followups` (infra z Phase 5.3, runtime scheduler post-MVP)
- `brief_pipeline_stats` — status-count dashboard opcjonalnie w morning brief
- `per_user_brief_time` — respektować `users.morning_brief_hour` (MVP hardcoduje 07:00)
- `morning_brief_polish_pass` — deklinacja / humanizacja linii briefu (MVP używa `Akcja: Klient` w mianowniku)

**Product vision only / wymaga osobnej decyzji Maana** — opisane w `poznaj_swojego_agenta_v5_FINAL.md` jako wizja, ale **nie zatwierdzone jako roadmapa**. Każdą trzeba osobno zaakceptować przed wejściem do implementacji. **Nie są NIEPLANOWANE i nie są POST-MVP roadmap** — zostają w tej warstwie dopóki Maan nie zdecyduje inaczej:

- `reschedule_meeting`
- `cancel_meeting`
- `free_slots`
- `delete_client` (ryzykowna mutacja — wymaga dodatkowej ostrożności)
- nauka nawyków (np. domyślna długość spotkania)
- elastyczne kolumny arkusza / refresh kolumn
- dzienny budżet interakcji — product/business direction, bez zatwierdzonej liczby i bez mechaniki pożyczania z dnia następnego. Nie jest kontraktem MVP.

**NIEPLANOWANE** (trwale poza zakresem):

- pre-meeting reminders po stronie agenta — przypomnienia przed spotkaniem obsługuje natywnie Google Calendar

### Voice, photo i multi-meeting

- Nie wchodzą do pierwszej wersji selective rewrite.
- Zostają jako POST-MVP / późniejsza runda.
- Obecny kod voice/photo oraz ewentualne fragmenty batch/multi-meeting traktujemy jako legacy reference, nie kontrakt.

### Product Vision

`poznaj_swojego_agenta_v5_FINAL.md` jest bardzo wartościowym plikiem produktowym.

Jego status:

**Product Vision / UX North Star, not implementation contract.**

Jeśli `poznaj...` obiecuje funkcję, której nie ma w `INTENCJE_MVP.md` albo `IMPLEMENTATION_PLAN.md`, to funkcja jest wizją, nie wymaganiem obecnej wersji.

---

## 5. Hierarchia prawdy

Jeśli dokumenty są sprzeczne, wygrywa dokument wyżej na liście:

1. `SOURCE_OF_TRUTH.md`
2. `CURRENT_STATUS.md`
3. `ARCHITECTURE.md`
4. `IMPLEMENTATION_PLAN.md`
5. `INTENCJE_MVP.md`
6. `agent_system_prompt.md`
7. `agent_behavior_spec_v5.md`
8. `TEST_PLAN_CURRENT.md`
9. `AGENT_WORKFLOW.md`
10. `poznaj_swojego_agenta_v5_FINAL.md`
11. `docs/archive/*`

Uwaga: `poznaj_swojego_agenta_v5_FINAL.md` ma wysoką wartość produktową, ale niski priorytet jako kontrakt implementacyjny.

---

## 6. Jak zaczynać nową sesję

### Jeśli robisz implementację

Czytaj w tej kolejności:

1. `SOURCE_OF_TRUTH.md`
2. `CURRENT_STATUS.md`
3. `ARCHITECTURE.md`
4. `IMPLEMENTATION_PLAN.md`
5. `INTENCJE_MVP.md`
6. `agent_system_prompt.md`

Nie zaczynaj od plików w `archive/`.

### Jeśli robisz testy

Czytaj:

1. `SOURCE_OF_TRUTH.md`
2. `CURRENT_STATUS.md`
3. `TEST_PLAN_CURRENT.md`
4. `INTENCJE_MVP.md`
5. `agent_system_prompt.md`

### Jeśli podejmujesz decyzje produktowe

Czytaj:

1. `SOURCE_OF_TRUTH.md`
2. `poznaj_swojego_agenta_v5_FINAL.md`
3. `INTENCJE_MVP.md`
4. `CURRENT_STATUS.md`

---

## 7. Status synchronizacji

| Dokument | Status |
|----------|--------|
| `CLAUDE.md` | ✅ Przepisany |
| `CURRENT_STATUS.md` | ✅ Oczyszczony |
| `SOURCE_OF_TRUTH.md` | ✅ Przepisany |
| `ARCHITECTURE.md` | ✅ Stworzony |
| `IMPLEMENTATION_PLAN.md` | ✅ Stworzony |
| `TEST_PLAN_CURRENT.md` | ✅ Stworzony |
| `AGENT_WORKFLOW.md` | ✅ Stworzony |
| `INTENCJE_MVP.md` | ✅ Zsynchronizowany (dual-write, duplicate resolution, buttons, display) |
| `agent_system_prompt.md` | ✅ Zsynchronizowany (button policies, display rules) |
| `agent_behavior_spec_v5.md` | ✅ Zsynchronizowany (duplicate flow, show_client, Calendar sync) |
| `poznaj_swojego_agenta_v5_FINAL.md` | ✅ Zsynchronizowany 14.04 jako Product Vision / UX North Star, nie runtime contract |

---

## 8. Najbliższy krok

Phase 1 z `IMPLEMENTATION_PLAN.md`: Infrastructure Audit.

Sprawdzić wrappery → verdict per wrapper → potem kontynuować rewrite zgodnie z `IMPLEMENTATION_PLAN.md`.
