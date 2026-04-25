# Poznaj swojego agenta

> **Status dokumentu.** Ten dokument opisuje wizję produktu z perspektywy handlowca. Aktualny zakres MVP i kontrakty intencji są w `docs/INTENCJE_MVP.md`. Aktualny stan implementacji jest w `docs/CURRENT_STATUS.md`. Część funkcji opisanych tutaj jest POST-MVP i pojawi się w kolejnych rundach.

## Czym jest OZE-Agent?

OZE-Agent to Twój osobisty asystent sprzedażowy, który żyje w aplikacji Telegram na Twoim telefonie. Rozmawiasz z nim tak, jak rozmawiasz ze znajomym — po polsku, swoimi słowami, bez żadnych specjalnych komend ani skomplikowanych formularzy.

Agent jest połączony z Twoim kontem Google. To znaczy, że kiedy powiesz mu o nowym kliencie, sam zapisze dane w Twoim arkuszu Google Sheets. Kiedy umówisz spotkanie, sam doda je do Twojego kalendarza Google. Kiedy wyślesz zdjęcie dachu klienta, sam zapisze je na Twoim Dysku Google i podepnie do tego klienta.

Ty mówisz — on robi. Żadnego wpisywania w tabelki, żadnego przeklikiwania się przez menu.

---

## Jak się z nim komunikować?

Masz trzy sposoby — używaj tego, który jest wygodniejszy w danym momencie:

### 🎙️ Głosówki (najszybszy sposób)

Jedziesz autem po spotkaniu? Przytrzymaj przycisk mikrofonu w Telegramie i po prostu powiedz co się wydarzyło. Mów naturalnie, tak jak opowiadałbyś koledze. Im więcej powiesz za jednym razem, tym lepiej — agent przetworzy wszystko naraz:

*"Byłem właśnie u Kowalskiego na Piłsudskiego 12 w Warszawie. Dom ma 160 metrów, dach skierowany na południe, około 40 metrów dachu. Zainteresowany fotowoltaiką, myśli o instalacji 8 kilowatów. Chce wycenę do środy. Numer telefonu 600 123 456."*

Po nagraniu agent pokaże Ci transkrypcję — to co usłyszał. Jeśli coś źle zrozumiał (np. przekręcił nazwisko), możesz poprawić tekstem albo nagrać ponownie. Dopiero po Twoim potwierdzeniu agent przetworzy dane.

Agent wyciągnie z tego wszystkie dane, pokaże co zrozumiał i na końcu wymieni wszystkie brakujące pola — wszystkie naraz, nie po jednym. Jeśli masz brakujące dane, uzupełniasz jedną wiadomością. Jeśli nie masz — mówisz "zapisz tak jak jest" i uzupełnisz później.

Nie musisz mówić w żadnym specjalnym formacie. Mów tak jak mówisz na co dzień. Agent zrozumie.

### ✍️ Pisanie (gdy jest ciszej)

Siedzisz w poczekalni? Wpisujesz wiadomość tak jak SMS:

*"Nowy klient Nowak, Leśna 5, Piaseczno, zainteresowany pompą ciepła, dom 120m2, tel 601234567"*

Im więcej informacji podasz w jednej wiadomości, tym szybciej agent zapisze klienta — i tym mniej zużyjesz swoich interakcji. Jedna rozbudowana wiadomość jest lepsza niż pięć krótkich.

### 📸 Zdjęcia (dokumentacja wizualna)

Zrobiłeś zdjęcie dachu klienta? Licznika prądu? Tabliczki z adresem? Wyślij je do agenta w Telegramie. Agent zapyta do którego klienta przypisać zdjęcie — powiesz imię i miejscowość, a on sam zapisze zdjęcie w folderze tego klienta na Twoim Dysku Google.

Możesz wysłać kilka zdjęć pod rząd — agent podepnie je wszystkie do tego samego klienta.

---

## Co agent potrafi?

### 👥 Zarządzanie klientami

Agent prowadzi Twoją bazę klientów w arkuszu Google Sheets. Ale Ty nigdy nie musisz otwierać tego arkusza ręcznie — agent robi to za Ciebie.

**Dodawanie klientów** — powiedz agentowi o nowym kliencie głosówką lub tekstem. Podaj jak najwięcej informacji naraz. Agent wyciągnie wszystkie dane, pokaże co zrozumiał, a na końcu wymieni wszystkie brakujące pola:

*Ty: "Byłem u Kowalskiego, Piłsudskiego 12 Warszawa, dom 160 metrów, dach południe 40 metrów, PV 8kW, telefon 600 123 456, chce wycenę do środy"*

*Agent: "📋 Zapisuję klienta:*
*Jan Kowalski, Piłsudskiego 12, Warszawa*
*Produkt: PV*
*Tel. 600 123 456*
*Notatki: moc PV 8kW, dom 160m², dach 40m² płd., chce wycenę do środy*
*❓ Brakuje: źródło leada*

*[✅ Zapisać]  [➕ Dopisać]  [❌ Anulować]"*

*Ty: klikasz ✅ Zapisać albo piszesz "tak"*

*Agent: "✅ Zapisane."*

Dwie wiadomości — klient w arkuszu.

**Wyszukiwanie klientów** — chcesz sprawdzić dane klienta? Wystarczy powiedzieć:
- *"Co mam o Mariuszu Kowalskim?"*
- *"Pokaż dane Karola Nowaka"*
- *"Jan Kowalski z Warszawy"*

Agent przeszuka arkusz i pokaże kartę klienta ze wszystkimi danymi. Jeśli znajdzie kilku klientów o podobnym nazwisku, pokaże listę i zapyta którego masz na myśli. Nawet jeśli zrobisz literówkę (np. "Kowalsky" zamiast "Kowalski"), agent domyśli się o kogo chodzi.

Jeśli masz dużo klientów (50+), agent zamiast długiej listy wyśle Ci link do Twojego arkusza Google Sheets.

**Edycja danych** — chcesz coś zmienić? Powiedz co i u kogo:
- *"Zmień telefon Kowalskiego na 601 234 567"*
- *"Dodaj notatkę do Nowaka: interesuje się też magazynem energii"*
- *"Kowalski ma 45 metrów dachu, nie 40"*

Gdy zmieniasz np. numer telefonu, agent zapyta: "Zostawić stary numer i dodać drugi, czy usunąć stary?" — żebyś nie stracił danych przypadkiem.

Agent pokaże co zmieni i poczeka na Twoje potwierdzenie.

**Zmiana statusu klienta** — Twoi klienci przechodzą przez etapy sprzedaży (nowy lead → spotkanie → oferta → podpisane). Żeby przesunąć klienta dalej, wystarczy powiedzieć:
- *"Marek Kowalski — wysłałem ofertę"*
- *"Krzystof Nowak podpisał umowę!"*
- *"Cezary Wiśniewski zrezygnował"*

Agent zaproponuje zmianę statusu i poczeka na Twoje potwierdzenie.

**Usuwanie klientów** — jeśli chcesz usunąć klienta z bazy, powiedz np. *"Usuń z bazy Krzysztofa Nowaka z Piaseczna"*. Agent zawsze pyta o potwierdzenie, bo tej operacji nie da się cofnąć.

### 📅 Kalendarz i spotkania

Agent zarządza Twoim dedykowanym kalendarzem Google. To osobny kalendarz tylko dla spotkań OZE — nie miesza się z Twoimi prywatnymi wydarzeniami. Możesz dodawać, przeglądać, przenosić i odwoływać spotkania — wszystko głosem lub tekstem.

**Dodawanie spotkań** — mów naturalnie:
- *"Jutro o 10 jadę do Marka Kowalskiego"*
- *"Umów spotkanie z Zbyszkiem Nowakiem w piątek o czternastej"*
- *"W środę o szesnastej wycena u Czarka Wiśniewskiego w Legionowie"*

Możesz dodać kilka spotkań w jednej wiadomości:
*"Jutro o 10 Wojtek Kowalski, o 14 Marek Nowak, o 17 Jarek Wiśniewski"*
Agent stworzy trzy wydarzenia naraz, a potem zapyta czy dodać tych klientów do bazy (tych, którzy jeszcze nie są w arkuszu).

Jeśli w danym terminie masz już inne spotkanie — agent ostrzeże o konflikcie, ale pozwoli dodać jeśli potwierdzisz.

Domyślna długość spotkania to 60 minut (możesz zmienić w ustawieniach). Z czasem agent nauczy się Twoich nawyków — jeśli większość Twoich spotkań trwa 45 minut, zacznie proponować 45 minut jako domyślne.

Każde spotkanie ma adres klienta — agent zapisuje go zarówno w kalendarzu jak i w arkuszu. Dzięki temu widzisz adres bezpośrednio w aplikacji Kalendarz Google na telefonie.

**Przeglądanie planu** — zapytaj:
- *"Co mam dziś?"*
- *"Pokaż jutrzejszy plan"*
- *"Co mam w tym tygodniu?"*
- *"Jakie mam wolne okna w czwartek?"*

**Przenoszenie spotkań** — jeśli klient odwołał:
- *"Przełóż Artura Kowalskiego na piątek o 10"*
- *"Przesuń jutrzejsze spotkanie z Wojciechem Nowakiem na przyszły wtorek"*

Agent pokaże dane klienta, stary termin i nowy termin — poczeka na potwierdzenie, a potem sam zmieni kalendarz i datę w arkuszu.

**Odwoływanie spotkań:**
- *"Odwołaj spotkanie z Andrzejem Kowalskim"*
- *"Usuń jutrzejsze spotkanie o 14"*

Do przeglądania i usuwania spotkań możesz też używać natywnej aplikacji Kalendarz Google na telefonie — zmiany będą widoczne od razu. Przypomnienia przed spotkaniem obsługuje natywnie Google Calendar według ustawień Twojej aplikacji kalendarza.

### 🤖 Co agent robi sam, bez Twojego pytania

Są dwie rzeczy, które agent robi automatycznie:

**☀️ Poranny brief** — codziennie rano w Twoje dni robocze (które ustawiasz w ustawieniach — domyślnie poniedziałek-piątek, godzina 7:00) dostajesz wiadomość z planem dnia: wszystkie spotkania z danymi klientów i adresami, wolne okna czasowe oraz zaległe follow-upy.

**📋 Follow-up po spotkaniach** — po Twoim ostatnim spotkaniu dnia agent sam się odezwie i zapyta jak poszły spotkania, o których jeszcze mu nie powiedziałeś. Wylistuje nieraportowane spotkania i poczeka na Twoją odpowiedź. Możesz odpowiedzieć jedną głosówką, opisując wszystkie spotkania naraz:

*"Z Kowalskim super, chce wycenę na 8kW, wyślę jutro. Nowak nie był w domu, trzeba przełożyć na przyszły tydzień. U Wiśniewskiego złożyłem ofertę, czekam na odpowiedź."*

Agent na podstawie tego zaktualizuje statusy (po Twoim potwierdzeniu), ustawi przypomnienia i zaproponuje nowe terminy tam, gdzie potrzeba.

---

## Twoje dane — gdzie są i kto ma do nich dostęp

Wszystkie Twoje dane klientów są na TWOIM koncie Google:

- **📊 Arkusz klientów** — w Twoich Arkuszach Google. Możesz go otworzyć w przeglądarce i zobaczyć lub edytować dane ręcznie w dowolnym momencie.
- **📅 Kalendarz spotkań** — osobny kalendarz w Twoim Kalendarzu Google. Widoczny w aplikacji Kalendarz na telefonie i komputerze, obok Twoich prywatnych wydarzeń ale w osobnej warstwie.
- **📸 Zdjęcia klientów** — na Twoim Dysku Google, w osobnym folderze dla każdego klienta.

Nikt inny — ani my, ani inni użytkownicy — nie widzi Twoich danych. Jeśli zrezygnujesz z OZE-Agent, Twoje dane zostają u Ciebie na koncie Google. Nic nie kasujemy.

💡 Zalecamy założenie oddzielnego konta Google dedykowanego do OZE-Agent. Dzięki temu masz osobne 15 GB miejsca na dane klientów i nie mieszasz ich ze swoimi prywatnymi plikami.

---

## Jak agent rozumie daty i godziny

Agent rozumie polskie sposoby podawania czasu:

- *"dziś"*, *"jutro"*, *"pojutrze"*
- *"w piątek"*, *"we wtorek"*, *"w przyszłą środę"*
- *"o czternastej"*, *"o dwudziestej drugiej"*, *"o ósmej"*
- *"o 14"*, *"o 14:30"*, *"na 16"*
- *"za godzinę"*, *"za dwie godziny"*
- *"12 maja"*, *"15.04.2026"*

---

## Arkusz klientów — co jest w środku

Przy rejestracji agent zaproponuje domyślne kolumny dostosowane do branży OZE:

Imię i nazwisko, Telefon, Email, Miasto, Adres, Status, Produkt, Notatki, Data pierwszego kontaktu, Data ostatniego kontaktu, Następny krok, Data następnego kroku, Źródło pozyskania, Zdjęcia, Link do zdjęć, ID wydarzenia Kalendarz.

**Gdzie trafiają szczegóły techniczne?** Metraż domu, metraż dachu, kierunek dachu, zużycie prądu, typ dachu i wszelkie inne dane techniczne lądują w kolumnie **Notatki** — jako tekst, w jednej kolumnie, wyszukiwalne. Agent celowo nie tworzy osobnych kolumn dla każdego parametru, bo każdy handlowiec ma trochę inne potrzeby. Jeśli potrzebujesz wyciągnąć wszystkich klientów z dachem 40m² — wyszukasz w Notatkach.

**Moc produktu** (np. 8kW, 12kW, 10kWh) trafia do kolumny **Notatki** razem z resztą specs technicznych — tak samo jak metraż domu, dachu czy kierunek. Kolumna **Produkt** zawiera tylko typ produktu (PV, Pompa ciepła, Magazyn energii, PV + Magazyn), bez wartości liczbowych. Nie ma osobnej kolumny "moc".

W aktualnej wersji schemat arkusza jest stały — 16 kolumn powyżej. W przyszłości będziesz mógł dodawać i zmieniać kolumny z poziomu dashboardu; agent odczyta nowe nagłówki i zacznie pytać o nowe pola przy kolejnych klientach.

Niektóre kolumny są fundamentami bazy klientów i pozostają zawsze: Imię i nazwisko, Telefon, Miasto, Adres, Produkt, Status, Notatki. Bez nich agent nie mógłby działać.

Domyślne statusy lejka sprzedażowego: Nowy lead → Spotkanie umówione → Spotkanie odbyte → Oferta wysłana → Podpisane → Zamontowana → Rezygnacja z umowy → Nieaktywny → Odrzucone. W przyszłości statusy będzie można edytować z dashboardu.

---

## Adresy i miejscowości

Agent zawsze zapisuje adres klienta w dwóch miejscach: w arkuszu Google Sheets i w wydarzeniu w kalendarzu (w polu "lokalizacja"). Dzięki temu widzisz adres klienta bezpośrednio w aplikacji Kalendarz na telefonie — np. możesz kliknąć i otworzyć nawigację.

---

## Przyciski w Telegramie

Przy każdej zmianie danych (dodanie klienta, notatka, zmiana statusu, dodanie spotkania) agent pokazuje kartę z trzema przyciskami:

**[✅ Zapisać]  [➕ Dopisać]  [❌ Anulować]**

- **✅ Zapisać** — zapisuje i zamyka
- **➕ Dopisać** — pozwala dopisać coś przed zapisem
- **❌ Anulować** — anuluje jednym kliknięciem, bez pytania "na pewno?"

Zamiast klikać możesz też odpowiedzieć tekstem ("tak", "zapisz", "anuluj") lub głosówką.

Przy prostych pytaniach nie-mutacyjnych (np. *"Czy chodziło Ci o Jana Kowalskiego z Warszawy?"*) agent pokazuje zwykłe **[Tak]** / **[Nie]**.

---

## Potwierdzenia

Agent nigdy nie zapisuje ważnych zmian bez Twojego OK. Dodanie klienta, notatki, zmiana statusu, dodanie spotkania — każda taka akcja najpierw pokazuje kartę 3-button i czeka.

Dopóki nie klikniesz **✅ Zapisać** (lub nie odpowiesz tekstem "tak" / "zapisz") — nic się nie zapisuje.

**❌ Anulować** zamyka operację od razu, bez pętli "Na pewno anulować?".


## Gdy klient już jest w bazie

Jeśli dodajesz klienta, którego agent rozpozna po imieniu, nazwisku i miejscowości, zapyta:

*Ten klient już jest w arkuszu: Jan Kowalski, Warszawa. Czy zapisać go w nowym wierszu czy zaktualizować?*

**[Nowy]  [Aktualizuj]**

- **[Nowy]** tworzy osobny wiersz w arkuszu (np. dwóch różnych Janów Kowalskich).
- **[Aktualizuj]** prowadzi do karty zapisu dla istniejącego klienta.

Bez tej decyzji agent sam nie łączy klientów i nic nie zapisuje.


## Pamięć rozmowy

Agent pamięta ostatnie 10 wiadomości (lub do 30 minut przerwy). Możesz prowadzić naturalną rozmowę bez powtarzania o kim mówisz:

*Ty: "Dodaj Kowalskiego z Warszawy, Piłsudskiego 12, PV 8kW, tel 600123456"*

*Agent pokazuje kartę:*
*"📋 Zapisuję: Jan Kowalski, Warszawa, PV. Brakuje: email, źródło pozyskania.*
*[✅ Zapisać]  [➕ Dopisać]  [❌ Anulować]"*

*Ty: "dopisz że dom 160 metrów i dach 40 metrów na południe"*

*Agent aktualizuje kartę:*
*"📋 Jan Kowalski, Warszawa, PV. Notatki: moc PV 8kW, dom 160m², dach 40m² płd. Brakuje: email, źródło pozyskania.*
*[✅ Zapisać]  [➕ Dopisać]  [❌ Anulować]"*

*Ty: klikasz ✅ Zapisać*

*Agent: "✅ Zapisane."*

---

## Agent uczy się Twoich nawyków

Z czasem agent zapamiętuje Twoje preferencje. Na przykład: jeśli większość Twoich spotkań trwa 45 minut, agent zacznie domyślnie proponować 45 minut zamiast 60. Zawsze możesz to nadpisać mówiąc np. "spotkanie na pół godziny".

---

## Wskazówka: jak korzystać najefektywniej

Podawaj jak najwięcej informacji w jednej wiadomości lub głosówce. Agent przetworzy wszystko naraz — jedną interakcją zamiast pięciu. Im więcej powiesz za jednym razem, tym szybciej masz dane zapisane i tym mniej zużywasz swoich interakcji.

Jedna rozbudowana głosówka po spotkaniu jest lepsza niż pięć krótkich wiadomości z pojedynczymi danymi.

Docelowo może pojawić się dzienny budżet interakcji, żeby koszty AI były przewidywalne. W praktyce jedna bogata wiadomość zawsze będzie lepsza niż pięć krótkich.

---

## Import klientów z pliku

Masz już bazę klientów w Excelu albo leady z Facebooka? Nie musisz ich przepisywać ręcznie. Na dashboardzie (strona "Import klientów") możesz wgrać plik CSV lub Excel, podejrzeć dane, zmapować kolumny na swój arkusz i jednym kliknięciem dodać wszystkich klientów do bazy.

---

## Ton agenta

Agent jest konkretny i zwięzły. Nie gada, nie filozofuje, nie pisze wypracowań. Odpowiada krótko, na temat, bo wie że korzystasz z niego na telefonie między spotkaniami. Czujesz że masz asystenta, nie chatbota.
