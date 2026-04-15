# OZE-Agent — Test Plan

_Last updated: 14.04.2026_

This is the test plan for the new behavior layer (selective rewrite). Not for the old patch-track.

Tests are manual Telegram tests unless stated otherwise.

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

## Proactive / Morning Brief

| # | Scenario | Expected |
|---|----------|----------|
| MB-1 | Morning brief at configured time | Meetings for today (client + address) + free slots + overdue follow-ups. **No pipeline stats** |
| MB-2 | No meetings today | "Na dziś nic nie masz w kalendarzu." |

---

## Proactive / Evening Follow-up

| # | Scenario | Expected |
|---|----------|----------|
| EF-1 | After last meeting of the day | Agent asks about unreported meetings with a list of names |
| EF-2 | Pre-meeting reminders | Agent does NOT send own pre-meeting reminders (handled by native Google Calendar) |
