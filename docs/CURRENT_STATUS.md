# OZE-Agent — Current Status
_Last updated: 12.04.2026 — po testach manualnych Sesja A–C (12 testów)_

> **Jak czytać ten plik.** To jest drugi plik który czytasz w nowej sesji (pierwszy: `SOURCE_OF_TRUTH.md`). Tu jest: stan aktualnej sesji, task na następną sesję, historia sesji, lista bugów. Wszystkie decyzje produktowe są w `SOURCE_OF_TRUTH.md` — tu tylko skróty i odniesienia. Jeśli coś się nie zgadza, wygrywa `SOURCE_OF_TRUTH.md`.

---

## Stan faz implementacji (po Sesji A–C + testach 12.04.2026)

```
Phase 1: Sheets — add client                       ✅ INFRASTRUKTURA OK / D.1 PENDING
  R1 3-button card działa (A-T1 ✅). One-click cancel działa (A-T2 ✅).
  Dopisać rebuild działa (A-T3 ✅). R4 merge działa (A-T4 ✅).
  handle_add_client pełna implementacja (D.1) — R4 default-merge, R7 call → następna sesja.

Phase 2: Sheets — search / status / notes           ⚠️ CZĘŚCIOWO
  - 2.1 show_client:       Działa read-only (search). Nie testowane po C.1.
  - 2.2 add_note:          STUB (D.2 następna sesja). Bug-C2-1: stub mówi
                            "w przygotowaniu" — identyczne z POST-MVP banner.
  - 2.3 change_status:     Działa (B-T3/B-T4 ✅). Bug-R7-2: R7 nie odpala
                            po change_status (tylko po add_client teraz).
  - 2.4 duplicates:        R4 2-button działa (A-T4 ✅). Bug-A4-1: classifier
                            czasem zwraca edit_client zamiast poprawnej intencji
                            gdy dane są ambiguous.

Phase 3: Calendar                                    ⚠️ CZĘŚCIOWO
  - 3.1 add_meeting:       Działa. Temporal guard aktywny.
  - 3.3 show_day_plan:     Przepisane na handle_show_day_plan (C.2) — bez
                            free_slots. Nie przetestowane po zmianie.
  - 3.7 R7 fusion:         Bug-C4-1 KRYTYCZNY: R7→add_meeting routing
                            martwy (C-T4 ❌). Kod wygląda poprawnie —
                            prawdopodobnie edge case w _route_pending_flow.

Phase 4: Drive (photos)                              ⏳ TODO
Phase 5: Voice input                                 ⏳ TODO
Phase 6: Proactive messages                          ⏳ TODO
Phase 7: Error handling + lejek POST-MVP banner      ⏳ TODO
```

---

## Zadanie na następną sesję — Sesja D (priorytet bugów + D.1 + D.2)

**Zanim D.1/D.2:** naprawić krytyczne bugi z testów.

### Krok 0 — Sheet-side fix (Maan, nie kod)
Maan musi ręcznie poprawić arkusz Google:
1. Zmienić nazwę kolumny P z `ID kalendarza` na `ID wydarzenia Kalendarz`
2. Usunąć pustą kolumnę bez nagłówka (pozycja 14, między "Źródło pozyskania" a "Zdjęcia")

Następnie wpisać `odśwież kolumny` w bocie żeby odświeżyć cache.

### Krok 1 — bug-C4-1 (KRYTYCZNY): R7→add_meeting routing
Diagnoza: Po C-T3 ✅ wiemy że R7 prompt się wyświetla. Po C-T4 ❌ wiemy że
user odpowiedź z datą/godziną nie trafia do `handle_add_meeting`.
Podejrzewane przyczyny:
- `is_yes` check w `_route_pending_flow` przechwytuje odpowiedź przed `flow_type == "r7_prompt"`
- `_TEMPORAL_MARKERS` nie matchuje frazy której użył tester
- `r7_prompt` flow nie przeżywa `finally: delete_pending_flow` w `handle_confirm`
Fix: dodać logging do `_route_pending_flow` + przetestować z konkretnym inputem. Commit: `fix: bug-C4-1 r7_prompt routing to add_meeting`

### Krok 2 — bug-R7-2: R7 nie odpala po change_status
W `handle_confirm`, gałąź `flow_type == "change_status"` nie woła `send_next_action_prompt`.
Fix: dodać wywołanie R7 po udanym `update_client` w change_status branch.
Commit: `fix: bug-R7-2 R7 after change_status commit`

### Krok D.1 — handle_add_note (było D.2 w planie, ale wyższy priorytet niż D.1)
Stub zastąpić prawdziwym handlerem:
- Identyfikacja klienta: imię + nazwisko + miasto (search_clients)
- Append do kolumny Notatki (z datą prefixem: `[12.04.2026]: treść`)
- R1 3-button card
- R7 po commicie
Commit: `Phase D.1: handle_add_note — MVP implementation`

### Krok D.2 — handle_add_client pełne (było D.1 w planie)
- R4 default-merge gdy klient istnieje i pola się nie kłócą
- R4 2-button disambiguation (`build_duplicate_buttons`) gdy konflikt
- R7 już podpięty w C.4 — weryfikacja
Commit: `Phase D.2: handle_add_client — R4 default-merge aligned`

---

## Znane bugi (stan 12.04.2026 po testach)

### Krytyczne (blokują MVP)

| ID | Objaw | Lokalizacja | Priorytet |
|----|-------|-------------|-----------|
| bug-C4-1 | R7 free-text parser martwy — user odpowiedź z datą nie trafia do add_meeting | `_route_pending_flow`, linia ~302 | KRYTYCZNY |
| bug-C2-1 | add_note zwraca "w przygotowaniu" — stub identyczny z POST-MVP banner, jest MVP intent | `handle_add_note` stub (C.1) | KRYTYCZNY — planowany D.1 |

### Wysokie (psują UX)

| ID | Objaw | Lokalizacja | Priorytet |
|----|-------|-------------|-----------|
| bug-R7-2 | R7 nie odpala po change_status (tylko po add_client) | `handle_confirm` change_status branch | HIGH |
| bug-A1-1 | "ID kalendarza" w arkuszu vs "ID wydarzenia Kalendarz" w kodzie → pojawia się w "Brakuje:" | Sheet-side fix (Maan) | HIGH |
| bug-B1-1 | Pusta kolumna bez nazwy na pozycji 14 → 17 col zamiast 16 | Sheet-side fix (Maan) | HIGH |
| bug-B2-1 | Klimatyzacja nadal się pojawia jako produkt | Prawdopodobnie deployment lag (kod czysty, grep=0) | HIGH — zweryfikować po redeploy |

### Niskie / kosmetyczne

| ID | Objaw | Lokalizacja | Priorytet |
|----|-------|-------------|-----------|
| bug-A4-1 | Classifier false-positive edit_client na ambiguous inputs → R5 banner zamiast właściwej akcji | `classify_intent` system prompt | MEDIUM |
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
