# OZE-Agent — Macierz intencji MVP

_Ostatnia aktualizacja: 11.04.2026_
_Status: blueprint implementacyjny po Sesji 1 Regresja (10.04 wieczór)_
_Owner: Maan_

Ten dokument definiuje **pełny kontrakt intencji MVP** — co agent ma robić w Sheets i Kalendarzu dla każdej rozpoznanej intencji, w jakiej kolejności, z jakimi potwierdzeniami. Jest to zamrożony blueprint produktowy — implementacja idzie fazowo, ale **projekt musi być kompletny od dnia 1**, żeby nie robić drugiego razu pracy jak dodajemy Kalendarz.

Jeśli coś w kodzie nie zgadza się z tym dokumentem → zmienia się kod. Jeśli coś w produkcie ma być zmienione → najpierw edytujesz ten plik, potem kod.

---

## 1. Zasada fundamentalna: Sheets = baza, Kalendarz = akcja

**Google Sheets** to statyczna baza klientów. Handlowiec do niej wchodzi rzadko — głównie gdy coś sprawdza, rozlicza się z szefem, albo eksportuje dane. Sheets mówi **co** wiemy o kliencie.

**Google Calendar** to codzienne narzędzie robocze. Handlowiec otwiera go wielokrotnie dziennie: żeby sprawdzić gdzie jechać, komu zadzwonić, kiedy wrócić do oferty. Calendar mówi **co** trzeba zrobić **kiedy** i **z kim**.

**Reguła dual-write:** każda informacja zapisana w Sheets musi mieć swoje odzwierciedlenie w Kalendarzu — jako wydarzenie (spotkanie, telefon, oferta, follow-up dokumentowy) w odpowiednim momencie na osi czasu. Klient przechodzi przez lejek sprzedażowy **wraz z przejściami w Kalendarzu**. Status w Sheets to skutek, nie przyczyna — przyczyną jest wydarzenie, które się odbyło lub się odbędzie.

**Implikacja techniczna:** każda intencja mutująca stan (add_client, change_status, add_meeting, add_note gdy note implikuje telefon) zawsze produkuje **parę**: wiersz w Sheets + wydarzenie w Kalendarzu. Nigdy jedno bez drugiego.

**Implikacja produktowa:** nie wydajemy beta-testerom agenta który tylko pisze do Sheets. Dla handlowca to nic nie zmienia — musiałby i tak ręcznie kopiować rzeczy do kalendarza. Agent bez Kalendarza to notatnik, nie asystent.

**Implikacja dla fazowania:** Sheets implementujemy pierwszy (to baza), ale **każda intencja Sheets od razu zawiera stub Calendar** (parametr `calendar_event: CalendarEventDraft | None`). W Phase A implementujemy tylko Sheets-side i zwracamy stub. W Phase B podpinamy Calendar API pod te same kontrakty, bez przerabiania intencji. Tworzenie stuba zajmuje 5 minut na intencję, oszczędza tygodnie przerabiania logiki później.

---

## 2. Zakres MVP — intencje MVP

Po Sesji 1 Regresja, decyzja produktowa: **MVP zawiera tylko intencje z tabeli poniżej**, nie wszystkie z briefu v5. Resztę odkładamy świadomie (sekcja 8).

| # | Intencja | Co robi | Czy mutuje Sheets | Czy mutuje Kalendarz |
|---|---|---|---|---|
| 1 | `add_client` | Dodaje nowego klienta | TAK (nowy wiersz) | TAK (Nowy lead → wydarzenie "lead" lub pierwszy follow-up jeśli user poda datę) |
| 2 | `show_client` | Pokazuje kartę klienta | NIE (read-only) | NIE (read-only) |
| 3 | `add_note` | Dodaje notatkę do istniejącego klienta | TAK (append do kolumny Notatki) | CZASAMI (jeśli note implikuje telefon/follow-up → compound z `create_call_event`) |
| 4 | `change_status` | Zmienia status w lejku | TAK (kolumna Status) | TAK (wydarzenie zmiany statusu + prompt o next action) |
| 5 | `add_meeting` | Tworzy wydarzenie spotkanie/telefon/oferta/follow-up | TAK (update Data ostatniego/następnego) | TAK (nowe wydarzenie, 1 z 4 typów) |
| 6 | `show_day_plan` | Pokazuje plan dnia | NIE (read-only) | NIE (read-only — czyta z Kalendarza) |

**Kluczowe: intencje `show_*` czytają z Kalendarza, nie z Sheets.** Plan dnia nie pochodzi z Sheets — pochodzi z Calendar API query "wydarzenia na dziś". To jest konsekwencja zasady "Calendar = akcja".

---

## 3. R4 — Identyfikacja klienta

Wszystkie intencje które pracują na istniejącym kliencie (`show_client`, `add_note`, `change_status`, `add_meeting` gdy spotkanie z konkretną osobą) muszą **najpierw zidentyfikować klienta**.

**Reguła R4 (redefinicja 10.04.2026):** identyfikacja klienta = `imię` + `nazwisko` + `miasto`. Nigdy po samym nazwisku. Polska ma za dużo "Kowalskich".

**Tryby identyfikacji:**

| Tryb | Input | Zachowanie agenta |
|---|---|---|
| **Full match** | "Jan Kowalski z Warszawy" | Jedno dopasowanie → procedury normalnie, bez pytania |
| **Imię + nazwisko, brak miasta** | "Jan Kowalski" | Jeśli 1 wynik → kontynuuj. Jeśli ≥2 → multi-match disambiguation z listą |
| **Samo nazwisko** | "Kowalski" | Zawsze multi-match disambiguation, nawet jeśli 1 wynik (bo user nie dał sygnału że wie którego) |
| **Imię + miasto** | "Jan z Radomia" | Wyszukaj w kolumnie Miasto, jeśli 1 wynik → kontynuuj |
| **Fuzzy** | "Kowalsky" (literówka) | Fuzzy match z progiem podobieństwa, prezentacja z "Miałeś na myśli Kowalskiego?" |
| **Polska odmiana** | "u Krzywińskim" / "Krzywińskiego" | Agent MUSI sprowadzić do mianownika przed wyszukaniem (`"Krzywiński"`). To jest Bug #16 — obecnie łamie się katastrofalnie. |

**R4 nie stosuje się do `add_client`** — bo to tworzy klienta, nie identyfikuje istniejącego. Ale `add_client` ma swój własny kontrakt minimalnych pól (imię + nazwisko + miasto jako pola obowiązkowe, bo to dane które identyfikują klienta w przyszłości).

**R4 nie stosuje się do `show_day_plan`** — bo to lista wszystkich wydarzeń dnia, nie operacja na konkretnym kliencie.

---

## 4. Kontrakty intencji (6 × parser → karta → Sheets → Kalendarz → R4 → gap)

Każda intencja ma 6 sekcji:
1. **Parser** — co LLM wyciąga z inputu użytkownika, jakie są pola wymagane vs opcjonalne
2. **Karta potwierdzenia** — dokładnie co agent pokazuje przed zapisem (R1)
3. **Efekt w Sheets** — które komórki się zmieniają
4. **Efekt w Kalendarzu** — jakie wydarzenie powstaje/aktualizuje się
5. **Zachowanie R4** — jak identyfikowany jest klient
6. **Gap dziś** — co w obecnym kodzie łamie ten kontrakt (bug z Sesji 1 lub starszy)

### 4.1. `add_client` — dodanie klienta

**Parser:**
- Pola obowiązkowe: `imię`, `nazwisko`, `miasto`
- Pola opcjonalne na karcie: `telefon`, `email`, `adres` (ulica + numer), `produkt` (typ bez mocy), `źródło leada`, `data następnego kontaktu` (jeśli user sam poda — w przeciwnym razie po commit agent zadaje `next_action_prompt`, sekcja 5.1)
- Pola do Notatek: wszystko inne co rozpoznane — `moc PV/pompy/magazynu`, `metraż domu`, `metraż dachu`, `kierunek dachu`, `zużycie kWh`, `typ dachu`, `napięcie`, kontekst emocjonalny, luźne komentarze
- Typ produktu: `PV` / `Pompa ciepła` / `Magazyn energii` / `PV + Magazyn` / kombinacje. **Nigdy moc w tej kolumnie.** (Klimatyzacja została świadomie wycięta z MVP — OZE-Agent nie obsługuje tego segmentu.)

**Karta potwierdzenia:**

```
📋 Zapisuję klienta:
Jan Kowalski, Piłsudskiego 12, Warszawa
Produkt: PV
Tel. 600 123 456
Notatki: moc PV 8kW, dom 160m², dach 40m² płd., chce wycenę
❓ Brakuje: email, źródło leada

[✅ Zapisać] [➕ Dopisać] [❌ Anulować]
```

**Zasady karty:**
- `Brakuje:` zawiera **tylko** pola opcjonalne-ale-ważne: email, źródło, telefon, adres, produkt. **Nigdy** nie listuje metraż/dach/kierunek — te lecą do Notatek bez wspomnienia w `Brakuje:`.
- Jeśli user podał datę follow-upu ("wyślę za tydzień", "dzwonię jutro") → parse, zapisz do Notatek, dodaj wydarzenie w Kalendarzu na podaną datę.
- **Po committed add_client agent zadaje `next_action_prompt`** (sekcja 5.1) — jedno wolnotekstowe pytanie "Co dalej z tym klientem? Spotkanie, telefon, odłożyć na później?" z możliwością Anulowania. Handlowiec odpowiada prozą; jeśli odpowiedź zawiera datę/typ akcji → agent startuje `add_meeting`/`phone_call`/`doc_followup` flow. Jeśli handlowiec pisze "nie wiem jeszcze" → flow się kończy bez zakłębienia.

**Efekt w Sheets (po `✅ Zapisać`):**
- Nowy wiersz w arkuszu
- Kolumny: `A=Imię nazwisko`, `B=Telefon`, `C=Email`, `D=Miasto`, `E=Adres`, `F=Status="Nowy lead"`, `G=Produkt` (tylko typ), `H=Notatki` (wszystko inne, w tym moc/metraż/dach), `I=Data pierwszego kontaktu=dziś`, `J=Data ostatniego kontaktu=dziś`, `K=Następny krok` (z dropdowna, pusty chyba że user podał), `L=Data następnego kroku` (pusta chyba że user podał), `M=Źródło pozyskania` (jeśli parser wyciągnął), `N/O=Zdjęcia` (puste — Phase 4), `P=ID wydarzenia Kalendarz` (puste — Faza B)

**Efekt w Kalendarzu (po [Tak]):**
- **Jeśli user podał datę follow-upu** → wydarzenie typu `doc_followup` lub `phone_call` (zależnie czy użył słowa "zadzwonię" vs "wyślę") na podaną datę.
- **Jeśli user NIE podał daty follow-upu** → brak wydarzenia w Kalendarzu (faza A: nie wymuszamy follow-upu; faza B: opcjonalnie domyślny "sprawdź lead" +3 dni — do decyzji).

**R4:** nie stosuje się (tworzymy nowego).

**Gap dziś:**
- Bug #14 (Sesja 1): moc obecnie nie była sklejana z produktem (próbowała → parser nie radził sobie z inflacją). **Ten bug znika razem z decyzją "moc → Notatki"** — nie trzeba go naprawiać, trzeba zmienić kontrakt parsera i system prompt.
- Bug #15 (Sesja 1): brakujące pola na karcie czasem listują `dom 160m²` jako brakujące. Trzeba wyraźnie w system promptie: `Brakuje:` to tylko email/źródło/tel/adres/produkt, NIGDY specs techniczne.
- Stare Bug #2 (regres po 10.04): parser czasem próbuje stworzyć kolumnę `moc_kw` mimo że nie ma takiej w schemacie. Musi być wyciągnięte z kodu parsera razem z decyzją moc→Notatki.

---

### 4.2. `show_client` — karta klienta

**Parser:**
- Pola obowiązkowe: identyfikator (imię+nazwisko+miasto lub fuzzy+R4)
- Pola opcjonalne: żadne

**Karta potwierdzenia:** NIE MA. To read-only, R1 nie stosuje się. Po rozpoznaniu intencji agent wykonuje search i od razu zwraca kartę wyniku.

**Format karty wyniku (single match):**

```
📋 Jan Kowalski — Piłsudskiego 12, Warszawa
Produkt: PV
Tel. 600 123 456
Email: jan@example.pl
Status: Oferta wysłana
Ostatni kontakt: 15.04.2026 (Środa)
Następny krok: 18.04.2026 (Sobota) 10:00
Notatki: moc PV 8kW, dom 160m², dach 40m² płd., chce wycenę, żona się boi
```

**Zasady karty:**
- Linia `Produkt:` zawiera tylko typ produktu, bez mocy i bez liczb.
- `Ostatni kontakt` i `Następny krok` w formacie `DD.MM.YYYY (Dzień tygodnia)` — nigdy Excel serial, nigdy ISO.
- Notatki zawsze jako ostatnia linia, w całości (bez skracania — handlowiec chce widzieć co wpisał).
- Brak `Wiersz: X`, brak `_row`, brak żadnych ID systemowych.

**Multi-match:**

```
Mam 3 Kowalskich:
1. Jan Kowalski — Warszawa (Oferta wysłana)
2. Piotr Kowalski — Piaseczno (Nowy lead)
3. Adam Kowalski — Legionowo (Podpisany)
Którego?
```

Po wyborze (numer lub imię+miasto) → pokazuje pełną kartę jak single match.

**Efekt w Sheets:** brak (read-only).
**Efekt w Kalendarzu:** brak (read-only).

**R4:** pełna reguła (samo nazwisko → zawsze multi-match disambiguation).

**Gap dziś:**
- Bug #16 (Sesja 1): polska odmiana gubi klienta katastrofalnie. "u Krzywińskim" → agent wymyśla "Kriwiński" i nie znajduje nikogo. Musi istnieć lematyzacja **przed** wyszukaniem — nie próba dopasować jak jest.
- Stary Bug (Sesja 1 Test 6): Excel serial date leci do karty jako `46120` zamiast `11.04.2026 (Sobota)`. Formatowanie dat jest po stronie agenta, nie po stronie Sheets — trzeba konwertować w `format_client_card()`.

---

### 4.3. `add_note` — notatka do istniejącego klienta (+ compound)

**Parser:**
- Pola obowiązkowe: identyfikator klienta (R4), treść notatki
- Detekcja compound: jeśli notatka zawiera wzorzec sygnalizujący telefon/follow-up ("zadzwonić", "zadzwoni", "trzeba oddzwonić", "wrócić do", "follow-up", "dopytać"), agent sugeruje dodatkowo utworzenie wydarzenia `phone_call` w Kalendarzu

**Karta potwierdzenia:**

**Flow A — notatka czysta (bez komponentu czasowego):**

Input: `"Marek Kowalski z Wyszkowa ma duży dom"`
Parser: intencja = `add_note`, client = `Marek Kowalski + Wyszków`, treść = `"ma duży dom"`, komponent czasowy = **nie ma**.

Karta:
```
📝 Marek Kowalski, Wyszków:
dodaj notatkę "ma duży dom"?

[✅ Zapisać] [➕ Dopisać] [❌ Anulować]
```

Po `Zapisać` → tylko Sheets write (append do Notatek, update J=Data ostatniego kontaktu), Calendar-side brak. `next_action_prompt` się **nie** pojawia (czysta notatka jest zamkniętym aktem).

**Flow B — notatka + komponent czasowy (compound):**

Input: `"jadę do Marka Jóźwiaka na spotkanie w czwartek o 17"`
Parser: intencja = compound `add_note + add_meeting`, client = `Marek Jóźwiak`, treść notatki = `"jadę na spotkanie"`, event = `in_person`, data = najbliższy czwartek, godzina = 17:00.

Karta zbiorcza:
```
📝 Marek Jóźwiak, Warszawa:
• Notatka: "jadę na spotkanie"
• Calendar: 16.04.2026 (Czwartek) 17:00 — spotkanie u klienta
• Status: Nowy lead → Spotkanie umówione (auto-przejście)

[✅ Zapisać] [➕ Dopisać] [❌ Anulować]
```

Po `Zapisać` → atomowy commit: Sheets (notatka + status + `K=Następny krok`) + Calendar (wydarzenie `in_person`). Żadnej klikaniny 3 razy — jeden `Zapisać` zamyka kompletny compound.

**Flow B — compound bez godziny (np. user mówi tylko o telefonie "w piątek"):**

Input: `"trzeba do niego oddzwonić w piątek"`
Karta:
```
📝 Jan Kowalski, Warszawa:
• Notatka: "trzeba oddzwonić w piątek"
• Calendar: 17.04.2026 (Piątek) 10:00 — telefon (domyślna godzina, zmień w Kalendarzu jeśli chcesz)

[✅ Zapisać] [➕ Dopisać] [❌ Anulować]
```

Jeśli handlowiec wciśnie `Dopisać` i dopisze `"ale o 14"` → karta się przebudowuje z godziną 14:00.

**Efekt w Sheets (po [Tak]):**
- Kolumna `H=Notatki`: append z separatorem `"; "` i datą w nawiasie: `"[11.04.2026] treść nowej notatki"` — żeby historia notatek była czytelna.
- Kolumna `J=Data ostatniego kontaktu`: aktualizowana na dziś.

**Efekt w Kalendarzu:**
- Bez compound: brak.
- Z compound: nowe wydarzenie typu `phone_call` na wskazany dzień/czas (jeśli user nie podał godziny → domyślnie 10:00 w piątek, z opisem "telefon do Jana Kowalskiego (Warszawa)" i lokalizacją = telefon klienta).

**R4:** pełna reguła.

**Gap dziś:**
- **Bug #6 (backlog):** `add_note` intent: "dodaj notatkę do Jana Nowaka" tworzy nowego klienta zamiast routingu do edit-note-of-existing. Musi istnieć jawna intencja `add_note`, nie udawana `add_client`. Routing w klasyfikatorze intencji.
- **Bug #17 (Sesja 1):** add_note ignoruje miasto — jeśli user pisze "do Krzywińskiego z Wołomina", agent zapisuje do innego Krzywińskiego (Marki). Identyfikacja musi uwzględniać miasto nawet wtedy, gdy user dał jawny sygnał.

---

### 4.4. `change_status` — zmiana statusu + prompt o next action

**Parser:**
- Pola obowiązkowe: identyfikator klienta (R4), nowy status
- Dedukcja statusu z luźnych fraz:
  - "zrobiłem ofertę", "wysłałem ofertę" → `Oferta wysłana`
  - "nie chce", "rezygnuje", "odpada" → `Rezygnacja z umowy`
  - "podpisali", "wzięli", "zamknąłem" → `Podpisane`
  - "zamontowane", "odebrali", "zakończone" → `Zamontowana`
  - "nie zainteresowany", "odrzucił" → `Odrzucone`
  - "byłem u niego", "spotkanie odbyte" → `Spotkanie odbyte`
- Jeśli user użył pełnego nazwa statusu → bezpośrednio (bez dedukcji)

**Statusy lejka sprzedażowego (aktualne, 9 opcji):**
```
Nowy lead → Spotkanie umówione → Spotkanie odbyte → Oferta wysłana →
Podpisane → Zamontowana → Rezygnacja z umowy → Nieaktywny → Odrzucone
```

("Negocjacje" zostały świadomie wycięte 11.04.2026 — status był teoretyczny i nigdy nie używany w realnych testach. Nie wraca.)

**Karta potwierdzenia:**

```
📊 Jan Kowalski, Warszawa
Status: Oferta wysłana → Spotkanie umówione

[✅ Zapisać] [➕ Dopisać] [❌ Anulować]
```

**Efekt w Sheets (po [Tak]):**
- Kolumna `F=Status`: nowa wartość
- Kolumna `J=Data ostatniego kontaktu`: aktualizowana na dziś

**Efekt w Kalendarzu (po [Tak]):**
- **Opcjonalnie** wydarzenie "Status change" (faza B — do decyzji czy nas interesuje audyt przejść statusów w kalendarzu)
- **Zawsze** po zmianie statusu agent pokazuje **prompt o next action** (sekcja 5 — state machine)

**R4:** pełna reguła.

**Gap dziś:**
- Bug z Sesji 1: multi-match disambiguation działa dla samego nazwiska, ale status change nie zawsze. Sprawdzić `intent_change_status` czy używa tej samej funkcji `identify_client` co pozostałe intencje.
- Po [Tak] w change_status brak next action prompt — musi być dodany (sekcja 5 opisuje).

---

### 4.5. `add_meeting` — wydarzenie w Kalendarzu (4 typy)

**Parser:**
- Pola obowiązkowe: identyfikator klienta (R4), data, godzina, typ wydarzenia
- Typy wydarzeń:
  - `in_person` — spotkanie osobiste (domyślny typ jeśli user mówi "spotkanie")
  - `phone_call` — telefon ("zadzwonić", "telefon")
  - `offer_email` — wysłanie oferty mailem ("wyślę ofertę", "mail z wyceną")
  - `doc_followup` — follow-up dokumentowy ("wrócić do", "follow-up", "przypomnieć się")
- Parsowanie daty: "jutro", "pojutrze", dni tygodnia ("w piątek"), "za tydzień", DD.MM, DD.MM.YYYY
- Parsowanie godziny: HH:MM, HH, "wpół do ósmej" → 07:30, "za kwadrans dziesiąta" → 09:45, "rano" → 09:00, "po południu" → 14:00, "wieczorem" → 18:00

**Karta potwierdzenia:**

```
📅 Spotkanie: Jan Kowalski, Warszawa
Data: 15.04.2026 (Środa) 14:00
Adres: Piłsudskiego 12, Warszawa
Typ: spotkanie osobiste

[✅ Zapisać] [➕ Dopisać] [❌ Anulować]
```

Wariant dla `phone_call`:
```
📞 Telefon: Jan Kowalski, Warszawa
Data: 15.04.2026 (Środa) 10:00
Typ: rozmowa telefoniczna

[✅ Zapisać] [➕ Dopisać] [❌ Anulować]
```

**Efekt w Sheets (po [Tak]):**
- Kolumna `K=Następny krok`: zaktualizowana do daty wydarzenia w formacie `15.04.2026 (Środa) 14:00`
- Kolumna `J=Data ostatniego kontaktu`: aktualizowana na dziś
- Jeśli to spotkanie fizyczne i klient jest w statusie `Nowy lead` → **auto-przejście statusu na `Spotkanie umówione`** (bo status lejka powinien odzwierciedlać fakt że spotkanie jest w kalendarzu). Karta pokaże to w polu "Status: Nowy lead → Spotkanie umówione".

**Efekt w Kalendarzu (po [Tak]):**
- Nowe wydarzenie Google Calendar, title: `{imię nazwisko} ({miasto})`, opis: produkt + notatki, lokalizacja: adres klienta (dla in_person) lub telefon (dla phone_call), czas trwania: 1h (in_person), 15 min (phone_call), 0 min (offer_email, doc_followup — tylko termin)
- Wydarzenie ma metadane `{client_sheet_row: X, event_type: "in_person"}` w polu extendedProperties (żeby reschedule/cancel mogło je znaleźć)

**R4:** pełna reguła.

**Gap dziś:**
- Stary Bug #1 (naprawiony bc765a2): "Spotkanie z Nowak" zamiast pełnego imienia → już działa.
- Bug #8 (backlog): multi-meeting parser gubi imię w niektórych edge cases. MVP: nie robimy multi-meeting, tylko single — zgłaszamy jedno wydarzenie na raz.
- Bug #9 (backlog): multi-meeting format daty bez roku. Jak wyżej, niedotyczy MVP single.
- Bug #10 (backlog): polska odmiana w opisie wydarzenia — "Spotkanie z Jan Mazur" powinno być "z Janem Mazurem". Low priority.
- **New:** auto-przejście statusu z `Nowy lead` → `Spotkanie umówione` jeszcze nie istnieje w kodzie — do dodania razem z add_meeting.

---

### 4.6. `show_day_plan` — plan dnia

**Parser:**
- Pola obowiązkowe: żadne (data domyślnie = dziś)
- Pola opcjonalne: data ("plan na jutro", "co mam w piątek")

**Karta potwierdzenia:** NIE MA (read-only).

**Format wyniku:**

```
📅 Plan na 11.04.2026 (Sobota)

09:00 📞 Jan Kowalski (Warszawa) — telefon
10:30 🤝 Piotr Nowak (Piaseczno) — spotkanie
      Kościuszki 15, Piaseczno • Status: Oferta wysłana
14:00 🤝 Adam Mazur (Radom) — spotkanie
      Słowackiego 3, Radom • Status: Oferta wysłana
16:00 ✉️ Michał Wiśniewski (Legionowo) — wysłać ofertę
```

**Zasady formatu:**
- Godzina + emoji typu + pełne `imię nazwisko (miasto)` — nigdy samo nazwisko
- Dla `in_person`: dodatkowa linia z pełnym adresem i statusem
- Dla `phone_call`: tylko godzina + imię + miasto (adres nieistotny)
- Dla `offer_email`/`doc_followup`: godzina + akcja + imię + miasto
- Format daty header: `DD.MM.YYYY (Dzień tygodnia)`
- Sortowanie: chronologicznie po godzinie
- Jeśli brak wydarzeń: `"Na dzisiaj nic nie masz w kalendarzu."`

**Efekt w Sheets:** brak.
**Efekt w Kalendarzu:** brak (read-only — query do Google Calendar API).

**R4:** nie stosuje się.

**Gap dziś:**
- Stary gap: day plan jest "Option A partial" — pełne imiona OK, ale brak pełnego adresu i statusu dla in_person. To jest zaplanowane jako Option A polish (~2-3h po Option C).
- Compact day plan format jest w system prompcie, ale rozrasta się dla >5 wydarzeń. MVP: akceptujemy długość, później ewentualnie "5 widocznych + X ukrytych, rozwiń?".

---

## 5. State machine pending flow (R1)

### 5.0. Karta potwierdzenia — 3 przyciski (zamrożone 11.04.2026)

Wszystkie karty mutacyjne (add_client, add_note, change_status, add_meeting, compound post-visit flow) mają **trzy przyciski** zamiast starego `[Tak] [Nie]`:

| Przycisk | Kolor | Znaczenie |
|---|---|---|
| **✅ Zapisać** | zielony | Commit: Sheets write + Calendar write (jeśli kontrakt intencji tego wymaga). Karta znika. Po commit agent może jeszcze zadać `next_action_prompt` (sekcja 5.1). |
| **➕ Dopisać** | żółty | Karta zostaje **pending** — handlowiec może dopisać więcej informacji kolejną wiadomością tekstową. Agent re-parsuje nowy tekst w kontekście otwartej karty, rekonstruuje kartę z doklejonymi polami i pokazuje ją ponownie. Handlowiec może naciskać "Dopisać" wielokrotnie (np. dorzucił telefon → Dopisać → dorzucił notatkę → Dopisać → Zapisać). |
| **❌ Anulować** | czerwony | Pending znika bez commitu. Agent odpowiada krótkim "Anulowane." i czeka na nowe polecenie. |

**Zasady:**
- **Karty read-only (`show_client`, `show_day_plan`) nie mają żadnych przycisków** — agent zwraca sam wynik, bo nic nie mutuje, R1 się nie stosuje.
- **"Dopisać" nie jest tym samym co "dodać do istniejącego klienta"** — to tryb edycji pending karty, nie flow `add_note`. Disambiguacja "nowy klient vs dopisać do istniejącego" dzieje się na etapie parsera (sekcja 5.3), zanim karta w ogóle się pojawi.
- **Compound flow** (jedna karta dla note + status + meeting, sekcja 5.2) używa tych samych 3 przycisków — `Zapisać` commituje wszystko atomowo, `Dopisać` pozwala doprecyzować (np. dorzucić godzinę spotkania), `Anulować` porzuca cały compound.
- Stary wzorzec `[Tak] [Nie]` oraz `[Tak] [Zapisz bez]` **przestaje istnieć** — nie pojawia się w żadnej nowej karcie, a istniejące w kodzie miejsca są do migracji w Fazie A (krok A.9, sekcja 10).

### 5.3. Disambiguacja "nowy klient vs dopisać do istniejącego"

Każda mutacja, która wygląda jak `add_client` albo `add_note`, przechodzi przez **detekcję istniejącego klienta** zanim agent pokaże kartę:

1. Parser wyciąga `imię + nazwisko + miasto` (jeśli podane).
2. Agent odpyta Sheets o istniejących klientów po tym kluczu.
3. **Jeśli match = 1** → agent nie tworzy nowego klienta; mutacja idzie na istniejący wiersz jako `add_note`/`change_status`/`add_meeting` (zależnie od treści). Na karcie pojawia się banner: `⚠️ Ten klient już istnieje — dopiszę do wiersza z 05.04.2026`.
4. **Jeśli match ≥ 2** → multi-match disambiguation (numerowana lista miast/dat pierwszego kontaktu), handlowiec wybiera.
5. **Jeśli match = 0** → normalny flow `add_client`.
6. **Jeśli brak miasta w inpucie**, a po imieniu+nazwisku jest ≥ 1 wynik → agent dopyta "Który Kowalski — Warszawa czy Piaseczno?" zanim zacznie tworzyć cokolwiek.

Ta detekcja pilnuje, żeby handlowiec nie zrobił duplikatu tego samego klienta w trzech miejscach arkusza, kiedy wpisze "dodaj Kowalskiego z Warszawy" pół roku po pierwszym wpisie.



Każda intencja mutująca przechodzi przez **3 stany**: `parsed → pending → committed` (lub `cancelled`).

```
       user input
           │
           ▼
     ┌─────────────┐
     │   parsed    │   LLM wyciągnął intencję + pola
     └──────┬──────┘
            │  agent pokazuje kartę
            ▼
     ┌─────────────┐
     │   pending   │   czeka na [Tak] / [Nie] / wiadomość
     └──────┬──────┘
            │
     ┌──────┴──────┐
     ▼             ▼
┌─────────┐   ┌──────────┐
│ [Tak]   │   │  [Nie]   │
└────┬────┘   └────┬─────┘
     │             │
     ▼             ▼
┌─────────┐   ┌──────────┐
│committed│   │cancelled │
└────┬────┘   └──────────┘
     │
     │ (post-commit effects)
     │
     ├── Sheets write
     ├── Calendar write
     └── next_action_prompt (change_status only)
```

**Zasady przejść:**

1. **`parsed → pending`:** agent ZAWSZE pokazuje kartę potwierdzenia (R1). Wyjątek: intencje read-only (`show_client`, `show_day_plan`) — one pomijają `pending` i idą wprost do wyniku.

2. **`pending → committed`:** tylko po jawnym [Tak] lub tekstowym potwierdzeniu ("tak", "ok", "zapisz"). Każda inna wiadomość podczas `pending` → **state-lock fix**: anuluj bieżący pending, potraktuj nową wiadomość jako nowy input (intent classification). Ten fix już działa i jest lessons learned z Round 4.

3. **`pending → cancelled`:** [Nie] lub "anuluj". Pending stan znika, user widzi krótkie "Anulowane. Co chcesz zrobić?".

4. **`committed` → post-commit effects:**
   - Sheets write (ZAWSZE przed Calendar write)
   - Calendar write (jeśli kontrakt intencji tego wymaga)
   - Dla `change_status` → **next_action_prompt** (sekcja 5.1)

**Niezmienniki:**
- W żadnym momencie agent nie pisze do Sheets/Kalendarza zanim nie przejdzie przez `pending`+[Tak]. R1 to absolut.
- Jeśli Sheets write uda się, ale Calendar write spadnie → agent informuje "Zapisałem do Sheets, ale kalendarz nie odpowiada. Spróbuj jeszcze raz za chwilę" i w Supabase/logu oznacza niespójność do ręcznego dopełnienia. Nie retry automatycznie (accepted tradeoff MVP).

### 5.1. Next action prompt (po każdej mutacji, wolnotekstowy)

**Zamrożone 11.04.2026** — odwrócenie decyzji z 10.04 wieczór (która usunęła R4 "zapytaj o następny kontakt"). Wracamy do pytania, ale w nowej, elastycznej formie.

Po każdym committed `add_client`, `add_note`, `change_status`, `add_meeting` — **o ile z tej mutacji nie wynika jeszcze wprost następny krok** (np. `add_meeting` sam w sobie definiuje następny krok, więc prompt się nie pojawia; ale `change_status → Oferta wysłana` bez meeting-follow-up = wyświetlamy prompt) — agent pokazuje **jedno wolnotekstowe pytanie**:

```
✅ Zapisane.
Co dalej z Janem Kowalskim z Warszawy? Spotkanie, telefon, mail, odłożyć na później?

[❌ Anuluj / nic]
```

**Zasady:**
- To jest **jedno pytanie**, nie 4-przyciskowa trójka. Handlowiec odpowiada prozą.
- Jeśli odpowiedź zawiera typ akcji + datę/godzinę (`"telefon w piątek o 10"`) → agent parsuje jako `add_meeting(phone_call)` i startuje normalny flow z kartą potwierdzenia.
- Jeśli odpowiedź to `"nie wiem jeszcze"`, `"później"`, `"zobaczę"` → agent zamyka flow bez tworzenia wydarzenia. Klient zostaje z `K=Następny krok` pustym (albo poprzednim, jeśli był).
- Jeśli handlowiec wciśnie `❌ Anuluj / nic` → to samo co "nie wiem" — koniec flow.
- **Wolnotekstowość jest celowa:** stara trójka meeting/call/not interested blokowała flow i irytowała. Teraz handlowiec może odpowiedzieć "zadzwoni sam, zostaw" i koniec — bez żadnej sztywnej procedury.

**Uzasadnienie:** bez tego pytania klienci zamierają w lejku w statusie "Nawiązano kontakt" tygodniami. Wolnotekstowa wersja nie blokuje, a jednocześnie przypomina handlowcowi, że ma klienta do obsłużenia dalej. Szczegóły decyzji: `SOURCE_OF_TRUTH.md` sekcja 4, 11.04.2026, punkt 3.

### 5.2. Post-visit flow (notatki po spotkaniu) — Variant 1

Po tym jak handlowiec wraca ze spotkania i pisze luźno "byłem u Kowalskiego w Warszawie, chcą pompę zamiast PV, wracam w czwartek", agent:

1. Klasyfikuje intencję → compound: `add_note` + `change_status` (Spotkanie umówione → Spotkanie odbyte) + `add_meeting` (phone_call lub in_person na czwartek)
2. Pokazuje **jedną kartę zbiorczą**:

```
📋 Spotkanie odbyte: Jan Kowalski, Warszawa

Zapisuję:
• Notatka: "chcą pompę zamiast PV"
• Status: Spotkanie umówione → Spotkanie odbyte
• Calendar: 15.04.2026 (Czwartek) 10:00 — wrócić do klienta

[✅ Zapisać] [➕ Dopisać] [❌ Anulować]
```

3. Po [Tak] → wszystko leci w 3 sequential writes: Sheets (notatka), Sheets (status), Calendar (wydarzenie). Jeden commit, jedna karta — handlowiec nie klika 3 razy.

Variant 1 różni się od naiwnego "osobna karta dla każdej intencji" tym że **grupuje compound intencje w jedno pytanie**. To jest kluczowe dla UX w polu — handlowiec wraca ze spotkania i chce jednym ruchem zamknąć temat, nie odpowiadać 3x [Tak] na kolejne karty.

---

## 6. Schema Sheets (zamrożona 11.04.2026, 16 kolumn)

Kolumny w arkuszu "OZE Klienci", w kolejności. Ten schemat jest **zgodny 1:1 z realnym arkuszem Maana** (screenshot, Sesja 1 Regresja). Kod jest schema-agnostic — odczytuje nagłówki przez `get_sheet_headers()` z wiersza 1 i cachuje w `users.sheet_columns`, więc kolejność/nazwy kolumn wynikają z arkusza, nie z hardkodu.

| Litera | Nazwa | Typ | Dropdown? | Opis |
|---|---|---|---|---|
| A | Imię i nazwisko | string | — | "Jan Kowalski". Pełny string w jednej komórce. |
| B | Telefon | string | — | Format zachowany jak user podał ("600 123 456" lub "600123456"). |
| C | Email | string | — | Opcjonalny. |
| D | Miasto | string | — | Jedno miasto, nie cały adres. |
| E | Adres | string | — | Ulica + numer. Bez miasta (to D). |
| F | Status | enum | **TAK** (9 opcji) | Lejek sprzedażowy: Nowy lead, Spotkanie umówione, Spotkanie odbyte, Oferta wysłana, Podpisane, Zamontowana, Rezygnacja z umowy, Nieaktywny, Odrzucone. |
| G | Produkt | string | — | Typ: PV, Pompa ciepła, Magazyn energii, PV + Magazyn, kombinacje. **Bez liczb, bez mocy.** |
| H | Notatki | string | — | Append-only w chronologii. Zawiera: moc PV/pompy/magazynu, metraż, dach, kierunek, zużycie, napięcie, typ dachu, kontekst emocjonalny, follow-up history. Separator: `; ` (z datą w nawiasach dla wpisów z różnych dni). |
| I | Data pierwszego kontaktu | date | — | `DD.MM.YYYY` (bez dnia tygodnia — to do wyświetlania). Ustawiana raz przy `add_client`, potem się nie zmienia. |
| J | Data ostatniego kontaktu | date | — | `DD.MM.YYYY`. Aktualizowana przy każdej intencji mutującej (add_note, change_status, add_meeting). |
| K | Następny krok | enum | **TAK** (7 opcji) | Dropdown: Telefon, Spotkanie, Wysłać ofertę, Follow-up dokumentowy, Czekać na decyzję klienta, Nic — zamknięte, Inne. |
| L | Data następnego kroku | date / datetime | — | `DD.MM.YYYY` lub `DD.MM.YYYY HH:MM`. Wypełniana automatycznie przy `add_meeting` (z daty wydarzenia) albo ręcznie przez handlowca. |
| M | Źródło pozyskania | string | — | Np. "Facebook", "polecenie", "targi", "strona www". Opcjonalne. |
| N | Zdjęcia | int / string | — | Licznik zdjęć lub krótki opis (np. "3 zdj. dachu"). Uzupełniany w Phase 4 (Drive). Dziś pole może być puste. |
| O | Link do zdjęć | url | — | URL do folderu klienta w Google Drive: `/OZE-Agent/{imię nazwisko}_{miasto}/`. Uzupełniany w Phase 4. |
| P | ID wydarzenia Kalendarz | string | — | Last-used Google Calendar event ID powiązany z klientem (do reverse lookup / aktualizacji). Może trzymać też `extendedProperties` hash. Uzupełniany w Fazie B. |

**Wiersz 1 (nagłówki) jest chroniony** (Protected range `A1:P1`) — handlowiec ani agent nie mogą go przepisywać, bo mapowanie kolumn przez `get_sheet_headers()` zależy od tego, żeby `H` zawsze zawierało dokładnie `"Notatki"`.

**Nigdy nie wprowadzamy:** `moc_kw`, `metraz_domu`, `metraz_dachu`, `kierunek_dachu`, `zrodlo_leada_szczegoly`, `typ_dachu`, `napiecie_sieci`. Wszystko techniczne → `H=Notatki`.

---

## 7. Typy wydarzeń Kalendarza

Wszystkie wydarzenia tworzone przez agenta mają `extendedProperties.private` z:
- `client_sheet_row: int` — do reverse lookup
- `event_type: string` — jeden z 4 typów poniżej
- `managed_by: "oze-agent"` — do filtrowania w query plan dnia

| Typ | Title | Duration | Emoji | Opis |
|---|---|---|---|---|
| `in_person` | `{imię nazwisko} ({miasto})` | 60 min | 🤝 | Spotkanie fizyczne. Lokalizacja = adres. |
| `phone_call` | `📞 {imię nazwisko} ({miasto})` | 15 min | 📞 | Rozmowa telefoniczna. Lokalizacja = telefon klienta. |
| `offer_email` | `✉️ Oferta: {imię nazwisko}` | 0 min | ✉️ | Termin wysłania oferty. All-day lub określona godzina. |
| `doc_followup` | `📄 Follow-up: {imię nazwisko}` | 0 min | 📄 | Przypomnienie "wrócić do klienta". |

Plan dnia filtruje po `extendedProperties.managed_by == "oze-agent"` — żeby nie pokazywać prywatnych wydarzeń handlowca.

---

## 8. Świadomie odrzucone z MVP

### 8.1. POST-MVP (wróci w późniejszej fazie)

| Intencja | Dlaczego nie teraz | Kiedy |
|---|---|---|
| `filtruj_klientów` | Handlowiec rzadko filtruje w locie. Częściej robi to w dashboardzie (który powstaje w Phase późniejszej). Dla beta wystarczy `show_client` z nazwiskiem. | Po MVP beta, jeśli testerzy tego chcą |
| `edit_client` | Pokrycie przez `add_note` + `change_status` wystarczy na MVP. Pełna edycja pola wymaga dodatkowego parsera i walidacji. | Po MVP, zależnie od feedbacku |
| `lejek_sprzedazowy` | Funkcja dashboardowa, czeka na dashboard Next.js. W bocie wzorzec zostaje jako referencja. | Razem z dashboardem |
| `voice input` | Phase 5 w implementation_guide. Whisper API + polski. Duża infra. | Phase 5 |
| `Drive photos` | Phase 4. Zdjęcia z terenu → Drive folder klienta. | Phase 4 |
| `proactive messages` | Brief poranny, podsumowanie wieczorne — scheduler-driven, wymaga APScheduler + dedupy. | Phase 6 |

### 8.2. NIEPLANOWANE — wycięte na stałe (decyzja 11.04.2026 popołudnie)

Te intencje **nigdy nie wejdą do produktu**. Były wcześniej oznaczone jako POST-MVP, ale po namyśle zostały wyrzucone — `SOURCE_OF_TRUTH.md` sekcja 4, 11.04.2026 popołudnie.

| Intencja | Dlaczego na stałe wycięte | Co robi handlowiec zamiast |
|---|---|---|
| `reschedule_meeting` | Dwa flow (edycja wydarzenia + wyszukiwanie którego wydarzenia dotyczy) dla marginalnej wartości. Jedno spójne flow jest prostsze: skasuj stare, dodaj nowe. | Kasuje stare wydarzenie w Kalendarzu ręcznie i pisze `add_meeting` komendą |
| `cancel_meeting` | Irreversible delete na podstawie interpretacji tekstu to ryzyko, którego agent nie bierze na siebie. | Kasuje wydarzenie w Kalendarzu bezpośrednio |
| `free_slots` | Handlowiec widzi luki z `show_day_plan`. Osobna intencja liczenia wolnych slotów to overhead bez realnej wartości. | Patrzy na plan dnia komendą `co mam w X` |
| `meeting_non_working_day_warning` | Handlowcy OZE pracują w soboty, niedziele, święta. Warning byłby fałszywym założeniem z innego segmentu. | Nic — `add_meeting` w weekend działa identycznie jak w dzień roboczy |

Klasyfikator intencji musi rozpoznać wyrażenia "przełóż / zmień spotkanie / przesuń", "wolne okna / kiedy mam wolne", "odwołaj / skasuj spotkanie" — ale tylko po to, żeby odpowiedzieć jedną linią tłumaczącą co handlowiec ma zrobić zamiast. Nie ma karty, nie ma flow mutacji.

---

## 9. Przyszłość: Phase 4 (Drive) + Phase 5 (Voice)

**Phase 4 — Drive (zdjęcia klienta):**
- Każdy klient ma folder w Google Drive: `/OZE-Agent/{imię nazwisko}_{miasto}/`
- Handlowiec w terenie robi zdjęcie dachu → wysyła do bota → agent wrzuca do folderu klienta
- Intencja: `add_photo` — pobiera telegram file, uploaduje do Drive, aktualizuje kolumny `N=Zdjęcia` (licznik/opis) + `O=Link do zdjęć` (URL do folderu)
- **Mobile reminder (mobile Google Drive w terenie):** gdy handlowiec wrzuci zdjęcie do Telegrama, agent przypomni, że w apce Google Drive na telefonie można **skanować dokumenty** (przycisk "+" → "Skanuj") i że skany też można kierować do folderu klienta przez bota. To jest miękki push — krótka wiadomość po uploadzie, raz na sesję, bez zakłębienia.
- Kontrakt już zaprojektowany: kolumny `N=Zdjęcia` i `O=Link do zdjęć` siedzą w zamrożonym schemacie sekcji 6. Dziś są puste, w Phase 4 zaczynają się wypełniać.

**Phase 5 — Voice input:**
- Telegram voice message → Whisper API (polski) → transkrypcja → normalny flow intencji
- Intencja nie zmienia się, tylko wejście staje się głosem
- Kontrakt: voice flow = text flow + transcription step z przodu
- Ryzyko: Whisper gubi polskie nazwy własne (Krzywiński → Krivinski) — wymaga post-processingu przez lekki LLM fuzzy-match z listą istniejących klientów

---

## 10. Kolejność implementacji (fazowanie)

Produktowo: **wszystkie intencje MVP są zaprojektowane teraz**, kod pisany **fazowo**.

### Faza A — Sheets-side + bugfixy z Sesji 1 Regresja

Cel: wyprostować bugi z Sesji 1 Regresji, zamrozić kontrakty intencji na nowym schemacie 16-kolumnowym, dodać detekcję istniejącego klienta i context-aware resolution. Kalendarz jest już **częściowo podpięty** (Phase 3.1 single meeting + 3.3 day plan są w stanie PARTIAL, sekcja `CURRENT_STATUS.md`), więc Faza A nie jest "Sheets only" — raczej "Sheets + porządki + infrastruktura dla Fazy B". Kontrakty intencji już zawierają pole `calendar_event: CalendarEventDraft | None` — w tej fazie dla nowych intencji zostaje `None`, ale sygnatura się nie zmienia.

1. **Bug #14 (moc → Notatki):** zmienić system prompt + parser, żeby moc nie trafiała do `G=Produkt`. Upewnić się że add_client test G1-G5 przechodzi.
2. **Bug #15 (karta niespójna `Brakuje:`):** poprawić formatter karty, lista `Brakuje:` tylko pola opcjonalne-ważne.
3. **Bug #16 (polska odmiana w search):** dodać lematyzację przed fuzzy match (biblioteka `morfeusz2` lub prosty pattern replace dla najczęstszych form przypadków).
4. **Bug #17 (add_note ignoruje miasto):** poprawić identify_client żeby zawsze patrzył na miasto jeśli user je podał.
5. **Bug #6 (add_note routing):** klasyfikator intencji musi rozpoznawać "dodaj notatkę do X" jako `add_note`, nie `add_client`.
6. **Excel serial date bug:** formatowanie dat w `format_client_card()` (konwersja z Google Sheets serial na `DD.MM.YYYY (Dzień tygodnia)`).
7. **Schemat 16-kolumnowy + dropdowny + ochrona nagłówka:** upewnić się, że realny arkusz Maana ma nazwy kolumn zgodne z sekcją 6, dropdowny na F (9 opcji) i K (7 opcji), oraz Protected range `A1:P1`. Kod nie potrzebuje zmiany (jest schema-agnostic), ale setup arkusza musi być zweryfikowany.
8. **A.8 — Context-aware client resolution (NOWY krok):** implementacja funkcji `resolve_active_client(user_id, history_window=10)` + mechanizmu `user_data["active_client"]`. Gdy handlowiec mówi "dodaj że ma duży dom" bez wskazania klienta, agent bierze ostatnio aktywnego klienta z kontekstu (ostatnie 10 wiadomości). Infrastruktura (`get_conversation_history`) już istnieje w `shared/database.py`, brakuje tylko pamięci aktywnego klienta. Patrz `SOURCE_OF_TRUTH.md` sekcja 4 (11.04, punkt 9).
9. **A.9 — Migracja kart do 3-przyciskowego UI:** wszystkie `[Tak] [Nie]` i `[Tak] [Zapisz bez]` w kodzie formatterów kart (`shared/formatting.py`, `bot/handlers/text.py`) zamieniamy na `[✅ Zapisać] [➕ Dopisać] [❌ Anulować]` zgodnie z sekcją 5.0. Dopisywanie wymaga nowego handlera przycisku Dopisać, który utrzymuje pending w `user_data` i re-parsuje kolejną wiadomość z doklejonymi polami.
10. **A.10 — Detekcja istniejącego klienta przed mutacją:** dodać krok "czy klient już istnieje" (sekcja 5.3) do parserów `add_client`, `add_note`, `change_status`, `add_meeting`. Bez tego flow `add_client` dla istniejącego klienta tworzy duplikat.
11. **A.11 — `next_action_prompt` (wolnotekstowy):** po każdym commit mutacji (z wyjątkami z sekcji 5.1), agent wysyła otwarte pytanie o następny krok. Implementacja jako stan maszyny (`awaiting_next_action`) — kolejna wiadomość handlowca jest parsowana w kontekście tego pending prompt.
12. **Stara R4 usunąć:** jeśli jeszcze gdzieś w kodzie jest "zapytaj o następny kontakt po add_client" w formie sztywnej trójki meeting/call/not interested — wyciąć i zastąpić wolnotekstowym (punkt 11).

**Deliverable:** intencje `add_client`, `show_client`, `add_note`, `change_status` działają zgodnie z nowym kontraktem dla Sheets-side, z 3-button UI, detekcją istniejącego klienta, wolnotekstowym next_action_prompt i context-aware resolution. Calendar-side dla nowych intencji zawraca stub, ale istniejące meeting/day plan z Phase 3 działają dalej (nie psujemy).

**Czas:** ~2-3 sesje Claude Code.

### Faza B — Calendar-side (od day 1 tego samego contractu)

Cel: podpiąć Google Calendar API pod intencje `add_meeting` i `show_day_plan`, plus dodać Calendar writes do `add_client` (follow-up optional), `add_note` (compound), `change_status` (next_action_prompt), `add_meeting` (wszystkie 4 typy).

1. **Google Calendar API setup:** OAuth credentials, calendar list query, create/read/update event functions. Code path: `shared/google_calendar.py`.
2. **`add_meeting` — 4 typy wydarzeń:** parser rozpoznaje typ, CalendarEventDraft buduje się na bazie typu, write do Calendar z extendedProperties.
3. **`show_day_plan` — query Calendar:** filtr po `managed_by == "oze-agent"`, format output, sortowanie chronologiczne, pełne imię+miasto+adres+status dla in_person.
4. **Auto-przejście statusu:** przy `add_meeting(in_person)`, jeśli klient jest w `Nowy lead`, automatyczna zmiana na `Spotkanie umówione` — pokazać to na karcie przed [Tak].
5. **Next action prompt:** po `change_status` committed, zawsze pokazuj 4 przyciski.
6. **Compound `add_note` + `phone_call`:** detekcja + karta z dwiema opcjami.
7. **Variant 1 post-visit flow:** jedna karta zbiorcza dla compound (note + status + meeting).

**Deliverable:** pełny MVP wszystkich intencji z dual-write Sheets+Calendar.

**Czas:** ~3-4 sesje Claude Code.

### Faza C — Bugfixy z Sesji Kalendarzowej (po pierwszych testach B)

Będą. Nie znamy ich jeszcze. Przewidywane obszary:
- Konflikty czasowe przy `add_meeting` (dodajesz 14:00 a masz już tam innego klienta)
- Strefy czasowe (Europe/Warsaw) i letni/zimowy czas (edge case ~2 razy na rok)
- Polska odmiana w tytule wydarzenia ("Jan Mazur" vs "Jana Mazura")

---

## 11. Mapping bugów Sesji 1 (#11–#17) do intencji

| Bug | Opis | Intencja | Faza naprawy |
|---|---|---|---|
| **#11** | `show_client` z samym nazwiskiem nie pokazuje multi-match nawet gdy jest 3 Kowalskich (zamiast tego zwraca pierwszego) | `show_client` | Faza A |
| **#12** | `add_client` karta listuje `dom 160m²` jako "Brakuje:" (powinno iść do Notatek bez wspomnienia) | `add_client` | Faza A (Bug #15) |
| **#13** | Format daty w `show_client` karta pokazuje `46120` zamiast `11.04.2026 (Sobota)` | `show_client` | Faza A |
| **#14** | Moc (`8kW`) zostawiana w Notatkach jako "moc 8kW" ale produkt pozostaje "PV 8kW" — podwójna | `add_client` | Faza A (kontrakt zmieniony: moc → Notatki, produkt = typ) |
| **#15** | `Brakuje:` w karcie add_client listuje rzeczy które nie powinny być listowane (metraż, kierunek dachu) | `add_client` | Faza A |
| **#16** | Polska odmiana gubi klienta katastrofalnie ("u Krzywińskim" → bot halucynuje "Kriwiński") | `show_client`, `add_note`, `change_status`, `add_meeting` (wszystkie identyfikujące) | Faza A |
| **#17** | `add_note` ignoruje miasto — zapis do wrong row mimo że user dał "z Wołomina" | `add_note` | Faza A |

Stare bugi z wcześniejszych rund (#1-#10) są w `CURRENT_STATUS.md`. Bug #6 (add_note routing) i #8-#10 (multi-meeting/polska odmiana) nadal otwarte, wchodzą do Fazy A (#6) lub Fazy B/C (reszta).

---

## 12. Zakończenie

Ten plik jest **zamrożony** jako blueprint MVP. Zmiany tylko po decyzji produktowej Maana. Jeśli Claude Code w trakcie implementacji znajdzie rozbieżność z kontraktem → STOP, wyjaśnij konflikt, nie zmieniaj kontraktu samodzielnie.

Po implementacji Fazy A + B + C, ten plik stanie się historycznym artefaktem (podobnie jak brief v5 dziś) — ale dopóki jesteśmy w fazie MVP, jest **drugim po SOURCE_OF_TRUTH.md** najwyższym dokumentem w hierarchii. Konflikty z `agent_behavior_spec_v5.md` rozstrzyga ten plik (bo jest nowszy i zawiera post-Sesja-1 decyzje).

**Hierarchia SSOT po dodaniu tego pliku (zsynchronizowana z `SOURCE_OF_TRUTH.md` sekcja 6):**

1. `docs/SOURCE_OF_TRUTH.md` — mapa + decision log
2. `docs/INTENCJE_MVP.md` — **ten plik** — kontrakty intencji MVP, zamrożony schemat Sheets (najbardziej aktualny po 11.04)
3. `docs/agent_behavior_spec_v5.md` — reguły R1-R6 + 52 testy akceptacyjne
4. `docs/agent_system_prompt.md` — ton + wzorce odpowiedzi
5. `docs/CURRENT_STATUS.md` — aktualny stan implementacji
6. `docs/implementation_guide_2.md` — plan budowy
7. `docs/poznaj_swojego_agenta_v5_FINAL.md` — opis user-facing
8. `docs/archive/...` — historyczne artefakty

`SOURCE_OF_TRUTH.md` sekcja 6 została zaktualizowana 11.04 (po Sesji 1 Regresja) i trzyma tę samą hierarchię — jeśli zobaczysz rozjazd, najpierw sprawdź datę edycji.
