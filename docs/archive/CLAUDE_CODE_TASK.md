# ZADANIE DLA CLAUDE CODE — PRIORYTET KRYTYCZNY

**Data:** 9 kwietnia 2026, 20:35
**Źródło:** Cowork Tester (Runda 6 testów manualnych na Telegramie)
**Priorytet:** KRYTYCZNY — blokuje wszystkie dalsze testy

---

## BUG #1: Agent gubi imiona klientów — wyświetla TYLKO nazwisko

### Opis problemu

Agent ZAWSZE wyświetla klientów jako samo nazwisko (np. "Nowak", "Mazur", "Kowalski") zamiast imię + nazwisko (np. "Jan Nowak", "Andrzej Mazur", "Jan Kowalski").

**Gdzie się pojawia:**
- Wyszukiwanie klienta: "Nowak, Piaseczno" zamiast "Jan Nowak, Piaseczno"
- Plan dnia: "Spotkanie z Nowak" zamiast "Spotkanie z Jan Nowak"
- Zmiana statusu: "Zmienić status klienta Nowak?" zamiast "Jan Nowak"
- Spotkania: "Klient: Nowak" zamiast "Klient: Jan Nowak"
- Wielokrotne wyniki: "1. Nowak — Piaseczno, 2. Nowak — Piaseczno" — IDENTYCZNE, nie da się odróżnić!
- Evening brief, morning brief, follow-upy — wszędzie samo nazwisko

**Gdzie działa poprawnie:**
- Dodawanie klienta (add_client) — bo user sam wpisuje imię i agent je kopiuje dosłownie

### Root Cause

**Przykłady w `docs/agent_system_prompt.md`** — to z nich Claude się uczy. WSZYSTKIE response patterns pokazują same nazwiska. Claude naśladuje te przykłady.

### PLIKI DO NAPRAWY (research wynik)

#### 1. `docs/agent_system_prompt.md` — GŁÓWNY PLIK (12+ zmian)

| Linia | Teraz (ŹLE) | Powinno być (DOBRZE) |
|-------|-------------|---------------------|
| ~125 | `📋 Nowak, Piaseczno` | `📋 Jan Nowak, Piaseczno` |
| ~136 | `📋 Wiśniewski, Kościuszki 8, Legionowo` | `📋 Adam Wiśniewski, Kościuszki 8, Legionowo` |
| ~149-157 | `📋 Jan Kowalski — Piłsudskiego 12` (OK), ale multi-match: `1. Jan Kowalski — Warszawa` | OK — tu jest poprawne |
| ~181 | `🫡 Kowalski → Podpisane?` | `🫡 Jan Kowalski → Podpisane?` |
| ~191-193 | `10:00 Kowalski — Piłsudskiego 12`, `14:00 Nowak — Leśna 5`, `17:00 Wiśniewski — Kościuszki 8` | `10:00 Jan Kowalski — ...`, `14:00 Jan Nowak — ...`, `17:00 Adam Wiśniewski — ...` |
| ~200 | `🫵 Wiśniewski nie jest w bazie` | `🫵 Adam Wiśniewski nie jest w bazie` |
| ~210-212 | Day plan z samymi nazwiskami | Dodaj imiona |
| ~220 | Wolne okna — OK (brak nazwisk) | — |
| ~230 | `📅 Kowalski:` | `📅 Jan Kowalski:` |
| ~232-233 | `Było: środa... Będzie: piątek...` | OK format |
| ~242 | `Usunąć spotkanie z Nowakiem` | `Usunąć spotkanie z Janem Nowakiem` |
| ~255 | `📸 3 zdjęcia → Kowalski, Warszawa` | `📸 3 zdjęcia → Jan Kowalski, Warszawa` |
| ~291 | `⚠️ Masz już Kowalskiego z Warszawy` | `⚠️ Masz już Jana Kowalskiego z Warszawy` |
| ~300 | `⚠️ Jutro o 14:00 masz już Nowaka` | `⚠️ Jutro o 14:00 masz już Jana Nowaka` |
| ~319-321 | Morning brief z samymi nazwiskami | Dodaj imiona |
| ~324-325 | `Mazur — wysłać ofertę`, `Zieliński — oddzwonić` | `Jan Mazur — wysłać ofertę`, `Piotr Zieliński — oddzwonić` |
| ~339-341 | Evening follow-up: `Kowalski (10:00)`, `Nowak (14:00)`, `Wiśniewski (17:00)` | Dodaj imiona |

#### 2. `docs/implementation_guide_2.md` — testy regresyjne

| Linia | Teraz | Powinno być |
|-------|-------|-------------|
| ~78-92 | Test oczekuje `📋 Nowak, Piaseczno` | `📋 Jan Nowak, Piaseczno` |
| ~96-99 | Test oczekuje `Nowak, Pompa ciepła` | `Jan Nowak, Pompa ciepła` |
| ~150-154 | Test oczekuje `📋 Kowalski — Piłsudskiego` | `📋 Jan Kowalski — Piłsudskiego` |

#### 3. `docs/poznaj_swojego_agenta_v5_FINAL.md` — dokumentacja userowa

| Linia | Teraz | Powinno być |
|-------|-------|-------------|
| ~220-222 | Bot response: `Zapisuję Kowalskiego...` | `Zapisuję Jana Kowalskiego...` |

---

## BUG #2: Specyfikacje techniczne klienta GUBIONE

Agent gubi: moc (kW), metraż domu, metraż dachu, kierunek dachu, zużycie prądu.

**Test:** "Tomasz Kowalski Warszawa Mokotowska 15 PV 8kW dom 160m2 dach 40m2 poludnie zuzycie 500kWh lead z internetu tel 600111222"
**Wynik:** Karta pokazuje tylko "PV" — bez 8kW, bez 160m², bez 40m², bez południe, bez 500kWh

**Test:** "PV-ka szóstka" → Bot zapisał "PV" — zgubił "6kW" z "szóstka"

### Gdzie szukać:
- `shared/claude_ai.py` — prompt do extract_client_data
- `shared/formatting.py` — formatowanie karty klienta
- Sprawdź czy Google Sheets ma kolumny na te dane (moc_kw, metraz_domu, metraz_dachu, kierunek_dachu, zuzycie_pradu)

---

## BUG #3: Format daty ISO zamiast polskiego

Agent wyświetla daty jako "2026-04-10" zamiast wymaganego "10.04.2026 (Piątek)".

**Dotyczy:**
- Karta spotkania: "Data: 2026-04-10" → powinno "10.04.2026 (Piątek)"
- Follow-up: "Następny krok: 2026-04-16" → powinno "16.04.2026 (Czwartek)"

### Gdzie szukać:
- `shared/formatting.py` — format_date(), format_meeting_card()
- `bot/handlers/` — wherever dates are formatted for display

---

## BUG #4: Edit client nie rozpoznawany

"zmień numer Nowaka z Piaseczna na 609888777" → Agent traktuje to jako ADD_CLIENT (odpalił flow duplikatów: "Dodać nowego czy zaktualizować?")

Powinien rozpoznać intent `edit_client` i pokazać stare vs nowe (R5).

### Gdzie szukać:
- `shared/claude_ai.py` — classify_intent prompt, edit_client examples
- `bot/handlers/` — handle_edit_client

---

## BUG #5: "Brakuje:" z pustą listą

Karta dodawania klienta czasem pokazuje "❓ Brakuje:" bez niczego po dwukropku.

### Gdzie szukać:
- `shared/formatting.py` — format_client_card(), sekcja "Brakuje"

---

## WYNIKI RUNDY 6 (dotychczasowe)

| Test | Input | Wynik | Bugi |
|------|-------|-------|------|
| A1 hej | "hej" | ✅ PASS | — |
| A2 co umiesz | "co umiesz?" | ✅ PASS | — |
| A3 add client | "Jan Nowak Piaseczno 601234567 pompa" | ✅ PASS | — |
| A4 day plan | "co mam dziś?" | ✅ PASS | Minor: "Nowak" bez imienia |
| A5 search | "co masz o Mazurze?" | ⚠️ PARTIAL | Brak imienia |
| B1 full add | Tomasz Kowalski + pełne dane | ❌ FAIL | Specyfikacje zgubione, "Brakuje:" puste |
| B2 minimal add | "Zielinski Legionowo 604555666" | ⚠️ PARTIAL | Nie wymaga imienia w "Brakuje" |
| B3 search inflection | "co masz o Nowaku?" | ❌ FAIL | Duplikaty identyczne, brak imion |
| B4 edit | "zmień numer Nowaka" | ❌ FAIL | Rozpoznane jako add_client |
| C1 status podpisał | "Nowak z Piaseczna podpisał" | ⚠️ PARTIAL | Brak imienia, nie pytał o którego |
| C2 status spadł | "Mazur z Radomia spadł" | ⚠️ PARTIAL | Brak starego statusu, "spadł"→"Rezygnuje" zamiast "Odrzucone" |
| D1 meeting | "jutro o 10 spotkanie z Mazurem z Radomia" | ⚠️ PARTIAL | Data ISO, brak imienia |
| D2 wpół do ósmej | "w piątek wpół do ósmej spotkanie z Janem Nowakiem" | ⚠️ PARTIAL | ✅ 07:30 FIXED! Ale imię zgubione |
| G1 chaotic slang | "PV-ka szóstka zona przekręciła..." | ⚠️ PARTIAL | Slang OK, emocje OK, specs zgubione, "szóstka"→brak 6kW |

**Pass rate: 3/14 PASS, 8/14 PARTIAL, 3/14 FAIL = 21% clean pass**

---

## PRIORYTETY NAPRAWY

1. **KRYTYCZNY** — Bug #1: Imiona w agent_system_prompt.md (12+ zmian w jednym pliku)
2. **KRYTYCZNY** — Bug #2: Specyfikacje techniczne gubione (extract_client_data prompt)
3. **WAŻNY** — Bug #3: Format daty ISO → polski
4. **WAŻNY** — Bug #4: edit_client intent nie rozpoznawany
5. **MINOR** — Bug #5: "Brakuje:" puste

**Szacunek:** Bug #1 to ~30 minut pracy (edycja przykładów w promptach). Bug #2-4 wymagają zmian w kodzie Python.
