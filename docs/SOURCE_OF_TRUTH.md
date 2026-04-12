# OZE-Agent — Source of Truth

_Last updated: 11.04.2026 popołudnie_
_Owner: Maan_

Ten plik to **mapa całej dokumentacji OZE-Agent**. Jeśli nie wiesz gdzie szukać odpowiedzi — zaczynasz tutaj. Jeśli dwa dokumenty mówią co innego — wygrywa ten oznaczony jako **SSOT** (Single Source of Truth) w tym pliku.

---

## 1. Jeśli wchodzisz tu pierwszy raz

### Jeśli jesteś Claude Code (implementacja / fix kodu)

Czytaj w tej kolejności, **w całości**, przed dotknięciem kodu:

1. `docs/CURRENT_STATUS.md` — co jest zrobione, co się psuje, co jest zadaniem na TĘ sesję
2. `docs/agent_behavior_spec_v5.md` — co agent ma robić, 52 testy akceptacyjne, reguły R1-R6
3. `docs/agent_system_prompt.md` — ton agenta, zakazane frazy, wzorce odpowiedzi
4. `docs/implementation_guide_2.md` — fazowy plan budowy + lessons learned
5. Ten plik (`SOURCE_OF_TRUTH.md`) — jeśli którykolwiek z powyższych jest niejasny

Nie zgaduj, nie wymyślaj, nie skracaj czytania. Jeśli konflikt — pytaj Maana zanim coś zmienisz.

### Jeśli jesteś Claude Cowork (testowanie manualne)

1. `docs/CURRENT_STATUS.md` — aktualny stan + lista znanych bugów
2. `docs/agent_behavior_spec_v5.md` — 52 testy akceptacyjne (sekcja 10)
3. `docs/protokol_testowania_v1.md` — jak raportować wyniki

### Jeśli jesteś Maan (decyzje produktowe / priorytety)

1. Ten plik — mapa decyzji i aktualny stan
2. `docs/CURRENT_STATUS.md` — co testerzy raportują
3. `docs/poznaj_swojego_agenta_v5_FINAL.md` — jak wygląda produkt z perspektywy użytkownika końcowego

---

## 2. Dokumenty żyjące (aktywne, czytane, edytowane)

| Plik | Co to jest | Kto czyta | SSOT dla czego |
|---|---|---|---|
| `SOURCE_OF_TRUTH.md` | **Ten plik.** Mapa, decyzje produktowe, priorytet między dokumentami | Wszyscy | Hierarchia dokumentów + decision log |
| `INTENCJE_MVP.md` | Kontrakty intencji MVP: co agent ma robić per intencja, schemat Sheets, karty potwierdzenia, plan Faza A/B/C | Claude Code (must-read przed dotknięciem logiki intencji), Maan | **Kontrakty intencji MVP + zamrożony schemat Sheets** |
| `CURRENT_STATUS.md` | Aktualny stan faz, naprawione bugi, zadanie na następną sesję | Claude Code, Cowork, Maan | **Aktualny stan implementacji** |
| `agent_behavior_spec_v5.md` | Zachowanie agenta: reguły R1-R6, slang, klasyfikacja intencji, 52 testy | Claude Code (must-read) | **Zachowanie agenta**, **testy akceptacyjne** |
| `agent_system_prompt.md` | System prompt LLM: ton, zakazane frazy, wzorce odpowiedzi | Claude Code przy edycji promptów | **Ton agenta + wzorce konkretnych odpowiedzi** |
| `implementation_guide_2.md` | Fazy 1-7, mikro-kroki, regression tests, lessons learned | Claude Code | **Plan budowy + lessons learned** |
| `poznaj_swojego_agenta_v5_FINAL.md` | Opis produktu z perspektywy handlowca (jak by go czytał użytkownik końcowy) | Maan, onboarding, marketing | **Opis produktu user-facing** |
| `protokol_testowania_v1.md` | Jak raportować testy — format, priorytet bugów | Claude Cowork | **Format raportów testowych** |
| `CLAUDE_CODE_TASK.md` | Zadanie dla konkretnej sesji Claude Code (tymczasowy, regenerowany) | Claude Code | Jednorazowy brief sesji (nie kanoniczny) |

### Raporty testowe (artefakty, nie-SSOT)

| Plik | Co to |
|---|---|
| `TEST_REPORT_10-04-2026.md` | Raport Round 7 — testy po fix B14, Bug #1, Bug #3 |
| `ROUND_8_AB_C_TESTS.md` | Raport Round 8 — testy opcji A/B/C po bugfixach Bug #1, add_note |

Raporty testowe są **artefaktami historycznymi**. Żyją w `docs/`, ale nie są SSOT dla niczego — kanoniczny stan bugów żyje w `CURRENT_STATUS.md`.

---

## 3. Archive (dokumenty zamrożone — NIE CZYTAJ jako źródła prawdy)

| Plik | Dlaczego w archive | Co go zastąpiło |
|---|---|---|
| `archive/OZE_Agent_Brief_v5_FINAL.md` | Oryginalny techniczny brief. Teoretycznie "source of truth for all decisions", ale: (1) zbyt gruby by czytać co sesja, (2) niektóre decyzje zostały zmienione po 4 rundach testów (specs techniczne, R4, schema Sheets). | `agent_behavior_spec_v5.md` + `agent_system_prompt.md` + ten plik |

**Reguła:** jeśli potrzebujesz informacji z briefu, sprawdź najpierw czy żyjąca wersja w nowych dokumentach tego nie pokrywa. Jeśli naprawdę musisz sięgnąć do archive — wiedz, że czytasz historyczny artefakt, nie wytyczne.

---

## 4. Decision log — kluczowe decyzje produktowe

### 11.04.2026 popołudnie — Intencje wycięte na stałe (nie POST-MVP, tylko NIEPLANOWANE)

Przy synchronizacji `agent_system_prompt.md` Maan zdecydował:

1. **`free_slots` — USUNIĘTE na stałe.**
   Intencja "wolne okna w czwartek" została wcześniej oznaczona jako POST-MVP. Po namyśle: **nigdy nie będzie takiej funkcji**. Handlowiec patrzy na `show_day_plan` i sam widzi gdzie ma luki — osobna intencja liczenia wolnych slotów to overhead bez wartości. Sekcja wzorca odpowiedzi w `agent_system_prompt.md` skasowana, testy 28/29 w `agent_behavior_spec_v5.md` będą przeklasyfikowane z POST-MVP na "NIEPLANOWANE", pozycja wyrzucona z `INTENCJE_MVP.md` sekcja 8.

2. **`reschedule_meeting` — USUNIĘTE na stałe.**
   Intencja "przełóż Jana na piątek o 10" podobnie: **nigdy nie będzie**. Realny flow: handlowiec kasuje stare spotkanie w Kalendarzu ręcznie i tworzy nowe komendą `add_meeting`. Jedno spójne flow zamiast dwóch. Sekcja wzorca skasowana.

3. **`cancel_meeting` / "Odwołaj Jana" — USUNIĘTE z promptu.**
   Spójnie z (2) — cancel przez Kalendarz ręcznie lub przez osobne usunięcie wiersza w Sheets. Agent nie bierze odpowiedzialności za irreversible delete na podstawie interpretacji wiadomości.

4. **`Meeting on non-working day` warning — USUNIĘTE.**
   Handlowcy OZE pracują w soboty, niedziele, w święta. Ostrzeganie "to nie jest dzień roboczy" było założeniem z innego segmentu. Żadnego warningu — `add_meeting` w sobotę działa tak samo jak w poniedziałek.

5. **`lejek_sprzedazowy` — POST-MVP z banerem + bez Negocjacji.**
   Zostaje jako POST-MVP, ale wzorzec odpowiedzi został przepisany: handlowiec pyta "ilu mam klientów?", agent odpowiada pytaniem o które etapy, w nawiasie po przecinku wymienia **9 statusów** (Negocjacje **wycięte**). Handlowiec może podać kilka etapów naraz. Linia `Lejek:` w morning briefingu **usunięta** (briefing nie ma pokazywać danych z intencji, której jeszcze nie ma).

6. **Disambiguation duplikatu — dwuprzyciskowa karta.**
   Gdy agent wykryje match = 1 przy `add_client`, pokazuje kartę z dwoma przyciskami: `[📋 Dopisz do istniejącego] [➕ Utwórz nowy wpis]`. Default (auto-merge przy kolejnej wiadomości pasującej do auto-fill) to `Dopisz do istniejącego`. Stary wzorzec `[Nowy][Aktualizuj]` zastąpiony — nowa para przycisków ma wizualnie jasne "wchodzisz w istniejącego klienta" vs "robisz osobny wpis".

7. **`add_meeting` wzorzec wspólny dla spotkania / telefonu / follow-up dokumentowego.**
   Trzy intencje z poprzedniej dokumentacji (meeting, call reminder, document follow-up) były osobnymi wzorcami. Są jedną intencją `add_meeting` z różnymi emoji: `📅` = spotkanie, `📞` = telefon, `📨` = follow-up dokumentowy. Agent wybiera emoji na podstawie słów kluczowych. Jeden wzorzec w promptach, jeden parser, jeden commit path.

### 11.04.2026 popołudnie — Bloki I, J, K (doprecyzowanie zachowania agenta w `agent_behavior_spec_v5.md`)

Po pierwszej rundzie synchronizacji `agent_behavior_spec_v5.md` do kontraktów z 11.04, trzy decyzje produktowe zostały świadomie zostawione jako TODO, bo wymagały osobnego namysłu. Dzisiaj popołudniu Maan je zatwierdził:

1. **Blok I — One-click cancel.**
   Przycisk `❌ Anulować` na każdej karcie mutacyjnej jest **jednoklikiem**. Agent natychmiast zamyka pending i odpowiada `🫡 Anulowane.` (1 linia). Nie ma żadnej pętli `Na pewno anulować? [Tak][Nie]`. Stary wzorzec dwukliku z v5 (testy 30, 31, 34, 36) **przestaje istnieć**.
   **Uzasadnienie:** handlowiec w aucie nie chce dwóch kliknięć dla porzucenia pending — jeden klik czerwonego krzyżyka, pending znika, koniec. Ryzyko przypadkowego anulowania jest niskie, bo `❌` jest osobnym przyciskiem obok `✅` i `➕`, nie myli się łatwo.

2. **Blok J — Auto-doklejanie + compound fusion.**
   R3 rozbita na **cztery drogi obsługi pending**: (1) auto-cancel (domyślnie, dla wiadomości niepasujących), (2) jawny `➕ Dopisać` (awaryjne wyjście), (3) **NOWE — auto-doklejanie** gdy wiadomość wyraźnie pasuje do `Brakuje:` pending bez sygnałów innego intencji, (4) **NOWE — compound fusion** gdy wiadomość pasuje do innej mutacji tego samego klienta (np. pending `change_status` + nowa wiadomość z `add_meeting`).

   **Scenariusz 1/2 reakcja (b):** auto-doklejanie jednopolowych uzupełnień. Przykład: pending `add_client` z `Brakuje: telefon, email`; handlowiec pisze `602 345 678` → agent automatycznie dokleja telefon do karty, bez klikania `➕ Dopisać`.

   **Scenariusz 3:** compound fusion. Przykład: pending `change_status: Oferta wysłana` dla Jana Kowalskiego; handlowiec pisze `i jutro o 10 spotkanie` → agent buduje jedną kartę zbiorczą "Status + Spotkanie" z jednym `✅ Zapisać oba`. Commit atomowy (Sheets → Calendar), R7 `next_action_prompt` pominięty bo z meeting wynika wprost następny krok.

   **Ograniczenia:** auto-doklejanie działa tylko dla pól strukturalnych (telefon, email, adres, źródło leada), nie dla notatek technicznych/emocji — te zawsze przez `➕ Dopisać`. Compound fusion wymaga żeby klient był ten sam i żeby kombinacja była na białej liście (status+meeting, note+meeting, client+meeting). Dwa statusy pod rząd, note+status sklejone — idą przez Drogę 1 (auto-cancel), bo ryzyko dwuznaczności > zysk.

   **Uzasadnienie:** (a) ścisła reguła "tylko przez przycisk" z poprzedniej wersji generowała niepotrzebne klikanie w przypadkach oczywistych, (b) compound fusion odzwierciedla realny flow handlowca — po wpisaniu "wysłałem ofertę" naturalnie chce dodać "i jutro o 10 spotkanie", jednym commitem zamiast dwoma flow.

3. **Blok K — Limit długości odpowiedzi zniesiony.**
   Pierwotne limity z v5 (karta klienta 4-8 linii, plan dnia 5-15 linii, briefing 10-20 linii) **usunięte**. Karta, plan i briefing mogą rosnąć wraz z zawartością — handlowiec z 8 spotkaniami widzi 25-linowy plan dnia i to jest OK. Zostają **twarde reguły** tylko dla `✅ Zapisane.` (1 linia) i błędu (1-2 linie).

   **Uzasadnienie:** oryginalne limity z v5 powstały, bo agent był wtedy zbyt lakoniczny i gubił konkret — ograniczenie miało go zmusić do zwięzłości. Po ośmiu rundach testów agent już rozumie że minimalizm = wartość, i nie wymaga sztywnego limitu. Limit ograniczał jakość kart z bogatymi notatkami i planów dni z wieloma spotkaniami. Zamiast limitu — zasada: "tak długie jak musi być, ale bez watyfraz, komentarzy meta i zakończeń".

   **Co nadal jest zakazane:** `"Oto twoja karta"`, `"Przygotowałem plan"`, `"Powodzenia!"`, `"Daj znać jak coś"`, puste linie "dla oddechu", podsumowania ("W sumie masz 3 spotkania").

### 11.04.2026 — Po Sesji 1 Regresja + zamrożenie kontraktów intencji MVP

Po Sesji 1 "Regresja 10.04" i długiej burzy mózgów o rozjazdach między dokumentacją, kodem i realnym arkuszem Maana, podjęto następujące decyzje produktowe. Większość z nich zamraża kontrakty dla intencji MVP i jest wprost spisana w `INTENCJE_MVP.md`. Tu żyje krótki log **dlaczego**.

1. **"Dodatkowe info" → "Notatki".**
   W dokumentacji kolumna była wcześniej nazywana "Dodatkowe info". W realnym arkuszu Maana jest i zawsze była "Notatki". Dokumentacja nadrabia terminologię pod rzeczywistość — **nie odwrotnie**. Wszystkie referencje do "Dodatkowe info" w żyjących dokumentach mają być zamienione na "Notatki".

2. **Schemat Sheets zamrożony: 16 kolumn.**
   Porządek i nazwy kolumn w arkuszu "OZE Klienci" są oficjalnie zamrożone na poziomie dokumentacji:
   `A=Imię i nazwisko`, `B=Telefon`, `C=Email`, `D=Miasto`, `E=Adres`, `F=Status`, `G=Produkt`, `H=Notatki`, `I=Data pierwszego kontaktu`, `J=Data ostatniego kontaktu`, `K=Następny krok`, `L=Data następnego kroku`, `M=Źródło pozyskania`, `N=Zdjęcia`, `O=Link do zdjęć`, `P=ID wydarzenia Kalendarz`.
   Kolumna `L=Data następnego kroku` została **dodana** między `K` a starą `L` — żeby "następny krok" miał konkretny termin, a nie tylko opis. Kod jest schema-agnostic (czyta nagłówki z wiersza 1 funkcją `get_sheet_headers()` i cachuje w `users.sheet_columns`), więc dokumentacja kolumn nie wymusza dotykania `DEFAULT_COLUMNS` w kodzie — wymusza tylko spójność opisów i przykładów w plikach `.md`.

3. **R4 PRZYWRÓCONA jako `next_action_prompt`.**
   Decyzja z 10.04 wieczór (punkt 3 niżej) mówiła "R4 usunięta, agent nigdy sam nie pyta o następny kontakt". Po Sesji 1 Regresja Maan to **odwraca**: po każdej mutacji (add_client, add_note, change_status, add_meeting), jeśli nie wiadomo jeszcze, co będzie następnym krokiem, agent ma zadać **jedno, wolnotekstowe pytanie** typu "Co dalej z tym klientem? Spotkanie, telefon, odłożyć na później?" i pozwolić handlowcowi odpowiedzieć prozą. To nie jest sztywna trójka "meeting / call / not interested" — to otwarte pytanie z możliwością wciśnięcia **❌ Anulować**.

   **Uzasadnienie odwrócenia:** (a) bez tego pytania lejek martwieje — klienci siedzą ze statusem "Nawiązano kontakt" tygodniami bez jasnego następnego kroku, (b) wolnotekstowa wersja nie blokuje flow tak jak sztywna trójka, (c) handlowiec może odpowiedzieć "nie wiem jeszcze" i zamknąć flow bez wpisu.

4. **Karty mutacyjne: 3 przyciski zamiast [Tak]/[Zapisz bez].**
   Wszystkie karty potwierdzenia (add_client, add_note, change_status, add_meeting, show_day_plan mutacje) mają trzy przyciski:
   - **✅ Zapisać** (zielony) — commit do Sheets/Calendar
   - **➕ Dopisać** (żółty) — zostaw kartę pending otwartą, handlowiec dopisze więcej info, karta przebudowuje się
   - **❌ Anulować** (czerwony) — porzuć flow

   Karty read-only (show_client, show_day_plan bez mutacji) **nie mają** tych przycisków. `[Tak]` i `[Zapisz bez]` jako wzorzec przestają istnieć.

5. **"Negocjacje" — USUNIĘTE z lejka.**
   Status "Negocjacje" był teoretyczny i nigdy realnie nie używany przez Maana w testach. Lejek ma 9 statusów (bez Negocjacji). Wszystkie wystąpienia "Negocjacje" w dokumentacji intencji, promptów i przykładów mają być usunięte.

6. **"Klimatyzacja" — USUNIĘTA z produktów.**
   Produkty: `PV`, `Pompa ciepła`, `Magazyn energii`, `PV + Magazyn`. Bez klimatyzacji — OZE-Agent nie obsługuje tego segmentu.

7. **Dropdowny w Sheets: Status (9 opcji) + Następny krok (7 opcji).**
   Kolumna `F=Status` ma data validation z 9 opcjami (lejek sprzedażowy). Kolumna `K=Następny krok` ma data validation z 7 opcjami. Dropdowny są zakładane przy pierwszym setupie arkusza, a kod mutacji respektuje listę opcji (nie wpisuje wartości spoza listy).

8. **Ochrona nagłówka arkusza: A1:P1 protected.**
   Pierwszy wiersz (nagłówki kolumn) ma być zabezpieczony przed zmianą przez handlowca lub przez agenta. Kod `get_sheet_headers()` czyta to aktywnie — jeśli ktoś zmieni nagłówek, mapowanie kolumn się rozsypie. Ochrona A1:P1 (Sheets "Protected range") jest częścią kontraktu setup arkusza.

9. **Context-aware client resolution (step A.8).**
   Nowa funkcjonalność: `resolve_active_client(user_id, history_window=10)` + `user_data["active_client"]`. Gdy handlowiec mówi "dodaj że ma duży dom" bez wskazania klienta, agent bierze ostatnio aktywnego klienta z kontekstu (ostatnie 10 wiadomości). Infrastruktura (`get_conversation_history`) już istnieje w `shared/database.py`, mechanizm aktywnego klienta — **nie istnieje jeszcze w kodzie**. To jest nowy krok A.8 w Fazie A planu implementacji.

10. **Detekcja istniejącego klienta w każdej mutacji.**
    Przed każdym `add_client` / `add_note` / `change_status` / `add_meeting` agent sprawdza, czy klient już istnieje w arkuszu (po imieniu + nazwisku + mieście). Jeśli tak — mutacja idzie na istniejący wiersz, nie tworzy duplikatu. Jeśli agent nie jest pewny (np. dwóch "Kowalski" w tym samym mieście) — pyta o disambiguację zanim dotknie Sheets.

### 10.04.2026 (wieczór) — Sprzątanie po 4 rundach testów

Po Round 7 + Round 8 testów manualnych w Telegramie, Maan podjął następujące decyzje produktowe:

1. **Specyfikacje techniczne → Notatki (nie dedykowane kolumny).**
   Metraż domu, metraż dachu, kierunek dachu, zużycie prądu, napięcie sieci, typ dachu, cokolwiek liczbowo-technicznego — wszystko ląduje w kolumnie `Notatki` w Google Sheets. **Nie tworzymy** dedykowanych kolumn `moc_kw`, `metraz_domu`, `metraz_dachu` itp.

   **Uzasadnienie:** (a) każdy handlowiec ma trochę inne potrzeby co do pól, (b) parsowanie LLM do wielu pól jest zawodne (Bug #2 wielokrotnie), (c) Notatki są wyszukiwalne i wystarczająco dobre dla MVP.

2. **Moc produktu — do Notatek razem z resztą specs.** ~~(wcześniej: doklejona do nazwy produktu)~~
   Moc (6kW / 8kW / 12kW / 10kWh) trafia do kolumny `Notatki`, tak samo jak metraż, kierunek dachu i reszta specs. Kolumna `Produkt` zawiera tylko typ produktu (`PV`, `Pompa ciepła`, `Magazyn energii`, `PV + Magazyn`), bez wartości liczbowych. **Nie ma dedykowanej kolumny `moc_kw`.**

   **Zmiana z 11.04.2026:** Pierwotna decyzja z 10.04 wieczór była "moc doklejona do produktu" (np. `PV 8kW`). Po Sesji 1 "Regresja 10.04" (Bug #14 — parser wyciągał moc ale nie umiał jej skleić z nazwą) i po dyskusji produktowej: doklejanie robi niepotrzebne zamieszanie na MVP. Moc idzie do Notatek, spójnie z decyzją 1. Sprzedawca widzi moc w Notatkach, nie w nazwie produktu.

3. **R4 (obowiązkowe pytanie o następny kontakt) — USUNIĘTA.**
   Wcześniejsza wersja reguły R4 wymagała, że każdy `add_client` flow musi zakończyć się pytaniem "Kiedy następny kontakt?" (meeting / call / not interested). To zostało **usunięte**. Agent nigdy sam z siebie nie pyta o "kiedy następny kontakt".

   **Uzasadnienie:** (a) handlowiec często nie wie jeszcze kiedy, (b) pytanie blokowało flow i irytowało, (c) follow-up można ustawić później osobną komendą.

   R4 w nowej wersji `agent_behavior_spec_v5.md` oznacza teraz **Identyfikację klienta** (imię + nazwisko + miejscowość), nie pytanie o follow-up.

   > **UPDATE 11.04.2026:** Ta decyzja została **odwrócona** w nowym decision logu (sekcja 4, 11.04.2026, punkt 3). Pytanie o następny krok wraca — ale w nowej formie: jedno wolnotekstowe pytanie `next_action_prompt` zamiast sztywnej trójki meeting/call/not interested. Agent pyta "Co dalej z tym klientem?" i przyjmuje dowolną odpowiedź lub Anuluj. Ten akapit zostaje w logu jako historia decyzji, ale kanoniczny stan to punkt 3 z 11.04.

4. **Brief v5 → archive.**
   `OZE_Agent_Brief_v5_FINAL.md` przeniesiony do `docs/archive/` z nagłówkiem ostrzegawczym. Nie jest już "source of truth for all decisions" — żyjące dokumenty (behavior_spec + system_prompt + ten plik) mają pierwszeństwo.

### Wcześniejsze decyzje (przed 10.04 wieczór)

- **Identyfikacja klienta = imię + nazwisko + miasto.** Nigdy samo nazwisko. W Polsce jest za dużo "Kowalskich".
- **Data format = `DD.MM.YYYY (Dzień tygodnia)`.** Nigdy ISO, nigdy sam numer, nigdy Excel serial.
- **Polish language.** Wszystkie komunikaty user-facing po polsku. Kod i komentarze po angielsku.
- **CRM data → Google (Sheets/Calendar/Drive). System data → Supabase. Nigdy nie mieszamy.**
- **R1 jest absolutna.** Agent NIGDY nie pisze do Sheets/Calendar/Drive bez potwierdzenia użytkownika.
- **State-lock fix:** podczas pending flow (nie-add_client), nowa wiadomość = auto-cancel + przetwórz normalnie.

---

## 5. "Szukam X — gdzie iść?"

| Szukasz... | Idź do |
|---|---|
| Co agent ma robić w sytuacji Y | `agent_behavior_spec_v5.md` sekcja 7 (scenariusze) lub sekcja 10 (testy akceptacyjne) |
| Dokładne brzmienie odpowiedzi bota | `agent_system_prompt.md` sekcja "Response patterns" |
| Lista zakazanych fraz | `agent_system_prompt.md` sekcja "Banned phrases" |
| Jak parsować polski slang OZE | `agent_behavior_spec_v5.md` sekcja 4 (słownik slangu) |
| Jak parsować polski czas | `agent_behavior_spec_v5.md` sekcja 5 |
| Aktualny stan fazy X | `CURRENT_STATUS.md` |
| Co się zepsuło ostatnio | `CURRENT_STATUS.md` sekcja "Zadanie na następną sesję" |
| Plan kolejnych kroków implementacji | `implementation_guide_2.md` |
| Lessons learned z poprzednich sesji | `implementation_guide_2.md` sekcja "Lessons learned" |
| Jak opisać produkt użytkownikowi | `poznaj_swojego_agenta_v5_FINAL.md` |
| Jakie są aktualne statusy lejka | `INTENCJE_MVP.md` — sekcja dropdown Status (9 opcji, lejek sprzedażowy po 11.04) |
| Raport z ostatnich testów | `TEST_REPORT_10-04-2026.md` + `ROUND_8_AB_C_TESTS.md` |
| Decyzje produktowe i dlaczego | Ten plik — sekcja 4 (Decision log) |
| Techniczny brief oryginalny (historyczny) | `archive/OZE_Agent_Brief_v5_FINAL.md` — **tylko historycznie** |

---

## 6. Hierarchia w razie konfliktu

Jeśli dwa dokumenty mówią co innego, wygrywa **wyższy** w tej liście:

1. **Ten plik (`SOURCE_OF_TRUTH.md`)** — decision log w sekcji 4 jest zawsze kanoniczny
2. **`INTENCJE_MVP.md`** — kontrakty intencji MVP, zamrożony schemat Sheets, karty potwierdzenia (najbardziej aktualny dokument po Sesji 1 Regresja)
3. **`agent_behavior_spec_v5.md`** — zachowanie agenta i testy akceptacyjne
4. **`agent_system_prompt.md`** — konkretne wzorce odpowiedzi i ton
5. **`CURRENT_STATUS.md`** — aktualny stan implementacji (nie stan docelowy — stan TERAZ)
6. **`implementation_guide_2.md`** — plan budowy
7. **`poznaj_swojego_agenta_v5_FINAL.md`** — opis user-facing (może wyprzedzać implementację)
8. **`archive/OZE_Agent_Brief_v5_FINAL.md`** — historyczny, najniższy priorytet

**Przykład 1:** Jeśli `archive/OZE_Agent_Brief_v5_FINAL.md` mówi "R4: po add_client zawsze pytaj o następny kontakt", a `agent_behavior_spec_v5.md` mówi "R4: identyfikacja klienta po imieniu i nazwisku + miasto" — wygrywa spec_v5 (bo jest wyżej w hierarchii i nowszy).

**Przykład 2:** Jeśli `agent_behavior_spec_v5.md` albo `agent_system_prompt.md` opisują "Negocjacje" jako jeden ze statusów lejka, a `INTENCJE_MVP.md` mówi "Negocjacje usunięte z lejka" — wygrywa `INTENCJE_MVP.md`, bo zamrożone kontrakty intencji z 11.04 mają pierwszeństwo przed starszymi opisami zachowania.

---

## 7. Znane rozbieżności w dokumentacji (do posprzątania)

Te rzeczy wiemy, że są niespójne — żyją tutaj jako jawny TODO:

- ~~**`agent_behavior_spec_v5.md`** — nie wie jeszcze o decyzjach z 11.04.~~ ✅ **W pełni zsynchronizowane 11.04.2026 popołudnie** — nagłówek, R1 (3-button, one-click cancel), R3 (cztery drogi pending: auto-cancel / `➕ Dopisać` / auto-doklejanie / compound fusion), R4 (detekcja istniejącego klienta + konflikt kalendarza), R5 (edit_client POST-MVP), R6 (active_client), R7 (next_action_prompt), sekcja 3 (limit linii zniesiony), sekcja 6 (6 MVP + POST-MVP, `show_client` zamiast `search_client`), sekcja 7 (przykładowa karta z 3 przyciskami, rezygnacja z umowy vs odrzucone), słownik slangu, testy 1-52, metryki. **Bloki I/J/K zatwierdzone i wdrożone** (decision log sekcja 4, 11.04 popołudnie): Blok I = one-click cancel, Blok J = auto-doklejanie jednopolowe + compound fusion status/client/note + meeting, Blok K = brak limitu linii. Nie ma otwartych TODO w tym pliku.
- ~~**`agent_system_prompt.md`** — wzorce odpowiedzi i banned phrases nie wiedzą o nowych kartach 3-przyciskowych.~~ ✅ **W pełni zsynchronizowane 11.04.2026 popołudnie** — nagłówek z changelogiem, sekcja Formatting z 3-button + read-only, sekcja Response length (Blok K, limit zniesiony), R1-R8 (3-button, one-click cancel, cztery drogi pending, duplikat = merge domyślnie, edit_client POST-MVP, 10/30 + active_client, `next_action_prompt`, frustration=calm), słownik OZE slang (Klimatyzacja wycięta, Rezygnacja z umowy vs Odrzucone rozróżnione, moc bez prefiksu), wszystkie wzorce odpowiedzi (`add_client`, `show_client`, status change, `add_meeting` — MERGE z follow-up/reminder w jeden wzorzec z emoji 📅/📞/📨, `show_day_plan`, photos, duplikat jako 2-button disambiguation card, calendar conflict, `lejek_sprzedazowy` z banerem POST-MVP bez Negocjacji), morning brief bez linii "Lejek:", voice processing flow z `[Tak][Nie]` na niskim confidence + 3-button dla sparsowanej karty. **Sekcje usunięte**: `Calendar — free slots`, `Calendar — rescheduling`, `Calendar — cancelling`, `Meeting on non-working day` — nie są w MVP ani POST-MVP.
- **`poznaj_swojego_agenta_v5_FINAL.md`** — opis user-facing nie został jeszcze zaktualizowany po 11.04: może wciąż pokazywać stare karty, stare statusy, stare pytania. Do synchronizacji przed następną iteracją marketingową.
- **`implementation_guide_2.md`** — plan Faz 1-7 nie ma jeszcze kroku A.8 (context-aware client resolution) ani kroków implementujących dropdowny/ochronę nagłówka/detekcję istniejącego klienta z 11.04. Do rozpisania przy najbliższym planowaniu Fazy A.
- **`CLAUDE.md` w korzeniu projektu** referuje `docs/implementation_guide.md`, `docs/OZE_Agent_Brief_v5_FINAL.md` (teraz w archive), oraz starą definicję Non-Negotiable Rule #9 ("Every add_client flow ends with a question about next contact") — wszystko już nieaktualne. Do poprawy przy następnej edycji CLAUDE.md. Wymaga uwagi bo to pierwszy plik jaki czyta Claude Code w każdej sesji.
- **`docs/CLAUDE_CODE_TASK.md`** — tymczasowy brief z poprzedniej sesji, referuje stare Bug #2 (specy w dedykowanych polach). Nie-kanoniczny artefakt — regeneruje się przy każdej sesji Claude Code, więc stara kopia zostaje jak jest.
- **`docs/TEST_REPORT_10-04-2026.md`** — historyczny raport Round 7, opisuje Bug #2 (dedykowane pola) jako otwarty. To jest historycznie poprawne (raport dokumentuje stan W TAMTYM momencie), więc nie edytujemy.

**Posprzątane 10.04 wieczór (już nie problem):**
- ~~`agent_system_prompt.md` — wzorce odpowiedzi ze specyfikacjami jako osobne pola~~ ✅ Zmiana 2
- ~~`poznaj_swojego_agenta_v5_FINAL.md` — dziura "Produkt, , Status", brak email, lista kolumn~~ ✅ Zmiana 3
- ~~`CURRENT_STATUS.md` — stare Bug #1 i Bug #2 jako zadanie na następną sesję (już naprawione w bc765a2)~~ ✅ Zmiana 4
- ~~`archive/OZE_Agent_Brief_v5_FINAL.md` bez ostrzegawczego nagłówka~~ ✅

---

## 8. Jak aktualizować ten plik

- **Nowa decyzja produktowa?** → dopisz do sekcji 4 (Decision log) z datą i uzasadnieniem.
- **Nowy dokument w `docs/`?** → dopisz do sekcji 2 lub 3 z opisem "co to jest" i "SSOT dla czego".
- **Zmiana hierarchii SSOT?** → edytuj sekcję 6 i wyjaśnij dlaczego w sekcji 4.
- **Archiwizacja dokumentu?** → przenieś do `docs/archive/`, zaktualizuj sekcje 2 i 3, dodaj powód do sekcji 4.

**Commit message format:** `docs: update SOURCE_OF_TRUTH — <krótki opis>`
