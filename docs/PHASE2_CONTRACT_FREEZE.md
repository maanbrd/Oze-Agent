# OZE-Agent — Phase 2 Behavior Contract Freeze

_Last updated: 14.04.2026_

## Context

Derived from `docs/PHASE1_AUDIT.md`. Nine behavior-contract decisions to freeze before Phase 3 (Intent Router), Phase 4 (Pending + Cards), Phase 5 (Mutation Pipeline), and Phase 6 (Proactive) implementation starts. Each decision is short, explicit, and the frozen value is the contract that Python code must honor.

One file, not sections in main specs — keeps runtime contracts (`INTENCJE_MVP.md`, `agent_system_prompt.md`, `agent_behavior_spec_v5.md`) clean.

## Status

| # | Decision | Status | Frozen value |
|---|---|---|---|
| D1 | Sheets date format | ✅ frozen 14.04 | ISO storage (`YYYY-MM-DD` / `YYYY-MM-DDTHH:MM:SS+HH:MM`); PL display (`DD.MM.YYYY (Dzień)`) |
| D2 | Calendar timezone contract | ✅ frozen 14.04 | Domain layer always produces tz-aware `Europe/Warsaw`; wrapper validates (no silent UTC), rejects naive with log+None |
| D3 | Calendar reminders policy | ✅ frozen 14.04 | `create_event` / `update_event` always set `reminders: {useDefault: True}`; no `overrides`; no scheduler-side pre-meeting reminders |
| D4 | `Następny krok` (column K) enum values | ✅ frozen 14.04 | Two enums with explicit mapping: runtime `event_type` (English codes) ↔ Sheets K dropdown (Polish labels); K = label (never date), L = ISO date per D1 |
| D5 | Voice / photo handler registration scope | ⏳ pending | — |
| D6 | `get_conversation_history` 30-minute window | ⏳ pending | — |
| D7 | Auth: Calendar scope narrowing | ⏳ pending | — |
| D8 | ExtendedProperties in Calendar events | ⏳ pending | — |
| D9 | User timezone in `users` schema | ⏳ pending | — |

## Decisions

### D1. Sheets date format [✅ frozen 14.04.2026]

**Decyzja:** Sheets przechowuje daty w formacie ISO. User-facing output zawsze renderuje PL.

**Storage format (Sheets):**
- Kolumny I (`Data pierwszego kontaktu`), J (`Data ostatniego kontaktu`), L (`Data następnego kroku`).
- ISO date `YYYY-MM-DD` dla pól bez godziny.
- ISO datetime z offsetem (`YYYY-MM-DDTHH:MM:SS+02:00`) jeśli potrzebny czas — głównie `Data następnego kroku` gdy R7 flow dokłada follow-up z konkretną godziną.

**Display format (Telegram / UI):**
- `DD.MM.YYYY (Dzień tygodnia)` — np. `14.04.2026 (Wtorek)`.
- **Telegram/UI nigdy nie pokazuje raw ISO.**
- Formatter obowiązkowy dla wszystkich read / display flows: mutation cards, `show_client`, `show_day_plan` (który czyta głównie Calendar), morning brief, evening follow-up.
- Formatter akceptuje oba typy wejścia: ISO date (`YYYY-MM-DD`) i ISO datetime with offset (`YYYY-MM-DDTHH:MM:SS+02:00`).

**Enhancement (non-blocking):** Przy `create_spreadsheet` ustawić Polish locale + `timeZone = "Europe/Warsaw"` (dokładna wartość `locale` do sprawdzenia w Google Sheets API — `pl_PL`, `pl-PL` albo `pl` zależnie od pola). Wtedy user edytujący Sheet ręcznie widzi ISO date renderowane natywnie jako PL. To enhancement, nie warunek decyzji.

**Affected:**
- `shared/google_sheets.py` — obecne writes już są ISO (no code change).
- Phase 5 formatter layer (`shared/formatting/dates.py` albo analogiczny) — obowiązkowo `ISO → DD.MM.YYYY (Dzień)`.
- Phase 5 read handlers (`show_client`, `show_day_plan`) — muszą używać formattera, nigdy raw ISO.
- Phase 6 proactive (morning brief, evening follow-up) — tak samo.
- Tests: `test_google_sheets.py` — dodać date write behavior (ISO format); istniejący `test_formatting.py` rozszerzyć o ISO → PL conversion (oba typy wejścia: date i datetime z offsetem).

---

### D2. Calendar timezone contract [✅ frozen 14.04.2026]

**Decyzja:** Domain / extraction / mutation layer zawsze produkuje tz-aware `Europe/Warsaw` datetimes. Wrapper waliduje i nie zgaduje — naive datetime nigdy nie jest traktowany jako UTC ani jako Warsaw "po cichu".

**Domain contract:**
- Intent parser, `extract_meeting_data`, `shared/mutations/add_meeting/` — muszą przekazywać do `shared/google_calendar.py` wyłącznie tz-aware datetimes.
- Dla MVP timezone = `Europe/Warsaw` (stała, hardcoded). Multi-timezone per-user jest POST-MVP — patrz D9.
- "Jutro o 10" zawsze oznacza `10:00 Europe/Warsaw`.

**Wrapper behavior:**
- `_to_rfc3339` nie przypisuje już naive datetime do UTC. Jeśli `dt.tzinfo is None` → `logger.error` + caller path returns `None` (consistent z "wrapper nie rzuca").
- `get_events_for_date(day: date)` liczy zakres dnia jako lokalny dzień Europe/Warsaw: **od 00:00 Europe/Warsaw do 00:00 Europe/Warsaw następnego dnia**. Konwersja do UTC tylko na potrzeby Google Calendar API call (`timeMin` / `timeMax`).

**Wire format (Calendar API):**
- ISO-8601 z offsetem: `YYYY-MM-DDTHH:MM:SS+02:00` (CEST, lato) albo `+01:00` (CET, zima).
- `zoneinfo.ZoneInfo("Europe/Warsaw")` obsługuje DST automatycznie.

**Display format (Telegram / UI):** nadal polski format per D1 — `DD.MM.YYYY (Dzień)` + `HH:MM`. Nigdy raw ISO.

**Fail mode:** naive datetime trafi do wrappera → `logger.error("... naive datetime not accepted ...")` + return None / False. Caller widzi None = failed operation.

**Tests coverage:**
- Typowy dzień zimowy `+01:00` (np. 15.01.2026).
- Typowy dzień letni `+02:00` (np. 15.07.2026).
- Dzień zmiany czasu (np. 28.03.2026 forward i 25.10.2026 back) — poprawne Warsaw-local boundaries.
- Event późnym wieczorem Warsaw (np. `23:30 Europe/Warsaw`) — `get_events_for_date(...)` musi go znaleźć w tym samym dniu Warsaw, nie przesunąć do następnego przez UTC boundary.
- Naive datetime input → log error + None.

**Nie wymagamy w testach:** edge case nieistniejącej godziny 02:30 w dniu przestawienia DST (zoneinfo to obsługuje, ale nie jest to MVP blocker).

**Affected:**
- `shared/google_calendar.py` — fix `_to_rfc3339` (no silent UTC fallback), fix `get_events_for_date` (Warsaw-local midnight boundary).
- Phase 5 `shared/extraction/extract_meeting_data.py` — zawsze outputs tz-aware Warsaw datetime.
- Phase 5 `shared/mutations/add_meeting/` — assert tz-aware przed call do wrappera.
- Tests: `test_google_calendar.py` — rozszerzyć o DST typowe dni + boundary + naive rejection.

### D3. Calendar reminders policy [✅ frozen 14.04.2026]

**Decyzja:** Wrapper explicit ustawia `reminders: {"useDefault": True}` w każdym evencie. Agent nigdy nie dopisuje `overrides` ani nie planuje własnych pre-meeting reminders po stronie bota/schedulera.

**Rozdziela dwie rzeczy:**
- **Agent nie tworzy własnych przypomnień** — per SSOT §4 NIEPLANOWANE.
- **Google Calendar może używać natywnych ustawień user'a/kalendarza** — user w Google Calendar UI decyduje czy chce reminder X min przed, push notification, email. Agent tego nie blokuje.

**Wrapper behavior:**
- `create_event` **zawsze** ustawia `body["reminders"] = {"useDefault": True}`.
- `update_event` (jeśli zostaje jako low-level primitive per D5 voice/photo decision) zachowuje `useDefault: True` — nie usuwa ani nie dopisuje `overrides`.
- Agent **nigdy** nie ustawia `reminders.overrides` (żadnych `[{"method": "popup", "minutes": 10}]` itp.).
- Agent **nigdy** nie planuje własnych Telegram-side / scheduler-side pre-meeting reminders (żadnego `shared/scheduler/` flow typu "30 min before meeting → send Telegram push").

**Native Calendar reminders** są dozwolone — jeśli wynikają z user's settings na poziomie OZE calendar w Google Calendar UI, Google je wyśle (push / email / notification). To nie jest "agent-side" reminder.

**Affected:**
- `shared/google_calendar.py` `create_event` (linie 148-185) — dodać `"reminders": {"useDefault": True}` do `body`.
- `shared/google_calendar.py` `update_event` (linie 188-231) — zachować `useDefault: True`, nigdy nie dopisywać `overrides`.
- Phase 6 scheduler (`bot/scheduler/`) — **żadnych pre-meeting reminder jobs**. Tylko morning brief + evening follow-up (matches ARCHITECTURE Proactive scheduler row).
- Tests:
  - `test_create_event_sets_reminders_use_default` — assertion że body zawiera `reminders: {useDefault: True}`.
  - `test_create_event_no_overrides` — assertion że `body["reminders"].get("overrides")` jest None / pusty.
  - Phase 6: test że scheduler nie ma pre-meeting reminder job.
- Reviewer antipattern list (`AGENT_WORKFLOW.md` — już zawiera "agent-side pre-meeting reminders" na liście). Dodać explicit: `reminders.overrides` w body eventu jako red flag.

**Rationale:** jawny kontrakt w kodzie (`useDefault: True` widoczny w PR) vs implicit reliance na Google default. User-friendly — nie interferuje z user's Calendar settings. NIEPLANOWANE per SSOT zachowane. Odporne na hipotetyczną zmianę Google API default.

### D4. `Następny krok` (column K) enum values [✅ frozen 14.04.2026]

**Decyzja:** Dwa enumy z explicit mappingiem. Python używa stabilnych angielskich kodów dla runtime logic. Sheets pokazuje handlowcowi polskie labele w dropdown.

**Runtime `event_type`** (internal, English — Calendar `extendedProperties`, routing, emoji/duration logic):

```python
Literal["in_person", "phone_call", "offer_email", "doc_followup"]
```

**Sheets column K dropdown** (user-facing, Polish — 7 opcji):

- `Spotkanie`
- `Telefon`
- `Wysłać ofertę`
- `Follow-up dokumentowy`
- `Czekać na decyzję klienta`
- `Nic — zamknięte`
- `Inne`

**Mapping runtime ↔ Sheets (4 event-bearing values):**

| Runtime `event_type` | Sheets K label | Emoji | Duration | Calendar event? |
|---|---|---|---|---|
| `in_person` | `Spotkanie` | 🤝 | 60 min | ✓ |
| `phone_call` | `Telefon` | 📞 | 15 min | ✓ |
| `offer_email` | `Wysłać ofertę` | 📨 | 0 min (timestamp only) | ✓ |
| `doc_followup` | `Follow-up dokumentowy` | 📄 | 0 min | ✓ |

**No-event K values (3):** `Czekać na decyzję klienta`, `Nic — zamknięte`, `Inne`. Zapisywane tylko w Sheets, bez Calendar eventu.

**K / L contract:**

- **K (`Następny krok`)** = zawsze label z dropdown albo puste. **K nigdy nie przechowuje daty.**
- **L (`Data następnego kroku`)** = ISO date / ISO datetime per D1 albo puste.

**Runtime examples:**

| User says | K | L | Calendar? |
|---|---|---|---|
| "spotkanie jutro o 10 z Kowalskim" | `Spotkanie` | `2026-04-15T10:00:00+02:00` | ✓ `in_person` 60 min |
| "zadzwonić do Nowaka w piątek" | `Telefon` | `2026-04-18T10:00:00+02:00` (domyślna) | ✓ `phone_call` 15 min |
| "wysłać ofertę do środy" | `Wysłać ofertę` | `2026-04-16` | ✓ `offer_email` 0 min |
| "follow-up za tydzień" | `Follow-up dokumentowy` | `2026-04-22` | ✓ `doc_followup` 0 min |
| "czekam na decyzję do piątku" | `Czekać na decyzję klienta` | `2026-04-18` | ✗ bez eventu |
| "niestandardowy krok" (szczegóły w Notatki) | `Inne` | opcjonalnie | ✗ bez eventu |
| "zamknięte" | `Nic — zamknięte` | puste | ✗ bez eventu |
| R7 "nie wiem jeszcze" | puste | puste | ✗ flow kończy się |

**Calendar event creation:** tylko dla 4 `event_type` values (`in_person`, `phone_call`, `offer_email`, `doc_followup`). Dla 3 "no-event" K values agent NIE tworzy Calendar eventu — zapisuje tylko Sheets.

**Affected:**

- `shared/google_sheets.py` linia 33 — aktualizacja comment na pełną listę 7 enum labels.
- `INTENCJE_MVP.md` fix: wszystkie miejsca mówiące "K zaktualizowana do daty" → "K = label, L = data" (szczególnie §4.5). **Spec bug do naprawy.**
- Phase 3 `shared/intent/` — classifier rozpoznaje typ następnego kroku i emituje `event_type` English code.
- Phase 5 `shared/mutations/` — implement mapping `event_type → Sheets K label` przy commit. Dla no-event K — bez Calendar API call.
- Phase 5 `shared/extraction/extract_meeting_data.py` — słowa kluczowe → `event_type`. Domyślne trwania / emoji per mapping.
- `create_spreadsheet` enhancement (non-blocking): dodać Google Sheets data validation na kolumnę K z 7-elementową listą dropdown.
- Phase 5 `shared/read/show_client` — renderuje K jako polski label bez zmiany, L przez date formatter per D1.
- Tests: `test_meeting_flow.py` — assertion że Sheets K ma Polish label, Calendar event extendedProperties ma English `event_type`. Coverage dla 7 enum values + puste. Coverage dla "no-event" K → no Calendar API call.

**Rationale:** separacja warstw (user-facing Polish, code-facing English). Stabilne typy w Pythonie (`Literal[...]`). Spójność z obecnym `extendedProperties` tagging per INTENCJE_MVP §4.5. Customizacja labels bez łamania kodu. User-friendly Sheets z polskimi dropdown values.

### D5. Voice / photo handler registration scope [⏳ pending]

— pending.

### D6. `get_conversation_history` 30-minute window [⏳ pending]

— pending.

### D7. Auth: Calendar scope narrowing [⏳ pending]

— pending.

### D8. ExtendedProperties in Calendar events [⏳ pending]

— pending.

### D9. User timezone in `users` schema [⏳ pending]

— pending.

---

## Commit strategy

- **Draft start:** D1 frozen, no commit yet.
- **Commit package 1:** D1-D4 (Sheets date format + Calendar-related: timezone, reminders, `Następny krok` enum).
- **Commit package 2:** D5-D9 (voice/photo handler, history window, auth scope, extendedProperties, user timezone).
- Alternative: single commit at the end of Phase 2. Decision at package 1.
