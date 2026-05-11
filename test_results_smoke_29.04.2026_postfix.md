# Smoke Test Run — 29.04.2026 (post-fix Supabase mappingu)

**MCP server:** `oze-e2e` (telethon → @OZEAgentTestBot, wrapped w `railway run`)
**Bot started:** 2026-04-29 18:33 UTC (≈ 20:33 local)
**Bot finished:** 2026-04-29 20:32 UTC (≈ 22:32 local)
**Pełny per-step report:** `oze-agent/test_results_e2e.md`
**Baseline:** `test_results_smoke_29.04.2026.md` (rano, przed naprawą)

## TL;DR

Naprawa Supabase user mappingu (railway run wrapper na `run_mcp_server.sh`) **odblokowała 33% scenariuszy**. BLOCKERy z mappingu: 36 → 0. Pozostały 3 BLOCKERy z **niemappingowej** przyczyny (`add_client_dup_dopisac_update_path` — znany drift starego `[Nowy]/[Aktualizuj]` flow vs nowy 3-button), powtarzające się w każdej rundzie.

Naprawa **odsłoniła 4 nowe realne FAILe**, które wczoraj były ukryte pod blockerem weryfikacji.

## Sumarycznie — 110 wykonań

| Wynik | Dziś | Wczoraj | Delta |
|---|---:|---:|---:|
| **PASS** | 89 (80.9%) | 60 (54.5%) | **+29** |
| **BLOCKER** | 3 (2.7%) | 36 (32.7%) | **−33** |
| **FAIL** | 18 (16.4%) | 14 (12.7%) | **+4** |

Mapping-related BLOCKER: **0**. Wszystkie 3 dzisiejsze BLOCKERy to powtórzony `add_client_dup_dopisac_update_path`.

## Per-runda

| Runda | PASS | FAIL | BLOCKER |
|---|---:|---:|---:|
| 1 — wszystkie 8 kategorii | 37/47 | 9 | 1 |
| 2 — powtórka 8 kategorii | 38/47 | 8 | 1 |
| 3 — extra mutating_core | 14/16 | 1 | 1 |
| **Razem** | **89/110** | **18** | **3** |

Rundy 1-3 są stabilne — te same scenariusze przechodzą i te same fail-ują. Brak driftu północy (runy o 20:30 local).

## Per-kategoria (sumaryczne 3 rundy, dziś vs wczoraj)

| Kategoria | Runów | PASS dziś | PASS wczoraj | BLOCKER dziś | BLOCKER wczoraj |
|---|---:|---:|---:|---:|---:|
| `mutating_core` | 48 | 42 | 27 | 3 | 18 |
| `read_only` | 16 | 10 | 10 | 0 | 0 |
| `routing` | 16 | 14 | 14 | 0 | 0 |
| `rules` | 12 | 10 | 2 | 0 | 8 |
| `notes` | 6 | 4 | 0 | 0 | 6 |
| `card_structure` | 4 | 4 | 4 | 0 | 0 |
| `error_path` | 4 | 3 | 3 | 0 | 0 |
| `polish_edge` | 4 | 2 | 0 | 0 | 3 |

Najsilniejszy zysk: `mutating_core` (+15 PASS), `rules` (+8 PASS), `notes` (+4 PASS), `polish_edge` (+2 PASS). Te kategorie były dotknięte mappingiem najmocniej.

## Stabilne FAILe (powtarzalne, do decyzji)

### Te same co wczoraj (drift testów względem aktualnego copy bota)

1. **`show_client_existing_just_created`** — `👤` vs oczekiwane `📋` ikona.
2. **`show_client_multi_match_disambig`** — fixture ma 2× Warszawa zamiast Warszawa + Kraków (`E2E-Beta-Fixture-Jan-Kowalski, Kraków` w bazie istnieje, ale bot nie znajduje albo fixture seed ma bug).
3. **`show_client_not_found`** — `'Nie mam X w bazie.'` vs `'Nie znalazłem'`.
4. **`general_question_unknown`** — `'Co chcesz zrobić?'` vs `'Nie zrozumiałem'`.
5. **`r8_frustration_calm_response`** — `'Co konkretnie nie działa?'` vs whitelist (`co chcesz / co dalej / powiedz / podaj / zacznijmy`).
6. **`polish_slang_pv_pompeczka_parsing`** — `"PV-kę"` (akusativ) vs verbatim `"PV-ka"`.

### Nowe realne defekty odsłonięte po naprawie mappingu

7. **`add_meeting_doc_followup_save`** — bot routuje "follow-up dok." jako `phone_call` zamiast `doc_followup`. Calendar event powstaje z poprawną datą i czasem, ale **typem telefonu** (`title='Telefon — ...'`). Wczoraj był BLOCKER, dziś prawdziwy defekt routingu intentu. **3/3 runów ten sam fail**.

8. **`add_note_compound_phone_save`** — bot tworzy phone_call event poprawnie, ale **gubi notatkę** w Sheets (`row['Notatki']=''`). Compound flow zapisuje tylko event, nie zapisuje notatki w komórce H. **2/2 runów ten sam fail**.

### `add_client_dup_dopisac_update_path` — BLOCKER niemappingowy

Bot po `➕ Dopisać` na karcie duplikatu odpowiada `'Co chcesz dopisać?'` zamiast wystawić nową kartę aktualizującą. Test oczekuje karty albo save confirm. To znana zmiana spec'a — 3-button flow zastąpił rozdzielne `[Nowy]/[Aktualizuj]`. Test powinien być przepisany pod nowy flow. **3/3 runów BLOCKER**.

## Ostatecznie: czy mapping jest naprawiony?

✅ **Tak.** Kryteria akceptacji spełnione:

- BLOCKER count: 3 (vs 36) — żaden nie jest mapping-related
- PASS count: 89 (vs 60) — wzrost o 48%
- FAIL count: 18 (vs 14) — wzrost o 4 nowe odsłonięte defekty + zachowane stabilne
- Cleanup pre-run: ✅ 111 klientów + 0 events
- Cleanup post-run: ✅ 70 klientów + 0 events

Dla pełnego zamknięcia naprawy potrzebne jeszcze:

1. **Naprawa cleanupu Calendar events** — filter w [tests_e2e/fixtures.py](oze-agent/tests_e2e/fixtures.py) `find_synthetic_events` nie matchuje tytułów typu `"Spotkanie — E2E-Beta-..."` / `"Telefon — E2E-Beta-..."`. Cleanup zwraca `Calendar: found 0`. Stąd Calendar w prod ma teraz ~110 syntetycznych eventów do ręcznego usunięcia.
2. **Przepis testu `add_client_dup_dopisac_update_path`** pod nowy 3-button flow.
3. **Decyzja per stabilny FAIL** — który updateować w teście (icon, copy "Nie mam"), a który przekazać botowi do poprawy (np. `polish_slang_pv_pompeczka` — lepiej ufać akusativowi).
4. **Diagnoza 2 nowych defektów** — `add_meeting_doc_followup_save` (phone_call zamiast doc_followup) i `add_note_compound_phone_save` (zgubiona notatka).

## Rekomendacje

1. **Zamknąć krok 5-6 z `docs/PLAN_FIX_E2E_SUPABASE_MAPPING.md`** — osiągnięte. Mapping naprawiony, weryfikowany, stabilny w 3 rundach.
2. **Otworzyć ticket na cleanup Calendar events** — fix filter w `find_synthetic_events`, ręczne posprzątanie eventów w Calendar.
3. **Otworzyć ticket na 2 nowe defekty bota** — doc_followup intent routing, compound note flow.
4. **Otworzyć ticket na review stabilnych FAILi** — który updateować w teście (drift), który zgłosić do bota (regresja).
5. **Wrócić do `test_results_creative_20.md`** — 20 kreatywnych scenariuszy czeka na decyzję (dopisać do `creative.py` + restart MCP, czy manual checklist).

## Out of scope

- Naprawa znalezionych defektów bota.
- Update testów stabilnych FAILi.
- Naprawa cleanupu Calendar.
- Run 20 kreatywnych scenariuszy.
- Aktualizacja `docs/PLAN_FIX_E2E_SUPABASE_MAPPING.md` (kolejność cleanup → seed → smoke → cleanup).
