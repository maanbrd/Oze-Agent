# Round 8 — Testy po bugfixach + rekonesans A/B/C

_Data: 10.04.2026, 20:09_
_Build: develop po `bc765a2` (Bug #1) + fix add_note intent_

---

## 1. Regression: Bug #1 po `bc765a2` — PASS

**Test:** `jutro o 15 spotkanie z Piotrem Lewandowskim z Lodzi`

Karta spotkania:
```
✅ Dodać spotkanie?
• Klient: Piotr Lewandowski
• Data: 11.04.2026 (sobota)
• Godzina: 15:00
• Czas trwania: 60 min
• Miejsce: Łódź
```

Pełne imię w karcie ✅, data PL format ✅, miasto PL ✅. 

Dodatkowo bot wykrył, że Piotr Lewandowski nie jest w Sheets i zapytał: **"Nie mam Piotr Lewandowski w bazie. Dodać?"** — nowa feature, dobra UX.

Bug #1 regression potwierdzony w meeting card **oraz** day plan ("Spotkanie z Piotr Lewandowski" w "co mam jutro?"). `_enrich_meeting` nie zepsute.

---

## 2. Option A — Enriched day plan

**Test:** `co mam jutro?`

Aktualna odpowiedź:
```
📅 Plan dnia:
📆 10:00-11:00 — Spotkanie z Jan Mazur
📍 Radom
📞 Tel: 888888888
Produkt: Wspólna 8
Następny krok: Follow-up za tydzień

📆 15:00-16:00 — Spotkanie z Piotr Lewandowski
📍 Łódź
```

### Status: **CZĘŚCIOWO zaimplementowane, nie zgadza się z Twoim opisem**

Co jest:
- Enrichment działa dla klientów W Sheets (Jan Mazur): telefon, produkt, następny krok
- Klienci spoza Sheets (Piotr Lewandowski) pokazani tylko z miejscem
- Miejsce = miasto z wydarzenia Calendar, **nie pełny adres ze Sheets**
- **Brak pola "Status"** (np. "Oferta wysłana", "Nowy lead")

Co chciałeś w Opcji A (compact, jedno-liniowy format):
```
10:00 Jan Nowak — Piłsudskiego 12, Warszawa — Oferta wysłana
14:00 Anna Kowalska — Leśna 5, Piaseczno — Nowy lead
```

### Co trzeba dorobić dla A
1. Wyciąganie **pełnego adresu** (ulica + numer + miasto) z Sheets, nie tylko miasta z Calendar.
2. Wyciąganie **statusu** klienta z kolumny Status w Sheets.
3. Refaktor formatu na **compact jedno-liniowy** (oszczędność miejsca na ekranie telefonu).
4. Fallback dla klientów spoza Sheets: "10:00 Piotr Lewandowski — Łódź — brak w bazie".

### Ocena wysiłku: ~2-3h (edycja `shared/formatting.py` + `shared/crm_sheets.py` lookup + fallback logic).

---

## 3. Option B — Wiele spotkań z jednej wiadomości

**Test:** `jutro o 9 spotkanie z Marcinem Kowalskim z Gdanska, o 12 Adam Wisniewski z Poznania, o 16 Tomasz Zielinski z Wroclawia`

Odpowiedź bota:
```
📅 Dodać 3 spotkań:
• Marcin Kowalski — 11.04 09:00, Gdańsk
• Wiśniewski — 11.04 12:00, Poznań
• Tomasz Zieliński — 11.04 16:00, Wrocław
```
[Tak] → `✅ Dodano 3 spotkań. Nie mam w bazie: Marcin Kowalski, Tomasz Zieliński. Dodać?`

### Status: **DZIAŁA (95%)**

Sukces:
- ✅ Bot rozpoznał że to 3 osobne spotkania (nie jedno)
- ✅ Sparsował imię, nazwisko, miasto, godzinę dla każdego
- ✅ Poprawnie zinterpretował przecinki jako separatory
- ✅ Pokazał batch confirmation (1x [Tak] → 3 eventy)
- ✅ **Bonus feature:** batch dodawanie klientów do Sheets (Marcin + Tomasz Zieliński)

Bug znaleziony:
- ❌ Adam Wiśniewski zgubił imię ("Wiśniewski — 11.04 12:00, Poznań" bez "Adam"). Prawdopodobnie LLM zgubił imię, bo między dwoma odmienionymi ("Marcinem Kowalskim", "Tomasza Zielińskiego") wstawiono jedno nieodmienione ("Adam Wiśniewski" w mianowniku). **Bug #8 — do backlog.**
- Drobne: format daty "11.04 09:00" bez roku (w single meeting było "11.04.2026 (sobota)"). Inconsistency.

### Co trzeba dorobić dla B
1. Fix LLM prompt — enforce first name extraction nawet jeśli w nominativum obok odmienionych form.
2. Ujednolicenie formatu daty z single meeting flow (pełna data + dzień tygodnia).

### Ocena wysiłku: ~1-2h (prompt tweak + format alignment).

---

## 4. Option C1 — Reschedule meeting

**Test:** `przełóż spotkanie z Piotrem Lewandowskim z jutra na pojutrze na 11`

Odpowiedź bota:
```
Podaj nazwę lub datę spotkania które chcesz przełożyć, oraz nowy termin.
```

### Status: **PLACEHOLDER — funkcja niezaimplementowana**

Bot rozpoznał intent `reschedule_meeting`, ale **nie sparsował parametrów** mimo że wszystkie były w wiadomości:
- Klient: "Piotr Lewandowski" ✅ w tekście
- Stary termin: "z jutra" ✅ w tekście
- Nowy termin: "pojutrze na 11" ✅ w tekście

Zamiast extract → Calendar API lookup → move event → confirm, bot pytnął w ciemno "podaj szczegóły". To jest hardcoded fallback bez implementacji.

### Co trzeba zrobić dla C1
1. LLM prompt extract: `client_name`, `old_date`, `new_date`, `new_time`
2. Google Calendar API: `list_events(time_min, time_max, q=client_name)` → znajdź event
3. Dry-run check: czy nowy termin nie koliduje z innym spotkaniem
4. Confirmation card: "Przełożyć spotkanie z X z [stara data] na [nowa data]?"
5. `update_event(event_id, new_start, new_end)`
6. Feedback: "✅ Przełożone. Spotkanie z X jest teraz [nowa data]."
7. Error cases: event not found, ambiguous (kilka spotkań z tym klientem), kolizja

### Ocena wysiłku: ~4-6h (nowy handler, Calendar API, edge cases, testy).

---

## 5. Option C2 — Cancel meeting

**Test:** `anuluj spotkanie z Piotrem Lewandowskim jutro`

Odpowiedź bota:
```
Podaj nazwę lub datę spotkania które chcesz odwołać.
```

### Status: **PLACEHOLDER — funkcja niezaimplementowana**

Ten sam wzorzec co C1. Intent `cancel_meeting` rozpoznany, ale zero parsing. Placeholder.

### Co trzeba zrobić dla C2
1. LLM prompt extract: `client_name`, `date`
2. Calendar API: list events → match by name + date
3. Confirmation card (**R1 — zawsze przed delete**): "Anulować spotkanie z X, [data]?"
4. `delete_event(event_id)` lub soft-cancel (move do "Anulowane" calendar)
5. Post-cancel: zapytaj czy ustawić next contact w Sheets (follow-up call, nowy termin)

### Ocena wysiłku: ~3-4h (podobne do C1, ale bez kolizji-check).

---

## Rekomendacja (moja)

### TL;DR: **Opcja C → Opcja B fix → Opcja A**

**Uzasadnienie:**

1. **C (Reschedule + Cancel) = krytyczne dla real-world workflow.** Spotkania handlowe są notorycznie przesuwane i odwoływane. Bez tego użytkownik musi otworzyć Google Calendar aplikację, co całkowicie kasuje sens bota. To **feature gap**, nie polish.

2. **B działa w 95%.** Bug z "Adamem Wiśniewskim" to edge case, i batch dodawanie klientów do Sheets (bonus) już działa. Fix ~1h → zamknięty.

3. **A jest nice-to-have.** Obecna wersja day planu pokazuje telefon + produkt + następny krok — to w praktyce wystarczy do rana sprzedawcy. Compact jedno-liniowy format oszczędza przewijanie ale informacyjnie jest tym samym.

### Alternatywa (jeśli chcesz szybki wizualny win)
Jeśli chcesz dać Maanowi "wow" w jeden dzień roboczy, **Opcja B fix + Opcja A** w sumie ~3-4h, można zrobić w jednej sesji i dostaniesz czysty multi-meeting + piękny day plan. C to osobna sesja.

### Mój wybór: **C1 (Reschedule) najpierw**, bo:
- To najczęstsze real-world use case ("klient mi przełożył na pojutrze")
- Wymusza porządną integrację z Calendar API (reusable dla C2)
- Po C1 zrobienie C2 (Cancel) zajmie <1h bo infra już będzie

---

## Backlog (do docs/backlog.md)

- **Bug #8**: Multi-meeting parse gubi imię gdy w mianowniku między odmienionymi formami ("Adam Wiśniewski" bez imienia w batch)
- **Bug #9**: Multi-meeting date format "11.04 09:00" bez roku (inconsistency z single meeting "11.04.2026 (sobota)")
- **Bug #10**: Polish inflection w day plan "Spotkanie z Jan Mazur" → "Spotkanie z Janem Mazurem" (narzędnik). Low-priority, ale notatka że to nie jest tylko w day plan — to w każdym miejscu gdzie bot generuje zdanie "z <klient>"
