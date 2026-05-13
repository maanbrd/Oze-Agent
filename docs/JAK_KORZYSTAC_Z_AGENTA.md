# Jak korzystać z OZE-Agenta

Krótki zestaw praktyk dla testów i codziennej pracy z botem. Celem jest pisać
tak, żeby agent dostał możliwie jednoznaczną intencję i nie musiał zgadywać.

## Spotkania fizyczne

Jeśli chodzi o spotkanie na miejscu, nie mieszaj w tej samej komendzie słów:
`przypomnij`, `follow-up`, `telefon`, `zadzwoń`. Obecnie mogą one skierować flow
w stronę telefonu zamiast spotkania fizycznego.

Lepiej:

```text
Jutro o 14 spotkanie: Mariusz Pudzianowski, Warszawa, ul. Kowaliowa 25D.
Notatka: faktura do omówienia.
```

Albo:

```text
Dodaj spotkanie z Mariuszem Pudzianowskim jutro o 14, Warszawa, ul. Kowaliowa 25D.
Notatka: faktura.
```

Ryzykownie:

```text
Dodaj spotkanie z Mariuszem Pudzianowskim jutro o 14 i przypomnij mu o fakturze.
```

## Telefony i follow-upy

Jeśli naprawdę chodzi o telefon, użyj tego wprost:

```text
Zadzwoń do Mariusza Pudzianowskiego jutro o 14 w sprawie faktury.
```

Jeśli chodzi o fizyczne spotkanie plus temat rozmowy, temat wpisuj jako
`Notatka: ...`, a nie jako `przypomnij`.

## Dane klienta

Najlepiej podawać klienta jako:

```text
Imię Nazwisko, miasto, adres
```

Przykład:

```text
Dodaj klienta: Mariusz Pudzianowski, Warszawa, ul. Kowaliowa 25D.
```

Gdy klient może mieć duplikaty, dopisz miasto. Agent nie powinien opierać się
na samym nazwisku.

## Zdjęcia

Przy pierwszym zdjęciu wpisz w opisie imię i nazwisko klienta. Miasto jest mile
widziane, ale nie powinno być konieczne, jeśli klient jest jednoznaczny.

```text
Mariusz Pudzianowski
```

Gdy trwa 15-minutowa sesja zdjęć i chcesz zmienić klienta, użyj jawnej komendy:

```text
zdjęcia do Anna Nowak Kraków
```

Zwykły opis typu `dach północny` trafi do aktualnej sesji zdjęć.

## Potwierdzenia

Klikaj przyciski tylko na najnowszej karcie aktywnego flow. Stare przyciski z
poprzednich kart mogą już nie odpowiadać aktualnemu stanowi rozmowy.

Do zapisów używaj kart:

- `✅ Zapisać`
- `➕ Dopisać`
- `❌ Anulować`

Jeśli po zapisie pojawi się kolejne pytanie o następny krok, możesz je zamknąć
przez `❌ Anuluj / nic`.

