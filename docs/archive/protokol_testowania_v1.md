# OZE-Agent — Protokol Testowania v1

Data: 09.04.2026 | Po rundzie 5 + commit 7e0ddc5 | 79 testow w 11 kategoriach

---

## 1. Cel i zakres

Protokol definiuje CO testujemy, JAKIMI danymi, JAK oceniamy wynik i W JAKIEJ kolejnosci. Testujemy agenta z wielu stron: funkcjonalnie, jezykowo, tonalnie, stresowo i regresyjnie.

### Role
- **Tester (Claude Cowork):** Wykonuje testy na Telegramie. Dokumentuje w CURRENT_STATUS.md.
- **Maan:** Testy manualne (realny scenariusz). Screenshoty.
- **Claude Code:** Naprawia bugi. NIE testuje.

### Dane testowe wymagane w Google Sheet

PRZED testami, w arkuszu CRM MUSZA istniec:

| Imie i nazwisko | Miasto | Telefon | Produkt | Status | Cel |
|---|---|---|---|---|---|
| Jan Nowak | Piaseczno | 601234567 | PV | Oferta wyslana | search/edit/status (moc 8kW → Notatki) |
| Jan Mazur | Radom | 602345678 | Pompa ciepla | Nowy lead | odmiana polska |
| Jan Kowalski | Warszawa | 600123456 | PV | Spotkanie umowione | duplikaty/filtrowanie (moc 5kW → Notatki) |
| Piotr Kowalski | Piaseczno | 600111222 | Magazyn energii | Nowy lead | wiele wynikow |
| Adam Wisniewski | Legionowo | 602345678 | PV | Negocjacje | ogolne (moc 6kW → Notatki) |
| Stefan Jankowski | Radom | 602888111 | PV + Magazyn | Oferta wyslana | multi-product |

**Spotkania w Google Calendar:** Min. 2 dzis + 1 jutro.
**Bez tych danych** testy search/edit/status/filter beda FAIL z powodu braku danych, NIE bugow.

---

## 2. Kategorie testow

| Kategoria | Co testuje | Ile | Priorytet |
|---|---|---|---|
| A. Smoke test | Czy bot odpowiada i parsuje | 5 | KRYTYCZNY |
| B. CRUD klientow | Dodawanie, szukanie, edycja, notatki | 12 | KRYTYCZNY |
| C. Statusy i lejek | Zmiana statusu, dedukcja, pipeline | 8 | WYSOKI |
| D. Kalendarz | Spotkania, plan dnia, polski czas | 10 | WYSOKI |
| E. Filtrowanie | Filter po miescie, statusie, produkcie | 5 | SREDNI |
| F. Ton i osobowosc | R6 frustracja, banned phrases, dlugosc | 8 | WYSOKI |
| G. Slang OZE | Parsowanie branzowego jezyka | 7 | WYSOKI |
| H. Przeplyw i state | Auto-cancel, R1, anulowanie | 8 | KRYTYCZNY |
| I. Regresja | Czy stare fixy dzialaja | 6 | KRYTYCZNY |
| J. Stres i tempo | Szybkie wiadomosci, zmiana zdania | 5 | WYSOKI |
| K. Edge cases | Smieci, puste, dlugie, emoji | 5 | SREDNI |

---

## A. Smoke test (5 testow)

Jesli smoke FAIL — nie kontynuuj dalej.

| # | Input | Oczekiwane | Sprawdz |
|---|---|---|---|
| A1 | hej | Odpowiedz w < 5s, po polsku, bez entuzjazmu | Bot odpowiada, nie crash |
| A2 | co umiesz? | Lista mozliwosci | NIE add_client |
| A3 | Jan Nowak Piaseczno 601234567 pompa | Karta z [Tak][Nie] | R1, parsowanie |
| A4 | co mam dzis? | Plan dnia | Routing show_day_plan |
| A5 | co masz o Janie Mazurze? | Karta klienta | Search, daty DD.MM.YYYY |

---

## B. CRUD klientow (12 testow)

### B1. Dodawanie

| # | Input | Sprawdz |
|---|---|---|
| B1a | Marek Zielinski Grodzisk Mazowiecki ul Lipowa 3 dom 140m2 dach 35m2 PV 8kW 607222333 zrodlo OLX | Wszystkie pola, diakrytyki, Produkt="PV" (BEZ mocy), Notatki zawieraja "moc PV 8kW, dom 140m2, dach 35m2", BRAK pytania o nastepny kontakt |
| B1b | Ewa Kaminska Radom pompeczka 603444555 | pompeczka->Pompa ciepla, Brakuje: adres |
| B1c | Witek Nowak Pruszkow 608333444 PV-ka 10kW magazyn 15kWh 3 jednostki zrodlo Facebook | Produkt="PV + Magazyn + Klimatyzacja" (BEZ mocy), Notatki zawieraja "moc PV 10kW, moc magazynu 15kWh, 3 jednostki klima" |
| B1d | 602888111 Radom Stefan Kowalczyk Slowackiego 15 | Kolejnosc slow nie ma znaczenia |

### B2. Wyszukiwanie

| # | Input | Sprawdz |
|---|---|---|
| B2a | co masz o Janie Nowaku? | DD.MM.YYYY (Dzien tyg.), brak _row |
| B2b | pokaz dane Janowi Mazurowi | Odmiana -> mianownik |
| B2c | pokaz Kowalskiego | Wiele wynikow: Jan + Piotr |
| B2d | pokaz Kowalsky | Literowka -> sugestia |

### B3. Edycja (nowe z commit 7e0ddc5)

| # | Input | Sprawdz |
|---|---|---|
| B3a | zmien telefon Jana Nowaka na 609222333 | Intent: edit_client, stare vs nowe |
| B3b | zaktualizuj adres Jana Mazura na Lipowa 5 Radom | Edit routing |

### B4. Notatki (nowe z commit 7e0ddc5)

| # | Input | Sprawdz |
|---|---|---|
| B4a | dodaj notatke do Jana Mazura: dzwonic po 15, zona sie boi | Intent: add_note, [Tak][Nie] |
| B4b | Janowi Nowakowi: spadla mu umowa z PGE, wracam za miesiac | Kontekst handlowy, 'spadla' rozpoznane |

---

## C. Statusy i lejek (8 testow)

| # | Input | Oczekiwany status | Sprawdz |
|---|---|---|---|
| C1 | wyslalem oferte Janowi Nowakowi | Oferta wyslana | Dedukcja, [Tak][Nie] |
| C2 | Jan Kowalski podpisal! | Podpisane | Dedukcja |
| C3 | Jan Nowak rezygnuje | Odrzucone | NIE 'Rezygnuje' |
| C4 | spadla umowa z Janem Nowakiem | Odrzucone | Slang |
| C5 | umowilem sie z Janem Mazurem | Spotkanie umowione | Dedukcja |
| C6 | Jan Nowak nie odpowiada | general_question | NIE auto-zmiana |
| C7 | ilu mam klientow? | Lejek z liczbami | lejek_sprzedazowy |
| C8 | jaki mam pipeline? | Lejek z liczbami | Synonim |

---

## D. Kalendarz (10 testow)

| # | Input | Oczekiwane | Sprawdz |
|---|---|---|---|
| D1 | spotkanie z Janem Nowakiem jutro o 10 | Spotkanie + [Tak][Nie] | Data, 10:00 |
| D2 | pojutrze o 14 Jan Mazur Radom | Spotkanie | Data +2 dni |
| D3 | spotkanie za kwadrans dziesiata u Jana Kowalskiego | 09:45 | Polski czas |
| D4 | mam spotkanie wpol do osmej u Jana Mazura | 07:30 z prefixem | Routing |
| D5 | w piatek o 10 u Jana Nowaka | Najblizszy piatek | Dzien tyg. |
| D6 | co mam dzis? | Plan | Format |
| D7 | co mam jutro? | Plan na jutro | Inny dzien |
| D9 | przeloz Jana Kowalskiego na piatek o 10 | Stary vs nowy | reschedule |
| D10 | wolne okna w czwartek? | Sloty | free_slots |

---

## E. Filtrowanie (5 testow)

Nowa funkcja z commit 7e0ddc5.

| # | Input | Oczekiwane | Sprawdz |
|---|---|---|---|
| E1 | pokaz klientow z Warszawy | Lista z Warszawy | filtruj_klientow |
| E2 | kto czeka na oferte? | Klienci Oferta wyslana | Filtr status |
| E3 | ilu mam klientow z Radomia? | Liczba/lista | Filtr miasto |
| E4 | pokaz klientow z PV | Klienci z PV | Filtr produkt |
| E5 | kto ma status nowy lead? | Nowe leady | Filtr status |

---

## F. Ton i osobowosc (8 testow)

| # | Input | PASS jesli | FAIL jesli |
|---|---|---|---|
| F1 | nie dziala to gowno | 'Co chcesz zrobic?' | 'Przepraszam za utrudnienia' |
| F2 | CZEMU NIE ZAPISALO??? | 'Jaki blad wyskakuje?' | Wpisz ponownie troche inaczej|
| F3 | dziekuje za pomoc! | Krotka, bez entuzjazmu | 'Z przyjemnoscia!' |
| F4 | super, ten agent jest swietny | Krotka, bez samochwalstwa | 'Dziekuje za mile slowa!' |
| F5 | (po zapisie) | Max 1 linia | Dluzsze niz 2 linie |
| F6 | (karta klienta) | 4-8 linii | > 10 linii |
| F7 | hej, co tam? | 'Co chcesz zrobic?' | 'Hej! Jak moge pomoc?' |
| F8 | (dowolna) | 0 banned phrases | Jakakolwiek zakazana |

---

## G. Slang OZE (7 testow)

| # | Input | Oczekiwane | Sprawdz |
|---|---|---|---|
| G1 | Jan Nowak Radom PV-ka 10kW | Produkt="PV", Notatki: "moc PV 10kW" | Slang + spec -> moc do Notatek |
| G2 | Jan Mazur pompeczka Radom 8kW | Produkt="Pompa ciepla", Notatki: "moc pompy 8kW" | Zdrobnienie + moc do Notatek |
| G3 | foto plus magazyn plus | Produkt="PV + Magazyn +  | 2 produkty |
| G4 | magazyn 10kWh | Produkt="Magazyn energii", Notatki: "moc magazynu 10kWh" | Spec pojemnosci -> Notatki |
| G5 | Jan Kowalski Warszawa PV 12kW plus magazyn 15kWh | Produkt="PV + Magazyn", Notatki: "moc PV 12kW, moc magazynu 15kWh" | Wszystkie specs w Notatkach |
| G6 | spadla mu umowa (notatka) | Notatki: spadla umowa | Kontekst handlowy |
| G7 | gos z Radomia, baba z Legionowa, kwit podpisany | klient, klientka, umowa | Kolokwializmy |

---

## H. Przeplyw i state (8 testow)

| # | Scenariusz | Oczekiwane | Sprawdz |
|---|---|---|---|
| H1 | Karta klienta -> [Tak] | Zapisane. | R1 zapis |
| H2 | Karta klienta -> [Nie] | Anulowac? [Tak][Nie] | Flow anulowania |
| H3 | Po H2: [Tak] na Anulowac | Anulowane. | Potwierdzenie |
| H4 | 'Jan Nowak rezygnuje' -> pending -> 'co mam dzis?' | Anulowane. + plan | AUTO-CANCEL |
| H5 | Pending status -> 'Ewa Piaseczno 601234567 PV' | Anulowane. + karta | Auto-cancel + nowy |
| H6 | add_client pending -> 'anuluj' | Anulowac? [Tak][Nie] | add_client NIE auto-cancel |
| H7 | Po zapisie, wyslij cokolwiek | Normalna odpowiedz | Brak 'Nie ma nic do potwierdzenia' |
| H8 | 3 wiadomosci pod rzad | Kazda przetworzona | Brak state-lock |

---

## I. Regresja (6 testow)

| # | Fix | Input | PASS jesli |
|---|---|---|---|
| I1 | State-lock (R4) | 'co mam dzis?' podczas pending | Auto-cancel + plan |
| I2 | Raw data (R4) | co masz o Janie Mazurze? | DD.MM.YYYY, brak _row |
| I3 | R1 potwierdzenia | wyslalem oferte Janowi Mazurowi | Dedukcja z [Tak][Nie] |
| I4 | OZE slang (R2) | Witek Pruszkow 608333444 PV-ka magazyn | 3 produkty w polach |
| I5 | Garbage (R2) | asdfghjkl 123 qwerty | Smieci odrzucone |
| I6 | Duplikat (R3) | Jan Nowak Piaseczno 601234567 PV | [Nowy][Aktualizuj] |

---

## J. Stres i tempo (5 testow)

| # | Scenariusz | Oczekiwane |
|---|---|---|
| J1 | Karta klienta -> natychmiast druga karta | Obie przetworzone |
| J2 | 3 szybkie wiadomosci (status -> plan -> notatka) | Kazda anuluje poprzednia |
| J3 | 200+ znakow z wszystkim (dane, produkt, spec, emocje, follow-up) | WSZYSTKO sparsowane |
| J4 | Sam numer telefonu: 608999111 | Karta + Brakuje: imie i nazwisko |
| J5 | 'zapisz' gdy nic nie jest pending | 'Co chcesz zrobic?' |

---

## K. Edge cases (5 testow)

| # | Input | Oczekiwane |
|---|---|---|
| K1 | Pusty / samo emoji | 'Co chcesz zrobic?' |
| K2 | TAK (wielkie, bez kontekstu) | Normalne przetwarzanie |
| K3 | Jan Nowak Jan Nowak Jan Nowak | Jedno wyszukiwanie |
| K4 | !!!???.../// | 'Co chcesz zrobic?' |
| K5 | pomoz mi napisac oferte | Odmowa (agent NIE generuje ofert) |

---

## 3. System oceniania

| Wynik | Definicja |
|---|---|
| PASS | Intent, dane, ton — wszystko OK |
| PARTIAL | Intent OK ale cos nie tak (format, dlugosc, drobny blad) |
| FAIL | Zly intent / crash / state-lock / zakazana fraza / R1 zlamane |
| SKIP | Nie zaimplementowane |

### Progi akceptacji

| Kategoria | Min. PASS | Komentarz |
|---|---|---|
| A. Smoke | 100% | STOP jesli FAIL |
| B. CRUD | 80% | Core |
| C. Statusy | 75% | Edge cases |
| D. Kalendarz | 70% | Polski czas trudny |
| E. Filtrowanie | 60% | Nowa funkcja |
| F. Ton | 90% | Kluczowe dla adopcji |
| G. Slang | 85% | Musi dzialac |
| H. Przeplyw | 90% | Zaufanie usera |
| I. Regresja | 100% | Regresja = blocker |
| J. Stres | 70% | Szybki handlowiec |
| K. Edge | 60% | Nice to have |
| **TOTAL** | **80%** | **Min. 63/79 PASS** |

---

## 4. Checklist na kazda odpowiedz bota

| # | Co sprawdzic | FAIL jesli |
|---|---|---|
| V1 | Jezyk | Po angielsku lub mieszana |
| V2 | Daty | Nie DD.MM.YYYY (Dzien tyg.) |
| V3 | Dane wewnetrzne | _row, _sheet_id, Wiersz: |
| V4 | Zakazane frazy | Z listy sekcji F |
| V5 | Emoji | Party, stars, sparkles, muscle, rocket |
| V6 | Dlugosc | Potwierdzenie > 2 linii, karta > 10 linii |
| V7 | 'Brakuje:' puste | Brakuje: bez zawartosci |
| V8 | R1 | Zapis bez [Tak] |
| V9 | Specs | kW/kWh dolaczone do nazwy produktu zamiast do Notatek (moc MUSI byc w Notatkach jako "moc PV/pompy/magazynu XkW") |
| V10 | Nastepny kontakt | add_client bez pytania o krok |

---

## 5. Format raportu

Po kazdej rundzie: `CURRENT_STATUS.md` ->

```
## Runda [N]: [opis] ([data], [czas])
Bot z commitem [hash]. [X] testow, [PASS]/[PARTIAL]/[FAIL] ([%] pass rate)
| # | Input | Wynik | Szczegoly |
```

### Severity
- **KRYTYCZNY:** Bot nieuzyteczny (state-lock, R1 zlamane, crash)
- **WAZNY:** Funkcja nie dziala (zly intent, specs zgubione, format daty)
- **DROBNY:** Kosmetyka (emoji, dlugosc, brak fuzzy)
