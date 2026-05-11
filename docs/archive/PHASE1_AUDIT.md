# OZE-Agent — Phase 1 Infrastructure Audit

_Last updated: 14.04.2026_

Verdicts per wrapper for Phase 1 of `IMPLEMENTATION_PLAN.md`. Each entry: **REUSE / MINOR FIX / REWRITE**, plus any fixes that are blockers for later phases.

Scope rule (per `SOURCE_OF_TRUTH.md` §1): stable integration wrappers stay; behavior layer is rewritten separately. This audit does not touch Python code — it only assigns verdicts and tags fixes.

---

## Overall status

| Wrapper | Verdict | Fixes | MVP Blockers | Priority |
|---|---|---|---|---|
| `shared/google_sheets.py` | REUSE with minor/contract fixes | 7 items (2 contract, 5 housekeeping) | R4 resolver 0/1/many, date format decision | high |
| `shared/google_calendar.py` | REUSE with minor/contract fixes | 6 items (2 contract, 4 housekeeping) | timezone contract (Phase 5), reminders policy | high |
| `shared/google_drive.py` | REUSE (deferred consumer) | 0 MVP blockers; 6 POST-MVP concerns for when photo flow ships | none (photo flow is POST-MVP) | low (until photo flow scheduled) |
| `shared/database.py` | REUSE with contract fix | 1 contract blocker (async/sync) + 5 housekeeping; schema has 2 vision-only artifacts to mark | async/sync wrapping before Phase 4 / 5 | high |
| `shared/claude_ai.py` | **SPLIT: REUSE transport, REWRITE behavior** | transport (2 fn + constants) reusable; all 8 prompt-bearing functions belong to Phase 3/5/6 rewrite | Phase 3 intent router rewrite; Phase 6 morning brief prompt violates 13.04 decision | high |
| `shared/google_auth.py` | REUSE with minor/security fixes | 8 items (1 top-security: refresh-token revoke; 1 onboarding bug: storage error swallowing; 1 Phase 2 decision: calendar scope; 4 housekeeping/ops-security; 1 tests) | none (OAuth works for MVP; Phase 2 decision on scope does not block rewrite start) | security follow-up, not MVP-rewrite blocker |
| `bot/main.py` | REUSE Telegram plumbing | 2 Phase 2/6 registration decisions (voice/photo handler scope; scheduler init) + 4 housekeeping | none (thin entrypoint; handler internals replaceable without touching this file) | low (plumbing adjustments, not core rewrite) |

---

## `oze-agent/shared/google_sheets.py`

**Size:** 457 lines. **Verdict:** **REUSE with minor/contract fixes.**

Pure async wrapper over sync Google Sheets API. Returns `None` / `False` / `[]` on errors; never raises. Zero coupling to bot handlers or behavior logic. Imports only from `shared/database` (for `google_sheets_id` + cache) and `shared/google_auth` (for credentials).

### Schema — `DEFAULT_COLUMNS`

16 columns A–P, exactly matches the canonical schema in `INTENCJE_MVP.md` §6 and `poznaj_swojego_agenta_v5_FINAL.md`:

`Imię i nazwisko, Telefon, Email, Miasto, Adres, Status, Produkt, Notatki, Data pierwszego kontaktu, Data ostatniego kontaktu, Następny krok, Data następnego kroku, Źródło pozyskania, Zdjęcia, Link do zdjęć, ID wydarzenia Kalendarz.`

N / O are POST-MVP (photo flow). **P is populated in MVP** for Calendar-backed next steps per D8 — stores `event_id` returned by `events.insert`; empty only for no-event K values (`Czekać na decyzję klienta`, `Nic — zamknięte`, `Inne`).

**Note — column K (Następny krok):** inline comment suggests an enum `Telefon / Spotkanie / Wysłać ofertę / …`. These values are not cross-referenced with canonical enum in `INTENCJE_MVP.md` / `agent_system_prompt.md` (where `phone_call` / `in_person` / `doc_followup` are used). Semantic gap → Phase 2 Behavior Contract Freeze.

### Public API — per-function findings

| Function | Lines | Finding |
|---|---|---|
| `get_sheets_service` | 117-119 | ✓ |
| `get_sheet_headers` | 122-145 | ✓. Caches headers in `users.sheet_columns` without invalidation. Dynamic columns are POST-MVP, so OK. |
| `get_all_clients` | 148-178 | ✓. Full-sheet read; OK for MVP scale (<100 clients). POST-MVP optimization if sheets grow. |
| `search_clients` | 199-239 | ✓. Phone path uses exact digit matching (avoids fuzzy false-positives). Suffix-strip + fuzzy per-word. `seen_rows` dedupe. |
| `get_client_by_name_and_city` | 242-252 | ⚠️ Useful as a primitive, but insufficient for R4. New contract requires 0 / 1 / ≥2 distinction (see fix #1). |
| `add_client` | 255-298 | ⚠️ fix #2 (date format decision). |
| `update_client` | 301-339 | ⚠️ fixes #2 (date) + #4 (A1 column letter guard). |
| `delete_client` | 342-385 | ⚠️ fix #5. Not MVP — `delete_client` is vision-only per SSOT §4. Do not expose from MVP behavior layer. |
| `create_spreadsheet` | 388-447 | ⚠️ fix #3 (docstring says "17 columns" — actually 16). |
| `get_pipeline_stats` | 450-457 | ⚠️ fix #6. POST-MVP / dashboard utility only — lejek removed from morning brief per 13.04 decision. |

### Internal helpers

| Helper | Lines | Finding |
|---|---|---|
| `_get_sheets_service_sync` | 45-50 | ✓ |
| `_is_auth_error` | 53-54 | ⚠️ dead code — never referenced. Remove. |
| `_digits_only` | 57-59 | ✓ |
| `_is_phone_query` | 62-66 | ✓ (≥7 digits, ≤4 non-digit chars). |
| `_fuzzy_match` | 69-111 | ✓ Well thought out. Docstring explains edge cases (shared surnames, single-word city false-match); shows history of targeted bug fixes. |
| `_strip_polish_suffix` | 186-196 | ⚠️ **Pragmatic but weak.** Docstring example itself shows the problem: `"Kowalskiego" → "Kowalsk"` (not `"Kowalski"`). Works as fuzzy fallback thanks to threshold, but not reliable Polish lemmatization. Acceptable fallback for MVP; consider `pymorphy2` / morfeusz / custom lemmatizer for POST-MVP if duplicate detection accuracy matters. |

### Fixes — classified

#### Phase 5 blockers (must ship before `shared/mutations/` / `shared/clients/` work)

**1. R4 duplicate resolver — 0 / 1 / ≥2.** `get_client_by_name_and_city` currently returns first match or `None`. `INTENCJE_MVP.md` §5.3 requires:
- **match = 0** → "nie ma takiego klienta"
- **match = 1** → duplicate detected; `[Nowy]` / `[Aktualizuj]` routing
- **match ≥ 2** → ambiguous; disambiguation list

Add `find_clients_by_name_and_city` returning `list[dict]` (with optional confidence / exactness score). `shared/clients/` builds on this.

**2. Date format decision.** `add_client` (line 268) and `update_client` (line 313) write dates as `YYYY-MM-DD`. Documentation (`agent_system_prompt.md`, `INTENCJE_MVP.md`) describes display as `DD.MM.YYYY (Dzień tygodnia)`. Contract does not state whether Sheets stores ISO (formatter renders PL) or PL directly.

Decision options:
- **A:** Change writes to `DD.MM.YYYY`.
- **B:** Formalize in contract: "Sheets stores ISO (`YYYY-MM-DD`); formatter renders PL on display."

Must be decided in Phase 2 Behavior Contract Freeze before Phase 5 read-only handlers (`show_client`, `show_day_plan`) rely on consistent formatting.

**Tests for #1 and #2** (coverage gap expansion — see below).

#### Housekeeping (separate commit; does not block Phase 5)

**3.** Docstring typo — `create_spreadsheet` (line 389): `"default 17 columns"` → `"default 16 columns"`.

**4.** A1 column-letter guard — `update_client` (line 323) uses `chr(ord("A") + col_idx)`. Safe for A-Z (indices 0-25); current 16-column schema (P = idx 15) is within range. Add inline guard comment: *"A1 range assumption holds for ≤26 columns; known safe for current A-P schema. Add proper A1 conversion helper if schema grows beyond Z."* Optional: helper `_col_letter(idx)`.

**5.** `delete_client` marker — add explicit comment: *"NOT MVP — `delete_client` is vision-only per SSOT §4. Do not import into `shared/mutations/`."* Optional: rename to `_delete_client_internal` so import is visibly internal. Reviewer enforces per `AGENT_WORKFLOW.md` antipattern list.

**6.** `get_pipeline_stats` marker — add comment: *"POST-MVP / dashboard utility only. NOT called by morning brief per 13.04 decision."*

**7.** Dead code — remove unused `_is_auth_error` (lines 53-54).

### Test coverage

**Existing:** `oze-agent/tests/test_google_sheets.py` — 108 lines, 9 functions, all passing.

Covered:
- `search_clients` (fuzzy typo, by city, no match, empty sheet)
- `get_pipeline_stats` (counts, empty sheet)
- `get_all_clients` (empty on error)
- `add_client` (returns None on missing sheet — error path only)
- `get_sheet_headers` (returns empty on missing sheet)

**Gaps to fill alongside fixes #1 and #2:**
- Duplicate resolution 0 / 1 / ≥2 matches (for the new R4 resolver).
- 16-column schema contract (create / update adheres to A-P).
- Date write behavior (ISO vs PL; auto-set on add/update).
- `add_client` happy path (row number parse from `updatedRange`).
- No tests for `update_client`, `delete_client`, `create_spreadsheet`, `get_client_by_name_and_city`.

### Observations (no action needed for MVP)

- Tight coupling to `shared/database` (imports `get_user_by_id`, `update_user`) — required for `google_sheets_id` lookup and header cache. Not urgent.
- Single-sheet assumption in `delete_client` (`meta["sheets"][0]`) — aligns with vision of dedicated OZE calendar / sheet. OK.

### Alignment with documentation

| Document | Status |
|---|---|
| `ARCHITECTURE.md` "What Stays" | ✓ wrapper remains as stable infrastructure |
| `IMPLEMENTATION_PLAN.md` Phase 1 | ✓ verdict: REUSE with fixes (1 contract, 6 housekeeping) |
| `IMPLEMENTATION_PLAN.md` Phase 2 | ⚠️ 2 items for freeze: `Następny krok` enum values + date format decision |
| `IMPLEMENTATION_PLAN.md` Phase 5 | ⚠️ blocker: R4 resolver must be ready before `shared/mutations/` / `shared/clients/` |
| `INTENCJE_MVP.md` §6 schema | ✓ 16 columns A-P exact match |
| `INTENCJE_MVP.md` §5.3 duplicate resolution | ⚠️ `get_client_by_name_and_city` does not handle match ≥ 2; need 0/1/many resolver |
| `SOURCE_OF_TRUTH.md` §4 Scope Guardrails | ⚠️ `delete_client` and `get_pipeline_stats` exist at wrapper level; require explicit markers / not-exposed from MVP behavior |

---

## `oze-agent/shared/google_calendar.py`

**Size:** 331 lines. **Verdict:** **REUSE with minor/contract fixes.**

Pure async wrapper over sync Google Calendar API. Same error discipline as `google_sheets.py` — returns `None` / `False` / `[]`; never raises. Imports only from `shared/database` (for `google_calendar_id`) and `shared/google_auth`. Constants: `WORKING_HOURS_START = 9`, `WORKING_HOURS_END = 18`.

### Public API — per-function findings

| Function | Lines | Finding |
|---|---|---|
| `get_calendar_service` | 59-61 | ✓ |
| `create_calendar` | 64-80 | ✓ Creates OZE calendar with `timeZone: "Europe/Warsaw"`. |
| `get_events_for_date` | 83-110 | ⚠️ Uses UTC-midnight boundary (line 91: `tzinfo=timezone.utc`). Events are then filtered by UTC day, not Warsaw day — near midnight this splits events across wrong boundary. See blocker #1. |
| `get_events_for_range` | 113-139 | ✓ Range query by caller-supplied datetimes. |
| `get_upcoming_events` | 142-145 | ✓ Next N hours from now (UTC-aware). |
| `create_event` | 148-185 | ⚠️ Has everything needed for `add_meeting` (title, start, end, location, description). Returns `_event_to_dict` with `id` — sufficient for writing event ID to Sheets column P. Does not set `reminders` field (see blocker #2). |
| `update_event` | 188-231 | ⚠️ fix #3 (vision-only marker). Underlying primitive for `reschedule_meeting`. |
| `delete_event` | 234-254 | ⚠️ fix #3 (vision-only marker). Underlying primitive for `cancel_meeting`. |
| `check_conflicts` | 257-261 | ⚠️ fix #4. Literally wraps `get_events_for_range` — does not compute conflicts. Naming misleads; add clarifier comment. |
| `get_free_slots` | 264-318 | ⚠️ fix #3 (vision-only marker). `free_slots` is vision-only per SSOT §4. |
| `get_todays_last_event` | 321-331 | ⚠️ fix #5. Uses `date.today()` (server-local, not Warsaw). For evening follow-up (Phase 6 Proactive Scheduler), near-midnight day boundary drifts on UTC-deployed servers. |

### Internal helpers

| Helper | Lines | Finding |
|---|---|---|
| `_get_calendar_service_sync` | 26-31 | ✓ |
| `_to_rfc3339` | 34-38 | ⚠️ **Silently assigns `tzinfo=timezone.utc` to naive datetimes** (line 37). A caller passing naive "jutro o 10" expecting Warsaw time gets an event at 10:00 UTC = 12:00 Warsaw. See blocker #1. |
| `_event_to_dict` | 41-53 | ✓ Normalizes events; handles both `dateTime` (timed) and `date` (all-day). |

### extendedProperties

**Not used anywhere in the wrapper.**

For MVP: acceptable. Events live on dedicated OZE calendar; reverse lookup from Calendar → Sheets goes via Sheets column P (`ID wydarzenia Kalendarz`) written by `add_meeting` at creation time. No need for app-level tagging on events.

**Note for Phase 2 contract freeze:** if the architecture ever moves from "dedicated OZE calendar" to "OZE events on user's primary calendar", `extendedProperties.private.oze_*` tagging would be required to filter OZE events. Not a fix now — contract note only.

### Fixes — classified

#### Phase 5/6 blockers (must ship before `shared/mutations/` add_meeting and Phase 6 Proactive)

**1. Timezone handling contract — blocker before Phase 5 (`add_meeting` mutation pipeline).**
- `_to_rfc3339` (lines 34-38) silently converts naive datetimes to UTC. Creates an ambiguity trap: callers passing naive Warsaw-local datetimes (e.g. from intent parser "jutro o 10") produce events at the wrong hour.
- `get_events_for_date` (line 91) uses UTC-midnight day boundary. For Warsaw-resident user, "today" events are queried from UTC-00:00 to UTC-00:00, i.e. Warsaw-02:00 (DST) / Warsaw-01:00 (CET) — off by 1-2 hours on day boundaries.

**Fix (Phase 2 Behavior Contract Freeze decision):**
- Option A: Wrapper contract is "all datetimes must be tz-aware when entering wrapper; naive datetimes rejected or assumed Warsaw". `_to_rfc3339` attaches `ZoneInfo("Europe/Warsaw")` to naive inputs instead of UTC.
- Option B: Document "wrapper callers must pass tz-aware datetimes"; agent layer (intent parser) always produces Warsaw-aware datetimes.
- `get_events_for_date` must use Warsaw-local day boundary (e.g. `ZoneInfo("Europe/Warsaw")` converted to UTC for API call).

**2. Reminders policy.**
- `create_event` (lines 148-185) does not set `reminders` field. Google Calendar default behavior: `reminders.useDefault = True` (event inherits calendar defaults).
- Per `SOURCE_OF_TRUTH.md` §4 NIEPLANOWANE: "Agent-side pre-meeting reminders — handled by native Google Calendar." Current implicit reliance on calendar defaults is accidentally compliant, but not explicit.

**Fix (Phase 2 Behavior Contract Freeze decision):**
- Option A: always set `"reminders": {"useDefault": True}` on `create_event` — explicit intent, relies on calendar defaults.
- Option B: always set `"reminders": {"useDefault": False, "overrides": []}` — fully suppresses reminders from the app side.
- Option C: document that the wrapper intentionally does not touch `reminders` and leaves behavior to Google default.
- **Maan's preferred direction:** wrapper does NOT create agent-side reminders — either Option A (native Google Calendar default) or Option B with explicit empty overrides. Option C (implicit) is acceptable but must be documented.
- Decide once, apply consistently. Current unstated behavior is a compliance cliff.

#### Housekeeping (separate commit; does not block Phase 5/6)

**3. Vision-only markers** on `update_event`, `delete_event`, `get_free_slots`:
- `update_event` and `delete_event` are primitives for `reschedule_meeting` / `cancel_meeting` (vision-only per SSOT §4). Add marker: *"NOT MVP — underlying primitive for vision-only `reschedule_meeting` / `cancel_meeting`. Do not import into `shared/mutations/`."*
- `get_free_slots` is vision-only (`free_slots` intent). Marker: *"NOT MVP — `free_slots` is vision-only per SSOT §4."*
- Reviewer enforces per `AGENT_WORKFLOW.md` antipattern list.

**4. `check_conflicts` clarifier comment.**
- Function name suggests conflict computation but literally wraps `get_events_for_range`.
- Add comment: *"Returns any events overlapping the given range. Calling code decides what counts as a conflict (e.g. any overlap is a conflict in `add_meeting`)."*

**5. `get_todays_last_event` — Warsaw date fix.**
- Line 324: `date.today()` is server-local. For cloud-deployed UTC server, "today" near Warsaw midnight resolves to the wrong date.
- Fix: compute Warsaw-local today via `ZoneInfo("Europe/Warsaw")`.
- Impact: Phase 6 evening follow-up; minor but visible near midnight.

**6. extendedProperties note** (already discussed above — contract note, not code fix).

### Test coverage

**Existing:** `oze-agent/tests/test_google_calendar.py` — 108 lines, 7 test functions, all passing:
- `test_check_conflicts_detects_overlap`
- `test_check_conflicts_no_overlap`
- `test_get_free_slots_full_day_no_events`
- `test_get_free_slots_blocks_occupied_hour`
- `test_get_free_slots_returns_empty_on_error`
- `test_get_todays_last_event_returns_latest`
- `test_get_todays_last_event_none_when_no_events`

**Gaps to fill alongside blockers #1 and #2:**
- `create_event` happy path — title, start, end, location, description, returned `id`, timezone field, reminders field.
- `_to_rfc3339` edge cases — naive vs tz-aware datetime, Warsaw DST transitions.
- `get_events_for_date` Warsaw-midnight boundary — event ending 23:59 Warsaw should be included in "today".
- `create_calendar` timezone (`Europe/Warsaw`).
- `update_event` and `delete_event` — end-to-end path. (Note: these won't be called from MVP behavior layer, but wrapper still needs coverage.)

### Observations (no action for MVP)

- **Tight coupling to `shared/database`** (imports `get_user_by_id`) — required for `google_calendar_id` lookup. Consistent with `google_sheets.py`.
- **Working hours hardcoded** (`WORKING_HOURS_START=9`, `WORKING_HOURS_END=18`) — acceptable for MVP. POST-MVP: user config.
- **No handling of recurring events at mutation level** — `singleEvents=True` expands recurrences on read, which is correct. `create_event` only creates single events. OK for MVP (agent doesn't generate recurring meetings).
- **`_event_to_dict` defaults `status` to `"confirmed"`** — cancelled events are pre-filtered by API (`showDeleted=False` default), so downstream only sees confirmed/tentative. OK.

### Calendar ↔ Sheets sync — feasibility check

Phase 2 contract: *"Calendar ↔ Sheets sync only for agent-owned mutations, especially `add_meeting`. Manual reschedule in Google Calendar is not observed by the bot."*

Wrapper sufficiency:
- ✓ `create_event` returns normalized dict with `id` → `shared/mutations/add_meeting` writes it to Sheets column P.
- ✓ No observation of manual calendar edits needed — matches contract.
- ✓ `add_meeting` auto-transition (`Nowy lead` → `Spotkanie umówione`) operates at Sheets level via `shared/mutations/`; wrapper only provides the event ID.

**Conclusion:** wrapper supports the agreed MVP sync direction (write-only from agent → Calendar + event_id back to Sheets). Sufficient.

### Alignment with documentation

| Document | Status |
|---|---|
| `ARCHITECTURE.md` "What Stays" | ✓ stable wrapper |
| `IMPLEMENTATION_PLAN.md` Phase 1 | ✓ verdict: REUSE with contract fixes (2 blockers + 4 housekeeping) |
| `IMPLEMENTATION_PLAN.md` Phase 2 | ⚠️ 3 items to freeze: timezone contract, reminders policy, extendedProperties note |
| `IMPLEMENTATION_PLAN.md` Phase 5 | ⚠️ timezone contract must be decided before `add_meeting` mutation pipeline |
| `IMPLEMENTATION_PLAN.md` Phase 6 | ⚠️ `get_todays_last_event` Warsaw date fix for evening follow-up |
| `INTENCJE_MVP.md` §5.4 Calendar↔Sheets sync | ✓ wrapper supports agent-owned mutations; `create_event` returns `id` for Sheets column P |
| `SOURCE_OF_TRUTH.md` §4 Scope Guardrails | ⚠️ `update_event`, `delete_event`, `get_free_slots` are vision-only primitives; require markers |
| `SOURCE_OF_TRUTH.md` §4 NIEPLANOWANE | ⚠️ reminders policy needs explicit decision (implicit compliance via calendar default) |

---

## `oze-agent/shared/google_drive.py`

**Size:** 202 lines. **Verdict:** **REUSE (deferred consumer).**

Pure async wrapper over sync Google Drive API. Same error discipline as `google_sheets.py` / `google_calendar.py` — returns `None` / `[]` on errors; never raises. Imports only from `shared/database` (for `google_drive_folder_id` cache) and `shared/google_auth`. Zero coupling to bot handlers or behavior logic.

**Deferred consumer:** Photo flow is POST-MVP per SSOT §4 and listed in `ARCHITECTURE.md` "Deferred flows". The MVP behavior layer does not import any function from this wrapper. Therefore there are **no MVP blockers** against it; the wrapper is structurally sound infrastructure. Concerns below are POST-MVP considerations for when photo flow is scheduled.

### Public API — per-function findings

| Function | Lines | Finding |
|---|---|---|
| `get_drive_service` | 35-37 | ✓ |
| `create_root_folder` | 40-71 | ⚠️ fix #4 (fallback to user_id). Folder name: `"OZE Klienci — {user.name or user_id}"`. If `user.name` is `None`, folder becomes `"OZE Klienci — {UUID}"` in the user's own Drive — visible to the end user and looks technical. |
| `create_client_folder` | 74-110 | ⚠️ fix #1 (collision). Folder name: `"{client_name} — {city}"`. No unique client identifier — two genuine clients with the same name + city collide at folder level. |
| `get_or_create_client_folder` | 113-151 | ⚠️ Compounds fix #1. Matches by folder name only; first hit wins. Two "Jan Kowalski Warszawa" clients would share one folder silently. |
| `upload_photo` | 154-177 | ⚠️ fix #2 (mime types). Only detects jpg/jpeg/png by extension. Misses HEIC (iOS default), WEBP, and magic-byte detection. Phone users commonly send HEIC. |
| `get_client_photos` | 180-202 | ✓ Lists photos ordered by `createdTime desc`, returns `id / name / webViewLink / createdTime`. |

### Internal helpers

| Helper | Lines | Finding |
|---|---|---|
| `_get_drive_service_sync` | 24-29 | ✓ |

### User-requested check list

**Photo flow is POST-MVP.**  
✓ Aligned. Wrapper is infrastructure, not invoked by MVP mutations. `bot/handlers/photo.py` is in `ARCHITECTURE.md` "Deferred flows".

**Folder naming / client identity.**  
- Root folder: `"OZE Klienci — {user.name or user_id}"` — user-facing in their Drive. Fallback to UUID looks technical (fix #4).
- Client folder: `"{client_name} — {city}"` — identity is display name + city. **Does not use unique client ID** (e.g. Sheets row number, UUID). Collision when two real clients share name + city (fix #1).
- Per `INTENCJE_MVP.md` canonical client identity (first name + last name + city): folder name follows this when `client_name` is composed correctly by the caller. No validation at wrapper level — that's callers' job.

**Upload without confirmation (R1).**  
✓ R1 is a **behavior-layer contract**, not wrapper contract. `upload_photo` correctly provides a primitive — it's the mutation pipeline in Phase 5 that must enforce confirmation before calling. Same pattern as `add_client` / `create_event`: wrapper does the write; confirmation gate is upstream.

Minor note: `get_or_create_client_folder` auto-creates folders during lookup — side-effectful during what reads like a "find" operation. Acceptable because it's only invoked inside an already-confirmed photo upload flow, but worth flagging as subtle.

**Permissions / sharing.**  
✓ No explicit `permissions.create` calls. Google Drive default: new files/folders are private to the owner (the user whose OAuth credentials were used). Matches `poznaj_swojego_agenta_v5_FINAL.md`: "Your data stays in your Google account. Nobody else sees your client data."

POST-MVP consideration: if "team / manager view" (from `poznaj`) ever ships, sharing primitives would need to be added. Not MVP.

**User-facing Drive links.**  
✓ `upload_photo` returns `webViewLink` — format like `https://drive.google.com/file/d/{id}/view`. Not raw tech metadata (URL is clickable, leads to Drive preview for the salesperson). Destination is Sheets column O (`Link do zdjęć`) per `INTENCJE_MVP.md` §6. Appropriate.

`get_client_photos` returns `webViewLink` + `name` + `createdTime`. Timestamps and names are fine for user-visible listing.

**Wrapper reusable despite photo flow deferred.**  
✓ Yes. Same infrastructure pattern as Sheets/Calendar: async-over-sync, clean error handling, no bot coupling. Ready to serve POST-MVP photo flow without rewrite.

### POST-MVP concerns (when photo flow is scheduled — **not MVP blockers**)

**1. Client folder name collision.** `"{client_name} — {city}"` is not unique. Two legitimate clients with the same name + city would share a folder. `get_or_create_client_folder` returns first match silently.  
**Fix direction (POST-MVP):** include Sheets row number or internal client UUID in folder name, e.g. `"Jan Kowalski — Warszawa (#42)"`.

**2. Mime type detection.** `upload_photo` line 164 checks only `.jpg` / `.jpeg` / `.png` by extension. HEIC (iOS default camera format) and WEBP are treated as `image/png` incorrectly. Missing magic-byte detection.  
**Fix direction (POST-MVP):** add HEIC, WEBP, GIF support; consider `python-magic` or similar for magic-byte sniffing.

**3. No client-side size / dimension guards.** Wrapper uploads arbitrary bytes. Multi-MB photos are accepted without guard. Drive quota applies but no friendly error before upload.  
**Fix direction (POST-MVP):** size check at handler layer (not wrapper).

**4. `user.name` fallback to user_id.** Root folder name `"OZE Klienci — {user.name or user_id}"`. If `user.name` is `None`, the end user sees `"OZE Klienci — 550e8400-e29b-41d4-a716-…"` in their Drive. Tech metadata leaked to user-facing surface.  
**Fix direction:** require `user.name` at onboarding; use email local-part or Telegram display name as fallback.

**5. No sharing primitives.** Folder is private by owner. Team / manager view (POST-MVP / vision) will need `permissions.create`.

**6. No tests.** `oze-agent/tests/test_google_drive.py` **does not exist**. Other wrappers have test scaffolding; this one has zero. Low priority now, but test scaffolding should exist before photo flow ships.

### Observations (informational)

- **R1 enforcement is caller responsibility.** Wrapper is correctly stateless with respect to user confirmation.
- **`get_or_create_client_folder` is side-effectful.** Name suggests "find", but it creates on miss. Acceptable in photo flow (already confirmed write path), worth documenting.
- **Root folder ID cached in `users.google_drive_folder_id`** — no invalidation if the user deletes the folder. Minor; photo flow handler could recover via `create_root_folder` retry.

### Alignment with documentation

| Document | Status |
|---|---|
| `ARCHITECTURE.md` "What Stays" | ✓ Drive wrapper stays as stable infrastructure |
| `ARCHITECTURE.md` "Deferred flows" | ✓ photo flow (`bot/handlers/photo.py`) is deferred; this wrapper is NOT deferred — it's infra that photo flow will later consume |
| `IMPLEMENTATION_PLAN.md` Phase 1 | ✓ verdict: REUSE; no MVP fixes; concerns parked for when photo flow is scheduled |
| `INTENCJE_MVP.md` §6 schema N/O | ✓ column N (Zdjęcia) + column O (Link do zdjęć) are POST-MVP per canonical schema; wrapper's `upload_photo` returns `webViewLink` appropriate for column O |
| `SOURCE_OF_TRUTH.md` §4 POST-MVP roadmap | ✓ `photo_upload` in POST-MVP roadmap; wrapper ready |
| `poznaj_swojego_agenta_v5_FINAL.md` | ✓ "Your data stays in your Google account" — default-private Drive aligns |

### Tests

**No test file.** `oze-agent/tests/test_google_drive.py` does not exist.

Gap is low priority now (MVP doesn't call these functions), but scaffolding should exist before photo flow is scheduled:
- `create_root_folder` (folder name fallback behavior)
- `create_client_folder` / `get_or_create_client_folder` (collision, side-effectful-find)
- `upload_photo` (mime type detection, HEIC failure mode)
- `get_client_photos` (ordering, filtering)

---

## `oze-agent/shared/database.py` (+ `supabase_schema.sql`)

**Size:** 312 lines of Python + 179 lines of schema (`oze-agent/supabase_schema.sql`). **Verdict (split as requested):**

- **DB wrapper as infra:** REUSE with one contract blocker (async/sync mismatch) + housekeeping.
- **Behavior state machine on top:** rewrite in `shared/pending/` (Phase 4). DB primitives are adequate storage; logic belongs elsewhere.

Supabase client singleton via service key (bypasses RLS). Returns `None` / `0` / `[]` on failure; never raises. Imports `bot.config.Config` (for Supabase URL + service key).

### Schema summary (`supabase_schema.sql`)

11 tables. Separation MVP/vision:

| Table | Role | Note |
|---|---|---|
| `users` | user config + Google IDs + scheduler settings + subscription + consents | ⚠️ contains `reminder_minutes_before` (NIEPLANOWANE) and `pipeline_statuses` / `default_meeting_duration` (vision-only) — see housekeeping #3 |
| `pending_flows` | one row per user; `flow_type` + `flow_data` JSONB + `reminder_sent` | ✓ adequate for state machine |
| `pending_followups` | evening follow-up queue with `status` ∈ {pending, asked, completed, skipped} | ✓ matches Phase 6 evening follow-up |
| `conversation_history` | role / content / message_type / created_at | ✓ matches Phase 4 memory needs |
| `interaction_log` | AI call telemetry (tokens, cost) | ✓ |
| `daily_interaction_counts` | interaction budget + `borrowed_from_tomorrow` | ⚠️ `borrowed_from_tomorrow` tied to interaction-limit mechanic that SSOT flagged as vision-only, not MVP contract |
| `user_habits` | `default_meeting_duration` | ⚠️ vision-only (nauka nawyków per SSOT §4). Can stay as empty scaffold. |
| `promo_codes`, `payment_history`, `webhook_log`, `admin_broadcasts` | billing + admin ops | ✓ out of agent MVP behavior scope |

**✓ No CRM source-of-truth leakage** — no `clients` / `notes` / `meetings` / `pipeline` tables keyed on client. All CRM data correctly lives in Google Sheets/Calendar/Drive. Matches `CLAUDE.md` boundary rule.

RLS enabled on all sensitive tables; service key bypasses. OK for server-side bot.

### Public API — per-function findings

| Function | Lines | Finding |
|---|---|---|
| `get_supabase_client` | 19-24 | ✓ Singleton, service key. |
| `get_user_by_telegram_id` | 30-44 | ⚠️ fix #1 (sync). ✓ logic. |
| `get_user_by_id` | 47-61 | ⚠️ fix #1 (sync). ✓ logic. |
| `create_user` | 64-76 | ⚠️ fix #1 (sync). ✓ logic. |
| `update_user` | 79-93 | ⚠️ fix #1 (sync). Auto-sets `updated_at`. ✓ |
| `log_interaction` | 99-120 | ⚠️ fix #1 (sync). ✓ telemetry primitive. |
| `get_daily_interaction_count` | 123-140 | ⚠️ fix #1 (sync). ⚠️ sums `count + borrowed_from_tomorrow` — implements vision-only "borrow 20 from tomorrow" mechanic. Works as a primitive, but behavior layer should not use the `borrowed_*` column in MVP. |
| `increment_daily_interaction_count` | 143-168 | ⚠️ fix #1 (sync). Read-modify-write race under concurrent load (not an issue for Telegram single-user stream). |
| `save_conversation_message` | 174-191 | ⚠️ fix #1 (sync). ✓ primitive. |
| `get_conversation_history` | 194-209 | ⚠️ fix #1 (sync). ⚠️ fix #2. No 30-minute window filter — returns last N regardless of age. Per `poznaj`: "10 messages or 30-minute gap". Caller must filter by `created_at`, or add optional `since` param. |
| `save_pending_flow` | 215-228 | ⚠️ fix #1 (sync). Upsert on PK telegram_id — one active flow per user. ✓ matches R3 pattern. |
| `get_pending_flow` | 231-245 | ⚠️ fix #1 (sync). ⚠️ fix #4. No age check — stale rows survive restarts (see Pending expiry). |
| `delete_pending_flow` | 248-255 | ⚠️ fix #1 (sync). ✓ |
| `save_pending_followup` | 261-281 | ⚠️ fix #1 (sync). ✓ |
| `get_pending_followups` | 284-299 | ⚠️ fix #1 (sync). ✓ ordered by `event_end_time`. |
| `update_pending_followup` | 302-312 | ⚠️ fix #1 (sync). Sets `asked_at` when status = `asked`. ✓ |

### User-requested focus areas

#### Pending state lifecycle (parsed → pending → committed/cancelled)

`pending_flows` primitives cover:
- **create / update** → `save_pending_flow` (upsert by PK = telegram_id).
- **read** → `get_pending_flow`.
- **terminate** → `delete_pending_flow` (both commit and cancel dissolve the row).

⚠️ **No `outcome` column** distinguishing `committed` vs `cancelled`. If `shared/pending/` wants telemetry for confirm vs cancel rates, it must log elsewhere (e.g. `interaction_log`) or extend the schema. Not a blocker; state machine decision in Phase 4.

**Verdict:** primitives adequate. State semantics live in `shared/pending/` on top of `flow_data` JSONB.

#### R3 routes (auto-cancel, ➕ Dopisać, auto-doklejanie, compound fusion)

All four are state-machine behaviors on top of the current DB primitives:

- **auto-cancel:** `delete_pending_flow` + next `save_pending_flow` for new parsed input. ✓
- **➕ Dopisać:** update `flow_data` on existing row via `save_pending_flow` upsert. ✓
- **auto-doklejanie:** same as Dopisać without button press — state-machine concern; DB unchanged. ✓
- **compound fusion:** merge two operations into a single `flow_data` blob before commit — state-machine concern; DB stores resulting blob. ✓

**Verdict:** DB is a fine backing store. Routes belong to `shared/pending/` (Phase 4 rewrite).

#### R7 `next_action_prompt` state (`awaiting_next_action`)

No dedicated column or table. Easily encoded as `flow_type = "awaiting_next_action"` with the relevant client reference in `flow_data`. No DB change required.

**Verdict:** covered by current primitives.

#### Conversation history: 10 messages / 30 minutes

- `get_conversation_history(telegram_id, limit=10)` returns oldest-first, limit = 10. ✓ 10-message part.
- ⚠️ **No 30-minute window** at DB layer. Post-filter by `created_at` in caller, or add optional `since` / `max_age` parameter to the wrapper. See fix #2.

Index `idx_conversation_history_telegram_id (telegram_id, created_at DESC)` is present — time-range queries are cheap.

#### Active client (rolling window)

No dedicated column, not persisted at DB level. Expected to be derived from `conversation_history` or cached in `pending_flows.flow_data` by the state machine (per `INTENCJE_MVP.md` R6: "`user_data['active_client']`" is runtime memory, not DB row).

**Verdict:** intentionally not at DB level. Phase 4 state machine responsibility.

#### Supabase boundary (system vs CRM)

✓ Clean separation. System state (users, pending, conversation, telemetry, billing) in Supabase. CRM source-of-truth (clients, notes, meetings, pipeline) in Google. No overlap tables.

One grey area: `daily_interaction_counts.borrowed_from_tomorrow` implements a vision-only mechanic (per SSOT §4: "daily interaction budget — product/business direction, no approved number, no borrow-from-tomorrow mechanic"). Column exists; behavior layer in MVP should not use it.

#### Cleanup / expiry of pendings

⚠️ **No automatic expiry** on `pending_flows`. Row persists until user's next flow overwrites it (PK upsert) or manual `delete_pending_flow`.

- User goes silent → pending stays → user comes back next day and hits stale pending.
- Per `poznaj` 30-minute conversation memory rule, pending should expire too.
- No scheduled cleanup function, no TTL column discipline.

`pending_followups` has `status` field and `asked_at` — better hygiene, but still no automatic archival.

**Finding:** expiry is a Phase 4 state-machine concern. Options:
- Check `updated_at` in `get_pending_flow` + stale → treat as absent.
- Scheduled cleanup (cron) deleting `updated_at < now() - interval '30 minutes'` for `pending_flows`, and archiving completed `pending_followups`.

Not a DB wrapper fix per se — the primitives expose what's needed. State machine owns the decision.

#### User config

Fields relevant to agent runtime (`users` table):

- ✓ OAuth: `google_access_token`, `_refresh_token`, `_token_expiry`
- ✓ Google IDs: `google_sheets_id`, `google_calendar_id`, `google_drive_folder_id`
- ✓ Scheduler: `morning_brief_hour INTEGER DEFAULT 7`, `working_days JSONB DEFAULT '[1,2,3,4,5]'`
- ✓ `sheet_columns JSONB` — cached header names
- ✓ `onboarding_completed BOOLEAN`
- ⚠️ `reminder_minutes_before INTEGER DEFAULT 60` — **NIEPLANOWANE** per SSOT §4 (no agent-side pre-meeting reminders). Column exists but MVP must not use it. See housekeeping #3.
- ⚠️ `default_meeting_duration INTEGER DEFAULT 60` — **vision-only** (nauka nawyków per SSOT §4).
- ⚠️ `pipeline_statuses JSONB` — editable statuses from dashboard (**vision-only**). Default value is the canonical 9 statuses, so MVP works if nobody edits it.
- ❌ **No timezone column.** Warsaw is hardcoded in `google_calendar.py`. For MVP (Poland only) this is fine, but Phase 2 Behavior Contract Freeze should note: "single-timezone assumption Europe/Warsaw; if multi-timezone ever shipped, `users.timezone` column must be added."
- ❌ **No explicit working-hours columns.** `google_calendar.py` has `WORKING_HOURS_START=9, END=18` hardcoded. `users.working_days` captures days but not hours. POST-MVP concern when dashboard ships user config.

#### No CRM source-of-truth leakage

✓ Verified. No client-level tables in Supabase. All CRM data in Google.

#### Async/sync mismatch — **CONTRACT BLOCKER**

**Every function in `database.py` is synchronous** (`def`, not `async def`). Other wrappers (`google_sheets.py`, `google_calendar.py`, `google_drive.py`) use `asyncio.to_thread` consistently. `database.py` does not — it calls `supabase-py` directly, which issues HTTP requests synchronously.

**Impact:** Called from `async def` Telegram handlers → **blocks the event loop** on every DB call. For MVP user scale (single user → single bot instance), latency hit is small. But:
- Pattern break vs other wrappers.
- Phase 4 `shared/pending/` will be called repeatedly per message; blocking I/O in an async state machine is wrong on principle.
- Under any real concurrency (Phase 6 proactive scheduler firing while user types) this causes contention.

**Fix (blocker before Phase 4):**
- Option A: wrap every function in `asyncio.to_thread` (same pattern as Sheets/Calendar/Drive wrappers). Minimal code change; consistent with other wrappers.
- Option B: switch to async Supabase client (if `supabase-py` v2 async is available). Bigger change; arguably cleaner.
- Option C (discouraged): keep sync but mandate callers wrap at call sites. Error-prone.

**Preferred direction:** Option A — uniformity with the other three Google wrappers.

### Fixes — classified

#### Phase 4 / 5 blockers (must ship before `shared/pending/` rewrite)

**1. Async/sync consistency.** Wrap all public functions in `asyncio.to_thread` (same pattern as Sheets/Calendar/Drive wrappers). Entire API surface is affected; signature change: `def` → `async def`. Callers must `await`. Phase 4 state machine depends on this being correct.

#### Housekeeping (separate commit; does not block Phase 4)

**2. `get_conversation_history` time window.** Add optional `since: datetime` / `max_age_minutes: int` parameter to enforce 30-minute memory rule at wrapper level, or document that caller must post-filter. Either works; pick one in Phase 2 Behavior Contract Freeze.

**3. Schema artifacts of vision-only features.** Add explicit markers in schema comments or in the wrapper docstrings:
- `users.reminder_minutes_before` — **NIEPLANOWANE** per SSOT §4 (no agent-side pre-meeting reminders). Column exists but MVP must not read or write it. Candidate for drop in future migration.
- `users.default_meeting_duration` and `user_habits.default_meeting_duration` — vision-only (nauka nawyków). Dormant in MVP.
- `users.pipeline_statuses` — vision-only (dashboard-editable statuses). MVP relies on default 9.
- `daily_interaction_counts.borrowed_from_tomorrow` — vision-only "borrow mechanic". MVP ignores.

Reviewer enforces per `AGENT_WORKFLOW.md` antipattern list.

**4. Pending flow expiry.** Not a wrapper fix, but a Phase 4 state-machine contract: treat `pending_flows` row as expired if `updated_at` older than N minutes (30 per `poznaj`). Alternative: scheduled cleanup in Phase 6.

**5. Timezone field missing.** `users.timezone` does not exist. Warsaw is hardcoded in `google_calendar.py`. Phase 2 Behavior Contract Freeze should note: MVP is single-timezone (`Europe/Warsaw`); multi-timezone POST-MVP would require schema migration.

**6. `update_user` `updated_at`.** Uses `datetime.utcnow().isoformat()` without `tzinfo`. Produces naive ISO string. Supabase `TIMESTAMPTZ` accepts but may interpret as UTC by default. Minor — tied to Calendar timezone discussion (fix #5 there). Prefer `datetime.now(timezone.utc)`.

### Test coverage

**Existing:** `oze-agent/tests/test_database.py` — 126 lines, 10 test functions, passing:

- `test_get_user_by_telegram_id_found` / `_not_found`
- `test_create_user_returns_created_dict` / `_returns_none_on_error`
- `test_log_interaction_does_not_raise` / `_on_db_error`
- `test_get_daily_interaction_count_new_day_returns_zero` / `_existing_row`
- `test_get_pending_flow_returns_none_when_not_found` / `_returns_flow`

**Gaps to fill alongside Phase 4 state machine:**

- `update_user` round-trip (fields + `updated_at` auto-set).
- `save_pending_flow` + `get_pending_flow` round-trip, including upsert on existing row (R3 Dopisać).
- `delete_pending_flow` idempotency.
- `save_conversation_message` / `get_conversation_history` ordering and time-window (once decision on fix #2 is made).
- `save_pending_followup` + `update_pending_followup` status transitions.
- `increment_daily_interaction_count` insert-vs-update branch.

### Observations (informational)

- **Singleton `_client`** is module-level mutable state. Safe for single-process bot; would need rework if tests run in parallel with distinct configs (set-up teardown can bypass by calling `create_client` directly, but the singleton sticks).
- **`single()` raises on zero rows** — caller paths handle via `try/except` + debug log. Consistent but spams `.debug` on every empty lookup (which happens often for `get_pending_flow`). Not a bug, just noisy at debug verbosity.
- **Service key usage** — bot is trusted server-side; bypasses RLS. Correct for this architecture. RLS on the tables is a defense-in-depth if anon key is ever exposed.

### Alignment with documentation

| Document | Status |
|---|---|
| `ARCHITECTURE.md` "What Stays" | ✓ DB wrapper + schema stay as stable infrastructure |
| `ARCHITECTURE.md` Module boundaries | ✓ system state in Supabase, CRM in Google — clean separation |
| `IMPLEMENTATION_PLAN.md` Phase 1 | ✓ verdict: REUSE + 1 contract blocker (async) + 5 housekeeping |
| `IMPLEMENTATION_PLAN.md` Phase 2 | ⚠️ 2 items to freeze: conversation-history 30-minute rule (wrapper-level vs caller-level) + timezone single-zone assumption |
| `IMPLEMENTATION_PLAN.md` Phase 4 | ⚠️ async/sync blocker; state machine in `shared/pending/` builds on these primitives |
| `IMPLEMENTATION_PLAN.md` Phase 6 | ⚠️ evening follow-up uses `pending_followups` — primitives adequate; scheduler logic in Phase 6 |
| `INTENCJE_MVP.md` R6 active client | ✓ not at DB level — rolling window in state machine, correct |
| `SOURCE_OF_TRUTH.md` §4 NIEPLANOWANE | ⚠️ `users.reminder_minutes_before` exists but must not be used |
| `SOURCE_OF_TRUTH.md` §4 vision-only | ⚠️ `default_meeting_duration`, `pipeline_statuses`, `user_habits`, `borrowed_from_tomorrow` — schema artifacts; MVP ignores |
| `CLAUDE.md` data ownership | ✓ no CRM leakage into Supabase; all client data in Google |

---

## `oze-agent/shared/claude_ai.py`

**Size:** 557 lines. **Verdict:** **SPLIT: REUSE transport, REWRITE behavior.**

This file is not a pure infrastructure wrapper. ~10% is transport (low-level Anthropic API calls); ~90% is behavior — prompt-bearing functions that encode contracts (intent classification, client/meeting/note extraction, morning brief format, follow-up parsing). Per `IMPLEMENTATION_PLAN.md` Phase 3 and `ARCHITECTURE.md` "Core rewrite", these behavior functions belong to the rewrite modules (`shared/intent/`, `shared/extraction/` or `shared/mutations/`, `shared/prompts/`, Phase 6 proactive). Transport pieces stay.

### What stays (transport)

| Piece | Lines | Role |
|---|---|---|
| `call_claude` | 42-78 | Low-level API call; returns `text / tokens_in / tokens_out / cost_usd / model` |
| `call_claude_with_tools` | 84-136 | Tool-use variant; returns `tool_name / tool_input / text` |
| `MODEL_COMPLEX`, `MODEL_SIMPLE` | 21-22 | Model IDs (hardcoded — see housekeeping #2) |
| `COST_PER_MTOK_IN` / `_OUT` | 25-26 | Cost tables per model-type |

These can be moved into a new `shared/ai/transport.py` (or kept here under a trimmed `shared/claude_ai.py`) when Phase 3 starts. They are clean, have no CRM side effects, and never raise.

### What gets rewritten (behavior)

| Function | Lines | Target phase | Notes |
|---|---|---|---|
| `classify_intent` | 199-288 | **Phase 3** `shared/intent/` | Prompt-based legacy; ~50 hand-written examples; JSON-in-text (not tool use); markdown-fence stripping workaround. See blockers below. |
| `extract_client_data` | 294-351 | **Phase 5** (extraction or mutations) | Heavy prompt with slang mapping, tech-specs routing. Returns JSON-in-text. |
| `extract_meeting_data` | 357-401 | **Phase 5** | Parses dates/times/locations. Includes multi-meeting batch in list — multi-meeting is POST-MVP per SSOT, so Phase 5 contract must decide whether classifier emits a single meeting per call. |
| `extract_note_data` | 407-440 | **Phase 5** | Simple 3-field JSON. |
| `generate_bot_response` | 446-457 | **Phase 3** `shared/prompts/` | Model-type auto-routing based on conversation length. |
| `parse_followup_response` | 463-511 | **Phase 6** evening follow-up | Bulk multi-meeting parsing from one transcription. |
| `format_morning_brief` | 517-557 | **Phase 6** morning brief | ⚠️ **Contract violation** — see blocker below. |
| `parse_voice_note` | 142-193 | **Deferred POST-MVP** | Voice is POST-MVP per SSOT §4 / `ARCHITECTURE.md` Deferred flows. |

### User-requested focus areas

#### Mixes transport with behavior/prompts/intents?

**Yes — heavily.** One file owns: API transport + intent classifier + 4 extractors + 2 proactive formatters. Clean split is feasible because transport is already factored (`call_claude`, `call_claude_with_tools`) and behavior functions all call into it without leaking lower-level SDK details.

#### Can we keep only a low-level call wrapper?

**Yes.** Recommended split for Phase 3:
- `shared/ai/transport.py` — `call_claude`, `call_claude_with_tools`, model constants, cost tables (≈100 lines).
- `shared/intent/` — new structured-output classifier (replaces `classify_intent`).
- `shared/extraction/` (or `shared/mutations/<intent>/extract.py`) — `extract_client_data`, `extract_meeting_data`, `extract_note_data`.
- `shared/prompts/` — runtime prompts + system prompt composer + `generate_bot_response`.
- Phase 6 proactive — `format_morning_brief`, `parse_followup_response`.
- Legacy / deferred — `parse_voice_note` stays dormant until voice flow is scheduled.

#### Is `classify_intent` prompt-based legacy that should be replaced by `shared/intent/`?

**Yes — Phase 3 rewrite target, confirmed.** Characteristics of legacy implementation:
- ~70-line hand-written prompt (lines 213-268) with ~50 example lines per edge case.
- JSON-in-text return — caller strips markdown fences (lines 273-277). Not using Anthropic tool-use API.
- Fallback logic: invalid intent → `general_question` with `confidence=0.5` default.
- `VALID_INTENTS` (lines 28-36) mixes MVP + POST-MVP + vision-only + utility intents — no per-intent scope tier.

Phase 3 rewrite should use tool-use / structured output + scope-tiered classification so agent can answer "to feature post-MVP" / "to poza aktualnym zakresem" / "to obsługuje natywnie Google Calendar" per `IMPLEMENTATION_PLAN.md` Phase 3 Done-when.

#### Structured output or free text?

**JSON-in-text everywhere**, with manual markdown-fence stripping. Tool-use API (`call_claude_with_tools`) exists but none of the behavior functions call it. Phase 3/5 rewrite should migrate to tool use for proper structured output.

#### Stale rules in prompts — scan for old decisions

| Rule | Status in `claude_ai.py` |
|---|---|
| 2-button cards | ✓ absent (prompts don't hardcode button counts — that's UI layer) |
| `[Tak]` / `[Nie]` as mutation confirmation | ✓ lines 261-262 map user-typed "tak"/"nie" to `confirm_yes` / `confirm_no` intents — this is user-typed text classification, not bot-emitted buttons. Compliant with the 14.04 decision. |
| `default-merge` for duplicates | ⚠️ line 253 says `"ma numer" + imię → add_client (pójdzie przez R4 merge), NIE edit_client`. "R4 merge" is stale terminology; current contract is `[Nowy]` / `[Aktualizuj]` routing (no merge). Prompt needs rewording in Phase 3 / Phase 5. |
| Voice / photo as MVP | ⚠️ `parse_voice_note` exists as MVP-shaped function. `VALID_INTENTS` includes `assign_photo`. These match POST-MVP intents classifier must recognize, but must not route into MVP mutation pipeline. Phase 3 contract. |
| Pre-meeting reminders | ✓ not mentioned in prompts |
| `Negocjacje` status | ✓ not present |
| Old / wrong statuses | ✓ referenced statuses (lines 229, 233-247): `Oferta wysłana`, `Podpisane`, `Rezygnacja z umowy`, `Odrzucone`, `Nieaktywny`, `Zamontowana`, `Spotkanie odbyte`. All align with the 9-status canonical list; `Negocjacje` is absent. |
| Pipeline stats in morning brief | ❌ **BLOCKER** — `format_morning_brief` (lines 517-557) explicitly asks Claude to render pipeline stats. Prompt (lines 541-546) lists `📊 pipeline` as functional emoji and uses `pipeline_stats` as input. Per 13.04 decision (committed across SSOT / ARCHITECTURE / TEST_PLAN_CURRENT): **morning brief has no pipeline stats.** Current implementation violates the contract. Phase 6 rewrite blocker. |

`VALID_INTENTS` also groups MVP + POST-MVP + vision-only + utility into one flat set. Phase 3 classifier contract requires scope-tier distinction.

#### Model / config / env isolation

- API key from `Config.ANTHROPIC_API_KEY` ✓
- Model IDs **hardcoded** on lines 21-22 (`claude-sonnet-4-6`, `claude-haiku-4-5-20251001`). Swapping models requires code change. Housekeeping #2.
- Cost tables **hardcoded** on lines 25-26. Same concern.
- No env-gated model override for testing / A-B / cheaper-model fallback.

#### Error handling / retries / timeouts

- SDK defaults for network retries; no wrapper-level retry logic.
- No explicit timeout — relies on Anthropic SDK defaults.
- On exception: log + return empty shape. Consistent "never raises" pattern. ✓
- ⚠️ **No distinction between transient (rate limit / 5xx) and permanent (invalid key / model not found) errors.** Caller sees "empty text" either way. Debugging invisible.
- ⚠️ **No cost ceiling / circuit breaker.** A runaway prompt burns unbounded budget.

#### Tests

**Existing:** `oze-agent/tests/test_claude_ai.py` — 134 lines, 8 functions, all passing:

- `test_call_claude_returns_text_and_cost`
- `test_call_claude_simple_uses_haiku`
- `test_call_claude_returns_empty_on_api_error`
- `test_cost_calculation_complex_more_expensive`
- `test_classify_intent_returns_valid_intent`
- `test_classify_intent_falls_back_on_invalid_intent`
- `test_classify_intent_falls_back_on_json_error`
- `test_parse_voice_note_returns_structured_data`

**Coverage:** transport + `classify_intent` + one extraction (voice note).

**Gaps (to address alongside Phase 3 / 5 / 6 rewrites):**
- No tests for `extract_client_data`, `extract_meeting_data`, `extract_note_data`.
- No tests for `generate_bot_response`, `parse_followup_response`, `format_morning_brief`.
- No tests for `call_claude_with_tools` (tool-use path is untested).

#### CRM data / side effects?

✓ **None.** Pure compute + LLM call. No writes to Sheets / Calendar / Drive / Supabase. Logs telemetry only (via caller). Clean separation from CRM layer. Good foundation for the split.

#### Phase 3 fit — transport yes, contract no

- Transport pieces are directly reusable by `shared/intent/` Phase 3.
- Behavior pieces must be rewritten; prompt engineering belongs to `shared/intent/` (intent) + `shared/extraction/` (entity) + `shared/prompts/` (system prompts) per ARCHITECTURE.

### Fixes — classified

#### Phase 3 blockers (before `shared/intent/` rewrite)

**1. Migrate classifier to tool use / structured output.** Replace JSON-in-text pattern with Anthropic tool-use API (`call_claude_with_tools`). Eliminates markdown-fence stripping, improves reliability, reduces prompt size.

**2. Scope-tier the classifier output.** Split `VALID_INTENTS` into:
- MVP intents (6 + `general_question`)
- POST-MVP roadmap (e.g. `edit_client`, `multi-meeting`, `voice_input`, `photo_upload`)
- Vision-only (e.g. `reschedule_meeting`, `cancel_meeting`, `free_slots`, `delete_client`)
- NIEPLANOWANE (e.g. pre-meeting reminders if a user ever asks)

Classifier tags intent with its scope tier so the agent can answer with the correct out-of-scope message (per `IMPLEMENTATION_PLAN.md` Phase 3 Done-when).

**3. Drop "R4 merge" terminology.** Line 253 in `classify_intent` prompt uses legacy "R4 merge" language. Current contract is `[Nowy]` / `[Aktualizuj]` routing with no default-merge. Update prompt.

**4. POST-MVP handling for `edit_client`, `filtruj_klientów`, `lejek_sprzedazowy`, `assign_photo`, `refresh_columns` in `VALID_INTENTS`.** Classifier must recognize these but route to the correct out-of-MVP response per the scope tier — not into the MVP mutation pipeline.

#### Phase 5 scope (extraction rewrite)

**5. Rewrite extractors** as structured-output tool calls:
- `extract_client_data` → `shared/extraction/` (or `shared/mutations/add_client/extract.py`).
- `extract_meeting_data` → `shared/extraction/` (or `shared/mutations/add_meeting/extract.py`). Contract note: multi-meeting is POST-MVP, so Phase 5 must decide whether extractor emits a single meeting or a list that's then rejected for batch > 1.
- `extract_note_data` → `shared/extraction/` (or `shared/mutations/add_note/extract.py`).

#### Phase 6 blockers (proactive rewrite)

**6. `format_morning_brief` prompt violates 13.04 decision.** Current prompt renders pipeline stats (`📊 pipeline` emoji + `pipeline_stats` input). Per SSOT / ARCHITECTURE: morning brief shows meetings + follow-ups; no pipeline stats. Free slots are vision-only per SSOT §4 and must not appear in the brief unless Maan explicitly approves them for proactive context in Phase 2. Remove pipeline stats from prompt and function signature.

**7. `parse_followup_response`** — rewrite per Phase 6 evening follow-up design. Current implementation is functional but interleaved with this file.

#### Deferred (POST-MVP / when voice flow ships)

**8. `parse_voice_note`** stays legacy; not in MVP rewrite. Current prompt mentions `default_duration` (tied to vision-only "nauka nawyków") — fine in legacy scope, flag when voice flow is scheduled.

#### Housekeeping (separate commit)

**9. Config-driven model IDs.** Move `MODEL_COMPLEX` / `MODEL_SIMPLE` to config / env so models can be swapped (test / cheaper / benchmark) without code change.

**10. Retry + timeout + cost ceiling policy.** Explicit decisions:
- Transient vs permanent error distinction (at least log with error code).
- Per-call timeout (avoid hung handlers).
- Cost ceiling per user per day (defense against runaway prompts).

These are cross-cutting concerns for the new `shared/ai/transport.py` after the split.

### Observations (informational)

- **`generate_bot_response` auto-routes to complex model if history > 4 messages** (line 456). Heuristic, not documented as contract. Likely obsolete after Phase 3 — new prompts layer decides model per intent class.
- **`classify_intent` parses last 3 context messages** (line 210). Reasonable; Phase 3 rewrite will formalize context window in `shared/intent/` contract.
- **`extract_client_data` ignores prior conversation context** (explicit in prompt line 304: "Parsuj TYLKO tę jedną wiadomość"). Intentional to avoid cross-client pollution. Keep this rule in Phase 5.
- **`parse_voice_note` + `default_duration`** — tied to vision-only "nauka nawyków" (habit learning). Dormant artifact of earlier vision coupling.

### Alignment with documentation

| Document | Status |
|---|---|
| `ARCHITECTURE.md` "Core rewrite" — intent router, prompt layer, agent decision layer | ⚠️ current file owns all three; Phase 3/5/6 splits them out |
| `ARCHITECTURE.md` "What Stays" | ✓ transport-only subset (call_claude, call_claude_with_tools, constants) remains as stable |
| `IMPLEMENTATION_PLAN.md` Phase 3 | ✓ classify_intent replacement confirmed as target |
| `IMPLEMENTATION_PLAN.md` Phase 5 | ✓ extractors belong here (not in wrapper) |
| `IMPLEMENTATION_PLAN.md` Phase 6 | ❌ `format_morning_brief` prompt VIOLATES 13.04 decision (pipeline stats removal) — rewrite blocker |
| `INTENCJE_MVP.md` §5.3 duplicate resolution | ⚠️ "R4 merge" stale terminology in `classify_intent` prompt |
| `SOURCE_OF_TRUTH.md` §4 scope tiers | ⚠️ `VALID_INTENTS` doesn't tier MVP vs POST-MVP vs vision-only — Phase 3 blocker |
| `CLAUDE.md` data ownership | ✓ no CRM writes / side effects |

---

## `oze-agent/shared/google_auth.py` (+ `shared/encryption.py`)

**Size:** 181 lines + 22 lines (Fernet helper). **Verdict:** **REUSE with minor/security fixes.**

OAuth token lifecycle for Google (Sheets / Calendar / Drive share one grant). Five public functions + `SCOPES` constant. No MVP-rewrite blockers. Several security / onboarding issues to schedule independently of Phase 3 / 4 / 5 / 6.

### What the file owns

| Function | Lines | Role |
|---|---|---|
| `SCOPES` | 21-25 | `spreadsheets`, `calendar`, `drive.file` |
| `get_google_credentials(user_id) -> Credentials \| None` | 28-85 | Runtime credential provider. Called on every Sheets/Calendar/Drive request. Auto-refresh on expiry; persists refreshed token. |
| `store_google_tokens(user_id, credentials)` | 88-98 | Encrypt + persist access + refresh + expiry. |
| `build_oauth_url(user_id) -> str` | 101-119 | Generate Google authorization URL. Uses `requests_oauthlib`. |
| `handle_oauth_callback(code, state) -> dict \| None` | 122-149 | Exchange code → tokens → persist. Uses `google_auth_oauthlib.flow.Flow`. |
| `revoke_google_tokens(user_id) -> bool` | 152-181 | POST `/revoke` + clear DB fields. Uses direct `httpx`. |

Encryption helper (`shared/encryption.py`):
- `get_fernet()` — Fernet from `Config.ENCRYPTION_KEY`
- `encrypt_token(token) -> str` / `decrypt_token(encrypted) -> str`
- `generate_encryption_key() -> str` — one-off admin utility

Callers:
- `build_oauth_url` / `handle_oauth_callback` → `api/routes/google_oauth.py` (FastAPI).
- `get_google_credentials` → Sheets / Calendar / Drive wrappers (all three).
- `revoke_google_tokens` → account-management flow (offboarding).

### User-requested focus areas

**OAuth token lifecycle.**
- *Refresh:* `get_google_credentials` lines 72-79 auto-refreshes and persists. ✓
- *Expiry:* Lines 55-60 parse ISO + strip tzinfo to naive UTC; explicit comment notes the compatibility trap with `datetime.utcnow()` (deprecated in Python 3.12+). Not a current bug; watchpoint.
- *Revoke:* ⚠️ posts **access_token**, which on Google's side may leave `refresh_token` valid. See fix #1.

**Token storage.** ✓ Fernet-encrypted in Supabase `users.google_access_token` / `users.google_refresh_token`. `users.google_token_expiry` is cleartext (non-sensitive). Single key, no rotation flow (fix #5).

**Sync vs async.** All 5 functions are `def`. `get_google_credentials` is the hot path — **but** it is called *inside* the `asyncio.to_thread` wrappers in Sheets/Calendar/Drive (e.g. `google_sheets.py:45-50`, wrapped by `get_sheets_service:117-119`). ✓ effectively non-blocking. The other four functions run at onboarding / offboarding only — rare and tolerable. Unlike `database.py`, this is not a blocker.

**Scopes.**
```
spreadsheets       — full Sheets (read+write). Needed because agent creates the sheet at onboarding.
calendar           — full Calendar (all calendars, all events). ⚠️ too broad.
drive.file         — ✓ restricted: only files created by this app.
```

`calendar` reads/writes **every calendar** on the user's Google account, including personal. Architecture vision (dedicated OZE calendar) supports narrowing — see fix #3.

**Missing / expired credentials.** Consistent "return None; caller decides" pattern; no exceptions propagated. ✓

**Works with Sheets/Calendar/Drive together.** ✓ Single OAuth grant; single access+refresh token pair; all three service wrappers share refresh logic.

**Multi-user isolation.** ✓ Tokens keyed on `user_id` UUID; no shared global Credentials state.

**Logging — secrets hygiene.** No direct token logging. Indirect risk in `%s % e` error lines (exception stringification could theoretically include ciphertext / transport detail). Low risk; guard via fix #6.

**OAuth URL generation.** `build_oauth_url` + `handle_oauth_callback` live in this file. Mixed concerns (runtime vs setup) but not a blocker; split possible in a later refactor.

**OAuth library mix.** ⚠️ fix #4 — `build_oauth_url` uses `requests_oauthlib`; `handle_oauth_callback` uses `google_auth_oauthlib.flow.Flow`. Both work, but inconsistent.

**Tests.** ❌ `oze-agent/tests/test_google_auth.py` does not exist. Significant gap for a security-sensitive module (fix #8).

**Config dependencies.** `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`, `ENCRYPTION_KEY` — all env-driven. No Railway-specific hard-coding.

**Error path smell — `store_google_tokens` swallows errors silently.** If storage fails during `handle_oauth_callback`, the caller still returns a user dict. Onboarding appears successful while tokens are missing (fix #2).

### Fixes — classified

Fixes are ordered by priority within this wrapper. None are MVP-rewrite blockers, but several matter for security.

#### Top security priority

**1. Revoke refresh_token (not access_token).** `revoke_google_tokens` (line 164) should post `refresh_token` — or both. Current behavior leaves the refresh token potentially usable on Google side if extracted by an attacker before the DB clear. **Highest-priority fix in this wrapper.**

#### Real onboarding bug

**2. `store_google_tokens` error-swallowing.** Change signature to `-> bool`. `handle_oauth_callback` checks the return value and fails hard on storage failure. Currently onboarding can appear successful with no tokens persisted.

#### Phase 2 product/security decision (not routine housekeeping)

**3. Calendar scope narrowing.** Reducing `calendar` → `calendar.app.created` (or `calendar.events` scoped to the OZE calendar) may:
- require a fresh OAuth consent from all existing users,
- break flows if the user has events on a non-app-created calendar,
- need a migration for users onboarded with the broader scope.

**Security decision, not silent change:** evaluate narrowing the `calendar` scope once "dedicated OZE calendar" is confirmed as MVP direction in Phase 2 Behavior Contract Freeze. Do not change scope silently for existing users — requires explicit re-consent flow or migration strategy.

#### Housekeeping / operational security

**4. Consolidate OAuth libraries.** Two libraries for one flow (`requests_oauthlib` vs `google_auth_oauthlib.flow.Flow`). Consolidate to `google_auth_oauthlib` (official Google library). Migrate `build_oauth_url` to Flow-based URL generation.

**5. Encryption key rotation runbook.** Single Fernet key, no rotation flow. **Operational security, not code:** document a one-off admin procedure for rotating the key (re-encrypt all users' tokens).

**6. Logging hygiene.** Replace `%s % e` in error logs with `type(e).__name__` + short message. Avoids theoretical ciphertext / token material leaking through exception stringification.

**7. `generate_encryption_key` placement.** Lives in `shared/encryption.py` inside app runtime. Admin utility; okay to stay, but must **not** be exposed through runtime routes (FastAPI endpoints, CLI subcommands served publicly). Document as internal-only.

#### Tests

**8.** `oze-agent/tests/test_google_auth.py` does not exist. Add:
- `encrypt_token` / `decrypt_token` round-trip.
- `build_oauth_url` URL shape + `state` param carries `user_id`.
- `handle_oauth_callback` happy path + failure modes (storage fail, invalid code).
- `get_google_credentials` paths (no user, no refresh_token, decryption fail, expired+refresh succeeds, expired+refresh fails).
- `revoke_google_tokens` happy path + partial failure (Google 400 / 500 + DB clear).
- **Security check:** no token material in logs (capture + grep for plaintext tokens / ciphertext). Low priority but worthwhile for a security-sensitive module.

### No MVP implementation blockers; one Phase 2 security decision

OAuth just works. Auto-refresh keeps runtime credentials alive transparently. **No Phase 3 / 4 / 5 / 6 implementation blockers** — MVP rewrite phases do not touch this wrapper. The only Phase 2 item is the `calendar` scope narrowing decision (#3), and it does not block the start of rewrite — current scope is functional; the decision is whether / when to tighten.

### Observations (informational)

- `datetime.utcnow()` compatibility comment on line 57 acknowledges the tradeoff; watchpoint if google-auth flips to tz-aware.
- Lazy imports of `requests_oauthlib` (line 107) and `httpx` (line 157) — minor hygiene. OK.
- `get_fernet()` per-call — negligible perf, readable.

### Alignment with documentation

| Document | Status |
|---|---|
| `ARCHITECTURE.md` "What Stays" | ✓ `shared/google_auth.py` is stable infrastructure |
| `IMPLEMENTATION_PLAN.md` Phase 1 | ✓ verdict: REUSE with security/hygiene housekeeping |
| `CLAUDE.md` data ownership | ✓ no CRM leakage; tokens are system data in Supabase |
| `SOURCE_OF_TRUTH.md` §4 | ✓ out of product-scope concerns |
| Security — encrypted token storage | ✓ Fernet adequate; single-key without rotation is operational risk |

---

## `oze-agent/bot/main.py`

**Size:** 71 lines. **Verdict:** **REUSE Telegram plumbing.** Thin entrypoint; behavior handlers behind it can be swapped in Phase 3-5 without touching this file. Two small Phase 2 / Phase 6 decisions concerning registration scope. No MVP-rewrite blockers.

### What the file owns

```
main()
 ├─ Config.validate_phase_a()              # legacy naming ⚠️ (see housekeeping #2)
 ├─ Application.builder().token(...).build()
 ├─ 6 handlers registered (order matters):
 │   1. CommandHandler("start", start_command)
 │   2. MessageHandler(filters.VOICE | filters.AUDIO, handle_voice)   ⚠️ voice is POST-MVP (see fix #1)
 │   3. MessageHandler(filters.PHOTO, handle_photo)                   ⚠️ photo is POST-MVP (see fix #1)
 │   4. MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
 │   5. CallbackQueryHandler(handle_button)
 │   6. MessageHandler(filters.ALL, handle_fallback)
 ├─ app.add_error_handler(error_handler)
 └─ branch on Config.ENV:
      dev → app.run_polling(drop_pending_updates=True)
      else → app.run_webhook(0.0.0.0:8443, url_path="/webhooks/telegram")
```

Imports only handler callables + `Application` primitives + `Config`. **Zero behavior logic** in this file.

Handler sizes for context (not audited here):
- `start.py` 121 lines, `text.py` **1779 lines**, `buttons.py` 301 lines, `voice.py` 112 lines, `photo.py` 125 lines, `fallback.py` 44 lines.

`text.py` is the legacy pending-flow / mutation-pipeline monolith — target for Phase 3/4/5 rewrite. `bot/main.py` registers it by reference; swapping the callable is a one-line change in Phase 4/5.

### User-requested focus areas

**Telegram plumbing vs behavior mix.** ✓ Pure plumbing. No business logic. Perfectly scoped.

**Handler registration.** 6 handlers in deterministic order (first match wins, per comment line 44). Current order is sensible.

**Webhook vs polling.** ✓ Explicit branch on `Config.ENV`. Dev polls (`drop_pending_updates=True`); prod webhooks on `0.0.0.0:8443` with `url_path=/webhooks/telegram`. Reasonable.

**Lifecycle / startup.** `main()` validates env, builds app, runs. **No explicit shutdown hook** (SIGTERM / SIGINT handlers) — relies on telegram.ext Application defaults. See housekeeping #4.

**Scheduler init.** ⚠️ fix #3 — `oze-agent/bot/scheduler/__init__.py` **is 0 bytes** (empty module). `main.py` does not import or start any scheduler. **Proactive scheduler is not running.** Matches `CURRENT_STATUS.md` / `IMPLEMENTATION_PLAN.md` Phase 6 status (TBD). When Phase 6 ships, main.py must call scheduler startup with an async job queue (telegram.ext JobQueue, APScheduler, or custom).

**Error handling.** `error_handler(update, context)` (lines 28-33) logs the exception with `exc_info`, replies to user with Polish "⚠️ Wystąpił nieoczekiwany błąd. Spróbuj ponownie za chwilę." — one-line, user-facing in Polish. ✓

**Imports old behavior handlers?** Yes — all 6 handlers in `bot/handlers/*` are pre-rewrite. `main.py` itself doesn't care about their content — it only registers callables. The key insight: **swapping the handler implementation (e.g. `text.handle_text` → new `shared/router/...` dispatcher) requires one line change in `main.py`** per handler. This is the correct plumbing boundary.

**Thin entrypoint, replaceable internals?** ✓ Yes. Only two kinds of change to `main.py` are needed during Phase 3-5 rewrite:
- Re-point registration to new handler callables (one import + one registration line each).
- Adjust filter expressions if chat-type scoping is centralized (see #4).

No other rewrites needed in this file.

**Voice / photo handlers registered despite deferred?** ⚠️ **YES — fix #1.** Lines 46-47:

```python
app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
```

Voice and photo are POST-MVP per `SOURCE_OF_TRUTH.md` §4 and `ARCHITECTURE.md` Deferred flows. Current registration invokes their legacy handlers. For first MVP rewrite, options:

- **A) Unregister:** drop lines 46-47. Incoming voice/photo messages fall through to `handle_fallback`, which replies with a generic "nie rozumiem". Simplest.
- **B) Register but route to POST-MVP response:** keep registration, but point to a small stub handler that says *"to feature post-MVP — nie jest jeszcze dostępne"*. Consistent with intent router's scope-tier response for POST-MVP text messages.
- **C) Feature flags:** `Config.VOICE_ENABLED`, `Config.PHOTO_ENABLED`. Off in MVP → not registered. Useful for gradual rollout.

**Recommendation:** B, because it gives consistent POST-MVP messaging whether the user typed "dodaj głosem" (text classified by router) or sent a voice note (caught by filter). Decision belongs in Phase 2 Behavior Contract Freeze alongside intent router scope tiers.

**Group / private chat filtering.** ⚠️ fix #4 — **not in `main.py`.** Grep finds chat-type filtering scattered across 7 handler files (`text.py`, `buttons.py`, `voice.py`, `photo.py`, `start.py`, `fallback.py`, `utils/telegram_helpers.py`). Each re-checks chat type.

Better architecture: centralize at registration level with `filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND`. Handlers then assume private chat and don't re-check. Simplifies ~6-7 handler files.

Not a Phase 1 blocker — behavior doesn't change — but worth doing when Phase 4/5 rewrites handlers anyway.

**Test coverage.** No test file for `main.py`. Typical for entrypoints; not a gap.

**Local run risks.**
- `drop_pending_updates=True` in both modes — safe default, avoids replay on restart.
- No graceful shutdown (SIGTERM / SIGINT). Relies on telegram.ext default.
- `asyncio.set_event_loop(asyncio.new_event_loop())` at `__main__` (lines 69-70) is unusual — likely workaround for an earlier python-telegram-bot version. Verify still needed.
- No health check path registered for webhook mode — depends on API side (`api/`) exposing one.

### Fixes — classified

#### Phase 2 Behavior Contract Freeze (decision required)

**1. Voice / photo handler registration scope.** Currently registered → invokes legacy POST-MVP handlers. Decide in Phase 2:
- Unregister (fall through to `handle_fallback`), or
- Keep registered but point to a stub that returns "to feature post-MVP" (aligned with intent router scope-tier response), or
- Guard by `Config.VOICE_ENABLED` / `Config.PHOTO_ENABLED` env flags.

Tie this to the intent router scope-tier contract from `claude_ai.py` audit (fix #2 there). A consistent POST-MVP message for voice / photo / text-with-post-mvp-intent keeps the UX coherent.

#### Phase 6 Proactive Scheduler (when that phase ships)

**2. Scheduler init absent.** `bot/scheduler/__init__.py` is empty. No startup hook in `main.py`. Phase 6 rewrite must add:
- Async job scheduler (telegram.ext JobQueue or APScheduler).
- Startup hook at the end of `main()` after `Application.builder().build()`.
- Per-user cron for `morning_brief_hour` + `working_days` (from `users` table).
- Evening follow-up trigger after last meeting per user.
- **No pre-meeting reminders** (explicit rule; `users.reminder_minutes_before` must stay unread — matches `database.py` audit fix #3).

#### Housekeeping

**3. `Config.validate_phase_a` rename.** Legacy "Faza A" naming (predates the 13-14.04 fazowanie cleanup). Rename to `validate_required_env()` or `validate_core()` in `bot/config.py`. Update the call site in `main.py` line 37. Cosmetic.

**4. Centralize chat-type filtering at registration.** ~7 handler files re-check `filters.ChatType` / `effective_chat.type`. Move to registration with `filters.ChatType.PRIVATE & ...`. Simplifies handlers; improves safety (group messages never reach business logic). Do this when Phase 4/5 rewrites handlers.

**5. Graceful shutdown.** Add SIGTERM / SIGINT handlers to close DB connections and cancel scheduled jobs. Low priority.

**6. `asyncio.set_event_loop` legacy check.** Lines 69-70 manually set a new event loop. Verify still needed with current python-telegram-bot version. May be legacy workaround.

### No MVP implementation blockers

`main.py` is correctly scoped as a thin entrypoint. Phase 3-5 rewrites can swap handler callables without touching this file. The two Phase 2 / Phase 6 decisions (voice/photo registration scope; scheduler init) are small plumbing changes tied to those phases, not blockers for starting them.

### Observations (informational)

- **Handler order is load-bearing.** `filters.VOICE | filters.AUDIO` (line 46) must come before `filters.TEXT` (line 48) — a voice note with a caption could match both. Current order catches voice first. OK.
- **`filters.ALL` fallback at end** ensures every message type gets a response — users never see silence from the bot. ✓
- **Webhook URL hard-codes port 8443 and path `/webhooks/telegram`.** Matches typical Telegram webhook setup. Config-driven would be nicer but not MVP.

### Alignment with documentation

| Document | Status |
|---|---|
| `ARCHITECTURE.md` "What Stays" — Telegram plumbing | ✓ `bot/main.py` is the plumbing layer |
| `ARCHITECTURE.md` Deferred flows — voice, photo | ⚠️ voice+photo registered in main.py; decision needed (fix #1) |
| `IMPLEMENTATION_PLAN.md` Phase 1 | ✓ verdict: REUSE with 2 registration/scope fixes + 4 housekeeping |
| `IMPLEMENTATION_PLAN.md` Phase 2 | ⚠️ 1 item: voice/photo handler registration scope |
| `IMPLEMENTATION_PLAN.md` Phase 3-5 | ✓ handler callables are swappable one-line changes |
| `IMPLEMENTATION_PLAN.md` Phase 6 | ⚠️ scheduler init missing; must be added when Phase 6 ships |
| `SOURCE_OF_TRUTH.md` §4 NIEPLANOWANE | ✓ no pre-meeting reminder code in main.py |
| `CLAUDE.md` data ownership | ✓ no CRM writes; pure plumbing |

---

## Phase 1 audit — complete

All 7 wrappers / entrypoints audited. See "Overall status" table at the top of this file for the summary.

Recommended next step: whole-file review of `docs/PHASE1_AUDIT.md` before moving to Phase 2 Behavior Contract Freeze.
