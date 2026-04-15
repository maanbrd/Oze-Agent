# OZE-Agent — Macierz intencji MVP

_Ostatnia aktualizacja: 14.04.2026_
_Hierarchia SSOT: ten plik jest #5 per `SOURCE_OF_TRUTH.md` sekcja 5. W razie konfliktu — wygrywa wyższy._

Ten dokument definiuje **kontrakt 6 intencji MVP** — co agent robi w Sheets i Kalendarzu dla każdej rozpoznanej intencji, w jakiej kolejności, z jakimi potwierdzeniami.

Jeśli kod nie zgadza się z tym dokumentem → zmienia się kod. Jeśli kontrakt ma być zmieniony → najpierw decyzja Maana + edycja tego pliku, potem kod.

---

## 1. Zasada fundamentalna: Sheets = baza, Kalendarz = akcja

**Google Sheets** to statyczna baza klientów. Handlowiec do niej wchodzi rzadko — głównie gdy coś sprawdza, rozlicza się z szefem, albo eksportuje dane. Sheets mówi **co** wiemy o kliencie.

**Google Calendar** to codzienne narzędzie robocze. Handlowiec otwiera go wielokrotnie dziennie: żeby sprawdzić gdzie jechać, do kogo zadzwonić, kiedy wrócić do oferty. Calendar mówi **co** trzeba zrobić **kiedy** i **z kim**.

**Reguła dual-write:** każda informacja zapisana w Sheets musi mieć swoje odzwierciedlenie w Kalendarzu — jako wydarzenie (spotkanie, telefon, oferta, follow-up dokumentowy) w odpowiednim momencie na osi czasu. Klient przechodzi przez lejek sprzedażowy **wraz z przejściami w Kalendarzu**. Status w Sheets to skutek, nie przyczyna — przyczyną jest wydarzenie, które się odbyło lub się odbędzie.

**Implikacja techniczna:** każda intencja mutująca stan (add_client, change_status, add_meeting, add_note gdy note implikuje telefon) zawsze produkuje **parę**: wiersz w Sheets + wydarzenie w Kalendarzu. Nigdy jedno bez drugiego.

**Implikacja produktowa:** agent bez Kalendarza to notatnik, nie asystent. MVP wydajemy z dual-write od dnia 1.

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

**Duplicate resolution:** gdy przy `add_client` match = 1 w Sheets → agent przechodzi przez flow duplicate resolution (sekcja 5.3): krótki komunikat + `[Nowy]` / `[Aktualizuj]`, potem karta mutacyjna.

---

## 4. Kontrakty intencji (5 × parser → karta → Sheets → Kalendarz → R4)

Każda intencja ma 5 sekcji:
1. **Parser** — co LLM wyciąga z inputu użytkownika, jakie są pola wymagane vs opcjonalne
2. **Karta potwierdzenia** — dokładnie co agent pokazuje przed zapisem (R1)
3. **Efekt w Sheets** — które komórki się zmieniają
4. **Efekt w Kalendarzu** — jakie wydarzenie powstaje/aktualizuje się
5. **Zachowanie R4** — jak identyfikowany jest klient

### 4.1. `add_client` — dodanie klienta

**Parser:**
- Pola obowiązkowe: `imię`, `nazwisko`, `miasto`
- Pola opcjonalne na karcie: `telefon`, `email`, `adres` (ulica + numer), `produkt` (typ bez mocy), `źródło pozyskania`, `data następnego kontaktu` (jeśli user sam poda — w przeciwnym razie po commit agent zadaje `next_action_prompt`, sekcja 5.1)
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
- Kolumny: `A=Imię nazwisko`, `B=Telefon`, `C=Email`, `D=Miasto`, `E=Adres`, `F=Status="Nowy lead"`, `G=Produkt` (tylko typ), `H=Notatki` (wszystko inne, w tym moc/metraż/dach), `I=Data pierwszego kontaktu=dziś`, `J=Data ostatniego kontaktu=dziś`, `K=Następny krok` (z dropdowna, pusty chyba że user podał), `L=Data następnego kroku` (pusta chyba że user podał), `M=Źródło pozyskania` (jeśli parser wyciągnął), `N/O` (puste — POST-MVP photo flow), `P=ID wydarzenia Kalendarz` (per D8: event_id jeśli `add_client` utworzył Calendar event przez podany follow-up; pusty gdy add_client bez follow-upu lub gdy follow-up to no-event K value)

**Efekt w Kalendarzu (po `✅ Zapisać`):**
- Jeśli user podał datę follow-upu ("zadzwonię jutro", "wyślę ofertę za tydzień") → wydarzenie typu `phone_call`/`doc_followup`/`in_person` zależnie od słów kluczowych.
- Jeśli user nie podał daty → brak wydarzenia w Kalendarzu.

**R4:** nie stosuje się (tworzymy nowego klienta; detekcja istniejącego klienta z match=1 → sekcja 5.3).

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
- Wyświetlaj **wszystkie uzupełnione kolumny** z Sheets **z wyjątkiem**: Zdjęcia (N), Link do zdjęć (O), ID wydarzenia Kalendarz (P). Nie pokazuj pustych pól.
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

**Efekt w Kalendarzu (po `✅ Zapisać`):**
- Brak wydarzenia (change_status nie tworzy eventu w Calendar).
- Po commit agent może pokazać `next_action_prompt` (sekcja 5.1) — tylko jeśli z mutacji nie wynika już następny krok.

**R4:** pełna reguła.

---

### 4.5. `add_meeting` — wydarzenie w Kalendarzu (4 typy)

**Scope MVP:** single meeting tylko. Multi-meeting (kilka spotkań w jednej wiadomości) — POST-MVP (sekcja 8.1).

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
- Kolumna `K=Następny krok`: enum label typu spotkania per D4 (`Spotkanie` dla `in_person`, `Telefon` dla `phone_call`, `Wysłać ofertę` dla `offer_email`, `Follow-up dokumentowy` dla `doc_followup`). **K nigdy nie przechowuje daty.**
- Kolumna `L=Data następnego kroku`: data wydarzenia w ISO (per D1 — `YYYY-MM-DD` albo `YYYY-MM-DDTHH:MM:SS+HH:MM` z offsetem); displayed PL jako `15.04.2026 (Środa) 14:00`.
- Kolumna `P=ID wydarzenia Kalendarz`: Calendar event `id` zwrócony przez `events.insert` (per D8).
- Kolumna `J=Data ostatniego kontaktu`: aktualizowana na dziś
- Jeśli to spotkanie fizyczne i klient jest w statusie `Nowy lead` → **auto-przejście statusu na `Spotkanie umówione`** (bo status lejka powinien odzwierciedlać fakt że spotkanie jest w kalendarzu). Karta pokaże to w polu "Status: Nowy lead → Spotkanie umówione".

**Efekt w Kalendarzu (po `✅ Zapisać`):**
- Nowe wydarzenie Google Calendar, title: `{imię nazwisko} ({miasto})`, opis: produkt + notatki, lokalizacja: adres klienta (dla in_person) lub telefon (dla phone_call), czas trwania: 1h (in_person), 15 min (phone_call), 0 min (offer_email, doc_followup — tylko termin).
- Wydarzenie ma metadane `extendedProperties.private.event_type: "in_person"` (per D8 — **tylko** `event_type`, bez `client_sheet_row` / `managed_by` / `client_name`). Link Sheets → Calendar przez kolumnę P (`ID wydarzenia Kalendarz`), nie przez extendedProperties.

**add_meeting dla istniejącego klienta:** agent identyfikuje klienta po imię+nazwisko+miasto (R4). Jeśli match=1 → enrichment z Sheets (adres, telefon, notatki, produkt trafiają do eventu). Jeśli match=0 → event tworzy się bez CRM context (user może dodać klienta osobno później).

**R4:** pełna reguła.

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
- Stary wzorzec `[Tak] [Zapisz bez]` **nie pojawia się w żadnej karcie mutacyjnej**. `[Tak] [Nie]` jest dopuszczalne tylko w pytaniach binarnych nie-mutacyjnych (sekcja 5.6).

### 5.3. Disambiguacja "nowy klient vs dopisać do istniejącego"

Każda mutacja, która wygląda jak `add_client` albo `add_note`, przechodzi przez **detekcję istniejącego klienta** zanim agent pokaże kartę:

1. Parser wyciąga `imię + nazwisko + miasto` (jeśli podane).
2. Agent odpyta Sheets o istniejących klientów po tym kluczu.
3. **Jeśli match = 1** → agent pokazuje krótki komunikat "Ten klient już istnieje w arkuszu." + skrót danych istniejącego klienta + `[Nowy]` / `[Aktualizuj]`. Po kliknięciu → standardowa karta mutacyjna 3-button (`✅ Zapisać` / `➕ Dopisać` / `❌ Anulować`).
   - `[Aktualizuj]` = merge do istniejącego wiersza (update pól z nowych danych)
   - `[Nowy]` = utwórz osobny rekord (duplikat świadomy)
   - To jest routing decision, nie karta mutacyjna — R1 mutation card pojawia się po wyborze.
4. **Jeśli match ≥ 2** → multi-match disambiguation (numerowana lista miast/dat pierwszego kontaktu), handlowiec wybiera.
5. **Jeśli match = 0** → normalny flow `add_client`.
6. **Jeśli brak miasta w inpucie**, a po imieniu+nazwisku jest ≥ 1 wynik → agent dopyta "Który Kowalski — Warszawa czy Piaseczno?" zanim zacznie tworzyć cokolwiek.

Ta detekcja pilnuje, żeby handlowiec nie zrobił duplikatu tego samego klienta w trzech miejscach arkusza, kiedy wpisze "dodaj Kowalskiego z Warszawy" pół roku po pierwszym wpisie.

### 5.4. Calendar ↔ Sheets sync (decyzja 13.04.2026)

Gdy zmienia się termin w Calendar (reschedule lub przeniesienie):
- `Data następnego kroku` (kolumna L) aktualizuje się w Sheets
- `Następny krok` (kolumna K) aktualizuje się jeśli zmiana typu (np. spotkanie → telefon)
- `Status` (kolumna F) może się zmienić jeśli przeniesienie zmienia pozycję w lejku

Gdy `add_meeting` commituje:
- `Data ostatniego kontaktu` (kolumna J) = dziś
- `Data następnego kroku` (kolumna L) = data spotkania
- `Następny krok` (kolumna K) = typ spotkania

**Uwaga:** `reschedule_meeting` jest **poza aktualnym MVP scope** — vision-only (sekcja 8.2); wymaga osobnej decyzji Maana przed wejściem do roadmap. W MVP: jeśli handlowiec ręcznie zmienia event w Google Calendar, agent tego nie widzi — sync jest one-way przy mutacjach agentowych. Stan Sheets może się rozjechać z Calendar, jeśli user edytuje Calendar poza botem.

### 5.5. Wyświetlanie danych klienta (decyzja 13.04.2026)

W kartach klienta (`show_client`) i podsumowaniach wyświetlamy **wszystkie uzupełnione kolumny z Sheets** z wyjątkiem:
- Zdjęcia (kolumna N) — osobny flow
- Link do zdjęć (kolumna O) — techniczne
- ID wydarzenia Kalendarz (kolumna P) — techniczne

Nie pokazujemy pustych pól. Nie pokazujemy surowych danych technicznych (`_row`, serial dates, sheet IDs).

### 5.6. Polityka przycisków (decyzja 13.04.2026)

| Kontekst | Przyciski |
|----------|-----------|
| Karta mutacyjna (add_client, add_note, change_status, add_meeting) | `[✅ Zapisać]` `[➕ Dopisać]` `[❌ Anulować]` |
| Duplicate resolution | `[Nowy]` `[Aktualizuj]` |
| Proste pytanie binarne (nie karta zapisu) | `[Tak]` `[Nie]` dopuszczalne — np. potwierdzenie fuzzy match ("Chodziło o Kowalskiego z Warszawy?"), potwierdzenie transkrypcji voice |
| Karta read-only (show_client, show_day_plan) | Brak przycisków |

`[Tak]` / `[Nie]` **NIE zastępuje** karty zapisu do Sheets/Calendar/Drive. Jest dopuszczalne tylko w pytaniach binarnych nie-mutacyjnych.

Każda intencja mutująca przechodzi przez **3 stany**: `parsed → pending → committed` (lub `cancelled`).

**Przejścia:**

- `parsed → pending`: agent zawsze pokazuje kartę potwierdzenia (R1). Wyjątek: intencje read-only (`show_client`, `show_day_plan`) pomijają `pending` i idą wprost do wyniku.
- `pending → committed`: tylko po kliknięciu `✅ Zapisać` na karcie mutacyjnej.
- `pending → cancelled`: kliknięcie `❌ Anulować` lub tekstowe "anuluj". Pending znika, user widzi krótkie "Anulowane.".
- Każda inna wiadomość podczas pending (która nie pasuje do schematu uzupełnienia, auto-doklejania ani compound fusion — sekcja 5.6 / R3) → auto-cancel pending + nowa wiadomość przechodzi przez klasyfikator jako świeży input.
- `committed` → post-commit effects:
  - Sheets write (zawsze przed Calendar write)
  - Calendar write (jeśli kontrakt intencji tego wymaga)
  - `next_action_prompt` (sekcja 5.1) — tylko gdy z mutacji nie wynika jeszcze następny krok

**Niezmienniki:**
- W żadnym momencie agent nie pisze do Sheets/Kalendarza zanim nie przejdzie przez `pending` + `✅ Zapisać`. R1 to absolut.
- Jeśli Sheets write uda się, ale Calendar write spadnie → agent informuje "Zapisałem do Sheets, ale kalendarz nie odpowiada. Spróbuj jeszcze raz za chwilę" i w Supabase/logu oznacza niespójność do ręcznego dopełnienia. Nie retry automatycznie (accepted tradeoff MVP).

### 5.1. Next action prompt (R7, warunkowy wolnotekstowy)

Po committed mutacji agent pokazuje **jedno wolnotekstowe pytanie** o następny krok — **ale tylko gdy z mutacji nie wynika jeszcze wprost następny krok.**

**R7 ODPALA się po:**
- `add_client` bez daty follow-upu (user nie podał kiedy kontakt dalej)
- `add_note` czysty (bez komponentu czasowego w notatce)
- `change_status` bez compound meeting (sam status zmieniony, brak follow-up spotkania)

**R7 NIE ODPALA się po:**
- `add_meeting` (samo definiuje następny krok — data spotkania)
- Compound z `add_meeting` (Variant 1 post-visit flow, sekcja 5.2 — meeting już zdefiniował następny krok)
- `add_client` z podaną datą follow-upu (user już określił co dalej)

**Format:**

```
✅ Zapisane.
Co dalej z Janem Kowalskim z Warszawy? Spotkanie, telefon, mail, odłożyć na później?

[❌ Anuluj / nic]
```

**Zasady:**
- To jedno pytanie, nie sztywna trójka. Handlowiec odpowiada prozą.
- Jeśli odpowiedź zawiera typ akcji + datę/godzinę (`"telefon w piątek o 10"`) → agent parsuje jako `add_meeting(phone_call)` i startuje normalny flow z kartą potwierdzenia.
- Jeśli odpowiedź to "nie wiem jeszcze", "później", "zobaczę" → agent zamyka flow bez tworzenia wydarzenia. Klient zostaje z `K=Następny krok` pustym.
- Jeśli handlowiec wciśnie `❌ Anuluj / nic` → koniec flow.

**Uzasadnienie:** bez tego pytania klienci zamierają w lejku tygodniami. Wolnotekstowa wersja nie blokuje, a przypomina o kliencie.

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

3. Po `✅ Zapisać` → wszystko leci w 3 sequential writes: Sheets (notatka), Sheets (status), Calendar (wydarzenie). Jeden commit, jedna karta — handlowiec nie klika 3 razy.

**Compound z `add_meeting` NIE odpala R7** — następny krok już zdefiniowany przez meeting.

Variant 1 różni się od naiwnego "osobna karta dla każdej intencji" tym że **grupuje compound intencje w jedno pytanie**. To jest kluczowe dla UX w polu — handlowiec wraca ze spotkania i chce jednym ruchem zamknąć temat, nie odpowiadać 3x na kolejne karty.

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
| N | Zdjęcia | int / string | — | **POST-MVP (photo flow)**. W MVP pole puste. |
| O | Link do zdjęć | url | — | **POST-MVP (photo flow)**. W MVP pole puste. |
| P | ID wydarzenia Kalendarz | string | — | **W MVP populated** dla Calendar-backed next steps (per D8) — zapisujemy `event_id` zwrócony przez `events.insert`. Pole puste tylko dla no-event K values (`Czekać na decyzję klienta`, `Nic — zamknięte`, `Inne`). Reverse-lookup Calendar → Sheets to przyszły flow (vision-only), jeśli zostanie zatwierdzony. |

**Wiersz 1 (nagłówki) jest chroniony** (Protected range `A1:P1`) — handlowiec ani agent nie mogą go przepisywać, bo mapowanie kolumn przez `get_sheet_headers()` zależy od tego, żeby `H` zawsze zawierało dokładnie `"Notatki"`.

**Nigdy nie wprowadzamy:** `moc_kw`, `metraz_domu`, `metraz_dachu`, `kierunek_dachu`, `zrodlo_leada_szczegoly`, `typ_dachu`, `napiecie_sieci`. Wszystko techniczne → `H=Notatki`.

---

## 7. Typy wydarzeń Kalendarza

Wydarzenia tworzone przez agenta niosą **minimalne** `extendedProperties.private` (per D8):
- `event_type: string` — jeden z 4 typów poniżej (per D4 runtime enum).

Nie zapisujemy `client_sheet_row`, `managed_by`, `client_name` ani żadnych innych custom kluczy. Link Sheets → Calendar realizowany przez kolumnę P (`ID wydarzenia Kalendarz`), nie przez extendedProperties.

| Typ | Title | Duration | Emoji | Opis |
|---|---|---|---|---|
| `in_person` | `{imię nazwisko} ({miasto})` | 60 min | 🤝 | Spotkanie fizyczne. Lokalizacja = adres. |
| `phone_call` | `📞 {imię nazwisko} ({miasto})` | 15 min | 📞 | Rozmowa telefoniczna. Lokalizacja = telefon klienta. |
| `offer_email` | `📨 Oferta: {imię nazwisko}` | 0 min | 📨 | Termin wysłania oferty. All-day lub określona godzina. |
| `doc_followup` | `📄 Follow-up: {imię nazwisko}` | 0 min | 📄 | Przypomnienie "wrócić do klienta". |

Plan dnia filtruje po **dedykowanym OZE calendar** (events tworzone tylko w tym kalendarzu przez agenta — per D8). User-added events w OZE calendar są tolerowane: jeśli brak / nieznany `event_type`, render jako generic calendar event bez mutation assumptions.

---

## 8. Świadomie odrzucone z MVP

### 8.1. POST-MVP (wróci w późniejszej fazie)

| Funkcja | Dlaczego nie teraz |
|---|---|
| `filtruj_klientów` | Handlowiec rzadko filtruje w locie. Dla beta wystarczy `show_client` z nazwiskiem. Później może w dashboardzie. |
| `edit_client` | Pokrycie przez `add_note` + `change_status` wystarczy na MVP. Pełna edycja pola wymaga dodatkowego parsera i walidacji. |
| `lejek_sprzedazowy` | Funkcja dashboardowa, czeka na dashboard Next.js. W bocie zostaje jako referencja. |
| `multi-meeting` | Batch kilku spotkań w jednej wiadomości. MVP obsługuje single meeting tylko. |
| `voice input` | Whisper API + polski. Duża infra + post-processing dla polskich nazw własnych. |
| `Drive photos` | Zdjęcia z terenu → Drive folder klienta. Kolumny N i O w Sheets zostają puste w MVP. |
| `proactive morning brief` | Scheduler-driven, wymaga APScheduler + dedupy. |

### 8.2. Product vision only — wymaga osobnej decyzji Maana

Zgodnie z `SOURCE_OF_TRUTH.md` §4 (4-tier scope model, 14.04.2026): te pozycje są opisane w Product Vision, ale **nie są zatwierdzone jako roadmap i nie są trwale wycięte**. Każda wymaga osobnej decyzji przed wejściem do implementacji. **Router klasyfikuje je jako `VISION_ONLY`** → reply w tonie "poza aktualnym zakresem; wymaga osobnej decyzji", nie "wycięte na stałe".

**Intent-level vision** (router rozpoznaje jako `VISION_ONLY` z odpowiednim `feature_key`):

| Funkcja | Dlaczego nie w MVP | Co robi handlowiec zamiast |
|---|---|---|
| `reschedule_meeting` | Dwa flow (edycja wydarzenia + wyszukiwanie którego wydarzenia dotyczy) dla marginalnej wartości. Jedno spójne flow jest prostsze: skasuj stare, dodaj nowe. | Kasuje stare wydarzenie w Kalendarzu ręcznie i pisze `add_meeting` komendą |
| `cancel_meeting` | Irreversible delete na podstawie interpretacji tekstu to ryzyko, którego agent nie bierze na siebie. | Kasuje wydarzenie w Kalendarzu bezpośrednio |
| `free_slots` | Handlowiec widzi luki z `show_day_plan`. Osobna intencja liczenia wolnych slotów to overhead bez realnej wartości. | Patrzy na plan dnia komendą `co mam w X` |
| `delete_client` | Ryzykowna mutacja — wymaga dodatkowej ostrożności i confirmation flow. Opisane w Product Vision, ale bez zatwierdzonej mechaniki undo. | Usuwa ręcznie w Google Sheets |

**Policy/business vision** (NIE jest intencją routera — żadnego `feature_key=daily_interaction_limit`):

| Mechanizm | Dlaczego nie w MVP |
|---|---|
| `daily interaction limit (100/day)` | Product/business vision only — wymaga osobnej decyzji pricing/product przed wejściem do roadmapy. To policy/quota mechanic, nie intencja użytkownika; router tego nie klasyfikuje. Opisany w Product Vision ale bez zatwierdzonej liczby i mechaniki pożyczania. |

Klasyfikator intencji rozpoznaje wyrażenia "przełóż / zmień spotkanie / przesuń", "wolne okna / kiedy mam wolne", "odwołaj / skasuj spotkanie", "usuń klienta / skasuj z bazy" — ale tylko po to, żeby zwrócić `VISION_ONLY` + właściwy `feature_key`, a reply template odpowiada jedną linią w tonie "poza aktualnym zakresem; wymaga osobnej decyzji". Nie ma karty, nie ma flow mutacji.

### 8.3. NIEPLANOWANE — trwale poza zakresem

Te funkcje **nigdy nie wejdą do produktu** — rationale jest trwały, nie zależy od decyzji produktowej.

| Funkcja | Dlaczego trwale wycięte | Co robi handlowiec zamiast |
|---|---|---|
| `pre-meeting reminders` (po stronie agenta) | Agent nie wysyła przypomnień godzinę/30 min przed spotkaniem. Handlowiec ma Google Calendar na telefonie — native reminders działają. Duplikacja z poziomu bota to szum. | Używa natywnych przypomnień Google Calendar |
| `meeting_non_working_day_warning` | Handlowcy OZE pracują w soboty, niedziele, święta. Warning byłby fałszywym założeniem z innego segmentu. | Nic — `add_meeting` w weekend działa identycznie jak w dzień roboczy |

Router klasyfikuje te przypadki jako `UNPLANNED` z pointer do native alternative (np. "przypomnienia ustawia Google Calendar w swoich ustawieniach").

---

## 9. Zakończenie

Ten plik definiuje kontrakty 6 intencji MVP. Jeśli kod różni się od kontraktu — zmienia się kod. Jeśli kontrakt ma być zmieniony — najpierw decyzja Maana + edycja tego pliku, potem kod.

**Hierarchia SSOT:** patrz `SOURCE_OF_TRUTH.md` sekcja 5.
