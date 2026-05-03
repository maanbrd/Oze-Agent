# Sesja 1 — "Regresja 10.04"

_Data: 10.04.2026 wieczór. Tester: Claude Cowork (przez Telegram). Cel: sprawdzić czy decyzje produktowe z 10.04 wieczór faktycznie żyją w kodzie bota._

## Zasady weryfikacji (dwa checkpointy)

Każdy test który powoduje zapis ma **dwa checkpointy**:

1. **Telegram** — karta bota, format odpowiedzi, brak niechcianych pytań
2. **Google Sheets** — stan wiersza klienta po kliknięciu `[Tak]`

Po każdym zapisie: otwieram arkusz Google Sheets w drugim oknie/tabie → znajduję świeżo dodany/edytowany wiersz → kopiuję jego stan do raportu → porównuję z expected.

**Verdict:** ✅ PASS jeśli oba checkpointy OK / ⚠️ PARTIAL jeśli jeden OK a drugi lekko nie / ❌ FAIL jeśli któryś twardo nie.

---

## Plan testów (10 testów)

### Test 1 — specy do Notatek (średnia wiadomość)
**Input:** `Jan Kowalski Warszawa Piłsudskiego 12, 600123456, pompa ciepła, dom 120m2, dach 30m wschód`

**Expected Telegram:**
- Karta z Produktem `Pompa ciepła`
- `Notatki: dom 120m², dach 30m² wsch.` (lub podobne, specy w Notatkach)
- `Brakuje:` zawiera co najwyżej `źródło leada` — NIE zawiera metrażu/dachu/kierunku
- BRAK pytania o następny kontakt
- Przycisk [Tak]/[Zapisz bez]

**Expected Sheets (po [Tak]):**
- Wiersz: Jan Kowalski | 600 123 456 | Piłsudskiego 12 | Warszawa | Pompa ciepła | Nowy lead | Notatki zawiera `dom 120m²` i `dach 30m² wsch.`

---

### Test 2 — specy do Notatek (długa wiadomość)
**Input:** `Byłem u Nowaka, Leśna 5 Piaseczno, 601234567, zainteresowany fotowoltaiką 8kW, dom 160m², dach 40m² południe, zużycie 4500 kWh rocznie, chce wycenę w przyszłym tygodniu`

**Expected Telegram:**
- Produkt: `PV 8kW` lub `Fotowoltaika 8kW`
- `Notatki:` zawiera `dom 160m²`, `dach 40m² płd.`, `zużycie 4500 kWh`, `chce wycenę w przyszłym tygodniu`
- `Brakuje:` co najwyżej `imię`, `źródło leada`
- BRAK pytania o next contact

**Expected Sheets:**
- Produkt zawiera `8kW`
- Notatki zawiera wszystkie 4 fragmenty specy/kontekstu
- `Zużycie prądu` NIE istnieje jako osobna kolumna (albo jest puste)

---

### Test 3 — Brakuje bez metrażu (średnia)
**Input:** `Dodaj Adam Wiśniewski, Legionowo, magazyn energii`

**Expected Telegram:**
- `Brakuje:` ma zawierać co najwyżej: `adres (ulica)`, `telefon`, `źródło leada`
- NIGDY: `metraż domu`, `metraż dachu`, `kierunek dachu`, `zużycie prądu`

---

### Test 4 — Brakuje bez metrażu (minimalna)
**Input:** `Nowy klient Piotr Zieliński z Radomia`

**Expected Telegram:**
- `Brakuje:` ma zawierać: `adres`, `telefon`, `produkt`, `źródło leada`
- NIGDY metrażu/dachu/zużycia

---

### Test 5 — brak pytania o next_contact (karta)
**Input:** `Zapisz: Tomasz Lewandowski, Krakowska 8, Kielce, PV 6kW, 602345678`

**Expected Telegram:**
- Pełna karta klienta
- NIE ma wiadomości typu `Kiedy następny kontakt?`, `Ustawić follow-up?`, `Kiedy zadzwonisz?`
- Sam pasek `Zapisać?` z [Tak] i [Zapisz bez]

---

### Test 6 — brak next_contact po [Tak]
**Akcja:** kliknij [Tak] na karcie z Testu 5

**Expected Telegram:**
- `✅ Zapisane.` — koniec
- NIE ma pytania o next contact
- NIE ma drugiej wiadomości typu "Nie ma nic do potwierdzenia."

**Expected Sheets:**
- Wiersz Tomasz Lewandowski z Produktem zawierającym `6kW`

---

### Test 7 — moc doklejona do produktu
**Input:** `Dodaj Krzysztof Dąbrowski Wrocław, Polna 3, 603456789, pompa ciepła 12kW`

**Expected Telegram:**
- Produkt: `Pompa ciepła 12kW`
- Notatki: pusto albo drobne

**Expected Sheets (po [Tak]):**
- Kolumna Produkt = `Pompa ciepła 12kW` (lub `Pompa ciepła 12 kW`)
- Moc NIE ląduje w osobnej kolumnie

---

### Test 8 — R4 Krzywiński disambiguation
**Input:** `co mam o Krzywińskim`

**Expected Telegram:**
- Bot wykrywa że są dwa Mariusze Krzywińscy
- Prosi o wybór: "Którego Krzywińskiego masz na myśli?" albo pokazuje listę z miastami
- NIGDY nie pokazuje jednego losowego Krzywińskiego bez disambiguation

---

### Test 9 — R4 search po mieście
**Input:** `pokaż Mariusza Krzywińskiego z Marek`

**Expected Telegram:**
- Bot pokazuje JEDNEGO konkretnego Krzywińskiego z danego miasta
- Żadnej disambiguation, bo miasto jest jednoznaczne

---

### Test 10 — R4 edit po mieście
**Input:** `dodaj notatkę do Mariusza Krzywińskiego z Wołomina: prosi o telefon po południu`

**Expected Telegram:**
- Bot dodaje notatkę do KONKRETNEGO Krzywińskiego (drugie miasto)
- NIE tworzy nowego klienta
- Pokazuje karta z propozycją zmiany, [Tak] / [Nie]

**Expected Sheets (po [Tak]):**
- Wiersz Krzywiński z miasta drugiego ma w Notatki nowy fragment `prosi o telefon po południu`
- Wiersz Krzywiński z miasta pierwszego bez zmian

---

## Wyniki

_(wypełniam na żywo w trakcie sesji)_

| # | Telegram | Sheets | Verdict | Notatki |
|---|----------|--------|---------|---------|
| 1 | Karta z "Dodatkowe info: dom 120m², dach 30m², wschód" + pyta "Kiedy następny kontakt?" | Row 14: Jan Kowalski, 600123456, Warszawa, Piłsudskiego 12, **Status PUSTY**, Pompa ciepła, **Notatki PUSTE**, 2026-04-10 | ❌ FAIL | Specy znikają między kartą a Sheets (Bug #11), Status nie ustawiony (Bug #12), next_contact prompt nadal jest (Bug #13) |
| 2 | Karta: `Nowak`, Leśna 5, Piaseczno, `PV` (BEZ 8kW!), `Następny krok: 17.04.2026 (piątek)`, `Dodatkowe info: dom 160m², dach 40m², moc 8kW, zużycie 4500 kWh, klient chce wycenę`, `Brakuje: Źródło pozyskania` | Row 15: Nowak, 601234567, Piaseczno, Leśna 5, **Status PUSTY**, **PV** (bez moc), **Notatki PUSTE**, 2026-04-10, , **2026-04-17** (ISO format!) | ❌ FAIL | Bug #11 potwierdzony (4 specy tracone), Bug #12 Status pusty, Bug #14 moc nie w Produkcie, Bug #15 data ISO zamiast DD.MM.YYYY |
| 3 | Karta: `Adam Wiśniewski, Legionowo`, `Magazyn energii`, `Brakuje: Telefon, Adres, Źródło pozyskania`, `Kiedy następny kontakt?` | Row 16: Adam Wiśniewski, , , Legionowo, , **Status PUSTY**, Magazyn energii, , 2026-04-10 | ⚠️ PARTIAL | Core criterium PASS (Brakuje bez metrażu). Ale Bug #12 (Status pusty) i Bug #13 (next_contact prompt) aktywne. Imię pełne ✅ |
| 4 | Karta: `Piotr Zieliński, Radom`, `Brakuje: Telefon, Adres, Produkt, Źródło pozyskania`, `Kiedy następny kontakt?` | Row 17: Piotr Zieliński, , , Radom, , **Status PUSTY**, , , 2026-04-10 | ⚠️ PARTIAL | Core PASS (Brakuje bez metrażu ✅). Bug #12 + Bug #13 aktywne. |
| 5 | Karta: `Tomasz Lewandowski, Krakowska 8, Kielce`, **`PV`** (bez 6kW!), `Tel. 602 345 678`, `Dodatkowe info: moc: 6kW`, `Brakuje: Źródło pozyskania`, **`Kiedy następny kontakt?`** | — (nie sprawdzamy, Test 6 sprawdza Sheets) | ❌ FAIL | Bug #13 aktywne (pytanie o next_contact w karcie). Bug #14 aktywne (PV zamiast PV 6kW). |
| 6 | Po [Zapisz] → `✅ Zapisane.` 23:21 — **BRAK** drugiej wiadomości o next_contact ✅ | Row 18: Tomasz Lewandowski, 602345678, , Kielce, Krakowska 8, **Status PUSTY**, **PV** (bez 6kW), **Notatki PUSTE**, 2026-04-10 | ⚠️ PARTIAL | Core criterium PASS (brak promptu po zapisie ✅). Ale Bug #12 (Status) + Bug #14 (PV bez 6kW) aktywne. |
| 7 | Karta: `Krzysztof Dąbrowski, Polna 3, Wrocław`, **`Pompa ciepła`** (bez 12kW!), `Tel. 603 456 789`, `Dodatkowe info: moc: 12kW`, `Brakuje: Źródło pozyskania`, `Kiedy następny kontakt?` | Row 19: Krzysztof Dąbrowski, 603456789, , Wrocław, Polna 3, **Status PUSTY**, **Pompa ciepła** (bez 12kW), **Notatki PUSTE**, 2026-04-10 | ❌ FAIL | Bug #14 potwierdzony 3x — moc ląduje w Dodatkowe info zamiast w nazwie Produktu. Bug #12 + #13 też aktywne. |
| 8 | Bot odpowiada: **`Nie mam "Kriwiński" w bazie.`** — NIE ma disambiguation, bot twierdzi że nie ma żadnego Krzywińskiego | (search, brak zapisu) | ❌ FAIL | **Bug #16 KRYTYCZNY** — LLM lemmatyzuje "Krzywińskim" do BŁĘDNEJ formy "Kriwiński" (brakuje "zyw") i twierdzi że nie ma klienta, chociaż w bazie są DWA wiersze "Mariusz Krzywiński" (Marki + Wołomin). |
| 9 | Bot odpowiada: **`Nie mam "Mariusz Spuknowski" w bazie.`** — halucynacja zupełnie innego nazwiska | (search, brak zapisu) | ❌ FAIL | Bug #16 potwierdzony w ekstremalnej postaci — LLM produkuje nazwisko "Spuknowski" z "Krzywińskiego z Marek". Kompletnie zepsuty lemmatyzer/search pipeline. |
| 10 | Karta bez disambiguation: `Mariusz Krzywinski — notatki: Dodaję: "Prosi o telefon po południu." Zapisać?` + [Tak]/[Nie]. BRAK miasta w karcie, user nie wie do którego wiersza zapisuje. | Row 6 (Marki) Notatki dopisane: `...; Prosi o telefor...` ❌. Row 11 (Wołomin) **bez zmian** ❌ | ❌ FAIL | **Bug #17 KRYTYCZNY** — add_note ignoruje miasto w inpucie. User wyraźnie powiedział "z Wołomina" a notatka poszła do Marek. Brak disambiguation w karcie potwierdzenia — user nie mógł skorygować. |

---

## Nowe bugi / obserwacje

**Bug #11 — Specy znikają między kartą a Sheets (KRYTYCZNY).**
Bot extractuje specy z inputu i wyświetla je w karcie potwierdzenia jako "Dodatkowe info: dom 120m², dach 30m², wschód". Po kliknięciu [Zapisz] kolumna Notatki w Sheets jest PUSTA. Dane są tracone cicho, bez żadnego ostrzeżenia. User widzi w karcie że wszystko jest OK, klika [Zapisz] i nie ma pojęcia że połowa danych zniknęła. Musimy naprawić pipeline save albo naprawić rendering karty żeby nie obiecywał czegoś czego nie zapisuje.

**Bug #12 — Domyślny Status "Nowy lead" nie jest ustawiany.**
Nowy klient w wierszu 14 ma pustą kolumnę Status. Powinno być "Nowy lead" automatycznie.

**Bug #13 — Pytanie "Kiedy następny kontakt?" nadal w karcie add_client.**
Decyzja z 10.04 wieczór (R4 usunięte) NIE żyje w kodzie bota. Dokumentacja została zaktualizowana (agent_system_prompt.md, agent_behavior_spec_v5.md, poznaj_swojego_agenta_v5_FINAL.md), ale kod generujący kartę nadal wstawia `📅 Kiedy następny kontakt?`.

**Obserwacja — pole w karcie nazywa się "Dodatkowe info", nie "Notatki".**
Mniejsza kwestia ale mylne dla usera. Spec mówi żeby specy szły do Notatek. Bot tworzy pole o innej nazwie ("Dodatkowe info") i mapuje je do kolumny Notatki — ale obecnie ten mapping jest zepsuty (Bug #11).

**Bug #14 — Moc produktu nie jest doklejana do nazwy Produktu.**
Test 2 input miał "fotowoltaiką 8kW". Bot zamiast produktu "PV 8kW" lub "Fotowoltaika 8kW" zwraca sam "PV", a moc ląduje w "Dodatkowe info: moc: 8kW". W Sheets kolumna Produkt = "PV" (bez moc). Decyzja z 10.04 mówiła: moc doklejona do nazwy produktu jeśli parsing pozwala. Obecnie parsing ZNAJDUJE moc, ale ją izoluje do osobnego pola zamiast doklejić.

**Bug #15 — Format daty "Następny krok" regresja do ISO.**
Test 2 zapisał w kolumnie Następny krok wartość `2026-04-17` zamiast `17.04.2026 (Piątek)`. To jest regresja Bug #3 który wcześniej był zamknięty. Bot w karcie pokazuje dobrze ("17.04.2026 (piątek)") ale do Sheets pisze ISO — więc problem jest w warstwie zapisu, nie rendering.

**Bug #16 — KRYTYCZNY. Search LLM halucynuje nazwisko klienta.**
Test 8 input: `co mam o Krzywińskim` → bot odpowiada `Nie mam "Kriwiński" w bazie.` (LLM zgubił "zyw" w lemacie).
Test 9 input: `pokaż Mariusza Krzywińskiego z Marek` → bot odpowiada `Nie mam "Mariusz Spuknowski" w bazie.` (LLM wyhalucynował zupełnie inne nazwisko).
W obu przypadkach w bazie są DWA wiersze "Mariusz Krzywiński" (Marki w wierszu 6 i Wołomin w wierszu 11), które bot powinien znaleźć. Pipeline search jest kompletnie zepsuty dla tego nazwiska — prawdopodobnie LLM dostaje instrukcję "wyekstrahuj nazwisko z wiadomości", a na "Krzywińskim"/"Krzywińskiego" halucynuje błędną formę podstawową zamiast zrobić zwykłe odwrócenie odmiany. R4 (Identyfikacja klienta) jest złamana na najbardziej podstawowym poziomie.

**Bug #17 — KRYTYCZNY. add_note ignoruje miasto w inpucie i nie pokazuje disambiguation.**
Test 10 input: `dodaj notatkę do Mariusza Krzywińskiego z Wołomina: prosi o telefon po południu`. Bot wykrył `add_note` intent (dobrze, Bug #6 tu NIE zadziałał) i wyświetlił kartę potwierdzenia — ale bez miasta, bez disambiguation. Po [Tak] notatka została dopisana do wiersza 6 (Krzywiński z **Marek**), chociaż user wyraźnie powiedział "z **Wołomina**". Wiersz 11 (Wołomin) nie został dotknięty.
Dwa problemy w jednym: (1) parser city constraint ignoruje miasto, (2) karta potwierdzenia nie pokazuje miasta/telefonu klienta więc user nie ma jak wyłapać błędu przed kliknięciem [Tak]. To jest scenariusz w którym bot cicho psuje dane.

---

## Podsumowanie Sesji 1 — "Regresja 10.04"

**Wynik:** 0/10 PASS, 3/10 PARTIAL, 7/10 FAIL.

**Wyniki per test:**

| Test | Co sprawdza | Verdict |
|------|-------------|---------|
| 1 | specy do Notatek (średnia) | ❌ FAIL |
| 2 | specy do Notatek (długa) | ❌ FAIL |
| 3 | Brakuje bez metrażu (średnia) | ⚠️ PARTIAL |
| 4 | Brakuje bez metrażu (minimalna) | ⚠️ PARTIAL |
| 5 | brak next_contact (karta) | ❌ FAIL |
| 6 | brak next_contact (po [Tak]) | ⚠️ PARTIAL |
| 7 | moc doklejona do produktu | ❌ FAIL |
| 8 | R4 disambiguation Krzywińskich | ❌ FAIL |
| 9 | R4 search po mieście (Marki) | ❌ FAIL |
| 10 | R4 edit po mieście (Wołomin) | ❌ FAIL |

**Nowe bugi znalezione w sesji:** Bug #11, #12, #13, #14, #15, #16, #17.

**Wnioski co do decyzji z 10.04 wieczór:**

1. **Specy → Notatki** (decyzja 1). Bot wykonuje parsing (Bug #11: specy widoczne w karcie jako "Dodatkowe info") i mapuje pole "Dodatkowe info" → Notatki, ale **mapping jest zepsuty** — w Sheets Notatki są puste. Decyzja produktowa jest częściowo zaimplementowana: parser OK, rendering OK, ale warstwa zapisu gubi dane. **Decyzja NIE ŻYJE w pełni w kodzie.**

2. **Moc → doklejona do produktu** (decyzja 2). Bot parsuje moc (widzi "8kW", "6kW", "12kW"), ale izoluje do "Dodatkowe info" zamiast skleić z nazwą produktu. W Sheets Produkt = "PV" / "Pompa ciepła" bez mocy. **Decyzja NIE ŻYJE w kodzie** — brak logiki doklejania.

3. **R4 next_contact USUNIĘTA** (decyzja 3). W 4 na 4 add_client testach (T1, T2, T4, T5) bot nadal wstawia `📅 Kiedy następny kontakt?` do karty. Dokumentacja została zaktualizowana, ale kod generujący kartę jej nie czytał. **Decyzja NIE ŻYJE w kodzie** — prompt/template nadal ma to pole.

4. **R4 Identyfikacja klienta (imię + nazwisko + miasto)** (decyzja 3, nowa definicja R4). Tests 8/9/10 to 3 kolejne FAIL-e tej reguły:
   - T8/T9: LLM halucynuje nazwisko ("Kriwiński", "Spuknowski") zamiast zrobić lemmatyzację
   - T10: add_note ignoruje miasto jako constraint
   **Decyzja NIE ŻYJE w kodzie** — więcej niż nie żyje, R4 jest zepsuta na bardziej podstawowym poziomie (LLM halucynuje nazwisko).

**Co działa** (z pozytywów):
- add_note intent wykrywany poprawnie (Bug #6 tu NIE zadziałał w T10)
- Polski slang ("pompa ciepła", "magazyn energii", "fotowoltaika") jest rozpoznawany jako produkt
- Brakuje list jest czyste od metraż/dach/kierunek/zużycia — decyzja 1 ZADZIAŁAŁA w warstwie rendering (chociaż nie w warstwie zapisu)
- `✅ Zapisane.` po [Zapisz] jest krótkie, brak drugiej wiadomości "nie ma nic do potwierdzenia" (T6 core PASS)

**Lista bugów do Claude Code na następną sesję (priorytet malejący):**

1. **Bug #16** (KRYTYCZNY) — search pipeline halucynuje nazwiska. Prawdopodobnie prompt LLM każe "wyekstrahować kanoniczną formę nazwiska", a LLM to robi losowo zamiast deterministycznie. Rozwiązanie: użyć biblioteki do odmiany polskiej (morfeusz? pyMorfologik?) albo przekazać LLM surowe tokeny + listę nazwisk w bazie i każ MATCHOWAĆ, nie GENEROWAĆ.
2. **Bug #17** (KRYTYCZNY) — add_note ignoruje city constraint. Fix: (a) parser city constraint z inputu, (b) obowiązkowe miasto + telefon w karcie potwierdzenia add_note, (c) disambiguation gdy wiele dopasowań.
3. **Bug #11** (KRYTYCZNY) — pipeline save gubi "Dodatkowe info" → Notatki mapping. Fix warstwa zapisu — powinna serializować "Dodatkowe info" do kolumny Notatki.
4. **Bug #13** — usunąć prompt "📅 Kiedy następny kontakt?" z template karty add_client. Grep w bocie za "Kiedy następny kontakt" lub `📅`.
5. **Bug #14** — dodać logikę doklejania mocy do nazwy produktu po parsowaniu (jeśli parser znalazł moc_kw i produkt → produkt = f"{produkt} {moc_kw}kW").
6. **Bug #12** — ustawić domyślny Status = "Nowy lead" w add_client pipeline.
7. **Bug #15** — format daty "Następny krok" regresja do ISO. Warstwa zapisu dla kolumny K musi formatować jako DD.MM.YYYY (Dzień tygodnia).

**Priorytet produktowy:** Bugi #11, #13, #14, #16 blokują kluczową wartość produktu (zapisywanie danych zgodne z tym co bot obiecuje + wyszukiwanie po nazwisku). Bugi #12, #15, #17 są ważne ale mogą poczekać jeden sprint.

---

## Notatka dla Sesji 2 "Polowanie"

Plan Sesji 2 był skupiony na bugach #6-#10 (z backlogu). Po wynikach Sesji 1 pojawiły się dwa NOWE krytyczne bugi (#16, #17) w okolicy search/add_note, które pokrywają się tematycznie z Bug #6 (add_note routing). Do przemyślenia: czy Sesja 2 nie powinna zostać przepisana na fokus "search + add_note + R4 identyfikacja".
