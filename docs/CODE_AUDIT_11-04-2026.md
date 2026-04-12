# CODE_AUDIT — 11.04.2026

Audyt kodu Python (`oze-agent/bot/`, `oze-agent/shared/`, `oze-agent/api/`) przeciwko zsynchronizowanym plikom SSOT po synchronizacji popo­łud­niowej 11.04.2026.

## Metadane

- **Data audytu:** 11.04.2026 wieczór
- **Audytor:** Claude Code (sesja po kompakcji)
- **Zakres:** `oze-agent/bot/**`, `oze-agent/shared/**`, `oze-agent/api/**`, `oze-agent/supabase_schema.sql`. Łącznie ~4.8k linii Python.
- **Poza zakresem:** `tests/`, `dashboard/`, `admin/`, `docs/**`, `oze-agent/bot/scheduler/` (folder istnieje ale zawiera tylko puste `__init__.py` — kompletny brak implementacji schedulera, to jest osobny fakt odnotowany niżej).
- **Kontrakt:** `docs/SOURCE_OF_TRUTH.md`, `docs/INTENCJE_MVP.md`, `docs/agent_behavior_spec_v5.md`, `docs/agent_system_prompt.md`, `docs/CURRENT_STATUS.md`. `implementation_guide_2.md` użyty wyłącznie jako pomocnicze tło rozumienia intencji — nigdy jako spec.
- **Format wierszy:** `plik:linia | stan kodu | stan speca (SSOT) | kategoria | priorytet | uwagi`.
- **Kategorie:** `known_bug` (wymieniony w `CURRENT_STATUS.md` aktywnych bugach #7-#10), `new_drift` (znaleziony w tym audycie), `aligned` (zgodne — tylko dla pewności).
- **Priorytety:** `must` (blokuje MVP / łamie R1-R8 / pisze złe dane do Sheets/Calendar), `should` (działa ale niezgodnie z tonem lub wzorcem speca), `nice` (kosmetyka / dług techniczny).
- **Brak sekwencji fixów.** Klasyfikacja per wiersz. Triage priorytetów robi Maan.
- **Testy NIE audytowane w tej rundzie.** Folder `tests/` pominięty zgodnie z brifem. Audyt pokrywa kod produkcyjny.

---

## 0. Wnioski ogólne (TL;DR)

Kod bota z commita `bc765a2` (i następujących łat) był pisany przeciwko wcześniejszej wersji SSOT niż ta ze synchronizacji 11.04 popołudnie. Po synchronizacji **większość warstwy UX i kontraktów danych jest out-of-sync**, ale warstwa backendowa (Google API wrapper, Supabase wrapper, search engine, auth) jest w dużej mierze zgodna lub łatwo adaptowalna. Konkretnie:

1. **R1 złamane systemowo.** Nie istnieje builder 3-przyciskowy `[✅ Zapisać][➕ Dopisać][❌ Anulować]`. Wszystkie mutacje używają starego builder­a `[Tak][Nie]` (`telegram_helpers.py:143`) lub `[✅ Zapisz]` (`telegram_helpers.py:153`). `buttons.py` nie obsługuje akcji `append`. W konsekwencji **każda karta mutacyjna w kodzie łamie R1** — nie tylko literalnie (błędne labele), ale też semantycznie (brak "dopisać"). Cancel jest dwu-krokowy ("Anulować? Tak/Nie") zamiast one-click.
2. **R4 złamane.** Duplikaty pokazują stary dialog `[Nowy][Aktualizuj]` (`text.py:404-407`) zamiast default-merge + `[📋 Dopisz do istniejącego][➕ Utwórz nowy wpis]`.
3. **R7 kompletnie nie istnieje.** Po żadnej commited mutacji (`add_client`, `add_note`, `change_status`, `add_meeting`) nie jest wysyłany wolnotekstowy `next_action_prompt` z przyciskiem `❌ Anuluj / nic`. `handle_confirm` kończy się sucharem `✅ Zapisane.`.
4. **R6 kompletnie nie istnieje.** `user_data["active_client"]` nigdzie nie jest utrzymywane. Brak 10-msg / 30-min rolling window context. `handle_general` używa `get_conversation_history(limit=10)` ale to tylko historia chat, nie active_client.
5. **Schema Sheets do wyrzucenia.** `DEFAULT_COLUMNS` w `google_sheets.py:21` ma **21 kolumn zamiast zamrożonych 16**, zawiera retired kolumny (`Dodatkowe info`, `Moc (kW)`, `Metraż domu (m²)`, `Metraż dachu (m²)`, `Kierunek dachu`, `Wartość kontraktu`), **brak kolumny `Data następnego kroku`** (spec L), źle nazwane kolumny (`Źródło` vs `Źródło pozyskania`, `ID kalendarza` vs `ID wydarzenia Kalendarz`). Konsekwencja: nowe arkusze tworzone przez `create_spreadsheet` są bezpośrednio niezgodne ze SSOT i sparsowany kod próbuje pisać do kolumn które nie powinny istnieć.
6. **Klimatyzacja + Negocjacje wciąż w kodzie.** Produkt `Klimatyzacja` jest hardcoded w promptach `claude_ai.py` w dwóch miejscach i w SYSTEM_FIELDS niebezpośrednio. Status `Negocjacje` siedzi w domyślnej liście `pipeline_statuses` w `supabase_schema.sql:32`. Obie rzeczy zostały usunięte ze speca 11.04.
7. **Intencje NIEPLANOWANE wciąż zaimplementowane.** `reschedule_meeting`, `cancel_meeting` mają własne handlery-placeholdery, free_slots ma pełną implementację (`google_calendar.py:264`) + handler w `text.py:1016`. `VALID_INTENTS` w `claude_ai.py:28` jeszcze je listuje, więc klasyfikator ich używa.
8. **POST-MVP bez bannera.** `lejek_sprzedazowy` i `filtruj_klientów` są routowane do pełnych handlerów zamiast odpowiadać "to będzie post-MVP, teraz otwórz dashboard".
9. **`add_note` routuje do złego handlera.** `text.py:210` mapuje `add_note → handle_edit_client_v2`. Intencja `add_note` powinna mieć własny handler odpowiadający `shared/followup.py` lub append do `Notatki`. Dzisiaj działa przypadkowo dzięki NOTE_TRIGGERS fallback w handlerze edit, ale to jest drift.
10. **Compound fusion (R3) nie istnieje.** Jedyna forma R3 w kodzie to "augment add_client" w `_route_pending_flow` który merguje nową wiadomość z istniejącym flow — ale tylko dla `add_client`, nie dla compound `add_meeting + add_client`, i nie ma detekcji "to jest nowa intencja" vs "to uzupełnienie". Inne pending flows (`add_meeting`, `change_status`, `edit_client`) **auto-anulują się** przy każdej nowej wiadomości (`text.py:339-343`) — nawet jeśli użytkownik dopisuje info do tego samego kontekstu.
11. **Scheduler nie istnieje.** `oze-agent/bot/scheduler/__init__.py` jest pusty. Morning brief, meeting reminders, follow-up prompts, pending-flow TTL — nic z planu fazy 5 nie zostało zaimplementowane, mimo że `followup.py`, `format_morning_brief` itd. są przygotowane w `shared/`. To nie jest drift — to brak implementacji — ale jest wpisane tutaj ponieważ zmienia percepcję co jest "w kodzie".

**Co JEST zgodne:**
- `shared/google_auth.py`, `shared/google_drive.py`, `shared/whisper_stt.py`, `shared/encryption.py` — nie audytowane szczegółowo w treści, ale grep nie pokazał żadnych referencji do retired pól. Wrapper Google Drive wygląda OK.
- `shared/search.py` — pure Python fuzzy matcher bez żadnych referencji do Sheets columns. Zgodny.
- `shared/database.py` — Supabase wrapper. `pending_flows` jest single-flow-per-user (upsert) co odpowiada modelowi R3 (jedno pending na raz). Zgodny z modelem danych SSOT. Brak `active_client` to nie jest wina database.py.
- `bot/handlers/start.py` — flow linkowania Telegrama, wygląda OK.
- `bot/handlers/fallback.py` — catch-all. OK.
- `shared/google_calendar.py` — generalnie OK. Jedyne drifty to (a) `get_free_slots` istnieje mimo wycięcia `free_slots`, (b) brak wsparcia dla 4 typów eventów (in_person/phone_call/offer_email/doc_followup).

---

## 1. Known bugs z `CURRENT_STATUS.md` (#7-#10)

Te bugi były już zgłoszone przez Cowork w poprzednich sesjach. Audyt potwierdza ich korzenie w kodzie.

| plik:linia | stan kodu | stan speca (SSOT) | kategoria | priorytet | uwagi |
|---|---|---|---|---|---|
| `bot/handlers/text.py:170-177` | Router auto-kieruje wiadomość zawierającą cyfry (`_contains_phone`) do `handle_add_client` zanim dotrze do klasyfikatora intencji. Pending flow jest sprawdzany WCZEŚNIEJ (`text.py:152-158`), więc teoretycznie jeśli jest pending `add_client` to wiadomość idzie do `_route_pending_flow`. ALE: dla pending flow typu `add_meeting`, `change_status`, `edit_client`, `delete_client` auto-cancel w `text.py:339-343` skasuje pending i nowa wiadomość z telefonem poleci do `handle_add_client`. | Bug #7 (CURRENT_STATUS): gołe telefony w pending flow dla `show_client` / `add_meeting` mają być interpretowane w kontekście aktywnego klienta (R6 active_client), nie jako nowy `add_client`. | known_bug | must | Fix wymaga: (a) active_client state w user_data, (b) detekcji "bare phone" w kontekście last-shown-client, (c) odsunięcia auto-routingu telefon→add_client do etapu PO sprawdzeniu active_client. |
| `bot/handlers/text.py:164-167` | Słowo "zapisz" w wiadomości z >1 słowem wymusza `save_immediately=True` w `handle_add_client` — pomija kartę, zapisuje od razu bez R1. | R1: żadne zapis do Sheets bez jawnego kliknięcia `✅ Zapisać`. Wyjątku "zapisz" NIE MA. | known_bug | must | Bug #7 powiązany. Usunąć `save_immediately` całkowicie, wszystkie zapisy przez kartę. |
| `shared/google_sheets.py:21-43` (`DEFAULT_COLUMNS`) | 21 kolumn, zawiera `Dodatkowe info`, `Moc (kW)`, `Metraż domu (m²)`, `Metraż dachu (m²)`, `Kierunek dachu`, `Wartość kontraktu`, `Źródło` (zamiast `Źródło pozyskania`), `ID kalendarza` (zamiast `ID wydarzenia Kalendarz`). **Brak `Data następnego kroku` (L).** | INTENCJE_MVP §3: zamrożone 16 kolumn A-P. Moc/metraże/kierunek zawsze do `Notatki`. | known_bug | must | Bug #8 (CURRENT_STATUS): schema drift. Zmienić na 16 kolumn dokładnie jak spec, usunąć resztę. |
| `supabase_schema.sql:32` | `pipeline_statuses JSONB DEFAULT '[..., "Negocjacje", ...]'` — 10 statusów, zawiera `Negocjacje`. | INTENCJE_MVP §7: 9 statusów bez `Negocjacje`. | known_bug | must | Bug #9 (CURRENT_STATUS). Poprawić default w sql + osobna migracja dla istniejących userów (poza tym audytem). |
| `shared/claude_ai.py:170` | Prompt `parse_voice_note`: `"Produkty mapuj na: PV, Pompa ciepła, Magazyn energii, Klimatyzacja"` | Produkty: PV, Pompa ciepła, Magazyn energii, PV + Magazyn energii. **Klimatyzacja wycięta 11.04**. | known_bug | must | Bug #10. Usunąć Klimatyzację, dodać opcję compound `PV + Magazyn energii`. |
| `shared/claude_ai.py:303-304` | Prompt `extract_client_data`: `"klimatyzacja → 'Klimatyzacja'"` + instrukcja aby wielo-produktowy zapis `"PV, Magazyn energii, Klimatyzacja"`. | Jak wyżej. | known_bug | must | Ten sam bug #10, drugie miejsce. |

---

## 2. New drift — intencje i router

Cała sekcja dotyczy `bot/handlers/text.py` + `shared/claude_ai.py`. Drift jest systemowy: router nie jest jeszcze zsynchronizowany z listą 6 MVP + 3 POST-MVP + 4 NIEPLANOWANE.

| plik:linia | stan kodu | stan speca (SSOT) | kategoria | priorytet | uwagi |
|---|---|---|---|---|---|
| `shared/claude_ai.py:28-34` (`VALID_INTENTS`) | `{add_client, search_client, edit_client, add_note, delete_client, add_meeting, show_day_plan, view_meetings, reschedule_meeting, cancel_meeting, lejek_sprzedazowy, filtruj_klientów, show_pipeline, change_status, assign_photo, refresh_columns, general_question, confirm_yes, confirm_no, cancel_flow}` | 6 MVP: `add_client`, `show_client`, `add_note`, `change_status`, `add_meeting`, `show_day_plan`. 3 POST-MVP: `edit_client`, `filtruj_klientów`, `lejek_sprzedazowy`. 4 NIEPLANOWANE (usunięte): `reschedule_meeting`, `cancel_meeting`, `free_slots`, `meeting_non_working_day_warning`. Pomocnicze: `general_question`, `confirm_yes`, `confirm_no`, `cancel_flow`. | new_drift | must | `search_client` → rename `show_client`. `delete_client` → usunąć (nie ma w SSOT). `view_meetings` → dedup z `show_day_plan`. `show_pipeline` → usunąć (alias). `reschedule_meeting`, `cancel_meeting` → usunąć. `assign_photo`, `refresh_columns` → nie są w 6 MVP ale są fizycznie potrzebne (foto, odświeżenie schematu) — decyzja do Maana czy zostawić poza listą intencji klasyfikatora. |
| `shared/claude_ai.py:217-218` | Przykłady klasyfikacji używają `search_client` jako label intencji: `"znajdź Jana Kowalskiego" → search_client`, `"co mam o Janie Mazurze" → search_client`. | Intencja nazywa się `show_client`. | new_drift | must | Dwa przykłady + cały prompt do zmiany. |
| `shared/claude_ai.py:225-228` | Przykłady dla `lejek_sprzedazowy` i `filtruj_klientów` są pełne, bez żadnego markeru POST-MVP. | Obie intencje są POST-MVP — R5 mówi: agent rozpoznaje intencję ale odpowiada "to feature post-MVP, teraz otwórz dashboard: <url>", nie wykonuje akcji. | new_drift | must | Klasyfikator może nadal rozpoznawać (dobrze), ale handlery muszą zmienić odpowiedź. Dodać banner R5. |
| `shared/claude_ai.py:230-231` | Przykłady: `"Jan Kowalski podpisał" → change_status {"status": "Podpisał"}`. | Status w pipeline nazywa się `Podpisane` (nie `Podpisał`). INTENCJE_MVP §7 + SOURCE_OF_TRUTH. | new_drift | must | Klasyfikator generuje złą wartość statusu → `change_status` commit zapisuje "Podpisał" do Sheets zamiast "Podpisane". `_STATUS_MAPPING` w `text.py:1154-1165` też nie zawiera mapowania `podpisał → Podpisane`. |
| `shared/claude_ai.py:253` | `"WAŻNE: 'podpisał', 'podpisał kwit/papier/umowę' → change_status {'status': 'Podpisał'}"` | Jak wyżej — wartość statusu musi być `Podpisane`. | new_drift | must | Ten sam korzeń. |
| `shared/claude_ai.py:239-246` | Obszerne przykłady `edit_client` (zmień telefon, popraw metraż, ma nowy numer). Prompt aktywnie zachęca klasyfikator do produkowania `edit_client`. | `edit_client` jest POST-MVP — R5 mówi: agent odpowiada "edycja klientów to post-MVP. Otwórz Sheets aby poprawić ręcznie: <url>." Nie wykonuje. | new_drift | must | Wszystkie przykłady edit_client muszą być zaktualizowane — klasyfikator niech rozpoznaje, handler niech odpowiada R5 bannerem. |
| `bot/handlers/text.py:206-226` (router handlers dict) | Mapa intencji → handler: patrz poniższe linie. | | | | |
| `bot/handlers/text.py:208` | `"search_client": handle_search_client` | Brak intencji `search_client`. Powinno być `"show_client": handle_show_client`. | new_drift | must | Rename. |
| `bot/handlers/text.py:209` | `"edit_client": handle_edit_client_v2` | POST-MVP, ma zwrócić R5 banner. | new_drift | must | Nowy placeholder handler. |
| `bot/handlers/text.py:210` | `"add_note": handle_edit_client_v2` | `add_note` to osobna intencja MVP. Appenduje do kolumny `Notatki` (`note_text` → `{existing}; {new}`). | new_drift | must | Nowy dedykowany handler. Obecna implementacja działa przez keyword fallback NOTE_TRIGGERS w edit flow — to przypadek, nie kontrakt. |
| `bot/handlers/text.py:211` | `"delete_client": handle_delete_client` | Brak intencji `delete_client` w SSOT. | new_drift | must | Usunąć z routera i usunąć `handle_delete_client` (lines 805-838). |
| `bot/handlers/text.py:213-214` | `show_day_plan` i `view_meetings` obie mapują na `handle_view_meetings`. | Jedna intencja: `show_day_plan`. | new_drift | should | Usunąć `view_meetings` alias (historyczny). |
| `bot/handlers/text.py:215-216` | `reschedule_meeting`, `cancel_meeting` mają handlery-placeholdery (`text.py:1049-1072`). | NIEPLANOWANE — intencja ma nie istnieć w klasyfikatorze, a agent ma odpowiadać "nie wspiera, zrób ręcznie w Calendar". | new_drift | must | Usunąć handlery + referencje w routerze + `VALID_INTENTS`. Jeśli klasyfikator sam czasem strzeli, dodać fallback "jeszcze nie obsługuję — otwórz Calendar". |
| `bot/handlers/text.py:217-218` | `lejek_sprzedazowy`, `show_pipeline` mapują na `handle_show_pipeline` (pełna implementacja `text.py:1075-1091`). | POST-MVP — ma odpowiadać R5 bannerem, nie renderować statystyk. | new_drift | must | Zamienić handler na R5 banner. Usunąć alias `show_pipeline`. |
| `bot/handlers/text.py:219` | `filtruj_klientów` → `handle_filter_clients` (pełna implementacja `text.py:1094-1137`). | POST-MVP. | new_drift | must | Zamienić handler na R5 banner. |
| `bot/handlers/text.py:1012-1032` | `handle_view_meetings` ma wbudowaną detekcję free_slots (`wants_free` keyword) która odpala `get_free_slots` i renderuje listę wolnych okien. | `free_slots` jest NIEPLANOWANE (sekcja 6.3 `agent_behavior_spec_v5.md`). | new_drift | must | Usunąć blok free-slot z `handle_view_meetings`. Usunąć import `get_free_slots` z `text.py:58`. |
| `shared/google_calendar.py:264-318` (`get_free_slots`) | Pełna implementacja generowania wolnych slotów 9-18. | NIEPLANOWANE. | new_drift | should | Zostawić funkcję bez referencji jest OK jako dług techniczny, ale lepiej usunąć — żadna część MVP jej nie potrzebuje. |
| `shared/formatting.py:339-363` (`format_morning_brief`) | Sygnatura: `(events, followups, stats, free_slots)`. Renderuje również `format_pipeline_stats(stats)` (jako "Pipeline:") i `free_slots`. | Morning brief w SSOT zawiera: plan dnia (3-4 spotkania), 1-2 follow-upy, zero statystyk pipeline, zero free_slots. | new_drift | must | Usunąć parametr `free_slots`. Usunąć wywołanie `format_pipeline_stats`. Zostawić plan + follow-upy. |
| `shared/claude_ai.py:463-503` (`format_morning_brief` — wersja AI) | Sygnatura: `(events, followups, pipeline_stats)`. Generuje "Pipeline: {stats}" w prompcie. | Jak wyżej — żadnego pipeline w morning brief. | new_drift | must | Usunąć `pipeline_stats`. |
| `bot/handlers/text.py:164-167` (`"zapisz" keyword`) | `if "zapisz" in words and len(words) > 1: save_immediately=True` | R1: brak takiego wyjątku. | new_drift + known_bug | must | Powiązane z bug #7. |
| `bot/handlers/text.py:255-267` (`_route_pending_flow` yes/no detection) | Globalne mapowanie `tak / ok / yes / zapisz / dobra / spoko → is_yes = handle_confirm`, `nie / anuluj → handle_cancel_flow`. Działa dla KAŻDEGO pending flow. | R1: confirm tylko przez przycisk `✅ Zapisać`. Tekst "tak" nie jest kontraktem. | new_drift | should | Decyzja do Maana: zostawić jako UX shortcut (pisanie "tak" zamiast klikania) albo wyciąć dla czystości R1. Obecnie istnieje ryzyko że "tak" w środku prozy (`"tak, jan nowak pompa"`) zostanie zinterpretowane jako confirm. |

---

## 3. New drift — R1 (3-przyciskowe karty) i keyboard builders

| plik:linia | stan kodu | stan speca (SSOT) | kategoria | priorytet | uwagi |
|---|---|---|---|---|---|
| `bot/utils/telegram_helpers.py:143-150` (`build_confirm_buttons`) | Zwraca 2 przyciski: `[✅ Tak][❌ Nie]` z callback_data `{prefix}:yes` / `{prefix}:no`. | R1: karta mutacyjna ma 3 przyciski: `[✅ Zapisać][➕ Dopisać][❌ Anulować]` (one-click cancel, nie "Na pewno?"). | new_drift | must | Zastąpić nowym builder­em `build_card_buttons(callback_prefix)` zwracającym 3 buttony. Stary builder zostawić tylko dla miejsc gdzie naprawdę potrzebujemy yes/no (np. voice_confirm niskiej pewności — też trzeba przedyskutować). |
| `bot/utils/telegram_helpers.py:153-157` (`build_save_buttons`) | Zwraca pojedynczy przycisk `[✅ Zapisz]`. Używany przez `format_add_client_card` flow. | Jak wyżej — 3 przyciski. | new_drift | must | Do usunięcia. |
| `bot/utils/telegram_helpers.py:147` | Label `"✅ Tak"` | Label powinien być `"✅ Zapisać"` (aspekt dokonany). | new_drift | must | |
| `bot/utils/telegram_helpers.py:148` | Label `"❌ Nie"` | Label powinien być `"❌ Anulować"`. | new_drift | must | |
| `bot/handlers/buttons.py:46-50` (`action == "confirm"`) | `value == "yes"` → `handle_confirm`, else → `handle_cancel_flow` (dwu-krokowy z "Anulować?" loop). | Trzy wartości callback: `save` (commit), `append` (dopisać, pending zostaje otwarty), `cancel` (one-click delete). | new_drift | must | Nowa obsługa akcji. |
| `bot/handlers/buttons.py:64-73` (`action == "duplicate"`) | `add_anyway` → save new client; else → `handle_cancel_flow`. Default path: cancel. | R4 default: **merge do istniejącego**. Przyciski: `[📋 Dopisz do istniejącego][➕ Utwórz nowy wpis]`. Żadnego yes/no. | new_drift | must | Pełna rekompozycja duplikat flow. |
| `bot/handlers/buttons.py:106-111` (`action == "cancel_confirm"`) | Dwu-krokowy cancel: pierwszy klik `[❌ Nie]` pyta "Anulować?", drugi klik [Tak] kasuje pending. | R1: one-click cancel. Jednym kliknięciem `❌ Anulować` pending ma być skasowany bez pytania. | new_drift | must | Usunąć cały handler `cancel_confirm`. |
| `bot/handlers/text.py:1432-1467` (`handle_cancel_flow`) | Implementuje dwu-krok cancel: pierwsze wejście ustawia `_cancelling=True` i pyta "Anulować?", drugie potwierdza. | One-click cancel. | new_drift | must | Usunąć `_cancelling` state. `handle_cancel_flow` ma od razu `delete_pending_flow` + `"🫡 Anulowane."`. |
| `bot/handlers/text.py:1464-1467` | Tekst `"Anulować?"` z `build_confirm_buttons` — to jest "Na pewno?" loop. | Spec wyraźnie zakazuje "Na pewno?" loop. | new_drift | must | Do usunięcia wraz z powyższym. |
| `shared/formatting.py:209` (`format_add_client_card`) | Ostatnia linia karty: `"Zapisać / dopisać / anulować?"` — to jest tekst WSKAZUJĄCY na 3 akcje, ale keyboard builder to tylko `build_save_buttons` (jeden przycisk `[✅ Zapisz]`). | Karta + keyboard muszą być spójne. | new_drift | must | Po zaimplementowaniu `build_card_buttons` tekst jest OK; problem jest w layer wyżej (`text.py` używa złego builder­a). |
| `shared/formatting.py:206-207` | `if not client_data.get("Następny krok") and not client_data.get("Data następnego kontaktu"): lines.append("📅 Kiedy następny kontakt?")` — hardcoded pytanie o next contact wewnątrz karty add_client. | R7 `next_action_prompt` jest WYSYŁANY JAKO OSOBNA WIADOMOŚĆ PO COMMIT mutacji, nie jest częścią karty add_client. Stare zachowanie (hardcoded pytanie w karcie) to pre-11.04 wzorzec. | new_drift | must | Usunąć z karty. Przenieść logikę do R7 post-commit prompt w `handle_confirm`. |
| `shared/formatting.py:193` | `_FOLLOWUP_FIELDS = {"Następny krok", "Data następnego kontaktu"}` — nazwa drugiego pola zła. | Spec L: `Data następnego kroku`. | new_drift | must | Rename. |
| `shared/formatting.py:217` | `_DATE_FIELDS = {..., "Data następnego kontaktu"}` | Jak wyżej. | new_drift | must | |
| `bot/handlers/text.py:404-407` (duplikat flow) | Przyciski: `[("Nowy", "duplicate:add_anyway"), ("Aktualizuj", "duplicate:no")]`. | R4: `[("📋 Dopisz do istniejącego", ...), ("➕ Utwórz nowy wpis", ...)]` + default-merge semantyka (bez akcji = merge). | new_drift | must | Labels + semantyka. |
| `bot/handlers/text.py:402-403` | Tekst: `"⚠️ Masz już {dup_name} ({dup_info}).\nDodać nowego czy zaktualizować?"` | Spec R4: agent NIE pyta "dodać czy zaktualizować". Spec zakłada default = merge + pokazuje kartę "aktualizacja klienta X" z 3 przyciskami R1 + przycisk "utwórz nowy wpis" jako alternatywę. | new_drift | must | Pełna rekompozycja. |
| `shared/formatting.py:395-412` (`format_confirmation`) | Labele: `add_client, edit_client, delete_client, add_meeting, update_meeting, delete_meeting, update_status`. Kończy wiadomość: `"Odpowiedz *tak* aby potwierdzić lub *nie* aby anulować."` | Edit_client POST-MVP, delete_client nie istnieje, update_meeting nie istnieje (reschedule NIEPLANOWANE), delete_meeting nie istnieje (cancel_meeting NIEPLANOWANE). Tekst "odpowiedz tak/nie" sprzeczny z R1 przyciskowym UX. | new_drift | must | Okroić słownik do: `add_client`, `add_note`, `add_meeting`, `change_status`. Zmienić outro na 3-button UX. |

---

## 4. New drift — R3 pending flow i compound fusion

R3 definiuje 4 drogi obsługi nowej wiadomości w trakcie pending flow: (a) auto-cancel dla obcej intencji, (b) `➕ Dopisać` przycisk, (c) auto-doklejanie dla pasujących pól tego samego typu, (d) compound fusion (np. `add_meeting` + info o kliencie z tej samej wiadomości).

| plik:linia | stan kodu | stan speca (SSOT) | kategoria | priorytet | uwagi |
|---|---|---|---|---|---|
| `bot/handlers/text.py:271-337` | Implementacja jednej drogi "augment add_client" — działa tylko jeśli `flow_type == "add_client"`, Claude wyciągnął nowe dane, nowe imię zgadza się ze starym. Merguje i pokazuje kartę na nowo. | To jest częściowo R3 droga (c) auto-doklejanie, ograniczona do add_client. | partial_aligned | must | Drogi (a), (b), (d) brak. Compound fusion (`add_meeting + add_client` w jednej wiadomości) nie istnieje. Jeśli użytkownik w trakcie pending `add_meeting` dopisze "telefon 601234567" to `text.py:339-343` kasuje pending i routuje telefon przez auto-routing do `add_client` — traci kontekst meeting. |
| `bot/handlers/text.py:339-343` | Else branch: `delete_pending_flow + "⚠️ Anulowane." + return False`. Dla KAŻDEGO innego flow typu i każdej nie-yes/no wiadomości. | R3 droga (a) — dla obcej intencji OK. Ale dla (d) compound fusion — źle; dla (c) doklejania w innych typach — też źle. | new_drift | must | Rozbicie na wiele dróg per flow_type. |
| `bot/handlers/text.py:902-995` (`handle_add_meeting`) | Jeśli user wyśle "jutro o 10 jadę do Jana Nowaka ul. Różana 3 Piaseczno telefon 601234567" → klasyfikator strzela `add_meeting` (ma temporal marker), meeting jest parsowany z `client_name="Jan Nowak"`, telefon i adres wylatują w próżnię. Nie ma logiki "rozpoznałem też dane klienta, pokażę 2 karty". | R3 compound fusion: agent rozpoznaje że wiadomość ma 2 intencje i pokazuje kartę `add_meeting` + kartę `add_client` sekwencyjnie (lub jako 1 kartę złożoną). | new_drift | must | Osobne zadanie — wymaga zmian w klasyfikatorze (zwrot listy intencji) i w orchestration layer w `handle_text`. |
| `shared/database.py` | Brak `active_client` w żadnym schemacie Supabase. `users.sheet_columns` jest cache, ale nie active_client state. `pending_flows` ma tylko `flow_type + flow_data`. | R6: 10 msg / 30 min rolling window dla kontekstu + `active_client` utrzymywany do kolejnej mutacji. | new_drift | must | Decyzja do Maana: gdzie trzymać active_client — Supabase (nowa kolumna w `users` albo nowa tabela `active_context`) czy in-process state w `context.user_data` (znika przy restarcie bota). Musi być wpisane gdzieś persistente dla follow-upów. |
| `bot/handlers/text.py:180` | `save_conversation_message(telegram_id, "user", message_text)` — zapisuje user msg do historii PO sprawdzeniu pending flow (czyli przepuszcza tylko te wiadomości które NIE były pochłonięte przez pending). | R6: historia musi być kompletna — inaczej context dla `handle_general` jest dziurawy. Ale to pomniejsze. | new_drift | should | |
| `bot/handlers/voice.py:89` | `save_conversation_message(telegram_id, "user", f"[głosówka] {transcription}")` — OK. | | aligned | — | |
| `bot/handlers/text.py:1515` | `save_conversation_message(telegram_id, "assistant", response_text)` tylko w `handle_general`. Dla innych handlerów (add_client, show_client, add_meeting, change_status) odpowiedzi bota NIE są zapisywane do historii. | R6 rolling window musi obejmować też assistant responses żeby klasyfikator następnej wiadomości miał pełny kontekst. | new_drift | should | Dopisać `save_conversation_message("assistant", ...)` we wszystkich handlerach lub w centralnym miejscu. |

---

## 5. New drift — R7 next_action_prompt

R7 (po synchronizacji 11.04 popołudnie): po każdej commited mutacji agent wysyła JEDNO wolnotekstowe pytanie "Co dalej z Janem Kowalskim? Spotkanie, telefon, follow-up?" z jedyną opcją `❌ Anuluj / nic`. NIE 3-button meeting/call/not-interested.

| plik:linia | stan kodu | stan speca (SSOT) | kategoria | priorytet | uwagi |
|---|---|---|---|---|---|
| `bot/handlers/text.py:1251-1266` (commit `add_client`) | Po sukcesie: `"✅ Zapisane."` i koniec (lub pyta o kolejnego klienta z `_offer_remaining`). Brak R7 prompt. | Po commit `add_client` agent wysyła R7 next_action_prompt. | new_drift | must | Dodać R7 prompt po wszystkich commit paths. |
| `bot/handlers/text.py:1277-1292` (commit `edit_client`) | `"✅ Zapisane."` | `edit_client` jest POST-MVP, więc cała sekcja do R5 banner. Gdyby była MVP — też R7. | new_drift | must | (Usuwane wraz z edit_client). |
| `bot/handlers/text.py:1396-1401` (commit `change_status`) | `"✅ Status zmieniony na: {new_value}"` | Po commit `change_status` — R7 prompt. | new_drift | must | |
| `bot/handlers/text.py:1302-1326` (commit `add_meeting`) | `"✅ Spotkanie dodane do kalendarza."` — jedyny wyjątek: jeśli klient nie jest w Sheets, pyta "Dodać?" (offer_add_client flow). | `add_meeting` ma wbudowany next step (sam meeting definiuje next contact), więc R7 prompt nie jest potrzebny dla meeting — tak mówi CLAUDE.md rule 9. | aligned-ish | nice | Weryfikacja: CLAUDE.md mówi "chyba że z samej mutacji wynika wprost następny krok (np. add_meeting już definiuje 'next contact')". Zatem add_meeting może zostać bez R7. Nie drift. |
| `bot/handlers/buttons.py:92-102` (commit `set_status` via button) | Po `set_status` button: `query.edit_message_text(f"✅ Status zmieniony na: {new_status}")` — brak R7. | R7 też po tej ścieżce. | new_drift | must | |

---

## 6. New drift — formatowanie i schema danych

| plik:linia | stan kodu | stan speca (SSOT) | kategoria | priorytet | uwagi |
|---|---|---|---|---|---|
| `shared/formatting.py:126-210` (`format_add_client_card`) | Linia 2 karty: `{product} {power}kW | {metraże}` — moc i metraże są sklejane do widocznego wiersza karty. | INTENCJE_MVP: moc/metraż/dach/kierunek zawsze do `Notatki`, nigdy do osobnej kolumny, nigdy nie mają swojego wiersza w karcie. Widoczny wiersz to tylko: produkt, mocno opcjonalnie rozmiar instalacji. | new_drift | should | Refaktor — moc i metraże nie mają specjalnego render, idą do `Notatki` jak reszta extra fields. |
| `shared/formatting.py:78-83` (`_MEASUREMENT_FIELDS`) | Słownik candidate columns: `house`, `roof`, `power`, `dir` — próbuje znaleźć dedykowane kolumny `Moc (kW)`, `Metraż domu (m²)`, `Metraż dachu (m²)`, `Kierunek dachu`. | Tych kolumn nie ma w 16-kolumnowym schemacie. Wszystko do Notatki. | new_drift | should | Usunąć cały mechanizm _MEASUREMENT_FIELDS. |
| `shared/formatting.py:313-320` (`format_daily_schedule`) | Renderuje tylko `📅` dla wszystkich eventów (przez `format_meeting`). | Spec: 4 typy eventów z różnymi emoji: 🤝 in_person (60 min), 📞 phone_call (15 min), ✉️ offer_email (0 min), 📄 doc_followup (0 min). Plan dnia ma je różnicować. | new_drift | should | Wymaga też zmian w `create_event` aby zapisywać event_type (np. w extended properties albo jako prefiks tytułu). |
| `shared/formatting.py:288-310` (`format_meeting`) | Użycie `format_meeting` renderuje `📅 HH:MM-HH:MM — *{title}*`. | Jak wyżej — emoji per typ. | new_drift | should | |
| `bot/handlers/text.py:871-877` (`_enrich_meeting`) | Tytuł: `f"Spotkanie z {full_name}"`. Brak event_type. | Spec: event_type potrzebny do różnicowania. Dla in_person (default) tytuł OK. Dla phone_call tytuł typu "Telefon do Jana Nowaka". | new_drift | should | Wymaga (a) klasyfikatora rozpoznającego "zadzwonię do" vs "jadę do", (b) różnych tytułów + duration. |
| `shared/google_sheets.py:222` (`add_client`) | `client_data["Data pierwszego kontaktu"] = date.today().strftime("%Y-%m-%d")` — zapisuje ISO `YYYY-MM-DD` do Sheets. | Spec: format `DD.MM.YYYY (Dzień tygodnia)`. ALE: to jest co idzie do arkusza, a Google Sheets renderuje daty po swojemu. Decyzja: albo zapisujemy ISO i formatujemy na read (`_fmt_date`), albo zapisujemy formatowany tekst. | partial_aligned | nice | Obecna implementacja działa, `_fmt_date` w `formatting.py` umie formatować ISO na `DD.MM.YYYY (dzień)` przy odczycie. Sprawdzić z Maanem czy to preferowany sposób. |
| `shared/google_sheets.py:267` (`update_client`) | `updates["Data ostatniego kontaktu"] = date.today().strftime("%Y-%m-%d")` — auto-update co update. | Zgodne ze spec (data ostatniego kontaktu aktualizuje się automatycznie). | aligned | — | |
| `bot/handlers/text.py:73-77` (`SYSTEM_FIELDS`) | `{"Data pierwszego kontaktu", "Data ostatniego kontaktu", "Status", "Zdjęcia", "Link do zdjęć", "ID kalendarza", "Email", "Dodatkowe info", "Notatki", "Następny krok"}` | `ID kalendarza` → `ID wydarzenia Kalendarz`. `Dodatkowe info` → usunąć. `Email` NIE jest systemowe — handlowiec często go wpisuje. `Notatki` NIE jest systemowe — handlowiec wpisuje notatki. `Następny krok` NIE jest systemowe — tak samo. | new_drift | must | Poprawny SYSTEM_FIELDS: `{"Data pierwszego kontaktu", "Data ostatniego kontaktu", "Status", "Zdjęcia", "Link do zdjęć", "ID wydarzenia Kalendarz"}`. Reszta to pola normalne. |
| `shared/formatting.py:215` (`SKIP_FIELDS`) | `{"_row", "Link do zdjęć", "ID kalendarza", "Wiersz"}` | `ID kalendarza` → `ID wydarzenia Kalendarz`. | new_drift | should | Po zmianie nazwy kolumny. |
| `shared/claude_ai.py:297` (extract prompt system fields) | `"...'Dodatkowe info', 'Notatki', 'Następny krok'"` listuje 3 pola które NIE są systemowe. | Jak wyżej. | new_drift | must | |
| `shared/claude_ai.py:316` | `"Gdy nie istnieją — zapisz w 'Dodatkowe info' lub 'Notatki' jako tekst"` | `Dodatkowe info` nie istnieje. Wszystko do `Notatki`. | new_drift | must | |
| `shared/claude_ai.py:307-311` (instrukcje ekstrakcji) | Instruuje LLM: metraż domu → szukaj kolumny z "domu", metraż dachu → szukaj kolumny z "dachu", moc → "Moc (kW)", kierunek → "Kierunek dachu". | Żadna z tych dedykowanych kolumn nie istnieje w spec. Wszystko do Notatki. | new_drift | must | Przepisać promptny sekcji "Parsuj bez pytania". |
| `shared/claude_ai.py:314` | `"zapisz w kolumnie 'Następny krok' lub 'Data następnego kontaktu'"` | Kolumna nazywa się `Data następnego kroku`. | new_drift | must | |

---

## 7. New drift — API i inne

| plik:linia | stan kodu | stan speca (SSOT) | kategoria | priorytet | uwagi |
|---|---|---|---|---|---|
| `api/main.py:11` | `allow_origins=["*"]` + komentarz `# Restrict in production` | Nie jest drift wg SSOT — SSOT nie mówi nic o CORS. | aligned | nice | Dług tech do post-MVP, nie audytu. |
| `api/main.py` | Pojedynczy route `/auth` + `/health`. Brak webhookow dla dashboardu/bot. | SSOT nie wymaga więcej — dashboard jest post-MVP. | aligned | — | |
| `bot/scheduler/__init__.py` | Pusty plik (0 bajtów). | Faza 5 w `implementation_guide_2.md` definiuje scheduler (morning brief, reminders, followup prompts). Bez schedulera: brak morning brief, brak meeting reminders, brak follow-up prompts po spotkaniu, brak TTL dla pending flows. | new_drift | should | Nie audytowane głębiej — po prostu nie istnieje. Informacja dla triage. Shared functions (`format_morning_brief`, `check_unreported_meetings`, `create_followup_prompts`) są gotowe ale nie są nigdzie wywoływane. |
| `bot/handlers/voice.py:103` | Stary pattern: `Czy to poprawne?` + `build_confirm_buttons("voice_confirm")` → [Tak][Nie] | Decyzja: voice confirmation to nie jest mutacja R1 (to jest "potwierdź że transkrypcja jest poprawna żeby móc przetworzyć"). Może pozostać dwa przyciski, ale warto uspójnić labele. | new_drift | nice | Do decyzji z Maanem — czy ten flow też ma być 3-przyciskowy? Moim zdaniem nie, bo nie ma akcji "dopisać". |
| `bot/handlers/photo.py:62-78` | Zapisuje bajty zdjęcia do Supabase `pending_flows` jako listę intów w JSON (line 66: `"photo_bytes": list(bytes(photo_bytes))`). | Supabase `pending_flows.flow_data` to `jsonb` — zapisywanie bajtów jako JSON-list inflatuje rozmiar 3-4x i jest nieoptymalne. SSOT o tym nie mówi wprost. | partial_aligned | nice | Nie jest drift SSOT — to jest wybór implementacyjny. Flag dla Maana bo może ugryźć na rozmiarze DB. |
| `shared/whisper_stt.py`, `shared/encryption.py`, `shared/google_drive.py`, `shared/google_auth.py` | Nie audytowane szczegółowo (brak referencji do retired pól w grep). | | aligned | — | Weryfikacja tylko przez grep na `Klimatyzacja`, `Negocjacje`, `Dodatkowe info` — żadnych trafień. |
| `bot/handlers/buttons.py:75-76` (`action == "edit"`) | Handler dla `edit` action — wywołuje `_handle_edit_choice` z replace/keep_both logic dla pola phone/email. | `edit_client` POST-MVP. | new_drift | should | Osiąga POST-MVP, handler można zostawić na razie (edge case dla phone conflict w `add_client` duplikacie), ale lepiej wyciąć wraz z edit_client. |
| `bot/handlers/buttons.py:76-78` (`action == "voice_confirm"`) | Handler dla voice_confirm. | OK. | aligned | — | |
| `bot/handlers/text.py:1470-1484` (`handle_refresh_columns`) | Handler dla intencji `refresh_columns`. Woła `get_sheet_headers` (który cache'uje w Supabase). | Spec nie mówi o `refresh_columns` jako dedykowanej intencji, ale praktycznie potrzebna — gdy user doda kolumnę w Sheets ręcznie, agent musi ją zauważyć. | partial_aligned | nice | Decyzja do Maana: zostawić czy usunąć. |

---

## 8. Aligned — zgodne elementy

| plik:linia | co jest zgodne |
|---|---|
| `shared/database.py` (cały plik) | Supabase wrapper — `pending_flows` jako single-upsert (dobrze dla single active flow per user), conversation_history insert, interaction logging. |
| `shared/search.py` (cały plik) | Pure Python fuzzy matcher, obsługa polskich diakrytyków, Levenshtein, detect_potential_duplicate z progami name<=2 city<=1 — bez referencji do retired pól. |
| `shared/google_calendar.py` poza `get_free_slots` | Wrapper Calendar API jest czysty. Create/update/delete/check_conflicts wszystko async via `asyncio.to_thread`. |
| `shared/google_sheets.py` (logika poza DEFAULT_COLUMNS) | `get_sheet_headers` czyta A1:ZZ1 i cache'uje — schema-agnostic czytanie działa. `add_client`, `update_client`, `delete_client`, `get_pipeline_stats`, `get_all_clients` są schema-agnostic (patrzą na `headers` / dict keys, nie hardcoded). Problem jest tylko z `DEFAULT_COLUMNS` przy tworzeniu nowych arkuszy. |
| `bot/handlers/start.py` | Flow linkowania Telegram z kodem deeplink. Weryfikacja expiry, conflict check. |
| `bot/handlers/fallback.py` | Catch-all z re-routing dla forwarded messages. |
| `bot/handlers/photo.py` | Upload logic działa end-to-end (folder + upload + sheet update). Jedyny drift: storage bajtów w JSON `pending_flows` (punkt 7). |
| `bot/handlers/voice.py` | Whisper transcription + confidence threshold + low-confidence confirmation. Logika przepływu OK. |
| `shared/claude_ai.py` poza VALID_INTENTS / prompts | `call_claude`, `call_claude_with_tools` core wrappers są OK. Model routing (sonnet-4.6 / haiku-4.5) zgodny ze SSOT. |
| `shared/followup.py` (cały plik) | Follow-up logic jest gotowa, po prostu nie jest wywoływana przez scheduler. Szkielet zgodny. |
| `shared/formatting.py:_fmt_date, _fmt_phone, format_client_card` | Helpers formatowania daty/telefonu i karta odczytu klienta. Karta odczytu (`format_client_card`) jest read-only zgodnie z R1 wyjątkiem. |
| `api/main.py` | FastAPI app z healthcheckiem i OAuth router. |

---

## 9. Checklista 1-15 — wyniki

Checklista pochodzi z `CURRENT_STATUS.md` — 15 punktów na które audyt miał odpowiedzieć.

| # | Pytanie | Wynik | Dowód |
|---|---|---|---|
| 1 | Czy `VALID_INTENTS` odpowiada 6 MVP + 3 POST-MVP + pomocniczym? | ❌ drift | §2. Zawiera retired intencje `delete_client`, `reschedule_meeting`, `cancel_meeting`, `view_meetings`, `show_pipeline`; używa `search_client` zamiast `show_client`; ma `assign_photo`, `refresh_columns` które nie są w SSOT. |
| 2 | Czy keyboard builder ma wariant 3-przyciskowy `[✅ Zapisać][➕ Dopisać][❌ Anulować]`? | ❌ brak | §3. `telegram_helpers.py:143-157` — tylko `build_confirm_buttons` (2) i `build_save_buttons` (1). Nowy builder do napisania. |
| 3 | Czy `handle_confirm` wykonuje next_action_prompt (R7) po commit? | ❌ brak | §5. Żaden commit path nie wysyła R7 prompt. Outro to `"✅ Zapisane."` / `"✅ Status zmieniony..."`. |
| 4 | Czy cancel jest one-click? | ❌ drift | §3. `handle_cancel_flow` (`text.py:1432-1467`) implementuje dwu-krok "Anulować? Tak/Nie". Też `buttons.py:106-111` `cancel_confirm` handler. |
| 5 | Czy duplikat flow R4 default-merges? | ❌ drift | §3. `text.py:402-408` pyta "Dodać nowego czy zaktualizować?" z `[Nowy][Aktualizuj]` buttons. Default to cancel (`buttons.py:72-73`). |
| 6 | Czy jest compound fusion R3 (d)? | ❌ brak | §4. Istnieje tylko auto-doklejanie dla add_client (droga c). Add_meeting z bare phone w tej samej wiadomości — nie ma obsługi. |
| 7 | Czy active_client state jest utrzymywany (R6)? | ❌ brak | §4. Nigdzie w `database.py` ani `text.py`. Context jest tylko przez `conversation_history` (bez struktury active_client). |
| 8 | Czy scheme Sheets to 16 kolumn zamrożonych (A-P)? | ❌ drift | §1 bug #8. 21 kolumn w `DEFAULT_COLUMNS`, brakujące `Data następnego kroku`, retired `Dodatkowe info`/`Moc (kW)`/metraże. |
| 9 | Czy pipeline to 9 statusów (bez Negocjacje)? | ❌ drift | §1 bug #9. `supabase_schema.sql:32` ma 10 statusów z Negocjacje. |
| 10 | Czy produkty to PV / Pompa ciepła / Magazyn energii / PV+Magazyn (bez Klimatyzacji)? | ❌ drift | §1 bug #10. `claude_ai.py:170, 303-304` ma Klimatyzację. Brak compound `PV + Magazyn energii` w mapowaniu. |
| 11 | Czy moc/metraż/dach/kierunek idą do Notatki, nigdy do osobnych kolumn ani do widocznej linii karty? | ❌ drift | §6. `formatting.py:155-180` skleja moc i metraże do widocznego wiersza karty. `claude_ai.py:307-311` instruuje LLM na dedykowane kolumny. `DEFAULT_COLUMNS` ma te kolumny. |
| 12 | Czy `reschedule_meeting`, `cancel_meeting`, `free_slots` zostały usunięte (NIEPLANOWANE)? | ❌ drift | §2. Handlery dla reschedule/cancel są placeholder­ami ale istnieją. `free_slots` ma pełną implementację w `google_calendar.py:264` + aktywne wywołanie w `text.py:1016-1032`. |
| 13 | Czy morning brief NIE zawiera pipeline stats ani free_slots? | ❌ drift | §2. Obie implementacje (`formatting.py:339-363` i `claude_ai.py:463-503`) mają te pola. |
| 14 | Czy `add_note` ma dedykowany handler? | ❌ drift | §2. `text.py:210` mapuje `add_note → handle_edit_client_v2`. Działa przez przypadek (NOTE_TRIGGERS). |
| 15 | Czy `edit_client`, `lejek_sprzedazowy`, `filtruj_klientów` zwracają banner POST-MVP (R5)? | ❌ drift | §2. Wszystkie trzy mają pełne handlery. Żaden nie wysyła bannera "to post-MVP, otwórz dashboard". |

**Wynik:** 0/15 w pełni zgodnych. Każdy punkt ma co najmniej jeden drift. Większość driftów to `must` priority.

---

## 10. Niepewności / decyzje dla Maana

1. **Voice low-confidence confirm** (`voice.py:103` + `build_confirm_buttons("voice_confirm")`) — to nie jest mutacja R1, to pytanie "czy transkrypcja jest poprawna". Czy ma zostać 2-przyciskowe, czy uspójnić z 3-button? Moim odczytem SSOT: R1 dotyczy tylko mutacji, voice confirm może zostać, ale warto zgrać labele (`✅ Tak`→`✅ Poprawne`, `❌ Nie`→`❌ Źle`).

2. **`refresh_columns` jako intencja** (`text.py:1470-1484`, `claude_ai.py:32`) — SSOT nie wymienia tej intencji w liście 6 MVP / POST-MVP / NIEPLANOWANE. Jest fizycznie potrzebna (user dodał kolumnę w Sheets ręcznie). Zostawiamy jako "systemowa poza listą" czy dodajemy do MVP?

3. **`assign_photo` flow** (`photo.py` + `VALID_INTENTS`) — podobnie. SSOT ma foto w "Zdjęcia" (kolumna N) ale nie definiuje tego jako osobnej intencji. Handler istnieje i działa. Zostawiamy?

4. **`save_immediately` keyword "zapisz"** (`text.py:164-167`) — Maan wie że to jest bug #7 i łamie R1. Pytanie: całkowicie usuwamy czy zamieniamy na "zapisz" = confirm w kontekście pending flow (ale nie save_immediately bez karty)?

5. **`build_confirm_buttons` jako generic helper** — czy po wprowadzeniu 3-button wariantu zachowujemy builder `[Tak][Nie]` dla innych flowów (borrow, voice_confirm, confirm_search), czy wycinamy całkowicie?

6. **`handle_delete_client`** (`text.py:805-838`) — usuwamy kompletnie czy tylko odcinamy od routera (zostawiając dead code do hipotetycznego POST-MVP)? Usunięcie zmniejsza powierzchnię ataku.

7. **Edit phone conflict flow** (`buttons.py:136-163`) — "Zamień / Dodaj drugi" dla kolizji numerów w add_client. Jest elegancki. Edit_client jest POST-MVP, ale ten sub-flow może być użyteczny też w samym add_client (gdy duplicate check pokaże kolizję numeru na tym samym kliencie po merge). Pytanie czy zachować.

8. **`DEFAULT_COLUMNS` vs istniejący userów arkusze** — `create_spreadsheet` używa `DEFAULT_COLUMNS` przy tworzeniu NOWEGO arkusza. Istniejący userów arkusze mają cokolwiek mają, bo `get_sheet_headers` czyta A1:ZZ1. Po fix: nowe arkusze będą 16-kolumnowe, istniejące nie zmienią się (user musiałby zmigrować ręcznie). OK? Potrzebna osobna migracja? Decyzja produktowa.

9. **Compound fusion (R3 droga d) — priorytet** — jest `must` bo łamie UX, ale technicznie wymaga zmiany klasyfikatora żeby zwracał listę intencji albo drugiego passu klasyfikatora na "pozostały tekst po wyciągnięciu add_meeting". Pytanie o hierarchię: czy to jest do zrobienia w tej samej fali co pozostałe R1/R3/R7, czy jako osobna faza?

10. **`active_client` state storage** — Supabase (persystentny) vs `context.user_data` (in-memory, reset przy restarcie). Spec nie mówi wprost. Moja rekomendacja: Supabase bo bot na Railway może restartować często. Ale wymaga nowej tabeli albo kolumny.

---

## 11. Uwagi końcowe

- **Zakres audytu był kod produkcyjny.** `tests/` NIE audytowane w tej rundzie. Po naprawie warstwy kodu Maan może zdecydować o osobnym audycie testów — szczególnie że wiele z nich było pisanych przeciwko starej schema/UX i pewnie jest aktualnie zielonych na rzeczy które nie powinny się dziać.
- **Scheduler (`bot/scheduler/`) jest pusty** — to nie jest drift, to brak implementacji. Faza 5 implementation_guide_2.md opisuje co ma robić. Shared helpers są gotowe. Flag dla triage.
- **Duży odsetek driftów ma ten sam korzeń** — system prompt dla Claude Haiku/Sonnet (`claude_ai.py`) i `telegram_helpers.py` keyboard builder. Fix jednego miejsca często koryguje kilka wierszy w tej tabeli. Maan zobaczy to przy triage.
- **Klasa `TodoWrite` i stan sesji nie dotyczą audytu** — wspomniane bo w sesji cię­gnę­ła się historia prac, nie wpływ na kod produkcyjny.
- **Nie cytowałem `implementation_guide_2.md` jako speca nigdzie.** Używałem go tylko jako tła dla zrozumienia intencji kodu, zgodnie z brifem.

**Audyt zakończony.** Zero wierszy kodu zmodyfikowanych podczas audytu — tylko czytanie.
