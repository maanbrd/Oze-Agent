# OZE-Agent — Implementation Guide v2

> ## ⚠️ UWAGA: Ten plik jest CZĘŚCIOWO NIEAKTUALNY (stan na 11.04.2026 popołudnie)
>
> Po pełnej synchronizacji czterech plików SSOT w dniu **11.04.2026 popołudnie** ten guide zawiera kroki odwołujące się do rzeczy, które już nie są w MVP albo działają inaczej niż opisane tutaj. Konkretnie:
>
> - **Intencje wycięte na stałe** (NIEPLANOWANE — nie wracają): `reschedule_meeting`, `cancel_meeting`, `free_slots`, `meeting_non_working_day_warning`. Jeśli któryś krok w tym guide mówi "zaimplementuj reschedule" / "parser free_slots" / "flow anulowania spotkania" — **pomiń go**, to już nie jest w MVP.
> - **Intencje POST-MVP** (poza pierwszym wydaniem, wrócą później): `edit_client` (pełna edycja), `filtruj_klientów`, `lejek_sprzedazowy`. Jeśli krok dotyczy tych intencji — nie implementuj w MVP, dodaj POST-MVP banner w odpowiedzi bota zamiast pełnej logiki.
> - **Pipeline statusów: 9 nie 10.** Status `Negocjacje` został wycięty 11.04. Jeśli widzisz w tym guide `["Nowy lead", ..., "Negocjacje", ...]` — usuń `Negocjacje` z listy.
> - **Produkty: 4 nie 5.** `Klimatyzacja` została wycięta 11.04. Lista: `PV`, `Pompa ciepła`, `Magazyn energii`, `PV + Magazyn energii`. Moc (kW/kWh) zawsze do kolumny `Notatki`, nigdy do nazwy produktu.
> - **3-button cards + one-click cancel (R1).** Każda karta mutacyjna ma `[✅ Zapisać] [➕ Dopisać] [❌ Anulować]`. Jeśli krok w guide mówi `[Tak][Nie]`, `[Zapisz bez]`, `[Nowy][Aktualizuj]` — to jest stary wzorzec, wycięty. Nowy wzorzec w `agent_system_prompt.md`.
> - **R7 next_action_prompt jako free-text** (nie sztywna trójka meeting/call/not-interested). Jeśli guide mówi o trzech przyciskach po mutacji — odwróć na otwarte pytanie tekstowe.
> - **Duplicate detection: default merge + 2-button disambiguation** `[📋 Dopisz do istniejącego] [➕ Utwórz nowy wpis]`, nie stary `[Nowy][Aktualizuj]`.
> - **Compound fusion** dozwolony w MVP dla trzech kombinacji: `add_client + add_meeting`, `change_status + add_meeting`, `add_note + add_meeting` — jedna karta, nie dwie.
> - **`add_meeting` emoji differentiation:** 📅 spotkanie / 📞 telefon / 📨 follow-up dokumentowy, rozpoznawane z tego co user napisał.
> - **Schemat Sheets zamrożony na 16 kolumnach A-P** w `INTENCJE_MVP.md` sekcja 3. Kod ma być schema-agnostic (nagłówki z wiersza 1).
>
> **Hierarchia SSOT** — jeśli ten guide i cokolwiek niżej w hierarchii mówi inaczej, **wygrywa to co wyżej**:
> 1. `docs/SOURCE_OF_TRUTH.md` — decision log + mapa dokumentów
> 2. `docs/INTENCJE_MVP.md` — zamrożone kontrakty intencji + schemat Sheets + pipeline
> 3. `docs/agent_behavior_spec_v5.md` — 52 testy akceptacyjne + R1-R8 reguły
> 4. `docs/agent_system_prompt.md` — ton + wzorce odpowiedzi
> 5. `docs/CURRENT_STATUS.md` — stan bieżącej sesji + bugi + task na następną
> 6. **ten plik** — plan fazowy, częściowo stale
>
> **Jak z tego korzystać:** kiedy jesteś w trakcie konkretnego kroku implementacyjnego, **zweryfikuj każdy krok** przeciwko SSOT (punkty 1-5 wyżej) **przed napisaniem kodu**. Jeśli jest konflikt — STOP i poinformuj Maana. Używaj tego guide do kolejności kroków i micro-testów Telegram — ale nie do sprawdzania "co jest w MVP" albo "jak wygląda karta". Do tego są pliki SSOT.
>
> **Pełny przegląd i aktualizacja tego pliku** zaplanowany po przejściu audytu kodu (`docs/CODE_AUDIT_11-04-2026.md`) i fixach must-have — nie wcześniej, bo dopóki nie wiemy co zostaje a co wypada, przepisywanie guide'a to marnowanie czasu.

## How to use this document

This guide is for **Claude Code** building the bot, and for **you (Maan)** testing it manually in Telegram.

### Structure
- Phases are sequential: finish Phase N before starting Phase N+1
- Each phase has micro-steps with status: ✅ DONE / ⚠️ PARTIAL / ⏳ TODO
- Each micro-step ends with **3 manual tests** — you type/record in Telegram, check the response
- Test format:
  - **YOU SEND:** what you type or record in Telegram
  - **BOT SHOULD REPLY:** expected response
  - **FAIL IF:** what makes the test fail

### Phase order
```
Phase 1: Sheets — add client                       ✅ DONE
Phase 2: Sheets — search / edit / status / dupes   ⏳ TODO
Phase 3: Calendar                                  ⚠️ PARTIAL (1 step done)
Phase 4: Drive (photos)                            ⏳ TODO
Phase 5: Voice input                               ⏳ TODO
Phase 6: Proactive messages (brief + evening)      ⏳ TODO
Phase 7: Lejek + reminders + error handling        ⏳ TODO
```

### Lessons learned (apply to all new steps)

These are things we discovered during Phase 1 + Phase 3.1 implementation. Apply to every new step:

1. **Claude API returns JSON wrapped in markdown code fences.** All `extract_*` functions must strip ` ```json ` and ` ``` ` before `json.loads`. This bit us twice (extract_client_data, extract_meeting_data).
2. **Card must display EVERY non-empty field** from pending record, not just core fields. Users need to see what they're confirming.
3. **Missing fields list must use exact column names** from user's sheet (fetched via sheet columns cache). Never hardcode field names.
4. **Never show system fields** as missing: Data pierwszego kontaktu, Data ostatniego kontaktu, Status, Zdjęcia, Link do zdjęć, ID kalendarza, Email, Notatki, Następny krok (at creation time).
5. **Merge flow:** when user sends supplementary data, parse it as partial field data and merge into pending record. Re-show updated card with fewer missing fields.
6. **Timezone:** all calendar times are Europe/Warsaw local. Store as local time, not UTC.
7. **Response after save:** one line only. "✅ Zapisane." for clients. "✅ Spotkanie dodane do kalendarza." for calendar events. No filler.
8. **Banned phrases are STRICT.** Zero tolerance. Run regex check on every response.
9. **Dates from Google Sheets can arrive as Excel serial integers** (e.g. 46120 = a date in 2026). ALL date fields must be converted to DD.MM.YYYY before display. Use `_fmt_date()` from `shared/formatting.py`. Apply to every place that renders client data.
10. **Never expose internal data to the user.** Row numbers (`_row`), raw API values, internal IDs — must be filtered in `SKIP_FIELDS` or `format_client_card`. Every field shown to the user must pass through `formatting.py`.
11. **Temporal guard is precise — movement verbs are NOT time markers.** "jestem u Nowaka" must NOT create a calendar event. Only genuine time words belong in `_TEMPORAL_MARKERS`: day names, "jutro", "pojutrze", "wpół", "kwadrans", "spotkanie". Extend `_TIME_RE` regex instead of adding verbs to the marker set.
12. **Garbage input must fail fast.** Confidence guard: if `classify_intent` returns `confidence < 0.5`, force intent to `general_question`. Add a garbage example to the classifier prompt (`confidence: 0.1`). Never let random strings reach `extract_client_data`.
13. **Pending flow must never block the user.** The `_route_pending_flow` function must return a bool. If a non-confirmation message arrives during a non-add_client flow, auto-cancel the flow and process the message normally. "State-lock" (freezing the bot until user types "tak"/"nie") is unacceptable for a field sales tool.
14. **Polish name inflection breaks exact-match search.** "Kowalskiego" (locative) won't match stored "Kowalski" (nominative). Add `_strip_polish_suffix()` to `google_sheets.search_clients` and try both raw and suffix-stripped queries.

---

## PHASE 1: Sheets — Add Client ✅ DONE

Goal: Bot parses text messages, extracts client data, shows confirmation card, writes to Google Sheets on confirm.

### Status: All 4 steps passing in manual tests.

### Current behavior (confirmed working)

**Card format:**
```
📋 Jurek Jurek, ul. Smutna 23, Wołomin
Magazyn energii
Tel. 777 777 777
Następny krok: 10 kW
Źródło: Facebook
❓ Brakuje: [only user-relevant fields]
Zapisać / dopisać / anulować?
```
Button: `[✅ Zapisz]`

**Flow:**
- User sends text → card appears with parsed data + missing fields
- User taps `[✅ Zapisz]` → row written to Sheets → "✅ Zapisane."
- User sends more data (e.g. "źródło pozyskania Facebook") → card updated with new data, fewer missing fields
- User sends "anuluj" → "Anulować? [Tak] [Nie]" → "🫡 Anulowane."

### Regression tests (run these whenever Phase 1 code is touched)

**Test 1 — minimal input:**
```
YOU SEND:    Nowak Piaseczno 601234567 pompa

BOT SHOULD REPLY:
📋 Nowak, Piaseczno
Pompa ciepła
Tel. 601 234 567
❓ Brakuje: Adres, Źródło pozyskania
Zapisać / dopisać / anulować?
[✅ Zapisz]

FAIL IF:
- Any banned phrase appears
- "Pompa" not mapped to "Pompa ciepła"
- System fields (Data pierwszego kontaktu, Status, etc.) appear in missing list
```

**Test 2 — full save + merge:**
```
YOU SEND:    Nowak Piaseczno 601234567 pompa dom 120m2
BOT REPLIES: card with Nowak, Pompa ciepła, 120m², phone, ❓ missing: Adres, Źródło pozyskania
YOU SEND:    ul. Leśna 5, źródło facebook
BOT REPLIES: updated card with Adres: Leśna 5, Źródło: Facebook, no missing fields
YOU TAP:     [✅ Zapisz]
BOT REPLIES: ✅ Zapisane.

CHECK GOOGLE SHEETS:
- Row with Nowak, Leśna 5, Piaseczno, Pompa ciepła, 120, 601234567, Facebook
- Status = "Nowy lead"
- Data pierwszego kontaktu = today

FAIL IF:
- Any field missing in Sheets
- Merge dropped any user-provided data
```

**Test 3 — cancel flow:**
```
YOU SEND:    Testowy Testowo 111222333 pompa
BOT REPLIES: card
YOU SEND:    anuluj
BOT REPLIES: Anulować? [Tak] [Nie]
YOU TAP:     [Tak]
BOT REPLIES: 🫡 Anulowane.

CHECK SHEETS: NO row with "Testowy" exists

FAIL IF: row written despite cancellation
```

---

## PHASE 2: Sheets — Search / Edit / Status / Duplicates ⏳ TODO

Goal: Complete the Sheets CRUD. User can find, edit, update status, and avoid duplicates.

**Prerequisite:** Phase 1 passing.

---

### Step 2.1: Search client by name ⏳ TODO

**What Claude Code builds:**
When user asks about a client, search Sheets by name. Fuzzy match (case-insensitive, Polish diacritics tolerant, typo tolerant via Levenshtein). Return:
- Single match → formatted client card
- Multiple matches → numbered list (max 10)
- 50+ matches → link to Sheets
- Typo → "Chodziło o X?" suggestion

**Reference:** `agent_system_prompt.md` → Response patterns: Searching for a client

**Test 1 — single match:**
```
(Kowalski exists in Sheets)
YOU SEND:    Co mam o Kowalskim?

BOT SHOULD REPLY:
📋 Kowalski — Piłsudskiego 12, Warszawa
Produkt: PV
Tel. 600 123 456
Status: Oferta wysłana
Źródło: Facebook
Notatki: moc PV 8kW, dom 160m², dach 40m² płd., chce wycenę, żona się boi

FAIL IF:
- Bot says "Szukam..." and nothing else follows
- Data doesn't match what's in Sheets
- Any banned phrase appears
```

**Test 2 — typo tolerance:**
```
YOU SEND:    Kowalsky

BOT SHOULD REPLY:
Nie mam "Kowalsky". Chodziło o Kowalskiego z Warszawy?
[Tak] [Nie]

FAIL IF:
- Bot says "Nie znaleziono" without suggesting match
- Bot silently returns Kowalski without mentioning typo
```

**Test 3 — multiple matches:**
```
(add 2 Nowaków — Warszawa and Piaseczno)
YOU SEND:    Pokaż Nowaka

BOT SHOULD REPLY:
Mam 2 Nowaków:
1. Nowak — Warszawa
2. Nowak — Piaseczno
Którego?

FAIL IF:
- Bot picks one without asking
- Bot shows full data for both
```

---

### Step 2.2: Edit client data ⏳ TODO

**What Claude Code builds:**
Parse edit requests. Find client. Show old vs new value. On confirmation, update cell in Sheets.

**Reference:** `agent_system_prompt.md` → R5, Response patterns

**Test 1 — change phone:**
```
YOU SEND:    Zmień telefon Kowalskiego na 601234567

BOT SHOULD REPLY:
Kowalski — telefon:
Stary: 600 123 456
Nowy: 601 234 567
Zamienić czy dodać drugi?
[Zamień] [Dodaj drugi]

YOU TAP:     [Zamień]
BOT REPLIES: ✅ Zapisane.
CHECK SHEETS: phone updated

FAIL IF:
- Bot overwrites without showing old vs new
- Bot doesn't offer "dodaj drugi" option
```

**Test 2 — update measurement:**
```
YOU SEND:    Kowalski ma 45 metrów dachu, nie 40

BOT SHOULD REPLY:
Kowalski — metraż dachu:
Było: 40m²
Będzie: 45m²
Zmienić?
[Tak] [Nie]

FAIL IF: bot changes without confirmation
```

**Test 3 — append note:**
```
YOU SEND:    Dodaj notatkę do Kowalskiego: interesuje się też magazynem

BOT SHOULD REPLY:
Kowalski — notatki:
Dodaję: "interesuje się też magazynem"
Zapisać?
[Tak] [Nie]

YOU TAP:     [Tak]
CHECK SHEETS: note appended (not replaced)

FAIL IF: old notes overwritten
```

---

### Step 2.3: Change client status ⏳ TODO

**What Claude Code builds:**
Detect status change intent from natural language. Map to correct lejek status. Show confirmation. Update Status + Data ostatniego kontaktu.

**Reference:** `agent_system_prompt.md` → Response patterns: Status change

**Test 1 — direct:**
```
YOU SEND:    Kowalski podpisał!

BOT SHOULD REPLY:
🫡 Kowalski → Podpisane?
[Tak] [Nie]

YOU TAP:     [Tak]
CHECK SHEETS: Status = "Podpisane", Data ostatniego kontaktu = today

FAIL IF:
- Bot asks "Jaki status?" instead of deducing
- Status not updated after confirm
```

**Test 2 — indirect language:**
```
YOU SEND:    Wysłałem ofertę Nowakowi

BOT SHOULD REPLY:
Nowak → Oferta wysłana?
[Tak] [Nie]

FAIL IF: bot doesn't map "wysłałem ofertę" → "Oferta wysłana"
```

**Test 3 — rejection:**
```
YOU SEND:    Wiśniewski rezygnuje

BOT SHOULD REPLY:
Wiśniewski → Odrzucone?
[Tak] [Nie]

FAIL IF:
- Bot asks "Dlaczego?"
- Bot comments on rejection
```

---

### Step 2.4: Duplicate detection ⏳ TODO

**What Claude Code builds:**
Before appending a new client, check if name + city combo already exists. If yes, warn and offer [Nowy] [Aktualizuj]. Never block.

**Reference:** `agent_system_prompt.md` → Duplicate client, R4

**Test 1 — duplicate found:**
```
(Kowalski, Warszawa already in Sheets)
YOU SEND:    Kowalski Warszawa PV 10kW tel 609999999

BOT SHOULD REPLY:
⚠️ Masz już Kowalskiego z Warszawy (Piłsudskiego 12, PV).
Dodać nowego czy zaktualizować?
[Nowy] [Aktualizuj]

FAIL IF:
- Bot adds without warning
- Bot blocks the operation
```

**Test 2 — same name, different city:**
```
YOU SEND:    Kowalski Piaseczno pompa tel 608888888

BOT SHOULD REPLY: normal add-client card, NO duplicate warning

FAIL IF: bot warns about Kowalski from Warszawa
```

**Test 3 — user chooses [Nowy]:**
```
YOU TAP:     [Nowy]
BOT REPLIES: ✅ Zapisane.
CHECK SHEETS: two Kowalski rows exist (Warszawa and new)

FAIL IF:
- Bot questions the decision
- Only one row exists
```

---

## PHASE 3: Calendar ⚠️ PARTIAL

Goal: Bot creates, reads, edits, deletes calendar events. Links to client data from Sheets.

**Prerequisite:** Phase 2 passing.

---

### Step 3.1: Add single meeting ✅ DONE

**Status:** Working. Timezone bug fixed. Title, location, description populated from Sheets.

**Current behavior:**
```
YOU SEND:    jutro spotkanie z jurkiem o 14

BOT REPLIES:
📅 Dodać spotkanie?
Jurek Jurek — Smutna 23, Wołomin
[tomorrow's date], 14:00-15:00
[✅ Dodaj]

YOU TAP:     [✅ Dodaj]
BOT REPLIES: ✅ Spotkanie dodane do kalendarza.
```

Google Calendar event contains:
- Title: "Spotkanie z Jurek Jurek"
- Time: 14:00-15:00 Europe/Warsaw
- Location: "Smutna 23, Wołomin"
- Description: phone, product, power, notes, next step from Sheets

### Regression tests

**Test 1 — known client:**
```
YOU SEND:    jutro o 10 jadę do Kowalskiego

BOT SHOULD REPLY:
📅 Dodać spotkanie?
Kowalski — Piłsudskiego 12, Warszawa
[tomorrow], 10:00-11:00
[✅ Dodaj]

YOU TAP:     [✅ Dodaj]
CHECK GOOGLE CALENDAR: event with address in location, full details in description

FAIL IF:
- Missing address
- Wrong timezone (e.g. 12:00 instead of 10:00)
- Ubogi title
```

**Test 2 — Polish time format:**
```
YOU SEND:    wpół do ósmej jestem u Nowaka

BOT SHOULD REPLY: card with 7:30-8:30

FAIL IF:
- Bot asks "O której dokładnie?"
- Wrong time
```

**Test 3 — unknown client:**
```
YOU SEND:    jutro o 14 spotkanie z Mazurem
(Mazur NOT in Sheets)

BOT SHOULD REPLY: calendar card WITHOUT address
YOU TAP:     [✅ Dodaj]
BOT SHOULD THEN ASK:
🫵 Mazur nie jest w bazie. Dodać? [Tak] [Nie]

FAIL IF:
- Bot refuses to create event for unknown client
- Bot doesn't offer to add client after event
```

---

### Step 3.2: Add multiple meetings from one message ⏳ TODO

**What Claude Code builds:**
Parse multiple meetings from single message. Create all in batch. After saving, ask about any new clients.

**Test 1 — three meetings:**
```
YOU SEND:    jutro o 10 Kowalski, o 14 Nowak, o 17 Wiśniewski

BOT SHOULD REPLY:
📅 Dodać spotkania?
10:00 Kowalski — Piłsudskiego 12, Warszawa
14:00 Nowak — Leśna 5, Piaseczno
17:00 Wiśniewski — Kościuszki 8, Legionowo
[✅ Dodaj]

YOU TAP:     [✅ Dodaj]
CHECK CALENDAR: 3 separate events

FAIL IF:
- Only 1 event created
- Addresses missing from any
```

**Test 2 — mix known + unknown:**
```
YOU SEND:    jutro o 10 Kowalski, o 14 Mazur
(Mazur not in Sheets)

YOU TAP:     [✅ Dodaj]
BOT REPLIES: ✅ Spotkania dodane.
THEN: 🫵 Mazur nie jest w bazie. Dodać? [Tak] [Nie]

FAIL IF:
- Bot asks about Mazur BEFORE creating events
- Only 1 event created
```

**Test 3 — cancel batch:**
```
YOU SEND:    jutro o 10 Kowalski, o 14 Nowak
BOT SHOWS: card
YOU SEND:    anuluj
BOT: Anulować? [Tak] [Nie]
YOU TAP:     [Tak]
BOT: 🫡 Anulowane.

CHECK CALENDAR: NO new events

FAIL IF: any events created
```

---

### Step 3.3: Show day plan ⏳ TODO

**What Claude Code builds:**
Fetch events from Calendar for requested day. Enrich with client status from Sheets. Format as compact list.

**Test 1 — today with meetings:**
```
(create 2-3 meetings for today first)
YOU SEND:    Co mam dziś?

BOT SHOULD REPLY:
📅 Dziś [date]:
10:00 Kowalski — Piłsudskiego 12, Warszawa — oferta wysłana
14:00 Nowak — Leśna 5, Piaseczno — nowy lead

FAIL IF:
- Missing addresses
- Missing statuses
- Longer than 15 lines
```

**Test 2 — empty day:**
```
YOU SEND:    Co mam w niedzielę?

BOT SHOULD REPLY:    📅 Niedziela [date]: brak spotkań.

FAIL IF:
- More than 1 line
- Any "Czy chcesz..." follow-up
```

**Test 3 — free slots:**
```
YOU SEND:    Wolne okna jutro?

BOT SHOULD REPLY:
📅 Jutro [date]:
Zajęte: 10:00-11:00, 14:00-15:00
Wolne: do 10:00, 11:00-14:00, po 15:00

FAIL IF: bot lists each hour individually
```

---

### Step 3.4: Reschedule meeting ⏳ TODO

**What Claude Code builds:**
Parse reschedule request. Show old vs new. Update Calendar + Sheets.

**Test 1 — simple reschedule:**
```
YOU SEND:    Przełóż Kowalskiego na piątek o 10

BOT SHOULD REPLY:
📅 Kowalski:
Było: [current] 14:00
Będzie: piątek [date] 10:00
Przenieść?
[Tak] [Nie]

YOU TAP:     [Tak]
CHECK: event moved, Sheets "Data następnego kontaktu" updated

FAIL IF:
- Old event stays + new one created (should be moved)
- Sheets date not updated
```

**Test 2 — reschedule creates conflict:**
```
(create Friday 10:00 event for Nowak)
YOU SEND:    Przełóż Kowalskiego na piątek o 10

BOT SHOULD REPLY:
⚠️ Piątek o 10:00 masz już Nowaka. Przenieść mimo to?
[Tak] [Zmień godzinę]

FAIL IF: bot silently moves or blocks
```

**Test 3 — cancel reschedule:**
```
YOU SEND:    Przełóż Kowalskiego na poniedziałek
BOT SHOWS: confirmation
YOU TAP:     [Nie]
CHECK: event unchanged

FAIL IF: event was moved
```

---

### Step 3.5: Cancel meeting ⏳ TODO

**What Claude Code builds:**
Parse cancellation. Show meeting details. Delete on confirmation.

**Test 1 — simple cancel:**
```
YOU SEND:    Odwołaj Nowaka

BOT SHOULD REPLY:
Usunąć spotkanie z Nowakiem jutro o 14:00?
[Tak] [Nie]

YOU TAP:     [Tak]
BOT REPLIES: 🫡 Odwołane.
CHECK CALENDAR: event deleted

FAIL IF:
- Bot asks "Dlaczego?"
- More than 1 line after confirmation
```

**Test 2 — ambiguous:**
```
(two meetings with Kowalski this week)
YOU SEND:    Odwołaj Kowalskiego

BOT SHOULD REPLY:
Masz 2 spotkania z Kowalskim:
1. Środa 14:00
2. Piątek 10:00
Które odwołać?

FAIL IF: bot deletes both or picks one
```

**Test 3 — non-existent:**
```
YOU SEND:    Odwołaj Mazura
(no meeting with Mazur)

BOT SHOULD REPLY:    Nie masz spotkania z Mazurem.

FAIL IF: more than 1 line
```

---

### Step 3.6: Combined client + meeting in one message ⏳ TODO

**What Claude Code builds:**
When a message contains BOTH client data AND meeting intent (e.g. "Kowalski Warszawa 600123456 pompa jutro o 14"), handle both in one flow with one combined confirmation card.

**Important lesson learned:** In earlier testing we saw routing confusion — messages with both client+meeting got sent to only the meeting handler, losing client data. This step fixes that.

**Test 1 — client + meeting:**
```
YOU SEND:    Jerzy Nowak 601234567 Warszawa Marszałkowska 10 pompa jutro o 14

BOT SHOULD REPLY:
📋 Jerzy Nowak, Marszałkowska 10, Warszawa
Pompa ciepła
Tel. 601 234 567
📅 Spotkanie: jutro [date] 14:00-15:00
❓ Brakuje: [any missing]
Zapisać / dopisać / anulować?
[✅ Zapisz]

YOU TAP:     [✅ Zapisz]
BOT REPLIES: ✅ Zapisane + spotkanie dodane.
CHECK: row in Sheets + event in Calendar

FAIL IF:
- Only client saved (meeting lost)
- Only meeting created (client not in Sheets)
- Two separate cards shown
```

**Test 2 — routing decision:**
```
YOU SEND:    jutro o 10 jadę do Kowalskiego
(Kowalski already in Sheets)

This must route to meeting handler only (no client add).

FAIL IF: bot tries to add Kowalski as new client
```

**Test 3 — new client via meeting shortcut:**
```
YOU SEND:    jutro o 10 Zieliński Radom
(Zieliński not in Sheets)

BOT SHOULD REPLY: meeting card, then ask "🫵 Zieliński nie jest w bazie. Dodać?"

FAIL IF: bot refuses or skips the add-client question
```

---

## PHASE 4: Drive — Photos ⏳ TODO

Goal: Bot stores photos in client folders on Google Drive. Links folders in Sheets.

**Prerequisite:** Phase 2 passing.

---

### Step 4.1: Receive photos and assign to client ⏳ TODO

**Test 1 — single photo:**
```
YOU SEND:    1 photo
BOT REPLIES: 📸 1 zdjęcie. Do którego klienta?
YOU SEND:    Kowalski Warszawa
BOT REPLIES: 📸 1 zdjęcie → Kowalski, Warszawa. Zapisać? [Tak] [Nie]
YOU TAP:     [Tak]
BOT REPLIES: ✅ Zapisane.

CHECK DRIVE: folder "Kowalski - Warszawa" has photo
CHECK SHEETS: "Zdjęcia" column has link

FAIL IF:
- Photo not on Drive
- Sheets not updated
```

**Test 2 — multiple photos:**
```
YOU SEND:    5 photos (one after another)
BOT REPLIES: 📸 5 zdjęć. Do którego klienta?
(bot batches photos, asks once)

FAIL IF: bot asks after each photo separately
```

**Test 3 — unknown client:**
```
YOU SEND:    1 photo
BOT REPLIES: 📸 1 zdjęcie. Do którego klienta?
YOU SEND:    Mazur Radom
(not in Sheets)

BOT SHOULD REPLY:    Nie mam Mazura z Radomia w bazie.

FAIL IF: bot creates folder for non-existent client
```

---

## PHASE 5: Voice Input ⏳ TODO

Goal: Bot processes voice messages — transcription + parsing + all previous phase operations.

**Prerequisite:** Phase 2 passing. Phase 3 recommended.

---

### Step 5.1: Voice → transcription → client data ⏳ TODO

**Test 1 — clear voice, new client:**
```
YOU RECORD:  "Byłem u Kowalskiego na Piłsudskiego dwanaście w Warszawie, dom sto sześćdziesiąt metrów, dach czterdzieści na południe, PV-ka ósemka, telefon sześćset sto dwadzieścia trzy czterysta pięćdziesiąt sześć"

BOT SHOWS:   🎙️ Transkrybuję... → 🔍 Analizuję...
BOT REPLIES: standard add-client card with all parsed fields

FAIL IF:
- Bot shows transcription when quality is good
- PV-ka not mapped to PV
- Numbers not parsed
```

**Test 2 — emotional voice:**
```
YOU RECORD:  "Kurde prawie miałem gościa Wiśniewski z Legionowa Kościuszki osiem PV-ka szóstka żona go przekręciła follow-up za tydzień numer sześćset dwa trzysta czterdzieści pięć sześćset siedemdziesiąt osiem"

BOT SHOULD REPLY: card with all fields, follow-up set to +7 days

FAIL IF:
- Emotional words break parser
- Follow-up not detected
- "szóstka" not mapped to 6kW
```

**Test 3 — noisy audio:**
```
YOU RECORD:  short/noisy voice

EXPECTED:
Low confidence → show transcription + "Dobrze usłyszałem? [Tak] [Nagraj ponownie]"
Timeout (60s) → "Wystąpił problem, spróbuj ponownie."

FAIL IF:
- Bot crashes
- Apologizes
- Gives stack trace
```

---

### Step 5.2: Voice → multi-client update (evening follow-up response) ⏳ TODO

**Test 1 — three clients in one voice:**
```
YOU RECORD:  "Z Kowalskim super, chce wycenę na ósemkę, wyślę jutro. Nowak nie był w domu, trzeba przełożyć na przyszły tydzień. U Wiśniewskiego złożyłem ofertę."

BOT SHOULD REPLY:
📋 Zrozumiałem:
1. Kowalski → wysłać ofertę, follow-up jutro
2. Nowak — nie był w domu, przełożyć
3. Wiśniewski → oferta złożona

Statusy:
Kowalski: Oferta wysłana
Wiśniewski: Oferta wysłana

Zapisać?
[Tak] [Nie]

FAIL IF:
- Only first client handled
- Bot asks per client
```

**Test 2 — mixed slang:**
```
YOU RECORD:  "Mazur bierze pompeczkę i magazyn, wyślę umowę pojutrze. Zieliński spał."

BOT SHOULD REPLY:
📋 Zrozumiałem:
1. Mazur → pompa ciepła + magazyn energii, wysłać umowę [date]
2. Zieliński — nie był w domu

FAIL IF:
- "pompeczkę" not mapped
- "spał" not understood
```

**Test 3 — voice with calendar intent:**
```
YOU RECORD:  "Do Kowalskiego jadę w piątek o dziesiątej, a Nowaka trzeba przełożyć na przyszły wtorek o czternastej"

BOT SHOULD REPLY: calendar confirmations for both operations

FAIL IF:
- Only one operation handled
- Wrong dates
```

---

## PHASE 6: Proactive Messages ⏳ TODO

Goal: Bot sends morning brief + evening follow-up automatically.

**Prerequisite:** Phase 2 + 3 passing.

---

### Step 6.1: Morning brief ⏳ TODO

**Test 1 — full day:**
```
(set brief hour to now, wait)

BOT SENDS (automatically):
🫡 Plan na [date]:

10:00 Kowalski — Piłsudskiego 12, Warszawa — oferta wysłana
14:00 Nowak — Leśna 5, Piaseczno — nowy lead

📋 Follow-upy:
• Mazur — wysłać ofertę

Lejek: X nowych, Y umówionych, Z ofert, W negocjacje

FAIL IF:
- Missing addresses/statuses
- Contains "Udanego dnia!" or any greeting
- Sent on non-working day
```

**Test 2 — no meetings, some follow-ups:**
```
(clear calendar for tomorrow)

BOT SENDS:
🫡 Plan na [date]:

📋 Follow-upy:
• Mazur — wysłać ofertę

Lejek: X nowych...

FAIL IF:
- Bot says "Brak spotkań na dziś" as separate section
- Skips message entirely
```

**Test 3 — no motivational content:**
```
Output must NOT contain:
- Udanego dnia
- Powodzenia
- Any greeting
- Emoji outside functional set (🫡 📋 📅 ❓ ✅ ⚠️)
```

---

### Step 6.2: Evening follow-up ⏳ TODO

**Test 1 — unreported meetings exist:**
```
(3 meetings today, 0 reported)

BOT SENDS (after last meeting + 2h):
🫵 Nieraportowane spotkania:
• Kowalski (10:00)
• Nowak (14:00)
• Wiśniewski (17:00)

Uzupełnisz? Jutro nie będziesz tak dobrze pamiętał.

FAIL IF:
- Missing unreported meeting
- Sent before last meeting ended
- Extra filler beyond motivating line
```

**Test 2 — all reported:**
```
(3 meetings, all reported during day)

BOT SENDS:    NOTHING

FAIL IF: bot sends "Wszystko uzupełnione!"
```

**Test 3 — partial reporting:**
```
(3 meetings, 1 reported)

BOT SENDS:
🫵 Nieraportowane spotkania:
• Nowak (14:00)
• Wiśniewski (17:00)

FAIL IF: includes already-reported Kowalski
```

---

## PHASE 7: Lejek + Reminders + Error Handling ⏳ TODO

---

### Step 7.1: Lejek sprzedażowy summary ⏳ TODO

**Test 1 — normal lejek:**
```
YOU SEND:    Ilu mam klientów?

BOT SHOULD REPLY:
📋 Lejek:
Nowy lead: X
Spotkanie umówione: Y
Oferta wysłana: Z
Negocjacje: W
Podpisane: V
Odrzucone: U

Szczegóły → [link]

FAIL IF:
- Bot lists individual client names
- Longer than 10 lines
```

**Test 2 — alternative phrasing:**
```
YOU SEND:    Pokaż lejek
BOT SHOULD REPLY: same format

FAIL IF: bot doesn't understand "lejek"
```

**Test 3 — empty:**
```
(new user, 0 clients)
YOU SEND:    Ilu mam klientów?
BOT SHOULD REPLY:    📋 Lejek: 0 klientów.

FAIL IF: more than 1 line
```

---

### Step 7.2: Follow-up reminders ⏳ TODO

**Test 1 — set reminder:**
```
YOU SEND:    Przypomnij zadzwonić do Nowaka w piątek

BOT SHOULD REPLY:
⏰ Piątek [date] — zadzwonić do Nowaka. Ustawić?
[Tak] [Nie]

FAIL IF:
- Set without confirmation
- Wrong date
```

**Test 2 — relative date:**
```
YOU SEND:    Follow-up Kowalski za 3 dni
Output: ⏰ [date +3] — follow-up Kowalski. Ustawić?
```

**Test 3 — delivery:**
```
(set reminder for now + 1 min)
BOT SENDS at scheduled time: ⏰ Przypomnienie: zadzwonić do Nowaka

FAIL IF:
- Not delivered
- Wrong time
- Extra filler
```

---

### Step 7.3: Error handling ⏳ TODO

**Test 1 — Google API failure (simulate by revoking token):**
```
YOU SEND:    Dodaj klienta Testowy Testowo 111222333

BOT SHOULD REPLY:
Google Sheets chwilowo niedostępne. Dane NIE zapisane. Spróbuj za kilka minut.

FAIL IF:
- "Przepraszam za utrudnienia"
- Stack trace in message
- Data written to Supabase as fallback
- More than 2 lines
```

**Test 2 — interaction limit (set limit to 3):**
```
(send 3 messages)
YOU SEND: 4th message

BOT SHOULD REPLY:
Limit na dziś wyczerpany. Jutro masz [X] interakcji.

FAIL IF: bot processes the message
```

**Test 3 — unintelligible:**
```
YOU SEND:    asdkjfhaskdjfh

BOT SHOULD REPLY:    Co chcesz zrobić?

FAIL IF:
- Bot tries to parse gibberish
- "Nie rozumiem Twojej wiadomości. Proszę spróbować ponownie."
- More than 1 line
```

---

## Global Tone Check (run after any phase)

Run these on recent bot outputs to catch tone regressions.

**Regex check — banned phrases:**
```
FAIL if any bot response matches:
/oczywiście|z przyjemnością|świetnie|doskonały|czy mogę.*pomóc|mam nadzieję|nie ma problemu|dziękuję za cierpliwość|przepraszam|rozumiem twoją|na podstawie twojej|przygotowałem dla|udanego dnia|powodzenia/i
```

**Length check:**
```
- Confirmations: ≤ 1 line
- Data cards: ≤ 8 lines
- Day plan: ≤ 15 lines
- Morning brief: ≤ 20 lines
- Errors: ≤ 2 lines
```

**Unprompted suggestion check:**
```
After any completed operation, verify bot response does NOT contain:
- "Może warto..."
- "Chcesz jeszcze..."
- "Mogę też..."
- Any question not requested by the user
```
