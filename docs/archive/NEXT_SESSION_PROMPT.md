# Prompt dla następnej sesji Claude Code — wykonanie fixów z audytu 11.04.2026

> Ten plik jest briefingiem dla następnej sesji Claude Code. Maan wkleja go w całości na start świeżej sesji. Nic tu nie jest opcjonalne — wszystkie sekcje są obowiązkowe.

---

## 0. Kim jesteś i czego się od ciebie oczekuje

Jesteś Claude Code pracującym nad projektem **OZE-Agent** — polskim botem Telegram do B2C sprzedaży OZE. Twoje zadanie w tej i kolejnych sesjach to **naprawienie driftu między kodem a SSOT**, zgodnie z audytem `docs/CODE_AUDIT_11-04-2026.md`.

**Twoja dyscyplina pracy jest święta i niepodważalna:**

1. Robisz **JEDNĄ rzecz naraz**. Nie dwie. Nie „przy okazji”. Nie „szybki drobiazg”. Jedną.
2. Po każdej jednej rzeczy **zatrzymujesz się** i raportujesz do Maana w formacie zdefiniowanym w sekcji 4 tego pliku.
3. Czekasz na zielone światło od Maana. Bez jego „ok, dalej” nie ruszasz następnego kroku.
4. Po każdym zielonym świetle commitujesz zmianę (`Phase X.Y: [opis]` dla kodu, `docs: [opis]` dla dokumentów). Commit = zakończony krok.
5. Testy **odkładamy na koniec**. Najpierw wszystkie must-priority fixy w kodzie, dopiero potem jedna dedykowana sesja testowa według `docs/TEST_PLAN_11-04-2026.md`. Nie testujemy po każdym kroku w Telegramie — testujemy statycznie (czytamy kod, weryfikujemy przeciwko SSOT, pokazujemy diff Maanowi).
6. **Nie zgadujesz.** Jak czegoś nie wiesz — pytasz. Jak SSOT jest niejednoznaczny — pytasz. Jak audyt mówi co innego niż implementation_guide_2 — wygrywa SSOT, ale i tak pytasz przed ruszeniem.
7. **Nie wchodzisz w scope creep.** Jeśli podczas kroku widzisz inny bug / inną niezgodność / pomysł — zapisujesz jedną linijką do `docs/backlog.md` i wracasz do bieżącego kroku. Nie naprawiasz „po drodze”.

To jest reguła #11 z `CLAUDE.md`, tylko trochę rozszerzona. Traktuj ją jak kontrakt.

---

## 1. Kontekst, który musisz wczytać ZANIM cokolwiek zrobisz

Kolejność obowiązkowa. Nie przeskakuj. Po każdym pliku zatrzymaj się i zastanów, co przeczytałeś — nie leć dalej mechanicznie.

1. **`CLAUDE.md`** — pełna instrukcja projektu, zasady architektoniczne, reguły R1–R11, stos technologiczny. To twój podstawowy kontrakt.
2. **`docs/SOURCE_OF_TRUTH.md`** — hierarchia SSOT + decision log. Mówi ci, który dokument wygrywa w razie konfliktu.
3. **`docs/CURRENT_STATUS.md`** — stan aktualnej sesji, lista bugów, task na tę sesję. Sprawdzasz tu, czy ten prompt jest dalej aktualny (jeśli CURRENT_STATUS mówi co innego, zatrzymujesz się i pytasz Maana).
4. **`docs/CODE_AUDIT_11-04-2026.md`** — autorytatywny audyt, na którym bazujesz wszystkie fixy. Wszystkie lokalizacje driftu są tu wypisane z numerami linii i kategorią priorytetu (must / should / nice).
5. **`docs/INTENCJE_MVP.md`** — zamrożone kontrakty 6 intencji MVP, 16-kolumnowy schemat Sheets, 9-statusowy pipeline, lista produktów (4, bez Klimatyzacji), lista POST-MVP, lista NIEPLANOWANE. To jest to, do czego równasz kod.
6. **`docs/agent_behavior_spec_v5.md`** — 52 testy akceptacyjne + reguły R1–R8 + scenariusze dla każdej intencji. Czytasz w całości, nie skrótami.
7. **`docs/agent_system_prompt.md`** — ton, wzorce odpowiedzi, banned phrases, OZE slang, voice flow. To jest wzór, jak agent ma mówić.
8. **`docs/TEST_PLAN_11-04-2026.md`** — 15 testów manualnych, które odpalimy po zakończeniu fixów. Teraz tylko przeglądasz, żeby wiedzieć, pod co kodujesz.
9. **`docs/implementation_guide_2.md`** — UWAGA: ma baner „partially stale”. Używasz tylko do kolejności implementacji, nigdy jako źródła prawdy o stanie MVP. SSOT wygrywa zawsze.

Po przeczytaniu tych 9 plików **zatrzymujesz się** i piszesz do Maana jedną wiadomość w stylu:
> „Wczytałem SSOT, audyt i plan. Rozumiem zadanie: [jedno zdanie]. Rozumiem dyscyplinę jedna-rzecz-naraz. Gotowy na Krok 1.1. Ruszamy?”

Nie piszesz nic więcej. Nie rozpisujesz planu. Nie kodujesz. Czekasz na odpowiedź.

---

## 2. Cel wysokopoziomowy

Z audytu wynika, że kod w `bot/`, `shared/` i `supabase_schema.sql` jest w ~0/15 zgodny z obecnym SSOT. Drift jest skoncentrowany w **warstwie UX/behavior**: karty mutacyjne, przyciski, router intencji, prompty do Claude, struktury danych. Backend (Google API, Supabase auth, search_engine) jest zasadniczo zdrowy i go nie ruszamy.

Plan naprawy jest podzielony na **7 sesji (Sesja A–G)**. W każdej sesji jest kilka **kroków**. W każdym kroku jest **jeden** commit. Po każdej sesji Maan weryfikuje, że nic się nie posypało i daje zielone światło na następną.

Kolejność sesji jest ułożona tak, żeby **nic się nie wywaliło po drodze** — najpierw budujemy fundamenty (klawiatury, prompty, dane), potem router, potem pojedyncze handlery, na końcu stanowe rzeczy (R6 active_client).

---

## 3. Plan sesji — 7 sesji, każda sesja = kilka kroków

Po każdym **Kroku** → raport → commit → zielone światło → następny krok.
Po każdej **Sesji** → Maan odpala **smoke test w Telegramie** (2–3 scenariusze najbardziej ryzykowne dla zakresu tej sesji, wybrane przez ciebie) → zielone światło → następna sesja.

### Sesja A — Fundamenty UX (klawiatury + przyciski)

Cel: zamienić stare 2-przyciskowe `[Tak][Nie]` i 1-przyciskowe `[Zapisz bez]` na **R1-zgodne 3-przyciskowe karty** `[✅ Zapisać] [➕ Dopisać] [❌ Anulować]`. Bez tego żaden handler dalej nie ma sensu.

- **Krok A.1** — `bot/utils/telegram_helpers.py`: usunąć `build_confirm_buttons` (stare) i `build_save_buttons` (1-przyciskowe). Dodać `build_mutation_buttons(pending_id)` zwracające dokładnie 3 przyciski R1 z callback_data `save:{id}`, `append:{id}`, `cancel:{id}`. Dodać `build_duplicate_buttons(pending_id)` zwracające 2 przyciski R4: `[📋 Dopisz do istniejącego]` (`merge:{id}`) + `[➕ Utwórz nowy wpis]` (`new:{id}`). Nie dotykać innych funkcji w pliku.
  - **Deliverable**: diff pliku + lista miejsc w kodzie, gdzie stare funkcje były wołane (będziesz to łatał w Sesji C — teraz tylko lista).
  - **Commit**: `Phase A.1: telegram_helpers — R1 3-button + R4 2-button builders`
- **Krok A.2** — `bot/handlers/buttons.py`: przepisać sekcję callback handlerów tak, żeby obsługiwała nowe `save:`, `append:`, `cancel:`, `merge:`, `new:`. Stare `yes/no`, `add_anyway`, `cancel_confirm` (2-step) **usunąć**. `cancel:` ma być **one-click** — natychmiast kasuje pending, odpowiada krótkim „Anulowane.” i kończy. Bez żadnego „Na pewno?”.
  - **Deliverable**: diff + opis flow każdego z 5 przycisków w 1–2 zdaniach.
  - **Commit**: `Phase A.2: buttons.py — R1 save/append/cancel + R4 merge/new handlers`

### Sesja B — Dane i prompty (statyczne fixy, zero logiki)

Cel: wyrównać stałe, prompty i schemat bazy do SSOT. Sama twarda edycja list i stringów — nie dotykamy flow.

- **Krok B.1** — `shared/claude_ai.py`, `VALID_INTENTS`: usunąć `delete_client`, `reschedule_meeting`, `cancel_meeting`, `view_meetings`, `show_pipeline`, `search_client`. Zostawić tylko 6 MVP + 3 POST-MVP (z flagą, że POST-MVP trafiają do R5 banner, nie do pełnych handlerów).
  - **Commit**: `Phase B.1: claude_ai — VALID_INTENTS to 6 MVP + 3 POST-MVP`
- **Krok B.2** — `shared/claude_ai.py`, prompt systemowy: wyciąć „Klimatyzacja” z listy produktów, poprawić `"Podpisał"` → `"Podpisane"`, zamienić etykietę `search_client` → `show_client`, usunąć referencje do retired kolumn (Moc kW, metraże, Dodatkowe info). Zaktualizować few-shot przykłady do 9-statusowego pipeline.
  - **Commit**: `Phase B.2: claude_ai — prompt sync with SSOT products+statuses`
- **Krok B.3** — `shared/google_sheets.py`, `DEFAULT_COLUMNS`: zamienić obecne 21 kolumn na dokładnie 16-kolumnowy schemat A–P z `INTENCJE_MVP.md` sekcja 3. Nazwy 1:1 z SSOT. Dodać brakującą `Data następnego kroku`.
  - **Commit**: `Phase B.3: google_sheets — DEFAULT_COLUMNS to 16-col SSOT schema`
- **Krok B.4** — `supabase_schema.sql`: zamienić default `pipeline_statuses` na 9 statusów (bez Negocjacji). Reszty SQL nie dotykać.
  - **Commit**: `Phase B.4: supabase_schema — 9-status pipeline default`
- **Krok B.5** — `bot/handlers/text.py`, `SYSTEM_FIELDS`: usunąć `Email`, `Notatki`, `Następny krok`, `Dodatkowe info` (to nie są system fields, to business fields). Zostawić tylko prawdziwe system fields według INTENCJE_MVP.
  - **Commit**: `Phase B.5: text.py — SYSTEM_FIELDS cleanup`
- **Krok B.6** — `shared/formatting.py`: usunąć `_MEASUREMENT_FIELDS` (retired), poprawić `_FOLLOWUP_FIELDS` na `Data następnego kroku`, usunąć hardcoded „Kiedy następny kontakt?” z `format_add_client_card` (to pójdzie do R7 post-commit, nie do samej karty).
  - **Commit**: `Phase B.6: formatting — drop retired measurement fields + followup cleanup`

### Sesja C — Router + confirm flow (mózg UX)

Cel: przepisać `bot/handlers/text.py` sekcje router + confirm tak, żeby działały z nową klawiaturą z Sesji A i nowymi intencjami z Sesji B.

- **Krok C.1** — `text.py`, router intencji (`handlers = {...}` ok. linii 206–226): wyrównać mapowanie 1:1 do 6 intencji MVP. `add_note` wskazuje na nowy `handle_add_note` (do napisania w Sesji D.2, na razie stub rzucający NotImplementedError). POST-MVP intencje (`edit_client`, `filtruj_klientów`, `lejek_sprzedazowy`) wskazują na jeden wspólny `handle_post_mvp_banner` (do napisania w tym samym kroku — zwraca R5 banner „w MVP tylko podgląd w dashboardzie”).
  - **Commit**: `Phase C.1: text.py — router aligned to 6 MVP + R5 banner`
- **Krok C.2** — `text.py`, usunąć martwe handlery: `handle_delete_client`, `handle_view_meetings` (z detekcją free_slots), stare `handle_show_pipeline`, stare `handle_filter_clients`. Usunąć też `_contains_phone` auto-routing do `handle_add_client` (Bug #7). Usunąć `save_immediately` via „zapisz” keyword (łamie R1).
  - **Commit**: `Phase C.2: text.py — remove dead handlers + R1 violations`
- **Krok C.3** — `text.py`, `handle_confirm` + cancel flow: przepisać na one-click cancel (bez „Na pewno?”), wywoływać `build_mutation_buttons` z A.1, obsłużyć `append` (zostawia pending otwarte, karta się przebuduje). Usunąć `handle_cancel_flow` 2-step.
  - **Commit**: `Phase C.3: text.py — confirm flow + one-click cancel per R1`
- **Krok C.4** — `text.py`, nowa funkcja `send_next_action_prompt(client_name)` implementująca R7: wysyła **jedno wolnotekstowe pytanie** w stylu „Co dalej z Janem Kowalskim? Spotkanie, telefon, follow-up?” z jednym przyciskiem `[❌ Anuluj / nic]`. **Nie sztywna trójka.** Parser odpowiedzi: jeśli zawiera akcję + czas → routuje do `add_meeting` flow z compound fusion; jeśli „nie wiem” / „potem” / cancel → zamyka cicho.
  - **Commit**: `Phase C.4: text.py — R7 next_action_prompt (free-text)`

### Sesja D — add_client + add_note

Cel: dwie najczęstsze mutacje przepisane pod nowy flow.

- **Krok D.1** — `handle_add_client` w `text.py`: używać `build_mutation_buttons`, budować kartę przez zaktualizowany `format_add_client_card` (moc i metraże do `Notatki`, nie do widocznego wiersza). Po commit wołać `send_next_action_prompt` (R7). Obsłużyć R4 default-merge (jeśli klient istnieje, domyślnie merge, przycisk `[📋 Dopisz do istniejącego] [➕ Utwórz nowy wpis]` pokazany tylko gdy parser widzi nowe informacje).
  - **Commit**: `Phase D.1: handle_add_client — R1+R4+R7 aligned`
- **Krok D.2** — `handle_add_note` (nowy handler zastępujący błędne mapowanie na `handle_edit_client_v2`): identyfikacja klienta przez imię + nazwisko + miasto (nigdy samo nazwisko), karta R1, commit zapisuje do kolumny `Notatki` (append z datą), R7 po commicie.
  - **Commit**: `Phase D.2: handle_add_note — new handler per INTENCJE_MVP`

### Sesja E — change_status + add_meeting + show_client + show_day_plan

Cel: reszta handlerów MVP. Każdy handler = osobny krok = osobny commit.

- **Krok E.1** — `handle_change_status`: 9 statusów, R1 karta, R7 po commicie. Walidacja, że status jest na liście SSOT (inaczej odrzuca).
  - **Commit**: `Phase E.1: handle_change_status — 9-status SSOT`
- **Krok E.2** — `handle_add_meeting`: emoji differentiation (📅 in_person / 📞 phone_call / 📨 offer_email+doc_followup), polski format czasu `DD.MM.YYYY (Dzień) HH:MM`, R1 karta. **Brak** free_slots, **brak** auto-reschedule. Po commicie NIE wołamy R7 (spotkanie samo definiuje next contact — wyjątek z reguły R7).
  - **Commit**: `Phase E.2: handle_add_meeting — emoji diff + polish time, no free_slots`
- **Krok E.3** — `handle_show_client`: read-only, **bez przycisków** (R1 nie dotyczy read-only), format według `agent_system_prompt.md`.
  - **Commit**: `Phase E.3: handle_show_client — read-only no buttons`
- **Krok E.4** — `handle_show_day_plan`: read-only, spotkania + R7 telefony + follow-upy z `Data następnego kroku`. Wycięte free_slots i pipeline_stats z `format_morning_brief`.
  - **Commit**: `Phase E.4: handle_show_day_plan — read-only, no free_slots`
- **Krok E.5** — `shared/google_calendar.py`: usunąć funkcję `get_free_slots` (nie istnieje w MVP).
  - **Commit**: `Phase E.5: google_calendar — drop get_free_slots`

### Sesja F — Duplicate flow (R4) + Pending flow (R3)

Cel: poprawa stanowych flow, teraz kiedy handlery już istnieją.

- **Krok F.1** — R4 duplicate disambiguation: przepisać sekcję duplikatów (text.py ok. 402–408) na **default merge** (jeśli pola się nie kłócą, merge bez pytania). Dopiero gdy parser wykryje konflikt (np. inny telefon) → pokazać 2-przyciskową kartę R4.
  - **Commit**: `Phase F.1: duplicate flow — R4 default merge + 2-button disambiguation`
- **Krok F.2** — R3 pending flow: 4 ścieżki — (a) auto-cancel przy obcej intencji, (b) `➕ Dopisać` button, (c) auto-merge matching fields, (d) compound fusion (add_client+add_meeting, change_status+add_meeting, add_note+add_meeting). Compound fusion jako osobna helper funkcja w `shared/`.
  - **Commit**: `Phase F.2: pending flow — R3 4 routes incl. compound fusion`

### Sesja G — R6 active_client state (zamyka Bug #7)

Cel: ostatnie stanowe usprawnienie, zamyka bug auto-routingu po telefonie.

- **Krok G.1** — `shared/active_client.py` (nowy plik): klasa `ActiveClientState` z 10-msg / 30-min rolling window, przechowywana per-user w Supabase (prosty JSON na userze). Setter po każdej mutacji lub show_client. Getter zwraca active_client lub None jeśli TTL minął.
  - **Commit**: `Phase G.1: active_client state — R6 TTL window`
- **Krok G.2** — `bot/handlers/text.py`: router używa `ActiveClientState.get()` jako fallback kontekstu identyfikacji klienta (jeśli user pisze „dopisz notatkę: …” bez imienia, bierzemy z active_client). To zamyka Bug #7 (telefon nie routuje już do `handle_add_client` po namyśle).
  - **Commit**: `Phase G.2: text.py — active_client fallback identification`

### Sesja H — TESTY (dedykowana, na końcu)

Cel: dopiero teraz odpalamy Telegram. Według `docs/TEST_PLAN_11-04-2026.md`.

- Maan uruchamia bota lokalnie.
- Przechodzimy **15 testów po kolei**, od #1 do #15.
- Po każdym teście Maan wkleja screenshoty Telegram + Sheets/Calendar, ty kwitujesz „pass” albo „fail + przyczyna”.
- Faile → dokumentujemy w `CURRENT_STATUS.md` jako nowe bugi, planujemy follow-up sesję. Nie łatamy on-the-fly.
- Po przejściu wszystkich testów → commit `docs: TEST_PLAN_11-04-2026 results` z wynikami.

---

## 4. Format raportu po każdym kroku

Po zakończeniu kroku wysyłasz do Maana **dokładnie taki blok**:

```
KROK [X.Y] — [nazwa]
───────────────────
ZROBIONE:
- [co zmieniłeś, w 1-3 zdaniach]
- [które pliki dotknąłeś, z listą linii]

WERYFIKACJA STATYCZNA:
- Audyt (CODE_AUDIT_11-04-2026.md sekcja [...]) → zgodny ✅
- SSOT (INTENCJE_MVP / agent_behavior_spec_v5 sekcja [...]) → zgodny ✅

DIFF: [krótki opis lub `git diff --stat`]

COMMIT: [hash + message]

RYZYKO / WĄTPLIWOŚCI:
- [jedna linijka jeśli coś cię niepokoi, albo „brak”]

GOTOWY NA: Krok [X.Y+1] — [nazwa następnego kroku]
Czekam na zielone światło.
```

Nie dodajesz nic więcej. Nie rozpisujesz planu całej sesji na zapas. Nie pokazujesz diffów rozleglejszych niż konieczne. Krótko, konkretnie, w formacie.

---

## 5. Czego NIE robisz

- **Nie testujesz w Telegramie po każdym kroku.** Między krokami wystarcza weryfikacja statyczna (czytanie kodu + porównanie do SSOT + ewentualnie odpalenie `pytest` jeśli testy unitowe już istnieją).
- **Po zakończeniu każdej całej Sesji (A, B, C, D, E, F, G) jest obowiązkowy smoke test Telegram.** Ty wybierasz 2–3 najbardziej ryzykowne scenariusze dla zakresu sesji (np. po Sesji A: wyświetlenie karty add_client → sprawdzenie że renderują się 3 przyciski `[✅ Zapisać][➕ Dopisać][❌ Anulować]`; po Sesji C: confirm flow + one-click cancel na prawdziwym pending). Maan odpala bota, klika, robi screeny, wkleja wyniki. Pełny `docs/TEST_PLAN_11-04-2026.md` (15 testów) idzie dopiero w Sesji H. Smoke test między sesjami = ~5–10 minut, łapie regresje zanim się nawarstwią, ale nie przerywa flow CC co krok. Ta reguła nadpisuje generalny zapis CLAUDE.md #11 dla tej konkretnej serii sesji — świadomie, na podstawie decyzji Maana z 11.04 wieczór.
- **Nie refaktoryzujesz kodu, którego audyt nie zgłosił jako drift.** Nawet jeśli widzisz brzydki kod. Backlog → bo potem, teraz nie.
- **Nie dotykasz `dashboard/`, `admin/`, scheduler, Google OAuth, search_engine, Supabase auth.** Audyt ich nie zgłosił — są zdrowe, zostawiamy.
- **Nie tworzysz nowych dokumentów SSOT.** Jeśli czegoś brakuje — pytasz Maana, on decyduje, gdzie to dopisać.
- **Nie scalasz kroków.** Nawet jeśli „to przecież to samo”. Każdy krok ma osobny commit i osobny raport.
- **Nie ignorujesz CURRENT_STATUS.md.** Jeśli on mówi co innego niż ten prompt — zatrzymujesz się i pytasz. Nowsze zawsze wygrywa, ale chcemy to potwierdzić świadomie.

---

## 6. Zasady konfliktu

- SSOT > `implementation_guide_2.md`. Zawsze.
- `SOURCE_OF_TRUTH.md` > pozostałe SSOT (jest w hierarchii #1).
- `CURRENT_STATUS.md` > ten prompt, jeśli czas między ich napisaniem się rozjechał.
- `CODE_AUDIT_11-04-2026.md` > twoja pamięć o tym, „jak powinno być”. Czytasz audyt ZA KAŻDYM razem, gdy bierzesz nowy krok.
- W razie ANY wątpliwości → pytasz Maana. Nigdy nie kodujesz ze zgadywania.

---

## 7. Pierwsza wiadomość w sesji

Po wczytaniu 9 plików z sekcji 1, twoja pierwsza wiadomość do Maana to **dokładnie** (bez dodatków):

> Przeczytałem CLAUDE.md, SOURCE_OF_TRUTH, CURRENT_STATUS, CODE_AUDIT_11-04-2026, INTENCJE_MVP, agent_behavior_spec_v5, agent_system_prompt, TEST_PLAN_11-04-2026 i implementation_guide_2 (z baneru wiem że jest stale).
>
> Rozumiem zadanie: naprawa driftu kodu do SSOT w 7 sesjach (A–G) + sesja testowa (H). Jedna rzecz naraz, commit po każdym kroku, raport w formacie z sekcji 4, smoke test Telegram (2–3 scenariusze) po zakończeniu każdej sesji, pełny TEST_PLAN 15-testowy dopiero w Sesji H.
>
> Gotowy na Krok A.1 — `telegram_helpers.py`: usunięcie `build_confirm_buttons` + `build_save_buttons`, dodanie `build_mutation_buttons` (R1 3-button) i `build_duplicate_buttons` (R4 2-button).
>
> Ruszam?

I czekasz. Nic więcej. Po „ruszaj” — robisz Krok A.1, raportujesz, commitujesz, czekasz.

---

## 8. Notatka końcowa od Maana

Pracujemy **powolutku, krok po kroku, jak woda drążąca kamień**. Nie chcę bohaterskich sesji, w których w jeden wieczór przepisujemy połowę bota. Chcę, żeby każda zmiana była świadoma, udokumentowana i zwalidowana zanim przejdziemy dalej. Jeśli przyjdzie ci do głowy „zrób to szybciej” — to jest znak, że coś robisz źle. Zwolnij.

Dziękuję. Działamy.
