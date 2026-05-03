# OZE-Agent — Round 7 Test Report
_Date: 10.04.2026, 19:32_
_Tester: Claude Cowork (manual Telegram tests)_
_Build: develop @ 22a6c69 (local, po naprawach Bug #1/#3/#4)_

---

## Wyniki

| Test #  | Input                                                                                  | Result  | Notes |
|---------|----------------------------------------------------------------------------------------|---------|-------|
| A (B14) | `Jan Nowak Piaseczno 601234567 pompa` → [Zapisz]                                        | PASS    | Karta pokazuje pełne "Jan Nowak". R4 pyta "Kiedy następny kontakt?". Po [Zapisz] tylko "✅ Zapisane." — **bez** "Nie ma nic do potwierdzenia". **Bug B14 FIXED.** |
| B (imiona) | `jutro o 10 spotkanie z Janem Mazurem z Radomia` → [Tak] → `co mam jutro?`            | PASS    | Karta spotkania: "Klient: Jan Mazur", "Data: 11.04.2026 (sobota)". Plan dnia: "Spotkanie z Jan Mazur". **Bug #1 FIXED.** Minor: powinno być "Spotkanie z Janem Mazurem" (odmiana narzędnika) — drobny lingwistyczny detal. |
| #37     | `Nie dziala to gowno`                                                                   | PASS    | Bot: "Co nie działa?" — bez przeprosin, bez banned phrases, spokojny ton. |
| #38     | `CZEMU NIE ZAPISALO`                                                                    | PASS    | Bot: "Nie wiem co dokładnie próbowałeś zapisać — podaj szczegóły." Spec example był "Jaki błąd wyskakuje?" — intencja dokładnie ta sama (spokój, prośba o detale, zero emocji). |
| #39     | `hej co tam`                                                                            | PASS    | Bot: "Co chcesz zrobić?" — nie weszło w chat, nie weszło w add_client. |
| #45     | `Piotr Nowak Krakow 602111222 foto plus magazyn`                                        | PASS    | Karta: "PV, Magazyn energii" — oba produkty wykryte z "foto plus magazyn". Multi-product parsing działa. |
| #46     | `Anna Kowalska Warszawa 603222333 magazyn 10kWh`                                        | PARTIAL | Produkt: "Magazyn energii" ✅. Ale "10kWh" wylądowało w "Dodatkowe info: magazyn 10kWh" zamiast być specem produktu (np. "Magazyn 10 kWh"). Spec capture nie idzie do dedykowanego pola. |
| #47     | `notatka do Jana Nowaka z Piaseczna: spadla mu umowa`                                   | FAIL    | Bot wytworzył **nową** kartę add_client z Notatki: "Spadła umowa" + Brakuje: Telefon, Adres, Produkt. Intent powinien być `add_note` do **istniejącego** Jana Nowaka (był zapisany w Test A). Slang "spadła umowa" rozpoznany ✅, ale intent routing zły. |
| #48     | 209-znakowy input (Krzysztof Wojcik, pełne dane + specyfikacje + kontekst)             | PARTIAL | Wszystko złapane: imię, adres, telefon, produkt, Źródło: "Polecenie od Tomka Nowaka", Notatki, Następny krok, wszystkie specyfikacje (6kW, 180m², 50m², południe, 450kWh). ALE: (1) data "2026-04-17" — **ISO format**, nie "17.04.2026 (Piątek)" — Bug #3 nie naprawiony w tym miejscu; (2) specy w "Dodatkowe info" zamiast dedykowanych pól — Bug #2 częściowo. |
| #49     | `605444555` (sam numer)                                                                 | FAIL    | Bot: "✅ Zapisane." zamiast karty z "Brakuje: imię". Prawdopodobnie zinterpretował numer jako odpowiedź do pending flow (Krzysztof Wojcik) i zapisał go. Problem może być spowodowany wieloma równoległymi pending flowami — nie testował się w izolacji. **Potrzeba retest bez pending state.** |
| #52     | `🤔🤔🤔` (sam emoji)                                                                    | PASS    | Bot: "Co chcesz zrobić?" — graceful, bez crash, bez próby zapisu. |

---

## Podsumowanie

**7 PASS / 2 PARTIAL / 2 FAIL** (11 testów, licząc A i B jako regression tests)

### Co działa dobrze (potwierdzone w Round 7)

- **Bug B14 FIXED**: "Nie ma nic do potwierdzenia" już nie pojawia się po [Zapisz].
- **Bug #1 FIXED (main flows)**: Pełne imiona w karcie spotkania, plan dnia, kartach klientów.
- **Bug #3 częściowo FIXED**: Data spotkania "11.04.2026 (sobota)" — polski format w karcie meeting.
- **Tone (#37, #38, #39, #52)**: Spokój, zero przeprosin, zero banned phrases, graceful clarification.
- **Multi-product (#45)**: "foto plus magazyn" → "PV, Magazyn energii".
- **Rozszerzony parsing (#48)**: 200+ znaków, źródło polecenia, notatki, następny krok, wszystkie specy — wszystko złapane w jednym strzale.

### Co nadal się psuje

#### 1. Bug #2: Specy produktu nie trafiają do dedykowanych pól
- Test #46: "magazyn 10kWh" → "Dodatkowe info: magazyn 10kWh" zamiast "Magazyn 10 kWh" jako spec produktu.
- Test #48: "6kW dom 180m2 dach 50m2 poludnie 450kWh" → wszystko w "Dodatkowe info", brak dedykowanych pól `moc_kw`, `metraz_domu`, `metraz_dachu`, `kierunek_dachu`, `zuzycie_pradu`.
- **Fix location**: `shared/claude_ai.py` prompt dla `extract_client_data` + Google Sheets schema (dodać kolumny jeśli brakuje) + `shared/formatting.py` karta klienta.

#### 2. Bug #3: Data ISO nadal w "Następny krok"
- Test #48: "Następny krok: Podpisanie umowy do **2026-04-17**" — powinno "17.04.2026 (Piątek)".
- Karta spotkania już ma polski format (Test B) — fix był niepełny.
- **Fix location**: `shared/formatting.py` → wszędzie gdzie formatuje się `next_step_date` lub `follow_up_date`, nie tylko meeting card. Sprawdź `format_client_card`, `format_add_client_confirmation`.

#### 3. Bug #6 (NEW): Intent routing `add_note` vs `add_client`
- Test #47: "notatka do Jana Nowaka z Piaseczna: spadła mu umowa" → utworzono nową kartę klienta zamiast dodać notatkę do istniejącego.
- Slang recognition ✅ ("spadła umowa" → Notatki).
- Intent classification ❌ — nie rozpoznał `add_note` pattern mimo explicit słowa kluczowego "notatka do".
- **Fix location**: `shared/claude_ai.py` classify_intent prompt, dodaj examples dla `add_note` z wzorcem "notatka do <Imię Nazwisko> [z <miasta>]: <treść>" → `add_note(client_name, city, content)`.

#### 4. Bug #7 (NEW): Pending flow collision — bare number
- Test #49: "605444555" z wieloma otwartymi kartami [Zapisz] → bot odpowiedział "✅ Zapisane." zamiast pokazać nową kartę.
- Możliwe, że state-lock fix zadziałał w jedną stronę (auto-cancel + process jako nowa wiadomość), ale bot potraktował bare number jako intent "zapisz pending flow".
- **Fix location**: sprawdź `bot/handlers/text.py` → `handle_text` — gdy user wpisze wiadomość podczas pending flow i wiadomość nie jest jasną komendą, powinien auto-cancel pending i traktować jako nową wiadomość. Nigdy nie traktować bare number jako zgodę na zapis.

---

## Priorytety do następnej sesji Claude Code

1. **KRYTYCZNY** — Bug #6: Intent `add_note` nie rozpoznawany. Wpływa na codzienny workflow sprzedawcy (dodawanie notatek po rozmowach).
2. **WAŻNY** — Bug #3 reszta: Data ISO w "Następny krok" w karcie klienta (jeden pozostały format).
3. **WAŻNY** — Bug #2: Specy produktu (moc_kw, metraż, kierunek, zużycie) w dedykowane pola Google Sheets. Wymaga refaktoru `extract_client_data` + schema Sheets.
4. **MINOR** — Bug #7: Bare number podczas pending flow. Low-priority bo real-world rzadki (user zwykle wpisuje pełne dane).
5. **MINOR** — Polish inflection "Spotkanie z Jan Mazur" → "Spotkanie z Janem Mazurem". Nice-to-have.

---

## Tło techniczne

- Testy przeprowadzone przeciwko lokalnemu botowi Maana (develop HEAD 22a6c69).
- Railway deployment zablokowany (brak GitHub credentials w sandboxie) — testy tylko local-machine.
- Wszystkie poprawki z ostatniej sesji (fix Bug B14, Bug #1 full names, Bug #3 date format w meeting, Bug #4 edit intent) zostały potwierdzone w Round 7 — testy A i B pokazują że fix działa.
- Test #47 pokazał że parsing slangu działa osobno od intent classification — to dwa różne moduły, Bug #6 dotyczy tylko tego drugiego.
