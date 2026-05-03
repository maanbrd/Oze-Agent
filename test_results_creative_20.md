# 20 kreatywnych scenariuszy z prawdziwego życia OZE B2C — propozycja

_Data: 29.04.2026_
_Cel: rozszerzyć smoke poza matrycę o realistyczne sytuacje, które handlowiec OZE napotyka w terenie_

## Limit techniczny

MCP server `oze-e2e` udostępnia tylko **zarejestrowane** scenariusze (48 sztuk pod kategoriami `mutating_core`, `read_only`, `routing`, `rules`, `notes`, `card_structure`, `error_path`, `polish_edge`, `proactive`). Nie ma w nim toola do ad-hoc wysłania dowolnej wiadomości do bota — wszystko musi przejść przez `run_scenario` / `run_category` z nazwy zarejestrowanego scenariusza.

Żeby uruchomić poniższe 20 — trzeba je dodać jako kod do `oze-agent/tests_e2e/scenarios/creative.py`, dopisać import w `__init__.py`, restartować MCP server, potem `run_category creative`. Sam tutaj zostawiam matrycę gotową do review przez Maana — dopiero po akceptacji decydujemy, czy implementujemy je jako kod, czy traktujemy jako checklist do ręcznego smoke.

---

## C-01 — Klient odłożony na później

**Cel handlowca:** Dodać klienta zainteresowanego, ale niegotowego teraz — chce się odezwać za ~2 tygodnie.

**Wiadomość:** `Dodaj klienta Tomasz Kowalski z Łomży, telefon 600100200, zainteresowany PV ale chce poczekać 2 tygodnie aż dostanie wycenę z banku`

**Oczekiwane:** add_client card, status "Nieaktywny" lub "Nowy lead", notatka o "2 tygodnie / wycena bank", brak Calendar event (bot nie wie kiedy konkretnie wraca).

**Co weryfikujemy:** czy bot dobrze rozpoznaje "miękki termin" (nie konkretna data) i nie zmusza handlowca do podania godziny.

---

## C-02 — Polskie znaki w imieniu i adresie

**Cel:** Dodać klienta z silnymi polskimi znakami.

**Wiadomość:** `Dodaj klienta Łukasz Żółć, Łódź, ul. Świętej Trójcy 5, telefon 600100201, PV + magazyn`

**Oczekiwane:** add_client card z dokładnie tymi znakami: `Łukasz Żółć`, `Łódź`, `ul. Świętej Trójcy 5`. Brak transliteracji do `Lukasz Zolc / Lodz`.

**Co weryfikujemy:** integralność diakrytyków na całej drodze user → bot → karta.

---

## C-03 — Niespójny format telefonu

**Cel:** Trzy klienci, trzy różne formaty zapisu numeru.

**Wiadomości (osobne):**
1. `Dodaj klienta Marek Adamski, telefon +48 600 100 202, Warszawa, PV`
2. `Dodaj klienta Adam Marecki, telefon 600-100-203, Łódź, pompa ciepła`
3. `Dodaj klienta Anna Kowalska, telefon (600) 100 204, Poznań, magazyn`

**Oczekiwane:** każda karta pokazuje znormalizowany numer w jednym, spójnym formacie (np. `600 100 202`).

**Co weryfikujemy:** normalizację telefonów — czy bot ujednolica, czy zapisuje surowy input.

---

## C-04 — Spotkanie z widełkami czasowymi

**Cel:** Handlowiec nie wie dokładnie, kiedy spotkanie — daje przedział.

**Wiadomość:** `Spotkanie z Janem Testowym przyszły wtorek między 14 a 16`

**Oczekiwane:** bot pyta o konkretną godzinę ALBO wybiera dolną granicę (14:00) i pokazuje na karcie + ostrzega "wybrałem 14:00, zmień jeśli inaczej".

**Co weryfikujemy:** zachowanie przy nieprecyzyjnym czasie. Lepiej zapytać niż zgadnąć.

---

## C-05 — Lokalizacja: u klienta vs w biurze

**Cel:** Sprawdzić, czy bot rozróżnia miejsce spotkania.

**Wiadomości:**
1. `Spotkanie z Markiem Nowakiem jutro 10 u nas w biurze`
2. `Spotkanie z Markiem Nowakiem jutro 14 u klienta`

**Oczekiwane:** Calendar event 1 ma `location: biuro` (lub puste z notatką), event 2 ma adres klienta. Karty pokazują różnicę.

**Co weryfikujemy:** czy w opisie wydarzenia widać miejsce, którego użytkownik się spodziewa.

---

## C-06 — Wartość transakcji w notatce

**Cel:** Zapisać klientowi kwotę umowy.

**Wiadomość:** `Anna Beta-Nowak podpisała umowę na 45 tysięcy złotych`

**Oczekiwane:** change_status card → status "Podpisane", notatka zawiera "45 tys" / "45000" / "45 000 zł".

**Co weryfikujemy:** czy bot zachowuje liczbę z wiadomości w notatkach (Sheets H), nie traktuje jej jako szumu.

---

## C-07 — Niejednoznaczne nazwisko bez podpowiedzi

**Cel:** Sprawdzić disambiguation gdy w bazie są dwie osoby o tym samym nazwisku.

**Pre-condition:** w bazie są Jan Kowalski Warszawa i Jan Kowalski Kraków (fixturey).

**Wiadomość:** `Spotkanie z Janem Kowalskim jutro 14`

**Oczekiwane:** bot listuje obu z miastami i pyta "którego?", NIE wybiera przypadkowo.

**Co weryfikujemy:** R6 / disambiguation tam gdzie nie ma active_client w sesji.

---

## C-08 — Przeniesienie spotkania (POST-MVP)

**Cel:** Sprawdzić czy bot poprawnie odsyła do Google Calendar przy reschedule.

**Pre-condition:** klient Marek ma spotkanie jutro 14:00.

**Wiadomość:** `Marek przełożył spotkanie z jutra na piątek 14`

**Oczekiwane:** bot odpowiada vision-only: "Nie mam dostępu do Twojego kalendarza — zmień termin bezpośrednio w Google Calendar." Brak karty add_meeting (NIE tworzy duplikatu).

**Co weryfikujemy:** rozpoznanie intencji "przełóż" (POST-MVP) i brak przypadkowego dodania nowego eventu.

---

## C-09 — Notatka wieloliniowa z bulletami

**Cel:** Zapisać szczegółową analizę klienta w jednej notatce.

**Wiadomość:**
```
Notatka do Adama Beta-Tester:
- dom 200m2
- dach południowy 35 stopni
- chce inverter Huawei
- planuje instalację do końca maja
- ma WIBOR + 2pp na kredyt
```

**Oczekiwane:** add_note card z zachowaną strukturą bulletów, treść w karcie czytelna (nie sklejona w jeden ciąg).

**Co weryfikujemy:** czy newline'y i myślniki przeżywają drogę do Sheets H.

---

## C-10 — Klient nieodbierający telefonu

**Cel:** Zarejestrować nieudaną próbę kontaktu + zaplanować ponowny.

**Wiadomość:** `Dzwoniłem do Marka Nowaka, nie odbiera, spróbuję jutro o 10`

**Oczekiwane:** karta z notatką "nie odbiera" + nowe spotkanie typu phone_call jutro 10:00 (15 min).

**Co weryfikujemy:** dwukrokowość — notatka + zaplanowany follow-up w jednej wiadomości.

---

## C-11 — Klient zostawiony przez partnera

**Cel:** Dodać klientkę, której numer dał partner (typowy pattern w B2C).

**Wiadomość:** `Pan Kowalski Tomasz dał numer do żony Anny, Anna decyduje, telefon 600100205, Lublin`

**Oczekiwane:** add_client card z imieniem **Anna Kowalska** (nie "Pan Kowalski"). Notatka opisuje kontekst ("od męża Tomasza").

**Co weryfikujemy:** czy bot wyłapuje, kto jest decydentem, a nie zapisuje pierwszego napotkanego imienia.

---

## C-12 — Status "zastanowi się"

**Cel:** Status pośredni — handlowiec zostawia inicjatywę po stronie klienta.

**Wiadomość:** `Maria Beta-Tester zastanowi się, odezwie się sama`

**Oczekiwane:** change_status na "Nieaktywny" lub "Spotkanie odbyte" (zależnie od dotychczasowego statusu). Brak follow-up date (handlowiec nie planuje sam dzwonić).

**Co weryfikujemy:** czy bot rozumie "klient odezwie się sam" jako sygnał do nie-planowania kolejnego kroku.

---

## C-13 — Spotkanie zdalne / online

**Cel:** Sprawdzić, czy bot oznaczy spotkanie jako online.

**Wiadomość:** `Spotkanie online z Janem Beta-Tester na MS Teams jutro 14`

**Oczekiwane:** karta wskazuje miejsce "online / MS Teams" (a nie city klienta). Calendar event w description ma "MS Teams".

**Co weryfikujemy:** czy bot rozumie "online / Teams / Zoom / Meet" jako lokalizację, nie zwykły komentarz.

---

## C-14 — Reklamacja po instalacji

**Cel:** Klient zgłasza problem z istniejącą instalacją — handlowiec dodaje notatkę + jedzie naprawiać.

**Wiadomość:** `Klient Andrzej Beta-Tester dzwonił, panele po instalacji nie generują, jadę do niego dziś o 15`

**Oczekiwane:** add_note card + add_meeting card (15:00 dziś, in_person, miejsce klienta). Status klienta NIE zmienia się na coś dramatycznego (bo nadal jest klientem podpisanym).

**Co weryfikujemy:** czy bot nie traktuje "problem techniczny" jako sygnału do zmiany statusu na "Rezygnacja".

---

## C-15 — Wielu klientów w jednej wiadomości

**Cel:** Sprawdzić zachowanie przy multi-client message.

**Wiadomość:** `Dziś spotkałem się z Markiem, Adamem i Tomaszem, wszyscy chcą oferty`

**Oczekiwane:** bot prosi o doprecyzowanie ("podaj nazwiska / opisz każdego z osobna") albo rejestruje pierwszego i pyta o resztę. Nie tworzy 3 kart na raz bez identyfikacji.

**Co weryfikujemy:** graceful degradation przy multi-entity input.

---

## C-16 — Brudna szybka wiadomość (typo + brak diakrytyków)

**Cel:** Symulacja głosowej transkrypcji albo szybkiego pisania w terenie.

**Wiadomość:** `kowalski jan ze zlotegostoku ma juz pdpisana umowe`

**Oczekiwane:** bot rozpoznaje "Jan Kowalski" + miejscowość "Złoty Stok" + status "Podpisane". Karta z poprawioną kapitalizacją i diakrytykami (Złoty Stok).

**Co weryfikujemy:** odporność na lower-case, sklejone słowa, literówki — typowe w voice-to-text.

---

## C-17 — Edycja danych klienta (POST-MVP)

**Cel:** Sprawdzić odmowę edycji.

**Wiadomość:** `Janowi Kowalskiemu zmienił się numer telefonu na 600999888`

**Oczekiwane:** vision-only / POST-MVP reply: "To feature post-MVP. Zmień w Google Sheets bezpośrednio." Brak karty.

**Co weryfikujemy:** R6 + POST-MVP routing dla edycji.

---

## C-18 — Spotkanie z dziwną godziną (po polsku)

**Cel:** Format godziny niestandardowy.

**Wiadomości (osobne):**
1. `Spotkanie z Adamem Beta-Tester jutro za kwadrans dwunasta`
2. `Spotkanie z Anną Beta-Tester jutro o pierwszej po południu`

**Oczekiwane:** karta 1 ma 11:45, karta 2 ma 13:00.

**Co weryfikujemy:** parser polskich form czasowych beyond "wpół do".

---

## C-19 — Anulacja po Zapisz (false positive)

**Cel:** Po pomyłkowym zapisie handlowiec chce się wycofać — bot powinien grzecznie wyjaśnić, że trzeba w Sheets.

**Sekwencja:**
1. `Dodaj klienta Test Pomyłka, Lublin, 600999000, PV` → ✅ Zapisać
2. `Cofnij ostatni zapis` (po fakcie)

**Oczekiwane:** karta odmowy / vision-only: "Nie mam możliwości cofnąć zapisu. Usuń wpis bezpośrednio w Google Sheets." Brak akcji.

**Co weryfikujemy:** przewidywalna odmowa "undo" (POST-MVP) zamiast tworzenia kolejnego eventu.

---

## C-20 — Plan dnia z odwołanymi spotkaniami

**Cel:** Sprawdzić, czy day plan pokazuje spotkania nawet gdy handlowiec ma luźny komentarz.

**Pre-condition:** w Calendar są jutro 3 wydarzenia.

**Wiadomość:** `co mam jutro, dwa pierwsze już chyba odwołali`

**Oczekiwane:** bot pokazuje pełen plan jutra (3 spotkania, format DD.MM.YYYY). NIE ukrywa "odwołanych" — bo nie ma podstaw, by je oznaczać. Może dodać krótką sugestię "potwierdź w kalendarzu jeśli odwołali".

**Co weryfikujemy:** day plan jest read-only — bot nie robi domyślnych założeń o "odwołaniu".

---

## Kategorie pokrycia

| Kategoria life-scenario | Scenariusze |
|---|---|
| Soft termin / nieprecyzyjny czas | C-01, C-04 |
| Polskie znaki / brudny tekst | C-02, C-16, C-18 |
| Normalizacja danych | C-03 |
| Lokalizacja / typ spotkania | C-05, C-13 |
| Notatki o wartości / treści | C-06, C-09 |
| Disambiguation | C-07, C-11 |
| POST-MVP / odmowa | C-08, C-17, C-19 |
| Multi-step / compound | C-10, C-14 |
| Status semantyka | C-12, C-14 |
| Multi-entity / odporność | C-15, C-20 |

---

## Decyzja Maana

Decyzja Maana: 

- [ ] dopisać jako kod (`creative.py` + `__init__.py` + restart MCP) i odpalić
- [ ] traktować jako manual checklist (handlowo-podobny smoke przed sprintem)
- [ ] poprawki / komentarze do scenariuszy: ______________________________
