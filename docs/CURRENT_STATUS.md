# OZE-Agent — Current Status
_Last updated: 11.04.2026 (popołudnie — po pełnej synchronizacji czterech plików SSOT + CLAUDE.md)_

> **Jak czytać ten plik.** To jest drugi plik który czytasz w nowej sesji (pierwszy: `SOURCE_OF_TRUTH.md`). Tu jest: stan aktualnej sesji, task na następną sesję, historia sesji, lista bugów. Wszystkie decyzje produktowe są w `SOURCE_OF_TRUTH.md` — tu tylko skróty i odniesienia. Jeśli coś się nie zgadza, wygrywa `SOURCE_OF_TRUTH.md`.

---

## Stan faz implementacji (po decyzjach 11.04.2026 popołudnie)

**Ważne:** po synchronizacji 11.04 popołudnie struktura intencji została zamrożona: 6 MVP + 3 POST-MVP + 4 NIEPLANOWANE (patrz `INTENCJE_MVP.md`). Poniższa mapa faz odzwierciedla tę decyzję — niektóre rzeczy które wcześniej były "⏳ TODO" zostały reklasyfikowane jako ❌ NIEPLANOWANE albo 🔵 POST-MVP.

```
Phase 1: Sheets — add client                       ⚠️ OUT-OF-SYNC
  Kod istnieje (commit bc765a2), ale pisany przeciwko wcześniejszemu specowi.
  Nowe wymagania po 11.04: 3-button cards (R1), R7 next_action_prompt (free-text),
  compound fusion (add_client + add_meeting), duplicate default-merge + 2-button
  disambiguation. Czy kod to robi — nie wiadomo, potrzebny audyt.

Phase 2: Sheets — search / status / notes           ⚠️ OUT-OF-SYNC
  - 2.1 show_client (search):     Kod działa, ale trzeba sprawdzić czy karta
                                   jest read-only (bez 3-button) — to jest MVP.
  - 2.2 add_note:                  Kod istnieje, wymaga 3-button + R7 po commicie.
  - 2.3 change_status:             Kod istnieje, wymaga 3-button + R7 + brak
                                   "Negocjacje" (pipeline 10→9 statusów).
  - 2.4 duplicates:                MVSZ: default merge + 2-button disambiguation
                                   `[📋 Dopisz] [➕ Utwórz nowy]`. Stary `[Nowy][Aktualizuj]`
                                   to drift. Trzeba sprawdzić co robi kod.
  - ~~2.5 filter~~:                🔵 POST-MVP — `filtruj_klientów` przeniesione,
                                   jeśli kod już to robi, musi wyświetlić banner
                                   POST-MVP albo zostać wycięty z MVP flow.
  - ~~2.6 edit_client~~:           🔵 POST-MVP — pełna edycja jako osobna intencja
                                   przeniesiona. Bug #6 (add_note routing) jest
                                   nieaktualny w starej formie — patrz sekcja bugów.

Phase 3: Calendar                                    ⚠️ OUT-OF-SYNC
  - 3.1 add_meeting (single):      Kod działa. Nowe wymagania: emoji 📅/📞/📨
                                   rozróżnienie (spotkanie / telefon / follow-up
                                   dokumentowy) wg tego co user powiedział. 3-button.
  - 3.2 Polish time:               Działa — "wpół do ósmej" → 07:30 ✅
  - 3.3 show_day_plan:             Karta read-only (bez 3-button). Bug #8 prompt tweak.
  - ~~3.4 reschedule_meeting~~:    ❌ NIEPLANOWANE (11.04) — user przesuwa ręcznie
                                   w Google Calendar. Jeśli kod już to obsługuje,
                                   wyciąć z routera intencji.
  - ~~3.5 cancel_meeting~~:        ❌ NIEPLANOWANE (11.04) — jak wyżej.
  - ~~3.6 free_slots~~:            ❌ NIEPLANOWANE (11.04) — user sam sprawdza w GCal.
  - 3.7 multi-meeting (compound):  Compound fusion w MVP: add_client+add_meeting,
                                   change_status+add_meeting, add_note+add_meeting.
                                   Bug #8 (gubi imię) nadal aktualny.

Phase 4: Drive (photos)                              ⏳ TODO
Phase 5: Voice input                                 ⏳ TODO
Phase 6: Proactive messages                          ⏳ TODO (morning brief bez Lejek)
Phase 7: Error handling + lejek POST-MVP banner      ⏳ TODO
```

**Pipeline statusów (9, po wycięciu Negocjacji 11.04):**
```json
["Nowy lead","Spotkanie umówione","Spotkanie odbyte","Oferta wysłana",
 "Podpisane","Zamontowana","Rezygnacja z umowy","Nieaktywny","Odrzucone"]
```
Jeśli w kodzie bota / w `shared/` widzisz jeszcze `"Negocjacje"` na tej liście — to jest drift do usunięcia w ramach audytu.

**Produkty MVP (4, po wycięciu Klimatyzacji 11.04):**
```
PV | Pompa ciepła | Magazyn energii | PV + Magazyn energii
```
Moc (kW / kWh) zawsze do kolumny `Notatki`, nigdy do nazwy produktu. Jeśli kod ma mapowanie `klimatyzacja` — drift.

---

## Naprawione (potwierdzone sesja 10.04)

| Bug | Commit |
|-----|--------|
| Excel serial (46120) + Wiersz: X w kartach | 8531d8a |
| "zmień telefon" → edit_client routing (wtedy MVP) | 82f92ab |
| "rezygnuje" → "Rezygnacja z umowy", format daty "Następny krok" | 08699a6, 39485b6 |
| Multi-match disambiguation przy zmianie statusu | 9fa41ec |
| Pipeline statusów rozszerzone do 10 wartości (wtedy) | 39485b6 |
| Bug #1 — pełne imiona w karcie meeting + day plan (`_enrich_meeting`) | bc765a2 |
| Bug #3 — data w karcie meeting (`Data: 11.04.2026 (sobota)`) | bc765a2 |
| B14 — polska odmiana w wyszukiwaniu | wcześniej |

**Uwaga:** niektóre z tych fixów mogą być teraz częściowo nieaktualne po zmianie struktury intencji — np. pipeline 10→9 wymaga revertu do "10 wartości". Audyt kodu to wychwyci.

---

## Znane bugi (stan 11.04 popołudnie, po reklasyfikacji)

### Bugi dalej aktywne w MVP

| Bug | Objaw | Priorytet | Uwagi |
|-----|-------|-----------|-------|
| Bug #7 | Gołe telefony podczas pending flow → kolizja (zapisuje jako commit zamiast pokazać kartę z "Brakuje: imię") | High | Dotyka dowolnej mutacji z niekompletnymi danymi — dotyka 3-button flow, więc musi być naprawione razem z R1 |
| Bug #8 | Multi-meeting parser gubi imię gdy w mianowniku między odmienionymi formami | Medium | Aktualne — compound fusion w MVP tego używa |
| Bug #9 | Multi-meeting format daty "11.04 09:00" bez roku (inconsistency z single meeting) | Low | Kosmetyka, prompt tweak |
| Bug #10 | Polish inflection w day plan "Spotkanie z Jan Mazur" → powinno być "z Janem Mazurem" | Low | Nice-to-have |

### Bugi zreklasyfikowane / nieaktualne

| Bug | Co się stało |
|-----|--------------|
| Bug #6 | Był: "dodaj notatkę do Jana Nowaka tworzy nowego klienta zamiast routingu do edit_client". Teraz: `edit_client` jest POST-MVP, więc routing wygląda inaczej — `add_note` powinien trafić do intencji `add_note` (MVP), a intent classifier musi to rozróżnić od `add_client`. To jest nadal bug, ale z innym celem routingu. Status: wymaga re-testu przy audycie. |

---

## Historia sesji

### 10.04.2026 wieczór — Round 7 + Round 8 testy manualne + decyzje produktowe
Po testach manualnych w Telegramie Maan podjął decyzje (autorytatywna wersja w `SOURCE_OF_TRUTH.md` sekcja 4):
1. Specyfikacje techniczne (metraż, kierunek dachu, kWh, napięcie, typ dachu) → kolumna `Notatki`, nie osobne kolumny.
2. Moc produktu (kW/kWh) → do `Notatki`. Kolumna `Produkt` zawiera tylko typ bez liczb. _(Rewersja decyzji "moc doklejona do produktu" z wcześniejszej sesji.)_
3. R4 (obowiązkowe pytanie o następny kontakt) — USUNIĘTE. Agent nie pyta sam z siebie.
4. `OZE_Agent_Brief_v5_FINAL.md` → `docs/archive/`.

Commity: 8531d8a, 82f92ab, 08699a6, 39485b6, 9fa41ec, bc765a2.

### 11.04.2026 rano — synchronizacja SOURCE_OF_TRUTH.md + INTENCJE_MVP.md
Sesja zaczęła się od audytu wszystkich dokumentów pod kątem spójności. Wynik: **zamrożenie kontraktów intencji MVP** w nowym pliku `INTENCJE_MVP.md` + rewizja hierarchii SSOT w `SOURCE_OF_TRUTH.md`. Decyzje:
- **6 MVP intencji:** add_client, show_client, add_note, change_status, add_meeting, show_day_plan.
- **3 POST-MVP:** edit_client (pełna edycja), filtruj_klientów, lejek_sprzedazowy.
- **4 NIEPLANOWANE (wycięte na stałe):** reschedule_meeting, cancel_meeting, free_slots, meeting_non_working_day_warning.
- **Pipeline 10 → 9 statusów** (usunięty "Negocjacje" — w B2C OZE etap "Negocjacje" nie istnieje jako osobny krok, "Oferta wysłana" → "Podpisane" bez stopnia pośredniego).
- **Produkty 5 → 4** (usunięta "Klimatyzacja" — nie wchodzi w scope MVP OZE-Agent, B2C w Polsce klimatyzację ma jako osobny biznes).
- **Schemat Sheets zamrożony na 16 kolumnach A-P.** Kod jest schema-agnostic (czyta nagłówki z wiersza 1), ale nowe kolumny dodajemy tylko przez zmianę tamtego kontraktu.
- **7 opcji "następnego kroku":** Telefon, Spotkanie, Wysłać ofertę, Follow-up dokumentowy, Czekać na decyzję klienta, Nic — zamknięte, Inne.

### 11.04.2026 popołudnie — synchronizacja agent_behavior_spec_v5.md + agent_system_prompt.md + CLAUDE.md
Kontynuacja poranka. Zmiany:
- **R1 → 3-button cards + one-click cancel.** Stare wzorce `[Tak][Nie]`, `[Zapisz bez]`, `[Nowy][Aktualizuj]` retired. Nowy wzorzec: `[✅ Zapisać] [➕ Dopisać] [❌ Anulować]`. Jedno kliknięcie anuluje — żadnej pętli `Na pewno?`.
- **R7 next_action_prompt → free-text open question** (nie sztywna trójka meeting/call/not-interested). Agent po committed mutacji pyta otwarcie "Co dalej z X?" i parsuje prozę. Rewersja decyzji z 10.04 wieczór.
- **R3 (kolizja z pending) cztery trasy:** compound fusion → auto-doklejanie → explicit `➕ Dopisać` → auto-cancel.
- **R4 (duplikaty) default merge + 2-button disambiguation:** `[📋 Dopisz do istniejącego] [➕ Utwórz nowy wpis]`. Domyślna akcja bez klikania: merge.
- **Compound fusion combos dozwolone w MVP:** change_status+add_meeting, add_note+add_meeting, add_client+add_meeting. Cała reszta — osobne karty.
- **add_meeting emoji differentiation:** 📅 spotkanie, 📞 telefon, 📨 follow-up dokumentowy. Jeden pattern zamiast dwóch (wcześniej były osobne "Calendar — adding meetings" i "Follow-up / reminder").
- **Morning brief** bez linii "Lejek:" (POST-MVP). Evening follow-up mentions osobne 3-button cards per klient + R7.
- **Voice processing flow (Faza 5):** low confidence → `[Tak][Nie]` disambiguation (non-mutation), good confidence → standard 3-button card.

Pliki zaktualizowane w tej sesji:
- `docs/SOURCE_OF_TRUTH.md` — nowy entry "11.04.2026 popołudnie", sekcja 7 marks wszystkie cztery pliki SSOT jako synced.
- `docs/INTENCJE_MVP.md` — sekcja 8 split na 8.1 (POST-MVP) + 8.2 (NIEPLANOWANE) z rationale.
- `docs/agent_behavior_spec_v5.md` — testy 28/29 reklasyfikowane na NIEPLANOWANE; sekcja 6.2 zaktualizowana; nowa sekcja 6.3 "Intencje NIEPLANOWANE"; sekcja 11.2 POST-MVP metryki updated.
- `docs/agent_system_prompt.md` — 14+ edytów: Adding a client, Searching, Status change, MERGED Calendar+Follow-up → add_meeting z emoji, DELETED free_slots/reschedule/cancel/non-working-day, Photos, Duplicate disambiguation, Calendar conflict, Lejek POST-MVP banner, Morning brief bez Lejek, Voice flow Faza 5.
- `CLAUDE.md` (root projektu) — przepisana sekcja `# Current Project: OZE-Agent` i wszystko pod spodem (linie 42-163). Dodana sekcja "SSOT (Single Source of Truth) — kolejność czytania", przepisane Rule #9 (R7 free-text) i Rule #10 (3-button + one-click cancel), rozszerzona tabela Architecture Rules, przepisana sekcja "What to Read Before Starting".
- `docs/CURRENT_STATUS.md` — ten plik (w toku).
- `docs/implementation_guide_2.md` — pending: dodać baner "partially stale od 11.04.2026 popołudnie".

---

## Zadanie na następną sesję

**Wykonanie fixów z audytu według `docs/NEXT_SESSION_PROMPT.md`, Sesja A–G, dyscyplina jedna rzecz naraz.** Audyt zakończony w poprzedniej sesji — wynik w `docs/CODE_AUDIT_11-04-2026.md` (0/15 punktów checklisty zgodnych, drift systemowy R1/R3/R4/R6/R7 + schema Sheets + retired intents/products/statuses). Plan krok-po-kroku podzielony na 7 sesji kodowych (A–G) + 1 sesja testowa (H) w `docs/NEXT_SESSION_PROMPT.md`. Smoke test Telegram (2–3 scenariusze) po zakończeniu każdej sesji, pełny `docs/TEST_PLAN_11-04-2026.md` (15 testów) w Sesji H na końcu. Poniższa sekcja (zakres audytu + 15-punktowa checklista) zostaje jako kontekst historyczny — audyt jest zamknięty, ta checklista była jego inputem.

**Zakres audytu:**
- `bot/` — cały router intencji, handlery, pending flow, 3-button keyboard builder
- `shared/` — business logic (Sheets/Calendar/Drive writers, R1 confirmation gate, R3 pending handling, R4 duplicate detection, R7 next_action_prompt, intent classifier, compound fusion, pipeline statusów, produkty, 7-opcji lista "Następny krok")
- `api/` — FastAPI endpointy jeśli ruszają CRM data

**Format tabeli CODE_AUDIT_11-04-2026.md:**
| Plik:linia | Stan kodu | Stan speca (który plik SSOT) | Kategoria | Priorytet | Estymata |

Kategorie:
- **known_bug** — coś co już było w Bug #X i dalej nie działa
- **new_drift** — kod jest zgodny ze starym specem, ale po 11.04 już nie jest
- **aligned** — ok, zgodne z nowym SSOT (nie pisz tego w tabeli, tylko żeby audyt był kompletny — można w osobnej sekcji "Sprawdzone, OK")

Priorytety:
- **must** — blokuje działanie MVP (np. `Negocjacje` w pipeline, `[Nowy][Aktualizuj]` w duplikatach, brakujące 3-button, brakujące R7)
- **should** — psuje UX ale bot działa (np. emoji 📅/📞/📨 w add_meeting)
- **nice** — kosmetyka (np. Bug #10 polish inflection)

**Kluczowe rzeczy do sprawdzenia explicite (checklist dla audytu):**
1. Router intencji — czy są w ogóle handlery na `reschedule_meeting` / `cancel_meeting` / `free_slots`? Jeśli tak, muszą wyjść z MVP flow.
2. Router intencji — czy `edit_client` i `filtruj_klientów` są w MVP flow? Jeśli tak, muszą dostać POST-MVP banner albo wyjść.
3. Pipeline statusów — czy lista zawiera `Negocjacje`? Gdziekolwiek.
4. Produkty — czy mapowanie obejmuje `klimatyzacja`?
5. Confirmation keyboard — czy jest 3-button `[✅ Zapisać] [➕ Dopisać] [❌ Anulować]`? Czy są jeszcze stare `[Tak][Nie]` / `[Zapisz bez]`? (Uwaga: `[Tak][Nie]` jest legit dla read-only disambiguation w voice flow i w fuzzy-match search — nie każdy `[Tak][Nie]` to drift.)
6. Anulowanie pending — czy jest pętla `Na pewno anulować?` czy one-click? (Musi być one-click.)
7. Duplicate detection (`add_client` z duplikatem) — czy jest 2-button `[📋 Dopisz] [➕ Utwórz nowy]` czy stary `[Nowy][Aktualizuj]`?
8. R7 next_action_prompt — czy bot pyta po committed mutacji? W jakiej formie? (Musi być free-text, nie trójka.)
9. Compound fusion — czy router rozpoznaje `add_client + add_meeting`, `change_status + add_meeting`, `add_note + add_meeting` i składa w jedną kartę?
10. `add_meeting` — czy rozróżnia 📅 spotkanie / 📞 telefon / 📨 follow-up dokumentowy na podstawie tego co user powiedział?
11. `show_client` i `show_day_plan` — czy karta jest read-only (bez 3-button)?
12. Morning brief — czy zawiera linię "Lejek:"? (Nie powinna.)
13. Moc produktu — czy trafia do `Notatki`, czy do nazwy produktu albo osobnej kolumny?
14. Schemat Sheets — czy kod czyta nagłówki z wiersza 1 (schema-agnostic), czy ma hardcoded indeksy kolumn?
15. Format daty w user-facing textach — czy zawsze `DD.MM.YYYY (Dzień tygodnia)`?

**Gdy audyt gotowy:** Maan triażuje (must → should → nice), decydujemy co wchodzi do Fazy fix przed testami, idziemy krok po kroku z manualnymi testami w Telegramie per Rule #11.

---

## Co działa dobrze (prawdopodobnie nie ruszać bez konkretnego powodu)

Poniższe zostało potwierdzone testami w poprzednich sesjach — ale uwaga, "działa" oznacza "działało przeciwko specowi z 10.04", a nie "działa przeciwko specowi z 11.04". Po audycie będzie jasne które punkty wciąż są OK a które są new_drift.

- Dodawanie klienta — merge, diakrytyki, slang OZE
- Wyszukiwanie — odmiana, fuzzy match, daty `DD.MM.YYYY (Dzień tygodnia)`
- Zmiana statusu — dedukcja, multi-match disambiguation
- Spotkania — proste formaty, polski czas ("wpół do ósmej" → 07:30)
- State-lock fix — auto-cancel + process normally
- Garbage handling (user pisze "xdddd" → bot nie próbuje dopasować do intencji)
- Kontekst emocjonalny → Notatki
- Format daty: `DD.MM.YYYY (Dzień tygodnia)` w user-facing tekstach

---

## Jak działamy

- **Claude Code** — implementuje i naprawia kod
- **Claude Cowork** — testuje manualnie w Telegram, generuje raporty
- **Maan** — decyduje o priorytetach, przekazuje wyniki między sesjami

**Na początku każdej sesji** Claude Code czyta w kolejności:
1. `docs/SOURCE_OF_TRUTH.md` — mapa decyzji + hierarchia SSOT
2. `docs/CURRENT_STATUS.md` — ten plik — stan teraz + task na sesję
3. Wedle potrzeby: `INTENCJE_MVP.md`, `agent_behavior_spec_v5.md`, `agent_system_prompt.md`, `implementation_guide_2.md` (z ostrożnością — częściowo stale).

**Na końcu każdej sesji** Claude Code aktualizuje ten plik: historia sesji + status bugów + task na następną sesję. Decyzje produktowe idą do `SOURCE_OF_TRUTH.md` decision log, nie tutaj.
