# OZE-Agent — Current Status
_Last updated: 12.04.2026 — Sesja D zaimplementowana (4 commity: C4-1, R7-2, D.1, D.2)_

> **Jak czytać ten plik.** To jest drugi plik który czytasz w nowej sesji (pierwszy: `SOURCE_OF_TRUTH.md`). Tu jest: stan aktualnej sesji, task na następną sesję, historia sesji, lista bugów. Wszystkie decyzje produktowe są w `SOURCE_OF_TRUTH.md` — tu tylko skróty i odniesienia. Jeśli coś się nie zgadza, wygrywa `SOURCE_OF_TRUTH.md`.

---

## Stan faz implementacji (po Sesji D — 12.04.2026)

```
Phase 1: Sheets — add client                       ✅ GOTOWE
  R1 3-button card (A-T1 ✅). One-click cancel (A-T2 ✅).
  Dopisać rebuild (A-T3 ✅). R4 default-merge no-conflict (D.2 ✅).
  R4 2-button conflict flow (A-T4 ✅). R7 po add_client (✅).

Phase 2: Sheets — search / status / notes           ✅ GOTOWE (MVP)
  - 2.1 show_client:       Działa read-only. Nie retestowane po D.
  - 2.2 add_note:          ✅ ZAIMPLEMENTOWANE (D.1). extract_note_data +
                            R1 karta + append do Notatki + Data ostatniego
                            kontaktu update. Bez R7 (zamknięty akt).
  - 2.3 change_status:     ✅ Działa + R7 po commit (D.2 fix bug-R7-2).
  - 2.4 duplicates:        R4 default-merge (D.2). R4 2-button conflict (A-T4 ✅).

Phase 3: Calendar                                    ⚠️ CZĘŚCIOWO
  - 3.1 add_meeting:       Działa. Temporal guard aktywny.
  - 3.3 show_day_plan:     Przepisane na handle_show_day_plan (C.2) — bez
                            free_slots. Nie przetestowane po zmianie.
  - 3.7 R7 fusion:         ✅ FIX (D krok 1, bug-C4-1): cancel_words
                            word-boundary — "poniedziałek"/"niedzielę"
                            nie powodują false-cancel. Do retestowania.

Phase 4: Drive (photos)                              ⏳ TODO
Phase 5: Voice input                                 ⏳ TODO
Phase 6: Proactive messages                          ⏳ TODO
Phase 7: Error handling + lejek POST-MVP banner      ⏳ TODO
```

---

## Sesja D — ZAKOŃCZONA (12.04.2026)

Commity: `7359848` (C4-1), `71b3c05` (R7-2), `86f1185` (D.1), `04721da` (D.2).

### Krok 0 — Sheet-side fix (Maan, nie kod — PENDING)
Maan musi ręcznie poprawić arkusz Google:
1. Zmienić nazwę kolumny P z `ID kalendarza` na `ID wydarzenia Kalendarz`
2. Usunąć pustą kolumnę bez nagłówka (pozycja 14, między "Źródło pozyskania" a "Zdjęcia")

Następnie wpisać `odśwież kolumny` w bocie żeby odświeżyć cache.

## Zadanie na Sesję E — testy manualne Sesji D

**Retest po Sesji D (Claude Cowork):**

| Test | Co sprawdzić |
|------|-------------|
| D-T1 (C4-1 fix) | R7 prompt → "W poniedziałek o 10:00" → add_meeting flow (nie zamknąć) |
| D-T2 (C4-1 fix) | R7 prompt → "W niedzielę o 14" → add_meeting flow |
| D-T3 (C4-1 fix) | R7 prompt → "nie wiem" → zamknięty cicho ✅ |
| D-T4 (R7-2 fix) | change_status commit → R7 prompt pojawia się po ✅ |
| D-T5 (D.1) | "dodaj notatkę do Jan Kowalski Warszawa: dzwonił w sprawie gwarancji" → karta 📝 + 3 przyciski |
| D-T6 (D.1) | Zapisać notatkę → sprawdź Sheets: Notatki ma `[12.04.2026]: dzwonił...` |
| D-T7 (D.1) | Sprawdź że R7 NIE pojawia się po dodaniu notatki |
| D-T8 (D.2) | Dodaj klienta który istnieje, brak konfliktu → karta "Zaktualizować X o: [pole]?" + 3 przyciski |
| D-T9 (D.2) | Dodaj klienta który istnieje, z konfliktem (inny telefon) → "Masz już X" + 2 przyciski |

---

## Znane bugi (stan 12.04.2026 po testach)

### Krytyczne (blokują MVP)

| ID | Objaw | Lokalizacja | Priorytet |
|----|-------|-------------|-----------|
| bug-C4-1 | ✅ NAPRAWIONE (D krok 1) — cancel_words word-boundary | `_route_pending_flow` | — |
| bug-C2-1 | ✅ NAPRAWIONE (D.1) — handle_add_note MVP | `handle_add_note` | — |

### Wysokie (psują UX)

| ID | Objaw | Lokalizacja | Priorytet |
|----|-------|-------------|-----------|
| bug-R7-2 | ✅ NAPRAWIONE (D krok 2) — client_name/city w flow_data + send_next_action_prompt | `handle_confirm` | — |
| bug-A1-1 | "ID kalendarza" w arkuszu vs "ID wydarzenia Kalendarz" w kodzie → pojawia się w "Brakuje:" | Sheet-side fix (Maan) | HIGH |
| bug-B1-1 | Pusta kolumna bez nazwy na pozycji 14 → 17 col zamiast 16 | Sheet-side fix (Maan) | HIGH |
| bug-B2-1 | Klimatyzacja nadal się pojawia jako produkt | Prawdopodobnie deployment lag (kod czysty, grep=0) | HIGH — zweryfikować po redeploy |

### Niskie / kosmetyczne

| ID | Objaw | Lokalizacja | Priorytet |
|----|-------|-------------|-----------|
| bug-A4-1 | Classifier false-positive edit_client na ambiguous inputs → R5 banner zamiast właściwej akcji | `classify_intent` system prompt | MEDIUM |
| bug-A4-2 | R7 nie pali po merge-path (A-T4 R4 "Dopisz do istniejącego") — do ustalenia z Maanem czy spec wymaga R7 po merge | `_handle_duplicate_merge` w `buttons.py` | LOW (do spec-clarification) |
| bug-B3-1 | `[➕ Dopisać]` na karcie change_status jest niejasne — może tylko 2 przyciski [Zapisać][Anulować]? | `handle_change_status` card buttons | LOW (question, do ustalenia z Maanem) |
| bug-A1-4 | "Co dalej z Jan Nowak" zamiast "Co dalej z Janem Nowakiem" — brak narzędnika w R7 | `send_next_action_prompt` (format stringa) | LOW |
| Bug #8 | Multi-meeting parser gubi imię gdy odmienione formy | `extract_meeting_data` | MEDIUM |
| Bug #10 | "Spotkanie z Jan Mazur" bez odmiany | `_enrich_meeting` | LOW |

### Zamknięte przez Sesje A–C

| ID | Fix | Commit |
|----|-----|--------|
| Old `[Tak][Nie]` / `[Zapisz bez]` | Zastąpione `build_mutation_buttons` | C.3 `2b76bd2` |
| 2-step cancel ("Na pewno?") | One-click cancel w `handle_cancel_flow` | C.3 `2b76bd2` |
| `[Nowy][Aktualizuj]` w duplikatach | `build_duplicate_buttons` + merge/new handlers | C.3 + A.2 `2b76bd2` |
| auto-routing phone→add_client (Bug #7) | Usunięty `_contains_phone` + `zapisz` keyword | C.2 `2358140` |
| `save_immediately` bypass R1 | Usunięty `save_immediately` param | C.2 `2358140` |
| Retired intenty w routerze | Router 6 MVP + R5 banner stubs | C.1 `b4fcb0e` |
| `Klimatyzacja` w AI promptach | B.2 `e9c3698` |
| `Negocjacje` w pipeline default | B.4 `8c6a78a` |
| DEFAULT_COLUMNS 21→16 | B.3 `501a9a8` |
| SYSTEM_FIELDS cleanup | B.5 `a2ae15b` |
| `_MEASUREMENT_FIELDS` + followup drift | B.6 `155a8f9` |

---

## Wyniki testów Sesja A–C (12.04.2026)

| Test | Wynik | Notatka |
|------|-------|---------|
| A-T1 (3-btn card) | ✅ PASS | |
| A-T2 (one-click cancel) | ✅ PASS | |
| A-T3 (Dopisać rebuild) | ✅ PASS | |
| A-T4 (R4 duplikat + merge) | ✅ PASS | + bug-A4-1 (classifier edge case) |
| B-T1 (16-col schema) | ⚠️ DRIFT | bug-A1-1 + bug-B1-1 → sheet-side fix |
| B-T2 (Klimatyzacja) | ❌ FAIL | bug-B2-1 — kod czysty, prawdopodobnie deployment |
| B-T3 (Podpisane) | ✅ PASS | + bug-R7-2 (R7 nie po change_status) |
| B-T4 (Rezygnacja) | ✅ PASS | + bug-R7-2 (ten sam) |
| C-T1 (R5 banner) | ✅ PASS | |
| C-T2 (add_note) | ❌ FAIL | bug-C2-1 — stub, planowane D.1 |
| C-T3 (R7 prompt) | ✅ PASS | + bug-A1-4 (brak narzędnika) |
| C-T4 (R7 fusion) | ❌ FAIL | bug-C4-1 KRYTYCZNY — R7→meeting routing |

**Wynik: 7/12 ✅, 2/12 ⚠️, 3/12 ❌**

Spośród 3 FAIL:
- C-T2: **oczekiwany** (stub planowany na D.1) — nie liczymy jako regression
- B-T2: deployment/cache (kod czysty) — nie liczymy jako regression
- C-T4: **prawdziwy bug** do naprawienia przed D

---

## Historia sesji

### 10.04.2026 wieczór — Round 7 + Round 8 testy manualne + decyzje produktowe
Po testach manualnych w Telegramie Maan podjął decyzje (autorytatywna wersja w `SOURCE_OF_TRUTH.md` sekcja 4):
1. Specyfikacje techniczne (metraż, kierunek dachu, kWh, napięcie, typ dachu) → kolumna `Notatki`, nie osobne kolumny.
2. Moc produktu (kW/kWh) → do `Notatki`. Kolumna `Produkt` zawiera tylko typ bez liczb.
3. R4 (obowiązkowe pytanie o następny kontakt) — USUNIĘTE. Agent nie pyta sam z siebie.
4. `OZE_Agent_Brief_v5_FINAL.md` → `docs/archive/`.

Commity: 8531d8a, 82f92ab, 08699a6, 39485b6, 9fa41ec, bc765a2.

### 11.04.2026 rano — synchronizacja SOURCE_OF_TRUTH.md + INTENCJE_MVP.md
Zamrożenie kontraktów intencji MVP: 6 MVP + 3 POST-MVP + 4 NIEPLANOWANE. Pipeline 9 statusów. Produkty 4. Schemat 16 kolumn A-P.

### 11.04.2026 popołudnie — synchronizacja agent_behavior_spec_v5.md + agent_system_prompt.md + CLAUDE.md
R1 3-button + one-click cancel. R7 free-text. R3 cztery trasy. R4 default-merge + 2-button. Compound fusion MVP.

### 11.04.2026 — Sesja B (statyczne fixy danych i promptów)
6 commitów (B.1–B.6): VALID_INTENTS cleanup, Klimatyzacja/Negocjacje removal, DEFAULT_COLUMNS 16-col, supabase pipeline 9-status, SYSTEM_FIELDS cleanup, formatting cleanup.
Commity: 40a69f0, e9c3698, 501a9a8, 8c6a78a, a2ae15b, 155a8f9.

### 12.04.2026 — Sesja C (router + confirm flow) + A.2 (buttons)
4 commity (C.1–C.4 + A.2):
- C.1 `b4fcb0e`: Router 6 MVP + R5 banner stubs + handle_add_note stub + handle_post_mvp_banner
- C.2 `2358140`: Dead handlers removed, handle_show_day_plan, auto-routing Bug #7 fixed
- C.3+A.2 `2b76bd2`: build_mutation_buttons, one-click cancel, buttons.py save/append/cancel/merge/new
- C.4 `6834b99`: send_next_action_prompt, r7_prompt flow w _route_pending_flow

Testy: 7/12 PASS, 3/12 krytyczne (C-T4 prawdziwy bug, B-T2 deployment, C-T2 oczekiwany stub).

### 12.04.2026 — Sesja D (bug fixes + handle_add_note + default-merge)
4 commity:
- `7359848`: fix bug-C4-1 — cancel_words word-boundary (nie/poniedziałek false-match)
- `71b3c05`: fix bug-R7-2 — R7 after change_status commit (client_name/city + send_next_action_prompt)
- `86f1185`: Phase D.1 — handle_add_note MVP (extract_note_data, R1 karta, append Notatki, bez R7)
- `04721da`: Phase D.2 — handle_add_client R4 default-merge (conflict-check, no-conflict → R1 karta merge)

---

## Co działa dobrze (potwierdzone testami 12.04.2026)

- 3-button confirmation card (R1)
- One-click cancel (R1)
- Dopisać flow — rebuild karty z doklejonymi danymi (R1 append)
- R4 duplicate 2-button + merge handler
- R5 POST-MVP banner (edit_client, filtruj, lejek)
- change_status — Podpisane, Rezygnacja z umowy
- R7 next_action_prompt po add_client commit
- Wyszukiwanie — fuzzy match, diakrytyki, odmiana
- Format daty DD.MM.YYYY (Dzień tygodnia)

---

## Jak działamy

- **Claude Code** — implementuje i naprawia kod
- **Claude Cowork** — testuje manualnie w Telegram, generuje raporty
- **Maan** — decyduje o priorytetach, przekazuje wyniki między sesjami

**Na początku każdej sesji:** czytaj `SOURCE_OF_TRUTH.md` → `CURRENT_STATUS.md` → wedle potrzeby INTENCJE_MVP.md / agent_behavior_spec_v5.md / agent_system_prompt.md.

**Na końcu każdej sesji:** zaktualizuj ten plik.
