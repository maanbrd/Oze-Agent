# OZE-Agent — Implementation Guide for Claude Code

## How to use this document

This guide is for **Claude Code** building the bot, and for **you (Maan)** testing it manually in Telegram.

### Structure
- Phases are sequential: finish Phase 1 before starting Phase 2
- Each phase has micro-steps
- Each micro-step ends with **3 manual tests** — you type/record in Telegram, check the response
- Format of each test:
  - **You send:** what you type or record in Telegram
  - **Bot should reply:** expected response
  - **FAIL if:** what makes the test fail

### Phase dependencies
```
Phase 1: Core text parsing + tone (no API calls)
Phase 2: Google Sheets integration (write/read/edit/search)
Phase 3: Google Calendar integration (requires Phase 2 — pulls client addresses)
Phase 4: Google Drive integration (requires Phase 2 — links to client records)
Phase 5: Voice input (requires Phase 2 — writes parsed data to Sheets)
Phase 6: Proactive messages (requires Phase 2 + 3)
Phase 7: Lejek, follow-ups, error handling
```

---

## PHASE 1: Core Text Parsing + Tone + Sheets Write

Goal: Bot understands text messages, extracts client data, responds in correct tone, and writes to Google Sheets on confirmation.

---

### Step 1.1: Parse text into client data and show confirmation ✅ DONE

**What Claude Code builds:**
Message handler that takes free-text input, extracts client fields (name, city, address, phone, product, measurements), maps OZE slang to canonical names, formats a confirmation card, and writes to Sheets when user taps [Tak].

**Reference:** `agent_system_prompt.md` → OZE slang table, R1, R2, Response patterns: Adding a client

**Card format (actual):**
```
📋 [Imię i nazwisko], [Adres], [Miasto]
[Produkt] [Moc]kW | dom [X]m², dach [Y]m² [dir.]
Tel. [XXX XXX XXX]
❓ Brakuje: [exact column names from sheet]
Zapisać czy jeszcze coś dopiszesz?
[Tak]
```

**Notes:**
- Single [Tak] button (no [Zapisz bez])
- Missing fields = exact column names from user's Google Sheet (never guessed names)
- System fields never shown as missing: Status, Notatki, Email, Następny krok, Zdjęcia, Link do zdjęć, ID kalendarza, Data pierwszego kontaktu, Data ostatniego kontaktu, Dodatkowe info

**Test 1 — minimal input:**
```
YOU SEND:    "Nowak Piaseczno 601234567 pompa"

BOT SHOULD REPLY:
📋 Nowak, Piaseczno
Pompa ciepła
Tel. 601 234 567
❓ Brakuje: Adres, [remaining user columns]
Zapisać czy jeszcze coś dopiszesz?
[Tak]

FAIL IF:
- Bot says "Oczywiście!" or "Z przyjemnością!" or any banned phrase
- Bot asks about fields one by one instead of listing all at once
- Bot doesn't map "pompa" → "Pompa ciepła"
- Response longer than 8 lines
- Shows [Zapisz bez] button
- Shows system fields (Status, Notatki etc.) as missing
```

**Test 2 — full input with slang:**
```
YOU SEND:    "Kowalski Piłsudskiego 12 Warszawa dom 160m2 dach 40 południe PV-ka 8kW tel 600123456"

BOT SHOULD REPLY:
📋 Kowalski, Piłsudskiego 12, Warszawa
PV 8kW | dom 160m², dach 40m² płd.
Tel. 600 123 456
❓ Brakuje: [remaining user columns]
Zapisać czy jeszcze coś dopiszesz?
[Tak]

FAIL IF:
- Bot asks "Co to jest PV-ka?"
- Bot doesn't combine metraż/dach/kierunek into compact format
- Missing fields list is incomplete or shows guessed names
```

**Test 3 — sloppy input, mixed order:**
```
YOU SEND:    "tel 602345678 Wiśniewski Legionowo magazyn dom 200"

BOT SHOULD REPLY:
📋 Wiśniewski, Legionowo
Magazyn energii, dom 200m²
Tel. 602 345 678
❓ Brakuje: Adres, [remaining user columns]
Zapisać czy jeszcze coś dopiszesz?
[Tak]

FAIL IF:
- Bot complains about message format
- Bot doesn't map "magazyn" → "Magazyn energii"
- Bot asks "Czy to nowy klient?" or any unnecessary question
```

---

### Step 1.2: Handle confirmation buttons and cancellation ✅ DONE

**What Claude Code builds:**
[Tak] writes to Sheets and replies "✅ Zapisane." Text equivalents of "tak" work too ("ok", "dobra", "spoko", "zapisz"). "nie" triggers cancel flow. After cancel prompt, user can type correction instead of tapping — bot merges and re-shows card.

**Reference:** `agent_system_prompt.md` → R1, R6

**Test 1 — confirm with button:**
```
(after Step 1.1 card)
YOU TAP:     [Tak]

BOT SHOULD REPLY:    ✅ Zapisane.
CHECK SHEETS: new row written

FAIL IF:
- More than 1 line
- Bot says "Klient został dodany" or any extra text
- No row in Sheets
```

**Test 2 — cancel flow:**
```
(after Step 1.1 card)
YOU TAP:     [Nie] (from "Anulować? [Tak][Nie]" prompt)
             — wait, [Nie] is NOT on the initial card. Card has only [Tak].
             To cancel, user types "nie".

YOU SEND:    "nie"
BOT SHOULD REPLY:    Anulować? [Tak] [Nie]
YOU TAP:     [Tak]
BOT SHOULD REPLY:    🫡 Anulowane.

FAIL IF:
- More than 3 messages total for cancellation
- Bot asks "Dlaczego?" or "Co chcesz zmienić?"
- Row written to Sheets despite cancellation
```

**Test 3 — correction after "nie":**
```
YOU SEND:    "nie"
BOT SHOULD REPLY:    Anulować? [Tak] [Nie]
YOU SEND:    "nie, adres to Leśna 5"

BOT SHOULD REPLY: updated card with Leśna 5, same format as Step 1.1, [Tak] button

FAIL IF:
- Bot discards data and starts over
- Bot ignores the correction
- Bot asks "Anulować?" again
```

---

### Step 1.3: Handle supplementary data after missing fields ✅ DONE (part of 1.1/1.2)

**What Claude Code builds:**
Already implemented in 1.1/1.2. When user types additional data while add_client flow is active, bot merges it, re-shows updated card.

**Reference:** `agent_system_prompt.md` → R2, R8

**Test 1 — fill some missing fields:**
```
(bot previously showed Nowak with missing: Adres, Metraż domu, Metraż dachu, Zużycie prądu)
YOU SEND:    "dom 160, dach 40 południe"

BOT SHOULD REPLY:
📋 Nowak, Piaseczno
Pompa ciepła | dom 160m², dach 40m² płd.
Tel. 601 234 567
❓ Brakuje: Adres, Zużycie prądu, [remaining user columns]
Zapisać czy jeszcze coś dopiszesz?
[Tak]

FAIL IF:
- Bot asks "Którego klienta masz na myśli?"
- Bot doesn't merge data — shows old version
- Missing fields list still includes Metraż domu and Metraż dachu
```

**Test 2 — "resztę nie wiem":**
```
YOU SEND:    "resztę nie wiem"

BOT SHOULD REPLY:    ✅ Zapisane.

FAIL IF:
- Bot asks about remaining missing fields
- Bot says "Proszę podać brakujące dane"
```

**Test 3 — fill ALL remaining fields:**
```
(bot showed missing: Zużycie prądu, Źródło pozyskania)
YOU SEND:    "4000 kWh, lead z Facebooka"

BOT SHOULD REPLY: updated card with NO ❓ Brakuje line, [Tak] button

FAIL IF:
- Bot still shows "Brakuje" line
- Bot doesn't parse "4000 kWh" as Zużycie prądu
```

---

### Step 1.4: Tone compliance — global check

**What Claude Code builds:**
System prompt / response formatting rules that prevent banned phrases and enforce brevity across ALL responses.

**Reference:** `agent_system_prompt.md` → Banned phrases, Banned behaviors, Response length limits

**Test 1 — no banned phrases:**
```
YOU SEND:    "Dodaj klienta Kowalski Warszawa PV 8kW"

FAIL IF bot response contains ANY of:
- "Oczywiście"
- "Z przyjemnością"
- "Świetnie"
- "Doskonały"
- "Czy mogę w czymś jeszcze pomóc"
- "Na podstawie Twojej wiadomości"
- "Przygotowałem dla Ciebie"
```

**Test 2 — no unprompted suggestions:**
```
(after successful save)
BOT SHOULD REPLY:    ✅ Zapisane.

FAIL IF bot adds:
- "Może chcesz dodać spotkanie?"
- "Chcesz jeszcze coś?"
- "Mogę też..."
- Any follow-up question not requested by user
```

**Test 3 — calm response to frustration:**
```
YOU SEND:    "nie działa to gówno"

BOT SHOULD REPLY:    "Co chcesz zrobić?" or "Co konkretnie nie działa?"

FAIL IF:
- Bot says "Przepraszam za utrudnienia"
- Bot says "Rozumiem Twoją frustrację"
- Response longer than 1 line
```

---

## PHASE 2: Google Sheets Integration

Goal: Bot reads from and writes to user's Google Sheets. All client operations become real.

**Prerequisite:** Phase 1 fully passing.

---

### Step 2.1: Write new client to Sheets on [Tak] ✅ DONE (merged into Phase 1)

**What Claude Code builds:**
Already implemented. [Tak] appends row to Sheets with parsed data. Status="Nowy lead", Data pierwszego kontaktu=today. Empty cells for missing fields.

**Reference:** `agent_system_prompt.md` → R1

**Test 1 — full write:**
```
YOU SEND:    "Nowak Leśna 5 Piaseczno pompa dom 120m2 tel 601234567"
BOT REPLIES: confirmation card
YOU TAP:     [Tak]
BOT REPLIES: ✅ Zapisane.

CHECK GOOGLE SHEETS:
- New row exists with: Nowak, Leśna 5, Piaseczno, Pompa ciepła, 120, 601234567
- Status = "Nowy lead"
- Data pierwszego kontaktu = today's date
- Missing fields = empty cells (not "brak" or "N/A")

FAIL IF:
- Row not in Sheets
- Status is empty or wrong
- Data pierwszego kontaktu is empty
```

**Test 2 — minimal data write:**
```
YOU SEND:    "Kowalski Warszawa 600123456"
BOT REPLIES: confirmation card with long missing fields list
YOU TAP:     [Tak]
BOT REPLIES: ✅ Zapisane.

CHECK GOOGLE SHEETS:
- Row exists with: Kowalski, Warszawa, 600123456
- All other fields = empty cells

FAIL IF:
- Bot didn't write to Sheets
- Bot filled in fields that user didn't provide
```

**Test 3 — cancelled write doesn't touch Sheets:**
```
YOU SEND:    "Testowy Testowo 111222333"
BOT REPLIES: confirmation card
YOU SEND:    "nie"
BOT REPLIES: Anulować? [Tak] [Nie]
YOU TAP:     [Tak]
BOT REPLIES: 🫡 Anulowane.

CHECK GOOGLE SHEETS:
- NO row with "Testowy" exists

FAIL IF:
- Row was written despite cancellation
```

---

### Step 2.2: Search client by name

**What Claude Code builds:**
When user asks about a client, search Sheets by name. Fuzzy match (case-insensitive, diacritics-tolerant, typo-tolerant). Return formatted client card, multiple match list, or link for 50+.

**Reference:** `agent_system_prompt.md` → Response patterns: Searching for a client

**Test 1 — single match:**
```
(Kowalski exists in Sheets)
YOU SEND:    "Co mam o Kowalskim?"

BOT SHOULD REPLY:
📋 Kowalski — Piłsudskiego 12, Warszawa
PV 8kW | Dom 160m², dach 40m² płd.
Tel. 600 123 456
Status: Nowy lead
Ostatni kontakt: [date]

FAIL IF:
- Bot says "Szukam..." and then nothing
- Data doesn't match what's in Sheets
- Response has banned phrases
```

**Test 2 — typo tolerance:**
```
YOU SEND:    "Kowalsky"

BOT SHOULD REPLY:
Nie mam "Kowalsky". Chodziło o Kowalskiego z Warszawy?
[Tak] [Nie]

FAIL IF:
- Bot says "Nie znaleziono klienta" without suggesting match
- Bot silently returns Kowalski without mentioning the typo
```

**Test 3 — multiple matches:**
```
(add 2 Nowaków to Sheets first — one in Warszawa, one in Piaseczno)
YOU SEND:    "Pokaż Nowaka"

BOT SHOULD REPLY:
Mam 2 Nowaków:
1. Nowak — Warszawa
2. Nowak — Piaseczno
Którego?

FAIL IF:
- Bot picks one without asking
- Bot shows full data for both (too long)
```

---

### Step 2.3: Edit client data

**What Claude Code builds:**
Parse edit requests. Find client. Show old vs new value. On confirmation, update cell in Sheets.

**Reference:** `agent_system_prompt.md` → R5, Response patterns

**Test 1 — change phone number:**
```
YOU SEND:    "Zmień telefon Kowalskiego na 601234567"

BOT SHOULD REPLY:
Kowalski — telefon:
Stary: 600 123 456
Nowy: 601 234 567
Zamienić czy dodać drugi?
[Zamień] [Dodaj drugi]

YOU TAP:     [Zamień]
BOT REPLIES: ✅ Zapisane.

CHECK SHEETS: phone updated to 601234567

FAIL IF:
- Bot overwrites without showing old vs new
- Bot doesn't offer "dodaj drugi" option
```

**Test 2 — update measurement:**
```
YOU SEND:    "Kowalski ma 45 metrów dachu, nie 40"

BOT SHOULD REPLY:
Kowalski — metraż dachu:
Było: 40m²
Będzie: 45m²
Zmienić?
[Tak] [Nie]

FAIL IF:
- Bot doesn't find the right field
- Bot changes without confirmation
```

**Test 3 — add note:**
```
YOU SEND:    "Dodaj notatkę do Kowalskiego: interesuje się też magazynem"

BOT SHOULD REPLY:
Kowalski — notatki:
Dodaję: "interesuje się też magazynem"
Zapisać?
[Tak] [Nie]

YOU TAP:     [Tak]
CHECK SHEETS: note appended (not replaced)

FAIL IF:
- Old notes overwritten
- Bot shows full old notes text (unnecessary)
```

---

### Step 2.4: Change client status

**What Claude Code builds:**
Detect status change intent from natural language. Map to correct lejek status. Show confirmation. Update Status column in Sheets.

**Reference:** `agent_system_prompt.md` → Response patterns: Status change

**Test 1 — direct:**
```
YOU SEND:    "Kowalski podpisał!"

BOT SHOULD REPLY:
🫡 Kowalski → Podpisane?
[Tak] [Nie]

YOU TAP:     [Tak]
CHECK SHEETS: Status = "Podpisane", Data ostatniego kontaktu = today

FAIL IF:
- Bot asks "Jaki status?" instead of deducing
- Status not updated in Sheets after confirm
```

**Test 2 — indirect:**
```
YOU SEND:    "Wysłałem ofertę Nowakowi"

BOT SHOULD REPLY:
Nowak → Oferta wysłana?
[Tak] [Nie]

FAIL IF:
- Bot doesn't map "wysłałem ofertę" → "Oferta wysłana"
```

**Test 3 — rejection:**
```
YOU SEND:    "Wiśniewski rezygnuje"

BOT SHOULD REPLY:
Wiśniewski → Odrzucone?
[Tak] [Nie]

FAIL IF:
- Bot asks "Dlaczego?" or comments on the rejection
```

---

### Step 2.5: Duplicate detection

**What Claude Code builds:**
Before appending new client, check if name + city already exists. If yes, warn and offer [Nowy] [Aktualizuj]. Never block.

**Reference:** `agent_system_prompt.md` → Duplicate client, R4

**Test 1 — duplicate found:**
```
(Kowalski, Warszawa already in Sheets)
YOU SEND:    "Kowalski Warszawa PV 10kW tel 609999999"

BOT SHOULD REPLY:
⚠️ Masz już Kowalskiego z Warszawy (Piłsudskiego 12, PV 8kW).
Dodać nowego czy zaktualizować?
[Nowy] [Aktualizuj]

FAIL IF:
- Bot adds without warning
- Bot blocks: "Nie można dodać, klient już istnieje"
```

**Test 2 — same name, different city (no duplicate):**
```
YOU SEND:    "Kowalski Piaseczno pompa tel 608888888"

BOT SHOULD REPLY:    Normal confirmation, NO duplicate warning

FAIL IF:
- Bot warns about Kowalski from Warszawa
```

**Test 3 — user chooses [Nowy]:**
```
YOU TAP:     [Nowy]
BOT REPLIES: ✅ Zapisane.
CHECK SHEETS: two Kowalski rows exist (Warszawa and new one)

FAIL IF:
- Bot questions the decision
- Only one row exists
```

---

## PHASE 3: Google Calendar Integration

Goal: Bot creates, reads, edits, deletes calendar events. Links to client data from Sheets.

**Prerequisite:** Phase 2 fully passing.

---

### Step 3.1: Add single meeting

**What Claude Code builds:**
Parse meeting request (date, time, client). If client in Sheets — pull address for event location. Create Google Calendar event. Show confirmation first.

**Reference:** `agent_system_prompt.md` → Calendar: adding meetings, Polish date/time

**Test 1 — known client:**
```
YOU SEND:    "Jutro o 10 jadę do Kowalskiego"

BOT SHOULD REPLY:
📅 Jutro [date], 10:00-11:00
Kowalski — Piłsudskiego 12, Warszawa
Dodać?
[Tak] [Nie]

YOU TAP:     [Tak]
CHECK GOOGLE CALENDAR: event exists, title "Spotkanie z Kowalski", location "Piłsudskiego 12, Warszawa"

FAIL IF:
- No address (should pull from Sheets)
- Duration wrong (should be user's default, e.g. 60 min)
- Event not in calendar after [Tak]
```

**Test 2 — Polish time format:**
```
YOU SEND:    "Wpół do ósmej jestem u Nowaka"

BOT SHOULD REPLY:
📅 [date], 7:30-8:30
Nowak — [address from Sheets]
Dodać?
[Tak] [Nie]

FAIL IF:
- Time is not 7:30
- Bot asks "O której dokładnie?"
```

**Test 3 — unknown client:**
```
YOU SEND:    "Jutro o 14 spotkanie z Mazurem"
(Mazur NOT in Sheets)

BOT SHOULD REPLY: calendar confirmation WITHOUT address
YOU TAP:     [Tak]
BOT SHOULD THEN REPLY:
🫵 Mazur nie jest w bazie. Dodać?
[Tak] [Nie]

FAIL IF:
- Bot refuses to create event without client in Sheets
- Bot doesn't ask about adding new client after event creation
```

---

### Step 3.2: Add multiple meetings from single message

**What Claude Code builds:**
Parse multiple meetings from one message. Create all as batch. After saving, ask about new clients.

**Reference:** `agent_system_prompt.md` → Calendar: adding meetings (batch)

**Test 1 — three meetings:**
```
YOU SEND:    "Jutro o 10 Kowalski, o 14 Nowak, o 17 Wiśniewski"

BOT SHOULD REPLY:
📅 Jutro [date]:
10:00 Kowalski — Piłsudskiego 12, Warszawa
14:00 Nowak — Leśna 5, Piaseczno
17:00 Wiśniewski — Kościuszki 8, Legionowo
Dodać?
[Tak] [Nie]

YOU TAP:     [Tak]
CHECK CALENDAR: 3 separate events with correct times and addresses

FAIL IF:
- Only 1 event created
- Addresses missing
```

**Test 2 — mix of known + unknown clients:**
```
YOU SEND:    "Jutro o 10 Kowalski, o 14 Mazur"
(Mazur not in Sheets)

YOU TAP:     [Tak]
BOT REPLIES: ✅ Dodane.
THEN: 🫵 Mazur nie jest w bazie. Dodać? [Tak] [Nie]

FAIL IF:
- Bot asks about Mazur BEFORE creating events
- Bot only creates 1 event
```

**Test 3 — cancel batch:**
```
YOU SEND:    "Jutro o 10 Kowalski, o 14 Nowak"
BOT SHOWS: confirmation
YOU TAP:     [Nie]
BOT: Anulować? [Tak] [Nie]
YOU TAP:     [Tak]
BOT: 🫡 Anulowane.

CHECK CALENDAR: NO new events

FAIL IF:
- Any events were created
```

---

### Step 3.3: Show day plan

**What Claude Code builds:**
Fetch events from Google Calendar for requested day. Enrich with client status from Sheets. Format as compact list.

**Reference:** `agent_system_prompt.md` → Calendar: day plan

**Test 1 — today with meetings:**
```
(create 2-3 meetings for today first)
YOU SEND:    "Co mam dziś?"

BOT SHOULD REPLY:
📅 Dziś [date]:
10:00 Kowalski — Piłsudskiego 12, Warszawa — oferta wysłana
14:00 Nowak — Leśna 5, Piaseczno — nowy lead

FAIL IF:
- Missing addresses
- Missing statuses (should pull from Sheets)
- Response longer than 15 lines
```

**Test 2 — empty day:**
```
YOU SEND:    "Co mam w niedzielę?"
(no events)

BOT SHOULD REPLY:    📅 Niedziela [date]: brak spotkań.

FAIL IF:
- More than 1 line
- Bot says "Nie masz żadnych spotkań zaplanowanych na niedzielę. Czy chcesz..."
```

**Test 3 — free slots:**
```
YOU SEND:    "Wolne okna jutro?"

BOT SHOULD REPLY:
📅 Jutro [date]:
Zajęte: 10:00-11:00, 14:00-15:00
Wolne: do 10:00, 11:00-14:00, po 15:00

FAIL IF:
- Bot lists each hour individually
- Response longer than 5 lines
```

---

### Step 3.4: Reschedule meeting

**What Claude Code builds:**
Parse reschedule request. Show old vs new datetime. Update Calendar event + Sheets "Data następnego kontaktu". Detect conflicts.

**Reference:** `agent_system_prompt.md` → Calendar: rescheduling, R5

**Test 1 — simple reschedule:**
```
YOU SEND:    "Przełóż Kowalskiego na piątek o 10"

BOT SHOULD REPLY:
📅 Kowalski:
Było: [current day+time]
Będzie: piątek [date] 10:00
Przenieść?
[Tak] [Nie]

YOU TAP:     [Tak]
CHECK CALENDAR: event moved
CHECK SHEETS: Data następnego kontaktu updated

FAIL IF:
- Old event still exists + new one created (should be moved, not duplicated)
- Sheets date not updated
```

**Test 2 — reschedule with conflict:**
```
(create event at Friday 10:00 for Nowak)
YOU SEND:    "Przełóż Kowalskiego na piątek o 10"

BOT SHOULD REPLY:
📅 Kowalski:
Było: [old time]
Będzie: piątek [date] 10:00
⚠️ Piątek o 10:00 masz już Nowaka. Przenieść mimo to?
[Tak] [Zmień godzinę]

FAIL IF:
- Bot silently moves without warning about conflict
- Bot blocks the move
```

**Test 3 — cancel reschedule:**
```
YOU SEND:    "Przełóż Kowalskiego na poniedziałek"
BOT SHOWS: confirmation
YOU TAP:     [Nie]

CHECK CALENDAR: event unchanged

FAIL IF:
- Event was moved despite [Nie]
```

---

### Step 3.5: Cancel meeting

**What Claude Code builds:**
Parse cancellation. Show event details. Delete on confirmation.

**Reference:** `agent_system_prompt.md` → Calendar: cancelling

**Test 1 — simple cancel:**
```
YOU SEND:    "Odwołaj Nowaka"

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

**Test 2 — ambiguous (multiple meetings):**
```
(two meetings with Kowalski)
YOU SEND:    "Odwołaj Kowalskiego"

BOT SHOULD REPLY:
Masz 2 spotkania z Kowalskim:
1. Środa 14:00
2. Piątek 10:00
Które odwołać?

FAIL IF:
- Bot deletes both without asking
- Bot picks one without asking
```

**Test 3 — cancel non-existent meeting:**
```
YOU SEND:    "Odwołaj Mazura"
(no meeting with Mazur)

BOT SHOULD REPLY:    Nie masz spotkania z Mazurem.

FAIL IF:
- Bot says "Przepraszam, nie znalazłem..."
- More than 1 line
```

---

## PHASE 4: Google Drive Integration

Goal: Bot stores photos and scans in client folders on Google Drive. Links folders in Sheets.

**Prerequisite:** Phase 2 fully passing.

---

### Step 4.1: Receive photos and assign to client

**What Claude Code builds:**
When user sends photo(s), ask which client. Upload to Drive folder "OZE Klienci - [user]/[Klient] - [Miasto]/". Update "Zdjęcia" column in Sheets with folder link.

**Reference:** `agent_system_prompt.md` → Response patterns: Photos

**Test 1 — single photo:**
```
YOU SEND:    1 photo
BOT REPLIES: 📸 1 zdjęcie. Do którego klienta?
YOU SEND:    "Kowalski Warszawa"
BOT REPLIES: 📸 1 zdjęcie → Kowalski, Warszawa. Zapisać? [Tak] [Nie]
YOU TAP:     [Tak]
BOT REPLIES: ✅ Zapisane.

CHECK DRIVE: folder "Kowalski - Warszawa" exists with photo inside
CHECK SHEETS: "Zdjęcia" column has link to folder

FAIL IF:
- Photo not on Drive
- Sheets not updated with link
- Bot asks more than necessary
```

**Test 2 — multiple photos in sequence:**
```
YOU SEND:    5 photos (one after another)
BOT REPLIES: 📸 5 zdjęć. Do którego klienta?
YOU SEND:    "Nowak"
BOT REPLIES: 📸 5 zdjęć → Nowak, Piaseczno. Zapisać? [Tak] [Nie]
YOU TAP:     [Tak]
BOT REPLIES: ✅ Zapisane.

CHECK DRIVE: all 5 photos in Nowak's folder

FAIL IF:
- Bot asks after each photo separately
- Only some photos uploaded
```

**Test 3 — client not found:**
```
YOU SEND:    1 photo
BOT REPLIES: 📸 1 zdjęcie. Do którego klienta?
YOU SEND:    "Mazur Radom"
(Mazur from Radom not in Sheets)

BOT SHOULD REPLY:    Nie mam Mazura z Radomia w bazie.

FAIL IF:
- Bot creates folder for non-existent client
- Bot uploads photo anyway
```

---

## PHASE 5: Voice Input

Goal: Bot processes voice messages — transcription + parsing + all Phase 2-4 operations.

**Prerequisite:** Phase 2 fully passing. Phase 3-4 recommended.

---

### Step 5.1: Voice → transcription → client data

**What Claude Code builds:**
Whisper integration. Processing indicators. Confidence-based flow (show transcription only if low quality). Then same parsing as Phase 1.

**Reference:** `agent_system_prompt.md` → Voice processing flow

**Test 1 — clear voice, new client:**
```
YOU RECORD:  "Byłem u Kowalskiego na Piłsudskiego dwanaście w Warszawie, dom sto sześćdziesiąt metrów, dach czterdzieści na południe, interesuje go PV-ka ósemka, telefon sześćset sto dwadzieścia trzy czterysta pięćdziesiąt sześć"

BOT SHOWS:   🎙️ Transkrybuję... → 🔍 Analizuję...
BOT REPLIES: standard confirmation (same format as Step 1.1)

FAIL IF:
- Bot shows transcription when quality is good
- Bot doesn't parse any field correctly
- Bot asks "Co to jest PV-ka?"
```

**Test 2 — emotional voice:**
```
YOU RECORD:  "Kurde, prawie miałem gościa, Wiśniewski z Legionowa, Kościuszki osiem, dom jakieś sto czterdzieści, dach trzydzieści pięć wschód, PV-ka szóstka, żona go przekręciła, follow-up za tydzień, numer sześćset dwa trzysta czterdzieści pięć sześćset siedemdziesiąt osiem"

BOT REPLIES:
📋 Wiśniewski, Kościuszki 8, Legionowo
PV 6kW, dom 140m², dach 35m² wsch.
Tel. 602 345 678
📅 Follow-up: [date +7 days]
❓ Brakuje: zużycie prądu, źródło leada
Zapisać?

FAIL IF:
- Emotional words break the parser
- Follow-up not detected
- "szóstka" not mapped to 6kW
```

**Test 3 — noisy audio / timeout:**
```
YOU RECORD:  very short or very noisy voice message

EXPECTED:
If Whisper returns low confidence → bot shows transcription + "Dobrze usłyszałem? [Tak] [Nagraj ponownie]"
If Whisper times out (60s) → "Wystąpił problem, spróbuj ponownie."

FAIL IF:
- Bot crashes on bad audio
- Bot says "Przepraszam, nie udało się..."
- Bot gives technical error details
```

---

### Step 5.2: Voice → multiple client updates (evening follow-up response)

**What Claude Code builds:**
Parse voice message that describes multiple client meetings at once. Extract per-client updates. Show grouped confirmation.

**Reference:** `agent_system_prompt.md` → Evening follow-up response

**Test 1 — three clients in one voice:**
```
YOU RECORD:  "Z Kowalskim super, chce wycenę na ósemkę, wyślę jutro. Nowak nie był w domu, trzeba przełożyć na przyszły tydzień. U Wiśniewskiego złożyłem ofertę, czekam na odpowiedź."

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
- Bot handles only first client
- Bot asks about each client separately
- Bot misses status change implications
```

**Test 2 — mixed slang and info:**
```
YOU RECORD:  "Mazur bierze pompeczkę i magazyn, wyślę umowę pojutrze. Zieliński spał, nie otworzył drzwi."

BOT SHOULD REPLY:
📋 Zrozumiałem:
1. Mazur → pompa ciepła + magazyn energii, wysłać umowę [date]
2. Zieliński — nie był w domu

Statusy:
Mazur: Podpisane

Zapisać?
[Tak] [Nie]

FAIL IF:
- "pompeczkę" not parsed as Pompa ciepła
- "magazyn" not parsed as Magazyn energii
- "spał" not understood as client no-show
```

**Test 3 — voice with calendar intent:**
```
YOU RECORD:  "Do Kowalskiego jadę w piątek o dziesiątej, a Nowaka trzeba przełożyć na przyszły wtorek o czternastej"

BOT SHOULD REPLY: calendar confirmations for both operations

FAIL IF:
- Bot only handles one operation
- Dates incorrectly parsed
```

---

## PHASE 6: Proactive Messages

Goal: Bot sends morning brief and evening follow-up automatically.

**Prerequisite:** Phase 2 + 3 fully passing.

---

### Step 6.1: Morning brief

**What Claude Code builds:**
Scheduled job at user's configured hour on working days. Fetches calendar events + enriches with Sheets data + adds follow-ups + lejek summary.

**Reference:** `agent_system_prompt.md` → Proactive messages: Morning brief

**Test 1 — full day (set brief hour to now, wait for delivery):**
```
BOT SENDS (automatically):
🫡 Plan na [date]:

10:00 Kowalski — Piłsudskiego 12, Warszawa — oferta wysłana
14:00 Nowak — Leśna 5, Piaseczno — nowy lead

📋 Follow-upy:
• Mazur — wysłać ofertę

Lejek: X nowych, Y umówionych, Z ofert, W negocjacje

FAIL IF:
- Missing addresses
- Missing statuses
- Contains "Udanego dnia!" or any greeting/motivation
- Sent on non-working day
```

**Test 2 — no meetings:**
```
(clear calendar for tomorrow, set brief for tomorrow)

BOT SENDS:
🫡 Plan na [date]:

📋 Follow-upy:
• Mazur — wysłać ofertę

Lejek: X nowych, Y umówionych...

FAIL IF:
- Bot says "Brak spotkań na dziś" as a separate section
- Bot skips the message entirely (should still send follow-ups + lejek)
```

**Test 3 — no meetings, no follow-ups:**
```
(clear everything)

BOT SENDS:
🫡 Plan na [date]:
Brak spotkań. Brak follow-upów.

Lejek: X nowych, Y umówionych...

FAIL IF:
- Bot doesn't send anything
- Bot sends motivational filler
```

---

### Step 6.2: Evening follow-up

**What Claude Code builds:**
After last meeting of the day (configurable delay), check for unreported meetings. Send prompt if any exist. Do NOT send if all reported.

**Reference:** `agent_system_prompt.md` → Proactive messages: Evening follow-up

**Test 1 — unreported meetings:**
```
(have 3 meetings today, report on 0)

BOT SENDS (after last meeting + delay):
🫵 Nieraportowane spotkania:
• Kowalski (10:00)
• Nowak (14:00)
• Wiśniewski (17:00)

Uzupełnisz? Jutro nie będziesz tak dobrze pamiętał.

FAIL IF:
- Missing any unreported meeting
- Sent before last meeting ends
- Contains motivational filler beyond the "jutro nie będziesz..." line
```

**Test 2 — all meetings reported:**
```
(have 2 meetings today, report on both during the day)

BOT SENDS:    NOTHING

FAIL IF:
- Bot sends "Wszystko uzupełnione!" or any message
```

**Test 3 — partial reporting:**
```
(3 meetings, reported on 1 during the day)

BOT SENDS:
🫵 Nieraportowane spotkania:
• Nowak (14:00)
• Wiśniewski (17:00)

Uzupełnisz? Jutro nie będziesz tak dobrze pamiętał.

FAIL IF:
- Bot includes already-reported Kowalski
```

---

## PHASE 7: Lejek, Follow-ups, Error Handling

Goal: Sales funnel view, reminder system, graceful error handling.

**Prerequisite:** Phase 2 fully passing.

---

### Step 7.1: Lejek sprzedażowy summary

**What Claude Code builds:**
Count clients per status from Sheets. Show numbers + dashboard link.

**Reference:** `agent_system_prompt.md` → Lejek sprzedażowy

**Test 1 — normal lejek:**
```
YOU SEND:    "Ilu mam klientów?"

BOT SHOULD REPLY:
📋 Lejek:
Nowy lead: X
Spotkanie umówione: Y
...
Szczegóły → [link]

FAIL IF:
- Bot lists individual client names
- Response longer than 10 lines
```

**Test 2 — alternative phrasing:**
```
YOU SEND:    "Pokaż lejek"
BOT SHOULD REPLY:    Same format as Test 1

FAIL IF:
- Bot doesn't understand "lejek"
```

**Test 3 — empty:**
```
(new user, 0 clients)
YOU SEND:    "Ilu mam klientów?"
BOT SHOULD REPLY:    📋 Lejek: 0 klientów.

FAIL IF:
- More than 1 line
```

---

### Step 7.2: Follow-up reminders

**What Claude Code builds:**
Parse follow-up requests. Store in pending_followups. Deliver at scheduled time.

**Reference:** `agent_system_prompt.md` → Follow-up / reminder

**Test 1 — set reminder:**
```
YOU SEND:    "Przypomnij zadzwonić do Nowaka w piątek"

BOT SHOULD REPLY:
⏰ Piątek [date] — zadzwonić do Nowaka. Ustawić?
[Tak] [Nie]

FAIL IF:
- Bot sets without confirmation
- Date wrong
```

**Test 2 — relative date:**
```
YOU SEND:    "Follow-up Kowalski za 3 dni"

BOT SHOULD REPLY:
⏰ [date +3] — follow-up Kowalski. Ustawić?
[Tak] [Nie]

FAIL IF:
- Date calculation wrong
```

**Test 3 — reminder delivery:**
```
(set reminder for "now + 1 minute" for testing)

BOT SENDS (at scheduled time):
⏰ Przypomnienie: zadzwonić do Nowaka

FAIL IF:
- Reminder not delivered
- Delivered at wrong time
- Contains extra filler text
```

---

### Step 7.3: Error handling

**What Claude Code builds:**
Graceful handling of: Google API failures, subscription expiry, interaction limits, unintelligible messages.

**Reference:** `agent_system_prompt.md` → Error handling

**Test 1 — Google API failure (simulate by revoking token temporarily):**
```
YOU SEND:    "Dodaj klienta Testowy Testowo 111222333"

BOT SHOULD REPLY:    Google Sheets chwilowo niedostępne. Dane NIE zapisane. Spróbuj za kilka minut.

FAIL IF:
- Bot says "Przepraszam za utrudnienia"
- Bot gives technical error (stack trace, status code)
- Bot writes to Supabase as fallback
- More than 2 lines
```

**Test 2 — interaction limit (set limit to 3 for testing):**
```
(send 3 messages to hit limit)
YOU SEND:    4th message

BOT SHOULD REPLY:    Limit na dziś wyczerpany. Jutro masz [X] interakcji.

FAIL IF:
- Bot processes the message anyway
- Bot apologizes
```

**Test 3 — unintelligible message:**
```
YOU SEND:    "asdkjfhaskdjfh"

BOT SHOULD REPLY:    Co chcesz zrobić?

FAIL IF:
- Bot tries to parse gibberish into client data
- Bot says "Nie rozumiem Twojej wiadomości. Proszę spróbować ponownie."
- More than 1 line
```
