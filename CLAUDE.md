# Agent Instructions

You're working inside the WAT framework (Workflows, Agents, Tools). This architecture separates concerns so that probabilistic AI handles reasoning while deterministic code handles execution. That separation is what makes this system reliable.

## The WAT Architecture

**Layer 1: Workflows (The Instructions)**
- Markdown SOPs stored in `workflows/`
- Each workflow defines the objective, required inputs, which tools to use, expected outputs, and how to handle edge cases
- Written in plain language, the same way you'd brief someone on your team

**Layer 2: Agents (The Decision-Maker)**
- This is your role. You're responsible for intelligent coordination.
- Read the relevant workflow, run tools in the correct sequence, handle failures gracefully, and ask clarifying questions when needed
- You connect intent to execution without trying to do everything yourself

**Layer 3: Tools (The Execution)**
- Python scripts in `tools/` that do the actual work
- API calls, data transformations, file operations, database queries
- Credentials and API keys are stored in `.env`
- These scripts are consistent, testable, and fast

**Why this matters:** When AI tries to handle every step directly, accuracy drops fast. If each step is 90% accurate, you're down to 59% success after just five steps. By offloading execution to deterministic scripts, you stay focused on orchestration and decision-making where you excel.

## How to Operate

**1. Look for existing tools first**
Before building anything new, check `tools/` based on what your workflow requires. Only create new scripts when nothing exists for that task.

**2. Learn and adapt when things fail**
When you hit an error: read the full error message and trace, fix the script and retest (if it uses paid API calls or credits, check with me before running again), document what you learned in the workflow.

**3. Keep workflows current**
Workflows should evolve as you learn. When you find better methods, discover constraints, or encounter recurring issues, update the workflow. Don't create or overwrite workflows without asking unless I explicitly tell you to.

## The Self-Improvement Loop

Every failure is a chance to make the system stronger: identify what broke → fix the tool → verify the fix works → update the workflow with the new approach → move on with a more robust system.

---

# Current Project: OZE-Agent

AI-powered sales assistant for B2C renewable energy salespeople in Poland. Telegram bot + FastAPI backend + Next.js dashboard.

_Last meaningful update to this file: 11.04.2026 popołudnie — po pełnej synchronizacji czterech plików SSOT (`SOURCE_OF_TRUTH.md`, `INTENCJE_MVP.md`, `agent_behavior_spec_v5.md`, `agent_system_prompt.md`) do decyzji z 11.04.2026. Stare referencje do `OZE_Agent_Brief_v5_FINAL.md` (teraz w `docs/archive/`) i `implementation_guide.md` (teraz `implementation_guide_2.md`, częściowo nieaktualne) zostały usunięte lub przesunięte._

## SSOT (Single Source of Truth) — kolejność czytania

Jeśli dwa dokumenty się nie zgadzają, **wygrywa ten wyżej w hierarchii**:

1. **`docs/SOURCE_OF_TRUTH.md`** — decision log + hierarchia wszystkich dokumentów + mapa decyzji produktowych. **Pierwsze co czytasz w nowej sesji.** Jeśli cokolwiek poniżej jest niespójne, decyduje ten plik.
2. **`docs/INTENCJE_MVP.md`** — zamrożone kontrakty intencji MVP (6 MVP + POST-MVP + NIEPLANOWANE), 16-kolumnowy schemat Sheets, 9-statusowy pipeline, 7-opcyjna lista "Następny krok", lista produktów (bez Klimatyzacji), banned phrases dla parserów.
3. **`docs/agent_behavior_spec_v5.md`** — 52 testy akceptacyjne, R1-R8 reguły, scenariusze dla każdej intencji, metryki sukcesu, sekcja 6.3 "Intencje NIEPLANOWANE".
4. **`docs/agent_system_prompt.md`** — ton agenta, wzorce odpowiedzi dla każdej intencji, banned phrases, słownik OZE slang, voice processing flow.
5. **`docs/CURRENT_STATUS.md`** — stan aktualnej sesji, task do wykonania, historia sesji, lista bugów. **Drugie co czytasz w nowej sesji.**
6. **`docs/implementation_guide_2.md`** — plan Faz 1-7 z krokami Telegram testów. **Uwaga: częściowo nieaktualne od 11.04 popołudnie** (ma baner na górze). Nie używaj do sprawdzania "co jest w MVP" — do tego jest INTENCJE_MVP.md. Używaj do kolejności implementacji konkretnych kroków, sprawdzając każdy krok przeciwko SSOT przed kodowaniem.

Dokumenty niżej w hierarchii (`poznaj_swojego_agenta_v5_FINAL.md`, stare raporty testowe, `archive/`) są **referencyjne** — nie kontraktują nic, żyją jako historia lub materiał marketingowy.

## How Sessions Work

Three roles:
- **Claude Code** (you) — implement and fix code
- **Claude Cowork** — manually tests the bot in Telegram after each session, generates test reports
- **Maan** — project owner, passes results between sessions, makes priority decisions

**Na początku każdej sesji:** przeczytaj `docs/SOURCE_OF_TRUTH.md` i `docs/CURRENT_STATUS.md` **w tej kolejności**. Pierwszy daje ci mapę decyzji produktowych i hierarchię SSOT; drugi daje ci dokładny task na tę sesję. Dopiero potem sięgaj do pozostałych plików SSOT (INTENCJE_MVP, agent_behavior_spec_v5, agent_system_prompt) wedle potrzeby zadania. **Nie zgaduj kontekstu — czytaj dokumenty.**

**Na końcu każdej sesji:** zaktualizuj `docs/CURRENT_STATUS.md` (historia sesji + status bugów + task na następną sesję). Jeśli podczas pracy znalazłeś nowe lessons learned wpływające na plan fazowy, dopisz do `docs/implementation_guide_2.md`. Jeśli decyzja produktowa — do `docs/SOURCE_OF_TRUTH.md` decision log.

## Execution Plan

Plan fazowy żyje w `docs/implementation_guide_2.md` (Fazy 1-7 z micro-krokami i manualnymi Telegram testami). **Ten plik jest częściowo nieaktualny od 11.04.2026 popołudnie** — niektóre kroki odwołują się do intencji wyciętych (reschedule_meeting, free_slots, cancel_meeting) albo do starych wzorców (`[Tak][Nie]` zamiast 3-button cards). Gdy jesteś w trakcie konkretnego kroku — zweryfikuj go najpierw przeciwko SSOT (sekcja wyżej) i jeśli jest konflikt, STOP i poinformuj Maana.

**Aktualna pozycja (stan na 11.04.2026 popołudnie):**
- **Fazy 1-3 — kod częściowo gotowy, ale spec się ruszył.** Kod bota z commita `bc765a2` był pisany przeciwko wcześniejszej wersji speca. Po synchronizacji 11.04 popołudnie wiele rzeczy w kodzie jest out-of-sync z nowym SSOT (3-button cards, R7 next_action_prompt, compound fusion, duplicate default-merge, wycięte intencje, Klimatyzacja/Negocjacje).
- **Następny krok (do potwierdzenia przez Maana):** pełny audyt kodu Python (`bot/`, `shared/`, `api/`) przeciwko zsynchronizowanym plikom SSOT. Nie zmieniać kodu. Wyprodukować `docs/CODE_AUDIT_11-04-2026.md` z tabelą rozbieżności: `plik:linia | stan kodu | stan speca | kategoria (known_bug/new_drift/aligned) | priorytet (must/should/nice) | estymata`. Dopiero po audycie i decyzji Maana wchodzimy w Fazę implementacji fixów + testy w Telegramie.

**Dokładne statusy bugów i faz** — patrz `docs/CURRENT_STATUS.md` (zawsze aktualne), a nie ten plik.

## Non-Negotiable Rules

1. **Step order is sacred.** Never skip ahead. Never start step N+1 before step N's tests pass.
2. **Commit after every step.** Message format: `"Phase X.Y: [description]"` dla kodu, `"docs: [krótki opis]"` dla dokumentacji.
3. **If a step is too large** (8+ functions, 3+ files), split it into substeps. Tell Maan the split BEFORE coding.
4. **If implementation conflicts with the guide** (library API changed, pattern doesn't work), STOP. Explain the conflict. Don't force the guide. **Konflikt SSOT vs implementation_guide_2 — wygrywa SSOT.**
5. **If unclear, ASK.** Don't guess. Don't assume. Don't invent.
6. **Before touching bot response logic, read `docs/agent_behavior_spec_v5.md` and `docs/agent_system_prompt.md` fully.** Every bot response must match the tone, format, and patterns defined there.
7. **New ideas go to backlog, not to code.** If during implementation you notice a new feature, edge case, or improvement that's NOT in the current step's scope, add it to `docs/backlog.md` as a one-line note and continue with the current step. Never implement off-plan features without explicit approval.
8. **Client identification always uses full name + city.** Never identify a client by last name alone. There will be multiple "Kowalski" clients. All examples, prompts, and search logic must use first name + last name + city.
9. **`next_action_prompt` (R7) po każdej committed mutacji.** Po zapisie `add_client` / `add_note` / `change_status` / `add_meeting` — chyba że z samej mutacji wynika wprost następny krok (np. `add_meeting` już definiuje "next contact") — agent wysyła JEDNO wolnotekstowe otwarte pytanie typu _"Co dalej z Janem Kowalskim? Spotkanie, telefon, follow-up?"_ z dostępną opcją `❌ Anuluj / nic`. **To NIE jest sztywna trójka meeting/call/not-interested** (stara wersja tej reguły z 10.04 wieczór została odwrócona 11.04 — szczegóły w `SOURCE_OF_TRUTH.md` decision log). Handlowiec odpowiada prozą; jeśli odpowiedź zawiera akcję + czas, agent parsuje jako `add_meeting` i uruchamia standardowy 3-button flow. Jeśli "nie wiem jeszcze" — zamyka flow bez wpisu.
10. **R1 jest absolutne — 3-button cards + one-click cancel.** Agent NIGDY nie pisze do Sheets / Calendar / Drive bez jawnego kliknięcia `✅ Zapisać`. Każda karta mutacyjna ma trzy przyciski: `[✅ Zapisać]` (commit), `[➕ Dopisać]` (zostaw pending otwarte, handlowiec dopisze więcej info, karta się przebuduje), `[❌ Anulować]` (jednym kliknięciem porzuca pending — żadnej pętli `Na pewno?`). Stare wzorce `[Tak][Nie]`, `[Zapisz bez]`, `[Nowy][Aktualizuj]` **przestały istnieć** — jeśli widzisz je w kodzie, to jest drift do naprawy. Karty read-only (`show_client`, `show_day_plan` bez mutacji) **nie mają przycisków** — R1 ich nie dotyczy.
11. **Każda zmiana testowana i udokumentowana.** Żadna edycja kodu nie kończy się commitem bez: (a) jasnego testu w Telegramie który Claude Code dyktuje Maanowi PRZED wdrożeniem — konkretne kroki, wiadomości do wpisania, oczekiwany efekt, co dokładnie sprawdzić w Sheets/Calendar/Drive, (b) wykonania tych testów przez Maana na realnym bocie, (c) zrzutów ekranu jako dowodu (z Telegrama + z Google), (d) zapisu wyniku testu w `docs/CURRENT_STATUS.md` w sekcji historii sesji, (e) aktualizacji statusu powiązanych bugów (✅ rozwiązany / ❌ wraca / ⚠️ częściowo). Dopiero po przejściu testu przechodzimy do kolejnego kroku. Zero domyślania się, zero "pewnie działa", zero przeskakiwania testów "bo to drobna zmiana". **Główna zasada systemu:** każda niescisłość między dokumentem, kodem i rzeczywistością jest przepytana zanim cokolwiek edytujemy. Powolutku, krok po kroku, jak woda drążąca kamień.

## Architecture Rules

| Rule | Detail |
|---|---|
| Shared services | ALL business logic in `shared/`. Bot and API import only. Zero duplication. |
| Source of truth (data) | CRM data → Google (Sheets/Calendar/Drive). System data → Supabase. Never mix. |
| No temp CRM storage | If Google API is down, inform user and wait. Never cache CRM data in Supabase. |
| Confirmation required | Agent NEVER writes to Sheets/Calendar/Drive without user confirmation (R1, 3-button card). |
| Polish language | All user-facing text and AI prompts in Polish. Code and comments in English. |
| Error messages | Always in Polish, always user-friendly, always identify source of problem. |
| No raw system data | Never expose `_row`, `_sheet_id`, Excel serial dates, or internal IDs to user. |
| Date format | Always `DD.MM.YYYY (Dzień tygodnia)` — e.g. `15.04.2026 (Środa)`. Never raw numbers. |
| Sheets schema | 16 kolumn A-P zamrożone w `INTENCJE_MVP.md` sekcja 3. Kod jest schema-agnostic (czyta nagłówki z wiersza 1), ale nowe kolumny dodajemy tylko przez zmianę tamtego kontraktu. |
| Pipeline statusów | 9 statusów (bez Negocjacji — usunięte 11.04). Lista w `INTENCJE_MVP.md` sekcja 7. `Rezygnacja z umowy` ≠ `Odrzucone` — pierwsze to klient zaangażowany który się wycofał, drugie to klient nigdy niezaangażowany. |
| Produkty | `PV` / `Pompa ciepła` / `Magazyn energii` / `PV + Magazyn energii`. **Klimatyzacja wycięta 11.04** — jeśli kod ma mapowanie na klimatyzację, to jest drift. Moc (kW/kWh) zawsze do `Notatki`, nigdy do nazwy produktu ani do osobnej kolumny. |

## Code Standards

- **Python:** type hints, docstrings, try/except with logging on all external calls
- **Async:** use `async` for Telegram handlers, Anthropic, OpenAI. Use `asyncio.to_thread()` for synchronous Google API calls.
- **Testing:** unit tests after each shared module, integration tests at phase end, manual Telegram tests per `implementation_guide_2.md` (+ weryfikacja przeciwko SSOT przed każdym krokiem)

## Key Files

```
docs/
  SOURCE_OF_TRUTH.md                 # SSOT #1 — decision log + hierarchia — READ FIRST
  INTENCJE_MVP.md                    # SSOT #2 — zamrożone kontrakty intencji, schemat Sheets, pipeline
  agent_behavior_spec_v5.md          # SSOT #3 — 52 testy akceptacyjne + R1-R8 reguły
  agent_system_prompt.md             # SSOT #4 — ton, wzorce odpowiedzi, OZE slang, voice flow
  CURRENT_STATUS.md                  # Stan sesji — READ SECOND, update at end of every session
  implementation_guide_2.md          # Plan Fazy 1-7 (PARTIALLY STALE od 11.04.2026 popołudnie — ma baner)
  backlog.md                         # Pomysły wpadające podczas implementacji, do zaplanowania później
  poznaj_swojego_agenta_v5_FINAL.md  # Marketing/onboarding dla handlowców (nie runtime — NIE czytaj dla audytu kodu)
  archive/
    OZE_Agent_Brief_v5_FINAL.md      # Historyczny brief v5 — NIE canonical, NIE czytaj dla bieżącego stanu
bot/                                 # Telegram bot (Python, Railway process 1)
api/                                 # FastAPI backend (Railway process 2)
shared/                              # Business logic (imported by bot + api + scheduler)
tests/                               # pytest
dashboard/                           # Next.js frontend (later phase, nie ruszamy w MVP)
admin/                               # Next.js admin panel (later phase, nie ruszamy w MVP)
```

## Tech Stack

- Python 3.13.12, python-telegram-bot 21.x, FastAPI, APScheduler
- Claude Sonnet 4.6 (complex tasks) + Claude Haiku 4.5 (simple tasks)
- Whisper API (speech-to-text, Polish)
- Supabase (PostgreSQL — auth, billing, logs, settings)
- Google Sheets API v4, Calendar API v3, Drive API v3
- Next.js 14, shadcn/ui, Tailwind CSS (dashboard — later phase)

## Known Tradeoffs (accepted for MVP)

- Scheduler runs in-process with bot (restart = lost in-memory dedup state)
- No auto-retry on Google API failure (user retries manually)
- Supabase free tier (500MB, no daily backups — fine for beta)
- Google OAuth in "testing" mode (max 100 users)
- Version ranges in requirements.txt — let pip resolve, adjust if conflicts

## What to Read Before Starting (kolejność obowiązkowa)

1. **`docs/SOURCE_OF_TRUTH.md`** — hierarchia SSOT + decision log. Daje ci mapę wszystkich decyzji produktowych i kolejność czytania reszty. Od tego zaczynasz zawsze.
2. **`docs/CURRENT_STATUS.md`** — dokładny task na tę sesję + stan bugów + historia poprzednich sesji.
3. Jeśli task dotyczy **intencji lub schematu danych**: czytaj `docs/INTENCJE_MVP.md` (sekcja odpowiadająca intencji).
4. Jeśli task dotyczy **logiki odpowiedzi bota lub testów**: czytaj `docs/agent_behavior_spec_v5.md` + `docs/agent_system_prompt.md` w całości. Nie skrótami — to nie jest plik referencyjny, to kontrakt.
5. Jeśli task dotyczy **kolejności implementacji fazy**: czytaj `docs/implementation_guide_2.md` — ale pamiętaj o banerze "partially stale" i weryfikuj każdy krok przeciwko SSOT (pkt 1-4 wyżej) przed kodowaniem.
6. Jeśli nie wiesz od jakiej fazy/kroku zaczynać — zapytaj Maana przed ruszeniem. Nie zgaduj.
