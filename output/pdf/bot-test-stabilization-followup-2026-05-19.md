# Bot-test stabilization follow-up - raport

Data: 19.05.2026  
Zakres: core bot-test, bez webappu, offer/Gmail i szerokiego customer-send smoke.

## Decyzja

Bot-test nie blokuje promocji core zmian do `main`, pod warunkiem wdrozenia tej paczki kodu/harnessu razem z poprawka ikony telefonu.

Najwazniejsze bramki sa zielone:

- Google health: PASS, bez `invalid_scope`.
- Core smoke: 5/5 PASS.
- Wczesniejsze blockery existing smoke: 5/5 PASS.
- Photo smoke: PASS, z potwierdzeniem Sheets + Drive.
- Fixture’y po testach zostaly odtworzone: Jan Kowalski Warszawa, Jan Kowalski Krakow, Marek Nowak Wyszkow oraz konflikt w Calendar.

## Co bylo problemem

1. Google OAuth byl podejrzany o `invalid_scope`. Health check potwierdzil, ze token beta usera dziala: odczyt Sheets, Calendar i Drive przeszedl.
2. Disambiguation uzywalo sztucznych nazw fixture, ktore nie przypominaly normalnych klientow. Fixture’y zostaly przeniesione na naturalne nazwy, a znacznik testowy jest w emailu/notatce.
3. Scenariusz duplicate/Dopisz byl stary: uzywal nazwy `E2E-Beta-Tester-...`, ktora jest jednym tokenem. Bot celowo nie traktuje single-token name jako duplikatu, zeby nie lapac samego "Jan". Scenariusz zostal zmieniony na pelne imie i nazwisko.
4. Phone-call zapisywal sie poprawnie, ale live bot nadal pokazuje stary naglowek bez ikony telefonu. Kod lokalny ma juz poprawke: naglowek z ikona telefonu i tekstem "Dodać telefon?". Live potwierdzenie ikony wymaga deploy/restartu bot-test.
5. Photo smoke usuwal fixture’y przez cleanup z `include_fixtures=True`. Harness zostal poprawiony, a ostatni photo smoke potwierdzil cleanup bez kasowania fixture’ow.

## Wyniki live

### Google health

Plik dowodu: `output/smoke/google-health-2026-05-19.md`

- User: `bd381405-66d2-4544-b817-117f8f8de441`
- Telegram admin E2E: `1690210103`
- Sheets header read: PASS, 16 naglowkow
- Calendar read: PASS
- Drive folder metadata: PASS, folder `OZE Klienci - Maan`
- Reauth: niepotrzebny

### Existing blockers

Plik dowodu: `output/smoke/core-existing-followup-final-2026-05-19.md`

Wynik: 5/5 PASS.

- SM-4 phone_call save: PASS; zapis do Calendar potwierdzony.
- Duplicate/Dopisz update path: PASS; ten sam wiersz w Sheets zostal zaktualizowany o adres.
- Show client multi-match disambiguation: PASS; bot pokazuje wybor klientow Jan Kowalski.
- R7 next action after add client: PASS; po zapisie klienta bot prowadzi do kolejnej akcji.
- R6 active-client implicit note: PASS; notatka trafia do aktywnego klienta.

Uwaga: w live raporcie phone-call nadal ma known drift dla samej ikony, bo bot-test nie byl deployowany po lokalnej poprawce kodu.

### Core smoke

Plik dowodu: `output/smoke/core-smoke-followup-final-2026-05-19.md`

Wynik: 5/5 PASS.

- SM-10 memory expiry: PASS; po 31 minutach bot prosi o klienta zamiast dopisywac notatke z pamieci.
- SM-1 compound meeting + new client: PASS.
- SM-2 voice compound meeting + new client: PASS.
- SM-3 phone field not meeting: PASS.
- SM-7 add meeting then preseed add_client: PASS.

### Photo smoke

Plik dowodu: `output/smoke/photo-smoke-followup-final2-2026-05-19.md`

Wynik: PASS.

- Przed potwierdzeniem klienta nie bylo zapisu do Sheets.
- Przed potwierdzeniem zdjecia nie bylo zapisu Drive/Sheets.
- Po kliknieciu `Zapisać` licznik `Zdjęcia` w Sheets = 1.
- `Link do zdjęć` wskazuje folder Drive.
- Plik zdjecia zostal znaleziony w Drive.
- Folder Drive i wiersz testowy zostaly posprzatane.
- Cleanup photo smoke zachowal fixture’y (`include_fixtures=False`).

## Zmiany w kodzie/harnessie

- Dodany test-only Google health: `tests_e2e/google_health.py`.
- Fixture’y klientow sa naturalne: Jan Kowalski / Marek Nowak, z markerem testowym w emailu/notatce.
- Cleanup rozpoznaje stare fixture’y z prefiksem i nowe po `e2e.fixture` / `E2E fixture`.
- Duplicate scenario uzywa pelnego imienia i nazwiska oraz emailowego markera cleanup.
- Parser kart rozpoznaje telefon z ikona po checkmarku i rozpoznaje duplicate-update prompt.
- Marker zapisu rozpoznaje `Telefon dodany do kalendarza.` i `Dane zaktualizowane.`.
- Phone-call heading w kodzie ustawiony na wersje z ikona telefonu i tekstem `Dodać telefon?`.
- Post-campaign cleanup zachowuje fixture’y domyslnie.

## Lokalna weryfikacja

- `pytest tests_e2e/tests/test_fixtures.py tests_e2e/tests/test_sheets_verify.py tests_e2e/tests/test_calendar_verify.py -q`: 55 passed.
- `pytest tests_e2e/tests/test_card_parser.py tests_e2e/tests/test_mutating_core.py tests_e2e/tests/test_helpers.py -q`: 70 passed.
- `pytest tests/test_google_auth.py tests/test_google_oauth_state.py -q`: 14 passed.
- `pytest tests/behavior/test_action_type.py -q`: 3 passed.
- `pytest tests_e2e/tests -q`: 237 passed.

## Co zostaje jako follow-up

1. Deploy/restart bot-test i szybki re-run samego `add_meeting_phone_call_save`, zeby live potwierdzil widoczna ikone telefonu.
2. Cancel UX zostaje osobnym zadaniem: runtime spelnia one-click/no-loop, ale komunikat `Anulowane.` mozna doprecyzowac pozniej.
3. Webapp, offer/Gmail i customer-send smoke sa poza ta fala i wymagaja osobnego przebiegu.

## Konkluzja

Core bot-test jest stabilny dla tej fali. Nie widze blockera dla promocji core zmian, ale po deployu tej paczki warto wykonac jeden szybki smoke telefonu dla potwierdzenia, ze live karta pokazuje ikone telefonu.
