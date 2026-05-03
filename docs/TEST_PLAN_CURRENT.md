# OZE-Agent — Test Plan

_Last updated: 27.04.2026_

This is the test plan for the new behavior layer (selective rewrite). Not for the old patch-track.

Tests are manual Telegram tests unless stated otherwise.

---

## Test Environments

Primary manual testing happens on the test bot first:
- Telegram: `t.me/OZEAgentTestBot`
- Railway service: `bot-test`
- Branch: `develop`

Production smoke happens only after the tested commit is promoted to `main`:
- Railway service: `bot`
- Branch: `main`

Important: `bot-test` has a separate Telegram token, but may still use the same
Google Sheets / Calendar / Supabase resources as production. Use fictional
clients and obvious test names until backend resources are explicitly separated.

---

## Current Smoke Pack — Agent Stabilization

Run these on `bot-test` after each agent behavior fix. Use fictional data.

| # | Message | Expected |
|---|---------|----------|
| SM-1 | `Dodaj spotkanie z Janem Testowym na jutro o 14. Mieszka w Markach na ulicy Zielonej 28. Telefon 600-100-200. Interesuje go fotowoltaika i magazyn energii.` | First card is `✅ Dodać spotkanie?`, not `Dodać klienta?`. Shows date tomorrow, 14:00, Marki / ul. Zielona 28. After `Zapisać`, client draft is preseeded with phone, city, address, product. |
| SM-2 | Voice message containing the same content as SM-1 | Bot shows transcription card first. After `✅ Zapisz`, flow is the same as SM-1. |
| SM-3 | `Dodaj klienta Jan Telefoniczny, telefon 600100200, jutro podeślę dane` | Does not force `ADD_MEETING`; should route as add_client or ask for client confirmation, not create a Calendar meeting. |
| SM-4 | `Zadzwoń do Marka Testowego pojutrze o 10` | Routes to add_meeting as `phone_call`, not add_client. |
| SM-5 | During any pending mutation card, send `/cancel` | Pending flow cancels in one step; no Sheets / Calendar write. |
| SM-6 | `co mam jutro?` | Routes to show_day_plan, not add_meeting. |
| SM-7 | Add meeting for a non-existing fictional client, then choose `Zapisać` | Calendar event is created; follow-up add_client draft carries all recognized client data from the meeting message. |
| SM-8 | Repeat SM-1 on production only after `bot-test` passes | Same behavior as test bot; no classifier PII in Railway logs. |
| SM-9 | Create/show `Jan R6 Testowy`, then send `dodaj notatkę: zainteresowany pompą` | Bot uses R6 active client and shows add_note card for Jan R6 Testowy. After `Zapisać`, Sheets Notatki contains the note. |
| SM-10 | Repeat SM-9 after the 30-minute memory window expires | Bot asks which client / requires identification instead of using stale context. |
| SM-11 | Send a photo with caption `Jan Foto Testowy Warszawa` | Bot skips "do którego klienta?", shows `✅ Zapisać` Drive card with 15-minute session copy. Before click: no Drive/Sheets write. After click: Drive folder/file exists, Sheets N/O updated. |

Expected Railway classifier log shape after SM-1 / SM-2:

```text
intent classify: tool=record_add_meeting preflight_meeting_hint=True message_len=...
```

Log must not contain client names, phone numbers, addresses, or `message_prefix`.

---

## R1 — No Write Without Confirmation

| # | Scenario | Expected | PASS when |
|---|----------|----------|-----------|
| R1-1 | add_client → check Sheets BEFORE tapping Zapisać | No new row | Sheets unchanged |
| R1-2 | add_meeting → check Calendar BEFORE tapping Zapisać | No new event | Calendar unchanged |
| R1-3 | add_note → check Sheets BEFORE tapping Zapisać | Notes column unchanged | Sheets unchanged |
| R1-4 | ❌ Anulować on any mutation card | One-click cancel, "Anulowane." | No write to Sheets/Calendar, no "Na pewno?" |

---

## add_client

| # | Scenario | Expected |
|---|----------|----------|
| AC-1 | New client: name + city + phone + product | 3-button card, all fields shown. Zapisać → new row in Sheets |
| AC-2 | New client: name + city only (minimal) | Card shows "Brakuje: telefon, email, produkt, adres, źródło" |
| AC-3 | Dopisać → add phone → Dopisać → add product → Zapisać | Card rebuilds each time. Final row has all fields |
| AC-4 | Existing client (same name+city) — certain match | Agent detects duplicate. Shows existing client data. Offers `[Nowy]` / `[Aktualizuj]` |
| AC-4a | AC-4 + click `[Nowy]` | New row created in Sheets (two separate clients, same name) |
| AC-4b | AC-4 + click `[Aktualizuj]` | 3-button mutation card opens for the existing row |
| AC-5 | Existing client — uncertain match (2+ results) | Disambiguation list with full names + cities |
| AC-6 | R7 after add_client Zapisać (no follow-up date given) | "Co dalej z [klient]?" free-text prompt. Any answer (incl. "nie wiem") → flow ends |
| AC-6b | R7 after add_client Zapisać (follow-up date given) | R7 does NOT fire — next step already defined by follow-up meeting |

---

## show_client

| # | Scenario | Expected |
|---|----------|----------|
| SC-1 | "pokaż Jan Kowalski Warszawa" | Read-only card. All filled fields shown (except photos). No buttons |
| SC-2 | "pokaż Kowalski" (bare last name) | Disambiguation list |
| SC-3 | All filled columns visible | Every non-empty column from Sheets appears on card, except Zdjęcia/Link do zdjęć/ID wydarzenia |
| SC-4 | Date fields formatted | DD.MM.YYYY (Dzień tygodnia), not ISO, not Excel serial |

---

## photo_upload

| # | Scenario | Expected |
|---|----------|----------|
| PH-1 | Photo with caption `Jan Kowalski Warszawa` | Skips "Do którego klienta?", shows Drive mutation card with `✅ Zapisać` / `➕ Dopisać` / `❌ Anulować` |
| PH-2 | Photo without caption | Bot asks: `Do którego klienta przypisać zdjęcie? Podaj imię, nazwisko i miasto.` |
| PH-3 | Check Drive/Sheets before clicking `✅ Zapisać` | No Drive upload, no Sheets N/O update |
| PH-4 | Click `✅ Zapisać` | Creates/reuses folder, uploads photo, sets `Zdjęcia` count and `Link do zdjęć`, opens 15-minute session |
| PH-5 | During session send photo without caption | Uploads directly to same client and confirms `📸 Dodane do: ...` |
| PH-6 | During session caption `dach północny` | Uploads to same client; caption becomes Drive description |
| PH-7 | During session caption `zdjęcia do Anna Nowak Kraków` | Does not upload to old client; starts confirmation for Anna |
| PH-8 | Unknown client, choose add | Enters add_client flow; final `✅ Zapisać` creates Sheets row and uploads first photo |
| PH-9 | `❌ Anulować` on photo card | Writes nothing to Drive/Sheets |
| PH-10 | `/cancel` during active photo session | Clears pending photo flow and active session |

---

## add_note

| # | Scenario | Expected |
|---|----------|----------|
| AN-1 | "dodaj notatkę do Jana Kowalskiego Warszawa: dzwonił, chce wycenę" | 3-button card. Zapisać → append to Notatki column |
| AN-2 | Dopisać → "i ma duży dom" → Zapisać | Card rebuilds with combined note |
| AN-3 | Non-existent client | "Nie znalazłem klienta" |
| AN-4 | add_note for client with identical name+city existing (match=1) | `[Nowy]` / `[Aktualizuj]` routing → then 3-button mutation card |

---

## change_status

| # | Scenario | Expected |
|---|----------|----------|
| CS-1 | "zmień status Jan Kowalski Warszawa na Oferta wysłana" | 3-button card (Zapisać + Dopisać + Anulować). Status comparison shown |
| CS-2 | Invalid status name | "Nie znam statusu X. Dostępne: [list]" |
| CS-3 | Same status as current | "Status klienta X jest już: Y." — no card |
| CS-4 | R7 after change_status Zapisać (no compound meeting) | "Co dalej z [klient]?" free-text prompt |
| CS-4b | R7 after change_status + compound add_meeting | R7 does NOT fire — next step defined by the meeting |
| CS-5 | Client not in Sheets | "Nie znalazłem klienta" |

---

## add_meeting

| # | Scenario | Expected |
|---|----------|----------|
| AM-1 | "jutro o 10 spotkanie z Jan Kowalski Warszawa" | 3-button card. Klient enriched from Sheets. Location from Sheets |
| AM-2 | Client not in Sheets | Meeting card with typed name, no enrichment. Calendar event created |
| AM-3 | Multi-meeting (batch) — POST-MVP | Not in MVP scope. In MVP, agent handles one meeting per message |
| AM-4 | Past date | "Data X jest w przeszłości. Podaj datę przyszłą." |
| AM-5 | Calendar conflict | Warning shown on card: "masz już spotkanie o tej porze" |
| AM-6 | Calendar event created after Zapisać | Event in Calendar with title, location, description from Sheets |
| AM-7 | add_meeting with client in "Nowy lead" status | Card shows "Status: Nowy lead → Spotkanie umówione" auto-transition |
| AM-8 | add_meeting for client whose name+city already exists (match=1) with different data | `[Nowy]` / `[Aktualizuj]` routing before meeting card |
| AM-9 | R7 after add_meeting Zapisać | R7 does NOT fire — meeting itself defines the next step |

---

## Calendar ↔ Sheets Sync

| # | Scenario | Expected |
|---|----------|----------|
| SY-1 | add_meeting Zapisać | `Data następnego kroku` updated in Sheets |
| SY-2 | change_status Zapisać | `Status` column updated in Sheets |
| SY-3 | add_note Zapisać | `Notatki` appended, `Data ostatniego kontaktu` updated |

---

## show_day_plan

| # | Scenario | Expected |
|---|----------|----------|
| SDP-1 | "co mam dziś?" | Compact per-meeting format per INTENCJE_MVP §4.6. Header `DD.MM.YYYY (Dzień)` |
| SDP-2 | "co mam w tym tygodniu?" | Grouped by day, each day with `DD.MM.YYYY (Dzień)` header |
| SDP-3 | Dates in output | All dates in `DD.MM.YYYY (Dzień tygodnia)` format, never ISO/Excel serial |
| SDP-4 | No meetings today | "Na dziś nic nie masz w kalendarzu." |
| SDP-5 | "jakie mam wolne okna w czwartek?" — free slots | VISION_ONLY (poza aktualnym MVP scope, wymaga osobnej decyzji Maana). Agent odpowiada że to vision-only i wskazuje `show_day_plan` jako alternatywę, bez halucynacji. |

---

## Pending Flow

| # | Scenario | Expected |
|---|----------|----------|
| PF-1 | Pending add_client + "co mam dziś?" | Auto-cancel pending + show_day_plan |
| PF-2 | Pending add_client + Dopisać + phone | Card rebuilds with phone |
| PF-3 | Pending add_client + type phone directly (auto-doklejanie) | Card rebuilds without clicking Dopisać |
| PF-4 | Pending change_status + "jutro o 10" (compound fusion) | Combined card: status + meeting |
| PF-5 | Pending add_client + unrelated text (e.g. "jutro o 10 Nowak") | Auto-cancel pending + re-route as new input (add_meeting) |

---

## Proactive / Morning Brief (Phase 6 MVP)

Brief runs at **07:00 Europe/Warsaw, Monday–Friday**. Always sent on weekdays
to every eligible user (not suspended, not deleted, `telegram_id` set). Dedup
via `users.last_morning_brief_sent_date` — one send per Warsaw date.

| # | Scenario | Expected |
|---|----------|----------|
| MB-1 | User has 2 Calendar events today + 1 Sheets row with `Następny krok ≤ today` | `Terminarz:` + event lines (`• HH:MM — Label: Client`) + blank line + `Do dopilnowania dziś:` + `• Label: Client`. No declension. |
| MB-2 | No Calendar events, no open Sheets next-steps | Exactly two lines: `Terminarz:\nNa dziś nie masz spotkań.` |
| MB-3 | No Calendar events but ≥1 Sheets row with overdue `Następny krok` | `Terminarz:\nNa dziś nie masz spotkań.` + blank line + `Do dopilnowania dziś:` + rows. |
| MB-4 | `is_suspended=true` user | No brief sent to this user. |
| MB-5 | Bot restart at 07:30 after brief fired | Dedup protects — no second send the same day. |
| MB-6 | Weekend (Saturday / Sunday) | Brief does NOT fire. |
| MB-7 | Calendar or Sheets API fails during brief fetch | Brief is NOT sent, dedup is NOT bumped, run logs `skipped_fetch_error`. |
| MB-8 | User missing `google_calendar_id` or `google_sheets_id` | User is skipped with `skipped_error`; no false-empty brief is sent. |
| MB-9 | Calendar event at 00:30 Europe/Warsaw | Event appears in that Warsaw date's brief. |
| MB-known-limit | Bot down across the entire 07:00 window | Missed day; PTB `JobQueue` does NOT retrofire missed runs. Acceptable for MVP; POST-MVP: persistent jobstore. If Google is down across the run window, the brief is skipped and logged as `skipped_fetch_error` until a later run succeeds. |

**NOT in MVP (do NOT test / do NOT implement):**

- Pipeline stats, free slots, attendee lists in brief.
- Per-user custom time (`users.morning_brief_hour` is ignored, brief is hardcoded 07:00).
- Per-user timezone (hardcoded Europe/Warsaw).
- Polish declension (client names in nominative, `Akcja: Klient` format).
- Evening follow-up — moved to POST-MVP.
- Pre-meeting reminders — NIEPLANOWANE, handled by native Google Calendar.
