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
| D5 | Voice / photo / multi-meeting handler scope | ✅ frozen 14.04 | Voice / photo / image-document handlers registered but route to POST-MVP stub (no Whisper / Drive / legacy flow); multi-meeting rejected at intent parser with "one meeting at a time" response; feature flag optional, not MVP requirement; raw media never stored in `history` |
| D6 | `get_conversation_history` 30-minute window | ✅ frozen 14.04 | Hybrid: wrapper accepts optional `since: timedelta \| None = None` (default raw); intent router + prompt builder **must** call with `since=timedelta(minutes=30)`; UTC-aware filter; pending lifecycle separate |
| D7 | Auth: Calendar scope narrowing | ✅ frozen 14.04 | MVP keeps full `calendar` scope (required by onboarding `calendars.insert`); narrowing to `calendar.events` is POST-MVP security hardening, not MVP blocker |
| D8 | ExtendedProperties in Calendar events | ✅ frozen 14.04 | Minimal `extendedProperties.private.event_type` only (per D4 enum); Sheets column P (`ID wydarzenia Kalendarz`) is primary Sheets → Calendar link; no `oze_agent` / `client_row` / `client_name` |
| D9 | User timezone in `users` schema | ✅ frozen 14.04 | MVP hardcodes `Europe/Warsaw` via single `DEFAULT_TIMEZONE` constant; `users` schema **nie zawiera** `timezone` kolumny w MVP; multi-timezone = POST-MVP roadmap; legacy kolumna (jeśli istnieje) → unused / legacy, housekeeping migration po audycie środowisk (nie ad hoc w Phase 2) |

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
| `offer_email` | `Wysłać ofertę` | 📨 | 15 min | ✓ |
| `doc_followup` | `Follow-up dokumentowy` | 📄 | 15 min | ✓ |

Amendment 16.04.2026: offer_email / doc_followup duration zmienione z 0 min na 15 min — wszystkie 4 event_types mają teraz domyślny blok Calendar.

**No-event K values (3):** `Czekać na decyzję klienta`, `Nic — zamknięte`, `Inne`. Zapisywane tylko w Sheets, bez Calendar eventu.

**K / L contract:**

- **K (`Następny krok`)** = zawsze label z dropdown albo puste. **K nigdy nie przechowuje daty.**
- **L (`Data następnego kroku`)** = ISO date / ISO datetime per D1 albo puste.

**Runtime examples:**

| User says | K | L | Calendar? |
|---|---|---|---|
| "spotkanie jutro o 10 z Kowalskim" | `Spotkanie` | `2026-04-15T10:00:00+02:00` | ✓ `in_person` 60 min |
| "zadzwonić do Nowaka w piątek" | `Telefon` | `2026-04-18T10:00:00+02:00` (domyślna) | ✓ `phone_call` 15 min |
| "wysłać ofertę do środy" | `Wysłać ofertę` | `2026-04-16` | ✓ `offer_email` 15 min |
| "follow-up za tydzień" | `Follow-up dokumentowy` | `2026-04-22` | ✓ `doc_followup` 15 min |
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

### D5. Voice / photo / multi-meeting handler registration scope [✅ frozen 14.04.2026]

**Decyzja:** Handlery voice / photo / image-document pozostają zarejestrowane w Telegram (`bot/main.py`) i **routują do explicit POST-MVP stub**. Multi-meeting pozostaje rozpoznawane na poziomie **intent parsera**, ale w MVP routuje do rejection / stub response. Legacy voice/photo behavior (Whisper, Drive upload, batch parser) **nie jest używany w MVP**. Feature flag opcjonalny — nie jest warunkiem MVP.

**Voice / photo handlers:**

- Handler zarejestrowany na Telegram message type: **voice, audio, photo, oraz image-as-document** (jeśli user wyśle zdjęcie jako plik / `document` z MIME type `image/*`). Wszystkie te ścieżki routują do tego samego POST-MVP stuba — zdjęcie wysłane "jako plik" nie może uciec bokiem do legacy flow.
- Handler ma **jedną odpowiedź** — stub reply w PL (patrz niżej). **Żadnych** wywołań Whisper, Drive, intent routera, pending flow, mutation pipeline.
- Stub message:

  > Głosówki i zdjęcia będą obsługiwane w kolejnej wersji. Na teraz napisz proszę tę informację tekstem.

- Handler **nie tworzy pending state**, **nie zapisuje** do Sheets/Calendar/Drive.
- **Conversation history contract:** stub reply może być zalogowany jako zwykła odpowiedź bota (standard conversation turn). **Raw voice/photo payloads, transkrypcje, Drive links, file_id, ani żadne media-specific artefakty nigdy nie są zapisywane w `history`** — bo w MVP ich nie generujemy.

**Multi-meeting:**

- Intent parser **nie próbuje batch flow**. Jeśli user w jednej wiadomości wysyła kilka spotkań (np. "spotkanie z Kowalskim jutro 10 i Nowakiem pojutrze 14"):
  - **Domyślne MVP:** agent odpowiada PL komunikatem, że obsługuje jedno spotkanie naraz, i prosi o powtórzenie pierwszego osobno. Bez partial processing.
  - **Alternatywa** (do decyzji w Phase 3/5): agent bierze tylko pierwsze spotkanie, pokazuje mutation card, i informuje że resztę trzeba wysłać osobno. Implementacja tej alternatywy wymaga jawnego potwierdzenia w intent router contract — nie jest to domyślne MVP zachowanie.
- Żaden batch parser, żadne multi-event Calendar creation.

**Feature flag:**

- **Opcjonalny.** MVP nie wymaga `ENABLE_VOICE` / `ENABLE_PHOTO` env var.
- Jeśli wprowadzony później (POST-MVP), flag = False → stub reply; flag = True → real flow. To nie jest MVP decision.

**Rozróżnienie warstwowe (per SSOT §4):**

- Voice / photo / multi-meeting są **POST-MVP roadmap**, nie NIEPLANOWANE. Więc reply ma ton "będzie później", nie "nie planujemy".
- Nie mylić z NIEPLANOWANE (agent-side pre-meeting reminders per D3), gdzie reply kieruje do native alternative.

**Affected:**

- `bot/main.py` — handlery voice / audio / photo / image-as-document pozostają zarejestrowane, ale ich callback `= stub_response`. **Usunąć** binding do legacy Whisper / Drive / intent code z tych handlerów. Sprawdzić czy Telegram dispatcher rozpoznaje image document (`document` z MIME `image/*`) — jeśli domyślnie trafia do `document_handler`, dodać filter / route do stuba.
- `bot/handlers/` (jeśli istnieje separate module dla voice/photo) — zastąpić implementacją stubem. Legacy code pozostaje w repo jako reference, ale **nie jest wołany z rejestracji handlerów**.
- Phase 3 `shared/intent/` — multi-meeting detection: jeśli parser wykryje >1 spotkanie w jednym message → `intent = general_question` (albo dedykowany `multi_meeting_rejection`) z responsem "jedno spotkanie naraz".
- Phase 7 tests:
  - `test_voice_message_returns_stub` — voice upload → stub response, no Sheets/Calendar/Drive write, no raw payload in history.
  - `test_photo_message_returns_stub` — photo message → stub response.
  - `test_image_document_returns_stub` — image sent as `document` (MIME `image/*`) → stub response (nie uciekł do document_handler / legacy Drive flow).
  - `test_multi_meeting_rejection` — message with 2+ meetings → agent asks for one at a time.
  - `test_no_raw_media_in_history` — po voice/photo/image-doc message, `history` zawiera tylko stub reply, żadnych file_id, transkrypcji, Drive linków.
- `TEST_PLAN_CURRENT.md` — usunięte voice/photo flows (już wcześniej zrobione 14.04). Ewentualnie dodać 3 smoke testy stub responses.
- Reviewer antipattern list (`AGENT_WORKFLOW.md`) — dodać: "voice/photo handler wywołujący Whisper/Drive/intent flow w MVP" jako red flag.

**Rationale:** User nie dostaje ciszy ani kryptycznego błędu po wysłaniu głosówki/zdjęcia. Scope MVP jest jasny (POST-MVP komunikat). Handler łatwo podmienić na prawdziwy flow w POST-MVP (jeden punkt zmiany). Spójność z 3-tier scope model (POST-MVP roadmap vs vision-only vs NIEPLANOWANE). Multi-meeting rejection zapobiega cichemu gubieniu danych (user zakłada że dopisaliśmy 2, a dopisaliśmy 1). Image-as-document coverage zamyka boczną ścieżkę do starego Drive flow. Conversation history bez raw mediów — brak payloadów których MVP i tak nie generuje.

### D6. `get_conversation_history` 30-minute window [✅ frozen 14.04.2026]

**Decyzja:** Hybrid opt-in. Wrapper akceptuje opcjonalny `since: timedelta | None = None`. Default = bez filtra (raw). **Intent router i prompt builder zawsze wołają z `since=timedelta(minutes=30)`** — to jest MVP mandate. Inne flow (morning brief, evening follow-up, debug/admin) mogą świadomie użyć innego okna albo żadnego.

**Contract:**

- `database.get_conversation_history(user_id, limit=N, since: timedelta | None = None)`.
- Jeśli `since` podane → wrapper filtruje rekordy **nowsze niż `now_utc - since`**, używając UTC-aware timestampów. Dokładna implementacja filtru (SQL predicate, Supabase API param, Python-side) nie jest kontraktem — kontrakt to: "rekordy starsze niż `since` są wykluczone, porównanie w UTC".
- Brak `since` → wrapper zwraca `limit` ostatnich wiadomości niezależnie od wieku (raw behavior).

**Mandatory callsites (MVP):**

- Phase 3 `shared/intent/` — każde wywołanie z `since=timedelta(minutes=30)`.
- Phase 3 prompt builder (prompts z historią) — każde wywołanie z `since=timedelta(minutes=30)`.

**Discretionary callsites:**

- Phase 6 proactive scheduler (morning brief, evening follow-up) — własny callsite z własnym oknem (np. 12h dla dziennego podsumowania) albo bez `since`. Decyzja w Phase 6 — nie jest contract-blokerem Phase 2.
- Debug / admin / analytics — bez `since`, pełna historia.

**30 min rationale:** Typowy flow OZE handlowca: pending state i kontekst LLM zamknięty w czasie jednej rozmowy (kilka-kilkanaście minut). Po 30 min nowy kontakt z botem = nowy kontekst i nowe intencje. Krótsze okno (5 min) ucina in-flight pending/rozmowę gdy user wraca po chwili przerwy (kawa, telefon). Dłuższe (1h+) miesza dwa różne tematy i myli intent classifier ("zadzwonić do Kowalskiego" sprzed 2h nie jest context dla nowego add_note).

**Pending lifecycle — osobne źródło prawdy:**

- **Pending state (`pending_flows`) nie zależy od conversation history window.** Pending lifecycle (create, confirm, cancel, expire) jest samodzielnym kontraktem w Phase 4.
- 30-min history window **nie kasuje automatycznie pending**. Nie zakładać, że po 30 min pending "zapomniał się sam" — pending expiry to osobna decyzja (Phase 4 scope).
- Odwrotnie też: pending confirm/cancel nie wpływa na 30-min okno history — user może mieć aktywny pending, ale history sprzed 35 min już nie trafia do promptu.

**Affected:**

- `shared/database.py` `get_conversation_history` — dodać `since: timedelta | None = None` param; filtr po UTC-aware timestampach.
- Phase 3 `shared/intent/` — wszystkie callsite do historii z `since=timedelta(minutes=30)`.
- Phase 3 prompt builder — tak samo.
- Phase 4 `shared/pending/` — **brak zależności od history window**; własny expiry/lifecycle per Phase 4 spec.
- Phase 6 scheduler — własny callsite, osobna decyzja dla okna.
- Tests: `test_database.py` — `test_get_history_with_since_filter` (rekordy > since są zwrócone), `test_get_history_since_excludes_older` (rekordy < since pominięte), `test_get_history_without_since_returns_raw`, `test_since_uses_utc_aware_comparison` (naive datetime vs UTC-aware nie mieszać).
- Reviewer antipattern (`AGENT_WORKFLOW.md`): `get_conversation_history` wołane bez `since` w MVP intent / prompt flow — red flag. Naive datetime porównanie w filtrze — red flag.

**Rationale:** Wrapper pozostaje generic (spójnie z Phase 1 audit — wrapper = transport, caller = policy). Intent router / prompt builder mają jednoznaczny kontrakt (zawsze `since=30min`). Future-proof dla Phase 6 (inne okna). Testowalny single-point filtr. UTC-aware wymóg zamyka klasę bugów z mixed-timezone comparison (spójne z D2). Pending lifecycle jawnie rozdzielony żeby nie powstała milcząca zależność "30 min → pending znika".

### D7. Auth: Calendar scope narrowing [✅ frozen 14.04.2026]

**Decyzja:** MVP keeps full `https://www.googleapis.com/auth/calendar` scope. Calendar scope narrowing to `calendar.events` (albo dedicated-calendar ACL equivalent) is **POST-MVP security hardening**, not MVP blocker.

**MVP scope set:**

- `https://www.googleapis.com/auth/calendar` — R/W all user calendars. **Required by onboarding** (`calendars.insert` creates dedykowany "OZE" kalendarz).
- `https://www.googleapis.com/auth/spreadsheets` — R/W Sheets (CRM arkusz tworzony przez Sheets API).
- `https://www.googleapis.com/auth/drive.file` — restricted to Drive files created/opened by the app; used for POST-MVP photo files. **Już narrow**, bez zmian.

**Security model (MVP):**

- Refresh token encrypted at application level with Fernet; ciphertext stored in Supabase (`users.encrypted_refresh_token`).
- Encryption key held in env (`ENCRYPTION_KEY`), nie w Supabase. Key rotation runbook jako operational security housekeeping (Phase 1 audit item, osobny od D7).
- Dedykowany kalendarz "OZE" w Google Calendar UI → user widzi dokładnie co agent tworzy i może w każdej chwili usunąć kalendarz/odebrać dostęp.
- Revoke refresh token flow (oddzielny Phase 1 housekeeping item, high priority) — **nie jest warunkiem D7**, ale komplementarne mitigacje.

**Why narrowing is deferred:**

- MVP onboarding wymaga `calendars.insert` → potrzebny pełny `calendar` scope. Odebranie tego psuje one-click onboarding.
- `calendar.events` scope nie daje per-calendar-ID narrowing — token z tym scope edytuje eventy we wszystkich kalendarzach usera. Realny benefit mniejszy niż się wydaje.
- Scope downgrade flow (dwustopniowe consent: onboarding z pełnym, potem re-auth z węższym) wprowadza double-auth UX regres i nie gwarantuje downgrade'u refresh_tokena po stronie Google.

**POST-MVP roadmap item:**

- `calendar_scope_narrowing` — migration do `calendar.events` z przeprojektowanym onboardingiem (user-created calendar + paste ID, albo scope downgrade flow z osobnym consent).
- Traktowane jako **POST-MVP security hardening** (roadmap), nie vision-only. Nie blokuje MVP go-live.

**Affected:**

- `shared/google_auth.py` — scope list pozostaje `["calendar", "spreadsheets", "drive.file"]`. **No code change for D7 itself.**
- `IMPLEMENTATION_PLAN.md` Scope Guardrails → POST-MVP roadmap section — dodać `calendar_scope_narrowing` jako security hardening item.
- Dokumentacja user-facing (onboarding / privacy section w `poznaj_swojego_agenta_v5_FINAL.md` lub dedykowany privacy doc) — dopisać transparentnie: MVP używa pełnego calendar scope; user może w każdej chwili odebrać dostęp w Google Account permissions.
- Tests: brak zmian w auth flow dla D7. (Revoke refresh_token / no-token-material-in-logs testy to osobne housekeeping items per Phase 1 audit.)

**Rationale:** Blast radius realistycznie mitigated przez Fernet-encrypted refresh token + dedykowany OZE kalendarz widoczny dla usera + revoke flow (osobny housekeeping). Narrowing wymaga przeprojektowania onboardingu — POST-MVP feature, nie MVP blocker. Uczciwe wobec MVP scope: pełny `calendar` scope to cena prostego one-click onboardingu. Security hardening roadmap utrzymany jawnie, bez silent drop.

### D8. ExtendedProperties in Calendar events [✅ frozen 14.04.2026]

**Decyzja:** MVP Calendar events carry minimal `extendedProperties.private`: **`event_type` only** (per D4 enum). `oze_agent` flag / `client_row` / `client_name` **nie są zapisywane**. Sheets column P (`ID wydarzenia Kalendarz`) is the primary Sheets → Calendar link, populated **only** for Calendar-backed next steps.

**Write contract (`create_event`) — agent-created events only:**

```python
extendedProperties={
    "private": {
        "event_type": "in_person",  # one of D4 runtime enum values
    }
}
```

- `event_type` values per D4: `in_person`, `phone_call`, `offer_email`, `doc_followup`.
- Agent nie zapisuje `oze_agent`, `client_row`, `client_name` ani żadnych innych custom kluczy w MVP.

**Sheets link (column P):**

- Sheets P column (`ID wydarzenia Kalendarz`) stores Calendar event `id` returned by `events.insert`.
- **P is populated only for Calendar-backed next steps** (D4 `in_person`, `phone_call`, `offer_email`, `doc_followup`). For no-event K values (`Czekać na decyzję klienta`, `Nic — zamknięte`, `Inne`) P **stays empty**.
- Primary direction: Sheets (CRM SSOT) → Calendar via P column event_id.

**Read flows — tolerant of user-added events:**

- `show_day_plan`: list events in dedicated OZE calendar for target date. Per event, read `extendedProperties.private.event_type`:
  - **Present and recognized** (D4 enum value) → render with D4 emoji/duration mapping.
  - **Missing or unknown** → render as generic calendar event. No mutation assumptions, no crash. User may have added event manually to OZE calendar.
- Event title may be used for user-facing display (it contains client name because `add_meeting` wrote it), **but identity/linking relies on Sheets column P event_id, not title parsing**.
- **No Sheets lookup per event for MVP render.**
- Evening follow-up (Phase 6): same tolerant read pattern.

**Reverse lookup (Calendar event → Sheets row):**

- Not MVP flow. Primary MVP direction is Sheets → Calendar via P column.
- Vision-only flows (if separately approved — e.g. `reschedule_meeting`, `cancel_meeting`) may scan Sheets P column for matching event_id. Out of Phase 2 scope.

**Why minimal:**

- Dedicated OZE calendar = no need for `oze_agent` flag (agent events are the default; user-added events are tolerated but not mis-treated).
- `client_row` / `client_name` would drift (user edits Sheets, Calendar stale) — SSOT stays in Sheets per SOURCE_OF_TRUTH.md §4.
- `event_type` stays because it's per-event stable metadata and `show_day_plan` needs emoji/duration without extra Sheets call.
- Title-as-identity forbidden to prevent brittle parsing; event_id in column P is stable and unambiguous.

**Affected:**

- `shared/google_calendar.py` `create_event` — dopisać `extendedProperties.private.event_type` param + write. Nic poza tym.
- `shared/mutations/add_meeting/` (Phase 5) — pass `event_type` do `create_event`; zapisać returned event_id do Sheets P column. Dla D4 no-event K values — skip Calendar create, leave P empty.
- `shared/read/show_day_plan` (Phase 5) — tolerant read: missing/unknown `event_type` → generic render. Żadnych Sheets calls per event.
- Phase 6 evening follow-up — ten sam tolerant pattern.
- Tests:
  - `test_create_event_has_event_type_extended_property` — body eventu zawiera `extendedProperties.private.event_type`.
  - `test_create_event_no_extraneous_private_keys` — body nie zawiera `oze_agent`, `client_row`, `client_name`.
  - `test_show_day_plan_renders_event_type_from_extended_properties` — render bez Sheets call.
  - `test_show_day_plan_handles_missing_event_type` — user-added event bez `event_type` → generic render, no crash.
  - `test_show_day_plan_handles_unknown_event_type` — value poza D4 enum → generic render.
  - `test_add_meeting_writes_event_id_to_sheets_column_p` — dla D4 event-bearing enum.
  - `test_no_event_k_value_leaves_column_p_empty` — `Czekać na decyzję klienta` / `Nic — zamknięte` / `Inne` → P pusty, no Calendar API call.
- Reviewer antipattern (`AGENT_WORKFLOW.md`):
  - Event body zawierający `oze_agent`, `client_row`, albo `client_name` w `extendedProperties.private` w MVP — red flag.
  - `show_day_plan` parsujący title dla identyfikacji klienta — red flag.
  - Sheets P populated dla no-event K values — red flag.

**Rationale:** Minimalne extendedProperties redukuje drift surface (client_name/row). `event_type` zostaje bo jest stabilną per-event metadaną potrzebną przy render. `oze_agent` flag redundantny wobec dedykowanego OZE calendar. Tolerant read (missing/unknown event_type → generic) zamyka risk crasha gdy user doda event ręcznie. Sheets column P jako stable linking key zamyka ryzyko brittle title parsing. P empty dla no-event K values zachowuje spójność D4 (no Calendar event = no event_id).

### D9. User timezone in `users` schema [✅ frozen 14.04.2026]

**Decyzja:** MVP hardcodes `Europe/Warsaw` w kodzie przez **jedną współdzieloną stałą / helper**. `users` table **nie zawiera** kolumny `timezone` w aktywnej MVP schema. Multi-timezone per-user jest **POST-MVP roadmap** item. Legacy kolumna (jeśli istnieje w istniejących środowiskach) → mark as unused / legacy; housekeeping migration **po audycie środowisk**, nie ad hoc w Phase 2.

**Kod contract (per D2):**

- **Jedna stała / helper** dla MVP timezone usage:

  ```python
  from zoneinfo import ZoneInfo
  DEFAULT_TIMEZONE = ZoneInfo("Europe/Warsaw")
  ```

  Lokalizacja: moduł timezone helper (np. `shared/formatting/timezone.py` albo `shared/constants.py` — do decyzji w Phase 5 implementacji). **Brak scattered string literals** `"Europe/Warsaw"` po modułach domain/wrapper/mutations.
- Żaden runtime read/write do `users.timezone` (kolumna nie istnieje w MVP schema).
- Wszystkie D2-affected flows (`shared/google_calendar.py`, `shared/extraction/extract_meeting_data.py`, `shared/mutations/add_meeting/`, formatter layer) **importują i używają `DEFAULT_TIMEZONE`** zamiast inline `ZoneInfo("Europe/Warsaw")`.

**Schema contract:**

- Aktywna MVP schema: `users` nie zawiera `timezone` / `preferred_timezone` / żadnego analogicznego pola.
- **Legacy handling (ostrożny):**
  - Jeśli istniejące środowisko ma legacy `users.timezone` kolumnę → **mark as unused / legacy** (nie czytamy, nie piszemy).
  - Housekeeping migration do usunięcia kolumny zaplanować **po audycie środowisk** (dev/staging/prod — sprawdzić czy są dane, czy nic tego nie czyta poza MVP kodem).
  - **Nie usuwać ad hoc w Phase 2** — usunięcie kolumny z produkcyjnej schema to osobna decyzja i migracja.
  - Spójne z Phase 1 audit podejściem do innych vision-only artefaktów w schema (`reminder_minutes_before` itd.) — flag jako legacy, cleanup pass osobno.

**Rationale:**

- MVP target = OZE handlowcy PL, 100% Europe/Warsaw. Brak real user demand dla multi-timezone.
- Spójność z D2 (domain hardcoded Warsaw, wrapper waliduje tz-aware).
- Schema slot bez runtime wsparcia = antipattern (fikcja; silent bug risk jeśli ktoś ustawi wartość oczekując że działa).
- Jedna stała `DEFAULT_TIMEZONE` zamiast scattered `ZoneInfo("Europe/Warsaw")` zabezpiecza przyszłą migrację do multi-timezone (jeden punkt zmiany) i upraszcza testy (mock w jednym miejscu).
- Legacy column removal ostrożnie — fizyczne dropowanie kolumny w prod wymaga audytu, nie jest Phase 2 housekeeping.

**POST-MVP roadmap item:**

- `multi_timezone_support` — dodać `users.timezone` kolumnę, read w domain layer (przez helper zamiast `DEFAULT_TIMEZONE`), UI / komenda do zmiany, DST coverage cross-country, testy per-user timezone.
- Traktowane jako **POST-MVP roadmap**, nie vision-only. Wejście zależy od real user demand (non-PL handlowcy).

**Affected:**

- `shared/` — nowa stała / helper `DEFAULT_TIMEZONE = ZoneInfo("Europe/Warsaw")` w dedykowanym module (Phase 5 decyzja exact path).
- D2-affected moduły — refactor z inline `ZoneInfo("Europe/Warsaw")` do importu `DEFAULT_TIMEZONE`. Zero funkcjonalnej zmiany, tylko DRY.
- `supabase_schema.sql` — jeśli MVP schema ma już `users.timezone` → mark w komentarzu jako `-- legacy / unused, migration pending audit`. **Nie dropować** w Phase 2.
- `shared/database.py` — żadnych zmian (wrapper nie czyta/nie pisze timezone).
- `IMPLEMENTATION_PLAN.md` POST-MVP roadmap — dodać `multi_timezone_support`.
- Housekeeping backlog (Phase 1 audit follow-ups) — dodać item: "audit environments for legacy `users.timezone` / `reminder_minutes_before` etc., plan consolidated cleanup migration".
- Tests:
  - Brak dedicated D9 runtime testów (D2 pokrywa timezone behavior).
  - Reviewer check: grep `ZoneInfo\("Europe/Warsaw"\)` po kodzie MVP — poza `DEFAULT_TIMEZONE` definicji, zero innych wystąpień. Jeśli pojawia się inline, red flag.
- Reviewer antipattern (`AGENT_WORKFLOW.md`):
  - Inline `ZoneInfo("Europe/Warsaw")` poza `DEFAULT_TIMEZONE` definicji — red flag.
  - Runtime read / write do `users.timezone` w MVP — red flag.
  - Ad hoc `ALTER TABLE users DROP COLUMN timezone` w Phase 2 migracji — red flag (czekamy na environment audit).

---

## Commit strategy

- **Draft start:** D1 frozen, no commit yet.
- **Commit package 1:** D1-D4 (Sheets date format + Calendar-related: timezone, reminders, `Następny krok` enum).
- **Commit package 2:** D5-D9 (voice/photo handler, history window, auth scope, extendedProperties, user timezone).
- Alternative: single commit at the end of Phase 2. Decision at package 1.
