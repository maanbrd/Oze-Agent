# Mapa Flow Rozmów z Agentem — dokument review

**Data opracowania:** 27.04.2026  
**Zakres:** live MVP na podstawie aktualnego kodu  
**Dane:** wyłącznie fikcyjne dane testowe  
**Cel:** przejść scenariusz po scenariuszu i oznaczyć, które flow są OK, a które mają zostać zmienione.

> Stan 04.05.2026: ten dokument nadal mapuje core flow Telegram/CRM z 27.04.
> Generator ofert jest osobnym zatwierdzonym slice'em i ma testy w
> `docs/TEST_PLAN_CURRENT.md` sekcja `Offer Generator — Web/API/Bot`. Nie
> dopisujemy tutaj pełnych scenariuszy OF-*, żeby nie mieszać review core agenta
> z web/Gmail flow.

## Jak czytać dokument

- Każdy scenariusz pokazuje obecne zachowanie agenta, nie docelowy ideał.
- Sekcja **Decyzja Maana** jest celowo pusta: służy do review.
- Sheets pokazuje konkretne pola A-P albo informację, że nie ma zapisu.
- Calendar pokazuje event albo informację, że event nie powstaje.

## Kanoniczne kolumny Google Sheets A-P

| Kolumna | Nazwa |
|---|---|
| A | Imię i nazwisko |
| B | Telefon |
| C | Email |
| D | Miasto |
| E | Adres |
| F | Status |
| G | Produkt |
| H | Notatki |
| I | Data pierwszego kontaktu |
| J | Data ostatniego kontaktu |
| K | Następny krok |
| L | Data następnego kroku |
| M | Źródło pozyskania |
| N | Zdjęcia |
| O | Link do zdjęć |
| P | ID wydarzenia Kalendarz |

## Indeks scenariuszy

- `V-01` — **VOICE** — Voice -> transkrypcja -> Zapisz -> ADD_MEETING
- `V-02` — **VOICE** — Voice -> transkrypcja -> Anuluj
- `V-03` — **VOICE** — Voice z błędną transkrypcją
- `V-04` — **VOICE** — Voice -> ADD_CLIENT
- `AC-01` — **ADD_CLIENT** — Nowy klient z kompletem danych
- `AC-02` — **ADD_CLIENT** — Nowy klient z brakami
- `AC-03` — **ADD_CLIENT** — Dopisać dane przed zapisem
- `AC-04` — **ADD_CLIENT** — Anulować klienta
- `AC-05` — **ADD_CLIENT** — Duplikat bez konfliktu -> aktualizacja istniejącego
- `AC-06` — **ADD_CLIENT** — Duplikat z konfliktem -> dopisz do istniejącego
- `AC-07` — **ADD_CLIENT** — Duplikat z konfliktem -> utwórz nowy wpis
- `AC-08` — **ADD_CLIENT** — Błąd Sheets przy zapisie klienta
- `AM-01` — **ADD_MEETING** — Istniejący jednoznaczny klient -> spotkanie
- `AM-02` — **ADD_MEETING** — Nowy klient nieobecny w Sheets
- `AM-03` — **ADD_MEETING** — Wieloznaczny klient -> wybór konkretnego
- `AM-04` — **ADD_MEETING** — Wieloznaczny klient -> Żaden z nich
- `AM-05` — **ADD_MEETING** — Za dużo kandydatów
- `AM-06` — **ADD_MEETING** — Brak daty/godziny
- `AM-07` — **ADD_MEETING** — Data w przeszłości
- `AM-08` — **ADD_MEETING** — Konflikt w Calendar
- `AM-09` — **ADD_MEETING** — Event type phone_call
- `AM-10` — **ADD_MEETING** — Event type offer_email
- `AM-11` — **ADD_MEETING** — Istniejący klient + nowe puste pola
- `AM-12` — **ADD_MEETING** — Calendar fail
- `AM-13` — **ADD_MEETING** — Calendar OK, Sheets fail
- `CS-01` — **CHANGE_STATUS** — Jednoznaczny klient -> status
- `CS-02` — **CHANGE_STATUS** — Wieloznaczny klient -> wybór
- `CS-03` — **CHANGE_STATUS** — Status + spotkanie w jednej wiadomości
- `CS-04` — **CHANGE_STATUS** — Niekanoniczny status
- `CS-05` — **CHANGE_STATUS** — Błąd Sheets przy statusie
- `AN-01` — **ADD_NOTE** — Jednoznaczny klient -> notatka
- `AN-02` — **ADD_NOTE** — Wieloznaczny klient -> wybór
- `AN-03` — **ADD_NOTE** — Notatka z istniejącą historią
- `AN-04` — **ADD_NOTE** — Brak treści notatki
- `AN-05` — **ADD_NOTE** — Błąd Sheets przy notatce
- `SC-01` — **SHOW_CLIENT** — Szukaj po nazwisku -> jeden wynik
- `SC-02` — **SHOW_CLIENT** — Szukaj po telefonie
- `SC-03` — **SHOW_CLIENT** — Wiele wyników
- `SC-04` — **SHOW_CLIENT** — Brak wyniku
- `SC-05` — **SHOW_CLIENT** — Szukaj tylko po mieście
- `DP-01` — **SHOW_DAY_PLAN** — Plan dziś
- `DP-02` — **SHOW_DAY_PLAN** — Plan jutro
- `DP-03` — **SHOW_DAY_PLAN** — Dzień bez wydarzeń
- `DP-04` — **SHOW_DAY_PLAN** — Kilka wydarzeń
- `R7-01` — **R7** — Po dodaniu klienta -> Co dalej?
- `R7-02` — **R7** — Po zmianie statusu -> Co dalej?
- `R7-03` — **R7** — Odpowiedź niejasna
- `R7-04` — **R7** — Odpowiedź: telefon jutro 9
- `R7-05` — **R7** — Użytkownik nie chce następnego kroku
- `GEN-01` — **GENERAL** — Zwykła wiadomość testowa
- `GEN-02` — **OUT_OF_SCOPE** — Przełóż spotkanie
- `GEN-03` — **OUT_OF_SCOPE** — Usuń klienta
- `GEN-04` — **MULTI_MEETING** — Wiele spotkań w jednej wiadomości

---

## V-01 — VOICE — Voice -> transkrypcja -> Zapisz -> ADD_MEETING

**Cel użytkownika:** Użytkownik dyktuje spotkanie z danymi klienta.

**Przykładowa wiadomość:** `🎤 audio 0:28: "Dodaj spotkanie z Janem Testowym na jutro o 14..."`

**Router / intent / pending:** voice_transcription pending -> po voice_confirm:yes tekst trafia do routera -> record_add_meeting

### Mock Telegram

> **Użytkownik:** [wiadomość głosowa 0:28]

> **Bot:** 🎙️ Transkrybuję...

> **Bot:** 🎙️ Transkrypcja (pewność: 54%):
> Dodaj spotkanie z Janem Testowym na jutro o 14...
> 
> Co z tym?

> **Użytkownik:** klika ✅ Zapisz

> **Bot:** ✅ Dodać spotkanie?
> • Klient: Jan Testowy
> • Data: 28.04.2026 (wtorek)
> • Godzina: 14:00
> • Dane klienta do zapisu: Tel.: 600100200; Adres: ul. Zielona 28; Produkt: PV + Magazyn energii

**Przyciski:** `✅ Zapisz` | `❌ Anuluj` | `potem: ✅ Zapisać / ➕ Dopisać / ❌ Anulować`

**Kliknięcie / odpowiedź w scenariuszu:** ✅ Zapisz, potem ✅ Zapisać

### Google Sheets — efekt po akcji

- `F Status`: Spotkanie umówione
- `J Data ostatniego kontaktu`: 2026-04-27
- `K Następny krok`: Spotkanie
- `L Data następnego kroku`: 2026-04-28T14:00:00+02:00
- `P ID wydarzenia Kalendarz`: cal_test_123
- `B Telefon`: 600100200
- `D Miasto`: Marki
- `E Adres`: ul. Zielona 28
- `G Produkt`: PV + Magazyn energii

### Google Calendar — efekt po akcji

- `summary`: Spotkanie — Jan Testowy
- `start`: 2026-04-28 14:00
- `end`: 2026-04-28 15:00
- `timeZone`: Europe/Warsaw
- `location`: Marki, ul. Zielona 28
- `description`: Dane klienta: Telefon: 600100200; Miejscowość: Marki; Adres: ul. Zielona 28; Produkt: PV + Magazyn energii
- `event_type`: in_person

### Obecna ocena
OK po hotfixie 961fad1; kluczowe, żeby nie wpadało w ADD_CLIENT.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## V-02 — VOICE — Voice -> transkrypcja -> Anuluj

**Cel użytkownika:** Użytkownik odrzuca transkrypcję.

**Przykładowa wiadomość:** `🎤 audio 0:12`

**Router / intent / pending:** voice_transcription pending -> voice_confirm:cancel -> delete_pending_flow

### Mock Telegram

> **Użytkownik:** [wiadomość głosowa]

> **Bot:** 🎙️ Transkrypcja: Halo halo
> 
> Co z tym?

> **Użytkownik:** klika ❌ Anuluj

> **Bot:** ❌ Anulowane.

**Przyciski:** `✅ Zapisz` | `❌ Anuluj`

**Kliknięcie / odpowiedź w scenariuszu:** ❌ Anuluj

### Google Sheets — efekt po akcji

- `-`: Brak zapisu do Sheets

### Google Calendar — efekt po akcji

- `-`: Brak zapisu do Calendar

### Obecna ocena
OK. Brak zapisu.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## V-03 — VOICE — Voice z błędną transkrypcją

**Cel użytkownika:** Bot pokazuje tekst do akceptacji, użytkownik może anulować lub poprawić osobną wiadomością.

**Przykładowa wiadomość:** `🎤 audio z niską pewnością`

**Router / intent / pending:** voice_transcription pending; brak zapisu bez potwierdzenia

### Mock Telegram

> **Użytkownik:** [wiadomość głosowa niewyraźna]

> **Bot:** 🎙️ Transkrypcja (pewność: 32%):
> Zapisz spotkanie z Janem... może jutro...
> 
> Co z tym?

> **Użytkownik:** klika ❌ Anuluj albo wysyła poprawny tekst

**Przyciski:** `✅ Zapisz` | `❌ Anuluj`

**Kliknięcie / odpowiedź w scenariuszu:** Do decyzji użytkownika

### Google Sheets — efekt po akcji

- `-`: Brak zapisu do Sheets

### Google Calendar — efekt po akcji

- `-`: Brak zapisu do Calendar

### Obecna ocena
Do decyzji: czy przy niskiej pewności bot powinien mocniej ostrzegać?

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## V-04 — VOICE — Voice -> ADD_CLIENT

**Cel użytkownika:** Transkrypcja zawiera tylko nowego klienta bez elementu czasowego.

**Przykładowa wiadomość:** `Dodaj klienta Marek Markowy, Marki, telefon 600100201, PV.`

**Router / intent / pending:** voice_confirm:yes -> record_add_client -> add_client pending

### Mock Telegram

> **Użytkownik:** [audio]

> **Bot:** 🎙️ Transkrypcja: Dodaj klienta Marek Markowy...

> **Użytkownik:** ✅ Zapisz

> **Bot:** 📋 Marek Markowy, Marki
> PV
> Tel. 600 100 201
> ❓ Brakuje: Email, Adres, Notatki...
> Zapisać / dopisać / anulować?

**Przyciski:** `✅ Zapisz` | `❌ Anuluj` | `potem: ✅ Zapisać / ➕ Dopisać / ❌ Anulować`

**Kliknięcie / odpowiedź w scenariuszu:** ✅ Zapisać

### Google Sheets — efekt po akcji

- `A Imię i nazwisko`: Marek Markowy
- `B Telefon`: 600100201
- `C Email`: 
- `D Miasto`: Marki
- `E Adres`: 
- `F Status`: 
- `G Produkt`: PV
- `H Notatki`: 
- `I Data pierwszego kontaktu`: 2026-04-27
- `J Data ostatniego kontaktu`: 
- `K Następny krok`: 
- `L Data następnego kroku`: 
- `M Źródło pozyskania`: 
- `N Zdjęcia`: 
- `O Link do zdjęć`: 
- `P ID wydarzenia Kalendarz`: 

### Google Calendar — efekt po akcji

- `-`: Brak zapisu do Calendar

### Obecna ocena
OK, jeśli brak daty/godziny.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## AC-01 — ADD_CLIENT — Nowy klient z kompletem danych

**Cel użytkownika:** Dodać pełny rekord klienta do Sheets.

**Przykładowa wiadomość:** `Dodaj klienta Jan Testowy, Marki, ul. Zielona 28, telefon 600-100-200, PV + magazyn energii.`

**Router / intent / pending:** record_add_client -> add_client pending

### Mock Telegram

> **Użytkownik:** Dodaj klienta Jan Testowy...

> **Bot:** 📋 Jan Testowy, ul. Zielona 28, Marki
> PV + Magazyn energii
> Tel. 600 100 200
> ❓ Brakuje: Email, Notatki, Następny krok...
> Zapisać / dopisać / anulować?

> **Użytkownik:** klika ✅ Zapisać

> **Bot:** ✅ Zapisane.

> **Bot:** Co dalej?

**Przyciski:** `✅ Zapisać` | `➕ Dopisać` | `❌ Anulować`

**Kliknięcie / odpowiedź w scenariuszu:** ✅ Zapisać

### Google Sheets — efekt po akcji

- `A Imię i nazwisko`: Jan Testowy
- `B Telefon`: 600100200
- `C Email`: 
- `D Miasto`: Marki
- `E Adres`: ul. Zielona 28
- `F Status`: 
- `G Produkt`: PV + Magazyn energii
- `H Notatki`: 
- `I Data pierwszego kontaktu`: 2026-04-27
- `J Data ostatniego kontaktu`: 
- `K Następny krok`: 
- `L Data następnego kroku`: 
- `M Źródło pozyskania`: 
- `N Zdjęcia`: 
- `O Link do zdjęć`: 
- `P ID wydarzenia Kalendarz`: 

### Google Calendar — efekt po akcji

- `-`: Brak zapisu do Calendar

### Obecna ocena
OK. Add client jest Sheets-only; po zapisie odpala R7.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## AC-02 — ADD_CLIENT — Nowy klient z brakami

**Cel użytkownika:** Zapisać częściowy rekord i pokazać brakujące pola.

**Przykładowa wiadomość:** `Dodaj klienta Jan Testowy z Marek.`

**Router / intent / pending:** record_add_client -> add_client pending

### Mock Telegram

> **Użytkownik:** Dodaj klienta Jan Testowy z Marek

> **Bot:** 📋 Jan Testowy, Marki
> ❓ Brakuje: Telefon, Email, Adres, Produkt, Notatki...
> Zapisać / dopisać / anulować?

**Przyciski:** `✅ Zapisać` | `➕ Dopisać` | `❌ Anulować`

**Kliknięcie / odpowiedź w scenariuszu:** ✅ Zapisać

### Google Sheets — efekt po akcji

- `A Imię i nazwisko`: Jan Testowy
- `B Telefon`: 
- `C Email`: 
- `D Miasto`: Marki
- `E Adres`: 
- `F Status`: 
- `G Produkt`: 
- `H Notatki`: 
- `I Data pierwszego kontaktu`: 2026-04-27
- `J Data ostatniego kontaktu`: 
- `K Następny krok`: 
- `L Data następnego kroku`: 
- `M Źródło pozyskania`: 
- `N Zdjęcia`: 
- `O Link do zdjęć`: 
- `P ID wydarzenia Kalendarz`: 

### Google Calendar — efekt po akcji

- `-`: Brak zapisu do Calendar

### Obecna ocena
Do decyzji: czy pozwalamy zapisywać tak ubogiego klienta?

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## AC-03 — ADD_CLIENT — Dopisać dane przed zapisem

**Cel użytkownika:** Użytkownik klika Dopisać i podaje brakujące dane.

**Przykładowa wiadomość:** `Po karcie klienta: klik ➕ Dopisać, potem "telefon 600100200, ul. Zielona 28, PV"`

**Router / intent / pending:** pending add_client -> append -> _route_pending_flow add_client -> merge client_data

### Mock Telegram

> **Bot:** 📋 Jan Testowy, Marki
> ❓ Brakuje: Telefon, Adres, Produkt...

> **Użytkownik:** klika ➕ Dopisać

> **Bot:** Co chcesz dopisać?

> **Użytkownik:** telefon 600100200, ul. Zielona 28, PV

> **Bot:** 📋 Jan Testowy, ul. Zielona 28, Marki
> PV
> Tel. 600 100 200
> Zapisać / dopisać / anulować?

**Przyciski:** `➕ Dopisać` | `✅ Zapisać`

**Kliknięcie / odpowiedź w scenariuszu:** ✅ Zapisać

### Google Sheets — efekt po akcji

- `A Imię i nazwisko`: Jan Testowy
- `B Telefon`: 600100200
- `C Email`: 
- `D Miasto`: Marki
- `E Adres`: ul. Zielona 28
- `F Status`: 
- `G Produkt`: PV
- `H Notatki`: 
- `I Data pierwszego kontaktu`: 2026-04-27
- `J Data ostatniego kontaktu`: 
- `K Następny krok`: 
- `L Data następnego kroku`: 
- `M Źródło pozyskania`: 
- `N Zdjęcia`: 
- `O Link do zdjęć`: 
- `P ID wydarzenia Kalendarz`: 

### Google Calendar — efekt po akcji

- `-`: Brak zapisu do Calendar

### Obecna ocena
OK; ważne do testów, bo tu LLM działa w kontekście pending.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## AC-04 — ADD_CLIENT — Anulować klienta

**Cel użytkownika:** Użytkownik odrzuca draft.

**Przykładowa wiadomość:** `Klik ❌ Anulować na karcie add_client.`

**Router / intent / pending:** cancel button -> delete_pending_flow

### Mock Telegram

> **Bot:** 📋 Jan Testowy...
> Zapisać / dopisać / anulować?

> **Użytkownik:** klika ❌ Anulować

> **Bot:** Anulowane.

**Przyciski:** `✅ Zapisać` | `➕ Dopisać` | `❌ Anulować`

**Kliknięcie / odpowiedź w scenariuszu:** ❌ Anulować

### Google Sheets — efekt po akcji

- `-`: Brak zapisu do Sheets

### Google Calendar — efekt po akcji

- `-`: Brak zapisu do Calendar

### Obecna ocena
OK.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## AC-05 — ADD_CLIENT — Duplikat bez konfliktu -> aktualizacja istniejącego

**Cel użytkownika:** Bot wykrywa istniejącego Jana i proponuje uzupełnić nowe puste dane.

**Przykładowa wiadomość:** `Dodaj Jan Testowy telefon 600100200.`

**Router / intent / pending:** record_add_client -> duplicate detected -> add_client_duplicate pending

### Mock Telegram

> **Użytkownik:** Dodaj Jan Testowy telefon 600100200

> **Bot:** Mam już Jan Testowy (Marki).
> Zaktualizować o: Telefon?

> **Użytkownik:** ✅ Zapisać

> **Bot:** ✅ Dane zaktualizowane.

> **Bot:** Co dalej?

**Przyciski:** `✅ Zapisać` | `➕ Dopisać` | `❌ Anulować`

**Kliknięcie / odpowiedź w scenariuszu:** ✅ Zapisać

### Google Sheets — efekt po akcji

- `B Telefon`: 600100200
- `J Data ostatniego kontaktu`: 2026-04-27

### Google Calendar — efekt po akcji

- `-`: Brak zapisu do Calendar

### Obecna ocena
OK; brak Calendar.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## AC-06 — ADD_CLIENT — Duplikat z konfliktem -> dopisz do istniejącego

**Cel użytkownika:** Nowe dane różnią się od istniejących.

**Przykładowa wiadomość:** `Dodaj Jan Testowy, adres ul. Nowa 5.`

**Router / intent / pending:** record_add_client -> add_client_duplicate -> merge button

### Mock Telegram

> **Użytkownik:** Dodaj Jan Testowy, adres ul. Nowa 5

> **Bot:** ⚠️ Masz już Jan Testowy (ul. Zielona 28, Marki, PV).
> Dodać nowego czy dopisać do istniejącego?

> **Użytkownik:** 📋 Dopisz do istniejącego

> **Bot:** ✅ Dane zaktualizowane.

**Przyciski:** `📋 Dopisz do istniejącego` | `➕ Utwórz nowy wpis`

**Kliknięcie / odpowiedź w scenariuszu:** 📋 Dopisz do istniejącego

### Google Sheets — efekt po akcji

- `E Adres`: ul. Nowa 5
- `J Data ostatniego kontaktu`: 2026-04-27

### Google Calendar — efekt po akcji

- `-`: Brak zapisu do Calendar

### Obecna ocena
Podejrzane: może nadpisać pole konfliktowe; do review polityka nadpisywania.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## AC-07 — ADD_CLIENT — Duplikat z konfliktem -> utwórz nowy wpis

**Cel użytkownika:** Użytkownik świadomie tworzy drugi rekord.

**Przykładowa wiadomość:** `Dodaj Jan Testowy, Warszawa, telefon 600100202.`

**Router / intent / pending:** record_add_client -> add_client_duplicate -> new button -> add_client commit

### Mock Telegram

> **Bot:** ⚠️ Masz już Jan Testowy (...).
> Dodać nowego czy dopisać do istniejącego?

> **Użytkownik:** ➕ Utwórz nowy wpis

> **Bot:** ✅ Zapisane.

**Przyciski:** `📋 Dopisz do istniejącego` | `➕ Utwórz nowy wpis`

**Kliknięcie / odpowiedź w scenariuszu:** ➕ Utwórz nowy wpis

### Google Sheets — efekt po akcji

- `A Imię i nazwisko`: Jan Testowy
- `B Telefon`: 600100202
- `C Email`: 
- `D Miasto`: Warszawa
- `E Adres`: 
- `F Status`: 
- `G Produkt`: 
- `H Notatki`: 
- `I Data pierwszego kontaktu`: 2026-04-27
- `J Data ostatniego kontaktu`: 
- `K Następny krok`: 
- `L Data następnego kroku`: 
- `M Źródło pozyskania`: 
- `N Zdjęcia`: 
- `O Link do zdjęć`: 
- `P ID wydarzenia Kalendarz`: 

### Google Calendar — efekt po akcji

- `-`: Brak zapisu do Calendar

### Obecna ocena
OK, ale wymaga wyraźnego copy, że powstaje drugi wiersz.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## AC-08 — ADD_CLIENT — Błąd Sheets przy zapisie klienta

**Cel użytkownika:** Google Sheets niedostępny.

**Przykładowa wiadomość:** `Dodaj klienta Jan Testowy...`

**Router / intent / pending:** add_client pending -> commit_add_client returns google_down

### Mock Telegram

> **Użytkownik:** ✅ Zapisać

> **Bot:** ⚠️ Google Sheets jest chwilowo niedostępny. Twoje dane NIE zostały zapisane. Spróbuj ponownie za kilka minut.

**Przyciski:** `✅ Zapisać`

**Kliknięcie / odpowiedź w scenariuszu:** ✅ Zapisać

### Google Sheets — efekt po akcji

- `-`: Błąd: brak zapisu

### Google Calendar — efekt po akcji

- `-`: Brak zapisu do Calendar

### Obecna ocena
OK. Do decyzji: czy pending ma zostać po błędzie, żeby kliknąć ponownie?

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## AM-01 — ADD_MEETING — Istniejący jednoznaczny klient -> spotkanie

**Cel użytkownika:** Dodać Calendar event i zsynchronizować istniejący wiersz.

**Przykładowa wiadomość:** `Dodaj spotkanie z Janem Testowym na jutro o 14.`

**Router / intent / pending:** record_add_meeting -> add_meeting pending; lookup unique client_row=12

### Mock Telegram

> **Użytkownik:** Dodaj spotkanie z Janem Testowym na jutro o 14

> **Bot:** ✅ Dodać spotkanie?
> • Klient: Jan Testowy
> • Data: 28.04.2026 (wtorek)
> • Godzina: 14:00
> • Czas trwania: 60 min
> • Miejsce: Marki, ul. Zielona 28

> **Użytkownik:** ✅ Zapisać

> **Bot:** ✅ Spotkanie dodane do kalendarza. Status klienta: Spotkanie umówione.

**Przyciski:** `✅ Zapisać` | `➕ Dopisać` | `❌ Anulować`

**Kliknięcie / odpowiedź w scenariuszu:** ✅ Zapisać

### Google Sheets — efekt po akcji

- `F Status`: Spotkanie umówione
- `J Data ostatniego kontaktu`: 2026-04-27
- `K Następny krok`: Spotkanie
- `L Data następnego kroku`: 2026-04-28T14:00:00+02:00
- `P ID wydarzenia Kalendarz`: cal_test_123

### Google Calendar — efekt po akcji

- `summary`: Spotkanie — Jan Testowy
- `start`: 2026-04-28 14:00
- `end`: 2026-04-28 15:00
- `timeZone`: Europe/Warsaw
- `location`: Marki, ul. Zielona 28
- `description`: Dane klienta: Telefon: 600100200; Miejscowość: Marki; Adres: ul. Zielona 28; Produkt: PV + Magazyn energii
- `event_type`: in_person

### Obecna ocena
OK.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## AM-02 — ADD_MEETING — Nowy klient nieobecny w Sheets

**Cel użytkownika:** Najpierw Calendar, potem draft ADD_CLIENT z danymi.

**Przykładowa wiadomość:** `Dodaj spotkanie z Markiem Markowym na jutro o 14. Mieszka w Markach na ul. Zielonej 28. Telefon 600100201. Fotowoltaika i magazyn energii.`

**Router / intent / pending:** record_add_meeting -> add_meeting pending client_row=None -> after save creates add_client pending

### Mock Telegram

> **Użytkownik:** Dodaj spotkanie z Markiem Markowym...

> **Bot:** ✅ Dodać spotkanie?
> • Klient: Marek Markowy
> • Dane klienta do zapisu: Tel.: 600100201; Adres: ul. Zielona 28; Produkt: PV + Magazyn energii

> **Użytkownik:** ✅ Zapisać

> **Bot:** ✅ Spotkanie dodane.
> 📋 Marek Markowy, ul. Zielona 28, Marki
> PV + Magazyn energii
> Tel. 600 100 201
> ❓ Brakuje: Email, Notatki...
> Zapisać / dopisać / anulować?

**Przyciski:** `✅ Zapisać` | `➕ Dopisać` | `❌ Anulować`

**Kliknięcie / odpowiedź w scenariuszu:** ✅ Zapisać spotkanie, potem decyzja na ADD_CLIENT

### Google Sheets — efekt po akcji

- `po pierwszym kliknięciu`: Brak klient_row, więc brak sync do istniejącego wiersza; powstaje pending ADD_CLIENT z A/B/D/E/F/G

### Google Calendar — efekt po akcji

- `summary`: Spotkanie — Marek Markowy
- `start`: 2026-04-28 14:00
- `end`: 2026-04-28 15:00
- `timeZone`: Europe/Warsaw
- `location`: Marki, ul. Zielona 28
- `description`: Dane klienta: Telefon: 600100200; Miejscowość: Marki; Adres: ul. Zielona 28; Produkt: PV + Magazyn energii
- `event_type`: in_person

### Obecna ocena
OK po fixie 8b0be20/961fad1; krytyczny scenariusz produkcyjny.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## AM-03 — ADD_MEETING — Wieloznaczny klient -> wybór konkretnego

**Cel użytkownika:** Bot znajduje kilku Janów i pyta którego użyć.

**Przykładowa wiadomość:** `Dodaj spotkanie z Janem Testowym jutro o 14.`

**Router / intent / pending:** record_add_meeting -> add_meeting_disambiguation pending -> select_client:row

### Mock Telegram

> **Użytkownik:** Dodaj spotkanie z Janem Testowym jutro o 14

> **Bot:** Mam 2 klientów o tym nazwisku. Którego użyć do spotkania?

> **Użytkownik:** klika Jan Testowy — Marki

> **Bot:** ✅ Dodać spotkanie?
> • Klient: Jan Testowy
> • Miejsce: Marki, ul. Zielona 28

**Przyciski:** `Jan Testowy — Marki` | `Jan Testowy — Warszawa` | `Żaden z nich`

**Kliknięcie / odpowiedź w scenariuszu:** Jan Testowy — Marki, potem ✅ Zapisać

### Google Sheets — efekt po akcji

- `F Status`: Spotkanie umówione
- `J Data ostatniego kontaktu`: 2026-04-27
- `K Następny krok`: Spotkanie
- `L Data następnego kroku`: 2026-04-28T14:00:00+02:00
- `P ID wydarzenia Kalendarz`: cal_test_123

### Google Calendar — efekt po akcji

- `summary`: Spotkanie — Jan Testowy
- `start`: 2026-04-28 14:00
- `end`: 2026-04-28 15:00
- `timeZone`: Europe/Warsaw
- `location`: Marki, ul. Zielona 28
- `description`: Dane klienta: Telefon: 600100200; Miejscowość: Marki; Adres: ul. Zielona 28; Produkt: PV + Magazyn energii
- `event_type`: in_person

### Obecna ocena
OK; dobre miejsce do oceny copy.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## AM-04 — ADD_MEETING — Wieloznaczny klient -> Żaden z nich

**Cel użytkownika:** Użytkownik nie wybiera istniejącego rekordu.

**Przykładowa wiadomość:** `Dodaj spotkanie z Janem Testowym jutro o 14, telefon 600100203.`

**Router / intent / pending:** add_meeting_disambiguation -> select_client:none -> add_meeting with client_row=None

### Mock Telegram

> **Bot:** Mam 2 klientów o tym nazwisku. Którego użyć do spotkania?

> **Użytkownik:** Żaden z nich

> **Bot:** ✅ Dodać spotkanie?
> • Klient: Jan Testowy
> • Dane klienta do zapisu: Tel.: 600100203

> **Użytkownik:** ✅ Zapisać

> **Bot:** ✅ Spotkanie dodane.
> 📋 Jan Testowy
> Tel. 600 100 203
> Zapisać / dopisać / anulować?

**Przyciski:** `Żaden z nich` | `✅ Zapisać`

**Kliknięcie / odpowiedź w scenariuszu:** Żaden z nich -> ✅ Zapisać

### Google Sheets — efekt po akcji

- `po Calendar`: pending ADD_CLIENT z A/B i ewentualnymi D/E/G

### Google Calendar — efekt po akcji

- `summary`: Spotkanie — Jan Testowy
- `start`: 2026-04-28 14:00
- `end`: 2026-04-28 15:00
- `timeZone`: Europe/Warsaw
- `location`: Marki, ul. Zielona 28
- `description`: Dane klienta: Telefon: 600100200; Miejscowość: Marki; Adres: ul. Zielona 28; Produkt: PV + Magazyn energii
- `event_type`: in_person

### Obecna ocena
OK; do decyzji czy tekst „Żaden z nich” jest wystarczająco jasny.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## AM-05 — ADD_MEETING — Za dużo kandydatów

**Cel użytkownika:** Bot nie pokazuje bardzo długiej listy.

**Przykładowa wiadomość:** `Spotkanie z Kowalskim jutro o 14.`

**Router / intent / pending:** lookup ambiguous > cap -> no pending

### Mock Telegram

> **Użytkownik:** Spotkanie z Kowalskim jutro o 14

> **Bot:** Znalazłem 6 klientów o tym nazwisku. Dopisz więcej danych klienta, np. miasto albo telefon.

### Google Sheets — efekt po akcji

- `-`: Brak zapisu do Sheets

### Google Calendar — efekt po akcji

- `-`: Brak zapisu do Calendar

### Obecna ocena
OK.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## AM-06 — ADD_MEETING — Brak daty/godziny

**Cel użytkownika:** Nie tworzyć eventu bez konkretnego czasu.

**Przykładowa wiadomość:** `Dodaj spotkanie z Janem Testowym.`

**Router / intent / pending:** record_add_meeting but extract_meeting_data missing date/time

### Mock Telegram

> **Użytkownik:** Dodaj spotkanie z Janem Testowym

> **Bot:** Nie rozpoznałem daty lub godziny spotkania. Podaj np. "jutro o 14:00 z Kowalskim".

### Google Sheets — efekt po akcji

- `-`: Brak zapisu do Sheets

### Google Calendar — efekt po akcji

- `-`: Brak zapisu do Calendar

### Obecna ocena
OK; do decyzji czy agent ma dopytać interaktywnie zamiast kończyć flow.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## AM-07 — ADD_MEETING — Data w przeszłości

**Cel użytkownika:** Odmowa zapisu przeszłego spotkania.

**Przykładowa wiadomość:** `Dodaj spotkanie z Janem wczoraj o 14.`

**Router / intent / pending:** record_add_meeting -> past temporal guard

### Mock Telegram

> **Użytkownik:** Dodaj spotkanie z Janem wczoraj o 14

> **Bot:** Data 26.04.2026 (...) o 14:00 jest w przeszłości. Podaj datę przyszłą.

### Google Sheets — efekt po akcji

- `-`: Brak zapisu do Sheets

### Google Calendar — efekt po akcji

- `-`: Brak zapisu do Calendar

### Obecna ocena
OK.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## AM-08 — ADD_MEETING — Konflikt w Calendar

**Cel użytkownika:** Karta pokazuje ostrzeżenie, ale pozwala zapisać.

**Przykładowa wiadomość:** `Dodaj spotkanie z Janem jutro o 14.`

**Router / intent / pending:** check_conflicts returns event

### Mock Telegram

> **Bot:** ✅ Dodać spotkanie?
> • Klient: Jan Testowy
> • Godzina: 14:00
> 
> ⚠️ Uwaga: masz już spotkanie o tej porze: Spotkanie — E2E-Beta-Tester

> **Użytkownik:** ✅ Zapisać

**Przyciski:** `✅ Zapisać` | `➕ Dopisać` | `❌ Anulować`

**Kliknięcie / odpowiedź w scenariuszu:** ✅ Zapisać mimo konfliktu

### Google Sheets — efekt po akcji

- `F Status`: Spotkanie umówione
- `J Data ostatniego kontaktu`: 2026-04-27
- `K Następny krok`: Spotkanie
- `L Data następnego kroku`: 2026-04-28T14:00:00+02:00
- `P ID wydarzenia Kalendarz`: cal_test_123

### Google Calendar — efekt po akcji

- `summary`: Spotkanie — Jan Testowy
- `start`: 2026-04-28 14:00
- `end`: 2026-04-28 15:00
- `timeZone`: Europe/Warsaw
- `location`: Marki, ul. Zielona 28
- `description`: Dane klienta: Telefon: 600100200; Miejscowość: Marki; Adres: ul. Zielona 28; Produkt: PV + Magazyn energii
- `event_type`: in_person

### Obecna ocena
Do decyzji: czy konflikt powinien blokować, czy tylko ostrzegać?

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## AM-09 — ADD_MEETING — Event type phone_call

**Cel użytkownika:** Telefon zapisuje Next Step jako Telefon i krótszy czas.

**Przykładowa wiadomość:** `Telefon do Jana Testowego jutro o 9.`

**Router / intent / pending:** record_add_meeting event_type=phone_call

### Mock Telegram

> **Użytkownik:** Telefon do Jana Testowego jutro o 9

> **Bot:** ✅ Dodać spotkanie?
> • Klient: Jan Testowy
> • Godzina: 09:00
> • Czas trwania: 15 min

**Przyciski:** `✅ Zapisać`

**Kliknięcie / odpowiedź w scenariuszu:** ✅ Zapisać

### Google Sheets — efekt po akcji

- `F Status`: Spotkanie umówione
- `J Data ostatniego kontaktu`: 2026-04-27
- `K Następny krok`: Telefon
- `L Data następnego kroku`: 2026-04-28T09:00:00+02:00
- `P ID wydarzenia Kalendarz`: cal_test_123

### Google Calendar — efekt po akcji

- `summary`: Telefon — Jan Testowy
- `start`: 2026-04-28 09:00
- `end`: 2026-04-28 09:15
- `timeZone`: Europe/Warsaw
- `location`: Marki, ul. Zielona 28
- `description`: Dane klienta: Telefon: 600100200; Miejscowość: Marki; Adres: ul. Zielona 28; Produkt: PV + Magazyn energii
- `event_type`: phone_call

### Obecna ocena
OK.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## AM-10 — ADD_MEETING — Event type offer_email

**Cel użytkownika:** Wysyłka oferty jako Calendar event i next step.

**Przykładowa wiadomość:** `Wyślij ofertę Janowi Testowemu jutro o 12.`

**Router / intent / pending:** record_add_meeting event_type=offer_email

### Mock Telegram

> **Użytkownik:** Wyślij ofertę Janowi Testowemu jutro o 12

> **Bot:** ✅ Dodać spotkanie?
> • Klient: Jan Testowy
> • Godzina: 12:00
> • Czas trwania: 15 min

**Przyciski:** `✅ Zapisać`

**Kliknięcie / odpowiedź w scenariuszu:** ✅ Zapisać

### Google Sheets — efekt po akcji

- `F Status`: Spotkanie umówione
- `J Data ostatniego kontaktu`: 2026-04-27
- `K Następny krok`: Wysłać ofertę
- `L Data następnego kroku`: 2026-04-28T12:00:00+02:00
- `P ID wydarzenia Kalendarz`: cal_test_123

### Google Calendar — efekt po akcji

- `summary`: Wysłać ofertę — Jan Testowy
- `start`: 2026-04-28 12:00
- `end`: 2026-04-28 12:15
- `timeZone`: Europe/Warsaw
- `location`: Marki, ul. Zielona 28
- `description`: 
- `event_type`: offer_email

### Obecna ocena
Do decyzji: czy oferta powinna być Calendar eventem czy tylko Sheets next step?

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## AM-11 — ADD_MEETING — Istniejący klient + nowe puste pola

**Cel użytkownika:** Spotkanie uzupełnia tylko puste dane klienta.

**Przykładowa wiadomość:** `Spotkanie z Janem jutro o 14, telefon 600100200, ul. Zielona 28, PV.`

**Router / intent / pending:** add_meeting with client_updates for empty fields only

### Mock Telegram

> **Użytkownik:** Spotkanie z Janem jutro o 14, telefon...

> **Bot:** ✅ Dodać spotkanie?
> • Dane klienta do zapisu: Tel.: 600100200; Adres: ul. Zielona 28; Produkt: PV

> **Użytkownik:** ✅ Zapisać

**Przyciski:** `✅ Zapisać`

**Kliknięcie / odpowiedź w scenariuszu:** ✅ Zapisać

### Google Sheets — efekt po akcji

- `F Status`: Spotkanie umówione
- `J Data ostatniego kontaktu`: 2026-04-27
- `K Następny krok`: Spotkanie
- `L Data następnego kroku`: 2026-04-28T14:00:00+02:00
- `P ID wydarzenia Kalendarz`: cal_test_123
- `B Telefon`: 600100200 tylko jeśli było puste
- `E Adres`: ul. Zielona 28 tylko jeśli było puste
- `G Produkt`: PV tylko jeśli było puste

### Google Calendar — efekt po akcji

- `summary`: Spotkanie — Jan Testowy
- `start`: 2026-04-28 14:00
- `end`: 2026-04-28 15:00
- `timeZone`: Europe/Warsaw
- `location`: Marki, ul. Zielona 28
- `description`: Dane klienta w description niezależnie od sync Sheets
- `event_type`: in_person

### Obecna ocena
OK; ważna polityka: nie nadpisujemy istniejących wartości.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## AM-12 — ADD_MEETING — Calendar fail

**Cel użytkownika:** Calendar niedostępny, Sheets nie są ruszane.

**Przykładowa wiadomość:** `Dodaj spotkanie z Janem jutro o 14.`

**Router / intent / pending:** commit_add_meeting create_event returns None

### Mock Telegram

> **Użytkownik:** ✅ Zapisać

> **Bot:** ⚠️ Google Calendar jest chwilowo niedostępny. Spotkanie NIE zostało dodane. Spróbuj ponownie za kilka minut.

**Przyciski:** `✅ Zapisać`

**Kliknięcie / odpowiedź w scenariuszu:** ✅ Zapisać

### Google Sheets — efekt po akcji

- `-`: Brak zapisu do Sheets, bo Calendar failed first

### Google Calendar — efekt po akcji

- `-`: Błąd: event nie powstał

### Obecna ocena
OK.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## AM-13 — ADD_MEETING — Calendar OK, Sheets fail

**Cel użytkownika:** Event powstał, ale klient nie został zsynchronizowany.

**Przykładowa wiadomość:** `Dodaj spotkanie z Janem jutro o 14.`

**Router / intent / pending:** commit_add_meeting success=True, sheets_attempted=True, sheets_synced=False

### Mock Telegram

> **Użytkownik:** ✅ Zapisać

> **Bot:** ✅ Spotkanie dodane do kalendarza. Nie udało się zaktualizować arkusza.

**Przyciski:** `✅ Zapisać`

**Kliknięcie / odpowiedź w scenariuszu:** ✅ Zapisać

### Google Sheets — efekt po akcji

- `-`: Błąd sync: F/J/K/L/P nie zapisane

### Google Calendar — efekt po akcji

- `summary`: Spotkanie — Jan Testowy
- `start`: 2026-04-28 14:00
- `end`: 2026-04-28 15:00
- `timeZone`: Europe/Warsaw
- `location`: Marki, ul. Zielona 28
- `description`: Dane klienta: Telefon: 600100200; Miejscowość: Marki; Adres: ul. Zielona 28; Produkt: PV + Magazyn energii
- `event_type`: in_person

### Obecna ocena
Podejrzane: mamy partial success; do decyzji czy bot ma dawać instrukcję naprawy.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## CS-01 — CHANGE_STATUS — Jednoznaczny klient -> status

**Cel użytkownika:** Zmienić status w kolumnie F.

**Przykładowa wiadomość:** `Jan Testowy podpisał.`

**Router / intent / pending:** record_change_status -> change_status pending row=12

### Mock Telegram

> **Użytkownik:** Jan Testowy podpisał

> **Bot:** ✅ Zmienić status?
> Status: Nowy lead → Podpisane

> **Użytkownik:** ✅ Zapisać

> **Bot:** ✅ Status zmieniony na: Podpisane

> **Bot:** Co dalej?

**Przyciski:** `✅ Zapisać` | `➕ Dopisać` | `❌ Anulować`

**Kliknięcie / odpowiedź w scenariuszu:** ✅ Zapisać

### Google Sheets — efekt po akcji

- `F Status`: Podpisane
- `J Data ostatniego kontaktu`: 2026-04-27

### Google Calendar — efekt po akcji

- `-`: Brak zapisu do Calendar

### Obecna ocena
OK; plain change_status odpala R7.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## CS-02 — CHANGE_STATUS — Wieloznaczny klient -> wybór

**Cel użytkownika:** Najpierw wybór osoby, potem karta statusu.

**Przykładowa wiadomość:** `Kowalski podpisał.`

**Router / intent / pending:** record_change_status -> disambiguation pending -> select_client

### Mock Telegram

> **Użytkownik:** Kowalski podpisał

> **Bot:** Znalazłem kilku klientów. Wybierz:

> **Użytkownik:** Jan Kowalski — Marki

> **Bot:** ✅ Zmienić status?
> Status: Oferta wysłana → Podpisane

**Przyciski:** `Jan Kowalski — Marki` | `Jan Kowalski — Warszawa`

**Kliknięcie / odpowiedź w scenariuszu:** wybór klienta -> ✅ Zapisać

### Google Sheets — efekt po akcji

- `F Status`: Podpisane
- `J Data ostatniego kontaktu`: 2026-04-27

### Google Calendar — efekt po akcji

- `-`: Brak zapisu do Calendar

### Obecna ocena
OK.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## CS-03 — CHANGE_STATUS — Status + spotkanie w jednej wiadomości

**Cel użytkownika:** Compound zapisuje status razem ze spotkaniem.

**Przykładowa wiadomość:** `Jan Testowy podpisał, spotkanie jutro o 14.`

**Router / intent / pending:** router prompt -> record_add_meeting with status_update=Podpisane

### Mock Telegram

> **Użytkownik:** Jan Testowy podpisał, spotkanie jutro o 14

> **Bot:** ✅ Dodać spotkanie?
> • Klient: Jan Testowy
> • Status: Nowy lead → Podpisane

> **Użytkownik:** ✅ Zapisać

> **Bot:** ✅ Spotkanie dodane do kalendarza. Status klienta: Podpisane.

**Przyciski:** `✅ Zapisać`

**Kliknięcie / odpowiedź w scenariuszu:** ✅ Zapisać

### Google Sheets — efekt po akcji

- `F Status`: Podpisane
- `J Data ostatniego kontaktu`: 2026-04-27
- `K Następny krok`: Spotkanie
- `L Data następnego kroku`: 2026-04-28T14:00:00+02:00
- `P ID wydarzenia Kalendarz`: cal_test_123

### Google Calendar — efekt po akcji

- `summary`: Spotkanie — Jan Testowy
- `start`: 2026-04-28 14:00
- `end`: 2026-04-28 15:00
- `timeZone`: Europe/Warsaw
- `location`: Marki, ul. Zielona 28
- `description`: Dane klienta: Telefon: 600100200; Miejscowość: Marki; Adres: ul. Zielona 28; Produkt: PV + Magazyn energii
- `event_type`: in_person

### Obecna ocena
OK po compound rules; krytyczne żeby nie robić dwóch osobnych ścieżek.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## CS-04 — CHANGE_STATUS — Niekanoniczny status

**Cel użytkownika:** Router powinien nie wymyślać statusu.

**Przykładowa wiadomość:** `Jan Testowy przesunięty.`

**Router / intent / pending:** jeśli nie pasuje do enum -> general/add_note lub prośba o doprecyzowanie

### Mock Telegram

> **Użytkownik:** Jan Testowy przesunięty

> **Bot:** [obecnie zależne od klasyfikatora]

### Google Sheets — efekt po akcji

- `-`: Brak zapisu do Sheets

### Google Calendar — efekt po akcji

- `-`: Brak zapisu do Calendar

### Obecna ocena
Do decyzji: docelowy tekst dla statusu spoza 9 wartości.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## CS-05 — CHANGE_STATUS — Błąd Sheets przy statusie

**Cel użytkownika:** Nie udało się zapisać F/J.

**Przykładowa wiadomość:** `Jan podpisał -> ✅ Zapisać`

**Router / intent / pending:** commit_change_status returns google_down

### Mock Telegram

> **Użytkownik:** ✅ Zapisać

> **Bot:** ⚠️ Google Sheets jest chwilowo niedostępny. Twoje dane NIE zostały zapisane. Spróbuj ponownie za kilka minut.

**Przyciski:** `✅ Zapisać`

**Kliknięcie / odpowiedź w scenariuszu:** ✅ Zapisać

### Google Sheets — efekt po akcji

- `-`: Brak zmiany F/J

### Google Calendar — efekt po akcji

- `-`: Brak zapisu do Calendar

### Obecna ocena
OK.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## AN-01 — ADD_NOTE — Jednoznaczny klient -> notatka

**Cel użytkownika:** Dopisać historię do kolumny H.

**Przykładowa wiadomość:** `Dopisz do Jana Testowego: klient chce ofertę do piątku.`

**Router / intent / pending:** record_add_note -> add_note pending row=12

### Mock Telegram

> **Użytkownik:** Dopisz do Jana Testowego: klient chce ofertę do piątku

> **Bot:** ✅ Dodać notatkę?
> • Klient: Jan Testowy
> • Notatka: klient chce ofertę do piątku

> **Użytkownik:** ✅ Zapisać

> **Bot:** ✅ Notatka dodana.

**Przyciski:** `✅ Zapisać` | `➕ Dopisać` | `❌ Anulować`

**Kliknięcie / odpowiedź w scenariuszu:** ✅ Zapisać

### Google Sheets — efekt po akcji

- `H Notatki`: [27.04.2026]: klient chce ofertę do piątku
- `J Data ostatniego kontaktu`: 2026-04-27

### Google Calendar — efekt po akcji

- `-`: Brak zapisu do Calendar

### Obecna ocena
OK; czysta notatka nie odpala R7.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## AN-02 — ADD_NOTE — Wieloznaczny klient -> wybór

**Cel użytkownika:** Wybór klienta przed notatką.

**Przykładowa wiadomość:** `Dopisz Kowalskiemu: ma oddzwonić.`

**Router / intent / pending:** record_add_note -> disambiguation -> select_client -> add_note pending

### Mock Telegram

> **Użytkownik:** Dopisz Kowalskiemu: ma oddzwonić

> **Bot:** Znalazłem kilku klientów. Wybierz:

> **Użytkownik:** Jan Kowalski — Marki

> **Bot:** ✅ Dodać notatkę?
> • Notatka: ma oddzwonić

**Przyciski:** `Jan Kowalski — Marki` | `Jan Kowalski — Warszawa`

**Kliknięcie / odpowiedź w scenariuszu:** wybór -> ✅ Zapisać

### Google Sheets — efekt po akcji

- `H Notatki`: [27.04.2026]: ma oddzwonić
- `J Data ostatniego kontaktu`: 2026-04-27

### Google Calendar — efekt po akcji

- `-`: Brak zapisu do Calendar

### Obecna ocena
OK.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## AN-03 — ADD_NOTE — Notatka z istniejącą historią

**Cel użytkownika:** Nowy wpis jest dopinany po średniku.

**Przykładowa wiadomość:** `Dopisz Janowi: wysłałem cennik.`

**Router / intent / pending:** record_add_note

### Mock Telegram

> **Bot:** ✅ Dodać notatkę?

> **Użytkownik:** ✅ Zapisać

> **Bot:** ✅ Notatka dodana.

**Przyciski:** `✅ Zapisać`

**Kliknięcie / odpowiedź w scenariuszu:** ✅ Zapisać

### Google Sheets — efekt po akcji

- `H Notatki`: stare notatki; [27.04.2026]: wysłałem cennik
- `J Data ostatniego kontaktu`: 2026-04-27

### Google Calendar — efekt po akcji

- `-`: Brak zapisu do Calendar

### Obecna ocena
OK.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## AN-04 — ADD_NOTE — Brak treści notatki

**Cel użytkownika:** Nie zapisywać pustej notatki.

**Przykładowa wiadomość:** `Dopisz Janowi.`

**Router / intent / pending:** prompt mówi: record_add_note tylko gdy note niepuste

### Mock Telegram

> **Użytkownik:** Dopisz Janowi

> **Bot:** [powinien dopytać: co dopisać?]

### Google Sheets — efekt po akcji

- `-`: Brak zapisu do Sheets

### Google Calendar — efekt po akcji

- `-`: Brak zapisu do Calendar

### Obecna ocena
Do decyzji: obecnie może trafić w add_client/show_client zależnie od routera.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## AN-05 — ADD_NOTE — Błąd Sheets przy notatce

**Cel użytkownika:** Notatka nie zapisana.

**Przykładowa wiadomość:** `Notatka -> ✅ Zapisać`

**Router / intent / pending:** commit_add_note returns google_down

### Mock Telegram

> **Użytkownik:** ✅ Zapisać

> **Bot:** ⚠️ Google Sheets jest chwilowo niedostępny. Twoje dane NIE zostały zapisane. Spróbuj ponownie za kilka minut.

**Przyciski:** `✅ Zapisać`

**Kliknięcie / odpowiedź w scenariuszu:** ✅ Zapisać

### Google Sheets — efekt po akcji

- `-`: Brak zmiany H/J

### Google Calendar — efekt po akcji

- `-`: Brak zapisu do Calendar

### Obecna ocena
OK.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## SC-01 — SHOW_CLIENT — Szukaj po nazwisku -> jeden wynik

**Cel użytkownika:** Pokazać kartę klienta bez zapisu.

**Przykładowa wiadomość:** `Co mam o Janie Testowym?`

**Router / intent / pending:** record_show_client -> lookup_client unique -> format_client_card

### Mock Telegram

> **Użytkownik:** Co mam o Janie Testowym?

> **Bot:** 📋 Jan Testowy
> Telefon: 600 100 200
> Miasto: Marki
> Adres: ul. Zielona 28
> Status: Spotkanie umówione
> Następny krok: Spotkanie...

### Google Sheets — efekt po akcji

- `-`: Brak zapisu do Sheets

### Google Calendar — efekt po akcji

- `-`: Brak zapisu do Calendar

### Obecna ocena
OK.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## SC-02 — SHOW_CLIENT — Szukaj po telefonie

**Cel użytkownika:** Telefon jako identyfikator istniejącego klienta.

**Przykładowa wiadomość:** `Pokaż 600100200.`

**Router / intent / pending:** record_show_client phone -> lookup_client

### Mock Telegram

> **Użytkownik:** Pokaż 600100200

> **Bot:** 📋 Jan Testowy...

### Google Sheets — efekt po akcji

- `-`: Brak zapisu do Sheets

### Google Calendar — efekt po akcji

- `-`: Brak zapisu do Calendar

### Obecna ocena
OK; uważać, żeby goły telefon nie tworzył klienta w złym kontekście.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## SC-03 — SHOW_CLIENT — Wiele wyników

**Cel użytkownika:** Bot pokazuje przyciski wyboru.

**Przykładowa wiadomość:** `Pokaż Kowalskiego.`

**Router / intent / pending:** record_show_client -> multiple candidates -> select_client buttons

### Mock Telegram

> **Użytkownik:** Pokaż Kowalskiego

> **Bot:** Znalazłem kilku klientów. Wybierz:

> **Użytkownik:** Jan Kowalski — Marki

> **Bot:** 📋 Jan Kowalski...

**Przyciski:** `Jan Kowalski — Marki` | `Adam Kowalski — Warszawa`

**Kliknięcie / odpowiedź w scenariuszu:** wybór

### Google Sheets — efekt po akcji

- `-`: Brak zapisu do Sheets

### Google Calendar — efekt po akcji

- `-`: Brak zapisu do Calendar

### Obecna ocena
OK.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## SC-04 — SHOW_CLIENT — Brak wyniku

**Cel użytkownika:** Bot informuje, że nie znalazł.

**Przykładowa wiadomość:** `Pokaż Alicję Nieistniejącą.`

**Router / intent / pending:** record_show_client -> lookup none

### Mock Telegram

> **Użytkownik:** Pokaż Alicję Nieistniejącą

> **Bot:** Nie znalazłem tego klienta.

### Google Sheets — efekt po akcji

- `-`: Brak zapisu do Sheets

### Google Calendar — efekt po akcji

- `-`: Brak zapisu do Calendar

### Obecna ocena
OK; do decyzji czy proponować dodanie klienta.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## SC-05 — SHOW_CLIENT — Szukaj tylko po mieście

**Cel użytkownika:** Potencjalnie wiele wyników z miasta.

**Przykładowa wiadomość:** `Pokaż klientów z Marek.`

**Router / intent / pending:** record_show_client city -> city-only query

### Mock Telegram

> **Użytkownik:** Pokaż klientów z Marek

> **Bot:** [lista wyników lub wybór klienta]

### Google Sheets — efekt po akcji

- `-`: Brak zapisu do Sheets

### Google Calendar — efekt po akcji

- `-`: Brak zapisu do Calendar

### Obecna ocena
Do decyzji: czy to show_client czy filter_clients poza MVP?

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## DP-01 — SHOW_DAY_PLAN — Plan dziś

**Cel użytkownika:** Pobrać wydarzenia Calendar z 27.04.2026.

**Przykładowa wiadomość:** `Co mam dzisiaj?`

**Router / intent / pending:** record_show_day_plan date=today -> Calendar list

### Mock Telegram

> **Użytkownik:** Co mam dzisiaj?

> **Bot:** Plan na 27.04.2026:
> 09:00 Telefon — Jan Testowy
> 14:00 Spotkanie — Marek Markowy

### Google Sheets — efekt po akcji

- `-`: Brak zapisu do Sheets

### Google Calendar — efekt po akcji

- `read`: Calendar events for day; brak zapisu

### Obecna ocena
OK.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## DP-02 — SHOW_DAY_PLAN — Plan jutro

**Cel użytkownika:** Pobrać wydarzenia Calendar z 28.04.2026.

**Przykładowa wiadomość:** `Co mam jutro?`

**Router / intent / pending:** record_show_day_plan date=2026-04-28

### Mock Telegram

> **Użytkownik:** Co mam jutro?

> **Bot:** Plan na 28.04.2026:
> 14:00 Spotkanie — Jan Testowy

### Google Sheets — efekt po akcji

- `-`: Brak zapisu do Sheets

### Google Calendar — efekt po akcji

- `read`: Calendar events for 2026-04-28; brak zapisu

### Obecna ocena
OK.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## DP-03 — SHOW_DAY_PLAN — Dzień bez wydarzeń

**Cel użytkownika:** Powiedzieć, że dzień pusty.

**Przykładowa wiadomość:** `Co mam w sobotę?`

**Router / intent / pending:** record_show_day_plan -> no events

### Mock Telegram

> **Użytkownik:** Co mam w sobotę?

> **Bot:** Nie masz zaplanowanych wydarzeń na ten dzień.

### Google Sheets — efekt po akcji

- `-`: Brak zapisu do Sheets

### Google Calendar — efekt po akcji

- `read`: Calendar no events

### Obecna ocena
OK.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## DP-04 — SHOW_DAY_PLAN — Kilka wydarzeń

**Cel użytkownika:** Lista posortowana po godzinie.

**Przykładowa wiadomość:** `Plan na jutro.`

**Router / intent / pending:** record_show_day_plan -> multiple events

### Mock Telegram

> **Użytkownik:** Plan na jutro

> **Bot:** 09:00 Telefon — Jan
> 12:00 Wysłać ofertę — Marek
> 14:00 Spotkanie — Jurek

### Google Sheets — efekt po akcji

- `-`: Brak zapisu do Sheets

### Google Calendar — efekt po akcji

- `read`: Calendar events sorted by start

### Obecna ocena
OK; do decyzji czy pokazywać location/status.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## R7-01 — R7 — Po dodaniu klienta -> Co dalej?

**Cel użytkownika:** R7 tworzy pending r7_prompt.

**Przykładowa wiadomość:** `Po ✅ Zapisać klienta`

**Router / intent / pending:** send_next_action_prompt -> r7_prompt pending

### Mock Telegram

> **Bot:** ✅ Zapisane.

> **Bot:** Co dalej?

> **Użytkownik:** Spotkanie jutro o 14

> **Bot:** ✅ Dodać spotkanie?
> • Klient: Jan Testowy...

**Kliknięcie / odpowiedź w scenariuszu:** odpowiedź z datą/godziną

### Google Sheets — efekt po akcji

- `po drugim kroku`: K/L/P/F jak add_meeting

### Google Calendar — efekt po akcji

- `summary`: Spotkanie — Jan Testowy
- `start`: 2026-04-28 14:00
- `end`: 2026-04-28 15:00
- `timeZone`: Europe/Warsaw
- `location`: Marki, ul. Zielona 28
- `description`: Dane klienta: Telefon: 600100200; Miejscowość: Marki; Adres: ul. Zielona 28; Produkt: PV + Magazyn energii
- `event_type`: in_person

### Obecna ocena
OK; to jest miejsce, gdzie agent ma prowadzić użytkownika.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## R7-02 — R7 — Po zmianie statusu -> Co dalej?

**Cel użytkownika:** R7 po plain change_status.

**Przykładowa wiadomość:** `Jan podpisał -> ✅ Zapisać -> Co dalej?`

**Router / intent / pending:** change_status confirm -> r7_prompt pending

### Mock Telegram

> **Bot:** ✅ Status zmieniony na: Podpisane

> **Bot:** Co dalej?

> **Użytkownik:** Wyślij ofertę serwisu jutro o 10

**Kliknięcie / odpowiedź w scenariuszu:** odpowiedź eventowa

### Google Sheets — efekt po akcji

- `K Następny krok`: Wysłać ofertę
- `L Data następnego kroku`: 2026-04-28T10:00:00+02:00
- `P ID wydarzenia Kalendarz`: cal_test_456

### Google Calendar — efekt po akcji

- `summary`: Wysłać ofertę — Jan Testowy
- `start`: 2026-04-28 10:00
- `end`: 2026-04-28 10:15
- `timeZone`: Europe/Warsaw
- `location`: Marki, ul. Zielona 28
- `description`: Dane klienta: Telefon: 600100200; Miejscowość: Marki; Adres: ul. Zielona 28; Produkt: PV + Magazyn energii
- `event_type`: offer_email

### Obecna ocena
OK.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## R7-03 — R7 — Odpowiedź niejasna

**Cel użytkownika:** Bot nie powinien improwizować.

**Przykładowa wiadomość:** `Po Co dalej?: "później"`

**Router / intent / pending:** r7_prompt -> if no meeting intent then uncertain path

### Mock Telegram

> **Bot:** Co dalej?

> **Użytkownik:** później

> **Bot:** [powinien dopytać: co dokładnie zapisać i kiedy?]

### Google Sheets — efekt po akcji

- `-`: Brak zapisu do Sheets

### Google Calendar — efekt po akcji

- `-`: Brak zapisu do Calendar

### Obecna ocena
Do decyzji: stworzyć deterministyczny fallback R7.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## R7-04 — R7 — Odpowiedź: telefon jutro 9

**Cel użytkownika:** R7 rozumie typ wydarzenia z krótkiej odpowiedzi.

**Przykładowa wiadomość:** `Telefon jutro o 9`

**Router / intent / pending:** r7_prompt text routes into handle_add_meeting with r7_client_row

### Mock Telegram

> **Bot:** Co dalej?

> **Użytkownik:** Telefon jutro o 9

> **Bot:** ✅ Dodać spotkanie?
> • Klient: Jan Testowy
> • Godzina: 09:00
> • Czas trwania: 15 min

**Przyciski:** `✅ Zapisać`

**Kliknięcie / odpowiedź w scenariuszu:** ✅ Zapisać

### Google Sheets — efekt po akcji

- `F Status`: Spotkanie umówione
- `J Data ostatniego kontaktu`: 2026-04-27
- `K Następny krok`: Telefon
- `L Data następnego kroku`: 2026-04-28T09:00:00+02:00
- `P ID wydarzenia Kalendarz`: cal_test_123

### Google Calendar — efekt po akcji

- `summary`: Telefon — Jan Testowy
- `start`: 2026-04-28 09:00
- `end`: 2026-04-28 09:15
- `timeZone`: Europe/Warsaw
- `location`: Marki, ul. Zielona 28
- `description`: Dane klienta: Telefon: 600100200; Miejscowość: Marki; Adres: ul. Zielona 28; Produkt: PV + Magazyn energii
- `event_type`: phone_call

### Obecna ocena
OK.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## R7-05 — R7 — Użytkownik nie chce następnego kroku

**Cel użytkownika:** Brak jasnego przycisku „nic”.

**Przykładowa wiadomość:** `Po Co dalej?: "nic"`

**Router / intent / pending:** r7_prompt pending; current behavior zależne od routera

### Mock Telegram

> **Bot:** Co dalej?

> **Użytkownik:** nic

> **Bot:** [obecnie do sprawdzenia; oczekiwane: OK, nie zapisuję następnego kroku.]

### Google Sheets — efekt po akcji

- `-`: Brak zapisu do Sheets

### Google Calendar — efekt po akcji

- `-`: Brak zapisu do Calendar

### Obecna ocena
Do decyzji: dodać obsługę „nic/koniec/anuluj”.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## GEN-01 — GENERAL — Zwykła wiadomość testowa

**Cel użytkownika:** Nie powinna robić zapisu ani błędu.

**Przykładowa wiadomość:** `Halo halo`

**Router / intent / pending:** record_general_question

### Mock Telegram

> **Użytkownik:** Halo halo

> **Bot:** Cześć! W czym mogę pomóc?

### Google Sheets — efekt po akcji

- `-`: Brak zapisu do Sheets

### Google Calendar — efekt po akcji

- `-`: Brak zapisu do Calendar

### Obecna ocena
OK po naprawie pustych odpowiedzi; wcześniej był unexpected error.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## GEN-02 — OUT_OF_SCOPE — Przełóż spotkanie

**Cel użytkownika:** Funkcja vision-only, nie wykonywać zmian.

**Przykładowa wiadomość:** `Przełóż spotkanie z Janem z jutra na środę.`

**Router / intent / pending:** record_out_of_scope feature_key=reschedule_meeting

### Mock Telegram

> **Użytkownik:** Przełóż spotkanie z Janem z jutra na środę

> **Bot:** To jest poza aktualnym zakresem MVP. Mogę pomóc zapisać nowe spotkanie albo notatkę.

### Google Sheets — efekt po akcji

- `-`: Brak zapisu do Sheets

### Google Calendar — efekt po akcji

- `-`: Brak zapisu do Calendar

### Obecna ocena
OK; do decyzji kiedy wchodzi reschedule.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## GEN-03 — OUT_OF_SCOPE — Usuń klienta

**Cel użytkownika:** Vision-only mimo legacy handlera; nie promować w MVP.

**Przykładowa wiadomość:** `Usuń Jana Testowego.`

**Router / intent / pending:** record_out_of_scope feature_key=delete_client albo legacy delete_client jeśli route ominie router

### Mock Telegram

> **Użytkownik:** Usuń Jana Testowego

> **Bot:** To jest poza aktualnym zakresem MVP i wymaga osobnej decyzji.

### Google Sheets — efekt po akcji

- `-`: Brak zapisu do Sheets

### Google Calendar — efekt po akcji

- `-`: Brak zapisu do Calendar

### Obecna ocena
Do decyzji: kod ma legacy delete_client, ale dokument v1 traktuje jako poza live MVP.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---

## GEN-04 — MULTI_MEETING — Wiele spotkań w jednej wiadomości

**Cel użytkownika:** MVP odrzuca batch.

**Przykładowa wiadomość:** `Dodaj spotkanie z Janem jutro o 9 i z Markiem o 12.`

**Router / intent / pending:** record_multi_meeting_rejection / REJECTED

### Mock Telegram

> **Użytkownik:** Dodaj spotkanie z Janem jutro o 9 i z Markiem o 12

> **Bot:** W tej wersji zapisuję jedno spotkanie naraz. Wyślij pierwsze spotkanie osobno.

### Google Sheets — efekt po akcji

- `-`: Brak zapisu do Sheets

### Google Calendar — efekt po akcji

- `-`: Brak zapisu do Calendar

### Obecna ocena
OK; istnieje legacy add_meetings, ale MVP ma odrzucać.

### Decyzja Maana
Decyzja Maana: OK / zmienić / doprecyzować: ______________________________


---
