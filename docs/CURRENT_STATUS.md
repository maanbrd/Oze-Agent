# OZE-Agent — Current Status

_Last updated: 04.05.2026_

---

## Decision

Previous bug-by-bug patching track is closed.

Current strategy: **selective rewrite of the behavior layer**.

The Python behavior layer is legacy/reference — not trusted as behavior contract.
The `.md` documentation is the primary project asset.
We do not delete infrastructure blindly.

Operational decision from 27.04.2026: **stabilize the Telegram agent before
finishing the web app**. The web app should not be treated as launch-ready until
the core agent flows are trustworthy in manual testing.

Product decision from 04.05.2026: **offer generator is an approved integrated
slice**. It lives in the existing webapp at `/oferty` and uses Telegram + Gmail
for real customer delivery. It does not reopen broad dashboard/webapp scope.

## Current Implementation Status

Phase 5 (Mutation Pipeline) — done. The active deployed behavior includes the
later 27.04 fixes on top of the original Phase 5 work.

Phase 6 MVP (Morning Brief) — implemented and deployed. Scope frozen per 24.04:
- **morning brief only**, 07:00 Europe/Warsaw, Mon–Fri.
- Sources: Terminarz = Calendar events; Do dopilnowania dziś = Sheets K/L
  (`Następny krok` + `Data następnego kroku` ≤ today, non-terminal status).
- Alt template `Akcja: Klient` — zero declension, deterministic output.
- Dedup via `users.last_morning_brief_sent_date`.
- P6-RCF fixes applied: Warsaw-local Calendar day bounds, strict Google
  fetch for proactive brief (no false-empty on outage), dedup write warning,
  `Follow-up dokumentowy` brief label.
- Evening follow-up, pipeline stats, pre-meeting reminders — POST-MVP /
  NIEPLANOWANE.

Latest deployed hotfixes:
- local R6 implementation — conversation memory now uses 10 messages / 30 min, assistant replies are persisted through handler wrappers, voice confirmations save as `message_type="voice"`, and add_note can derive an active client from recent history.
- `e744d84` — normalize Unicode line/paragraph separators and prevent empty Telegram replies.
- `bfa4061` — strip secret env whitespace before constructing API clients.
- `8b0be20` — carry client data extracted from meeting text into the add-meeting → add-client flow.
- `961fad1` — force `record_add_meeting` when meeting + temporal markers co-occur, redact classifier logs, and avoid treating a contact `telefon` field as a phone-call intent.

Current verification baseline:
- Unit/full test baseline after local R6 implementation: `834 passed`.
- Production Railway deploy for `bot`: `bba35789-9b52-4a77-ae29-3597171ee461`, status `SUCCESS`.
- Test Railway deploy for `bot-test`: `0f206b73-b001-49d1-9d1e-413c1ae7b7d4`, status `SUCCESS`.

### Keep (potential reuse)

- Google Sheets wrapper (`shared/google_sheets.py`)
- Google Calendar wrapper (`shared/google_calendar.py`)
- Google Drive wrapper (`shared/google_drive.py`)
- Supabase / database wrapper (`shared/database.py`)
- OpenAI wrapper (`shared/claude_ai.py`)
- auth / config (`shared/google_auth.py`, env)
- basic Telegram plumbing (`bot/main.py`, handler registration)

### Rewrite

- intent routing
- pending flow / state machine
- confirmation cards
- prompts / orchestration layer
- proactive scheduler / morning brief
- agent decision layer

### Deferred beyond first version

- multi-meeting

Current batch/multi-meeting fragments are legacy reference only.

### Active post-MVP slice (live)

- **Voice transcription** — live since 25.04.2026 (post-MVP slice, 5 commits
  `8beecba..6a8b1d4` on main). Whisper STT → Polish name post-pass via Claude
  haiku → 2-button confirm card (Zapisz/Anuluj). Confirmed transcription flows
  through normal text path via `handle_text(text_override=...)`.
- **Google Drive photo upload** — active post-MVP slice. Telegram photos/images
  use an R1 `✅ Zapisać` card before the first Drive write, update Sheets N/O,
  and open a 15-minute same-client upload session that can be switched by
  caption `zdjęcia do [imię nazwisko miasto]`.
- **Global `/cancel` command** — universal escape hatch for any pending flow
  (added in `48e4a76`).

### Offer Generator baseline

Implementation baseline: `09e0957 feat: add offer generator`.

Delivered scope:
- Web route `/oferty` inside the existing dark app shell.
- Offer templates for `PV`, `Magazyn energii`, `PV + Magazyn energii`.
- Ready offers and drafts, manual ordering for ready offers, duplicate-as-draft,
  delete, validation before publishing/saving ready templates.
- Seller profile with persisted company, logo and global email body template.
  `Akcent` and `Podpis maila` are no longer active UI fields.
- Email body editor uses natural text with draggable variable chips; chips render
  as clean inline rectangles in the editor and can be removed with `x`.
- Test PDF uses the dark preview-style layout, white text, seller logo/company
  when available and no upper-right price block.
- Backend API: `oze-agent/api/routes/offers.py`.
- Shared logic: `oze-agent/shared/offers/` for validation, pricing, PDF,
  email rendering, Gmail MIME/send pipeline and idempotency.
- Supabase system data: `offer_templates`, `offer_seller_profiles`,
  `offer_send_attempts`, bucket `offer-logos`.
- Telegram flow: `jakie mam oferty?`, send with offer number, no-number list,
  wrong-number list, confirmation card `✅ Wysłać` / `❌ Anulować`, Gmail first,
  Sheets follow-up writes only after Gmail success.

Verified before commit:
- Targeted offer/backend pytest suite: `86 passed`.
- `node --test web/tests/offer-email-template-ui.test.mjs web/tests/offer-navigation.test.mjs web/tests/offer-pdf-encoding.test.mjs`: `21 passed`.
- `npm run lint` in `web/`: passed.
- `npm run build` in `web/`: passed.

Not yet proven end-to-end:
- Live Telegram voice → transcript → send offer smoke.
- Controlled-address Gmail Sent check from staging/test user.
- Deployed Supabase Storage bucket and logo upload in target environment.
- Real Sheets partial-failure messaging after Gmail success.

### Operational environments — 27.04.2026

- Production Telegram bot runs from Railway service `bot` on branch `main`, deployment `bba35789-9b52-4a77-ae29-3597171ee461`.
- Test Telegram bot is live at `t.me/OZEAgentTestBot`, Railway service `bot-test`, branch `develop`, deployment `0f206b73-b001-49d1-9d1e-413c1ae7b7d4`.
- `main` and `develop` currently point to `961fad1` (`fix(intent): force record_add_meeting when meeting+temporal markers present`).
- `bot-test` has its own Telegram token and is online, but it may still use the same Google Sheets / Calendar / Supabase integrations as production.
- Manual smoke tests on `bot-test` must use fictional data until backend resources are explicitly separated.

---

## Next Steps

Completed foundation:

1. Uporządkować `SOURCE_OF_TRUTH.md` — done
2. Stworzyć `ARCHITECTURE.md` — done
3. Stworzyć `IMPLEMENTATION_PLAN.md` — done
4. Stworzyć `TEST_PLAN_CURRENT.md` — done
5. Stworzyć `AGENT_WORKFLOW.md` — done
6. Zsynchronizować dokumenty z decyzjami 13-14.04 — done:
   - `INTENCJE_MVP.md`, `agent_system_prompt.md`, `agent_behavior_spec_v5.md`
   - `poznaj_swojego_agenta_v5_FINAL.md`
   - `TEST_PLAN_CURRENT.md`
   - `CLAUDE.md`
   - `SOURCE_OF_TRUTH.md`
7. Phase 1 Infrastructure Audit — done (archived at `docs/archive/PHASE1_AUDIT.md`)
8. Phase 2 Behavior Contract Freeze — done (archived at `docs/archive/PHASE2_CONTRACT_FREEZE.md`; 9/9 decyzji frozen, commits `65b5661` + `117f9c2`)
9. Phase 3 — Intent Router Rewrite — done
10. Phase 4 — Pending Flow + Confirmation Cards — done
11. Phase 5 — Mutation Pipeline — done
12. Phase 6 — Proactive Scheduler / Morning Brief — implemented and deployed
13. Voice transcription — live
14. Google Drive photo upload — active post-MVP slice
15. Test bot on `develop` — live at `t.me/OZEAgentTestBot`

Current active track:

1. Stabilize agent behavior on `bot-test` using fictional data.
2. Build and run a small real-world regression pack for: text add_client, text add_meeting, voice → transcript → add_meeting, photo → Drive, add_meeting → preseed add_client, disambiguation, duplicate handling, R7 next-action prompts, show_day_plan, `/cancel`.
3. Promote fixes from `develop` → `main` only after `bot-test` smoke passes.
4. Separate test backend resources (Sheets / Calendar / Supabase) before destructive or high-volume testing.
5. Run offer-generator smoke separately on fictional clients and controlled email addresses before any real customer send.
6. Return to broad web app/dashboard implementation after the core Telegram agent is stable.

---

## Phase 2 Behavior Contract Freeze — done

9/9 decyzji zamrożonych — pełny kontrakt behavior layer spisany w `docs/archive/PHASE2_CONTRACT_FREEZE.md`.

- **Package 1** (`65b5661`) — D1 Sheets date format, D2 Calendar timezone contract, D3 Calendar reminders policy, D4 `Następny krok` enum values.
- **Package 2** (`117f9c2`) — D5 voice/photo/multi-meeting handler scope, D6 `get_conversation_history` 30-min window, D7 Calendar scope narrowing, D8 extendedProperties, D9 user timezone.

Housekeeping / security items z Phase 1 audit (~32) — osobny backlog, obsługiwane w miarę implementacji Phase 3-7.

## Phase 3 — Intent Router Rewrite — done

Per `docs/IMPLEMENTATION_PLAN.md` Phase 3. Klasyfikator 6 MVP intentów + `general_question` z strukturalnym JSON output. Rozróżnia POST-MVP roadmap / vision-only / NIEPLANOWANE z odpowiednio różnymi reply templates.

Kontrakty zamrożone w Phase 2 (w szczególności D4 enum, D5 voice/photo stub, D6 30-min history window) są wejściem dla Phase 3. D5 dla photo zostało później superseded przez aktywny photo upload slice.

---

## What Changed

### Sesja 13.04

- `CLAUDE.md` — przepisany pod nową strategię (selective rewrite, not patch-track)
- `SOURCE_OF_TRUTH.md` — przepisany na czystą mapę projektu
- `CURRENT_STATUS.md` — oczyszczony z historii sesji i starych bugów
- `ARCHITECTURE.md` — stworzony
- `IMPLEMENTATION_PLAN.md` — stworzony
- `TEST_PLAN_CURRENT.md` — stworzony
- `AGENT_WORKFLOW.md` — stworzony
- `INTENCJE_MVP.md` — zsynchronizowany (dual-write, duplicate resolution, display fields, Calendar sync)
- `agent_system_prompt.md` — zsynchronizowany (button policies, display rules)
- `agent_behavior_spec_v5.md` — zsynchronizowany (duplicate flow, show_client fields, Calendar sync, button rules)

### Sesja 14.04

- `poznaj_swojego_agenta_v5_FINAL.md` — zsynchronizowany jako Product Vision / UX North Star (ramka wizji, 16 kolumn kanonicznych, 9 statusów bez Negocjacji, 3-button, sekcja "Gdy klient już jest w bazie", pre-meeting reminders i twardy limit 100/dzień usunięte z runtime)
- `TEST_PLAN_CURRENT.md` — change_status 3-button, duplicate resolution testy (AC-4a/4b, AN-4, AM-8), show_day_plan (SDP-1..5), voice/photo flow usunięte, morning brief bez pipeline stats, evening follow-up dodany
- `CLAUDE.md` — unified 3-button dla wszystkich mutacji (usunięty wyjątek change_status 2-button), Read First rozszerzone o ARCHITECTURE/IMPLEMENTATION_PLAN/AGENT_WORKFLOW/TEST_PLAN_CURRENT, rewrite list bez voice/photo (POST-MVP)
- `SOURCE_OF_TRUTH.md` — czterowarstwowy podział zakresu prac (MVP / POST-MVP roadmap / Product vision only-wymaga decyzji / NIEPLANOWANE); reschedule_meeting, cancel_meeting, free_slots, delete_client eksplicite vision-only; Voice/photo/multi-meeting jako sekcja deferred; sekcja "Najbliższy krok" bez obietnicy "Phase 2"
- `docs/archive/PHASE1_AUDIT.md` — **stworzony**. Per-wrapper audyt 7 plików infrastruktury (Google Sheets/Calendar/Drive, Supabase, OpenAI/Claude, OAuth, Telegram plumbing). 6 MVP blockerów, 9 Phase 2 decisions, ~32 housekeeping/security items. Zero rewrite'ów — wszystkie wrappery zostają z adjustmentami.

### Sesja 15.04

- `docs/archive/PHASE2_CONTRACT_FREEZE.md` — **stworzony i domknięty**. 9/9 decyzji zamrożonych: D1 Sheets date format (ISO + PL display), D2 Calendar timezone (tz-aware Warsaw, wrapper rejects naive), D3 Calendar reminders (`useDefault: True`, no scheduler pre-meeting), D4 `Następny krok` enum (runtime English ↔ Sheets Polish, K=label never date), D5 voice/photo/multi-meeting → POST-MVP stub (photo później superseded przez aktywny photo upload slice), D6 `get_conversation_history` hybrid `since` param (MVP mandate 30 min), D7 Calendar full scope in MVP (narrowing = POST-MVP hardening), D8 minimal `extendedProperties.private.event_type` + Sheets P as primary link, D9 hardcoded `Europe/Warsaw` via single `DEFAULT_TIMEZONE` constant. Commits: `65b5661` (D1-D4), `117f9c2` (D5-D9).
- `INTENCJE_MVP.md` — docs follow-up: §4.5 K/L semantics per D4 (K=label, L=data, P=event_id), extendedProperties tylko `event_type` per D8 (usunięte `client_sheet_row`/`managed_by`), §7 plan dnia filtruje po dedykowanym OZE calendar zamiast `managed_by` flag, offer_email emoji 📨.
- `IMPLEMENTATION_PLAN.md` — dopisane POST-MVP roadmap items: `calendar_scope_narrowing` (D7), `multi_timezone_support` (D9).
- Drift reconcile #2 (pre-Phase 3): `INTENCJE_MVP.md` §8.2 split na vision-only + §8.3 NIEPLANOWANE (per 4-tier SSOT model z 14.04; reschedule/cancel/free_slots/delete_client przeklasyfikowane z NIEPLANOWANE → VISION_ONLY; daily interaction limit oznaczony jako policy/business vision, nie router intent); §11 kolumna P poprawiona (populated w MVP dla Calendar-backed next steps, per D8); `agent_behavior_spec_v5.md` §6.3 rename NIEPLANOWANE → VISION-ONLY + §6.4 NIEPLANOWANE (tylko pre-meeting reminders); `PHASE2_CONTRACT_FREEZE.md` D8 wording "POST-MVP flows" → "Vision-only flows"; `TEST_PLAN_CURRENT.md` SDP-5 reclassify POST-MVP → VISION_ONLY.

### Sesja 25.04

Voice transcription post-MVP slice deployed na Railway, 5 commitów `8beecba..6a8b1d4` on main:

- **Stage 1** (`8beecba`) — `shared/voice_postproc.py` Polish name normalizer (Claude haiku post-pass, 8-guard fallback strategy: empty input, empty model response, empty corrected, over-long, too many changes, too much diff, JSON invalid, API error) + 28 unit tests. Cherry-pick z reverted `b8bd274`.
- **Stage 2** (`48e4a76`) — `bot/handlers/cancel.py` global `/cancel` command + register w `bot/main.py` + 6 tests. Universal escape hatch dla każdego pending flow.
- **Stage 3** (`8c6c467`) — `bot/handlers/voice.py` rewrite: zawsze pokazuje transcript card (nie ma już high-confidence fast-path), Whisper STT + post-proc integration, MarkdownV2 escape via `escape_markdown_v2()`, single cost log `"whisper-1+haiku"` post-transcribe regardless of next user action. Initial scope miał 4 buttons (Tak/Popraw/Ponów/Anuluj) + 17 tests.
- **Stage 3.5** (`cda6302`) — hotfix `shared/whisper_stt.py:_segment_avg_logprob` helper. OpenAI SDK ≥1.50 zwraca segmenty jako Pydantic `TranscriptionSegment` objects (attribute access), nie dict. Bug istniał wcześniej w stable wrapper, objawił się po Stage 3 deploy. Helper wspiera oba formaty (`isinstance(dict)` → `.get()`, else `getattr()`). 4 nowe testy.
- **Stage 3.6** (`6a8b1d4`) — simplification + readonly fix. 4 buttons → 2 (✅ Zapisz / ❌ Anuluj), drop `:correct`/`:retry` w `buttons.py`. Krytyczny fix: `Message.text` jest read-only w PTB ≥21 (raise AttributeError on assignment) — dodany `text_override: str | None = None` parameter do `handle_text(...)`. Voice intent routing branch w `text.py` ANULOWANY — confirmed transcription idzie przez normalny text path (`handle_text(text_override=transcription)`). Drop 5 nieaktualnych testów.

End state: 801 testów zielony (0 xfailed). Voice end-to-end zweryfikowany na Railway (Telegram smoke: voice → 2-button card → ✅ Zapisz → klasyfikacja → mutation card add_client). Whisper SDK breaking change naprawiony niezależnie. `/cancel` global escape hatch działa.

---

## Phase 4 — Known follow-ups

**Next concrete slice (16.04.2026):** typed-pending **disambiguation / duplicate UX** (see first follow-up below). After F7b parking, this is the next active work per `docs/IMPLEMENTATION_PLAN.md` Phase 4, not more auto-cancel / card-rendering polish (those are largely covered by `a1ec65c`, `cd4a648`, earlier commits). Do not start a new slice until disambiguation typed-pending is completed.

### duplicate UX: same full name across multiple cities needs disambiguation

**Status:** open follow-up.

When the same full name exists in two or more cities and the user types only the name (no city), `detect_potential_duplicate` (post-`aefa2e5`) returns the first name-only match by iteration order instead of asking the user which row they meant.

Example:
- Sheets: `Marysia Mastalerz — Warszawa`, `Marysia Mastalerz — Kraków`
- User: `Marysia Mastalerz`
- Expected: bot asks which Marysia (or shows both candidates).
- Current: bot picks one row silently.

Discovered during smoke testing of `aefa2e5`. Documented as MVP limitation in the docstring at `oze-agent/shared/search.py::detect_potential_duplicate`.

Does not block continuing the typed-pending migration. Duplicate UX is not fully complete until a disambiguation flow is added (separate slice — same shape as the existing disambiguation pending flow used by `add_note` / `change_status`).

### add_note future-action follow-up should offer next step

**Status:** open follow-up.

When a saved note contains a future action / date phrase, the bot stores the note in Sheets but does not propose or create a Calendar event / D4 next step.

Example:
- User: `dodaj notatkę do Marysia Mastalerz: dzwoniła w sprawie awarii pv. Zadzwonić w piątek`
- Current: note appended to Sheets `Notatki`, no Calendar/next-step prompt.
- Expected: agent asks whether to create a `phone_call` next step (D4 enum) / Calendar event for the detected future action, or routes to the `add_meeting` / next-step pipeline.

Discovered during smoke testing of `f56000a`. Not a regression — the `add_note` write migration only changed pending-flow serialization. This is a product gap in note→next-step detection.

Does not block the typed-pending migration. Implementation belongs in a separate slice (likely a small extractor over note text + R7-style follow-up prompt, or routing the suffix into the existing `add_meeting` flow).

### F7a: explicit duration parsing for natural-language meetings

**Status:** open follow-up.

The D4 duration defaults are event-type aware (`in_person=60`, `phone_call=15`, `offer_email=15`, `doc_followup=15`), but natural-language explicit durations like `na 30 minut` are not yet reliable in the production Telegram flow.

Example:
- User: `Zadzwoń do Tomasza Nowickiego jutro o 13 na 30 minut`
- Expected: `phone_call` event with explicit 30-minute duration.
- Current scope: deliberately keeps the event-type defaults and does not harden explicit duration extraction.

Does not block other fixes. Treat as a separate extractor/parser hardening slice over `extract_meeting_data`.

### F7b: production add_meeting duration still shows 60 min for phone/offer flows

**Status:** unresolved, parked (16.04.2026).

After landing the deterministic event_type resolver (`fcad12c`), pending intent-switch guard (`cd4a648`), and LLM prompt alignment (`86f5d27`), manual Telegram smoke still shows meetings created with `60 min` for phone/offer/doc_followup event types.

Smoke observation:
- User typed: `Zadzwoń do Tomasza Nowickiego w sobotę o 12`
- Expected: `phone_call`, `15 min`, location `telefonicznie`.
- Actual: Telegram card displays `Czas trwania: 60 min`.
- Bot was declaratively restarted before the test.

**Decision 16.04.2026:** park the bug, do not hotfix further right now. Resume the main Phase 4 track. Return to this as a dedicated diagnostic slice, not bundled into unrelated work.

**Diagnostic hypotheses to verify on the next attempt:**
1. Is the deterministic resolver (`_resolve_meeting_event_type` / `_infer_meeting_event_type`) actually reached in the production path, or does the dispatcher route into a different code path than `handle_add_meeting` single?
2. Is duration calculated **after** the final `event_type` is resolved, or is there a real path (single or batch) where the old `default_duration` is still applied first?
3. Is the confirmation card rendered from the freshly saved pending flow (post `save_pending`), or from an earlier/cached payload that still carried the 60-min fallback?
4. Is the Telegram bot actually running the current code after the restart? Verify the process, `.venv`, and checkout match the latest commits — a stale process or wrong venv silently reproduces the old behaviour.

**Instrumentation strategy for the next diagnostic pass:**
- Log on entry to `handle_add_meeting` with raw `message_text` and `intent_data.entities`.
- Log the full `meetings` list returned from `extract_meeting_data`.
- Log just before `save_pending` with final `event_type`, `start`, `end`, and computed `duration`.
- Before rerunning the manual smoke, confirm the bot process in use actually comes from the current checkout and venv (kill/restart explicitly; avoid assumptions).

Does not block the main Phase 4 track. Do not revert `fcad12c`, `cd4a648`, or `86f5d27` while diagnosing.

### full-client-data augment: `client_found=True` path can create duplicates

**Status:** open follow-up.

In the Slice 1 ("empty add_meeting + full client data") branch, `_enrich_meeting` may match an existing client in Sheets (`client_found=True`) and return that client's title/location. The handler still pre-seeds an `ADD_CLIENT` draft from the newly-extracted `client_data` at confirm time, bypassing duplicate detection.

Example:
- Sheets row: `Jan Kowalski — Warszawa, tel 111111111, ul. Stara 1`
- Meeting card is empty → user types `Jan Kowalski, Warszawa, ul. Nowa 5, tel 222222222, PV`
- Expected: bot routes through `detect_potential_duplicate` → `[Nowy]` / `[Aktualizuj]` card.
- Current: bot adds Calendar event with Sheets-derived title, then pre-seeds a second `ADD_CLIENT` draft with user's new address/phone, risking a duplicate row if the user taps `Zapisać`.

Discovered during review of Slice 1 (not a regression — pre-existing gap exposed by the new branch). Fix likely: when `_enrich_meeting` returns `client_found=True` and the extracted data differs from the matched row, route through the existing duplicate-detection flow instead of the new-client draft.

### DRY: `extract_client_data` call pattern repeated across augment branches

**Status:** open follow-up.

The pattern `get_sheet_headers + extract_client_data + _filter_invalid_products + filter empty` is now duplicated in the `add_client` augment branch and the new `add_meeting` empty-card branch. A small helper (e.g. `_extract_filtered_client_data(user_id, message_text) -> dict`) would remove the repetition and keep a single point of change for future LLM schema tweaks.

Low priority — no behavior impact.

### change_status Dopisać narrows to next-action only

**Status:** open follow-up.

The `change_status` pending flow's `➕ Dopisać` branch (introduced in `a1ec65c`) only accepts next-action phrasing ("telefon jutro o 14", "spotkanie w piątek"). Non-action replies like `tel 123456789` show the error message `"Dopisz następny krok, np. 'telefon jutro o 14'..."` instead of updating the client's phone number.

This is a deliberate narrow scope — compound fusion per `agent_behavior_spec_v5.md §80` covers `change_status + add_meeting`, not `change_status + edit_client`. If users want to edit client data during a status change, they must cancel and use `add_client` augment.

Product decision needed before implementation: should `➕ Dopisać` in `change_status` route non-action replies through a client-edit flow (analogous to `add_client` augment but on an existing row), and if so, under what confirmation pattern? Likely needs R1 confirmation card for any Sheets write.

Low-to-medium priority — current UX is slightly inconvenient but not broken.
