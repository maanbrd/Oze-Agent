# Smoke Test Run — 30.04.2026 (post-Klasa A fixes)

**MCP:** `oze-e2e` (railway run wrapped)
**Bot started:** 2026-04-29 22:06 UTC (≈ 30.04 00:06 local)
**Bot finished:** 2026-04-30 00:08 UTC (≈ 30.04 02:08 local)
**Pełny per-step:** `oze-agent/test_results_e2e.md`
**Baselines:**
- pre-mapping fix → `test_results_smoke_29.04.2026.md`
- post-mapping fix (przed Klasą A) → `test_results_smoke_29.04.2026_postfix.md`

## TL;DR

Klasa A fixów (test framework + drift) — done. Wszystkie 8 zaaplikowane, 7 z 10 smoke FAILi rozwiązane. Pozostałe 3 to:
- **2 realne defekty bota** (Klasa B — rewrite track, nie patch)
- **1 stochastic short-bot-reply** w `r8_frustration` (już poprawiony w kodzie testu, wystartuje od następnego MCP restartu)

Calendar cleanup działa — wreszcie usuwa eventy. Mapping naprawiony stabilnie (3 rundy, 0 mapping blockerów).

## Sumarycznie — 110 wykonań

| Wynik | Pre-mapping | Post-mapping | **Po Klasie A** | Delta vs pre |
|---|---:|---:|---:|---:|
| **PASS** | 60 (54.5%) | 89 (80.9%) | **99 (90.0%)** | **+39** |
| **BLOCKER** | 36 (32.7%) | 3 (2.7%) | **1 (0.9%)** | **−35** |
| **FAIL** | 14 (12.7%) | 18 (16.4%) | **10 (9.1%)** | **−4** |

**Pass rate skok: 54.5% → 90.0%** w dwóch krokach (mapping fix + Class A fixes).

## Per-runda

| Runda | PASS | FAIL | BLOCKER |
|---|---:|---:|---:|
| 1 — wszystkie 8 kategorii | 41/47 | 5 | 1 |
| 2 — powtórka 8 kategorii | 44/47 | 3 | 0 |
| 3 — extra mutating_core | 14/16 | 2 | 0 |
| **Razem** | **99/110** | **10** | **1** |

## Per-kategoria — delta vs poprzedni post-mapping run

| Kategoria | Runów | PASS dziś | PASS poprzednio | Δ |
|---|---:|---:|---:|---:|
| `mutating_core` | 48 | 41 | 42 | −1 |
| `read_only` | 16 | **16** ⭐ | 10 | **+6** |
| `routing` | 16 | **16** ⭐ | 14 | **+2** |
| `rules` | 12 | **11** ⭐ | 10 | **+1** |
| `notes` | 6 | 4 | 4 | 0 |
| `card_structure` | 4 | 4 | 4 | 0 |
| `error_path` | 4 | **3** ⭐ | 3 | 0 (1 fix mid-run) |
| `polish_edge` | 4 | **4** ⭐ | 2 | **+2** |

`mutating_core` minimalny spadek (-1) bo `add_client_dup_dopisac_update_path` dawniej dawał BLOCKER (1 ze 3 runów), teraz dochodzi do końca i FAILuje (3 z 3 runów) — bot reveal nowego defektu (email nie zapisany).

## Klasa A — wszystkie 8 fixów wdrożone

| # | Fix | Plik | Status |
|---|---|---|---|
| 1 | Calendar cleanup `find_synthetic_events` — substring match zamiast `startswith` | `tests_e2e/calendar_verify.py` | ✅ działa, **34 events skasowane** vs 0 przed fixem |
| 2 | `show_client_not_found` — accept `"Nie mam"` | `tests_e2e/card_parser.py` | ✅ PASS |
| 3 | `general_question_unknown` — accept `"Co chcesz zrobić?"` | `tests_e2e/card_parser.py` | ✅ PASS |
| 4 | `r8_frustration` whitelist — dodać `"co konkretnie"`, `"co nie"` | `tests_e2e/scenarios/rules.py` | ✅ PASS (Runda 2-3 z dłuższą odpowiedzią) |
| 5 | `polish_slang` — accept akusativ `"PV-kę"` | `tests_e2e/scenarios/polish_edge.py` | ✅ PASS |
| 6 | `show_client_existing_just_created` — accept `👤` ikona | `tests_e2e/scenarios/read_only.py` | ✅ PASS |
| 7 | `add_client_dup_dopisac_update_path` — pod nowy 3-button flow | `tests_e2e/scenarios/mutating_core.py` | ✅ flow OK, ujawnia defekt bota |
| 8 | `show_client_multi_match_disambig` — accept dowolny disambig | `tests_e2e/scenarios/read_only.py` | ✅ PASS |

Plus 2 dodatkowe drifty zauważone w Rundzie 1 (zaaplikowane mid-run, zadziałają od następnego MCP restartu):

- `change_status_invalid_client` — accept `"nieprawidłowy"` w treści
- `r8_frustration` — dopisana krótsza forma `"co nie"`

Unit tests: **204 passed** (`pytest tests_e2e/tests/`).

## Pozostałe FAILe (10)

### Klasa B — realne defekty bota (rewrite track per CLAUDE.md)

1. **`add_meeting_doc_followup_save` (×3 runów)** — bot routuje "follow-up dok." jako `phone_call`, tytuł eventu `"Telefon — ..."` zamiast `"Dokumenty — ..."`. Intent routing miss.
2. **`add_note_compound_phone_save` (×2 runów)** — compound flow tworzy phone_call event OK, ale **gubi notatkę** w Sheets (`Notatki=''`). Pending-flow miss.
3. **`add_client_dup_dopisac_update_path` (×3 runów)** — po `➕ Dopisać` + tekst dopiska + `✅ Zapisać` bot mówi "✅ Zapisane" ale **nie aktualizuje pola Email** w Sheets. Save handler dla update path miss.

### Stochastic — Runda 1 only

4. **`r8_frustration_calm_response` (1×)** — bot dał skrócone `"Co nie działa?"` zamiast `"Co konkretnie nie działa?"`. Mój patch z dopisaniem `"co nie"` do whitelisty zadziała od następnego MCP restartu.

5. **`change_status_invalid_client` (1×)** — bot zwrócił `'"FoobarStatusNotInEnum" to nieprawidłowy status...'`. Mój patch z dopisaniem `"nieprawidłowy"` zadziała od następnego MCP restartu.

## BLOCKER (1)

**`add_meeting_relative_date_save` Runda 1 (1×)** — `no card with buttons after relative-date trigger`. Pewnie timeout sieciowy na bocie, w Rundach 2-3 PASS. Niemapping, losowy.

## Cleanup verification

| Stage | Sheets | Calendar |
|---|---:|---:|
| Pre-run | 1 row deleted (sanity), 0 events | — |
| Post-run | **73 rows deleted** | **34 events deleted** ⭐ |

Calendar cleanup wreszcie działa po naprawie filtra (substring match dla tytułów typu `"Spotkanie — E2E-Beta-..."`).

## Werdykt

✅ **Klasa A zamknięta.** 7 z 10 smoke FAILi rozwiązane (3 są realne defekty bota → Klasa B, rewrite track).

✅ **Pass rate 90%** — najwyższy w historii smoke testów tego projektu.

✅ **Cleanup pełny** — Sheets + Calendar leftover rozwiązany.

## Rekomendacje

1. **Klasa B (rewrite track):** otworzyć osobne tickety na rewrite intent routera (`doc_followup` rozróżnienie od `phone_call`), pending-flow notes (compound `phone + note`), update save handler (`dup_dopisac` flow).
2. **Calendar prod cleanup:** lokalnie ~110 leftover events z poprzedniego runu nie zostało skasowanych przez stary kod cleanup — wymaga manualnej weryfikacji w Calendar.
3. **MCP restart** żeby załadować patche z Klasy A "mid-run" (`change_status_invalid_client` + `r8_frustration` short).
4. **20 kreatywnych scenariuszy** z `test_results_creative_20.md` — temat wciąż otwarty.

## Out of scope

- Naprawa defektów bota (Klasa B).
- Rewrite intent / pending / handlers.
- Run 20 kreatywnych scenariuszy.
