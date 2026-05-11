# OZE-Agent — Mapa Zachowań i Workflow Agenta

_Wersja robocza do review Maana — 27.04.2026_

Ten dokument opisuje, jak agent ma rozmawiać z użytkownikiem, co pokazuje,
kiedy pyta, kiedy zapisuje oraz co dokładnie trafia do Google Sheets,
Google Calendar i Supabase. To nie jest opis marketingowy. To mapa zachowania,
na której dopracowujemy agenta do końca.

## 0. Najważniejsza Zasada

Agent nie ma być „LLM-em, który improwizuje”. Agent ma być deterministycznym
systemem workflow, w którym LLM pełni rolę parsera języka.

Warstwy:

1. **Telegram input** — tekst, głos, przycisk, komenda `/cancel`.
2. **Guards** — czy użytkownik jest znany, prywatny chat, limity, pending flow.
3. **Intent router** — rozpoznaje jedną intencję przez Anthropic tool-use.
4. **Parser danych** — wyciąga klienta, datę, godzinę, telefon, adres, produkt.
5. **Deterministyczny safety-net** — dogrywa oczywiste rzeczy regexami i regułami.
6. **Pending state** — karta oczekująca na `Zapisać / Dopisać / Anulować`.
7. **Mutation layer** — dopiero po potwierdzeniu zapisuje do Sheets / Calendar.
8. **Renderer** — pokazuje krótką kartę lub wynik.
9. **Logs** — bez PII; logujemy decyzje, nie dane klienta.

Każdy bug produkcyjny ma zostać zamieniony w test i scenariusz w tym dokumencie.

## 1. Środowiska i Proces Testowania

1. **Produkcja**
   - Telegram: główny bot OZE-Agent.
   - Railway service: `bot`.
   - Branch: `main`.
   - Aktualny commit: `961fad1`.

2. **Test**
   - Telegram: `t.me/OZEAgentTestBot`.
   - Railway service: `bot-test`.
   - Branch: `develop`.
   - Aktualny commit: `961fad1`.
   - Ma osobny Telegram token.
   - Może nadal używać tych samych Google Sheets / Calendar / Supabase co produkcja.
   - Do testów używamy fikcyjnych danych.

3. **Promocja zmian**
   - Fix trafia najpierw na `develop`.
   - Testujemy na `bot-test`.
   - Dopiero po akceptacji Maana promujemy na `main`.
   - Po deployu produkcji robimy krótki smoke test.

## 2. Zasady Globalne

### 2.1. Brak zapisu bez potwierdzenia

Agent nigdy nie zapisuje do Sheets ani Calendar bez jawnego kliknięcia:

```text
✅ Zapisać
```

Wyjątki read-only:
- `show_client`
- `show_day_plan`
- ogólna odpowiedź bez mutacji

### 2.2. Standardowa karta mutacyjna

Każda mutacja używa wzorca:

```text
<co agent zrozumiał>
<braki, jeśli są>

✅ Zapisać
➕ Dopisać
❌ Anulować
```

Znaczenie:

1. `✅ Zapisać` — commit.
2. `➕ Dopisać` — pending zostaje otwarty, następna wiadomość doprecyzowuje dane.
3. `❌ Anulować` — jeden klik, pending znika, zero zapisu.

### 2.3. Braki danych

`Brakuje:` pokazuje tylko pola ważne operacyjnie:
- Telefon
- Email
- Miasto
- Adres
- Produkt
- Notatki
- Następny krok
- Data następnego kroku
- Źródło pozyskania

Nie pytamy o parametry techniczne jako osobne braki, jeśli można je zapisać
w `Notatki`, np. moc instalacji, moc magazynu, metraż, kierunek dachu.

### 2.4. Logs

Logi klasyfikatora mają mieć kształt:

```text
intent classify: tool=record_add_meeting preflight_meeting_hint=True message_len=...
```

Log nie może zawierać:
- imienia i nazwiska,
- telefonu,
- adresu,
- treści wiadomości,
- `message_prefix`.

## 3. Źródła Danych i Miejsca Zapisu

### 3.1. Google Sheets

Sheets jest bazą klientów. Kanoniczne pola używane przez agenta:

| Pole | Znaczenie | Kiedy zmieniane |
|---|---|---|
| `Imię i nazwisko` | klient | `add_client`, preseed po `add_meeting` |
| `Telefon` | numer kontaktowy | `add_client`, uzupełnianie pustych pól przy `add_meeting` |
| `Email` | email | `add_client`, uzupełnianie pustych pól |
| `Miasto` / `Miejscowość` | miasto | `add_client`, parser spotkania |
| `Adres` | ulica + numer | `add_client`, parser spotkania |
| `Status` | etap lejka | `change_status`, auto-upgrade po spotkaniu |
| `Produkt` | typ produktu | `add_client`, parser spotkania |
| `Notatki` | historia i szczegóły | `add_note`, dane techniczne |
| `Data pierwszego kontaktu` | data utworzenia klienta | automatycznie przy `add_client` |
| `Data ostatniego kontaktu` | ostatnia mutacja kontaktowa | automatycznie przez touching update |
| `Następny krok` | etykieta działania | `add_meeting` |
| `Data następnego kroku` | data/godzina działania | `add_meeting` |
| `Źródło pozyskania` | lead source | `add_client` jeśli znane |
| `ID wydarzenia Kalendarz` | link techniczny do eventu | `add_meeting` |

### 3.2. Google Calendar

Calendar jest miejscem zaplanowanych działań:

| `event_type` | Etykieta w Sheets `Następny krok` | Domyślny sens |
|---|---|---|
| `in_person` | `Spotkanie` | spotkanie fizyczne |
| `phone_call` | `Telefon` | rozmowa telefoniczna |
| `offer_email` | `Wysłać ofertę` | wysyłka oferty |
| `doc_followup` | `Follow-up dokumentowy` | dopilnowanie dokumentów |

Calendar event zawiera:
- title,
- start,
- end,
- location,
- description,
- `extendedProperties.private.event_type`.

### 3.3. Supabase / DB

Supabase trzyma systemowe dane:
- użytkownicy,
- pending flow,
- historia rozmowy,
- morning brief dedup,
- konfiguracja.

Pending flow typy:

1. `add_client`
2. `add_client_duplicate`
3. `add_note`
4. `change_status`
5. `add_meeting`
6. `add_meeting_disambiguation`
7. `disambiguation`
8. `r7_prompt`
9. `voice_transcription` (legacy shape, zapis przez helper DB)

## 4. Klasyfikacja Intencji

### 4.1. Intencje MVP

| Tool | Intent | Co oznacza |
|---|---|---|
| `record_add_client` | `ADD_CLIENT` | dodanie klienta bez konkretnego terminu działania |
| `record_show_client` | `SHOW_CLIENT` | pokazanie istniejącego klienta |
| `record_add_note` | `ADD_NOTE` | dopisanie notatki bez elementu czasowego |
| `record_change_status` | `CHANGE_STATUS` | zmiana statusu klienta |
| `record_add_meeting` | `ADD_MEETING` | spotkanie / telefon / oferta / follow-up z datą |
| `record_show_day_plan` | `SHOW_DAY_PLAN` | plan dnia / tygodnia |
| `record_general_question` | `GENERAL_QUESTION` | pytanie ogólne |

### 4.2. Safety-net dla spotkań

Jeśli wiadomość ma jednocześnie:

1. marker spotkania / telefonu / oferty / follow-upu, oraz
2. marker czasu (`jutro`, `pojutrze`, godzina, `o 14`, `14:00`),

router wymusza:

```text
tool_choice = record_add_meeting
```

To zabezpiecza przypadek, w którym użytkownik mówi dużo danych klienta
i LLM błędnie wybiera `ADD_CLIENT`.

Przykład:

```text
Dodaj spotkanie z Janem jutro o 14. Telefon 600100200. Marki, Zielona 28. Fotowoltaika.
```

Wynik:

```text
ADD_MEETING
```

Nie:

```text
ADD_CLIENT
```

### 4.3. Samo pole `telefon` nie oznacza spotkania

To nie może wymuszać `ADD_MEETING`:

```text
Dodaj klienta Jan Kowalski, telefon 600100200, jutro podeślę dane
```

To jest `ADD_CLIENT` albo doprecyzowanie klienta.

To może oznaczać `ADD_MEETING`:

```text
Zadzwoń do Marka jutro o 10
Telefon do Marka pojutrze o 9
Rozmowa telefoniczna z Anną w środę o 12
```

## 5. Workflow Głosowy

### V-1. Głosówka do transkrypcji

Użytkownik wysyła voice/audio.

Kroki:

1. `handle_voice()`
2. Guard: prywatny chat + aktywny użytkownik.
3. Pobranie pliku z Telegrama.
4. Whisper STT.
5. Claude Haiku post-pass dla polskich nazw.
6. Zapis kosztu interakcji.
7. Zapis pending:

```text
flow_type = voice_transcription
flow_data = {
  transcription,
  confidence,
  whisper_cost,
  postproc_cost,
  fallback
}
```

Bot pokazuje:

```text
🎙 Transkrypcja (pewność: XX%):

<tekst transkrypcji>

Co z tym?

✅ Zapisz
❌ Anuluj
```

Zapisy:
- Sheets: brak
- Calendar: brak
- Supabase: pending voice + interaction cost

### V-2. Kliknięcie `✅ Zapisz`

Kroki:

1. Bot bierze tekst transkrypcji.
2. Przekazuje go do normalnego `handle_text(text_override=...)`.
3. Dalej działa zwykły router intencji.

Przykład:

```text
Zapisz spotkanie z Markiem jutro o 14, Marki, Zielona 28, telefon 600100200.
```

Oczekiwane:
- karta `Dodać spotkanie?`
- nie karta `Dodać klienta?`

Zapisy przed kolejnym `✅ Zapisać` na karcie spotkania:
- Sheets: brak
- Calendar: brak
- Supabase: pending spotkania

### V-3. Kliknięcie `❌ Anuluj`

Efekt:
- pending voice usunięty,
- brak zapisu do Sheets,
- brak zapisu do Calendar,
- bot odpowiada krótko: `❌ Anulowane.`

## 6. Workflow `ADD_CLIENT`

### AC-1. Nowy klient z kompletem danych

Input:

```text
Dodaj klienta Jan Testowy z Marek, telefon 600100200, Zielona 28, fotowoltaika i magazyn energii, źródło Facebook.
```

Decyzja:

```text
Intent = ADD_CLIENT
```

Funkcje:

1. `classify()`
2. `handle_add_client()`
3. `extract_client_data()`
4. `_filter_invalid_products()`
5. `format_add_client_card()`
6. `save_pending(PendingFlowType.ADD_CLIENT)`

Karta:

```text
📋 Jan Testowy, ul. Zielona 28, Marki
PV + Magazyn energii
Tel. 600 100 200
Źródło pozyskania: Facebook
Zapisać / dopisać / anulować?

✅ Zapisać
➕ Dopisać
❌ Anulować
```

Przed kliknięciem:
- Sheets: brak zapisu
- Calendar: brak zapisu
- Supabase: pending `add_client`

Po `✅ Zapisać`:

Funkcje:

1. `handle_confirm()`
2. `_confirm_add_client()`
3. `commit_add_client()`
4. `create_client_row()`
5. `google_sheets.add_client()`
6. `send_next_action_prompt()`

Sheets:
- nowy wiersz,
- `Imię i nazwisko = Jan Testowy`,
- `Telefon = 600100200`,
- `Miasto = Marki`,
- `Adres = ul. Zielona 28`,
- `Produkt = PV + Magazyn energii`,
- `Źródło pozyskania = Facebook`,
- `Data pierwszego kontaktu` ustawiana automatycznie przez wrapper,
- inne pola według rozpoznanych danych.

Calendar:
- w aktualnym kodzie brak eventu dla zwykłego `add_client`.
- jeśli ma powstać follow-up, robi to dopiero R7 / `ADD_MEETING`.

Bot:

```text
✅ Zapisane.
Co dalej z Jan Testowy z Marki? Spotkanie, telefon, mail, odłożyć na później?
```

Stan:
- Supabase pending `r7_prompt`

### AC-2. Nowy klient z brakami

Input:

```text
Dodaj klienta Jan Brakowy z Radomia.
```

Karta:

```text
📋 Jan Brakowy, Radom
❓ Brakuje: Telefon, Email, Adres, Produkt, Notatki, Następny krok, Data następnego kroku, Źródło pozyskania
Zapisać / dopisać / anulować?

✅ Zapisać
➕ Dopisać
❌ Anulować
```

Po `➕ Dopisać` i wiadomości:

```text
telefon 600200300, interesuje go pompa ciepła
```

Kroki:

1. `_route_pending_flow()`
2. ścieżka augment `add_client`
3. `extract_client_data()` na dopisanej wiadomości
4. merge danych
5. rebuild karty

Zapisy:
- do momentu kliknięcia `✅ Zapisać` nic nie trafia do Sheets/Calendar.

### AC-3. Duplikat klienta

Input:

```text
Dodaj klienta Jan Kowalski Warszawa, telefon 600100200.
```

Jeśli Sheets ma jednego Jana Kowalskiego z Warszawy:

Bot pokazuje routing:

```text
Ten klient już jest w arkuszu:
Jan Kowalski — Warszawa

Co robimy?

[Nowy] [Aktualizuj]
```

`[Nowy]`:
- tworzy świadomy nowy wiersz po standardowej karcie `ADD_CLIENT`.

`[Aktualizuj]`:
- tworzy pending `add_client_duplicate`.
- po `✅ Zapisać` wywołuje `commit_update_client_fields()`.

Sheets przy aktualizacji:
- aktualizuje wskazany istniejący wiersz,
- `Data ostatniego kontaktu` jest bumpowana przez `update_client_row_touching_contact()`.

Calendar:
- brak eventu.

Po udanej aktualizacji:

```text
✅ Dane zaktualizowane.
Co dalej z Jan Kowalski z Warszawa?
```

## 7. Workflow `ADD_MEETING`

### AM-1. Spotkanie z istniejącym klientem

Input:

```text
Dodaj spotkanie z Janem Kowalskim jutro o 14.
```

Decyzja:

```text
Intent = ADD_MEETING
event_type = in_person
```

Funkcje:

1. `classify()`
2. `_meeting_preflight_hint()` jeśli są markery
3. `handle_add_meeting()`
4. `extract_meeting_data()`
5. `_extract_meeting_client_data()`
6. `_enrich_meeting()`
7. `check_conflicts()`
8. `save_pending(PendingFlowType.ADD_MEETING)`

Karta:

```text
✅ Dodać spotkanie?

• Klient: Jan Kowalski
• Data: <jutro> (dzień)
• Godzina: 14:00
• Czas trwania: 60 min
• Miejsce: <z danych klienta albo wiadomości>

✅ Zapisać
➕ Dopisać
❌ Anulować
```

Przed kliknięciem:
- Sheets: brak zapisu
- Calendar: brak zapisu
- Supabase: pending `add_meeting`

Po `✅ Zapisać`:

Funkcje:

1. `handle_confirm()`
2. `commit_add_meeting()`
3. `google_calendar.create_event()`
4. `update_client_row_touching_contact()`

Calendar:
- tworzy event.
- `title = Spotkanie — Jan Kowalski` albo etykieta zależna od typu.
- `start = data/godzina`.
- `end = start + duration`.
- `location = miejsce`.
- `description = opis spotkania + dane klienta`.
- `event_type = in_person`.

Sheets:
- `Następny krok = Spotkanie`,
- `Data następnego kroku = start.isoformat()`,
- `ID wydarzenia Kalendarz = calendar_event_id`,
- `Data ostatniego kontaktu` bumpowana automatycznie,
- jeśli status pusty lub `Nowy lead`, to `Status = Spotkanie umówione`,
- jeśli `client_updates` ma wartości dla pustych pól, uzupełnia tylko puste pola.

Bot:

```text
✅ Spotkanie dodane do kalendarza. Status klienta: Spotkanie umówione.
```

R7:
- nie odpala się, bo spotkanie samo definiuje następny krok.

### AM-2. Spotkanie + dane klienta, klient nie istnieje

Input:

```text
Dodaj spotkanie z Janem Nowym na jutro o 14. Mieszka w Markach na ulicy Zielonej 28. Telefon 600-100-200. Interesuje go fotowoltaika i magazyn energii.
```

Decyzja:

```text
Intent = ADD_MEETING
```

Najważniejszy kontrakt:
- nie wolno wybrać `ADD_CLIENT`,
- najpierw ma powstać karta spotkania,
- dane klienta muszą zostać przeniesione do późniejszego draftu klienta.

Karta 1:

```text
✅ Dodać spotkanie?

• Klient: Jan Nowy
• Data: <jutro>
• Godzina: 14:00
• Czas trwania: 60 min
• Miejsce: Marki, ul. Zielona 28

✅ Zapisać
➕ Dopisać
❌ Anulować
```

Po `✅ Zapisać`:

Calendar:
- event spotkania powstaje zawsze, nawet jeśli klient nie istnieje w Sheets.

Sheets:
- jeszcze brak wiersza klienta, bo klient nie istnieje.

Bot pokazuje od razu kartę klienta z preseed:

```text
✅ Spotkanie dodane.
📋 Jan Nowy, ul. Zielona 28, Marki
PV + Magazyn energii
Tel. 600 100 200
Status: Spotkanie umówione
❓ Brakuje: Email, Notatki, Następny krok, Data następnego kroku, Źródło pozyskania
Zapisać / dopisać / anulować?

✅ Zapisać
➕ Dopisać
❌ Anulować
```

Supabase:
- nowy pending `add_client` z `client_data` zebranym z wiadomości spotkania.

Po kolejnym `✅ Zapisać`:
- Sheets dostaje nowy wiersz klienta.
- Calendar nie tworzy drugiego eventu.

### AM-3. Spotkanie + dane klienta, klient istnieje

Input:

```text
Dodaj spotkanie z Markiem Testowym jutro o 15. Telefon 600123123. Interesuje go magazyn energii.
```

Jeśli Marek istnieje w Sheets:

Calendar:
- event spotkania powstaje.

Sheets:
- `Następny krok`, `Data następnego kroku`, `ID wydarzenia Kalendarz`,
- auto status jeśli dotyczy,
- `Telefon` / `Produkt` tylko jeśli w istniejącym wierszu są puste.

Nie wolno:
- nadpisać istniejącego telefonu,
- nadpisać istniejącego produktu,
- nadpisać istniejącego adresu, jeśli jest już uzupełniony.

### AM-4. Rozmowa telefoniczna

Input:

```text
Zadzwoń do Marka Testowego pojutrze o 10.
```

Decyzja:

```text
Intent = ADD_MEETING
event_type = phone_call
```

Calendar:
- title: `Telefon — Marek Testowy`
- duration: zwykle 15 min
- location: telefonicznie lub puste / telefon klienta
- `event_type = phone_call`

Sheets:
- `Następny krok = Telefon`
- `Data następnego kroku = start.isoformat()`
- `ID wydarzenia Kalendarz = event_id`
- `Data ostatniego kontaktu` bumpowana

Status:
- nie robi auto-upgrade do `Spotkanie umówione`, bo to nie jest `in_person`.

### AM-5. Konflikt kalendarza

Jeśli `check_conflicts()` znajduje event w tym czasie, karta ma ostrzeżenie:

```text
⚠️ Uwaga: masz już spotkanie o tej porze:
Spotkanie — E2E-Beta-Tester-...

✅ Zapisać
➕ Dopisać
❌ Anulować
```

Po `✅ Zapisać`:
- agent tworzy nowe wydarzenie mimo konfliktu.

Do decyzji produktowej:
- czy w przyszłości dodać przycisk „zmień godzinę”.
- obecnie `Dopisać` może doprecyzować dane, ale nie jest pełnym reschedule UX.

## 8. Workflow `ADD_NOTE`

### AN-1. Czysta notatka

Input:

```text
Dodaj notatkę do Jana Kowalskiego Warszawa: klient pyta o większy magazyn.
```

Funkcje:

1. `classify()`
2. `handle_add_note()`
3. `search_clients()`
4. `save_pending(PendingFlowType.ADD_NOTE)`
5. `format_add_note_card`

Karta:

```text
📝 Dodać notatkę?

• Klient: Jan Kowalski
• Notatka: klient pyta o większy magazyn

✅ Zapisać
➕ Dopisać
❌ Anulować
```

Po `✅ Zapisać`:

Funkcje:
- `_confirm_add_note()`
- `commit_add_note()`
- `update_client_row_touching_contact()`

Sheets:
- `Notatki = <stare>; [DD.MM.YYYY]: klient pyta o większy magazyn`
- `Data ostatniego kontaktu` bumpowana automatycznie

Calendar:
- brak eventu

Bot:

```text
✅ Notatka dodana.
```

R7:
- aktualny kod nie odpala R7 po czystej notatce.
- jeśli chcemy inaczej, to jest decyzja do review.

### AN-2. Notatka z przyszłą akcją

Input:

```text
Dodaj notatkę do Jana: dzwonił w sprawie awarii PV. Zadzwonić w piątek.
```

Stan aktualny:
- może zostać potraktowane jako notatka,
- Calendar follow-up nie jest gwarantowany.

Docelowo do decyzji:
- czy agent ma automatycznie zaproponować `ADD_MEETING event_type=phone_call`,
- czy najpierw zapisać notatkę i zapytać R7,
- czy w ogóle nie robić Calendar z notatek.

Rekomendacja:
- jeśli notatka zawiera przyszłą akcję i datę, agent powinien pokazać kartę compound:

```text
📝 + 📅 Zapisać?

• Notatka: dzwonił w sprawie awarii PV
• Telefon: piątek, 10:00

✅ Zapisać
➕ Dopisać
❌ Anulować
```

Po commit:
- Sheets: notatka + J bump
- Calendar: telefon
- Sheets K/L/P: Telefon + data + event_id

## 9. Workflow `CHANGE_STATUS`

### CS-1. Zmiana statusu

Input:

```text
Zmień status Jana Kowalskiego Warszawa na Oferta wysłana.
```

Funkcje:

1. `classify()`
2. `handle_change_status()`
3. `search_clients()`
4. `save_pending(PendingFlowType.CHANGE_STATUS)`

Karta:

```text
📊 Zmienić status?

• Klient: Jan Kowalski
• Status: Nowy lead → Oferta wysłana

✅ Zapisać
➕ Dopisać
❌ Anulować
```

Po `✅ Zapisać`:

Funkcje:
- `_confirm_change_status()`
- `commit_change_status()`
- `update_client_row_touching_contact()`

Sheets:
- `Status = Oferta wysłana`
- `Data ostatniego kontaktu` bumpowana

Calendar:
- brak eventu w aktualnym kodzie

Bot:

```text
✅ Status zmieniony na: Oferta wysłana
Co dalej z Janem Kowalskim z Warszawa?
```

Supabase:
- pending `r7_prompt`

### CS-2. Status + spotkanie w jednej wiadomości

Input:

```text
Wojtek podpisał, spotkanie jutro o 14.
```

Decyzja:

```text
Intent = ADD_MEETING
status_update = { field: "Status", new_value: "Podpisane" }
```

Po `✅ Zapisać` na karcie spotkania:

Calendar:
- event spotkania.

Sheets:
- `Status = Podpisane`,
- `Następny krok = Spotkanie`,
- `Data następnego kroku = start`,
- `ID wydarzenia Kalendarz = event_id`,
- `Data ostatniego kontaktu` bumpowana.

R7:
- nie odpala się, bo spotkanie jest następnym krokiem.

## 10. Workflow `SHOW_CLIENT`

Input:

```text
Pokaż Jana Kowalskiego Warszawa.
```

Funkcje:

1. `classify()`
2. `handle_show_client()` / obecna ścieżka w `handle_text`
3. `search_clients()`
4. renderer karty klienta

Efekt:
- read-only.

Sheets:
- tylko odczyt.

Calendar:
- brak.

Bot pokazuje wszystkie niepuste pola z Sheets poza technicznymi:
- `_row`
- `Link do zdjęć`
- `ID wydarzenia Kalendarz`
- `Wiersz`

Przy wielu wynikach:

```text
Mam 2 Kowalskich:
1. Jan Kowalski — Warszawa
2. Piotr Kowalski — Piaseczno
Którego?
```

## 11. Workflow `SHOW_DAY_PLAN`

Input:

```text
Co mam jutro?
```

Decyzja:

```text
Intent = SHOW_DAY_PLAN
```

Efekt:
- read-only.

Calendar:
- odczyt eventów na dzień / zakres.

Sheets:
- może być odczyt danych klientów do wzbogacenia planu, ale bez zapisu.

Bot:
- pokazuje plan dnia z godzinami, tytułami, lokalizacją i danymi klienta, jeśli dostępne.

Nie wolno:
- tworzyć spotkania tylko dlatego, że padło `jutro`.
- wymuszać `ADD_MEETING`, jeśli brak markerów spotkania/telefonu/oferty.

## 12. Pending Flow i Przyciski

### PF-1. `✅ Zapisać`

Zawsze:

1. Pobiera pending z Supabase.
2. Wybiera handler po `flow_type`.
3. Robi commit.
4. Usuwa pending, chyba że handler tworzy kolejny pending, np. R7 albo preseed add_client.

### PF-2. `➕ Dopisać`

Zawsze:
- pending zostaje,
- następna wiadomość jest traktowana jako uzupełnienie,
- karta jest przebudowana.

### PF-3. `❌ Anulować`

Zawsze:
- pending usunięty,
- brak write,
- odpowiedź krótka.

### PF-4. `/cancel`

Input:

```text
/cancel
```

Funkcje:
- `handle_cancel_command()`
- `get_pending_flow()`
- `delete_pending_flow()`

Jeśli pending istnieje:

```text
❌ Anulowane.
```

Jeśli pending nie istnieje:

```text
Nie ma żadnej aktywnej operacji do anulowania.
```

## 13. R7 — Pytanie „Co Dalej?”

R7 to osobny pending po udanej mutacji, gdy nie ma jeszcze następnego kroku.

Obecnie odpala po:
- `add_client`,
- aktualizacji duplikatu klienta,
- `change_status`.

Obecnie nie odpala po:
- `add_meeting`,
- `add_note`,
- voice confirmation samym w sobie,
- read-only.

Karta / wiadomość:

```text
✅ Zapisane.
Co dalej z Janem Kowalskim z Warszawa? Spotkanie, telefon, mail, odłożyć na później?
```

Jeśli użytkownik odpowie:

```text
telefon w piątek o 10
```

Agent powinien przejść do `ADD_MEETING event_type=phone_call`.

Jeśli odpowie:

```text
nie wiem
```

Flow kończy się bez zapisu.

## 14. Błędy i Fallbacki

### ERR-1. Anthropic / LLM error

Oczekiwane:
- brak pustej wiadomości do Telegrama,
- bot odpowiada fallbackiem typu:

```text
Co chcesz zrobić?
```

### ERR-2. Calendar failure przy `ADD_MEETING`

Jeśli `create_event()` zwraca błąd:
- Sheets nie powinien być aktualizowany,
- bot pokazuje błąd,
- pending może zostać usunięty lub użytkownik musi zacząć od nowa.

### ERR-3. Sheets failure po utworzeniu Calendar eventu

Przy `ADD_MEETING` pipeline jest Calendar → Sheets.

Jeśli Calendar się udał, a Sheets nie:

Calendar:
- event istnieje.

Sheets:
- brak sync K/L/P/F.

Bot:

```text
✅ Spotkanie dodane do kalendarza. Nie udało się zaktualizować arkusza.
```

To jest partial success, nie pełna atomowość.

### ERR-4. Wielu klientów przy spotkaniu

Jeśli agent nie może jednoznacznie wybrać klienta:
- pokazuje disambiguation,
- po wyborze tworzy pending `ADD_MEETING`,
- po `Żaden z nich` traktuje klienta jako nowego i zachowuje `source_client_data`.

## 15. Scenariusze Rozmów End-to-End

### S-1. Tekst: spotkanie z nowym klientem

User:

```text
Dodaj spotkanie z Janem Testowym na jutro o 14. Mieszka w Markach na ulicy Zielonej 28. Telefon 600-100-200. Interesuje go fotowoltaika i magazyn energii.
```

Agent:

```text
✅ Dodać spotkanie?

• Klient: Jan Testowy
• Data: 28.04.2026 (wtorek)
• Godzina: 14:00
• Czas trwania: 60 min
• Miejsce: Marki, ul. Zielona 28

✅ Zapisać
➕ Dopisać
❌ Anulować
```

User klika:

```text
✅ Zapisać
```

Agent:

```text
✅ Spotkanie dodane.
📋 Jan Testowy, ul. Zielona 28, Marki
PV + Magazyn energii
Tel. 600 100 200
Status: Spotkanie umówione
❓ Brakuje: Email, Notatki, Następny krok, Data następnego kroku, Źródło pozyskania
Zapisać / dopisać / anulować?
```

Zapisy po pierwszym kliknięciu:
- Calendar: event spotkania.
- Sheets: jeszcze brak klienta, bo to nowy klient.
- Supabase: pending `add_client`.

User klika:

```text
✅ Zapisać
```

Zapisy po drugim kliknięciu:
- Sheets: nowy wiersz klienta z danymi z transkrypcji.
- Calendar: bez nowego eventu.

### S-2. Głosówka: spotkanie z nowym klientem

User wysyła głosówkę:

```text
Zapisz spotkanie z Janem Testowym na jutro o 14...
```

Agent:

```text
🎙 Transkrypcja (pewność: 54%):

Zapisz spotkanie z Janem Testowym...

Co z tym?

✅ Zapisz
❌ Anuluj
```

User:

```text
✅ Zapisz
```

Dalej identycznie jak S-1.

### S-3. Add client bez terminu

User:

```text
Dodaj klienta Anna Testowa z Radomia, telefon 600200300, pompa ciepła.
```

Agent:

```text
📋 Anna Testowa, Radom
Pompa ciepła
Tel. 600 200 300
❓ Brakuje: Email, Adres, Notatki, Następny krok, Data następnego kroku, Źródło pozyskania
Zapisać / dopisać / anulować?
```

Po `✅ Zapisać`:
- Sheets: nowy klient.
- Calendar: brak.
- R7: agent pyta co dalej.

### S-4. Telefon jako spotkanie

User:

```text
Zadzwoń do Marka Testowego pojutrze o 10.
```

Agent:

```text
✅ Dodać spotkanie?

• Klient: Marek Testowy
• Data: pojutrze
• Godzina: 10:00
• Czas trwania: 15 min
• Typ: Telefon

✅ Zapisać
➕ Dopisać
❌ Anulować
```

Po `✅ Zapisać`:
- Calendar: event `Telefon — Marek Testowy`.
- Sheets: K/L/P update jeśli klient istnieje.

### S-5. Pole telefonu nie jest spotkaniem

User:

```text
Dodaj klienta Jan Telefoniczny, telefon 600100200, jutro podeślę dane.
```

Agent:
- nie tworzy Calendar eventu,
- nie pokazuje karty spotkania,
- traktuje jako `ADD_CLIENT` albo prosi o brakujące dane klienta.

### S-6. `/cancel`

User ma otwartą kartę.

User:

```text
/cancel
```

Agent:

```text
❌ Anulowane.
```

Zapisy:
- Sheets: brak nowych zmian.
- Calendar: brak nowych zmian.
- Supabase: pending usunięty.

## 16. Punkty Do Review Maana

Te elementy wymagają świadomej decyzji, bo obecny kod i wcześniejsze docs nie zawsze mówią to samo.

1. **Czy `add_client` bez terminu ma tworzyć Calendar event?**
   - Aktualny kod: nie.
   - Stare docs: sugerowały dual-write.
   - Rekomendacja: nie tworzyć eventu; R7 pyta o następny krok.

2. **Czy czyste `add_note` ma odpalać R7?**
   - Aktualny kod: nie.
   - Stare behavior spec: sugerowało, że tak.
   - Rekomendacja: nie dla czystej notatki; tak dla notatki z przyszłą akcją.

3. **Czy `change_status` ma tworzyć Calendar event statusowy?**
   - Aktualny kod: nie.
   - Rekomendacja: nie; status to stan w Sheets, a przyszła akcja idzie przez R7.

4. **Jak traktować notatkę z datą, np. "zadzwonić w piątek"?**
   - Aktualny kod: nie w pełni gwarantuje Calendar.
   - Rekomendacja: compound note + phone_call.

5. **Czy testowy bot ma dostać osobne Google Sheets / Calendar / Supabase?**
   - Aktualnie: osobny Telegram, backend potencjalnie wspólny.
   - Rekomendacja: rozdzielić przed większymi testami.

6. **Czy po spotkaniu z nowym klientem drugi krok ma pytać o klienta, czy automatycznie zapisywać klienta?**
   - Aktualny kod: pyta kartą `ADD_CLIENT`.
   - Rekomendacja: zostawić pytanie, bo zapis klienta to osobna mutacja.

## 17. Definicja „Idealnie Działa”

Agent jest gotowy, gdy:

1. Każdy flow ma opis: input → decyzja → karta → zapis → kolejny stan.
2. Każdy zapis jest jawnie potwierdzony.
3. Każdy Calendar write i Sheets write ma test.
4. Każdy błąd produkcyjny ma test regresyjny.
5. Testowy bot przechodzi smoke pack bez ręcznego ratowania flow.
6. Logi pozwalają diagnozować decyzje bez PII.
7. Użytkownik nigdy nie musi zgadywać, co bot zapisał.
8. Bot nigdy nie pyta o dane, które już dostał.
9. Bot nigdy nie gubi telefonu, miasta, adresu i produktu z wiadomości spotkania.
10. Web app wraca jako priorytet dopiero po stabilizacji tych flow.

