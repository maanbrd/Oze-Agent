# Brief dla claude.ai/design — Web App OZE-Agent

> Wklej całość jako prompt w claude.ai/design. Brief jest po polsku, bo cały produkt mówi po polsku do polskich handlowców OZE. Wszystkie teksty UI muszą być po polsku.

---

## 1. Co budujemy

Web app o nazwie roboczej **OZE-Agent**. Jest to centrum dowodzenia dla **handlowca B2C w branży OZE** (fotowoltaika, pompy ciepła, magazyny energii) w Polsce.

Handlowiec ma już agenta AI, który żyje w Telegramie na jego telefonie — agent zarządza klientami w jego Google Sheets, kalendarzem w Google Calendar i zdjęciami w Google Drive. Telegram jest do pracy w terenie (głosówki w aucie, szybkie wpisy między spotkaniami).

**Web app jest do pracy przy biurku.** Kiedy handlowiec siada do komputera rano albo wieczorem, otwiera ten web app i widzi:
- gdzie stoi z lejkiem sprzedaży,
- co go dziś czeka i co zaległe,
- którzy klienci wymagają działania teraz,
- jego aktywność w czasie.

**Web app nie ma czatu z agentem.** Czat dzieje się w Telegramie — to jest świadoma decyzja produktowa, nie ograniczenie. Web app jest do **przeglądania, planowania, ustawień i płatności**, nie do rozmowy z agentem.

---

## 2. Użytkownik docelowy

- **Mężczyzna 28–50 lat**, handlowiec terenowy w firmie OZE w Polsce.
- Pracuje z telefonem w aucie, laptopem wieczorem.
- **Nie jest geekiem** — Excel/Google Sheets traktuje jak rzecz konieczną, ale nie lubi.
- Liczy się dla niego: liczba podpisanych umów w miesiącu, prowizja, brak pomyłek z terminami.
- **Język bardzo bezpośredni** — handlowcy w terenie mówią twardo, czasem przeklinają. UI ma być rzeczowe, **bez korpomowy**, bez „Witaj!", „Cieszymy się, że tu jesteś!", „Świetnie!".
- Nie chce się uczyć narzędzia. Powinien widzieć od razu co robić.

---

## 3. Ton i język UI

**Bezwzględnie zabronione frazy:**
- „Świetnie!" / „Doskonale!" / „Z przyjemnością!" / „Oczywiście!"
- „Czy możemy w czymś jeszcze pomóc?"
- „Mam nadzieję, że się przyda!"
- „Przygotowaliśmy dla Ciebie..." / „Oto Twój dashboard..."
- Motywacyjne hasła („Powodzenia!", „Udanego dnia!").

**Pożądany ton:**
- Konkretny. Krótki. Z lekką szorstkością, ale uprzejmy.
- Jak zdolny kolega po fachu — mówi po imieniu, nie traci czasu na grzeczności.
- Maksimum informacji, minimum słów.
- Polski **potoczny biznesowy**, nie formalny urzędowy.

**Przykładowe linijki w stylu, w którym ma to brzmieć:**
- „Dziś masz 4 spotkania. 2 wymagają potwierdzenia." (zamiast: „Witaj! Oto Twój plan dnia.")
- „6 ofert czeka >7 dni — zadzwoń." (zamiast: „Może warto skontaktować się z klientami?")
- „Subskrypcja kończy się za 3 dni." (zamiast: „Pamiętaj, że Twoja subskrypcja wkrótce wygaśnie!").
- „Anulowane." (zamiast: „Operacja została anulowana pomyślnie.").

**Emoji** — używaj funkcjonalnie, nie dekoracyjnie. Dozwolone: ✅ ❌ ➕ 📋 📅 📞 📨 📸 📄 ⚠️ 🫡. Zabronione: 🎉 🌟 ✨ 💪 🙌 👏 🚀 😊.

---

## 4. Stylistyka wizualna

- **Dark mode pierwszy** (light mode opcjonalny w przyszłości — ale zaprojektuj dark od razu, to jest target).
- **Minimalistyczny, profesjonalny, gęsty informacyjnie** — handlowiec chce zobaczyć dużo na jednym ekranie, nie scrollować przez airy whitespace.
- **Inspiracja:** Linear, Notion (dark), Vercel dashboard. **NIE:** SaaS-y typu HubSpot, Salesforce (przeładowane). **NIE:** webowe „kreatywne" portfolio.
- **Typografia:** Inter lub podobny san-serif, czytelność > efekt. Liczby (metryki) wyróżnione tabular-nums.
- **Paleta:**
  - Tło: bardzo ciemny grafit, nie czysta czerń (np. `#0B0D10`, `#13161B`)
  - Tekst: jasny szary (nie czysta biel — mniej męczący wieczorem)
  - **Akcent główny: ciepły zielony OZE** (kojarzy się z energią odnawialną, ale nie kiczowaty „eko" — bardziej jak Spotify zielony lub bardziej stonowany)
  - Akcent ostrzegawczy: bursztyn/żółty (zaległe follow-upy)
  - Akcent krytyczny: czerwień (subskrypcja wygasła, błąd zapisu)
- **Border-radius:** umiarkowany (8–12 px), nie pillowy.
- **Cienie:** subtelne, bardziej outline niż drop shadow.
- **Komponenty:** styl shadcn/ui jest dobrym punktem wyjścia.
- **Mobile:** drugorzędne. Ten app jest do desktopa (handlowiec siada do komputera). Responsywność w sensie „nie psuje się na tablecie" wystarczy. Telefon mają dla Telegrama.

---

## 5. Struktura nawigacji

**Sidebar po lewej, persistent, kolapsowalny** (ikona + label, w wąskim widoku tylko ikony).

Sekcje sidebar (kolejność istotna):

1. **Dashboard** (home, ikona dashboardu) — centrum dowodzenia.
2. **Klienci** (ikona ludzi) — widok tabelaryczny + filtry, klik w wiersz = karta klienta.
3. **Kalendarz** (ikona kalendarza) — widok tygodnia / miesiąca / listy spotkań.
4. **Statystyki** (ikona wykresu) — wykresy aktywności i lejka w czasie.
5. **Import klientów** (ikona upload) — CSV / Excel.
6. **Instrukcja** (ikona książki) — interaktywny tutorial / „Poznaj swojego agenta".
7. **FAQ** (ikona ?) — najczęstsze pytania.
8. **Płatności** (ikona portfela) — status subskrypcji, faktury, zmiana planu.
9. **Ustawienia** (ikona zębatki, dół sidebar) — kolumny arkusza, statusy lejka, godzina morning briefu, dni robocze, profil.

**Topbar:** logo lewo (kliknięcie → dashboard), pole wyszukiwania klienta (działa cross-page), avatar usera prawo (rozwija menu: profil, wyloguj).

**Floating action buttons w prawym dolnym rogu** — **zawsze widoczne na każdej stronie po zalogowaniu**. Trzy okrągłe przyciski w pionie:
- 📊 **Sheets** — klik otwiera w nowej karcie Google Sheets usera (jego osobisty arkusz klientów stworzony przy onboardingu).
- 📅 **Calendar** — klik otwiera Google Calendar usera (jego dedykowany kalendarz OZE).
- 📁 **Drive** — klik otwiera folder na Google Drive (gdzie agent zapisuje zdjęcia klientów).

Każdy przycisk ma tooltip po prawej („Otwórz arkusz klientów", „Otwórz kalendarz", „Otwórz folder zdjęć"). Klik = `target="_blank"`, nie embed.

---

## 6. Strony — szczegółowy opis

### 6.1. `/` — Landing publiczny (niezalogowany)

Strona marketingowa. Cele: wyjaśnić co robi agent, pokazać demo, sprzedać subskrypcję.

**Sekcje, w kolejności scrollowania:**

**Hero**
- Headline (duży, mocny, jedna linia): „Twój asystent sprzedaży OZE w Telegramie."
- Subheadline (jedna linia, bez korpomowy): „Mówisz po spotkaniu — agent zapisuje klienta, dodaje spotkanie do kalendarza, pilnuje follow-upów. Bez klikania w Excelu."
- CTA primary: „Załóż konto" (zielony, prowadzi do `/rejestracja`).
- CTA secondary: „Zobacz demo" (outline, scroll do sekcji demo).
- Po prawej: mockup ekranu Telegrama z przykładową rozmową: handlowiec mówi głosówką → karta zapisu klienta → ✅ Zapisane.

**Co umie agent (3 kolumny ikon)**
- 🎙️ „Mów głosówką po spotkaniu" — agent wyciągnie dane klienta i zapisze.
- 📅 „Dodaje spotkania do kalendarza" — same powiedz „jutro o 14 jadę do Kowalskiego".
- 🫡 „Przypomina rano o planie dnia" — codziennie o 7:00 dostajesz brief w Telegramie.

**Jak to działa (4 kroki, prosta linia)**
1. Zakładasz konto i podpinasz swoje Google.
2. Łączysz konto z Telegramem (kod 6-cyfrowy).
3. Mówisz/piszesz do bota w Telegramie po polsku, swoimi słowami.
4. Agent zapisuje, ty potwierdzasz `✅ Zapisać` — i dane są w Twoim arkuszu i kalendarzu Google.

**Demo dashboard (interaktywny podgląd dashboardu)**
- Mała sekcja z screenshotami / wbudowanym żywym demo dashboardu z fikcyjnymi 20+ klientami, lejkiem, planem dnia.
- Banner u góry sekcji: „To demo — dane są fikcyjne. Załóż konto, żeby zobaczyć swoje."
- Pod demo CTA: „Zobacz pełne demo" (otwiera `/demo` — pełny dashboard tylko-do-podglądu).

**Cennik (3 karty)**
- **Aktywacja** — 199 zł jednorazowo (zakładamy Twoje arkusze, kalendarz, łączymy z Telegramem).
- **Miesięcznie** — 49 zł / mies (rezygnujesz kiedy chcesz).
- **Rocznie** — 350 zł / rok (oszczędność ~40%, badge „Najczęściej wybierane").
- CTA każdej karty: „Wybierz".

**FAQ (skrócony, 5–6 pytań)**
- „Gdzie są moje dane klientów?" → na Twoim koncie Google — w Twoich Sheets, Calendar i Drive. Możesz je w każdej chwili otworzyć ręcznie i edytować.
- „Co jeśli zrezygnuję?" → dane zostają na Twoim koncie Google. Nic nie kasujemy.
- „Czy mogę używać agenta z laptopa?" → tak, **w Telegram Web** lub **w aplikacji desktop Telegrama**. Web app to centrum dowodzenia, nie czat.
- „Czy agent rozumie polskie odmiany imion?" („u Krzywińskim" → Krzywiński)? → tak.
- „Czy muszę kupować nowe konto Google?" → zalecamy osobne konto OZE (15 GB Drive za darmo), ale to nie jest wymagane.
- „Co z VAT-em?" → faktury VAT dostępne w sekcji Płatności.

**Stopka**
- Linki: Polityka prywatności, Regulamin, Kontakt, Status systemu.
- Copyright + adres firmy.

**Sticky CTA bar na dole strony** (po zescrollowaniu hero): „Zacznij — 3 minuty setup" + przycisk „Załóż konto".

---

### 6.2. `/rejestracja` — Onboarding wizard (krytyczny ekran)

To jest **najważniejszy flow w całym appie** — Maan chce żeby był prowadzący, interaktywny, bezbłędny. **Stepper na górze**, jeden krok na ekranie. Można cofać krokami, nie można skakać do przodu bez ukończenia poprzedniego.

#### Krok 1 — Rejestracja konta

- Pola: imię, nazwisko, email, telefon, hasło (lub Google Sign-In jako alternatywa).
- 6 pól ankiety (pomagają nam zrozumieć usera, ale **krótkie**):
  - Region działania (lista województw)
  - Branża szczegółowa (PV / Pompy / PV+Magazyn / wszystko)
  - Skąd nas znasz (Facebook / polecenie / Google / inne)
  - Doświadczenie w sprzedaży OZE (do 1 roku / 1–3 lata / 3+ lat)
- 3 checkboxy: regulamin (wymagany), marketing (opcjonalny), kontakt telefoniczny (opcjonalny).
- CTA: „Dalej → Płatność".

#### Krok 2 — Płatność

- Wybór planu: Miesięcznie 49 zł / Rocznie 350 zł (z badge „Oszczędzasz 238 zł").
- Aktywacja 199 zł doliczona automatycznie (informacja widoczna).
- Metoda: **Przelewy24** (BLIK domyślnie zaznaczony).
- Sumaryzacja koszyka po prawej (sticky).
- CTA: „Zapłać i kontynuuj".
- **Po sukcesie płatności** → ekran tranzycyjny:

> ✅ Płatność przyjęta.
>
> **Ważne:** w następnym kroku połączymy agenta z Twoim kontem Google. **Mocno zalecamy założyć osobne konto Google dedykowane OZE** — dostaniesz wtedy własne 15 GB na zdjęcia klientów, oddzielone od Twoich prywatnych plików.
>
> [Mam już osobne konto, dalej] [Załóż nowe konto Google (otwiera Google w nowej karcie)]

#### Krok 3 — Połączenie z Google (OAuth)

- Krótkie wyjaśnienie co dostajemy:
  - **Google Sheets** — do prowadzenia bazy klientów (utworzymy nowy arkusz).
  - **Google Calendar** — do zarządzania spotkaniami (utworzymy nowy, dedykowany kalendarz „OZE").
  - **Google Drive** — do przechowywania zdjęć klientów (utworzymy nowy folder).
- CTA: „Połącz konto Google" (przycisk z logo Google) → standardowy Google OAuth consent screen.
- Po sukcesie → automatyczne przejście do kroku 4.

#### Krok 4 — Nazwij swoje zasoby

- 3 pola input z domyślnymi wartościami:
  - Nazwa arkusza klientów: `OZE Klienci — [Imię]` (edytowalne)
  - Nazwa kalendarza: `OZE Spotkania — [Imię]` (edytowalne)
  - Nazwa folderu na Drive: `OZE Klienci — Zdjęcia` (edytowalne)
- Pod tym, jako preview: lista 16 kolumn arkusza, które zostaną automatycznie utworzone (Imię i nazwisko, Telefon, Email, Miasto, Adres, Status, Produkt, Notatki, Data pierwszego kontaktu, Data ostatniego kontaktu, Następny krok, Data następnego kroku, Źródło pozyskania, Zdjęcia, Link do zdjęć, ID wydarzenia).
- Akord „Pokaż statusy lejka" (rozwijany) z 9 statusami: Nowy lead → Spotkanie umówione → Spotkanie odbyte → Oferta wysłana → Podpisane → Zamontowana → Rezygnacja z umowy → Nieaktywny → Odrzucone.
- Notka: „To jest standard branżowy. Zmienisz w Ustawieniach jeśli chcesz."
- CTA: „Utwórz wszystko".
- **Po kliknięciu** — pełnoekranowy stan ładowania z animowanym checklistem:

```
✅ Tworzę arkusz „OZE Klienci — Marek"...
✅ Dodaję 16 kolumn...
✅ Ustawiam dropdowny statusów (9 opcji)...
✅ Tworzę kalendarz „OZE Spotkania — Marek"...
✅ Tworzę folder na Drive...
🔄 Łączę wszystko z agentem...
```

Każdy ✅ pojawia się sekwencyjnie (300–500 ms odstęp). Na końcu „Gotowe! Ostatni krok →".

#### Krok 5 — Parowanie z Telegramem

- **To jest krok, który Maan podkreślił — ma być solidnie i interaktywnie poprowadzony.**
- Lewa strona: instrukcja krok po kroku (numerowana lista z ilustracjami / GIF-ami):
  1. Otwórz Telegram na telefonie.
  2. Wyszukaj `@OZEAgentBot`.
  3. Naciśnij „Start" (lub wpisz `/start`).
  4. Bot poprosi o kod parujący — przepisz go z prawej strony tego ekranu.
- Prawa strona: **duży kod 6-cyfrowy** w monospace (np. `4 8 2 9 1 7`), pod nim countdown „Kod ważny przez 14:23 minut", przycisk „Wygeneruj nowy kod".
- Pod kodem: link „Otwórz @OZEAgentBot w Telegramie (jeśli masz go na tym komputerze)" (deep link `tg://`).
- **Live status na dole:** „⏳ Czekam na Twoje sparowanie…" → po sparowaniu zmienia się na: „✅ Połączono z Markiem (Telegram)" + automatyczne przejście do dashboardu po 2 sek.
- Pod stepperem: pomocnicza sekcja „Coś nie działa?" z linkami do FAQ + przycisk „Zadzwoń do supportu" (opcjonalnie, tylko jeśli mamy support).

#### Po onboardingu — pierwszy widok dashboardu

- Pełnoekranowy banner powitalny (bez „Witaj!"):

> 🫡 Konto gotowe.
>
> Twój pierwszy klient: powiedz agentowi w Telegramie głosówką lub tekstem. Agent zapisze go w arkuszu i pojawi się tutaj.
>
> [Otwórz instrukcję] [Zaczynam, zamknij]

---

### 6.3. `/dashboard` — Centrum dowodzenia (po zalogowaniu)

To jest **ekran, który handlowiec widzi najczęściej**. Otwiera laptopa rano albo wieczorem i tu ląduje.

**Layout: grid 12 kolumn, 3–4 wiersze.**

#### Górny pas (full width)

- **Powitanie tylko z imieniem + datą:** „Marek · Sobota, 25 kwietnia 2026" (drobny, nienachalny).
- **4 KPI cards w rzędzie** (każda zajmuje 3 kolumny z 12), bardzo czytelne liczby:
  - **Spotkania dziś** — duża liczba (np. „4"), drobno: „2 osobiste · 2 telefony" + kierunek vs wczoraj („+1").
  - **Nowi klienci ten tydzień** — duża liczba, sparkline ostatnie 7 dni.
  - **Oferty wysłane** — liczba, drobno: „czeka na decyzję: 6".
  - **Podpisane w tym miesiącu** — liczba + zielony pasek progresu (cel miesięczny, edytowalny w Ustawieniach).

#### Środkowy pas — Lejek sprzedaży (8 kolumn) + Aktywność (4 kolumny)

**Lejek sprzedaży (8 kolumn)** — wizualizacja 9 statusów jako lejek poziomy lub kolumny słupkowe:

```
Nowy lead         ████████████ 23
Spotkanie umówione  ███████ 14
Spotkanie odbyte    █████ 10
Oferta wysłana      ██████ 12
Podpisane           ████ 8
Zamontowana         ███ 6
Rezygnacja z umowy  ██ 3
Nieaktywny          █ 2
Odrzucone           █ 4
```

- Każdy słupek klikalny → przekierowanie do `/klienci?status=Nowy+lead`.
- Pod lejkiem mała linia: „Konwersja Nowy lead → Podpisany: 18% (ostatnie 30 dni)" — w stonowanym kolorze.

**Aktywność (4 kolumny)** — wykres słupkowy ostatnie 14 dni, każdy słupek = liczba interakcji z agentem (dodane klienty, dodane spotkania, zmienione statusy). Hover = szczegóły. Pod wykresem przełącznik: 7 dni / 14 dni / 30 dni.

#### Dolny pas — Plan dnia (6 kolumn) + Top klienci do działania (6 kolumn)

**Plan dnia (6 kolumn)**

- Header: „📅 Dziś — Sobota, 25 kwietnia 2026" + mały selektor („Wczoraj | **Dziś** | Jutro | Tydzień").
- Lista wydarzeń chronologicznie:

```
09:00  📞 Jan Kowalski (Warszawa) — telefon
10:30  🤝 Piotr Nowak (Piaseczno) — spotkanie
       Kościuszki 15, Piaseczno · Status: Oferta wysłana
14:00  🤝 Adam Mazur (Radom) — spotkanie
       Słowackiego 3, Radom · Status: Oferta wysłana
16:00  📨 Michał Wiśniewski (Legionowo) — wysłać ofertę
```

- Każda pozycja klikalna → karta klienta na boku.
- Pod listą podsumowanie zaległości:

```
⚠️ 3 zaległe follow-upy:
• Tomasz Lis — telefon (4 dni temu)
• Anna Zub — wysłać ofertę (6 dni temu)
• Krzysztof Bury — przypomnieć się (2 dni temu)
```

- Brak spotkań → tylko podsumowanie zaległości lub komunikat „Dziś bez spotkań."

**Top klienci do działania (6 kolumn)**

- Header: „🫵 Wymagają uwagi" + mały dropdown „Top 10".
- Lista 5–10 klientów posortowana wg „pilności":
  - Oferta wysłana >7 dni temu bez odpowiedzi (czerwony badge).
  - Spotkanie odbyte bez next stepu (bursztyn badge).
  - Klient bez aktywności >30 dni w statusie aktywnym (szary badge).
- Każdy wiersz: imię nazwisko, miasto, status, „od X dni", przycisk inline „📞 Zadzwoń" (opens `tel:`) i „📨 Mail" (opens `mailto:`).
- Klik w wiersz → karta klienta z prawej.
- Pod listą link „Zobacz wszystkich →" (do `/klienci?filter=requires-action`).

---

### 6.4. `/klienci` — Lista klientów

- **Tabela** z filtrami u góry: status (multi-select), miasto (multi-select), produkt, źródło, zakres dat (pierwszy / ostatni kontakt).
- Pole wyszukiwania (pełnotekstowe — imię, nazwisko, miasto, telefon, email).
- Kolumny tabeli (resizowalne, ukrywalne): Imię i nazwisko, Miasto, Produkt, Status (pill z kolorem), Tel., Ostatni kontakt, Następny krok.
- Sort po każdej kolumnie.
- Klik w wiersz → **karta klienta wjeżdża z prawej strony** (panel side, 50% szerokości).
- Karta klienta pokazuje **wszystkie 16 kolumn z Sheets** (poza technicznymi: ID wydarzenia), w sekcjach: Dane podstawowe, Adres, Status i lejek, Notatki (full text, append-only, z datami w nawiasach), Zdjęcia (miniatury z Drive), Historia spotkań (z Calendar).
- W karcie 3 akcje (przyciski u góry): „📊 Otwórz w Sheets" (deep link do konkretnego wiersza), „📅 Pokaż w kalendarzu" (filtr Calendar po kliencie), „📁 Folder zdjęć" (deep link do folderu Drive).
- **Karta jest read-only.** Edycja danych klienta dzieje się przez agenta w Telegramie (R5 z behavior spec — `edit_client` to POST-MVP). Banner u góry karty: „💡 Żeby zmienić dane klienta — napisz do agenta w Telegramie."
- Selekcja wierszy → bulk actions (np. „Eksportuj zaznaczonych do CSV").

---

### 6.5. `/kalendarz` — Widok kalendarza

- **3 widoki przełączane:** Dzień / Tydzień / Miesiąc (Tydzień domyślny).
- Bezpośrednie połączenie z Google Calendar usera (przez nasze API, nie iframe — styl ma być spójny z dark theme).
- Wydarzenia kolorowane wg typu:
  - 🤝 spotkania osobiste — zielony,
  - 📞 telefony — niebieski,
  - 📨 wysłać ofertę — żółty,
  - 📄 follow-up dokumentowy — fioletowy.
- Klik w wydarzenie → popup z danymi klienta (imię, miasto, adres, telefon, status, notatki) + 3 akcje („Karta klienta", „Otwórz w Google Calendar", „Nawiguj" dla in_person — deep link do Google Maps).
- Sidebar po prawej: **Lista zaległych follow-upów** (z datą zaległości, czerwony pasek z liczbą dni).
- **Brak akcji „dodaj spotkanie" w UI** — wszystko przez agenta w Telegramie. Banner na dole: „💡 Żeby dodać spotkanie — napisz do agenta w Telegramie."

---

### 6.6. `/statystyki` — Statystyki w czasie

Dashboard analityczny.

- **Wybór zakresu czasu:** ten tydzień / miesiąc / kwartał / rok / własny.
- **3 wykresy główne:**
  - **Lejek w czasie** (stacked area chart, 9 statusów, miesiąc po miesiącu) — pokazuje jak rośnie/spada baza w każdym statusie.
  - **Aktywność dzienna** (bar chart, dni × kategorie: nowi klienci, spotkania, telefony, podpisane).
  - **Konwersja per etap** (sankey lub funnel chart, % przechodzących z etapu do etapu).
- **3 KPI cards na górze:**
  - Średni czas Nowy lead → Podpisany,
  - Średni cykl sprzedaży (dni),
  - % konwersji ogólny (Nowy lead → Zamontowana).
- **Tabela źródeł leadów:** ile podpisanych z Facebooka / polecenia / strony www, % konwersji per źródło.

---

### 6.7. `/import` — Import klientów z CSV/Excel (POST-MVP — placeholder)

> **Uwaga:** import CSV jest POST-MVP w roadmapie produktowej. W pierwszej iteracji web appa **zrób tę stronę jako „coming soon"** — pojedynczy ekran z opisem funkcji + emailem zapisu na powiadomienie, gdy będzie gotowa. Pełny wizard poniżej zostawiony jako specyfikacja na drugą iterację.

**Coming soon screen (pierwsza iteracja):**
- Headline: „Import klientów z pliku — wkrótce"
- Paragraph: „Będziesz mógł wgrać CSV lub Excel z istniejącą bazą leadów (Facebook, stara baza, eksport z innego CRM) i jednym kliknięciem dodać wszystkich klientów."
- Pole email: „Daj znać kiedy będzie gotowe" + przycisk „Powiadom mnie".

**Specyfikacja na później (druga iteracja, gdy POST-MVP się otworzy):**

Prosty 3-step wizard:

1. **Upload pliku** (drag-and-drop CSV / XLSX, max 10 MB).
2. **Mapowanie kolumn** — tabela: kolumna z pliku → kolumna w arkuszu OZE (dropdown). Auto-detekcja prostych nazw („imie", „telefon"). Podgląd 5 wierszy.
3. **Podsumowanie:** „Importuję 47 klientów. 3 mają duplikaty z istniejącymi (pokaż listę). Co zrobić: pominąć / nadpisać / dodać jako nowych."
4. CTA: „Importuj" → progress bar → „✅ Zaimportowano 47 klientów."

---

### 6.8. `/instrukcja` — Interaktywna instrukcja „Poznaj swojego agenta"

**To ma być solidna, interaktywna instrukcja**, nie suchy tekst. Cel: handlowiec w 10 minut wie, jak używać agenta.

- **Lewy sidebar:** spis treści (sticky), 8 sekcji:
  1. Czym jest OZE-Agent (1 min)
  2. Jak rozmawiasz z agentem — głos, tekst, zdjęcia (2 min)
  3. Dodawanie klientów (2 min)
  4. Wyszukiwanie i karty klientów (1 min)
  5. Spotkania i kalendarz (2 min)
  6. Zmiana statusu i lejek (1 min)
  7. Poranny brief i follow-upy wieczorne (1 min)
  8. Co robi agent sam, czego nie robi (1 min)
- **Każda sekcja:**
  - Krótki paragraf (max 5 linii prozą).
  - **Interaktywny mockup Telegrama** po prawej — symulacja prawdziwej rozmowy: handlowiec pisze (auto-typed), karta agenta się pojawia, klika ✅ Zapisać, widzi commit. Animacja pętli po 5 sek przerwy. User może kliknąć „Powtórz" lub „Następna sekcja →".
  - Pod mockupem: 2–3 bullet pointy z **najczęstszymi błędami** („Nie pisz tylko nazwiska — agent nie wie którego Kowalskiego masz na myśli. Dodaj miasto.").
- **Na końcu każdej sekcji:** mały quiz (1 pytanie, 3 odpowiedzi) — tylko dla utrwalenia, bez gamifikacji.
- **Footer instrukcji:** „Masz pytanie nieobjęte tym? → Idź do FAQ" + „Coś jest niejasne? → [napisz do nas]".

---

### 6.9. `/faq` — FAQ

- **Akordeon** zgrupowany w 4 sekcje:
  1. **Konto i płatność** (jak zmienić plan, jak wystawić fakturę, jak usunąć konto)
  2. **Konto Google i Twoje dane** (gdzie są moje dane, jak otworzyć arkusz/kalendarz ręcznie, jak odebrać dostęp Google jeśli rezygnuję)
  3. **Korzystanie z agenta** (czemu nie rozumie nazwiska, czemu zapisał na zły dzień, jak edytować zapisanego klienta)
  4. **Problemy techniczne** (Telegram nie odpowiada, kalendarz się nie synchronizuje, agent się gubi)
- Każde pytanie rozwija się w odpowiedź (krótka, konkretna, max 5 linii). Linki do innych sekcji jeśli relevant.
- Pole wyszukiwania na górze (filtruje pytania na żywo).
- Pod FAQ: „Nie znalazłeś odpowiedzi? → [Napisz do supportu]".

---

### 6.10. `/platnosci` — Płatności i subskrypcja

- **Status subskrypcji** (top, bardzo widoczny):
  - Aktywna do: 25 kwietnia 2027 (lub: „Wygasa za 12 dni — odnów").
  - Plan: Roczny (350 zł/rok).
  - Następna płatność: 25 kwietnia 2027.
  - Przyciski: „Zmień plan", „Anuluj subskrypcję" (z confirmation modalem).
- **Historia płatności** (tabela): data, kwota, plan, status (opłacona/zwrot), faktura (link „Pobierz PDF").
- **Metoda płatności:** widoczne ostatnie 4 cyfry karty / logo BLIK + przycisk „Zmień metodę płatności".
- **Faktura ustawienia:** dane do faktury (NIP, nazwa firmy, adres) — edytowalne.
- **Banner** jeśli subskrypcja kończy się <14 dni: czerwone tło + „Subskrypcja kończy się za X dni. Po tym agent przestanie działać." + CTA „Odnów teraz".

---

### 6.11. `/ustawienia` — Ustawienia

Tabbed layout, 6 sekcji:

1. **Profil** — imię, nazwisko, email, telefon, hasło (zmiana), avatar.
2. **Agent — preferencje** — godzina morning briefu (domyślnie 07:00), dni wysyłki briefu (Pon–Pt domyślnie, edytowalne), domyślna długość spotkania (60 min), włącz/wyłącz follow-up wieczorny.
3. **Arkusz — kolumny** — lista 16 kolumn, możliwość dodania własnych (POST-MVP, na razie disabled z notką „Wkrótce").
4. **Arkusz — statusy lejka** — lista 9 statusów, drag-and-drop kolejność (POST-MVP, disabled).
5. **Integracje Google** — status połączenia Sheets/Calendar/Drive, przycisk „Odnów autoryzację", przycisk „Rozłącz" (z mocnym warningiem).
6. **Telegram** — status sparowania, przycisk „Wygeneruj nowy kod parowania" (np. po zmianie telefonu), przycisk „Rozparuj".

---

### 6.12. `/login` — Logowanie

- Prosty formularz: email + hasło.
- Przycisk „Zaloguj przez Google" (alternatywa).
- Link „Nie pamiętasz hasła?" → reset przez email.
- Link „Nie masz konta? Załóż" → `/rejestracja`.

---

## 7. Komponenty wielokrotnego użytku (zaprojektuj od razu, używane w wielu miejscach)

- **StatusPill** — pill z 9 kolorami (po 1 dla każdego statusu lejka). Spójna kolorystyka: Nowy lead = niebieski, Spotkanie umówione = jasno-zielony, Spotkanie odbyte = zielony, Oferta wysłana = żółty, Podpisane = ciemnozielony, Zamontowana = oliwkowy, Rezygnacja = czerwony, Nieaktywny = szary, Odrzucone = ciemnoszary.
- **EventTypeIcon** — emoji + kolor dla 4 typów wydarzeń: 🤝 in_person (zielony), 📞 phone_call (niebieski), 📨 offer_email (żółty), 📄 doc_followup (fioletowy).
- **DateBadge** — format `25.04.2026 (Sobota)`. **Nigdy** ISO, nigdy serial number.
- **ClientCard** (side panel z prawej) — używana w `/klienci`, `/dashboard` (top klienci), `/kalendarz`.
- **EmptyState** — przyjazne komunikaty bez korpomowy: „Nie masz jeszcze klientów. Powiedz agentowi w Telegramie o pierwszym." + ikona, bez „Add client" CTA (bo dodawanie tylko przez agenta).
- **WarningBanner** — bursztyn dla zaległości, czerwony dla subskrypcji, niebieski dla informacji.
- **FloatingActionButtons** (Sheets/Calendar/Drive) — opisane w §5.

---

## 8. Zachowania i zasady, których ABSOLUTNIE musisz przestrzegać

1. **Web app NIE jest interfejsem do mutacji danych klientów.** Dodawanie, edycja, dodawanie spotkań, zmiana statusu — wszystko przez agenta w Telegramie. Web app tylko **wyświetla** i **konfiguruje**. Wyjątek: import CSV (`/import`) i operacje na koncie usera (płatności, ustawienia).
2. **Dane klientów żyją na Google koncie usera** (Sheets, Calendar, Drive). Web app **odczytuje** je przez backend, ale nie traktuje jako własnego źródła prawdy. Nie buduj UI sugerującego, że klient jest „w naszej bazie" — wszędzie pokazuj „📊 Otwórz w Sheets" jako akcję dotykową.
3. **Daty zawsze w formacie `DD.MM.YYYY (Dzień tygodnia)`**. Nigdy ISO, serial, „2026-04-25". Nigdy „2 days ago" — zamiast tego „25.04.2026 (Sobota)".
4. **Klient zawsze identyfikowany pełnym `imię + nazwisko + miasto`**. Nigdy samo nazwisko (zbyt wiele Kowalskich).
5. **Brak technicznych wartości w UI** — żadnych ID rekordów, numerów wierszy w Sheets, surowych floatów. Wszystko w „ludzkim" formacie.
6. **Brak motywacyjnych komentarzy nigdzie.** „Świetnie!", „Brawo, podpisałeś 5 umów!" — zabronione.
7. **Pop-upy w prawym dolnym rogu (Sheets/Calendar/Drive) muszą być na każdym ekranie** po zalogowaniu, łącznie z dashboardem, listą klientów, kalendarzem, statystykami, ustawieniami.
8. **Onboarding nie może mieć rezygnacji w środku** — do końca pełnego setupu (krok 5 sparowane Telegram) flow jest wymuszony. User może wyjść tylko przez „Wyloguj" (z confirmation).

---

## 9. Czego NIE budujemy (nie dodawaj tego nawet jako placeholderów)

- Czat z agentem w web appie — agent żyje tylko w Telegramie.
- Kanban board statusów (drag-and-drop klient między statusami) — POST-MVP.
- Gamifikacja, achievementy, leaderboardy — nigdy.
- Powiadomienia push w przeglądarce — agent wysyła wszystko przez Telegram.
- Funkcje społecznościowe (zespoły, dzielenie się klientami) — to jest single-user app w MVP.
- Edycja klientów w UI — przez agenta tylko.
- Drag-and-drop dodawanie spotkań w kalendarzu — przez agenta.

---

## 9b. Notka strategiczna — web app może wyprzedzać agenta

Niektóre funkcje w tym briefie (statystyki lejka, top klienci do działania, sortowanie po pilności) są w roadmapie agenta oznaczone jako POST-MVP — agent w Telegramie ich jeszcze nie umie. **To w porządku w web appie**: web app czyta dane bezpośrednio z Google Sheets i Calendar, więc może wystawiać widoki, które wymagają agregacji danych — agent w Telegramie skupia się na konwersacyjnych mutacjach (dodać klienta, zmienić status, dodać spotkanie).

Nie traktuj tego jako sprzeczność. Web app i agent to dwa kanały tego samego produktu, z różnymi mocnymi stronami: Telegram = szybkie wpisy w terenie, web = przeglądy i planowanie przy biurku.

---

## 10. Co dostarcz w pierwszej iteracji

1. **Landing publiczny** (`/`) — pełna strona z hero, sekcjami, demo, cennikiem, FAQ, stopką. Sticky CTA bar.
2. **Dashboard** (`/dashboard`) — pełny układ z 4 KPI, lejkiem, aktywnością, planem dnia, top klientami. Z floating action buttons.
3. **Onboarding wizard** (`/rejestracja`) — wszystkie 5 kroków z transitions i loading states (zwłaszcza animowany checklist w kroku 4 i live status sparowania w kroku 5).
4. **Lista klientów** (`/klienci`) — tabela + filtry + side-panel karta klienta.
5. **Kalendarz** (`/kalendarz`) — widok tygodnia + side-panel popup wydarzenia.
6. **Płatności** (`/platnosci`) — status + historia + zarządzanie planem.

Pozostałe (statystyki, import, instrukcja, FAQ, ustawienia, login) — w drugiej iteracji.

---

## 11. Format outputu, którego oczekujemy od Ciebie (claude.design)

- Komponenty React + Tailwind CSS + shadcn/ui (lub równoważne dark-theme components).
- TypeScript.
- Realistyczne, polskie dane mockowe — Polskie imiona (Marek Kowalski, Anna Lis, Krzysztof Bury), polskie miasta (Warszawa, Piaseczno, Legionowo, Radom, Wyszków), polskie statusy zgodne z listą 9 statusów.
- Każdy ekran w osobnym pliku/route.
- Estetyka: dark, gęsta informacyjnie, profesjonalna — patrz §4.
- Język UI: **wyłącznie polski**, wg tonu z §3.

Powodzenia.
