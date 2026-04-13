# OZE-Agent — Current Status
_Last updated: 13.04.2026 — Sesja Q: show_day_plan format rewrite (compact per §4.6). Do testowania._

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
  - 3.1 add_meeting:       ✅ Działa. Temporal guard, multi-meeting, enrichment.
  - 3.3 show_day_plan:     Format przepisany na compact (§4.6). Do testowania.
  - 3.7 R7 fusion:         ✅ FIX (D krok 1, bug-C4-1).

Phase 4: Drive (photos)                              ⏳ TODO
Phase 5: Voice input                                 ⏳ TODO
Phase 6: Proactive messages                          ⏳ TODO
Phase 7: Error handling + lejek POST-MVP banner      ⏳ TODO
```

---

## Stan bugów po Sesji P (13.04.2026)

**Wszystkie code-fixable bugi naprawione i potwierdzone testami.**

### Otwarte (wymagają ręcznej akcji Maana)

| ID | Co trzeba zrobić | Priorytet |
|----|-----------------|-----------|
| bug-A1-1 | Zmień nazwę kolumny P w arkuszu: "ID kalendarza" → "ID wydarzenia Kalendarz". Potem wpisz `odśwież kolumny` w bocie | HIGH |
| bug-B1-1 | Usuń pustą kolumnę bez nagłówka na pozycji 14 (między "Źródło pozyskania" a "Zdjęcia"). Potem `odśwież kolumny` | HIGH |
| bug-B3-1 | ✅ NAPRAWIONE — change_status ma teraz 2 przyciski [Zapisać][Anulować] (bez Dopisać) | — |

### Naprawione (pełna lista — 27 bugów)

| ID | Sesja naprawy | Potwierdzenie |
|----|--------------|---------------|
| bug-E1-3 | Sesja G | E-tests ✅ |
| bug-E1-9 | Sesja I | I-T2 ✅ |
| bug-E2-1 | Sesja G | G-tests ✅ |
| bug-E2-5 | Sesja G | G-tests ✅ |
| bug-E2-7 | Sesja H+J | J-T3, J-T4 ✅ |
| bug-E3-3 | Sesja G | G-tests ✅ |
| bug-E4-7 | Sesja I | I-T3 ✅ |
| bug-E5-1 | Sesja G | G-tests ✅ |
| bug-E6-1/E10-2/E10-7 | Sesja F+P | P-T2,3,5,6,7 ✅ |
| bug-E9-6 | Sesja K+L | K-T4, L-T1 ✅ |
| bug-E9-9 | Sesja G | G-tests ✅ |
| bug-E10-4 | Sesja G | G-tests ✅ |
| bug-E14-7 | Sesja I | I-T5 ✅ |
| bug-E19-9 | Sesja I | I-T1 ✅ |
| bug-E23-9 | Sesja H | H-T4 ✅ |
| bug-F2-2 | Sesja I | I-T1, I-T4 ✅ |
| bug-F3-1 | Sesja H | H-T1 ✅ |
| bug-B2-1 | Sesja J+K | J-tests ✅ |
| bug-C2-1 | Sesja D | D-tests ✅ |
| bug-C4-1 | Sesja D | D-tests ✅ |
| bug-R7-2 | Sesja D | D-tests ✅ |
| bug-A1-4 | Sesja M | M-T1, M-T3 ✅ |
| bug-A4-1 | Sesja O | O-T1–O-T3 ✅ |
| bug-A4-2 | Sesja N | N-T2 ✅ |
| Bug #8 | Sesja O | O-T4 ✅ |
| Bug #10 | Sesja M | M-T2 ✅ |
| bug-P8-1 | Sesja P | P2-T2 ✅ |

### Reklasyfikowane (nie bug)

| ID | Powód |
|----|-------|
| bug-P4-1 | add_meeting tworzy Calendar event — nie wymaga klienta w bazie. Handlowiec może mieć spotkanie z nowym leadem nie dodanym do CRM |

---

## Sesja D — ZAKOŃCZONA (12.04.2026)

Commity: `7359848` (C4-1), `71b3c05` (R7-2), `86f1185` (D.1), `04721da` (D.2).

### Krok 0 — Sheet-side fix (Maan, nie kod — PENDING)
Maan musi ręcznie poprawić arkusz Google:
1. Zmienić nazwę kolumny P z `ID kalendarza` na `ID wydarzenia Kalendarz`
2. Usunąć pustą kolumnę bez nagłówka (pozycja 14, między "Źródło pozyskania" a "Zdjęcia")

Następnie wpisać `odśwież kolumny` w bocie żeby odświeżyć cache.

## Sesja G — ZAKOŃCZONA (12.04.2026)

Commit: `efcdf1d` — 7 bugów naprawionych jednym commitem.

### Zmiany

| Plik | Co zmieniono |
|------|-------------|
| `buttons.py` | `_handle_select_client` sprawdza pending `disambiguation` flow, kontynuuje change_status/add_note mutation card zamiast read-only. Dodano importy `build_mutation_buttons`, `build_choice_buttons`, `format_edit_comparison`, `escape_markdown_v2` |
| `text.py` | `handle_change_status` i `handle_add_note` disambiguation branches zapisują `save_pending_flow("disambiguation", ...)` przed pokazaniem buttonsów. `_VALID_STATUSES` stała z 9 statusami. Whitelist walidacja w `handle_change_status`. Pre-check "statusy" keyword. `_parse_show_day_date` helper (nazwy dni, explicite daty, DD.MM). Temporal guard w `handle_add_meeting`. |
| `formatting.py` | Usunięty "Odpowiedz tak/nie" z `format_confirmation`. `_fmt_date` obsługuje datetime strings z czasem ("2026-04-14 14:00"). |

### Testy do wykonania (Claude Cowork po deploy Railway)

| # | Wiadomość | Oczekiwany wynik |
|---|-----------|-----------------|
| G-T1 | "zmień status Kowalski na Spotkanie umówione" → disambiguation → kliknij "Jan Kowalski Warszawa" | **Mutation card**: "Zmienić status Jan Kowalski? Status: → Spotkanie umówione" + 3 przyciski |
| G-T2 | "dodaj notatkę do Mazur Radom: dzwonił" → disambiguation → kliknij klienta | **📝 Mutation card** z treścią notatki + 3 przyciski |
| G-T3 | "statusy" | Sformatowana lista 9 statusów bez raw Python, bez Negocjacji |
| G-T4 | "zmień status Jan Kowalski Warszawa na Zbanowany" | Odrzucenie: "Nie znam statusu Zbanowany. Dostępne: ..." |
| G-T5 | "plan na poniedziałek" | Spotkania na najbliższy poniedziałek (nie "Brak na dziś") |
| G-T6 | "plan na 20 kwietnia" | Spotkania na 20.04 |
| G-T7 | add_meeting "wczoraj o 14 z Kowalskim" | Odrzucenie z komunikatem o dacie w przeszłości |
| G-T8 | add_meeting dowolne → sprawdź kartę | Brak tekstu "Odpowiedz tak/nie" w treści karty |
| G-T9 | show_client Mariusz Kalamaga | "Data następnego kroku: 14.04.2026 (wtorek)" (nie ISO) |

---

## Sesja E+F — TRWA (12.04.2026, autonomiczne testy A-D scope + fuzzy fix)

### Batch 1 (10 testów) — ZAKOŃCZONY

| # | Test | Wynik | Notatka |
|---|------|-------|---------|
| E1-T1 | show_client (Bartek Wojcik Warszawa) | ✅ PASS | Karta read-only poprawna, brak przycisków |
| E1-T2 | show_day_plan (dziś) | ✅ PASS | Format daty DD.MM.YYYY (Dzień) poprawny |
| E1-T3 | add_meeting (Mariusz Kalamaga) | ⚠️ PASS | 3-button R1 keyboard OK, ale body ma stary tekst "tak/nie" (bug-E1-3) |
| E1-T4 | cancel meeting (Anulować) | ✅ PASS | One-click cancel, flow zamknięty |
| E1-T5 | general_question | ✅ PASS | Odpowiedź w kontekście OZE |
| E1-T6 | gibberish ("asdf qwer") | ✅ PASS | Agent prosi o wyjaśnienie |
| E1-T7 | add_client fotowoltaika→PV | ✅ PASS | Parser zamienił "fotowoltaika" na "PV" |
| E1-T8 | add_client magazyn energii+moc | ✅ PASS | Moc do Notatki, produkt "Magazyn energii" |
| E1-T9 | add_client PV+magazyn combined | ⚠️ PARTIAL | Powinno: "PV + Magazyn energii", jest: "PV, Magazyn energii" (bug-E1-9) |
| E1-T10 | R5 edit_client | ✅ PASS | Banner "Ta funkcja jest w przygotowaniu" |

**Wynik Batch 1: 8/10 ✅, 2/10 ⚠️ (nowe bugi, nie regresje)**

### Nowe bugi znalezione w Batch 1

| ID | Objaw | Lokalizacja | Priorytet |
|----|-------|-------------|-----------|
| bug-E1-3 | add_meeting card body ma stary tekst "Odpowiedz tak aby potwierdzić lub nie aby anulować" obok nowych 3-button R1 | `handle_add_meeting` lub `_enrich_meeting` response text | MEDIUM |
| bug-E1-9 | "PV z magazynem energii" / "PV + Magazyn energii" parsowane jako dwa osobne produkty zamiast jednego combined | `extract_client_data` / classifier prompt | MEDIUM |

### Batch 2 (10 testów) — ZAKOŃCZONY

| # | Test | Wynik | Notatka |
|---|------|-------|---------|
| E2-T1 | show_day_plan "plan na poniedziałek" | ❌ FAIL | Bot zwraca "Brak spotkań na dziś" zamiast poniedziałkowych. Nie parsuje nazwy dnia (bug-E2-1) |
| E2-T2 | add_meeting commit (✅ Zapisać) | ✅ PASS | Spotkanie dodane do kalendarza. Brak R7 po add_meeting (poprawne per spec) |
| E2-T3 | Dopisać flow na add_client | ✅ PASS | Karta przebudowana z email+adres. "Brakuje" lista zaktualizowana. |
| E2-T4 | change_status "podpisał umowę" | ✅ PASS | Karta: Rezygnacja z umowy → Podpisane. 3-button R1 OK. |
| E2-T5 | change_status invalid "zbanowany" | ❌ FAIL | Bot akceptuje nieistniejący status "Zbanowany" bez walidacji (bug-E2-5) |
| E2-T6 | Fuzzy search misspelled name | ✅ PASS | "Bartk Wujcik Waszawa" → znaleziony Bartek Wojcik Warszawa |
| E2-T7 | Search by phone number | ⚠️ PARTIAL | "kto ma numer 602333444" → misclassified as add_client, R4 duplicate prompt (bug-E2-7) |
| E2-T8 | R5 filtruj_klientów | ✅ PASS | Banner POST-MVP poprawny |
| E2-T9 | R5 lejek_sprzedażowy | ✅ PASS | Banner POST-MVP poprawny |
| E2-T10 | Compound message (8 fields) | ✅ PASS | Wszystkie pola wyekstrahowane poprawnie z jednej wiadomości |

**Wynik Batch 2: 6/10 ✅, 1/10 ⚠️, 2/10 ❌, 1/10 ✅ (z known bug-E1-3 potwierdzone)**

### Nowe bugi znalezione w Batch 2

| ID | Objaw | Lokalizacja | Priorytet |
|----|-------|-------------|-----------|
| bug-E2-1 | show_day_plan nie parsuje nazwy dnia — "plan na poniedziałek" zwraca "Brak spotkań na dziś" zamiast sprawdzić poniedziałek | `handle_show_day_plan` — brak date parsing z wiadomości | HIGH |
| bug-E2-5 | Bot akceptuje dowolny status (np. "Zbanowany") bez walidacji przeciwko 9-statusowemu pipeline | `handle_change_status` / `extract_status_data` — brak whitelist validation | HIGH |
| bug-E2-7 | "kto ma numer X" misclassified jako add_client zamiast show_client. Bot traktuje jako nowy wpis, znajduje duplikat, pyta z mutation buttons | `classify_intent` — phone-number search pattern not recognized | MEDIUM |

### Batch 3 (10 testów) — ZAKOŃCZONY

| # | Test | Wynik | Notatka |
|---|------|-------|---------|
| E3-T1 | add_client minimal (name+city) | ✅ PASS | "Tomek Zieliński Lublin" — karta z długą listą "Brakuje" |
| E3-T2 | show_client non-existent | ✅ PASS | "Nie mam 'Zenon Nieistniejący' w bazie." — czysta odpowiedź |
| E3-T3 | add_meeting past date "wczoraj" | ❌ FAIL | Temporal guard NIE działa — karta na 11.04.2026 (przeszłość) bez ostrzeżenia (bug-E3-3) |
| E3-T4 | add_meeting today "dziś o 18:00" | ✅ PASS | 12.04.2026 (niedziela), 18:00, "u klienta, Warszawa" |
| E3-T5 | Polish special chars (Ł,ą,ó,ź) | ✅ PASS | Wojciech Łączkowski Łódź — wszystkie znaki OK. Tech specs → Notatki |
| E3-T6 | (merged with T5) | — | — |
| E3-T7 | "Rezygnacja" as classifier edge | ✅ PASS | Poprawnie routed do change_status, nie do add_client |
| E3-T8 | add_client "klimatyzacja" | ❌ FAIL | Bot akceptuje "klimatyzacja" jako produkt (bug-B2-1 potwierdzone) |
| E3-T9 | show_day_plan "dziś" explicit | ✅ PASS | "Brak spotkań na dziś." — poprawne (brak spotkań w niedzielę) |
| E3-T10 | add_note (Sesja C deployed) | ✅ PASS | R5 banner — oczekiwane (D.1 nie deployed) |

**Wynik Batch 3: 7/9 ✅, 2/9 ❌ (T6 merged z T5)**

### Nowe bugi znalezione w Batch 3

| ID | Objaw | Lokalizacja | Priorytet |
|----|-------|-------------|-----------|
| bug-E3-3 | Temporal guard NIE działa — "spotkanie wczoraj o 14:00" tworzy kartę na 11.04 (przeszłość) bez ostrzeżenia | `handle_add_meeting` / `extract_meeting_data` — brak past-date validation | HIGH |
| bug-B2-1 | POTWIERDZONE — "klimatyzacja" nadal akceptowana jako produkt. Nie tylko deployment lag. | `extract_client_data` / classifier prompt | HIGH |

---

### Batch 4 (10 testów) — ZAKOŃCZONY

| # | Test | Wynik | Notatka |
|---|------|-------|---------|
| E4-T1 | add_client duplicate (R4) | ✅ PASS | R4 2-button: [Dopisz do istniejącego] [Utwórz nowy wpis] + info o istniejącym |
| E4-T2 | add_meeting bez godziny | ✅ PASS | "Nie rozpoznałem daty lub godziny" + przykład. Poprawne odrzucenie |
| E4-T3 | add_meeting bez daty (tylko czas) | ✅ PASS | Default do dziś (12.04), godzina 15:30. Rozsądne |
| E4-T4 | show_client only last name (ambiguous) | ✅ PASS | Disambiguation: "Mam 2 klientów" + 2 choice buttons |
| E4-T5 | Compound: add_client + add_meeting | ⚠️ PARTIAL | Tylko add_meeting processed. Single-intent classifier MVP limitation |
| E4-T6 | Empty/whitespace message | N/A | Telegram nie wysyła pustych wiadomości |
| E4-T7 | change_status to same status | ⚠️ PARTIAL | Bot tworzy kartę "Rezygnacja z umowy → Rezygnacja z umowy" (no-op, bug-E4-7) |
| E4-T8 | Search by first name + city | ✅ PASS | "pokaż Bartek Warszawa" → Bartek Wojcik bezpośrednio |
| E4-T9 | add_meeting z adresem ulicy | ✅ PASS | "jutro"→13.04, Miejsce: Warszawa, ul. Marszałkowska 100 |
| E4-T10 | Search without diacritics | ✅ PASS | "pokaz Wojcik Lublin" → Krzysztof Wojcik znaleziony |

**Wynik Batch 4: 7/9 ✅, 2/9 ⚠️ (T6 N/A)**

### Nowe bugi znalezione w Batch 4

| ID | Objaw | Lokalizacja | Priorytet |
|----|-------|-------------|-----------|
| bug-E4-7 | Bot tworzy mutation card dla zmiany statusu na ten sam status (no-op). Powinien wykryć i poinformować | `handle_change_status` — brak porównania current==new | LOW |

---

### Batch 5 (10 testów) — ZAKOŃCZONY

| # | Test | Wynik | Notatka |
|---|------|-------|---------|
| E5-T1 | show_day_plan "plan na jutro" | ✅ PASS | "jutro" (13.04) parsed poprawnie — spotkanie Mariusza Kalamaga wyświetlone |
| E5-T2 | show_day_plan "plan na poniedziałek" | ❌ FAIL | Defaultuje do "dziś" (12.04) — bug-E2-1 potwierdzone (nazwy dni nie parsowane) |
| E5-T3 | add_client z notatką techniczną | ✅ PASS | "Zbigniew Nowak Gdańsk 500600700 PV dach skośny 40m2" → PV + dach skośny→Notatki |
| E5-T4 | change_status valid (Spotkanie umówione) | ✅ PASS | Poprawna karta z transition display + R7 prompt po zapisie |
| E5-T5 | add_meeting compound "za tydzień" | ✅ PASS | 19.04.2026 (niedziela) poprawnie obliczone |
| E5-T6 | show_client partial name match | ✅ PASS | "pokaż Zbigniew Gdańsk" → Zbigniew Nowak znaleziony |
| E5-T7 | R5 POST-MVP "edytuj klienta" | ✅ PASS | Banner "Ta funkcja jest w przygotowaniu" |
| E5-T8 | help request "jak dodać nowego klienta?" | ✅ PASS | Helpful response with example format |
| E5-T9 | add_meeting "telefoniczne" as location | ✅ PASS | "Miejsce: telefoniczne" — poprawnie parsed. bug-E1-3 (tak/nie remnant) present |
| E5-T10 | show_client full (Mariusz Kalamaga) | ⚠️ PARTIAL | Dane poprawne, ALE "Data następnego kroku: 2026-04-14" w formacie ISO zamiast DD.MM.YYYY (bug-E5-1) |

**Wynik Batch 5: 8/10 ✅, 1/10 ⚠️, 1/10 ❌**

### Nowe bugi znalezione w Batch 5

| ID | Objaw | Lokalizacja | Priorytet |
|----|-------|-------------|-----------|
| bug-E5-1 | "Data następnego kroku" w show_client wyświetlana w formacie ISO (2026-04-14) zamiast DD.MM.YYYY (Dzień tygodnia) | `handle_show_client` / `format_client_card` — brak date-format normalization | MEDIUM |
| bug-E2-1 | POTWIERDZONE (2x) — "plan na poniedziałek" i "plan na jutro" — parser rozumie "jutro"/"dziś" ale NIE nazwy dni tygodnia | `handle_show_day_plan` date parser | HIGH |

---

### Batch 6 (10 testów) — ZAKOŃCZONY

| # | Test | Wynik | Notatka |
|---|------|-------|---------|
| E6-T1 | add_client "Pompa ciepła" explicit | ✅ PASS | Agnieszka Wiśniewska Kraków — product parsed poprawnie |
| E6-T2 | add_meeting "pojutrze o 14" | ✅ PASS | 14.04.2026 (wtorek) — "pojutrze" poprawnie obliczone |
| E6-T3 | show_client by phone "znajdź klienta z numerem 999999999" | ❌ FAIL | Misclassified jako add_client (bug-E2-7 potwierdzone 2x) |
| E6-T4 | change_status "Oferta wysłana" | ✅ PASS | Poprawna karta, brak from-status gdy current=empty |
| E6-T5 | add_client "z polecenia od sąsiada" source | ✅ PASS | Źródło: polecenie od sąsiada — poprawnie extracted |
| E6-T6 | Long message 290 chars stress test | ✅ PASS | Doskonała ekstrakcja: produkt, notatki techniczne, źródło |
| E6-T7 | add_meeting wrong client match | ❌ FAIL | "Tomek Zieliński" → karta "Piotr Zieliński" — silent wrong-client substitution (bug-E6-1) |
| E6-T8 | show_day_plan "15 kwietnia" explicit date | ❌ FAIL | Defaultuje do "dziś" — explicit dates not parsed (bug-E2-1 extended) |
| E6-T9 | Classifier "ile mam klientów" | ✅ PASS | R5 banner "Ta funkcja jest w przygotowaniu" |
| E6-T10 | add_client "Magazyn energii" only | ✅ PASS | Produkt poprawnie parsed jako single item |

**Wynik Batch 6: 6/10 ✅, 0/10 ⚠️, 3/10 ❌ (+ 1 N/A)**

### Nowe bugi znalezione w Batch 6

| ID | Objaw | Lokalizacja | Priorytet |
|----|-------|-------------|-----------|
| bug-E6-1 | Bot silently substitutes wrong client — "Tomek Zieliński Lublin" matched to "Piotr Zieliński" (different first name). No disambiguation, no warning. | `find_client` / fuzzy matching logic — matches last name+city, ignores first name mismatch | HIGH |
| bug-E2-1 | EXTENDED — show_day_plan nie parsuje explicit dates ("15 kwietnia"), nie tylko day names ("poniedziałek"). Tylko "dziś"/"jutro" działają | `handle_show_day_plan` date parser | HIGH |
| bug-E2-7 | POTWIERDZONE (2x) — "znajdź klienta z numerem X" misclassified jako add_client | `classify_intent` system prompt | MEDIUM |

---

### Batch 7 (10 testów) — ZAKOŃCZONY

| # | Test | Wynik | Notatka |
|---|------|-------|---------|
| E7-T1 | add_client with email "kamil.baran@gmail.com" | ✅ PASS | Email poprawnie extracted do osobnego pola |
| E7-T2 | add_meeting "na godzinę 16 w piątek" | ✅ PASS | 17.04.2026 (piątek) 16:00 — day name parsed w add_meeting (ale NIE w show_day_plan!) |
| E7-T3 | show_client misspelled city "Waeszawa" | ✅ PASS | Fuzzy match → Bartek Wojcik Warszawa znaleziony |
| E7-T4 | change_status "Podpisane" | ✅ PASS | "Rezygnacja z umowy → Podpisane" — from-status wyświetlony poprawnie |
| E7-T5 | add_client same phone different name | ✅ PASS | Jan Nowak z tel 999999999 (=Mariusz Kalamaga). R4 name-based, no phone-dup detect. Per spec OK |
| E7-T6 | Gibberish 85-char string | ✅ PASS | "Co chcesz zrobić?" — clean fallback, no crash |
| E7-T7 | add_meeting "za 2 godziny" | ⚠️ PARTIAL | Parser nie obsługuje relative time expressions. Clean error msg z przykładem |
| E7-T8 | show_client "pokaż Wojcik" disambiguation | ✅ PASS | "Mam 2 klientów" + choice buttons — perfect |
| E7-T9 | Rapid-fire 2 messages (1s gap) | ✅ PASS | Oba przetworzone poprawnie, w kolejności, zero race conditions |
| E7-T10 | "pokaż plan" (no date) | ✅ PASS | Default do dziś — "Brak spotkań na dziś." (niedziela) |

**Wynik Batch 7: 8/10 ✅, 1/10 ⚠️, 0/10 ❌ (+ 1 observation: E7-T5 phone-dup not detected but per-spec OK)**

### Kluczowe odkrycie Batch 7

add_meeting parser obsługuje nazwy dni tygodnia ("w piątek" → 17.04.2026) ale show_day_plan NIE ("plan na poniedziałek" → default dziś). To potwierdza że oba handlery używają różnych parserów daty — bug-E2-1 jest specyficzny dla show_day_plan.

---

### Batch 8 (10 testów) — ZAKOŃCZONY

| # | Test | Wynik | Notatka |
|---|------|-------|---------|
| E8-T1 | Dopisać flow (add phone+address+email) | ✅ PASS | Card rebuild z 3 nowymi polami — Brakuje list zaktualizowany |
| E8-T2 | add_meeting time overlap (15:00 conflict) | ✅ PASS | ⚠️ Uwaga: "masz już spotkanie o tej porze: Spotkanie z Mariusz Kalamaga" — excellent |
| E8-T3 | "pokaż klientów z Warszawy" city filter | ✅ PASS | R5 banner — filtruj_klientów POST-MVP |
| E8-T4 | change_status "Zamontowana" | ✅ PASS | Poprawna karta, from-status empty (klient bez statusu) |
| E8-T5 | add_client with address "ul. Główna 10" | ✅ PASS | Adres poprawnie extracted do osobnego pola |
| E8-T6 | "anuluj" without pending flow | ✅ PASS | "Anulowane." — clean handling, no crash |
| E8-T7 | add_meeting full address "Kraków ul. Długa 15" | ✅ PASS | Miejsce: Kraków ul. Długa 15 — city+street combined |
| E8-T8 | Pure number "123456789" | ✅ PASS | "Co chcesz zrobić?" — clean fallback, not misclassified as add_client |
| E8-T9 | "pomóż" help request | ✅ PASS | "Co chcesz zrobić?" — generic prompt for vague input |
| E8-T10 | add_client → quick cancel | ✅ PASS | One-click cancel, immediate "Anulowane.", no confirmation loop |

**Wynik Batch 8: 9/10 ✅, 0/10 ⚠️, 0/10 ❌ (best batch — no new bugs)**

### Kluczowe odkrycie Batch 8

⚠️ Meeting overlap detection działa! Bot wyświetla ostrzeżenie gdy nowe spotkanie koliduje z istniejącym. To nie była wcześniej testowana funkcjonalność.

### Batch 9 (10 testów) — ZAKOŃCZONY

| # | Test | Wynik | Notatka |
|---|------|-------|---------|
| E9-T1 | add_client "Ewa Mazur Szczecin PV 700800900 ewa@test.pl" | ✅ PASS | Compound message — all fields parsed correctly |
| E9-T2 | show_client "Ewa Mazur Szczecin" (just added) | ✅ PASS | Read-only card, no buttons, date DD.MM.YYYY (sobota) |
| E9-T3 | add_note "Ewa Mazur Szczecin: chce ofertę na 10kW" | ✅ PASS | 📝 add_note card with 3 buttons, note text correct |
| E9-T4 | change_status "Ewa Mazur Szczecin Spotkanie umówione" | ✅ PASS | Status card Nowy lead → Spotkanie umówione, 3 buttons |
| E9-T5 | add_meeting "spotkanie z Ewą Mazur Szczecin jutro o 14" | ✅ PASS | Card with correct date, 14:00, place Szczecin |
| E9-T6 | "Ala Wrocław" after disambiguation flow | ❌ FAIL | **Flow state leak** — bot showed Mariusz Kalamaga card instead of handling "Ala Wrocław" as new input. Disambiguation state leaked through intervening messages |
| E9-T7 | add_meeting "1.5 godziny" duration | ✅ PASS | "1.5 godziny" parsed as 90 min. Day-name "wtorek" → 14.04.2026. Known bug-E1-3 (tak/nie text) |
| E9-T8 | "pokaż Kowalskiego" disambiguation | ✅ PASS | 2 matches (Jan — Warszawa, Marcin — Gdańsk). Button click → correct card |
| E9-T9 | "statusy" command | ❌ FAIL | Raw Python list format: `['Nowy lead', ..., 'Negocjacje', ..., 'Odrzucone']`. Contains removed 'Negocjacje', missing 'Zamontowana'/'Nieaktywny'/'Rezygnacja z umowy'. Only 7/9 statuses |
| E9-T10 | add_client "fotowoltaika" synonym | ✅ PASS | "fotowoltaika" correctly mapped to "PV". Known bug-A1-1 (ID kalendarza in Brakuje) |

**Wynik Batch 9: 8/10 ✅, 0/10 ⚠️, 2/10 ❌**

### Nowe bugi z Batch 9

| ID | Objaw | Priorytet |
|----|-------|-----------|
| bug-E9-6 | Flow state leak — disambiguation state persists through intervening unrelated messages. After disambiguation flow for "Mariusz" + subsequent messages, "Ala Wrocław" showed Mariusz Kalamaga card instead of fresh intent routing | HIGH |
| bug-E9-9 | "statusy" command returns stale/wrong list: raw Python list format, includes removed "Negocjacje", missing "Zamontowana"/"Nieaktywny"/"Rezygnacja z umowy" (7 vs 9 statuses) | HIGH |

---

### Batch 10 (10 testów) — ZAKOŃCZONY

| # | Test | Wynik | Notatka |
|---|------|-------|---------|
| E10-T1 | add_client email only (no phone) | ✅ PASS | Email extracted, phone listed in Brakuje. Known bugs (A1-1, E1-3) |
| E10-T2 | add_meeting "za tydzień" relative | ❌ FAIL | "za tydzień" → 19.04.2026 ✅, BUT **wrong client**: "Jan Kowalski Warszawa" → matched "Jan Nowak". 3rd case of bug-E6-1 |
| E10-T3 | show_client exact "Jan Kowalski Warszawa" | ⚠️ WARN | Exact full name+city still triggered disambiguation with 3 results incl. "Jan Nowak — Piaseczno". Too-fuzzy search |
| E10-T4 | change_status "Marcin Kowalski Gdańsk Odrzucone" | ❌ FAIL | Disambiguation shown (correct) → clicked Marcin Kowalski → got read-only card, but **NO status change mutation card**. Intent lost after disambiguation |
| E10-T5 | add_client "pompa ciepła" multi-word | ✅ PASS | "Pompa ciepła" parsed correctly, all fields correct |
| E10-T6 | "edytuj klienta" POST-MVP | ✅ PASS | R5 banner "Ta funkcja jest w przygotowaniu. Niedługo dostępna." |
| E10-T7 | add_meeting "Ewą Mazur Szczecin pojutrze" | ❌ FAIL | "pojutrze" → 14.04 ✅, BUT **wrong client**: "Ewa Mazur" → matched "Jan Mazur". 4th case bug-E6-1 |
| E10-T8 | Two consecutive add_client (sequential) | ✅ PASS | Cancel first → second processed correctly, no state leak |
| E10-T9 | "lejek sprzedażowy" POST-MVP | ✅ PASS | R5 banner correct |
| E10-T10 | add_note non-existent client | ⚠️ WARN | R5 banner returned. Expected if D not deployed. BUT E9-T3 add_note worked earlier — discrepancy needs investigation |

**Wynik Batch 10: 5/10 ✅, 2/10 ⚠️, 3/10 ❌**

### Nowe bugi z Batch 10

| ID | Objaw | Priorytet |
|----|-------|-----------|
| bug-E10-2 | Fuzzy search too broad — "Jan Kowalski Warszawa" returns "Jan Nowak Piaseczno" as match. add_meeting silently picks first result → wrong client | HIGH (extends bug-E6-1) |
| bug-E10-4 | Intent loss after disambiguation in change_status — clicking disambiguation button shows read-only card but drops the change_status mutation flow | HIGH |
| bug-E10-7 | add_meeting "Ewa Mazur Szczecin" matched to "Jan Mazur" — fuzzy matcher ignores first name entirely, matches on last name only | HIGH (extends bug-E6-1) |

---

### Batch 11 (10 testów) — ZAKOŃCZONY

| # | Test | Wynik | Notatka |
|---|------|-------|---------|
| E11-T1 | "kto ma numer 600123456" phone search | ⚠️ WARN | Correct routing (not misclassified as add_client!) but Sheets access error "Brak dostępu do danych" |
| E11-T2 | add_client with tech specs + source | ✅ PASS | "10kW dach skośny południe" → Notatki, "z ogłoszenia na OLX" → Źródło: OLX. Excellent extraction |
| E11-T3 | "plan na poniedziałek" day name | ❌ FAIL | Confirms bug-E2-1: defaulted to "dziś" (niedziela), ignored "poniedziałek" |
| E11-T4 | change_status "Ewa Mazur Szczecin Oferta wysłana" | ❌ FAIL | Returned Jan Mazur Radom/Legionowo disambiguation — didn't find Ewa Mazur at all. Extreme case of bug-E6-1 |
| E11-T5 | add_meeting "8:30" non-round time | ❌ FAIL | 08:30 parsed ✅ BUT wrong client: "Marcin Kowalski Gdańsk" → "Jan Kowalski". 5th case bug-E6-1 |
| E11-T6 | "ile mam klientów" general question | ✅ PASS | R5 banner — correctly classified as aggregate/filter POST-MVP |
| E11-T7 | add_client with "z Facebooka" source | ✅ PASS | Źródło: Facebook extracted correctly. All fields correct |
| E11-T8 | change_status "Rezygnacja z umowy" via disambiguation | ❌ FAIL | Confirms bug-E10-4: disambiguation → clicked Jan Kowalski → read-only card, change_status intent lost |
| E11-T9 | show_client diacritics-free "Zielinskiego" | ✅ PASS | Matched "Piotr Zieliński" correctly — diacritics-free search works |
| E11-T10 | add_meeting "telefoniczne" | ⚠️ WARN | Client matched correctly (Piotr Zieliński ✅), BUT "telefoniczne" not captured as Miejsce — defaulted to client city "Radom". Inconsistent with earlier test |

**Wynik Batch 11: 4/10 ✅, 2/10 ⚠️, 4/10 ❌**

### Kluczowe odkrycia Batch 11

1. **bug-E6-1 jest SYSTEMOWY** — fuzzy matcher w add_meeting silently picks wrong client (5th case). W change_status triggers disambiguation with wrong clients.
2. **bug-E10-4 potwierdzone 2x** — intent loss after disambiguation is reproducible in change_status flows.
3. **Phone search routing IMPROVED** — "kto ma numer X" was correctly routed (not add_client), but hit Sheets API error.
4. **Diacritics-free search works** — "Zielinskiego" → "Piotr Zieliński" ✅

---

### Batch 12 (10 testów) — ZAKOŃCZONY

| # | Test | Wynik | Notatka |
|---|------|-------|---------|
| E12-T1 | add_client all fields (name, city, product, phone, email, address, source, notes) | ✅ PASS | Outstanding NLP: 12kW dach płaski→Notatki, email, address, source all extracted from single message |
| E12-T2 | /start command | ✅ PASS | "Jesteś już połączony z OZE-Agent. Napisz cokolwiek, żeby zacząć!" |
| E12-T3 | add_meeting "15 kwietnia" explicit date | ✅ PASS | 15.04.2026 (środa) ✅. Confirms add_meeting parser handles explicit dates (unlike show_day_plan) |
| E12-T4 | show_client non-existent "Zbigniew Wróblewski Olkusz" | ✅ PASS | Clean "Nie mam X w bazie." — no crash, no false match |
| E12-T5 | change_status natural language "podpisał umowę" | ✅ PASS | "podpisał umowę" → Status: → Podpisane. Excellent NLP classification |
| E12-T6 | "Nowak" bare last name | ✅ PASS | 5 matches with disambiguation buttons — correct show_client behavior |
| E12-T7 | add_client "PV + Magazyn energii" combined | ❌ FAIL | Confirms bug-E1-9 (3rd time): parsed as "PV, Magazyn energii" (two products) |
| E12-T8 | "plan na dziś" | ✅ PASS | "Brak spotkań na dziś." — correct behavior on Sunday |
| E12-T9 | add_meeting "wczoraj" past date | ❌ FAIL | Confirms bug-E3-3: created card for 11.04 (yesterday), temporal guard did NOT reject |
| E12-T10 | "odśwież kolumny" admin command | ✅ PASS | Shows 17 columns (empty col visible as double comma). Confirms bugs A1-1 and B1-1 still present in sheet |

**Wynik Batch 12: 8/10 ✅, 0/10 ⚠️, 2/10 ❌**

### Kluczowe odkrycia Batch 12

1. **NLP extraction jest imponujące** — compound message z 8 polami (name, city, product, phone, email, address, source, tech notes) poprawnie rozparsowany w jednym kroku.
2. **Natural language change_status** — "podpisał umowę" → Podpisane. Classifier correctly infers status from prose.
3. **"odśwież kolumny" potwierdza sheet-side bugs** — empty column (double comma) + "ID kalendarza" still there.

---

### Batch 13 (10 testów) — 12.04.2026, 09:56-10:02

| # | Input | Wynik | Uwagi |
|---|-------|-------|-------|
| E13-T1 | add_client "Michał Grabowski Kielce PV 510620730" → Zapisać → R7 → Anuluj/nic | ✅ PASS | Full save+R7+R7-cancel flow tested. Client SAVED to Sheets |
| E13-T2 | "." minimal input | ✅ PASS | Clean "Co chcesz zrobić?" fallback |
| E13-T3 | (merged into T2) | ✅ PASS | — |
| E13-T4 | add_meeting "za 2 dni o 14" Michał Grabowski Kielce | ✅ PASS | "za 2 dni" → 14.04.2026 (wtorek) correct. Duration 60min default. Miejsce auto-filled Kielce. bug-E1-3 confirmed (old tak/nie text) |
| E13-T5 | show_client with emoji 🏠 "pokaż klienta 🏠 Michał Grabowski Kielce" | ✅ PASS | Emoji in message didn't break intent classification. Read-only card, no buttons (correct per R1) |
| E13-T6 | "klient rezygnuje z umowy Jan Kowalski Warszawa" | ❌ FAIL | NLP correctly parsed as change_status. Disambiguation appeared (3 results incl. wrong: Jan Nowak Piaseczno, Marcin Kowalski Gdańsk — confirms bug-E6-1/E10-2). After clicking correct "Jan Kowalski Warszawa" → read-only card only. **bug-E10-4 confirmed 3rd time**: intent lost after disambiguation |
| E13-T7 | add_client "Zofia Wiśniewska Łódź" (name+city only) | ✅ PASS | Minimum data accepted. "Brakuje" lists all missing fields. 3-button card. bug-A1-1 confirmed (ID kalendarza in Brakuje) |
| E13-T8 | "spotkania na ten tydzień" | ⚠️ PARTIAL | Intent correctly classified as show_day_plan but "na ten tydzień" not parsed — defaulted to "dziś". Confirms bug-E2-1 |
| E13-T9 | add_meeting "Jan Kowalskim Warszawa jutro o 10 na 30 minut" | ❌ FAIL | "30 minut" correctly parsed (Czas trwania: 30 min ✅). "jutro" → 13.04 ✅. **BUT Klient: Jan Nowak** — wrong client! bug-E6-1 confirmed 6th time. Also bug-E1-3 (tak/nie text) |
| E13-T10 | Long gibberish (126 chars random letters) | ✅ PASS | Clean "Co chcesz zrobić?" fallback, no crash |

**Wynik Batch 13: 6/10 ✅, 1/10 ⚠️, 2/10 ❌** (T3 merged into T2, effective 9 unique tests)

### Kluczowe odkrycia Batch 13

1. **bug-E6-1 is the #1 systemic issue** — 6th confirmed wrong-client substitution. Fuzzy matcher consistently ignores first name.
2. **bug-E10-4 confirmed 3rd time** — disambiguation always drops intent. change_status after disambiguation = dead flow.
3. **"za 2 dni" relative date** works perfectly in add_meeting. Duration "30 minut" also parsed correctly.
4. **Emoji robustness** — bot handles emoji in messages without any issues.
5. **Minimum-data add_client** — name+city only is enough to create a card.

---

### Batch 14 (10 testów) — 12.04.2026, 10:04-10:11

| # | Input | Wynik | Uwagi |
|---|-------|-------|-------|
| E14-T1 | "dodaj notatkę do Michał Grabowski Kielce: [long note 180 chars]" | ✅ PASS | R5 POST-MVP banner correctly shown (add_note not deployed in A-C) |
| E14-T2 | "spotkanie z Michałem Grabowskim Kielce w środę o 11 ul. Kwiatowa 5 Kielce" | ✅ PASS | "w środę" → 15.04.2026 ✅. Address "ul. Kwiatowa 5, Kielce" extracted ✅. Correct client ✅ |
| E14-T3 | "pokaż Michała Grabowskiego z Kielc" (declined Polish forms) | ✅ PASS | Genitive case handling works! "Michała Grabowskiego" → Michał Grabowski, "z Kielc" → Kielce |
| E14-T4 | "zmień status Michał Grabowski Kielce na Spotkanie umówione" | ✅ PASS | Direct status name correctly parsed. Client found without disambiguation. Mutation card with 3 buttons |
| E14-T5 | "nowy klient Adam Baran Gdynia PV + Magazyn energii 501222333 adam.baran@wp.pl ul. Morska 22 z targów OZE Expo" | ⚠️ PARTIAL | 7/8 fields correctly extracted (name, city, phone, email, address, source all ✅). **bug-E1-9 confirmed 4th time**: "PV + Magazyn energii" split into "PV, Magazyn energii" |
| E14-T6 | "anuluj" (no pending flow) | ✅ PASS | Clean "Anulowane." — no crash, no error |
| E14-T7 | "spotkanie telefoniczne z Michałem Grabowskim Kielce pojutrze o 9:30" | ⚠️ PARTIAL | Date/time/client correct. **NEW: "telefoniczne" not parsed as Miejsce** — client city "Kielce" auto-filled instead. Previous tests confirmed "telefoniczne" worked — possible adjective vs noun form difference |
| E14-T8 | "pokaż klienta z numerem 510620730" | ❌ FAIL | **bug-E2-7 confirmed 3rd time**: phone search misclassified as add_client. Entire message treated as client name. Duplicate detection suggested Michał Grabowski |
| E14-T9 | Rapid-fire: "pokaż Michała Grabowskiego Kielce" + "plan na jutro" (0s gap) | ✅ PASS | Both processed sequentially. show_client ✅, show_day_plan jutro ✅ (shows 15:00-16:00 Spotkanie z Mariusz Kalamaga with full details). No race conditions |
| E14-T10 | "pomoc" | ✅ PASS | Clean "Co chcesz zrobić?" fallback. No help command in MVP spec — graceful handling |

**Wynik Batch 14: 7/10 ✅, 2/10 ⚠️, 1/10 ❌**

### Kluczowe odkrycia Batch 14

1. **Polish declension handling is impressive** — "Michała Grabowskiego z Kielc" (genitive) correctly resolved.
2. **bug-E2-7 is consistent** — phone-based search ALWAYS misclassifies as add_client. Needs classifier prompt fix.
3. **"telefoniczne" as adjective** — when used as "spotkanie telefoniczne" (adj.), not parsed as location. May work only as standalone/noun form.
4. **show_day_plan "jutro" shows rich data** — client name, address, phone, product, next step. Quality display.
5. **Rapid-fire robustness confirmed again** — zero race conditions.

---

### Batch 15 (10 testów) — 12.04.2026, 10:13-10:23

| # | Input | Wynik | Uwagi |
|---|-------|-------|-------|
| E15-T1 | add_client "Paweł Zając Poznań" → Dopisać → "telefon 602333444 pompa ciepła" | ✅ PASS | Dopisać flow works: card rebuilt with phone+product merged. "Brakuje" list updated. 3-button card |
| E15-T2 | add_meeting Michał Grabowski jutro o 12 → Zapisać | ✅ PASS | Meeting saved to Calendar (visible in UI at 12:00 Mon). No R7 after add_meeting — correct per spec (add_meeting defines next step) |
| E15-T3 | "zmień status Michał Grabowski Kielce na Odrzucone" | ✅ PASS | Status "Odrzucone" correctly parsed. Client found. 3-button mutation card |
| E15-T4 | "edytuj klienta Michał Grabowski Kielce" | ✅ PASS | R5 POST-MVP banner correctly shown |
| E15-T5 | "lejek sprzedażowy" | ✅ PASS | R5 POST-MVP banner correctly shown |
| E15-T6 | add_client duplicate "Michał Grabowski Kielce pompa ciepła 511999888" | ✅ PASS | R4 duplicate detection: "⚠ Masz już Michał Grabowski (Kielce, PV)." + 2-button card [Dopisz do istniejącego][Utwórz nowy wpis] |
| E15-T7 | "pokaż klienta Grabowski Kilece" (misspelled city + last name only) | ✅ PASS | Fuzzy city matching "Kilece" → "Kielce" works. Michał Grabowski found |
| E15-T8 | "spotkanie z Grabowskim Kielce za tydzień o 16" | ✅ PASS | "za tydzień" → 19.04.2026 (niedziela) ✅. Last-name-only + declined form resolved correctly |
| E15-T9 | "dodaj klienta Jean-Pierre Müller Wrocław PV 502111222" | ✅ PASS | Hyphenated name + umlaut handled perfectly. All fields extracted |
| E15-T10 | "filtruj klientów po statusie Nowy lead" | ✅ PASS | R5 POST-MVP banner correctly shown |

**Wynik Batch 15: 10/10 ✅, 0/10 ⚠️, 0/10 ❌** 🏆 Perfect batch!

### Kluczowe odkrycia Batch 15

1. **Dopisać flow robust** — card rebuild with merged data works, Brakuje list updates correctly.
2. **add_meeting Calendar integration confirmed** — meeting visible in Google Calendar after save.
3. **R4 duplicate detection with conflict** — different phone+product triggers 2-button choice card.
4. **Fuzzy city matching** — "Kilece" → "Kielce" resolved. Misspellings handled.
5. **International characters** — hyphens and umlauts in names (Jean-Pierre Müller) work.
6. **All 3 R5 POST-MVP banners confirmed** — edit_client, lejek, filtruj all return correct banner.
7. **No R7 after add_meeting** — correct per spec (meeting itself IS the next step).

### Batch 16 (10 testów) — 12.04.2026, 10:23-10:32

| # | Input | Wynik | Uwagi |
|---|-------|-------|-------|
| E16-T1 | "kto ma numer 600123456" | ❌ FAIL | bug-E2-7 (4th confirm): Phone search misclassified as add_client. Bot tries to create new client instead of searching |
| E16-T2 | add_client "PV i magazyn energii" | ⚠️ PARTIAL | bug-E1-9 (5th confirm): "PV i magazyn energii" split into two products instead of single "PV + Magazyn energii" |
| E16-T3 | change_status "Zamontowana" | ✅ PASS | Status correctly parsed, 3-button mutation card shown |
| E16-T4 | "plan na piątek" | ❌ FAIL | bug-E2-1: show_day_plan doesn't parse day names — defaulted to today instead of Friday |
| E16-T5 | add_meeting "wczoraj o 10" | ❌ FAIL | bug-E3-3 (3rd confirm): Past date "wczoraj" accepted. BUT overlap detection works — showed conflict with existing meeting |
| E16-T6 | change_status "Negocjacje" | ❌ FAIL | bug-E2-5 (2nd confirm): Removed status "Negocjacje" accepted without whitelist validation |
| E16-T7 | "pokaż Zenon Marciniak Bydgoszcz" | ✅ PASS | Non-existent client → clean "Nie mam w bazie" response, no crash, no false match |
| E16-T8 | add_client "klimatyzacja" as product | ⚠️ PARTIAL | bug-B2-1 inconsistency: "klimatyzacja" went to Notatki field this time (not product). Earlier tests had it accepted as product. Non-deterministic AI parser |
| E16-T9 | /start | ✅ PASS | Clean welcome message |
| E16-T10 | "pokaż Kowalskiego" (bare last name) | ✅ PASS | Disambiguation shown: 2 clients (Jan Kowalski Warszawa, Marcin Kowalski Gdańsk) with buttons |

**Wynik Batch 16: 4/10 ✅, 2/10 ⚠️, 4/10 ❌**

### Kluczowe odkrycia Batch 16

1. **bug-E2-7 systemic** — phone search "kto ma numer X" consistently misclassified as add_client (4th confirmation).
2. **bug-E3-3 + overlap detection** — past date accepted (bad) but overlap detection works correctly (good). Mixed result.
3. **bug-B2-1 non-deterministic** — "klimatyzacja" handling inconsistent between tests. Sometimes product, sometimes Notatki. AI parser variance.
4. **Disambiguation still solid** — bare last name "Kowalskiego" correctly shows 2-client disambiguation.
5. **Non-existent client handling clean** — no crash, no false fuzzy match.

### Batch 17 (10 testów) — 12.04.2026, 10:35-10:41

| # | Input | Wynik | Uwagi |
|---|-------|-------|-------|
| E17-T1 | add_client "Jan Wiśniewski Łódź 501 222 333 PV" | ✅ PASS | Phone with spaces "501 222 333" correctly parsed. All fields extracted. 3-button R1 |
| E17-T2 | add_meeting "Bartek Wojcik Warszawa 15 kwietnia o 14:30" | ✅ PASS | Explicit date "15 kwietnia" → 15.04.2026 (środa) ✅. Time 14:30 ✅. bug-E1-3 old tak/nie text still in body (known) |
| E17-T3 | "pokaż Bartek Warszawa" (first name + city, no last name) | ✅ PASS | Bartek Wojcik found correctly. Read-only card, no buttons. All fields displayed |
| E17-T4 | add_client "Tomasz Lewandowski Gdańsk pompa ciepła i PV 509111222" | ✅ PASS | Two separate products correctly parsed as "Pompa ciepła, PV" (these ARE two products, not the combined "PV + Magazyn energii") |
| E17-T5 | "Michał Grabowski Kielce złożył rezygnację" | ✅ PASS | Natural language "złożył rezygnację" → "Rezygnacja z umowy". Client found. 3-button mutation card |
| E17-T6 | add_meeting "Jan Kowalski Warszawa za 3 dni o 9:00" | ❌ FAIL | bug-E6-1 (7th confirm): "Jan Kowalski Warszawa" → matched "Jan Nowak". Wrong client. Date arithmetic "za 3 dni" = 15.04 correct |
| E17-T7 | "ile mam klientów" | ✅ PASS | Classified as POST-MVP stats feature → R5 banner "Ta funkcja jest w przygotowaniu" |
| E17-T8 | add_client minimal "Anna Mazurek Katowice" → Dopisać → "telefon 512333444 magazyn energii z polecenia" | ✅ PASS | Dopisać flow: card rebuilt with phone+product+source merged. Brakuje list updated. Source "z polecenia" → polecenie |
| E17-T9 | "plan na poniedziałek" | ❌ FAIL | bug-E2-1: show_day_plan defaults to today (niedziela). Calendar has meetings on Monday but bot says "Brak spotkań na dziś" |
| E17-T10 | add_client duplicate "Jan Kowalski Warszawa 999888777 pompa ciepła" | ✅ PASS | R4 conflict detection: ⚠ "Masz już Jan Kowalski (Piłsudskiego 12, Warszawa, Pompa ciepła)" + 2-button [Dopisz][Utwórz nowy] |

**Wynik Batch 17: 8/10 ✅, 0/10 ⚠️, 2/10 ❌**

### Kluczowe odkrycia Batch 17

1. **Phone with spaces normalized** — "501 222 333" correctly parsed and stored.
2. **First name + city search works** — "Bartek Warszawa" → Bartek Wojcik found without ambiguity.
3. **Multi-product (legitimate two products)** — "pompa ciepła i PV" correctly parsed as two separate products.
4. **Natural language status mapping** — "złożył rezygnację" → "Rezygnacja z umowy" ✅.
5. **"za 3 dni" date arithmetic correct** — 12.04 + 3 = 15.04 ✅ (even though wrong client matched).
6. **Dopisać with source extraction** — "z polecenia" → Źródło: polecenie.
7. **R4 conflict with address** — duplicate shows existing client's address (Piłsudskiego 12) for disambiguation.
8. **bug-E6-1 systemic** — 7th confirmation of wrong client substitution in add_meeting.
9. **bug-E2-1 persistent** — show_day_plan still can't parse day names ("poniedziałek").

### Batch 18 (10 testów) — 12.04.2026, 10:42-10:48

| # | Input | Wynik | Uwagi |
|---|-------|-------|-------|
| E18-T1 | add_meeting "Marcin Kowalski Gdańsk jutro o 11 na ul. Długa 5" | ❌ FAIL | bug-E6-1 (8th confirm): "Marcin Kowalski Gdańsk" → matched "Jan Kowalski". Address "Gdańsk, ul. Długa 5" extracted correctly. Date "jutro"=13.04 ✅ |
| E18-T2 | add_client "Ewa Sikora Wrocław ewa.sikora@gmail.com PV" | ✅ PASS | Email-only (no phone) works. Email extracted, phone in Brakuje. 3-button R1 |
| E18-T3 | Rapid-fire: "pokaż Bartek Wojcik Warszawa" then 1s later "pokaż Michał Grabowski Kielce" | ✅ PASS | Both messages processed sequentially, both read-only cards displayed correctly. No race condition |
| E18-T4 | "zmień status Kowalski na Spotkanie umówione" → disambiguation → click Jan Kowalski | ❌ FAIL | bug-E10-4 (4th confirm): Intent loss after disambiguation. Shows read-only show_client card, NOT change_status mutation card |
| E18-T5 | add_meeting "Bartek Wojcik Warszawa pojutrze o 16:30" | ✅ PASS | "pojutrze" = 14.04.2026 (wtorek) ✅. Correct client. 16:30 ✅. 3-button R1 |
| E18-T6 | Whitespace-only message "   " | ✅ PASS | Telegram blocks empty/whitespace messages at client level. Bot never receives them |
| E18-T7 | add_client "Krzysztof Aleksandrowicz-Wójcik Nowy Sącz PV 501999888" | ✅ PASS | Hyphenated double-barrel last name + two-word city "Nowy Sącz" both handled perfectly |
| E18-T8 | add_meeting "Bartek Wojcik Warszawa jutro o 10 na 2 godziny" | ✅ PASS | Custom duration "2 godziny" → 120 min ✅. Correct client. Date+time correct |
| E18-T9 | "odśwież kolumny" | ✅ PASS | Admin command works. Shows 17 columns including blank one (Krok 0 not done). "ID kalendarza" still old name |
| E18-T10 | "pokaż klienta Mariusz Kalamaga Piaseczno" (wrong city) | ⚠️ PARTIAL | Client found by name (ignoring city mismatch). bug-E5-1: "Data następnego kroku: 2026-04-14" ISO format |

**Wynik Batch 18: 7/10 ✅, 1/10 ⚠️, 2/10 ❌**

### Kluczowe odkrycia Batch 18

1. **bug-E6-1 systemic** — 8th confirmation. "Marcin Kowalski Gdańsk" → "Jan Kowalski". Fuzzy matcher ignores first name entirely.
2. **bug-E10-4 systemic** — 4th confirmation. change_status intent ALWAYS lost after disambiguation.
3. **Hyphenated double-barrel names work** — "Aleksandrowicz-Wójcik" parsed perfectly.
4. **Two-word cities work** — "Nowy Sącz" handled correctly.
5. **Custom duration "2 godziny" = 120 min** — correctly parsed.
6. **Fuzzy search ignores city mismatch** — "Piaseczno" when actual is "Warszawa", but name match was unique so OK.
7. **bug-E5-1 persistent** — ISO date in "Data następnego kroku" field confirmed 2nd time.

### Batch 19 (10 testów) — 12.04.2026, 10:49-10:55

| # | Input | Wynik | Uwagi |
|---|-------|-------|-------|
| E19-T1 | "co mam dziś" | ✅ PASS | show_day_plan "dziś" → "Brak spotkań na dziś" (Sunday, correct). Alternate phrasing works |
| E19-T2 | "co mam jutro" | ✅ PASS | show_day_plan "jutro" → rich plan: 12:00 Grabowski Kielce + 15:00 Kalamaga Warszawa. Matches Calendar |
| E19-T3 | add_client "Piotr Adamski Lublin PV 10kW dach płaski południowy 505666777" | ✅ PASS | Tech specs "10kW dach płaski południowy" → Notatki. Product "PV" separate. Phone extracted |
| E19-T4 | add_meeting "Bartek Wojcik Warszawa jutro" (no time) | ✅ PASS | Correctly rejected: "Nie rozpoznałem daty lub godziny spotkania." Helpful example provided |
| E19-T5 | add_client "Zofia Kamińska Rzeszów pompa ciepła z Facebooka 508222111" | ✅ PASS | "z Facebooka" → Źródło: Facebook. All fields extracted correctly |
| E19-T6 | "Bartek Wojcik Warszawa podpisał umowę" | ✅ PASS | "podpisał umowę" → change_status "Podpisane". Transition "Rezygnacja z umowy → Podpisane" shown |
| E19-T7 | add_meeting "Grabowskim Kielce w czwartek o 14" | ✅ PASS | Day name "czwartek" → 16.04.2026 ✅. Declined form "Grabowskim" → Michał Grabowski. Confirms add_meeting parses day names |
| E19-T8 | "zmień status Michał Grabowski Kielce na Oferta wysłana" | ✅ PASS | Status "Oferta wysłana" correctly parsed. Client found. 3-button mutation card |
| E19-T9 | "spotkanie z Grabowskim Kielce się odbyło" | ❌ FAIL | NEW bug-E19-9: "się odbyło" → "Zamontowana" instead of "Spotkanie odbyte". Wrong status mapping |
| E19-T10 | add_client "Marek Zieliński Kraków ul. Szewska 12/4 PV 504555666 marek@wp.pl" | ✅ PASS | Apartment number "12/4" in address extracted correctly. All 5 fields parsed in one message |

**Wynik Batch 19: 9/10 ✅, 0/10 ⚠️, 1/10 ❌**

### Kluczowe odkrycia Batch 19

1. **NEW bug-E19-9** — "się odbyło" mapped to "Zamontowana" instead of "Spotkanie odbyte". AI classifier error on natural language status.
2. **show_day_plan "jutro" rich data** — shows meeting details: client, location, phone, product, next step.
3. **add_meeting rejects missing time** — clean Polish error message with helpful example.
4. **add_meeting parses day names** — "w czwartek" = 16.04 ✅ (unlike show_day_plan which can't).
5. **Address with apartment number** — "ul. Szewska 12/4" correctly extracted.
6. **Tech specs to Notatki** — "10kW dach płaski południowy" routed correctly.
7. **change_status from→to transition** — "Rezygnacja z umowy → Podpisane" shown when from-status exists in DB.

### Batch 20 (10 testów) — 12.04.2026, 10:56-11:03

| # | Input | Wynik | Uwagi |
|---|-------|-------|-------|
| E20-T1 | "zmień status Bartek Wojcik Warszawa na Nieaktywny" | ✅ PASS | "Nieaktywny" correctly parsed. Transition "Rezygnacja z umowy → Nieaktywny" shown. 3-button R1 |
| E20-T2 | "nowy lead Karol Borkowski Białystok pompa ciepła z OLX 507333222" | ✅ PASS | "nowy lead" phrasing classified as add_client. "z OLX" → Źródło: OLX. All fields correct |
| E20-T3 | "jak przekonać klienta do pompy ciepła?" | ✅ PASS | General OZE question answered in Polish. Mentions savings, gas independence, Czyste Powietrze program |
| E20-T4 | "zmień status Michał Grabowski Kielce na Nowy lead" | ✅ PASS | "Nowy lead" correctly parsed. Mutation card correct. 3-button R1 |
| E20-T5 | "plan na 20 kwietnia" | ❌ FAIL | bug-E2-1: Explicit date "20 kwietnia" ignored → "Brak spotkań na dziś." Defaults to today |
| E20-T6 | add_meeting "Bartek Wojcik Warszawa za godzinę" | ⚠️ PARTIAL | "za godzinę" not parsed as valid time. Clean rejection. Limitation — parser expects explicit date+time |
| E20-T7 | "dodaj Agnieszka Witkowska Toruń magazyn energii ze strony internetowej 503444555" | ✅ PASS | "ze strony internetowej" → Źródło: strona internetowa. "dodaj" without "klienta" classified correctly |
| E20-T8 | "Mariusz Kalamaga Warszawa ma umówione spotkanie" | ⚠️ PARTIAL | Classified as add_meeting not change_status. "spotkanie" keyword overrides status intent. Edge case |
| E20-T9 | add_client minimal → Dopisać phone → Dopisać product (double Dopisać) | ✅ PASS | Double Dopisać works! Card rebuilt twice, Brakuje list progressively reduced |
| E20-T10 | add_client "Rafał Pawłowski Świnoujście PV 506777888" | ✅ PASS | Polish diacritics "Świnoujście" (Ś, ś, ć) handled perfectly |

**Wynik Batch 20: 7/10 ✅, 2/10 ⚠️, 1/10 ❌**

### Kluczowe odkrycia Batch 20

1. **Double Dopisać confirmed** — can Dopisać twice in sequence, card rebuilds each time.
2. **"nowy lead" / "dodaj"** — alternate phrasings for add_client correctly classified.
3. **Source extraction robust** — "z OLX", "ze strony internetowej" both extracted to Źródło.
4. **All 9 statuses tested** — Nowy lead ✅, Spotkanie umówione ✅, Oferta wysłana ✅, Podpisane ✅, Zamontowana ✅, Rezygnacja z umowy ✅, Nieaktywny ✅, Odrzucone ✅. Only "Spotkanie odbyte" had wrong mapping (bug-E19-9).
5. **"za godzinę" limitation** — relative time from now not supported. Clean rejection.
6. **Ambiguous intent edge case** — "ma umówione spotkanie" classified as add_meeting not change_status.

### Batch 21 (10 testów) — 12.04.2026, 11:05-11:15

| # | Test | Wynik | Szczegóły |
|---|------|-------|-----------|
| E21-T1 | add_client Zapisać → commit to Sheets | ✅ | "Test Sesja-E Testowo PV 500000001" → Zapisane → R7 prompt → Anuluj/nic → verified row 24 in Sheets |
| E21-T2 | "notatka [client]: [text]" | ❌ | "notatka Jan Kowalski Warszawa: rozmowa telefoniczna..." → R5 POST-MVP banner. add_note IS MVP intent #3 |
| E21-T3 | "dodaj notatkę do [client]: [text]" | ⚠️ | Same R5 banner. Consistent with E21-T2. May be expected if add_note not deployed in A-C |
| E21-T4 | change_status after disambiguation | ❌ | "zmień status Jan Kowalski Warszawa na podpisał umowę" → disambiguation (bug-E10-2) → click correct client → read-only show_client card (bug-E10-4 5th time) |
| E21-T5 | show_client phone search "pokaż klienta 602345678" | ✅ | Found 3 clients sharing same phone → correct disambiguation |
| E21-T6 | add_meeting DD.MM date "18.04 o 14:00" | ✅ | 18.04.2026 (sobota) 14:00, 60 min, Miejsce: Kielce ✅. bug-E1-3 text remnant noted |
| E21-T7 | show_day_plan "plan na 18 kwietnia" | ❌ | "Brak spotkań na dziś." — defaulted to today (12.04) not 18.04. bug-E2-1 confirmed again |
| E21-T8 | add_client with email | ✅ | Anna Wiśniewska Kraków pompa ciepła 601222333 anna.w@gmail.com — all fields parsed perfectly |
| E21-T9 | show_client first-name-only "Mariusz" | ✅ | Found 3 Mariusz clients: Krzywinski×2, Kalamaga — correct disambiguation |
| E21-T10 | add_client with source "z polecenia od sąsiada" | ✅ | Źródło: Polecenie (sąsiad) — NLP source extraction works |

**Wynik: 6/10 ✅, 1/10 ⚠️, 3/10 ❌**

### Kluczowe odkrycia Batch 21

1. **add_client Zapisać → Sheets commit verified** — data confirmed in Google Sheets row 24 (first end-to-end write verification).
2. **R7 next_action_prompt after add_client** — fires correctly, "Anuluj/nic" dismisses cleanly.
3. **add_note triggers R5 on A-C code** — both "notatka" and "dodaj notatkę" phrasings. May be expected (add_note implemented in Sesja D, not deployed).
4. **bug-E10-4 confirmed 5th time** — change_status intent lost after disambiguation → read-only card.
5. **bug-E2-1 confirmed again** — "18 kwietnia" ignored by show_day_plan, defaults to today.
6. **Phone search with shared number** — 3 clients with 602345678, correctly disambiguated.
7. **Source extraction "z polecenia od sąsiada"** → "Polecenie (sąsiad)" — smart NLP.
8. **"Testowo" parsed as name not city** — parser couldn't distinguish city from identifier without explicit prefix.

### Batch 22 (10 testów) — 12.04.2026, 11:17-11:27

| # | Test | Wynik | Szczegóły |
|---|------|-------|-----------|
| E22-T1 | change_status unique client (no disambiguation) | ✅ | "Radek Sikorski Radom na oferta wysłana" → direct match, Status: → Oferta wysłana, R1 card |
| E22-T2 | add_client with address "ul. Polna 7/3" | ✅ | Kamila Zając, ul. Polna 7/3, Poznań — address extracted, Adres+Miasto not in Brakuje |
| E22-T3 | add_meeting "za 5 dni o 10:30" | ✅ | 12+5=17.04.2026 (piątek) 10:30 Radom — correct arithmetic |
| E22-T4 | show_client misspelled "Krzystof Wojcik Lublin" | ✅ | → Krzysztof Wojcik found directly, full card with all fields. bug-E5-1 ISO date confirmed |
| E22-T5 | add_meeting location override "w biurze ul. Marszałkowska 100 Warszawa" | ✅ | Miejsce: biuro ul. Marszałkowska 100 Warszawa (not client's city Legionowo). Day name "piątek" → 17.04 |
| E22-T6 | show_client non-existent "Zbigniew Stonoga Katowice" | ❌ | "Nie mam Zbigniew Stonoga. Chodziło o Zbigniew Nowak z Piaseczno?" + mutation buttons. Wrong fuzzy match + inappropriate buttons on show_client |
| E22-T7 | add_client duplicate R4 (Zbigniew Nowak Piaseczno PV) | ✅ | ⚠️ "Masz już Zbigniew Nowak" + 2-button [Dopisz do istniejącego][Utwórz nowy wpis] |
| E22-T8 | show_day_plan "co mam dziś w planie" | ✅ | Correctly classified, "dziś" parsed. "Brak spotkań na dziś." |
| E22-T9 | change_status Zapisać full flow (Bartek Wojcik) | ✅ | Rezygnacja z umowy → Spotkanie umówione. Commit confirmed. R7 not firing = expected (Sesja D feature) |
| E22-T10 | add_client "fotowoltaika" synonym + "z internetu" source | ✅ | Ewa Kowalczyk Gdynia, PV (fotowoltaika→PV), Źródło: Internet, R1 card |

**Wynik: 9/10 ✅, 0/10 ⚠️, 1/10 ❌**

### Kluczowe odkrycia Batch 22

1. **change_status works without disambiguation** — unique client "Radek Sikorski Radom" matched directly. Full flow: card→Zapisać→commit.
2. **Address with apartment "ul. Polna 7/3"** correctly extracted into Adres field.
3. **"za 5 dni" arithmetic** — 12+5=17 correctly calculated.
4. **Location override in add_meeting** — "w biurze ul. Marszałkowska 100 Warszawa" used instead of client's city.
5. **show_client non-existent bug** — wrong fuzzy suggestion "Stonoga"→"Nowak" (completely unrelated names) + mutation keyboard on show_client intent. New aspect of bug-E10-2.
6. **R4 duplicate conflict detection** — shows existing product (Pompa ciepła) when PV sent, 2-button choice.
7. **change_status Zapisać confirmed** — status actually updated in Sheets: Rezygnacja z umowy → Spotkanie umówione.
8. **R7 correctly not firing** after change_status on A-C code (Sesja D feature).
9. **"fotowoltaika"→PV** synonym and **"z internetu"→Internet** source extraction both work.

### Batch 23 (10 testów) — 12.04.2026, 11:28-11:42

| # | Test | Wynik | Szczegóły |
|---|------|-------|-----------|
| E23-T1 | add_meeting Zapisać → Calendar commit | ✅ | Michał Grabowski Kielce, poniedziałek 16:00, ul. Kielecka 5. Calendar entry created, visible in Google Calendar |
| E23-T2 | show_day_plan "jutro" after new meeting | ✅ | 3 meetings shown including newly created one. Rich data: client, address, phone, product, next step |
| E23-T3 | add_client "PV + Magazyn energii" compound product | ⚠️ | Parsed as "PV, Magazyn energii" (comma-separated) instead of "PV + Magazyn energii". Known bug-E1-9 |
| E23-T4 | edit_client → R5 POST-MVP banner | ✅ | "edytuj klienta" → "Ta funkcja jest w przygotowaniu. Niedługo dostępna." |
| E23-T5 | Next step extraction "zadzwonić w poniedziałek" | ✅ | Następny krok: zadzwonić + Data następnego kroku extracted correctly |
| E23-T6 | Dopisać with phone+email, card rebuilt | ✅ | Phone 507222111 + email agnieszka.wilk@wp.pl merged, Brakuje list updated |
| E23-T7 | Meeting overlap detection | ✅ | Conflicting meeting name shown with ⚠️ warning |
| E23-T8 | change_status "spotkanie odbyte" direct name | ✅ | "Spotkanie odbyte" correctly parsed from natural language |
| E23-T9 | Rapid-fire: add_client + show_client (0s gap) | ❌ | Both messages processed, BUT show_client "pokaż klienta Michał Grabowski Kielce" returned MUTATION card with [Zapisać][Dopisać][Anulować] instead of read-only display. **NEW BUG: show_client misclassified when pending add_client exists** (bug-E23-9) |
| E23-T10 | Compound add_meeting (date+time+address+context) | ⚠️ | "umów spotkanie z Karol Nowak Piaseczno w czwartek o 10:00 przy ul. Słonecznej 5 żeby omówić fotowoltaikę na dach płaski" → correctly parsed date (16.04 czwartek), time (10:00), address (ul. Słoneczna 5, Piaseczno). But: old "tak/nie" text remnant (bug-E1-3), context "fotowoltaikę na dach płaski" not captured as meeting note |

**Wynik: 7/10 ✅, 2/10 ⚠️, 1/10 ❌**

### Kluczowe odkrycia Batch 23

1. **add_meeting Calendar commit verified** — meeting created in Google Calendar, visible next day in show_day_plan.
2. **show_day_plan "jutro" works with rich data** — shows meeting with client name, address, phone, product, next step.
3. **NEW BUG bug-E23-9**: show_client returns mutation card (Zapisać/Dopisać/Anulować) instead of read-only display when there's a pending add_client from a rapid-fire previous message. The concurrent pending state contaminates the second intent.
4. **Compound add_meeting parsing excellent** — day name, time, full address all extracted from natural language. But contextual notes ("żeby omówić fotowoltaikę na dach płaski") not captured as meeting note.
5. **"spotkanie odbyte" direct status name** correctly parsed by change_status.
6. **bug-E1-9 confirmed again** — "PV + Magazyn energii" → "PV, Magazyn energii".

---

## Podsumowanie Sesji E (23 batchy, 228 testów)

**Łączne wyniki:**
- Batch 1: 8/10 ✅, 2/10 ⚠️
- Batch 2: 7/10 ✅, 1/10 ⚠️, 2/10 ❌
- Batch 3: 7/9 ✅, 2/9 ❌
- Batch 4: 7/9 ✅, 2/9 ⚠️
- Batch 5: 8/10 ✅, 1/10 ⚠️, 1/10 ❌
- Batch 6: 6/10 ✅, 0/10 ⚠️, 3/10 ❌
- Batch 7: 8/10 ✅, 1/10 ⚠️, 0/10 ❌
- Batch 8: 9/10 ✅, 0/10 ⚠️, 0/10 ❌
- Batch 9: 8/10 ✅, 0/10 ⚠️, 2/10 ❌
- Batch 10: 5/10 ✅, 2/10 ⚠️, 3/10 ❌
- Batch 11: 4/10 ✅, 2/10 ⚠️, 4/10 ❌
- Batch 12: 8/10 ✅, 0/10 ⚠️, 2/10 ❌
- Batch 13: 6/10 ✅, 1/10 ⚠️, 2/10 ❌
- Batch 14: 7/10 ✅, 2/10 ⚠️, 1/10 ❌
- Batch 15: 10/10 ✅, 0/10 ⚠️, 0/10 ❌ 🏆
- Batch 16: 4/10 ✅, 2/10 ⚠️, 4/10 ❌
- Batch 17: 8/10 ✅, 0/10 ⚠️, 2/10 ❌
- Batch 18: 7/10 ✅, 1/10 ⚠️, 2/10 ❌
- Batch 19: 9/10 ✅, 0/10 ⚠️, 1/10 ❌
- Batch 20: 7/10 ✅, 2/10 ⚠️, 1/10 ❌
- Batch 21: 6/10 ✅, 1/10 ⚠️, 3/10 ❌
- Batch 22: 9/10 ✅, 0/10 ⚠️, 1/10 ❌
- Batch 23: 7/10 ✅, 2/10 ⚠️, 1/10 ❌

### Batch F-T (8 testów, fuzzy fix) — 12.04.2026, 17:30-17:55

Testy po commit `b40268b` (fuzzy match fix: `_fuzzy_match` word-to-word, `_first_name_ok` guard).

| # | Test | Wynik | Notatka |
|---|------|-------|---------|
| F-T1 | add_meeting "Radek Sikorski Radom jutro o 10" | ✅ PASS | Bezpośredni match, brak zbędnej disambiguation |
| F-T2 | add_meeting "Jan Mazur Radom piątek 11:00" | ✅ PASS | Bezpośredni match, poprawny klient |
| F-T3 | add_meeting "Ewa Mazur Szczecin środa 14:00" | ✅ PASS | "Nie mam 'Ewa Mazur Szczecin'" — poprawne (nie istnieje) |
| F-T4 | show_client "Tomek Zieliński Lublin" | ⚠️ PARTIAL | Guard blokuje złego klienta (✅), ale wynik: disambiguation z 2 Lublin klientami zamiast direct match |
| F-T5 | change_status "Radek Sikorski Radom → Umówione spotkanie" | ✅ PASS | Direct match, mutation card poprawna |
| F-T6 | add_note "Ewa Mazur Szczecin: interesuje się PV" | ⚠️ PARTIAL | Guard blokuje złego klienta (✅), ale "Nie znaleziono klienta" — nie szuka dalej |
| F-T7 | add_note "Marcin Kowalski Gdańsk: oferta wysłana" | ✅ PASS | Direct match, mutation card z notatką |
| F-T8 | show_client "Jan Kowalski Warszawa" | ✅ PASS | Direct match, read-only card |

**Wynik F-T: 6/8 ✅, 2/8 ⚠️ (0 ❌)**

### Batch F2 (8 testów, regresja + nowe) — 12.04.2026, 18:00-18:11

| # | Test | Wynik | Notatka |
|---|------|-------|---------|
| F2-T1 | add_note "Jan Kowalski Warszawa" via disambiguation (3 Warszawa) | ❌ FAIL | bug-E10-4: intent loss → show_client card zamiast add_note mutation |
| F2-T2 | add_note "Radek Sikorski Radom" exact match | ❌ FAIL | Zbędna disambiguation (3 Radom) + bug-E10-4: intent loss → show_client card |
| F2-T3 | change_status "Marcin Kowalski Gdańsk → Umówione spotkanie" + R7 | ✅ PASS | Direct match, 3-button card, R7 prompt pojawił się, cancel działa |
| F2-T4 | add_client "Tomasz Nowicki Łódź" + Zapisać + R7 + cancel | ✅ PASS | Pełny flow: parsed 4 pola, Zapisane, R7 prompt, Anulowane |
| F2-T5 | show_day_plan "co mam jutro" | ✅ PASS | 3 spotkania poprawnie wyświetlone, read-only (brak przycisków). Minor: brak daty w nagłówku |
| F2-T6 | add_meeting "Piotr Zieliński Radom środa 14:00" + Zapisać | ✅ PASS | Direct match, data 15.04.2026 (środa) poprawna, "Spotkanie dodane do kalendarza", brak R7 (poprawne per spec) |
| F2-T7 | R4 duplicate "Jan Kowalski Warszawa" | ⚠️ PARTIAL | Duplikat wykryty (✅), ale R1 3-button zamiast R4 2-button card. Funkcjonalnie OK |
| F2-T8 | add_client compound (8 pól w jednej wiadomości) | ✅ PASS | Anna Wiśniewska Kraków — name, address, city, product, phone, email, source wyekstrahowane poprawnie |

**Wynik F2: 5/8 ✅, 1/8 ⚠️, 2/8 ❌**

### Batch F3 (8 testów, nowe scenariusze) — 12.04.2026, 18:30-18:39

| # | Test | Wynik | Notatka |
|---|------|-------|---------|
| F3-T1 | add_note Dopisać flow (Marcin Kowalski Gdańsk) | ❌ FAIL | Dopisać na add_note nie działa — canceluje pending note, pyta od nowa (bug-F3-1) |
| F3-T2 | add_note Zapisać → verify no R7 | ✅ PASS | "Notatka dodana." + brak R7 — poprawne per spec (zamknięty akt) |
| F3-T3 | change_status → Nowy lead (reset) | ✅ PASS | from→to: "Umówione spotkanie → Nowy lead", 3-button card |
| F3-T4 | show_client by phone ("kto ma numer 5555555555") | ❌ FAIL | "Nie mam dostępu do Twoich danych" — API error lub misclassification (bug-E2-7 variant) |
| F3-T5 | add_meeting "za tydzień" | ✅ PASS | "za tydzień" → 19.04.2026 (niedziela) poprawne (+7 dni), direct match Bartek Wojcik |
| F3-T6 | general_question "jakie produkty oferujemy" | ⚠️ PARTIAL | Classified OK ale "Nie mam dostępu do asortymentu — sprawdź Drive". Powinno odpowiedzieć z OZE context |
| F3-T7 | add_client minimal + Dopisać (phone+email) | ✅ PASS | Karta przebudowana z Tel+Email, "Brakuje" lista zaktualizowana, 3-button R1 |
| F3-T8 | Anulować mid-flow on add_meeting | ✅ PASS | One-click cancel, natychmiastowe "Anulowane.", brak pętli "Na pewno?" |

**Wynik F3: 4/8 ✅, 1/8 ⚠️, 2/8 ❌ (+ 1 nowy bug)**

- Batch F-T: 6/8 ✅, 2/8 ⚠️, 0/8 ❌
- Batch F2: 5/8 ✅, 1/8 ⚠️, 2/8 ❌
- Batch F3: 4/8 ✅, 1/8 ⚠️, 2/8 ❌
- Batch H: 4/6 ✅, 2/6 ⚠️, 0/6 ❌
- Batch I: 5/5 ✅, 0/5 ⚠️, 0/5 ❌
- Batch J: 2/5 ✅, 2/5 ⚠️, 1/5 ❌
- Batch K: 3/5 ✅, 0/5 ⚠️, 2/5 ❌
- Batch L: 3/3 ✅, 0/3 ⚠️, 0/3 ❌
- Batch M: 4/4 ✅, 0/4 ⚠️, 0/4 ❌ 🏆 (retest po restarcie bota)
- Batch N: 4/4 ✅, 0/4 ⚠️, 0/4 ❌ 🏆
- Batch O: 4/4 ✅, 0/4 ⚠️, 0/4 ❌ 🏆
- Batch P: 5/8 ✅, 1/8 ⚠️, 2/8 ❌
- Batch P2: 4/5 ✅, 0/5 ⚠️, 1/5 ❌
- Batch P3: 3/3 ✅, 0/3 ⚠️, 0/3 ❌ 🏆
- **Razem: 221/304 ✅ (73%), 31/304 ⚠️ (10%), 47/304 ❌ (15%)**

**Nowe bugi znalezione w Sesji E+F (20):**

| ID | Priorytet | Objaw |
|----|-----------|-------|
| bug-E2-1 | HIGH | show_day_plan nie parsuje: nazwy dni ("poniedziałek"), explicit dates ("15 kwietnia"). Tylko "dziś"/"jutro" działają |
| bug-E2-5 | HIGH | Bot akceptuje dowolny status bez walidacji whitelist |
| bug-E3-3 | HIGH | Temporal guard nie działa — past dates accepted |
| bug-B2-1 | HIGH | Klimatyzacja nadal akceptowana (potwierdzone, nie deployment lag) |
| bug-E6-1 | HIGH | Bot silently substitutes wrong client (Tomek→Piotr Zieliński) — no disambiguation |
| bug-E9-6 | HIGH | Flow state leak — disambiguation state persists through intervening messages, causes wrong client card |
| bug-E9-9 | HIGH | "statusy" returns stale raw Python list with Negocjacje, missing Zamontowana/Nieaktywny/Rezygnacja z umowy (7/9) |
| bug-E10-2 | HIGH | Fuzzy search too broad — exact "Jan Kowalski Warszawa" returns "Jan Nowak Piaseczno". add_meeting silently picks first/wrong result |
| bug-E10-4 | HIGH | Intent loss after disambiguation in change_status — drops mutation flow, shows only read-only card |
| bug-E10-7 | HIGH | add_meeting fuzzy match ignores first name — "Ewa Mazur Szczecin" → "Jan Mazur" (4th wrong-client case) |
| bug-E1-3 | ✅ NAPRAWIONE (Sesja G) | add_meeting card body — stary tekst "tak/nie" usunięty |
| bug-E1-9 | ✅ NAPRAWIONE (Sesja I, potwierdzone I-T2) | "PV + Magazyn energii" jako jeden compound produkt |
| bug-E2-7 | ⚠️ CZĘŚCIOWO (Sesja H) | Classifier naprawiony (show_client nie add_client). Ale phone search zbyt szeroki — exact "600123456" zwrócił 7 klientów zamiast exact match |
| bug-E5-1 | MEDIUM | "Data następnego kroku" w show_client w formacie ISO zamiast DD.MM.YYYY |
| bug-E19-9 | ✅ NAPRAWIONE (Sesja I, potwierdzone I-T1) | "się odbyło" → "Spotkanie odbyte" (not Zamontowana) |
| bug-E14-7 | ✅ NAPRAWIONE (Sesja I, potwierdzone I-T5) | "telefoniczne" → Miejsce: "telefonicznie" (not client city) |
| bug-E23-9 | ✅ NAPRAWIONE (Sesja H, potwierdzone H-T4) | show_client during pending add_client → "⚠️ Anulowane." + clean re-process |
| bug-E4-7 | ✅ NAPRAWIONE (Sesja I, potwierdzone I-T3) | Same-status → "Status klienta X jest już: Y." (info message, no card) |
| bug-F2-2 | ✅ NAPRAWIONE (Sesja I, potwierdzone I-T1+I-T4) | Exact name match bypasses disambiguation (add_note + change_status) |
| bug-F3-1 | ✅ NAPRAWIONE (Sesja H) | `_route_pending_flow` — dodano `elif flow_type == "add_note"` |

**Co działa dobrze (potwierdzone 78 testami):**
- add_client parsing (compound messages, minimal data, diacritics, tech specs→Notatki)
- show_client (fuzzy search, misspellings, non-existent handling, disambiguation, first-name+city, no-diacritics)
- add_meeting commit (Calendar save, date format, location parsing, address extraction, "jutro" parsing)
- add_meeting validation (rejects missing time, defaults to today for time-only)
- change_status (correct transition display, correct routing from natural language)
- R4 duplicate detection (shows existing client info + 2-button choice)
- Dopisać flow (card rebuild with merged data, "Brakuje" update)
- One-click cancel (Anulować) — zero regressions across all 38 tests
- R5 POST-MVP banners (edit_client, filtruj, lejek, add_note stub)
- Classifier: ambiguous "ma nowy numer/telefon" → add_client (nie edit_client false-positive)
- Classifier: jawne "zmień/popraw" → edit_client R5 banner (poprawne)
- Multi-meeting parser: declined Polish names (genetyw→mianownik) — "Jana Nowaka"→"Jan Nowak", "Anny Kowalskiej"→"Anna Kowalska"
- show_client direct match z `_first_name_ok` guard (P-T7: "Jan Kowalski Warszawa" → direct card bez disambiguation)
- 3-button R1 keyboard — present on all mutation cards, consistent
- Classifier routing (Rezygnacja→change_status, general questions, gibberish)
- Date format DD.MM.YYYY (Dzień tygodnia) — consistent on mutation cards (ale nie na show_client → bug-E5-1)
- add_meeting "telefoniczne" parsed jako Miejsce correctly
- show_day_plan "jutro"/"dziś" relative dates working
- add_meeting "pojutrze" relative date parsed correctly
- Source field extraction ("z polecenia od sąsiada" → Źródło: polecenie od sąsiada)
- Long message (290 chars) NLP extraction — product, tech details→Notatki, source all correct
- "Magazyn energii" and "Pompa ciepła" parsed as single products correctly
- Email extraction from add_client messages (kamil.baran@gmail.com)
- add_meeting day-name parsing ("w piątek" → 17.04) — works! (unlike show_day_plan)
- Fuzzy city matching ("Waeszawa" → Warszawa)
- Gibberish input → clean "Co chcesz zrobić?" fallback
- Rapid-fire messages (1s gap) — no race conditions, sequential processing
- "pokaż plan" without date → defaults to today correctly
- change_status shows from→to transition when from-status exists
- Dopisać flow: card rebuild with multiple new fields (phone+address+email), Brakuje list updates
- Meeting time overlap detection with ⚠️ warning (shows conflicting meeting name)
- Address extraction in add_client ("ul. Główna 10" → Adres field)
- Full address as meeting location ("Kraków ul. Długa 15")
- "anuluj" without pending flow → clean "Anulowane." (no crash)
- Pure number input → "Co chcesz zrobić?" (not misclassified as phone/add_client)
- One-click cancel timing — immediate, no confirmation loop
- "fotowoltaika" synonym correctly mapped to "PV"
- Custom meeting duration "1.5 godziny" → 90 min
- R7 next_action_prompt po change_status commit (free-text + "❌ Anuluj / nic" button)
- R7 next_action_prompt po add_client commit (free-text + cancel)
- R7 correctly skipped after add_meeting (meeting itself defines next contact)
- R7 "❌ Anuluj / nic" → clean "Anulowane." closure
- Fuzzy match fix (b40268b): word-to-word matching blocks wrong-client substitution
- add_client compound 8-field parsing (name, city, phone, email, address, product, source)
- R4 duplicate detection functional (detects existing client, offers update)
- add_note Zapisać → no R7 (confirmed: zamknięty akt per spec)
- add_note direct match (Marcin Kowalski Gdańsk — no disambiguation needed)
- change_status from→to display with reverse transition (Umówione spotkanie → Nowy lead)
- "za tydzień" relative date → correct +7 days calculation
- add_client Dopisać flow: phone+email merged, Brakuje list updated correctly
- One-click cancel on add_meeting: immediate "Anulowane.", zero confirmation loops
- add_note full flow: extract note text, 3-button card, timestamp prefix
- change_status from→to transition display (Nowy lead → Spotkanie umówione)
- Disambiguation button-click → correct client card display
- add_client with email only (no phone) → email extracted, phone in Brakuje
- "za tydzień" relative date → correctly calculated +7 days
- "pompa ciepła" multi-word product parsed as single product
- R5 POST-MVP banners for edit_client AND lejek_sprzedażowy
- Sequential add_client operations — no state leak between cancel→new
- "pojutrze" relative date parsing in add_meeting
- "Magazyn energii" parsed correctly as product
- 8-field compound message parsed in one shot (name+city+product+phone+email+address+source+notes)
- /start command returns clean welcome message
- add_meeting "15 kwietnia" explicit date → 15.04.2026 (środa) ✅
- Non-existent client → clean "Nie mam X w bazie" (no crash, no false match)
- Natural language "podpisał umowę" → change_status Podpisane
- Bare last name "Nowak" → 5-client disambiguation with buttons
- "plan na dziś" → correct show_day_plan for today
- "odśwież kolumny" admin command works, shows column inventory
- Phone search "kto ma numer X" correctly routed (not add_client)
- "za 2 dni" relative date parsing in add_meeting → correctly calculated future date
- Emoji in message (🏠) doesn't break intent classification
- add_client with minimum data (name+city only) creates valid card
- "30 minut" custom duration correctly parsed in add_meeting
- Long gibberish (126 chars) → clean fallback, no crash or misclassification
- add_client full flow: save→R7 prompt→R7 cancel — all 3 steps work in sequence
- Miejsce auto-filled from client's city in add_meeting
- Polish declension handling ("Michała Grabowskiego z Kielc" genitive → Michał Grabowski Kielce)
- add_note correctly shows R5 POST-MVP banner on A-C deployed code
- "w środę" day name + address extraction in single add_meeting message
- change_status with direct status name "Spotkanie umówione" correctly parsed
- "anuluj" without pending flow → clean "Anulowane." (confirmed 2x)
- Rapid-fire 2 messages (0s gap) → both processed sequentially, correct results
- show_day_plan "jutro" shows rich meeting data (client, address, phone, product, next step)
- "pomoc" → clean fallback (no crash, correct handling of unknown command)
- Dopisać flow: card rebuild with phone+product merged, Brakuje list updates
- add_meeting → Zapisać → Calendar integration confirmed (meeting visible in Google Calendar)
- No R7 after add_meeting (correct per spec — meeting IS the next step)
- R4 duplicate detection with data conflict (different phone/product) → 2-button choice card
- Fuzzy city matching: "Kilece" → Kielce resolved
- Hyphenated name "Jean-Pierre" + umlaut "Müller" handled correctly
- "za tydzień" → +7 days correctly calculated
- Last-name-only declined form "Grabowskim" + misspelled city → correct client found
- All 3 R5 POST-MVP banners: edit_client, lejek_sprzedażowy, filtruj_klientów
- change_status "Odrzucone" — direct status name correctly parsed
- change_status "Zamontowana" — direct status name correctly parsed
- Non-existent client "Zenon Marciniak Bydgoszcz" → clean "Nie mam w bazie" (no false match)
- /start welcome message confirmed clean (2nd time)
- Bare last-name disambiguation "Kowalskiego" → correct 2-client list with buttons
- add_meeting overlap detection works — shows conflicting meeting name with ⚠️ warning (confirmed 2nd time)
- Phone with spaces "501 222 333" correctly normalized and parsed
- First name + city search "Bartek Warszawa" → correct client found (no last name needed)
- Two legitimate separate products "pompa ciepła i PV" correctly parsed as "Pompa ciepła, PV"
- Natural language "złożył rezygnację" → change_status "Rezygnacja z umowy"
- "za 3 dni" relative date arithmetic: 12.04 + 3 = 15.04 ✅
- Dopisać source extraction "z polecenia" → Źródło: polecenie
- R4 duplicate conflict shows existing address for disambiguation (Piłsudskiego 12)
- "ile mam klientów" → POST-MVP R5 banner (stats feature correctly classified)
- add_meeting Zapisać → Calendar commit verified (meeting visible in Google Calendar, confirmed 2nd time)
- show_day_plan "jutro" shows newly created meeting with rich data (confirmed 2nd time)
- edit_client → R5 POST-MVP banner (confirmed 2nd time)
- Next step extraction "zadzwonić w poniedziałek" → Następny krok + Data następnego kroku
- Dopisać with phone+email merged → card rebuilt, Brakuje updated (confirmed 3rd time)
- Meeting overlap detection with ⚠️ warning (confirmed 3rd time)
- "spotkanie odbyte" direct status name correctly parsed by change_status
- Compound add_meeting: day name + time + full address all extracted from single natural language message
- Email-only add_client (no phone) → email extracted, phone in Brakuje correctly
- Rapid-fire 2 messages (1s gap) → both processed sequentially (confirmed 3rd time)
- Hyphenated double-barrel last name "Aleksandrowicz-Wójcik" handled perfectly
- Two-word city "Nowy Sącz" correctly parsed
- Custom duration "2 godziny" → 120 min in add_meeting
- "odśwież kolumny" admin command shows column inventory (confirmed 2nd time)
- "pojutrze" relative date → +2 days correctly calculated (confirmed 2nd time)
- Whitespace-only input blocked at Telegram level (never reaches bot)
- "co mam dziś" alternate phrasing → show_day_plan correctly classified
- "co mam jutro" → rich plan with meeting details (client, location, phone, product, next step)
- Technical specs "10kW dach płaski południowy" → Notatki field (confirmed 2nd time)
- add_meeting without time → clean rejection with helpful example "jutro o 14:00 z Kowalskim"
- "z Facebooka" source extraction → Źródło: Facebook
- "podpisał umowę" → change_status "Podpisane" with from→to transition display
- add_meeting "w czwartek" day name parsing → correct date (confirmed: add_meeting CAN parse day names)
- "Oferta wysłana" direct status name correctly parsed
- Address with apartment "ul. Szewska 12/4" correctly extracted in add_client
- 5-field compound message (name+city+address+product+phone+email) parsed in one shot
- "Nieaktywny" status correctly parsed with from→to transition
- "nowy lead" alternate phrasing → add_client (no "klienta" keyword needed)
- "dodaj" without "klienta" → add_client correctly classified
- General OZE sales question → contextual Polish answer (Czyste Powietrze program)
- "Nowy lead" status correctly parsed
- "z OLX" source extraction → Źródło: OLX
- "ze strony internetowej" source extraction → Źródło: strona internetowa
- Double Dopisać in sequence — card rebuilt twice, Brakuje progressively reduced
- Polish diacritics "Świnoujście" (Ś, ś, ć) handled perfectly
- 8 out of 9 pipeline statuses correctly parsed when used explicitly
- add_client Zapisać → data committed to Google Sheets (verified row 24 with name, phone, product)
- R7 next_action_prompt fires after add_client commit, "Anuluj/nic" dismisses cleanly
- Phone search "pokaż klienta [phone]" — finds all clients sharing same phone number, correct disambiguation
- add_meeting DD.MM date parsing "18.04 o 14:00" → 18.04.2026 (sobota) correctly
- add_client email parsing "anna.w@gmail.com" extracted into Email field
- First-name-only search "Mariusz" → 3-client disambiguation (Krzywinski×2, Kalamaga)
- Source extraction "z polecenia od sąsiada" → Źródło: Polecenie (sąsiad) — smart NLP extraction
- change_status unique client direct match (no disambiguation needed for "Radek Sikorski Radom")
- Address with apartment number "ul. Polna 7/3" correctly extracted into Adres field
- "za 5 dni" relative date arithmetic: 12+5=17.04.2026 (piątek) ✅
- add_meeting location override: custom "w biurze ul. Marszałkowska 100 Warszawa" instead of client city
- Misspelled name tolerance: "Krzystof Wojcik" → "Krzysztof Wojcik" (direct match)
- R4 duplicate with product conflict: existing Pompa ciepła vs new PV → 2-button choice card
- change_status Zapisać commit confirmed: Rezygnacja z umowy → Spotkanie umówione in Sheets
- "fotowoltaika" synonym → PV mapping (confirmed 2nd time)
- "z internetu" source extraction → Źródło: Internet
- add_note Dopisać flow: text appended correctly, card rebuilt with merged note (bug-F3-1 fix)
- Phone search "kto ma numer X" → show_client (not add_client) — classifier fixed (bug-E2-7)
- show_client during pending add_client → "⚠️ Anulowane." + clean re-process (bug-E23-9 fix)
- General question "jakie produkty oferujemy" → product list from agent knowledge, no Drive error (bug-F3-6 fix)
- General question "jakie są nasze statusy" → 9 statusów from agent knowledge, no Negocjacje
- "się odbyło" → change_status "Spotkanie odbyte" (not "Zamontowana") — bug-E19-9 fix
- "PV + Magazyn energii" → single compound product (not two) — bug-E1-9 fix
- Same-status no-op guard: "Status klienta X jest już: Y." — no mutation card (bug-E4-7 fix)
- add_note Zapisać → no R7 (confirmed M-T4 retest: zamknięty akt per spec — "Notatka dodana." i koniec, brak follow-up)
- change_status Zapisać → status committed + R7 fires with new format (confirmed M-T3 retest: "Co dalej — X (Y)?")
- R7 new format "Co dalej — Name (City)?" with em-dash + parentheses (confirmed M-T1+M-T3 retest: bug-A1-4 fix)
- Calendar title "Spotkanie — Name" with em-dash (confirmed M-T2 retest: Bug #10 fix)
- Exact name match bypasses disambiguation in add_note (Radek Sikorski Radom, multiple Radom clients) — bug-F2-2 fix
- Exact name match bypasses disambiguation in change_status (Radek Sikorski Radom) — bug-F2-2 fix
- "spotkanie telefoniczne" → Miejsce: "telefonicznie" (not client's city) — bug-E14-7 fix
- Text "tak" accepted as confirmation for phone search disambiguation (bot interprets free-text responses)
- Exact phone search: "kto ma numer 600123456" → direct Jan Kowalski card (fixed from 7-client disambiguation)
- Exact phone search: "pokaż klienta z numerem 510620730" → direct Michał Grabowski (fixed from "Nie mam... Chodziło o?")
- Klimatyzacja rejected from Produkt field — moved to Notatki (wording "Zainteresowany klimatyzacją")
- Mixed products "PV i klimatyzacja" → Produkt: "PV" only, klimatyzacja to Notatki

---

## Zadanie na Sesję E (oryginalne) — testy manualne Sesji D

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

### Naprawione w Sesji I (commit `6e97e62`, 12.04.2026)

| ID | Co naprawiono | Plik |
|----|---------------|------|
| bug-E19-9 | "się odbyło" → "Zamontowana" zamiast "Spotkanie odbyte" — dodano przykłady do `classify_intent`: "się odbyło / odwiedziłem / odbyłem" + WAŻNE rule | `claude_ai.py` |
| bug-E1-9 | "PV + Magazyn energii" parsowane jako dwa produkty — dodano explicit rule: "PV i/z magazynem / PV + magazyn" → "PV + Magazyn energii" (jeden produkt) | `claude_ai.py` |
| bug-E4-7 | Same-status no-op mutation card — dodano guard w `handle_change_status`: jeśli `old_status == new_status` → "Status klienta X jest już: Y." | `text.py` |
| bug-F2-2 | Exact name+city triggers unnecessary disambiguation — dodano `_find_exact_name_match` helper; w `handle_add_note` i `handle_change_status` exact full-name match bypasses disambiguation | `text.py` |
| bug-E14-7 | "spotkanie telefoniczne" adjective nie parsowane jako Miejsce — dodano rule do `extract_meeting_data`: "telefoniczne/telefonicznie/przez telefon" → location: "telefonicznie" | `claude_ai.py` |

### Testy do wykonania po deploy (Sesja I)

| # | Wiadomość | Oczekiwany wynik |
|---|-----------|-----------------|
| I-T1 | "spotkanie z Radkiem Sikorskim Radom się odbyło" | change_status → "Spotkanie odbyte" mutation card (nie Zamontowana) |
| I-T2 | add_client "Adam Baran PV + Magazyn energii" | Produkt: "PV + Magazyn energii" (jeden produkt, nie "PV, Magazyn energii") |
| I-T3 | "zmień status Michał Grabowski Kielce na Nowy lead" gdy status już jest "Nowy lead" | "Status klienta Michał Grabowski jest już: Nowy lead." (brak karty) |
| I-T4 | add_note "Radek Sikorski Radom: dzwonił" (przy wielu klientach z Radom) | Bezpośredni match Radek Sikorski bez disambiguation |
| I-T5 | "spotkanie telefoniczne z Marcin Kowalski Gdańsk jutro o 11" | add_meeting card: Miejsce: "telefonicznie" (nie "Gdańsk") |

### Wyniki Batch I (5 testów, bug-fix verification) — 12.04.2026, 20:37-20:51

| # | Test | Wynik | Notatka |
|---|------|-------|---------|
| I-T1 | "spotkanie z Radkiem Sikorskim Radom się odbyło" | ✅ PASS | change_status → "Spotkanie odbyte" (nie Zamontowana). bug-E19-9 fix potwierdzone. Bonus: exact match bez disambiguation (bug-F2-2 fix potwierdzone na change_status) |
| I-T2 | add_client "Adam Baran Poznań PV + Magazyn energii" | ✅ PASS | Produkt: "PV + Magazyn energii" — jeden compound produkt, nie dwa. bug-E1-9 fix potwierdzone |
| I-T3 | "zmień status Michał Grabowski Kielce na Nowy lead" (status już Nowy lead) | ✅ PASS | "Status klienta Michał Grabowski jest już: Nowy lead." — info message, brak karty mutacyjnej. bug-E4-7 fix potwierdzone |
| I-T4 | "notatka Radek Sikorski Radom: dzwonił" (wielu klientów z Radom) | ✅ PASS | Bezpośredni match "Radek Sikorski, Radom" → karta add_note bez disambiguation. bug-F2-2 fix potwierdzone na add_note |
| I-T5 | "spotkanie telefoniczne z Marcin Kowalski Gdańsk jutro o 11" | ✅ PASS | Miejsce: "telefonicznie" (nie Gdańsk). Data: 13.04.2026 (poniedziałek), Godzina: 11:00. bug-E14-7 fix potwierdzone |

**Wynik I: 5/5 ✅, 0/5 ⚠️, 0/5 ❌ — wszystkie bug-fixy z Sesji I potwierdzone!**

---

---

## Sesja J — ZAKOŃCZONA (12.04.2026)

### Naprawione w Sesji J (commit TODO, 12.04.2026)

| ID | Co naprawiono | Plik |
|----|---------------|------|
| bug-B2-1 | "klimatyzacja" deterministycznie odrzucana z Produkt — dodano `_filter_invalid_products` helper. Invalid products przenoszone do Notatki. Wywoływane w `handle_add_client` i Dopisać branch `_route_pending_flow` | `text.py` |
| bug-E2-7 (phone precision) | Phone search zbyt szeroki (fuzzy ratio 0.89 na 1-cyfrową różnicę) — dodano `_is_phone_query` + `_digits_only` helpers w `google_sheets.py`. `search_clients` używa exact digit matching dla phone queries (7+ cyfr). `handle_search_client` pomija "Chodziło o?" confirmation dla phone queries | `google_sheets.py`, `text.py` |

### Testy do wykonania po deploy (Sesja J)

| # | Wiadomość | Oczekiwany wynik |
|---|-----------|-----------------|
| J-T1 | add_client "Marcin Bąk Rzeszów klimatyzacja 505111222" | Produkt: "" (puste), Notatki: "Produkt nieobsługiwany: klimatyzacja". Karta BEZ "klimatyzacja" w Produkt |
| J-T2 | add_client "Jan Nowak Kraków PV i klimatyzacja 501222333" | Produkt: "PV", Notatki: "Produkt nieobsługiwany: klimatyzacja". Tylko PV zachowane |
| J-T3 | "kto ma numer 600123456" | show_client → dokładne wyniki (tylko klienci z tym numerem), NIE 7 klientów |
| J-T4 | "pokaż klienta z numerem 510620730" | Bezpośrednia karta Michała Grabowskiego — BEZ "Chodziło o?" pytania |
| J-T5 | bug-E9-6 retest: show_client "Kowalski" → disambiguation → następnie wpisz "Ala Wrocław" | Bot mówi "⚠️ Anulowane." + obsługuje "Ala Wrocław" jak nowe zapytanie (nie pokazuje Kowalskiego) |

### Wyniki Batch J (5 testów, bug-fix verification Sesja J) — 12.04.2026, 21:22-21:38

| # | Test | Wynik | Notatka |
|---|------|-------|---------|
| J-T1 | add_client "Marcin Bąk Rzeszów klimatyzacja 505111222" | ⚠️ PARTIAL | Produkt: puste ✅ (klimatyzacja odrzucona). Ale Notatki: "Zainteresowany klimatyzacją" zamiast spec "Produkt nieobsługiwany: klimatyzacja". Wording differs |
| J-T2 | add_client "Jan Nowak Kraków PV i klimatyzacja 501222333" | ⚠️ PARTIAL | Produkt: "PV" ✅ (tylko valid product zachowany). Notatki: "Zainteresowany również klimatyzacją" zamiast "Produkt nieobsługiwany: klimatyzacja". Core behavior poprawny, wording nie z spec |
| J-T3 | "kto ma numer 600123456" | ✅ PASS | Bezpośrednia karta Jan Kowalski — zero disambiguation! (w H-T2 było 7 klientów). Exact phone match fix potwierdzone |
| J-T4 | "pokaż klienta z numerem 510620730" | ✅ PASS | Bezpośrednia karta Michał Grabowski — BEZ "Nie mam... Chodziło o?" (w H-T3 było pytanie potwierdzające). Direct phone match fix potwierdzone |
| J-T5 | bug-E9-6 retest: "Kowalski" disambiguation → "Ala Wrocław" | ❌ FAIL | Brak "⚠️ Anulowane." — disambiguation state przetrwał. Bot wyświetlił Mariusz Kalamaga (Warszawa) — zupełnie wrong client, niezwiązany z "Ala Wrocław" ani z Kowalskim. **bug-E9-6 nadal aktywny** |

**Wynik J: 2/5 ✅, 2/5 ⚠️, 1/5 ❌**

---

## Sesja K — ZAKOŃCZONA (12.04.2026)

### Naprawione w Sesji K (commit `334667d`, 12.04.2026)

| ID | Co naprawiono | Plik |
|----|---------------|------|
| bug-E9-6 | **Root cause**: `_fuzzy_match` `v in q` check pozwala "Wrocław" (stored city, 1 słowo) matchować query "Ala Wrocław" (2 słowa), bo "wrocław" IS a substring of "ala wrocław". Po auto-cancel flow (else branch działa), re-processed "Ala Wrocław" znajdował Mariusza Kalamaga przez false city match. **Fix**: `v in q` teraz działa tylko gdy v ma >1 słowo LUB query ma 1 słowo. Zapobiega false-positive city-in-name-city-query | `shared/google_sheets.py` `_fuzzy_match` |
| bug-B2-1 (Notatki wording) | `_filter_invalid_products` teraz sprawdza też pole Notatki. Gdy LLM wpisze klimatyzację bezpośrednio do Notatki (zamiast Produkt), helper normalizuje do standardowego "Produkt nieobsługiwany: klimatyzacja" | `bot/handlers/text.py` `_filter_invalid_products` |

### Testy do wykonania po deploy (Sesja K)

| # | Wiadomość / kroki | Oczekiwany wynik |
|---|-----------|-----------------|
| K-T1 | bug-E9-6: "dodaj notatkę do Jana Kowalskiego: dzwonił" → disambiguation → wpisz "pokaż Michała Grabowskiego z Kielc" | "⚠️ Anulowane." + fresh routing → karta Michała Grabowskiego (albo "Nie mam..." jeśli nie istnieje) |
| K-T2 | J-T1 retest: add_client "Marcin Bąk Rzeszów klimatyzacja 505111222" | Produkt: puste, Notatki: "Produkt nieobsługiwany: klimatyzacja" (standard wording) |
| K-T3 | J-T2 retest: add_client "Jan Nowak Kraków PV i klimatyzacja 501222333" | Produkt: "PV", Notatki: "Produkt nieobsługiwany: klimatyzacja" |
| K-T4 | Regression: "pokaż Jan Kowalski Warszawa" | Karta Jana Kowalskiego z Warszawy — NIE fałszywy Wrocław match |
| K-T5 | Regression: "wrocław" (single word city search) | Disambiguation list klientów z Wrocławia — single-word city search nadal działa |

### Wyniki Batch K (5 testów, bug-fix verification) — 12.04.2026, 22:49-23:07

| # | Test | Wynik | Notatka |
|---|------|-------|---------|
| K-T1 | bug-E9-6: add_note pending + unrelated "pokaż Michała Grabowskiego z Kielc" | ❌ FAIL | Flow NIE został anulowany. Bot potraktował unrelated message jako Dopisać — dodał tekst do notatki: "dzwonił pokaż Michała Grabowskiego z Kielc". `_route_pending_flow` dla add_note appenduje tekst zamiast sprawdzać czy to unrelated intent. bug-E9-6 NIE naprawiony dla add_note pending flow |
| K-T2 | klimatyzacja solo → Notatki wording | ✅ PASS | Produkt: puste ✅, Notatki: "Produkt nieobsługiwany: klimatyzacja" ✅ (standard wording). bug-B2-1 Notatki fix potwierdzone |
| K-T3 | "PV i klimatyzacja" → compound split | ✅ PASS | Produkt: "PV" ✅, Notatki: "Produkt nieobsługiwany: klimatyzacja" ✅. Compound product split + standard wording |
| K-T4 | Regression: "pokaż Jan Kowalski Warszawa" | ✅ PASS | Karta Jan Kowalski, Warszawa, Pompa ciepła — read-only, bez fałszywego Wrocław match. `_fuzzy_match` fix działa poprawnie |
| K-T5 | Regression: "wrocław" single word city search | ❌ FAIL | Bot odpowiedział "Ta funkcja jest w przygotowaniu. Niedługo dostępna." zamiast disambiguation klientów z Wrocławia. Classifier nie rozpoznaje gołego "wrocław" jako show_client. Nie jest to regresja `_fuzzy_match` — message nigdy nie dociera do search logic bo classifier odrzuca |

**Wynik K: 3/5 ✅, 0/5 ⚠️, 2/5 ❌**

---

## Sesja L — ZAKOŃCZONA (12.04.2026)

### Naprawione w Sesji L (commit `eaddb75`, 12.04.2026)

| ID | Co naprawiono | Plik |
|----|---------------|------|
| bug-E9-6 (add_note leak) | `_route_pending_flow` add_note branch teraz sprawdza `_search_prefixes` przed appendowaniem tekstu. Wiadomości z "pokaż", "znajdź", "zmień status", itd. → `delete_pending_flow` + "⚠️ Anulowane." + `return False` (re-routing). Identyczna logika jak w add_client guard (linia ~259) | `bot/handlers/text.py` |
| K-T5 (bare city classifier) | `classify_intent` prompt — dodano przykład: `"wrocław" / sama nazwa miasta → show_client, entities: {"city": "..."}` + WAŻNE rule | `shared/claude_ai.py` |

### Testy do wykonania po deploy (Sesja L)

| # | Wiadomość / kroki | Oczekiwany wynik |
|---|-----------|-----------------|
| L-T1 | K-T1 retest: "dodaj notatkę do Jana Kowalskiego: dzwonił" → karta add_note + 3 buttons → wpisz "pokaż Michała Grabowskiego z Kielc" | "⚠️ Anulowane." + karta Michała Grabowskiego (fresh routing) |
| L-T2 | K-T5 retest: "wrocław" (single word) | Disambiguation list klientów z Wrocławia (show_client), NIE "Ta funkcja jest w przygotowaniu" |
| L-T3 | Regression: add_note "Marcin Kowalski Gdańsk: dzwonił" → Dopisać → "i chce rabat" | Karta 📝 z notatką "dzwonił i chce rabat" (Dopisać flow nadal działa po dodaniu guard) |

### Wyniki Batch L (3 testy, bug-fix verification) — 12.04.2026, 23:32-23:38

| # | Test | Wynik | Notatka |
|---|------|-------|---------|
| L-T1 | bug-E9-6: add_note pending + "pokaż Michała Grabowskiego z Kielc" | ✅ PASS | "⚠️ Anulowane." + karta Michała Grabowskiego (Kielce, 510620730, Nowy lead, PV). `_search_prefixes` guard w add_note branch działa — "pokaż" triggeruje cancel + fresh routing. bug-E9-6 NAPRAWIONY |
| L-T2 | "wrocław" single word → show_client | ✅ PASS | Bot znalazł Krzysztofa Dąbrowskiego z Wrocławia: "Nie mam 'wrocław'. Chodziło o Krzysztof Dąbrowski z Wrocław?" z [Tak, pokaż][Nie]. Classifier rozpoznaje bare city → show_client. Jeden klient w Wrocławiu → confirmation zamiast disambiguation list (correct). K-T5 fix potwierdzone |
| L-T3 | Regression: add_note Dopisać "dzwonił" + "i chce rabat" | ✅ PASS | Karta: "Marcin Kowalski, Gdańsk: dodaj notatkę 'dzwonił i chce rabat'?" z 3 buttons. Dopisać appenduje tekst poprawnie — guard nie blokuje legitimate Dopisać input |

**Wynik L: 3/3 ✅, 0/3 ⚠️, 0/3 ❌**

---

## Sesja Q — W TOKU (13.04.2026)

Cel: show_day_plan format rewrite — compact format per INTENCJE_MVP.md §4.6.

### Zmiany w Sesji Q

| Plik | Zmiana |
|------|--------|
| `shared/formatting.py` | Nowy `format_schedule_entry` (compact one-liner per event) + rewrite `format_daily_schedule` (header z datą DD.MM.YYYY + dzień tygodnia, empty day message) |
| `bot/handlers/text.py` | `handle_show_day_plan` przekazuje `target` date do `format_daily_schedule` |

### Testy Q do wykonania po restarcie bota

| # | Wiadomość | Oczekiwany wynik |
|---|-----------|-----------------|
| Q-T1 | "Co mam dziś?" (z istniejącymi spotkaniami) | Header: "📅 Plan na DD.MM.YYYY (dzień):" + compact entries (HH:MM 🤝 Klient (Miasto) — spotkanie) |
| Q-T2 | "Co mam w niedzielę?" (pusty dzień) | "Na DD.MM.YYYY (niedziela) nic nie masz w kalendarzu." — 1 linia |
| Q-T3 | "Plan na jutro" | Poprawna data jutro + header + eventy |
| Q-T4 | "Plan na piątek" | Day name → następny piątek, poprawna data w header |
| Q-T5 | "Co mam 15 kwietnia?" | Explicit date → header "📅 Plan na 15.04.2026 (środa):" |

---

## Sesja P — ZAKOŃCZONA (13.04.2026)

Cel: naprawić F-T4 partial (show_client disambiguation zamiast direct match) + pełny retest bug-E6-1/E10-2/E10-7.
Commity: `78c7efa` (show_client fix), `de0719a` (bug-P4-1 + P8-1), `95968fc` (revert P4-1 client check)

### Naprawione w Sesji P

| ID | Co naprawiono | Plik |
|----|---------------|------|
| F-T4 partial | `handle_search_client` multi-result path brakowało `_find_exact_name_match` + `_first_name_ok` filtra — szło prosto w disambiguation. Dodano ten sam pattern co w `handle_add_note` i `handle_change_status`: jeśli dokładnie jeden wynik pasuje po imieniu, pokaż kartę bezpośrednio | `bot/handlers/text.py` |

### Testy do wykonania po restarcie bota (Sesja P)

Pełny retest F-T1–F-T8 (bug-E6-1/E10-2/E10-7 fix verification):

| # | Wiadomość | Oczekiwany wynik |
|---|-----------|-----------------|
| P-T1 | "pokaż Tomka Zielińskiego z Lublina" (show_client) | Bezpośrednia karta Tomek Zieliński (direct match, BEZ disambiguation) |
| P-T2 | add_meeting "Radek Sikorski Radom jutro o 10" | Bezpośredni match, karta spotkania z Radek Sikorski |
| P-T3 | add_meeting "Jan Mazur Radom piątek 11:00" | Bezpośredni match Jan Mazur (NIE inny Mazur) |
| P-T4 | add_meeting "Ewa Mazur Szczecin środa 14:00" | "Nie mam" / "Nie znaleziono" (Ewa Mazur nie istnieje — guard blokuje Jana Mazura) |
| P-T5 | change_status "Radek Sikorski Radom → Umówione spotkanie" | Direct match, mutation card |
| P-T6 | add_note "Marcin Kowalski Gdańsk: oferta wysłana" | Direct match, mutation card z notatką |
| P-T7 | show_client "Jan Kowalski Warszawa" | Direct match, read-only card (BEZ disambiguation) |
| P-T8 | show_client "Kowalski" (bare last name, 2+ klientów) | Disambiguation z listą Kowalskich (poprawne — brak imienia do filtrowania) |

### Wyniki Batch P (8 testów, 13.04.2026, 14:24-14:28)

| # | Test | Wynik | Notatka |
|---|------|-------|---------|
| P-T1 | show_client "pokaż Tomka Zielińskiego z Lublina" | ⚠️ PARTIAL | "Nie mam Tomek Zieliński w bazie" — brak fałszywej disambiguation (fix działa ✅), ale klient nie istnieje (w bazie jest Piotr Zieliński Lublin, nie Tomek). Test zakładał że klient istnieje |
| P-T2 | add_meeting "Radek Sikorski Radom jutro o 10" | ✅ PASS | Direct match: Klient Radek Sikorski, 14.04.2026 (wtorek) 10:00, Radom. Brak disambiguation |
| P-T3 | add_meeting "Jan Mazur Radom piątek 11:00" | ✅ PASS | Direct match: Klient Jan Mazur, 17.04.2026 (piątek) 11:00, Radom. Brak disambiguation |
| P-T4 | add_meeting "Ewa Mazur Szczecin środa 14:00" | ❌ FAIL | Bot pokazał kartę spotkania z "Ewa Mazur" zamiast "Nie znaleziono". add_meeting nie weryfikuje czy klient istnieje w bazie — tworzy kartę z dowolnym imieniem |
| P-T5 | change_status "Radek Sikorski Radom na Spotkanie umówione" | ✅ PASS | Direct match: mutation card "Zmienić status klienta Radek Sikorski? → Spotkanie umówione" + 3 przyciski |
| P-T6 | add_note "Marcin Kowalski Gdańsk: oferta wysłana" | ✅ PASS | Direct match: "📝 Marcin Kowalski, Gdańsk: dodaj notatkę 'oferta wysłana'?" + 3 przyciski |
| P-T7 | show_client "Jan Kowalski Warszawa" | ✅ PASS | Direct match: read-only card z pełnymi danymi. BEZ disambiguation. Fix show_client działa ✅ |
| P-T8 | show_client "Kowalski" (bare last name) | ❌ FAIL | Bot pokazał kartę Jan Kowalski Warszawa bezpośrednio zamiast disambiguation. Brak listy Kowalskich do wyboru |

**Wynik P: 5/8 ✅, 1/8 ⚠️, 2/8 ❌**

**Nowe bugi z Sesji P:**
- **bug-P4-1**: add_meeting nie weryfikuje czy klient istnieje w bazie — tworzy kartę spotkania z dowolnym imieniem (Ewa Mazur Szczecin nie istnieje, a dostała kartę). Regresja vs F-T3 który mówił "Nie mam".
- **bug-P8-1**: show_client z samym nazwiskiem (bare last name "Kowalski") nie wywołuje disambiguation — pokazuje pierwszego znalezionego bezpośrednio. `_first_name_ok` guard prawdopodobnie nie filtruje gdy brak imienia w query.

### Naprawione w Sesji P (runda 2)

| ID | Co naprawiono | Plik |
|----|---------------|------|
| bug-P4-1 | `_enrich_meeting` teraz zwraca `client_found` flag. `handle_add_meeting` sprawdza: jeśli `client_name` podane ale klient nie znaleziony w Sheets → "Nie znalazłem klienta: '{name}'" (per INTENCJE_MVP.md R4). Dotyczy zarówno single jak i multi-meeting path | `bot/handlers/text.py` |
| bug-P8-1 | W `handle_search_client` multi-result path, `_first_name_ok` guard jest teraz pomijany gdy query ma <2 słów (np. "Kowalski"). Single-word query → zawsze disambiguation. `_first_name_ok` działa tylko gdy query zawiera imię (2+ słów) | `bot/handlers/text.py` |

### Testy P2 do wykonania po restarcie bota

| # | Wiadomość | Oczekiwany wynik |
|---|-----------|-----------------|
| P2-T1 | add_meeting "Ewa Mazur Szczecin środa 14:00" | "Nie znalazłem klienta: 'Ewa Mazur'" (klient nie istnieje) |
| P2-T2 | show_client "Kowalski" (bare last name) | Disambiguation: lista Kowalskich z przyciskami |
| P2-T3 | add_meeting "Jan Mazur Radom jutro o 10" | Direct match: karta spotkania Jan Mazur ✅ (regresja check — istniejący klient) |
| P2-T4 | show_client "Jan Kowalski Warszawa" | Direct match: read-only card (regresja check — 2+ słowa query) |
| P2-T5 | add_meeting "Jutro jadę do Jana Nowaka o 10 i do Anny Kowalskiej o 15" | 2 spotkania (regresja check multi-meeting z istniejącymi klientami) |

### Wyniki Batch P2 (5 testów, 13.04.2026, 14:37-14:39)

| # | Test | Wynik | Notatka |
|---|------|-------|---------|
| P2-T1 | add_meeting "Ewa Mazur Szczecin środa 14:00" | ✅ PASS | "Nie znalazłem klienta: 'Ewa Mazur'" — bug-P4-1 fix potwierdzone! |
| P2-T2 | show_client "Kowalski" (bare last name) | ✅ PASS | Disambiguation: "Mam 2 klientów: 1. Jan Kowalski — Warszawa, 2. Marcin Kowalski — Gdańsk. Którego?" + przyciski. bug-P8-1 fix potwierdzone! |
| P2-T3 | add_meeting "Jan Mazur Radom jutro o 10" (regression) | ✅ PASS | Direct match: Klient Jan Mazur, 14.04.2026, 10:00, Radom. Brak regresji |
| P2-T4 | show_client "Jan Kowalski Warszawa" (regression) | ✅ PASS | Direct match: read-only card. Brak regresji |
| P2-T5 | multi-meeting "Jutro jadę do Jana Nowaka o 10 i do Anny Kowalskiej o 15" | ❌ FAIL | "Nie znalazłem klienta: 'Anna Kowalska'" — client_found verification rejects multi-meeting when client not in DB. Regresja vs O-T4 (które pokazywało 2 spotkania). Anna Kowalska nie istnieje w Sheets |

**Wynik P2: 4/5 ✅, 0/5 ⚠️, 1/5 ❌**

**Nowy bug:**
- **bug-P2-5**: Multi-meeting z klientem spoza bazy → "Nie znalazłem klienta" zamiast karty spotkania. Regresja po bug-P4-1 fix. `_enrich_meeting` client_found check blokuje całą multi-meeting kartę gdy jeden z klientów nie istnieje. Pytanie produktowe: czy add_meeting powinno wymagać klienta w bazie? (INTENCJE_MVP mówi: "Klient może nie istnieć — handlowiec wpisuje nazwisko ręcznie, spotkanie się dodaje"). Jeśli tak — fix P4-1 jest za agresywny i powinien być cofnięty/ograniczony.

### Runda 3 — cofnięcie bug-P4-1 client check

**Decyzja:** client_found check w `handle_add_meeting` cofnięty. Handlowiec może tworzyć spotkania z klientami spoza bazy (nowy lead, jeszcze nie dodany do CRM). Guard `_first_name_ok` nadal chroni przed ZŁYM klientem (np. "Jan Kowalski" ≠ "Jan Nowak"), ale brak klienta w bazie NIE blokuje spotkania.

bug-P4-1 reklasyfikowany: to nie jest bug — add_meeting tworzy event w Calendar, nie mutuje Sheets. R4 (identyfikacja klienta) dotyczy mutacji CRM (add_note, change_status), ale add_meeting to Calendar event, nie Sheets mutation.

### Testy P3 po restarcie bota

| # | Wiadomość | Oczekiwany wynik |
|---|-----------|-----------------|
| P3-T1 | "Jutro jadę do Jana Nowaka o 10 i do Anny Kowalskiej o 15" | 2 spotkania: Jan Nowak (enriched) + Anna Kowalska (nie w bazie, ale karta OK) |
| P3-T2 | "Ewa Mazur Szczecin środa 14:00" | Karta spotkania z "Ewa Mazur" (nie w bazie, ale tworzy event) |
| P3-T3 | "Jan Mazur Radom jutro o 10" | Direct match: Jan Mazur enriched (regresja check) |

### Wyniki Batch P3 (3 testy, 13.04.2026, 14:48-14:49)

| # | Test | Wynik | Notatka |
|---|------|-------|---------|
| P3-T1 | multi-meeting "Jutro jadę do Jana Nowaka o 10 i do Anny Kowalskiej o 15" | ✅ PASS | 2 spotkania: "Jan Nowak — 14.04 10:00, Piaseczno" + "Anna Kowalska — 14.04 15:00". Mianownik ✅. Regresja P2-T5 naprawiona |
| P3-T2 | add_meeting "Ewa Mazur Szczecin środa 14:00" | ✅ PASS | Karta: Klient Ewa Mazur, 15.04.2026 (środa) 14:00, Szczecin. Tworzy bez enrichment (klient nie w bazie) |
| P3-T3 | add_meeting "Jan Mazur Radom jutro o 10" (regression) | ✅ PASS | Direct match: Klient Jan Mazur, 14.04.2026 (wtorek) 10:00, Radom. Enriched z bazy. Brak regresji |

**Wynik P3: 3/3 ✅, 0/3 ⚠️, 0/3 ❌** 🏆

---

## Sesja O — ZAKOŃCZONA (13.04.2026)

Commit: `91fe4b5`

### Naprawione w Sesji O

| ID | Co naprawiono | Plik |
|----|---------------|------|
| bug-A4-1 | Classifier false-positive edit_client — usunięto szerokie przykłady "ma nowy numer/telefon" → edit_client. Teraz edit_client TYLKO gdy jawne "zmień/zaktualizuj/popraw + pole + na + wartość". Ambiguous inputs → add_client (R4 merge). Usunięto szeroką regułę "danych ISTNIEJĄCEGO klienta → edit_client" | `shared/claude_ai.py` `classify_intent` |
| Bug #8 | Multi-meeting parser gubił imię w odmienionej formie — wzmocniono WAŻNE: "kto? co?" framing, dodano "Dotyczy KAŻDEGO spotkania w liście", konkretne przykłady z imionami w dopełniaczu → mianownik | `shared/claude_ai.py` `extract_meeting_data` |

### Testy do wykonania po restarcie bota (Sesja O)

| # | Wiadomość / kroki | Oczekiwany wynik |
|---|-----------|-----------------|
| O-T1 | "Jan Nowak ma nowy numer 609222333" | add_client (NIE edit_client R5 banner) — pójdzie przez R4 duplicate detection |
| O-T2 | "nowy telefon Jana Kowalskiego to 601000222" | add_client (NIE edit_client R5 banner) |
| O-T3 | "zmień telefon Jana Nowaka na 601234567" | edit_client R5 banner (jawna poprawka — poprawne) |
| O-T4 | "Jutro jadę do Jana Nowaka o 10 i do Anny Kowalskiej o 15" → Zapisać | 2 spotkania: meetings[0].client_name="Jan Nowak", meetings[1].client_name="Anna Kowalska" (mianownik, NIE genetyw) |

### Wyniki Batch O (4 testy, 13.04.2026, 13:55-13:56)

| # | Test | Wynik | Notatka |
|---|------|-------|---------|
| O-T1 | "Jan Nowak ma nowy numer 609222333" | ✅ PASS | add_client 3-button card (Jan Nowak, Tel. 609 222 333). NIE edit_client R5 banner. bug-A4-1 fix potwierdzone! |
| O-T2 | "nowy telefon Jana Kowalskiego to 601000222" | ✅ PASS | add_client 3-button card (Jan Kowalski, Tel. 601 000 222). NIE edit_client R5 banner. bug-A4-1 fix potwierdzone! |
| O-T3 | "zmień telefon Jana Nowaka na 601234567" | ✅ PASS | R5 POST-MVP banner: "Ta funkcja jest w przygotowaniu. Niedługo dostępna." Jawne "zmień" → poprawnie edit_client |
| O-T4 | "Jutro jadę do Jana Nowaka o 10 i do Anny Kowalskiej o 15" | ✅ PASS | 2 spotkania: "Jan Nowak — 14.04 10:00" + "Anna Kowalska — 14.04 15:00". Mianownik ✅ (NIE genetyw). Bug #8 fix potwierdzone! |

**Wynik O: 4/4 ✅, 0/4 ⚠️, 0/4 ❌** 🏆

### Pozostałe otwarte bugi po Sesji O

| ID | Status | Priorytet |
|----|--------|-----------|
| bug-E6-1/E10-2/E10-7 | ✅ NAPRAWIONE (Fix 1+2+2b, potwierdzone Sesja P: P-T2,3,5,6,7 ✅) | — |
| bug-A1-1 | Sheet-side — Maan musi zmienić nazwę kol. P w arkuszu | HIGH |
| bug-B1-1 | Sheet-side — Maan musi usunąć pustą kolumnę poz. 14 | HIGH |
| bug-A4-1 | ✅ NAPRAWIONE (Sesja O, potwierdzone O-T1–O-T3) | — |
| bug-B3-1 | ✅ NAPRAWIONE (Sesja P) — 2 przyciski na change_status | — |
| Bug #8 | ✅ NAPRAWIONE (Sesja O, potwierdzone O-T4) | — |

---

## Sesja N — ZAKOŃCZONA (13.04.2026)

### Naprawione w Sesji N (commit `65e1470`, 13.04.2026)

| ID | Co naprawiono | Plik |
|----|---------------|------|
| bug-A4-2 | R7 nie paliło po conflict-path merge ("Dopisz do istniejącego"). Dodano R7 do `_handle_duplicate_merge` w buttons.py — po `update_client` wysyła prompt + zapisuje `r7_prompt` flow. | `bot/handlers/buttons.py` |
| no-conflict merge | `handle_confirm` dla `add_client_duplicate` wywoływał `add_client` (nowy wiersz!) zamiast `update_client` (aktualizacja istniejącego). Naprawiono: teraz wywołuje `update_client` + R7 po sukcesie. | `bot/handlers/text.py` |

### Testy do wykonania po restarcie bota (Sesja N)

| # | Wiadomość / kroki | Oczekiwany wynik |
|---|-----------|-----------------|
| N-T1 | add_client klient który już istnieje (bez konfliktu) → Zapisać | "✅ Dane zaktualizowane." + R7 prompt "Co dalej — X (Y)?" (NIE "✅ Zapisane." bez R7) |
| N-T2 | add_client klient który już istnieje (z konfliktem inny tel./produkt) → "Dopisz do istniejącego" | "✅ Dane zaktualizowane." + R7 prompt "Co dalej — X (Y)?" |
| N-T3 (regression) | add_client klient który nie istnieje → Zapisać | "✅ Zapisane." + R7 prompt (bez regresji) |
| N-T4 (regression) | add_client duplicate → "Utwórz nowy wpis" | Nowy klient dodany (nie duplikat-merge) |

### Pozostałe otwarte bugi po Sesji N

| ID | Status | Priorytet |
|----|--------|-----------|
| bug-E6-1/E10-2/E10-7 | ✅ NAPRAWIONE (Sesja P) | — |
| bug-A1-1 | Sheet-side — Maan musi zmienić nazwę kol. P w arkuszu | HIGH |
| bug-B1-1 | Sheet-side — Maan musi usunąć pustą kolumnę poz. 14 | HIGH |
| bug-A4-1 | ✅ NAPRAWIONE (Sesja O) | — |
| bug-B3-1 | ✅ NAPRAWIONE (Sesja P) — 2 przyciski na change_status | — |
| Bug #8 | ✅ NAPRAWIONE (Sesja O) | — |

---

## Sesja M — ZAKOŃCZONA (13.04.2026)

### Naprawione w Sesji M (commit `8e35db8`, 13.04.2026)

| ID | Co naprawiono | Plik |
|----|---------------|------|
| bug-A1-4 | R7 prompt "Co dalej z Jan Nowak z Gdańsk" (błędna składnia) → "Co dalej — Jan Nowak (Gdańsk)?" — nazwa w mianowniku, bez prefiksów wymagających odmiany. Zmieniono format `name_city` z `"{name} z {city}"` na `"{name} ({city})"` | `bot/handlers/text.py` `send_next_action_prompt` |
| Bug #10 | Tytuł zdarzenia kalendarza "Spotkanie z Jan Mazur" (bez odmiany) → "Spotkanie — Jan Mazur" — myślnik zamiast "z X" eliminuje potrzebę narzędnika. Zmiana w `_enrich_meeting` | `bot/handlers/text.py` `_enrich_meeting` |

### Testy do wykonania po deploy (Sesja M)

| # | Wiadomość / kroki | Oczekiwany wynik |
|---|-----------|-----------------|
| M-T1 | add_client "Piotr Testowy Lublin PV 509111222" → Zapisać | R7 prompt: "Co dalej — Piotr Testowy (Lublin)? Spotkanie, telefon, mail, odłożyć na później?" (NIE "Co dalej z Piotr Testowy z Lublin") |
| M-T2 | add_meeting "Jan Kowalski Warszawa jutro o 10" → Zapisać → sprawdź Google Calendar | Tytuł: "Spotkanie — Jan Kowalski" (NIE "Spotkanie z Jan Kowalski") |
| M-T3 (regression) | change_status "Marcin Kowalski Gdańsk na Podpisane" → Zapisać | R7 prompt pojawia się z nowym formatem (bez broken Polish) |
| M-T4 (regression) | add_note "Jan Kowalski Warszawa: dzwonił" → Zapisać | Brak R7 po add_note (zamknięty akt per spec) |

### Wyniki Batch M — runda 1 (4 testy, 13.04.2026, 12:22-12:35) — BEZ RESTARTU BOTA

| # | Test | Wynik | Notatka |
|---|------|-------|---------|
| M-T1 | add_client "Piotr Testowy Lublin PV 509111222" → Zapisać → R7 | ❌ FAIL | R7 prompt: "Co dalej z Piotr Testowy z Lublin?" — stary format. Bot nie zrestartowany po deploy |
| M-T2 | add_meeting "Jan Kowalski Warszawa jutro o 10" → Zapisać → Calendar | ❌ FAIL | Calendar title: "Spotkanie z Jan Kowalski" — stary format. Bot nie zrestartowany |
| M-T3 | change_status "Jan Kowalski Warszawa na Spotkanie umówione" → Zapisać | ❌ FAIL | R7 prompt: stary format "Co dalej z X z Y?" |
| M-T4 | add_note "Jan Kowalski Warszawa klient zainteresowany PV 10kW" → Zapisać | ✅ PASS | Brak R7 po add_note — poprawne (zamknięty akt) |

**Wynik M runda 1: 1/4 ✅, 3/4 ❌** — bot działał na starym kodzie (brak restartu)

### Wyniki Batch M — runda 2 RETEST (4 testy, 13.04.2026, 12:56-13:01) — PO RESTARCIE BOTA

| # | Test | Wynik | Notatka |
|---|------|-------|---------|
| M-T1 | add_client "Anna Retest Kraków PV 501222333" → Zapisać → R7 | ✅ PASS | R7 prompt: **"Co dalej — Anna Retest (Kraków)?"** — nowy format z em-dash ✅ |
| M-T2 | add_meeting "Anna Retest Kraków jutro o 15" → Zapisać → Calendar | ✅ PASS | Calendar title: **"Spotkanie — Anna Retest"** — nowy format z em-dash ✅ |
| M-T3 | change_status "Anna Retest Kraków na Spotkanie umówione" → Zapisać | ✅ PASS | R7 prompt: **"Co dalej — Anna Retest (Kraków)?"** — nowy format z em-dash ✅ |
| M-T4 | add_note "Anna Retest Kraków klientka zainteresowana PV 8kW" → Zapisać | ✅ PASS | "✅ Notatka dodana." — brak R7 po add_note. Poprawne: zamknięty akt per spec ✅ |

**Wynik M runda 2: 4/4 ✅, 0/4 ⚠️, 0/4 ❌** 🏆

**Wniosek:** Obie zmiany z Sesji M (bug-A1-4 R7 format + Bug #10 Calendar title) **działają poprawnie**. Runda 1 failowała bo bot nie został zrestartowany po deploy — pracował na starym kodzie w pamięci.

### Pozostałe otwarte bugi po Sesji M

| ID | Status | Priorytet |
|----|--------|-----------|
| bug-E6-1/E10-2/E10-7 | ✅ NAPRAWIONE (Sesja P) | — |
| bug-A1-1 | Sheet-side — Maan musi zmienić nazwę kol. P w arkuszu | HIGH |
| bug-B1-1 | Sheet-side — Maan musi usunąć pustą kolumnę poz. 14 | HIGH |
| bug-A4-1 | ✅ NAPRAWIONE (Sesja O) | — |
| bug-A4-2 | ✅ NAPRAWIONE (Sesja N) | — |
| bug-B3-1 | ✅ NAPRAWIONE (Sesja P) — 2 przyciski na change_status | — |
| Bug #8 | ✅ NAPRAWIONE (Sesja O) | — |

---

## Sesja N — ZAKOŃCZONA (13.04.2026)

### Naprawione w Sesji N

| ID | Co naprawiono | Plik |
|----|---------------|------|
| bug-A4-2 | R7 nie paliło po "Dopisz do istniejącego" (conflict-path merge). `_handle_duplicate_merge` w `buttons.py` teraz wysyła R7 prompt po `update_client` | `bot/handlers/buttons.py` |
| no-conflict merge bug | `handle_confirm` dla `add_client_duplicate` wywoływał `add_client` (tworzył nowy wiersz!) zamiast `update_client`. Krytyczny bug danych — naprawiony. Dodano R7 po sukcesie | `bot/handlers/text.py` |

### Wyniki Batch N (4 testy, 13.04.2026, 13:20-13:26)

| # | Test | Wynik | Notatka |
|---|------|-------|---------|
| N-T1 | add_client istniejący (bez konfliktu) "Anna Retest Kraków anna.retest@gmail.com" → Zapisać | ✅ PASS | "✅ Dane zaktualizowane." (update, nie nowy wiersz) + R7 "Co dalej — Anna Retest (Kraków)?" ✅ |
| N-T2 | add_client z konfliktem "Anna Retest Kraków 600999888 pompa ciepła" → Dopisz do istniejącego | ✅ PASS | "✅ Dane zaktualizowane." + R7 "Co dalej — Anna Retest (Kraków)?" ✅ — bug-A4-2 fix potwierdzone! |
| N-T3 | add_client nowy "Tomasz Nowy Wrocław PV 505111222" → Zapisać (regression) | ✅ PASS | "✅ Zapisane." + R7 "Co dalej — Tomasz Nowy (Wrocław)?" ✅ — brak regresji |
| N-T4 | add_client duplikat "Tomasz Nowy Wrocław 777888999 pompa ciepła" → Utwórz nowy wpis (regression) | ✅ PASS | "✅ Zapisane." + R7 "Co dalej — Tomasz Nowy (Wrocław)?" ✅ — brak regresji |

**Wynik N: 4/4 ✅, 0/4 ⚠️, 0/4 ❌** 🏆

---

### Naprawione w Sesji H (commit `16dce63`, 12.04.2026)

| ID | Co naprawiono | Plik |
|----|---------------|------|
| bug-F3-1 | Dopisać na add_note anulowało zamiast dopisywać — dodano `elif flow_type == "add_note"` w `_route_pending_flow` który appenduje tekst do istniejącej notatki i pokazuje przebudowaną kartę | `text.py` |
| bug-E2-7 | Phone search "kto ma numer X" misclassified jako add_client — dodano 4 przykłady phone→show_client do classifier prompt + `phone` entity support w `handle_search_client` | `claude_ai.py`, `text.py` |
| bug-E23-9 | show_client zwraca mutation card gdy pending add_client istnieje — dodano `_search_prefixes` guard w `elif flow_type == "add_client"` który auto-cancels i re-processes | `text.py` |
| bug-F3-6 | General question "jakie produkty oferujemy" zwraca Drive error — naprawiono `handle_general` system context: usunięto fałszywe "Masz dostęp do Drive", dodano listę produktów i statusów, zakazano odsyłania do zewnętrznych plików | `text.py` |

### Testy do wykonania po deploy (Sesja H)

| # | Wiadomość | Oczekiwany wynik |
|---|-----------|-----------------|
| H-T1 | "dodaj notatkę do Marcin Kowalski Gdańsk: dzwonił" → Dopisać → "i chce rabat" | Karta 📝 z notatką "dzwonił i chce rabat" + 3 przyciski |
| H-T2 | "kto ma numer 600123456" | show_client → znalezieni klienci z tym numerem, NIE add_client |
| H-T3 | "pokaż klienta z numerem 510620730" | show_client → Michał Grabowski znaleziony |
| H-T4 | add_client "Anna Kowal Poznań" → rapid-fire "pokaż Michał Grabowski Kielce" | "⚠️ Anulowane." + karta read-only Michała Grabowskiego |
| H-T5 | "jakie produkty oferujemy?" | Krótka odpowiedź z listą PV/Pompa ciepła/Magazyn energii/PV+Magazyn — BEZ Drive error |
| H-T6 | "jakie są nasze statusy?" (general question) | Odpowiedź z listą 9 statusów |

### Wyniki Batch H (6 testów, bug-fix verification) — 12.04.2026, 19:00-19:40

| # | Test | Wynik | Notatka |
|---|------|-------|---------|
| H-T1 | add_note Dopisać flow (dzwonił → i chce rabat) | ✅ PASS | Dopisać appenduje tekst, karta przebudowana z "dzwonił i chce rabat". bug-F3-1 fix potwierdzone |
| H-T2 | "kto ma numer 600123456" → show_client | ⚠️ PARTIAL | Classifier naprawiony (show_client ✅ nie add_client). Ale phone search zbyt szeroki — 7 klientów w disambiguation zamiast exact match. Po kliknięciu "Jan Kowalski — Warszawa" → poprawna karta read-only |
| H-T3 | "pokaż klienta z numerem 510620730" → Michał Grabowski | ⚠️ PARTIAL | Bot znalazł prawidłowego klienta (Michał Grabowski Kielce), ale powiedział "Nie mam 510620730" mimo że numer JEST w Sheets row 23. Po potwierdzeniu "tak" → poprawna karta read-only |
| H-T4 | add_client Anna Kowal + rapid-fire show_client | ✅ PASS | "⚠️ Anulowane." + karta Michała Grabowskiego read-only. bug-E23-9 fix potwierdzone — zero kontaminacji stanu |
| H-T5 | "jakie produkty oferujemy?" | ✅ PASS | "PV, Pompa ciepła, Magazyn energii, PV + Magazyn energii." — z wiedzy agenta, bez Drive error. bug-F3-6 fix potwierdzone |
| H-T6 | "jakie są nasze statusy?" | ✅ PASS | 9 statusów z wiedzy agenta: Nowy lead, Spotkanie umówione, Spotkanie odbyte, Oferta wysłana, Podpisane, Zamontowana, Rezygnacja z umowy, Nieaktywny, Odrzucone. Bez Negocjacji ✅ |

**Wynik H: 4/6 ✅, 2/6 ⚠️, 0/6 ❌**

---

### Naprawione w Sesji G (commit `efcdf1d`, 12.04.2026)

| ID | Co naprawiono | Commit |
|----|---------------|--------|
| bug-E10-4 | Intent loss po disambiguation — `_handle_select_client` teraz sprawdza pending `disambiguation` flow i kontynuuje change_status/add_note mutation card | efcdf1d |
| bug-E9-9 | "statusy" zwraca stary raw Python list — teraz pre-check keyword, formatted lista z `_VALID_STATUSES` | efcdf1d |
| bug-E2-5 | Brak whitelist walidacji statusów — dodano `_VALID_STATUSES` + walidacja + status menu | efcdf1d |
| bug-E2-1 | show_day_plan nie parsuje nazw dni ani explicite dat — przepisano na `_parse_show_day_date` helper | efcdf1d |
| bug-E3-3 | Temporal guard nie działa — dodano past-date check przed save_pending_flow w add_meeting | efcdf1d |
| bug-E1-3 | Stary "Odpowiedz tak/nie" tekst w add_meeting card — usunięty z `format_confirmation` | efcdf1d |
| bug-E5-1 | "Data następnego kroku" w ISO — naprawiono `_fmt_date` żeby obsługiwał "YYYY-MM-DD HH:MM" | efcdf1d |

### Krytyczne (blokują MVP)

| ID | Objaw | Lokalizacja | Priorytet |
|----|-------|-------------|-----------|
| bug-C4-1 | ✅ NAPRAWIONE (D krok 1) — cancel_words word-boundary | `_route_pending_flow` | — |
| bug-C2-1 | ✅ NAPRAWIONE (D.1) — handle_add_note MVP | `handle_add_note` | — |

### Wysokie (psują UX)

| ID | Objaw | Lokalizacja | Priorytet |
|----|-------|-------------|-----------|
| bug-R7-2 | ✅ NAPRAWIONE (D krok 2) | `handle_confirm` | — |
| bug-E10-4 | ✅ NAPRAWIONE (Sesja G) | `_handle_select_client` | — |
| bug-E9-9 | ✅ NAPRAWIONE (Sesja G) | `handle_text` pre-check | — |
| bug-E2-5 | ✅ NAPRAWIONE (Sesja G) | `handle_change_status` | — |
| bug-E2-1 | ✅ NAPRAWIONE (Sesja G) | `handle_show_day_plan` | — |
| bug-E3-3 | ✅ NAPRAWIONE (Sesja G) | `handle_add_meeting` | — |
| bug-E1-3 | ✅ NAPRAWIONE (Sesja G) | `format_confirmation` | — |
| bug-E5-1 | ✅ NAPRAWIONE (Sesja G) | `_fmt_date` | — |
| bug-A1-1 | "ID kalendarza" w arkuszu vs "ID wydarzenia Kalendarz" w kodzie → pojawia się w "Brakuje:" | Sheet-side fix (Maan) | HIGH |
| bug-B1-1 | Pusta kolumna bez nazwy na pozycji 14 → 17 col zamiast 16 | Sheet-side fix (Maan) | HIGH |
| bug-B2-1 | ✅ NAPRAWIONE (Sesja J+K) | Sesja J: odrzuca z Produkt. Sesja K: normalizuje gdy LLM pisze do Notatki bezpośrednio | — |
| bug-E6-1/E10-2/E10-7 | ✅ NAPRAWIONE (Sesja F+P) — `_first_name_ok` guard + `_fuzzy_match` word-to-word + show_client direct match. Potwierdzone P-T2,3,5,6,7 ✅ | `google_sheets.py` + `text.py` | — |
| bug-E9-6 | ✅ NAPRAWIONE (Sesja K+L) — Sesja K: `_fuzzy_match` city false-positive (K-T4 ✅). Sesja L: `_route_pending_flow` add_note `_search_prefixes` guard (L-T1 ✅). Oba root causes naprawione | `_fuzzy_match` + `_route_pending_flow` | — |
| bug-E23-9 | ✅ NAPRAWIONE (Sesja H) | `_route_pending_flow` add_client guard | — |

### Nowe otwarte

| ID | Objaw | Lokalizacja | Priorytet |
|----|-------|-------------|-----------|
| bug-E1-9 | ✅ NAPRAWIONE (Sesja I) | `claude_ai.py` extract_client_data prompt | — |
| bug-E2-7 | ✅ NAPRAWIONE (Sesja H + J) | `classify_intent`, `handle_search_client` (is_exact skip), `google_sheets.py` (exact phone match) | — |
| bug-E4-7 | ✅ NAPRAWIONE (Sesja I) | `handle_change_status` no-op guard | — |
| bug-E14-7 | ✅ NAPRAWIONE (Sesja I) | `claude_ai.py` extract_meeting_data prompt | — |
| bug-E19-9 | ✅ NAPRAWIONE (Sesja I) | `claude_ai.py` classify_intent prompt | — |
| bug-F2-2 | ✅ NAPRAWIONE (Sesja I) | `text.py` _find_exact_name_match + handle_add_note + handle_change_status | — |

### Niskie / kosmetyczne

| ID | Objaw | Lokalizacja | Priorytet |
|----|-------|-------------|-----------|
| bug-A4-1 | ✅ NAPRAWIONE (Sesja O, potwierdzone O-T1–O-T3) | `classify_intent` system prompt | — |
| bug-A4-2 | ✅ NAPRAWIONE (Sesja N, potwierdzone N-T2) — R7 pali po "Dopisz do istniejącego" merge | `_handle_duplicate_merge` w `buttons.py` | — |
| bug-B3-1 | ✅ NAPRAWIONE (Sesja P) — change_status ma teraz `build_confirm_cancel_buttons` (2 przyciski: Zapisać + Anulować, bez Dopisać) | `text.py` + `buttons.py` + `telegram_helpers.py` | — |
| bug-A1-4 | ✅ NAPRAWIONE (Sesja M, potwierdzone retest M-T1+M-T3) — "Co dalej — Anna Retest (Kraków)?" zamiast "Co dalej z X z Y" | `send_next_action_prompt` | — |
| Bug #8 | ✅ NAPRAWIONE (Sesja O, potwierdzone O-T4) | `extract_meeting_data` | — |
| Bug #10 | ✅ NAPRAWIONE (Sesja M, potwierdzone retest M-T2) — "Spotkanie — Anna Retest" zamiast "Spotkanie z X" | `_enrich_meeting` | — |

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
- Flow state cancel — unrelated message during add_note/add_client pending → "⚠️ Anulowane." + fresh routing (L-T1)
- Bare city search — "wrocław" → show_client z klientem z Wrocławia (L-T2)
- Dopisać guard — `_search_prefixes` nie blokuje legitimate Dopisać text (L-T3)

---

## Jak działamy

- **Claude Code** — implementuje i naprawia kod
- **Claude Cowork** — testuje manualnie w Telegram, generuje raporty
- **Maan** — decyduje o priorytetach, przekazuje wyniki między sesjami

**Na początku każdej sesji:** czytaj `SOURCE_OF_TRUTH.md` → `CURRENT_STATUS.md` → wedle potrzeby INTENCJE_MVP.md / agent_behavior_spec_v5.md / agent_system_prompt.md.

**Na końcu każdej sesji:** zaktualizuj ten plik.
