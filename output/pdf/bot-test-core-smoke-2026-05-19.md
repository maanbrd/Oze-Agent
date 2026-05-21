# Raport bot-test Core Agent Smoke

Data raportu: 19.05.2026 (wtorek)  
Środowisko: `bot-test`, Railway production env  
Telegram E2E admin: `1690210103`  
Beta user: `bd381405-66d2-4544-b817-117f8f8de441`

## Decyzja w skrócie

Core agent jest dużo stabilniejszy niż na starcie testu. Główna paczka `core_smoke` przeszła finalnie 5/5 w jednym przebiegu: spotkanie + nowy klient, flow głosowe, klient z telefonem bez tworzenia spotkania, spotkanie z dosiewem klienta oraz wygaśnięcie pamięci po 31 minutach.

Nie rekomenduję jeszcze promocji `develop -> main` dla pełnego zakresu bot-test. Powód nie leży już w core packu, tylko w dodatkowych istniejących smoke’ach: w czasie testu Google OAuth/refresh zwracał błąd zakresów i przez kilka minut Sheets/Calendar były niedostępne. To zablokowało część scenariuszy, które trzeba powtórzyć po stabilizacji autoryzacji Google.

## Co zostało zmienione

- Naprawiłem dostęp E2E: obecny Telegram admin `1690210103` został przypisany w Supabase do beta usera `bd381405-66d2-4544-b817-117f8f8de441`.
- Dodałem kategorię E2E `core_smoke` z brakującymi scenariuszami SM-1, SM-2 voice, SM-3, SM-7 i SM-10.
- Dodałem wysyłkę pliku jako prawdziwy voice note przez Telethon.
- Dodałem obsługę różnic z voice/STT: syntetyczne nazwy po transkrypcji mogą stracić myślniki, więc testy i cleanup rozpoznają też format `E2E Beta ...`.
- Wzmocniłem izolację scenariuszy: przed niezależnymi smoke’ami czyszczony jest pending flow i wygaszana historia rozmowy.
- Wydłużyłem timeouty tam, gdzie realny bot wolniej odpowiada po LLM/Google.
- Rozszerzyłem cleanup Sheets/Calendar o nazwy po voice-STT.

## Preflight i dostęp

| Obszar | Wynik | Uwagi |
|---|---:|---|
| Mapowanie Telegram -> beta user | OK | Przed update sprawdzone, że żaden inny user nie miał `telegram_id=1690210103`. |
| Supabase schema check | OK | Widoczne tabele photo/offers oraz bucket `offer-logos`. |
| Google Sheets | OK po poprawce | W arkuszu była literówka `Data nastepnego kroku`; poprawione na `Data następnego kroku`. |
| Google Calendar | OK w finalnym core runie | Wydarzenia były tworzone i potem sprzątane. |
| Google Drive/photo | OK | Photo smoke przeszedł razem z uploadem i cleanup folderu. |
| Fixture’y | OK | Po finalnym cleanupie fixture’y zostały na miejscu. |

Zasoby beta usera:

- Sheet: `17X2Xy9tFy0FsLW8g_AXbfu6OAqEqCTPIEQUDFQQy9FE`
- Calendar: `a23845212ef26ca63e14bce2e83c3f311cbb8268d3030c03f8a70fef186dd1bd@group.calendar.google.com`
- Drive folder: `1514ECM8Cp82uH09fxyB8u0d4oIVjjaSc`

## Wyniki core smoke

Finalny raport surowy: `output/smoke/core-smoke-2026-05-19-pass.md`

| Scenariusz | Wynik | Co sprawdził |
|---|---:|---|
| SM-1 spotkanie + nowy klient | PASS | Bot najpierw pokazał kartę spotkania, bez zapisu do Google przed kliknięciem. Po kliknięciu powstało wydarzenie Calendar, potem karta klienta i dopiero po drugim kliknięciu wiersz Sheets. |
| SM-2 voice | PASS | Lokalny głos po polsku został wysłany jako voice note. Bot pokazał transkrypcję, po kliknięciu `Zapisz` przeszedł w ten sam flow co SM-1. |
| SM-3 telefon nie oznacza spotkania | PASS | Tekst z telefonem i słowem „jutro” został rozpoznany jako klient/notatka, nie jako spotkanie. Po zapisie powstał tylko wiersz Sheets, bez Calendar. |
| SM-7 spotkanie z nowym klientem | PASS | Spotkanie zostało zapisane po potwierdzeniu, potem bot dosiał kartę klienta i zapisał klienta dopiero po drugim kliknięciu. |
| SM-10 pamięć po 31 minutach | PASS | Po wymuszeniu wygaśnięcia historii bot nie dopisał notatki „w ciemno”, tylko poprosił o wskazanie klienta. |

Najważniejszy wynik produktu: potwierdzenie przed zapisem działa w core flow. Testy potwierdziły brak zapisu do Sheets/Calendar przed kliknięciem przycisku `Zapisać`.

## Wyniki istniejących smoke’ów

Raport surowy: `output/smoke/core-existing-2026-05-19.md`

| Scenariusz | Wynik | Uwagi |
|---|---:|---|
| SM-4 telefoniczne spotkanie | FAIL środowiskowy | Karta była poprawna i bez zapisu przed kliknięciem, ale Calendar zwrócił komunikat niedostępności po kliknięciu. W logach Railway w tym oknie były błędy Google refresh `invalid_scope`. |
| SM-5 anulowanie | PASS z drift | Nie było drugiego pytania „na pewno?”, ale karta została edytowana w miejscu bez osobnej linii `Anulowane.`. |
| SM-6 plan dnia | PASS | Odpowiedź była po polsku, bez przycisków mutacji i bez technicznych danych. |
| Duplicate / Dopisać / Aktualizuj | BLOCKER środowiskowy | Setup nie mógł zapisać klienta, bo Sheets był chwilowo niedostępny. |
| Disambiguation Jan Kowalski | FAIL | Bot odpowiedział, że nie ma Jana Kowalskiego w bazie, mimo że test oczekuje fixture’ów Warszawa/Kraków. Do sprawdzenia po reseedzie i stabilizacji Google. |
| R7 następny krok po dodaniu klienta | BLOCKER środowiskowy | Zablokowane przez Sheets unavailable. |
| SM-9 aktywny klient / notatka | BLOCKER środowiskowy | Zablokowane przez Sheets unavailable. |

To nie jest czysty wynik aplikacyjny, bo trzy scenariusze nie przeszły setupu przez zewnętrzny problem Google auth. Trzeba je powtórzyć po naprawie lub odświeżeniu autoryzacji Google.

## Photo / Drive smoke

Raport surowy: `output/smoke/photo-smoke-2026-05-19.md`

Wynik: PASS.

Co zostało potwierdzone:

- klient nie istniał przed akcją,
- przed kliknięciem nie było zapisu zdjęcia do Drive ani metadanych do Sheets,
- po kliknięciu `Zapisać` powstał plik w Drive,
- Sheets dostał `Zdjęcia=1` i link do folderu zdjęć,
- folder Drive i dane testowe zostały sprzątnięte.

## Cleanup po testach

Po finalnym core runie cleanup był bezpieczny:

- usunięte wiersze Sheets: 5,
- usunięte wydarzenia Calendar: 3,
- pending flow wyczyszczony,
- historia rozmowy przesunięta poza 31-minutowe okno,
- fixture’y testowe zostały zachowane.

## Automatyczne testy

| Komenda | Wynik |
|---|---:|
| `pytest tests_e2e/tests -q` | 227 passed |
| `pytest tests/handlers/test_voice_handler.py tests/test_database_photo_sessions.py tests/test_google_sheets.py::test_update_client_photo_metadata_does_not_touch_last_contact -q` | 17 passed |

## Otwarte błędy i drifty

1. Google OAuth refresh / zakresy
   - W czasie istniejących smoke’ów Railway logował `invalid_scope`, a bot odpowiadał, że Sheets lub Calendar są chwilowo niedostępne.
   - Skutek: SM-4, duplicate, R7 i SM-9 nie dają jeszcze wiarygodnego wyniku produktowego.

2. Disambiguation Jan Kowalski
   - Scenariusz oczekiwał dwóch fixture’ów, a bot odpowiedział „Nie mam Jana Kowalskiego w bazie”.
   - Możliwe przyczyny: problem z fixture query, prefiks `E2E-Beta-Fixture-`, wcześniejszy cleanup fixture’ów albo search po innej formie nazwy.

3. Cancel drift
   - Produktowo ważne: nie ma pętli „na pewno?”, więc główna reguła jest spełniona.
   - Drift względem spec: brak osobnej odpowiedzi `Anulowane.`

4. Phone-call card drift
   - Karta telefonicznego spotkania działa jako mutation card, ale test oznacza brak ikony telefonu jako znany drift.

## Plan napraw

1. Ustabilizować Google OAuth dla beta usera:
   - porównać obecne scope’y w kodzie i scope’y zapisane przy tokenie,
   - sprawdzić, czy token wymaga ponownej autoryzacji po dodaniu/zmianie scope’ów,
   - dodać preflight „token refresh + Sheets read + Calendar read” przed live smoke.

2. Powtórzyć zablokowane smoke’i po naprawie Google:
   - SM-4 phone_call,
   - duplicate / Dopisać / Aktualizuj,
   - R7,
   - SM-9 active-client note.

3. Rozdzielić fixture’y od naturalnego wyszukiwania:
   - sprawdzić, czy komenda `pokaż Jana Kowalskiego` ma znajdować fixture `E2E-Beta-Fixture-Jan-Kowalski`,
   - jeśli tak, dostosować matcher testowy lub seed,
   - jeśli nie, zmienić fixture na nazwę bliższą realnemu klientowi.

4. Podjąć decyzję produktową o driftach:
   - czy cancel musi wysyłać osobne `Anulowane.`,
   - czy karta phone-call musi mieć ikonę telefonu.

5. Po poprawkach uruchomić:
   - `pytest tests_e2e/tests -q`,
   - targeted voice/photo tests,
   - pełny core smoke,
   - zablokowany existing smoke pack,
   - photo smoke.

## Rekomendacja

Core agent można traktować jako gotowy do dalszej stabilizacji. Nie promowałbym jeszcze `develop -> main`, dopóki Google OAuth blocker i disambiguation nie zostaną wyjaśnione i zablokowane smoke’i nie przejdą ponownie.
