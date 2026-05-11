# Brief — Rozszerzenie firmowe (POST-MVP)

> Status: **POST-MVP**, do wdrożenia po ustabilizowaniu wersji indywidualnej.
> Ten dokument rozszerza `WEB_APP_BRIEF_FOR_CLAUDE_DESIGN.md` o widok firmowy. Wszystko co jest w głównym briefie — zostaje. Tu opisane jest tylko **co dochodzi**, gdy włączamy konta firmowe.

---

## 1. Czym jest rozszerzenie firmowe

Dziś OZE-Agent jest single-user: jeden handlowiec = jedno konto = jego osobiste Sheets/Calendar/Drive.

Rozszerzenie firmowe wprowadza **drugi typ konta**: **konto firmowe (Workspace)**, gdzie:

- **Właściciel firmy** (manager / szef sprzedaży / właściciel jednoosobowej firmy zatrudniającej handlowców) jest właścicielem subskrypcji.
- Właściciel **zaprasza handlowców** mailem; każdy zaproszony handlowiec dostaje konto pod parasolem firmy.
- Każdy handlowiec **dalej ma swoje osobiste Sheets, Calendar, Drive** — bot Telegram dla niego pracuje tak samo jak dziś.
- **Web app właściciela** dodatkowo **widzi wszystkie arkusze i kalendarze swoich handlowców** zagregowane w jednym miejscu — pipeline firmowy, kalendarz zespołowy, wszyscy klienci wszystkich handlowców.
- **Faktura jest jedna**, na firmę, per-seat (X handlowców × cena/seat/mies).

**Cel produktu firmowego:** dać szefowi sprzedaży to, czego dziś nie ma — prawdziwą widoczność tego, co robią jego handlowcy, bez proszenia ich o eksporty z Excela.

---

## 2. Decyzje architektoniczne (zamrożone)

### 2.1. Model danych — Model B (per-handlowiec sheets, web app agreguje)

**Każdy handlowiec ma własny arkusz, kalendarz i folder na Drive — tak samo jak konto indywidualne.** Bot Telegram dla niego nie wie, że jest w firmie — działa identycznie.

Web app właściciela odpytuje przez backend wszystkie arkusze handlowców (po `users.organization_id`) i agreguje dane do widoków firmowych w pamięci/cache.

**Plus tego modelu:**
- Bot Telegram zostaje praktycznie bez zmian.
- Brak konfliktów zapisu (każdy handlowiec pisze tylko do swojego arkusza).
- Migration path z konta indywidualnego do firmowego jest naturalny — patrz §6.
- Łatwo przywrócić handlowcowi self-ownership jeśli wychodzi z firmy.

**Minus, zaakceptowany świadomie:**
- Manager view dla 20+ handlowców jest wolniejszy (wymaga równoległych zapytań do 20 arkuszy + cache).
- Cross-handlowiec deduplikacja (alert „ten klient rozmawiał już z Twoim kolegą") wymaga osobnego indeksu w Supabase, nie wynika z arkuszy bezpośrednio.

**Model A (jeden master arkusz dla firmy)** zostaje jako **enterprise tier do rozważenia później** — dla firm 30+ handlowców, gdzie agregacja Modelu B przestaje być wydajna. **Nie wchodzi w pierwszej rundzie rozszerzenia firmowego.**

### 2.2. Migracja konto indywidualne → firmowe

Handlowiec, który dziś ma konto indywidualne, może dołączyć do firmy na zaproszenie. **Nie próbujemy automatycznie łączyć baz danych** — to skomplikowane, ryzykowne i rzadko warte zachodu.

Zamiast tego:

1. Handlowiec akceptuje zaproszenie firmowe.
2. **Ekran „Co z dotychczasowymi danymi?":** dwie opcje do wyboru:
   - **„Wyeksportuj moje obecne klienty do CSV"** — pobiera CSV z dotychczasowego osobistego arkusza, handlowiec może go potem zaimportować do nowej bazy firmowej (przez import CSV gdy będzie gotowy w POST-MVP).
   - **„Zostawiam jak jest, zaczynam świeżo"** — dotychczasowy arkusz zostaje na koncie Google handlowca jako historyczny, agent przestaje do niego pisać i zaczyna pracować z nowym arkuszem firmowym.
3. **W obu przypadkach** stary arkusz indywidualny **nie znika** — zostaje na osobistym Google handlowca, dostępny ręcznie. Po prostu agent przestaje do niego pisać.
4. **Dane historyczne nie są automatycznie przepisywane do firmowej bazy.** Jeśli handlowiec chce — robi to ręcznie przez eksport CSV i (przyszły) import. Świadoma decyzja, nie próbujemy być sprytni.

Najważniejsze: **arkusz indywidualny zostaje u handlowca**, niezależnie czy zostaje w firmie, czy z niej kiedyś odejdzie.

### 2.3. Co się dzieje, gdy handlowiec opuszcza firmę

Trzy scenariusze, jasna polityka dla każdego:

- **Handlowiec sam wychodzi:** klika „Opuść firmę" w ustawieniach. Jego dotychczasowy firmowy arkusz/kalendarz/folder zostają **u właściciela firmy** (na koncie Google właściciela albo handlowca, w zależności od kto go założył — patrz §3 i onboarding). Handlowiec wraca do statusu konta indywidualnego — ale bez danych firmowych. Może zostać na koncie indywidualnym (płaci sam), albo zostać na koncie indywidualnym darmowym tylko-do-podglądu starych własnych danych.
- **Właściciel usuwa handlowca:** ten sam efekt. Handlowiec dostaje email „Twoje konto w firmie X zostało zamknięte". Bot Telegram przestaje mu odpowiadać poza komunikatem „Twoje konto firmowe wygasło. Skontaktuj się z managerem."
- **Właściciel anuluje subskrypcję firmową:** wszyscy handlowcy dostają komunikat „Subskrypcja firmowa wygasa za X dni". Po wygaśnięciu — wszystkie konta firmowe lądują w stanie „expired" (jak indywidualne konta po wygaśnięciu).

---

## 3. Czyje konto Google jest właścicielem zasobów (Sheets/Calendar/Drive)

To jest **najczęstsze pytanie** od potencjalnego właściciela firmy. Trzeba to rozstrzygnąć w onboardingu jasno, **dwiema ścieżkami do wyboru**:

### Ścieżka A — „Konta handlowców" (rekomendowana, prostsza)

Każdy handlowiec łączy **swoje** konto Google. Arkusze, kalendarze i foldery powstają na **jego** Google. Właściciel firmy widzi je w web appie firmowym, **bo handlowiec udziela mu read-only dostępu** w trakcie onboardingu (jednym kliknięciem w naszym backendzie — bot share'uje arkusz/kalendarz na email właściciela z poziomu Google API).

**Plus:**
- Każdy handlowiec ma swoje miejsce na Drive (15 GB free per Google account).
- Brak konieczności posiadania Google Workspace przez firmę.
- Wyjście z firmy = handlowiec po prostu cofa share — dane zostają u niego.

**Minus:**
- Jeśli handlowiec wychodzi i cofa share, właściciel traci podgląd jego historycznych klientów (chyba że je wcześniej wyeksportuje).
- Drive 15 GB per handlowiec może nie wystarczyć dla intensywnego photo flow.

### Ścieżka B — „Konto firmowe Google Workspace" (enterprise)

Firma ma własną domenę i Google Workspace (`@firmazrenowacjami.pl`). Właściciel zakłada subkonta Workspace dla każdego handlowca w swoim Workspace. **Wszystkie zasoby (Sheets/Calendar/Drive) powstają w obrębie Workspace firmy** — właściciel jako Workspace admin ma do nich pełny dostęp natywnie.

**Plus:**
- Pełna kontrola właściciela — handlowiec wychodzi → jego konto Workspace się dezaktywuje → dane zostają w firmie automatycznie.
- Shared Drive (Team Drive) zamiast 15 GB per user — zarządzane centralnie.
- Najlepszy security story dla większych firm.

**Minus:**
- Wymaga że firma kupiła Google Workspace (~30 zł/user/mies dodatkowo).
- Onboarding trudniejszy — wymaga konfiguracji po stronie firmy (Workspace admin musi zaakceptować naszą aplikację).
- Niewiele małych firm OZE w Polsce ma Workspace.

**Decyzja:** **Ścieżka A jest domyślna, Ścieżka B opcjonalna jako tier „Enterprise"** — wybór w trakcie onboardingu firmowego.

W pierwszej rundzie POST-MVP **dowieziemy tylko Ścieżkę A**. Ścieżkę B jako późniejszy enterprise feature.

---

## 4. Model danych — co dochodzi w Supabase

### Nowa tabela `organizations`

```
id                    uuid (PK)
name                  text                    -- nazwa firmy ("Firma Renowacje Sp. z o.o.")
nip                   text nullable           -- NIP do faktur
address               text nullable           -- adres do faktur
owner_user_id         uuid (FK → users.id)    -- kto założył, jeden owner
plan_type             enum ('starter', 'team', 'enterprise')
seat_count            int                     -- ilu handlowców (kupione miejsca)
seat_used             int                     -- ilu zaakceptowało zaproszenie
created_at            timestamptz
google_path           enum ('shared_individual', 'workspace')  -- Ścieżka A vs B
```

### Rozszerzenia tabeli `users`

```
+ organization_id     uuid nullable (FK)      -- NULL = konto indywidualne
+ role                enum ('owner', 'member', 'individual')
+ joined_org_at       timestamptz nullable
+ shared_to_owner     bool                    -- czy share do ownera już aktywny (Ścieżka A)
```

### Nowa tabela `organization_invites`

```
id                    uuid (PK)
organization_id       uuid (FK)
email                 text                    -- na jaki mail wysłano
token                 text unique             -- token w linku akceptacyjnym
expires_at            timestamptz             -- 7 dni od wysłania
accepted_at           timestamptz nullable
declined_at           timestamptz nullable
sent_by_user_id       uuid (FK → users.id)    -- kto zaprosił (zwykle owner)
```

### Nowa tabela `organization_aggregates_cache`

Cache dla widoków firmowych — agregacja per handlowiec aktualizowana co X minut, żeby manager view nie odpytywał 20 arkuszy synchronicznie:

```
organization_id       uuid (FK)
user_id               uuid (FK)               -- którego handlowca dotyczy
total_clients         int
clients_per_status    jsonb                   -- {"Nowy lead": 12, "Podpisane": 5, ...}
meetings_today        int
last_activity_at      timestamptz
cache_updated_at      timestamptz
```

---

## 5. Onboarding firmowy

**Drugi flow obok obecnego onboardingu indywidualnego.** Na `/rejestracja` na samym początku ekran wyboru:

> **Zakładasz konto dla siebie czy dla firmy?**
>
> [👤 Indywidualne — pracuję sam]
> [🏢 Firmowe — mam zespół handlowców]

### 5.1. Onboarding firmowy — krok po kroku (właściciel)

**Krok 1 — Dane firmy + dane właściciela**
- Imię, nazwisko, email, hasło (lub Google Sign-In) — to dane właściciela jako osoby
- Nazwa firmy
- NIP firmy
- Adres firmy (do faktury)
- 6 pól ankiety jak w indywidualnym (region, branża, doświadczenie, źródło)
- Liczba handlowców planowanych (1-5 / 5-15 / 15+) — pomaga dobrać plan
- 3 checkboxy (regulamin wymagany, marketing, kontakt)

**Krok 2 — Wybór planu firmowego**
- 3 plany do wyboru:
  - **Starter** — do 5 handlowców, 39 zł / handlowiec / mies (rocznie 350 zł / handlowiec)
  - **Team** — do 15 handlowców, 35 zł / handlowiec / mies (rocznie 320 zł / handlowiec)
  - **Enterprise** — 15+ handlowców, indywidualnie (CTA „Skontaktuj się z nami")
- **Aktywacja firmowa: 499 zł jednorazowo** (zakładamy organizację, agregację, robimy onboarding handlowców)
- **Wybór liczby seats** — slider 1-15, kalkulator pokazuje koszt miesięczny i roczny
- Płatność: Przelewy24, faktura VAT na firmę

**Krok 3 — Wybór ścieżki Google**

> **Skąd mają pochodzić arkusze i kalendarze handlowców?**
>
> **[A — Każdy handlowiec łączy swoje konto Google]** (rekomendowane, najprostsze)
> Każdy handlowiec ma własny arkusz na swoim Google. Ty widzisz wszystko w panelu firmowym, bo każdy udzieli Ci dostępu w trakcie onboardingu.
>
> **[B — Mamy Google Workspace dla firmy]** (enterprise)
> Wszystkie arkusze i kalendarze powstają w Twojej domenie firmowej (`@twojafirma.pl`). Kontrola jest pełna, ale wymaga że firma ma Workspace.

W pierwszej rundzie pokazujemy tylko ścieżkę A (B disabled z tooltipem „Wkrótce — w międzyczasie zacznij od ścieżki A").

**Krok 4 — Połączenie konta Google właściciela**
- Standardowy Google OAuth — **mocno zaakcentowane: nawet jeśli ty osobiście nie jesteś handlowcem, łączysz konto Google bo na nie będą przychodzić share'y od Twoich handlowców** (ich arkusze, ich kalendarze).
- Można pominąć ten krok („Nie chcę swojego Google teraz") — wtedy właściciel widzi panel firmowy bez bezpośredniego dostępu do plików Google handlowców (tylko przez naszą agregację). Nie zalecane, bo gubi się quick-action „otwórz arkusz handlowca w Google".

**Krok 5 — Zaproszenie handlowców**
- Pole tekstowe: „Wpisz emaile handlowców, każdy w osobnej linii". Walidacja na żywo.
- Lista mailów z X obok („usuń"), licznik „Wysłałeś N z M zakupionych miejsc".
- Opcjonalnie pole „Wiadomość dla zespołu" — krótki tekst, który dołączymy do emaila zaproszeniowego.
- CTA: „Wyślij zaproszenia".
- **Można pominąć:** „Zaproszę później, zacznij konfigurację zespołu" — wtedy idzie do dashboardu.
- Po wysłaniu: ekran z listą wysłanych zaproszeń + status każdego („📧 Wysłano · czeka na akceptację").

**Krok 6 — Powitanie w panelu firmowym**
- Ekran przejściowy (nie pełen banner, raczej overlay):

> 🫡 Konto firmowe gotowe.
>
> **Co dalej:**
> 1. Twoi handlowcy dostali emaile z zaproszeniem — każdy z nich przejdzie własny krótki onboarding (Google + Telegram).
> 2. Możesz śledzić ich postęp w sekcji **Zespół**.
> 3. Twój panel firmowy zacznie pokazywać dane gdy chociaż jeden handlowiec skończy swój onboarding.
>
> [Otwórz Zespół] [Otwórz instrukcję firmową]

### 5.2. Onboarding handlowca zaproszonego do firmy

Handlowiec klika link w emailu zaproszeniowym → ląduje na `/akceptuj-zaproszenie?token=XXX`.

**Krok 1 — Akceptacja zaproszenia**
- Karta:
  > **Marek Kowalski (właściciel) zaprasza Cię do firmy „Firma Renowacje Sp. z o.o."**
  >
  > Twoja rola: handlowiec.
  > Twój manager będzie widział Twoich klientów i Twój kalendarz.
  >
  > [Akceptuję — załóż konto] [Odrzucam zaproszenie]

- **Brak ukrywania faktu, że manager widzi.** Punkt z naszej rozmowy: nigdzie nie obiecujemy że dane są niewidoczne. Onboarding firmowy mówi to wprost.

**Krok 2 — Konto handlowca**
- Imię, nazwisko, email (pre-filled z zaproszenia), hasło (lub Google Sign-In).
- Bez ankiety — to jest konto pod parasolem firmy, dane firmowe wzięte z org.
- 1 checkbox: regulamin (wymagany).

**Krok 3 — Czy masz już konto OZE-Agent indywidualne na tym mailu?**
- Auto-detekcja: jeśli `email` zaproszenia istnieje już w `users` jako `role=individual` → wyświetlamy:

> Mamy już Twoje konto indywidualne na tym mailu.
>
> Co zrobić z dotychczasowymi danymi?
>
> [📥 Wyeksportuję teraz CSV i potem zaimportuję do firmy]
> [➡️ Zostawiam jak jest, zaczynam świeżo]
>
> W obu przypadkach Twój dotychczasowy arkusz zostaje na Twoim koncie Google.

- Jeśli wybrał eksport → **przycisk „Pobierz CSV teraz"** generuje plik, otwiera download. Dopiero po pobraniu CTA „Idę dalej" odblokowuje się.
- Jeśli zostawia jak jest → bezpośrednio do kroku 4.

**Krok 4 — Połączenie konta Google handlowca + auto-share do właściciela**
- Standardowy Google OAuth (Sheets + Calendar + Drive).
- Po sukcesie: **animowany checklist taki sam jak w onboardingu indywidualnym**, ale z dodatkową linią na końcu:

```
✅ Tworzę arkusz „OZE Klienci — Marek (Firma Renowacje)"...
✅ Dodaję 16 kolumn...
✅ Ustawiam dropdowny statusów...
✅ Tworzę kalendarz „OZE Spotkania — Marek (Firma Renowacje)"...
✅ Tworzę folder na Drive...
🔄 Udzielam dostępu Twojemu managerowi (właścicielowi firmy)...
✅ Gotowe.
```

- Ostatni krok (share) jest robiony przez nasz backend: Google Sheets API → `permissions.create` z `type=user`, `role=reader`, `emailAddress=owner_email`. Dla Calendar: ACL rule. Dla Drive folder: też share.

**Krok 5 — Parowanie z Telegramem**
- Identyczne jak w onboardingu indywidualnym (kod 6-cyfrowy, sparowanie z @OZEAgentBot).

**Krok 6 — Powitanie**

> 🫡 Witaj w firmie. Konto gotowe.
>
> Twój pierwszy klient: powiedz agentowi w Telegramie. Twój manager zobaczy go w swoim panelu firmowym.

---

## 6. Web app — co dochodzi w widoku firmowym

### 6.1. Sidebar — nowe sekcje dla roli `owner`

Dla `role=owner` sidebar zawiera dodatkowe sekcje na górze, **przed** sekcjami osobistymi:

- 🏢 **Panel firmowy** (dashboard firmy — agregacja całego zespołu)
- 👥 **Zespół** (lista handlowców, zarządzanie zaproszeniami, seats)
- 📊 **Lejek zespołowy** (ten sam co w widoku osobistym, ale agregowany ze wszystkich handlowców)
- 📅 **Kalendarz zespołowy** (wszystkie spotkania wszystkich handlowców)
- 👨‍💼 **Klienci zespołu** (wszystkie kontakty wszystkich handlowców, z kolumną „Handlowiec")

Pod tym **separator** + zwykłe sekcje (Dashboard / Klienci / Kalendarz / Statystyki / Ustawienia / itd.) jako **„Mój widok"** — manager też może być handlowcem swojego osobistego pipeline'u, jeśli chce.

Dla `role=member` (zwykły handlowiec w firmie) sidebar wygląda identycznie jak konto indywidualne. **Handlowiec nie widzi nic z firmowego panelu — widzi tylko siebie.** (Punkt etyczny: jednostronna widoczność. Manager widzi wszystko, handlowiec widzi siebie.)

### 6.2. `/firma/dashboard` — Panel firmowy (główny ekran ownera)

Layout taki sam jak osobisty dashboard, ale dane są agregatem.

**Górny pas — 4 KPI cards:**
- **Cały zespół: spotkania dziś** (liczba + breakdown per handlowiec po hover)
- **Nowi klienci ten tydzień** (cały zespół, sparkline)
- **Oferty wysłane (cały zespół)** (z liczbą czekających)
- **Podpisane w tym miesiącu (cały zespół)** + cel firmowy

**Środkowy pas:**
- **Lejek zespołowy** (8 kolumn) — 9 statusów × cały zespół, każdy słupek klikalny → lista wszystkich klientów w tym statusie z kolumną „Handlowiec"
- **Aktywność zespołu** (4 kolumny) — wykres słupkowy z **stacked colors per handlowiec** (każdy handlowiec ma swój kolor)

**Dolny pas:**
- **Plan dnia firmy** (6 kolumn) — wszystkie spotkania zespołu chronologicznie, każde z avatarem handlowca prowadzącego
- **Top handlowcy tygodnia** (6 kolumn) — leaderboard? **NIE** — Maan w guidance mówi „brak gamifikacji". Zamiast tego: **„Aktywność handlowców w tym tygodniu"** — neutralna lista z liczbami (nowi klienci, podpisane, spotkania), bez rankingu, bez emoji medali. Daje informację, nie konkurencję.

### 6.3. `/firma/zespol` — Zarządzanie zespołem

**Główna tabela:** lista wszystkich handlowców firmy.

Kolumny: avatar + imię nazwisko, email, status (active / pending invitation / paused), data dołączenia, liczba klientów, ostatnia aktywność, akcje.

Akcje per wiersz (3-dot menu):
- **Otwórz panel handlowca** — manager wchodzi w widok danego handlowca (jak impersonate, ale tylko-do-podglądu — nie może mutować nic w jego imieniu)
- **Wyślij wiadomość przez Telegram** — krótkie pole, wiadomość trafia jako broadcast od ownera do handlowca w jego Telegramie (np. „Spotkanie zespołu w piątek 16:00")
- **Zawieś dostęp** — wyłącza handlowca tymczasowo (urlop), agent przestaje odpowiadać
- **Usuń z firmy** — z confirmation modalem mocno ostrzegawczym

**U góry tabeli:**
- **Licznik seats:** „Wykorzystane: 7 z 10 zakupionych. [Dokup miejsca]"
- **Przycisk „Zaproś handlowca":** otwiera modal z polem na email + opcjonalna wiadomość, wysyła zaproszenie, dodaje wiersz „pending" do tabeli z linkiem do skopiowania zaproszenia (na wypadek gdyby email nie doszedł).

**Sekcja „Zaproszenia":**
- Tabela pending invites: email, kiedy wysłane, kiedy wygasa, akcje (resend, cancel).

### 6.4. `/firma/klienci` — Wszyscy klienci zespołu

Identyczna w strukturze jak osobista `/klienci`, **ale z dodatkową kolumną „Handlowiec"** (avatar + imię), filtrem po handlowcu (multi-select), i opcją grupowania „Pokaż zgrupowane per handlowiec".

**Side panel karty klienta** dodatkowo pokazuje:
- Linijka u góry: „Klient handlowca: Marek Kowalski"
- Akcję „📊 Otwórz w Sheets Marka" (deep link do arkusza tego konkretnego handlowca, do tego konkretnego wiersza)
- Czytelne, że dane żyją na koncie tego handlowca, manager je tylko czyta przez share

**Wykrycie duplikatów cross-team** (niska priorytet, dorobić jak będzie czas):
- Banner u góry karty jeśli ten sam imię+nazwisko+miasto występuje u dwóch handlowców firmy: „⚠️ Ten klient występuje też u Anny Lis (Spotkanie umówione, 12.04.2026). Skontaktujcie się żeby uniknąć dublowania."

### 6.5. `/firma/kalendarz` — Kalendarz zespołowy

Widok tygodnia / miesiąca, ale każde wydarzenie ma kolor handlowca. Legenda po prawej (lista handlowców z kolorami, można klikać żeby filtrować widok).

Klik w wydarzenie → popup z danymi klienta + linią „Spotkanie handlowca: [imię]".

**Funkcja `team-conflict detection` (przyszłość, nie pierwsza runda):** ostrzeżenie gdy dwóch handlowców ma spotkanie z tym samym klientem tego samego dnia.

### 6.6. `/firma/statystyki` — Statystyki zespołu

Layout taki sam jak osobiste `/statystyki`, ale:
- **Filtr handlowca** (all / single / multi-select)
- Dodatkowo: **wykres porównawczy handlowców** (bar chart per handlowiec × metryka: nowi klienci, podpisane, % konwersji)
- **Tabela źródeł leadów** — z kolumną „% konwersji per handlowiec per źródło" (które źródło Marek konwertuje najlepiej?)

### 6.7. `/firma/ustawienia` — Ustawienia firmy

Tabbed:

1. **Dane firmy** — nazwa, NIP, adres, dane do faktury, telefon, logo (opcjonalnie do brandingu maili/zaproszeń)
2. **Plan i seats** — aktualny plan, ilu używanych z ilu zakupionych, „Dokup seats", „Zmień plan", „Anuluj subskrypcję firmową"
3. **Standardy firmy** — ustawienia, które dotyczą wszystkich handlowców firmy (mogą być nadpisane przez handlowca w jego osobistych ustawieniach):
   - Domyślna godzina morning briefu zespołu (np. 06:30 zamiast 07:00)
   - Standardowy lejek statusów (czy wszyscy używają tych samych 9, czy firma ma swoje)
   - Standardowe kolumny dodatkowe (POST-MVP)
4. **Powiadomienia ownera** — czy chcesz codzienny brief firmowy mailem (rano), tygodniowy raport, alerty (handlowiec nieaktywny >7 dni)
5. **Branding** — logo firmy w stopce arkuszy, kolor akcentowy (POST-MVP, miłe-do-mam)

### 6.8. `/firma/platnosci` — Płatności firmowe

- **Status subskrypcji firmowej** — plan, seats, kwota miesięczna/roczna
- **Faktura na firmę** (NIP, dane firmy) — historia faktur z download PDF
- **Rozliczenie per seat** — pokazuje ile aktualnie aktywnych handlowców × cena/seat, czy są seats nieobsadzone (z opcją „zwolnij niewykorzystane")
- **Dokupywanie seats** w trakcie — proporcjonalne doliczenie do bieżącego okresu

---

## 7. Cennik firmowy (propozycja, do walidacji)

| Plan | Limit handlowców | Cena/seat/mies | Cena/seat/rok | Aktywacja |
|------|------------------|----------------|---------------|-----------|
| Starter | do 5 | 39 zł | 350 zł | 499 zł |
| Team | do 15 | 35 zł | 320 zł | 499 zł |
| Enterprise | 15+ | indywidualnie | indywidualnie | indywidualnie |

**Założenie biznesowe:** plan firmowy jest tańszy per-seat niż konto indywidualne (49 zł), bo właściciel zobowiązuje się do zakupu wielu seats. Ale wyższa aktywacja (499 vs 199), bo wymaga więcej naszej pracy onboardingowej.

**Opcjonalnie:**
- 14-dniowy darmowy trial dla planów firmowych (POST-MVP, zarządzanie ryzykiem trial-abuse)
- Discount roczny ~17% (jak indywidualny)

---

## 8. Komunikacja / FAQ — co dochodzi

### Nowe sekcje w `/faq`

**Konta firmowe:**
- „Czym różni się konto indywidualne od firmowego?"
- „Czy handlowiec widzi klientów innych handlowców z firmy?" → **NIE**, widzi tylko swoich. Manager widzi wszystkich.
- „Czy handlowiec wie, że manager widzi jego dane?" → **TAK**, mówimy to wprost przy akceptacji zaproszenia firmowego.
- „Czy mogę zaprosić siebie jako handlowca, jeśli jestem właścicielem?" → TAK — owner ma też swoje osobiste konto handlowca pod parasolem firmy.
- „Co się dzieje gdy handlowiec opuszcza firmę?" → patrz §2.3.
- „Mam już dane w koncie indywidualnym, jak je przenieść do firmowego?" → eksport CSV → import w nowej bazie firmowej. Patrz §2.2.
- „Czy faktura jest jedna na firmę?" → TAK, z NIP-em, miesięcznie lub rocznie.
- „Czy mogę zmienić plan ze Starter na Team w trakcie?" → TAK, kalkulujemy proporcjonalnie do końca okresu.
- „Co jeśli mam Workspace Google?" → patrz Ścieżka B (Enterprise tier, w przyszłości).

### Nowa sekcja w `/instrukcja` (sidebar)

**Część firmowa** (widoczna tylko dla `role=owner`):
9. „Panel firmowy — co tu jest" (1 min)
10. „Zarządzanie zespołem" (2 min)
11. „Co handlowiec widzi, a czego nie" (1 min)

---

## 9. Implications dla bota Telegram (co dochodzi po stronie bota)

### Generator ofert w kontekście firmowym

Stan 04.05.2026: generator ofert jest zaimplementowany jako profil i szablony
sprzedawcy (`offer_seller_profiles`, `offer_templates`). W modelu firmowym nie
zakładamy automatycznie współdzielonych ofert całej organizacji. Jeśli owner ma
zarządzać wspólnymi szablonami, to jest osobna decyzja produktowa i osobny model
uprawnień.

**Bot nie zmienia się prawie wcale**, ale:

1. **Nowy intent typu informacyjnego** — handlowiec może zapytać agenta „Kto jeszcze rozmawiał z Kowalskim w naszej firmie?" — agent odpowiada na podstawie cross-team query (czyli musi mieć dostęp do `organization_aggregates_cache`). To jest **POST-MVP rozszerzenia firmowego**, nie pierwsza runda.

2. **Nowy typ powiadomienia od ownera** — manager z web appa wysyła wiadomość do całego zespołu („Spotkanie firmowe w piątek 16:00") — bot dostarcza ją każdemu handlowcowi w Telegramie. Wymaga endpointu `POST /api/org/broadcast` w backendzie + queue w bocie.

3. **Subscription state per organization** — handlowiec dostaje od bota komunikat „Subskrypcja firmowa wygasła" zamiast „Twoja subskrypcja wygasła". Tekst inny, mechanika ta sama.

4. **Agent zachowuje się tak samo dla handlowca** — nie wie, że jest w firmie. Pisze do swojego arkusza (który share-uje do ownera) i swojego kalendarza. Cała magia agregacji dzieje się w web appie.

---

## 10. Nie robimy w pierwszej rundzie rozszerzenia firmowego

- **Master arkusz dla całej firmy (Model A)** — zostaje jako enterprise tier.
- **Workspace Google integration (Ścieżka B)** — enterprise.
- **Cross-team intent w bocie** („kto rozmawiał z Kowalskim") — POST-rozszerzenie.
- **Team conflict detection w kalendarzu** — POST-rozszerzenie.
- **Trial 14-dniowy** — POST-rozszerzenie.
- **Branding firmowy** (logo, kolor akcentowy) — POST-rozszerzenie.
- **Leaderboard / ranking handlowców** — **nigdy.** Maan jasno powiedział: brak gamifikacji.
- **Automatyczna migracja danych z konta indywidualnego do firmowego** — **świadomie nie**, robimy przez eksport CSV (§2.2).

---

## 11. Co dostarczyć w pierwszej iteracji rozszerzenia firmowego

1. **Modyfikacja onboardingu**: ekran wyboru indywidualne vs firmowe na samym początku `/rejestracja`.
2. **Onboarding firmowy 6-step** dla ownera — patrz §5.1.
3. **Onboarding handlowca zaproszonego** 6-step — patrz §5.2 (z auto-share do ownera w trakcie OAuth).
4. **`/firma/dashboard`** — pełen panel firmowy (4 KPI + lejek zespołowy + aktywność + plan dnia firmy + lista aktywności handlowców).
5. **`/firma/zespol`** — zarządzanie zespołem (lista, zaproszenia, seats).
6. **`/firma/klienci`** — wszyscy klienci zespołu z kolumną Handlowiec.
7. **`/firma/platnosci`** — płatności firmowe z fakturą na NIP.

Pozostałe (kalendarz zespołowy, statystyki firmowe, ustawienia firmowe, FAQ rozszerzenie) — w drugiej iteracji rozszerzenia.

---

## 12. Estymacja wysiłku (gruba)

- **Backend (Supabase + FastAPI):** model danych, agregacja per org, share automation w Google API, billing per-seat → **~4–5 tygodni**
- **Frontend (web app):** 7 nowych ekranów + modyfikacja onboardingu + role-based sidebar → **~4 tygodnie**
- **Bot (Telegram):** broadcast endpoint + subscription messaging dla orgs → **~1 tydzień**
- **QA i bug fixing:** **~2 tygodnie**

**Razem: ~10–12 tygodni** dla pierwszej rundy rozszerzenia firmowego (jeden pełnoetatowy programista, plus design dostarczany przez claude.design).

---

## 13. Notka strategiczna

Rozszerzenie firmowe jest decyzją produktową, która zmienia OZE-Agent z **narzędzia dla freelancerów handlowych** w **narzędzie zespołowe dla firm OZE w Polsce**. To są dwa różne rynki, z różnymi cyklami sprzedaży:

- **Indywidualny handlowiec:** decyduje sam, kupuje kartą za 199+49 zł, używa od razu.
- **Firma:** decyduje właściciel po rozmowie z paroma handlowcami, czeka na fakturę VAT, potrzebuje onboardingu zespołu.

Cykl sprzedaży B2B jest dłuższy (2-4 tygodnie zamiast 24 godzin), ale LTV jest 5-10x wyższe. Warto rozważyć, czy nie warto **przed wdrożeniem rozszerzenia** dorobić małego sales pipeline'u po naszej stronie (formularz „Skontaktuj się ze sprzedażą firmową" zamiast samoobsługi w pierwszej rundzie). To jest decyzja go-to-market, nie produktu — ale spec o niej wspomina, żebyś o tym pamiętał.
