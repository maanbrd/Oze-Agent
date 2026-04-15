# OZE-Agent — Phase 3 Audit + Implementation Plan (Intent Router Rewrite)

_Last updated: 15.04.2026_

## Context

Phase 2 Behavior Contract Freeze domknięta (9/9 decyzji, commits `65b5661`, `117f9c2`). Drift reconcile #1 (`02eb94e`) i #2 (`c32fbe6`) spójne z 4-tier scope model (MVP / POST-MVP roadmap / VISION_ONLY / NIEPLANOWANE).

Ten dokument = **audit + file-level implementation plan** dla Phase 3 Intent Router Rewrite. Python kod **nie jest w scope** tego dokumentu — deliverable jest plan. Implementacja startuje osobnymi commitami po akceptacji.

**Phase 3 Goal** (per `IMPLEMENTATION_PLAN.md` Phase 3): Czysty klasyfikator intentów z structured output (tool-use), rozróżnia 6 MVP intencji + `general_question` catch-all; out-of-MVP intencje (POST-MVP roadmap / VISION_ONLY / NIEPLANOWANE) klasyfikowane z odpowiednio różnymi reply templates.

Scope-tier drift grep (per `feedback_scope_tier_drift_check.md`): **zero hits** w active docs → Phase 3 startuje bez drift ryzyka.

---

## 1. Audit `shared/claude_ai.py` (557 LoC)

Plik: [oze-agent/shared/claude_ai.py](oze-agent/shared/claude_ai.py)

### KEEP as transport (no change in Phase 3)

| Fragment | LoC | Rationale |
|---|---|---|
| `MODEL_COMPLEX`, `MODEL_SIMPLE` | 21-22 | Model routing config. Stable. |
| `COST_PER_MTOK_IN/OUT` | 25-26 | Cost tracking. Stable. |
| `call_claude(system, user, model_type, max_tokens)` | 42-78 | Raw LLM call + usage stats + graceful error handling. Generic transport. |
| `call_claude_with_tools(system, user, tools, model_type)` | 84-136 | Tool-use transport. **Fundament Phase 3 routera.** |

Te 4 elementy **pozostają w obecnej lokalizacji** w Phase 3.

**Świadome odstępstwo od Phase 1 audit rekomendacji:** [PHASE1_AUDIT.md:622](PHASE1_AUDIT.md#L622) rekomendował split do `shared/ai/transport.py`. Phase 3 świadomie tego **nie wykonuje** — Phase 3 ma już duży zakres zmian (nowy `shared/intent/` moduł, schemas, router integration, `bot/handlers/banners.py` wydzielenie, tests). Transport split bez wartości dodanej dla router rewrite; housekeeping dla Phase 4+ backlog.

### REWRITE in Phase 3 (behavior → `shared/intent/`)

| Fragment | LoC | What |
|---|---|---|
| `VALID_INTENTS` set | 28-36 | **Replace** z `IntentType` enum z jawnym scope tier. Obecna lista miesza MVP (6), POST-MVP (3: `edit_client`, `filtruj_klientów`, `lejek_sprzedazowy`), utility (`assign_photo`, `refresh_columns`), flow control (`confirm_yes`, `confirm_no`, `cancel_flow`) — poza 4-tier scope model per SSOT §4. |
| `classify_intent(message, context)` | 199-288 | **Full rewrite.** 70+ linii system prompta inline; JSON-in-text z kruchym ``` stripowaniem; POST-MVP/utility intencje na równi z MVP; `context[-3:]` ignoruje D6 30-min window (brak `since` param). **Stara terminologia `R4 merge`** w prompcie ([line 253](../oze-agent/shared/claude_ai.py#L253)) — zastąpić `[Nowy]` / `[Aktualizuj]` routing terminology per `INTENCJE_MVP.md` §5.3 (Phase 1 audit blocker #3). |

### REWRITE in Phase 5 (extraction — poza Phase 3)

| Fragment | LoC | Note |
|---|---|---|
| `extract_client_data(message, user_columns)` | 294-351 | Inline prompt + JSON-in-text. Phase 5 → `shared/extraction/`. |
| `extract_meeting_data(message, today)` | 357-401 | **Produkuje `meetings: [...]` list** — multi-meeting pipeline. Per D5 multi-meeting rejectuje router → Phase 5 extraction wspiera tylko single meeting. |
| `extract_note_data(message)` | 407-440 | Phase 5 refactor jako tool-use. |

### REWRITE in Phase 6 (proactive — poza Phase 3)

| Fragment | LoC | Note |
|---|---|---|
| `format_morning_brief(events, followups, pipeline_stats)` | 517-557 | **Violates 13.04 decision** — przyjmuje `pipeline_stats` + używa 📊 emoji. Per `INTENCJE_MVP.md` §4.6 morning brief = meetings + follow-ups, no pipeline stats. Phase 6 rewrite. |
| `parse_followup_response(...)` | 463-511 | Evening follow-up parser. Phase 6 review. |

### REMOVE from router callsite (per D5)

| Fragment | LoC | Note |
|---|---|---|
| `parse_voice_note(transcription, ...)` | 142-193 | Voice = POST-MVP stub per D5. Router **nie importuje**. Funkcja zostaje w repo jako legacy reference; brak wywołań z MVP code path. |

### Separate path — `refresh_columns` as Telegram command (not router intent)

| Fragment | LoC | Decision |
|---|---|---|
| `handle_refresh_columns` | [text.py:1722-1736](../oze-agent/bot/handlers/text.py#L1722) | **Keep as functional handler, poza routerem.** Migruje na dedykowaną komendę Telegram: `/odswiez_kolumny` (główna) + opcjonalny alias `/refresh_columns`. Router **nie klasyfikuje** `refresh_columns` — to technical cache refresh (Sheets headers → Supabase), nie conversational NLU intent. |

**Rationale:**

- Functionalność (refresh Sheets column cache) jest fizycznie potrzebna w MVP — gdy user ręcznie dodaje kolumnę do Sheets, agent musi ją zobaczyć.
- SSOT §4 `elastyczne kolumny arkusza / refresh kolumn` (vision-only) = produktowa funkcja UI customization, nie technical cache plumbing. Dwa różne wymiary — rozdzielamy.
- Router NLU scope obejmuje **conversational intents**. Technical commands (`/start`, `/help`, `/odswiez_kolumny`) siedzą w Telegram CommandHandler, nie w NLU pipeline.
- Jeśli user napisze naturalnie "odśwież kolumny" → router klasyfikuje jako `GENERAL_QUESTION`; reply pointer: "Użyj komendy `/odswiez_kolumny`."

**Integration impact:**

- `bot/main.py`: dodać `CommandHandler("odswiez_kolumny", handle_refresh_columns)` + opcjonalny alias `CommandHandler("refresh_columns", handle_refresh_columns)`.
- `bot/handlers/text.py` handler map: **usunąć** entry `"refresh_columns": handle_refresh_columns`.
- `shared/intent/schemas.py`: `refresh_columns` **nie jest** w żadnej schema (ani MVP intent, ani out-of-scope feature_key).
- Tests: `test_router_refresh_columns_not_an_intent` (schema introspection — `refresh_columns` nie występuje nigdzie w tools) + `test_refresh_columns_is_telegram_command` (`bot/main.py` rejestruje CommandHandler). Obie w §7.

### Thin wrapper — Phase 3 keep

| Fragment | LoC | Note |
|---|---|---|
| `generate_bot_response(system_context, user, history)` | 446-457 | 11-liniowy shim nad `call_claude` z heurystyką "history > 4 → complex". Phase 3 używa dla `GENERAL_QUESTION` replies. Keep as-is; Phase 5/6 zrewiduje. **Świadome odstępstwo od Phase 1 audit rekomendacji** ([PHASE1_AUDIT.md:608](PHASE1_AUDIT.md#L608) klasyfikował jako Phase 3 → `shared/prompts/`) — pragmatyzm: jedno-użytkowy shim nie wymaga własnego modułu teraz, cleanup razem z pozostałym `claude_ai.py` behavior pieces w Phase 5/6. |

---

## 2. `shared/intent/` module layout

```
oze-agent/shared/intent/
  __init__.py              # public API: classify() + IntentType + ScopeTier + IntentResult
  router.py                # classify(message, user_id) -> IntentResult
  intents.py               # IntentType enum + ScopeTier enum + IntentResult dataclass
  schemas.py               # anthropic tool-use definitions
  prompts.py               # system prompt builder (no 70-liniowe inline strings)
  replies/
    __init__.py
    out_of_scope.py        # PL templates per feature_key (post_mvp_roadmap / vision_only / unplanned)
    multi_meeting.py       # PL template: "jedno spotkanie naraz"
```

### Public API

```python
from shared.intent import classify, IntentType, ScopeTier, IntentResult
```

### `IntentType` enum

```python
class IntentType(str, Enum):
    # 6 MVP (mutating + read)
    ADD_CLIENT = "add_client"
    SHOW_CLIENT = "show_client"
    ADD_NOTE = "add_note"
    CHANGE_STATUS = "change_status"
    ADD_MEETING = "add_meeting"
    SHOW_DAY_PLAN = "show_day_plan"
    # catch-all
    GENERAL_QUESTION = "general_question"
    # out-of-scope markers (classified, not mutated)
    POST_MVP_ROADMAP = "post_mvp_roadmap"
    VISION_ONLY = "vision_only"
    UNPLANNED = "unplanned"
    # D5 rejection
    MULTI_MEETING = "multi_meeting"
```

**No `REFRESH_COLUMNS` as router intent.** Router has ONLY 6 MVP + `GENERAL_QUESTION` + out-of-scope markers + `MULTI_MEETING`. **`refresh_columns` jest Telegram command (`/odswiez_kolumny`), poza NLU routerem** — szczegóły w §1 "Separate path". Nie jest MVP intent, nie jest VISION_ONLY feature_key, nie jest nigdzie w schemach routera.

`flexible columns` / UI customization kolumn (SSOT §4 vision-only) to **inna funkcja niż technical cache refresh** — pozostają vision-only w katalogu `feature_key` (§3).

### `ScopeTier` enum

```python
class ScopeTier(str, Enum):
    MVP = "mvp"
    POST_MVP_ROADMAP = "post_mvp_roadmap"
    VISION_ONLY = "vision_only"
    UNPLANNED = "unplanned"
    REJECTED = "rejected"          # multi-meeting, malformed tool-use
```

### `IntentResult` dataclass

```python
@dataclass
class IntentResult:
    intent: IntentType
    scope_tier: ScopeTier
    entities: dict
    confidence: float
    feature_key: str | None = None   # stable identifier for out-of-scope replies
                                      # e.g. "edit_client", "photo_upload", "voice_input",
                                      #      "reschedule_meeting", "cancel_meeting",
                                      #      "free_slots", "delete_client",
                                      #      "flexible_columns", "pre_meeting_reminders"
    reason: str | None = None        # short rationale from model (debug / logs / tests)
    model: str | None = None         # model name used for classification — feeds
                                      # increment_interaction instead of hardcoded string
```

---

## 3. Structured output contract (tool-use, not JSON-in-text)

Router wywołuje `call_claude_with_tools(...)` z zestawem tools. Model wybiera **dokładnie jeden** tool call.

### Tool schemas per intent

| Tool name | Required | Optional | Enum constraints |
|---|---|---|---|
| `record_add_client` | `name` | `city`, `phone`, `product`, `notes` | — |
| `record_show_client` | — (≥1 z poniższych) | `name`, `city`, `phone` | — |
| `record_add_note` | `client_name`, `note` | `city` | — |
| `record_change_status` | `client_name`, `status` | `city` | `status` = 9 pipeline statuses per `INTENCJE_MVP.md` §6 (`Nowy lead`, `Spotkanie umówione`, `Spotkanie odbyte`, `Oferta wysłana`, `Podpisane`, `Zamontowana`, `Rezygnacja z umowy`, `Nieaktywny`, `Odrzucone`) |
| `record_add_meeting` | `client_name`, `date_iso`, `event_type` | `time`, `duration_minutes`, `location` | `event_type` = D4 runtime enum: `in_person`, `phone_call`, `offer_email`, `doc_followup` |
| `record_show_day_plan` | — | `date_iso` | — |
| `record_general_question` | — | `reason` | — |
| `record_out_of_scope` | `category`, `feature_key` | `details` | `category` = `post_mvp_roadmap` / `vision_only` / `unplanned`. `feature_key` = stable identifier z catalog below. |
| `record_multi_meeting_rejection` | `meeting_count` | — | `meeting_count >= 2` |

### `feature_key` catalog (dla `record_out_of_scope`)

Stabilne wartości które propaguje się do `IntentResult.feature_key` i sterują reply template:

**POST-MVP roadmap** (`category=post_mvp_roadmap`):
- `edit_client`, `filter_clients`, `pipeline_dashboard`, `multi_meeting` (gdy model pominął rejection tool), `voice_input`, `photo_upload`, `csv_import`, `full_dashboard`.

**VISION_ONLY** (`category=vision_only`, wymaga osobnej decyzji Maana):
- `reschedule_meeting`, `cancel_meeting`, `free_slots`, `delete_client`, `habit_learning`, `flexible_columns`.
- **NIE**: `refresh_columns` — to jest technical cache refresh (Telegram `/odswiez_kolumny` command, nie router intent; per §1 "Separate path"). `flexible_columns` (UI customization of column layout) to osobny vision-only wymiar.
- **NIE**: `daily_interaction_limit` — policy/business mechanic, nie router intent (per INTENCJE §8.2 reconcile #2).

**UNPLANNED** (`category=unplanned`, permanently out of scope):
- `pre_meeting_reminders` (agent-side), `meeting_non_working_day_warning`.

### Phase 2 alignment

- **D4 alignment:** `record_add_meeting.event_type` enum = dokładnie 4 runtime English codes. Sheets K label mapping robi Phase 5 mutation pipeline.
- **D1 alignment:** `date_iso` przyjmuje ISO string (`YYYY-MM-DD` albo `YYYY-MM-DDTHH:MM:SS+HH:MM`). Router nie renderuje PL — to Phase 5 formatter layer.
- **D5 multi-meeting:** **Primary source of truth = tool-use output** (`record_multi_meeting_rejection`). Regex pre-check / post-call sanity (np. `\bi\s+(?:do|z|ze?)\b`, "dwa spotkania", "dwoje klientów") może istnieć jako **safety net**, **nie jest kontraktem**. Jeśli regex matches ale model wybrał `record_add_meeting` (single) → wynik = single meeting (tool-use wygrywa).
- **D5 voice/photo:** Router nigdy nie widzi voice/photo messages — Telegram stub je przejmuje w `bot/main.py` przed routerem.
- **D7-D9:** enum values routera (status, event_type) aligned z INTENCJE_MVP — brak bezpośredniego kontaktu z D7-D9, ale implementacja zobaczy je przez schemy.

### Text fallback

Jeśli model wróci text zamiast tool call → `IntentResult(intent=GENERAL_QUESTION, scope_tier=MVP, entities={}, confidence=0.0, model=<model_name>)`. Brak parsowania textu.

### API error

API exception → `logger.error` + `IntentResult(intent=GENERAL_QUESTION, scope_tier=MVP, entities={}, confidence=0.0, model=<model_name>)`. Spójne z "wrapper nie rzuca" per D2 / Phase 1 audit.

---

## 4. D6 history window integration

**Router owns history fetch** — caller nie musi pamiętać o `since`.

```python
# shared/intent/router.py
from datetime import timedelta
from shared.database import get_conversation_history

HISTORY_WINDOW = timedelta(minutes=30)

async def classify(message: str, telegram_id: int) -> IntentResult:
    history = get_conversation_history(
        telegram_id=telegram_id,
        limit=5,
        since=HISTORY_WINDOW,   # D6 mandate
    )
    # build prompt (shared/intent/prompts.py)
    # call_claude_with_tools(system=..., user=message, tools=...)
    # parse tool_use response → IntentResult
    ...
```

Naming: `telegram_id` konsystentnie z `get_conversation_history` wrapper signature i resztą `bot/handlers/text.py`. Minimalizuje mental load przy integracji.

### Pre-work dependency

`shared/database.py::get_conversation_history` wymaga uzupełnienia o `since: timedelta | None = None` param per D6. To jest **single-file infrastructure fix, nie pełen rewrite** — osobny mały commit przed Phase 3 router code.

### Call-site update

`bot/handlers/text.py:168` — linia `history = get_conversation_history(telegram_id, limit=3)` → **usunąć** (router owns fetch).
`bot/handlers/text.py:171` — `classify_intent(message_text, history)` → `shared.intent.router.classify(message_text, telegram_id=telegram_id)`.

---

## 5. Integration point: `bot/handlers/text.py`

Plik: [oze-agent/bot/handlers/text.py](oze-agent/bot/handlers/text.py)

### Minimalne zmiany w Phase 3

1. **Import swap** (l. 29-36):
   - Remove: `from shared.claude_ai import classify_intent`.
   - Add: `from shared.intent import classify, IntentType, ScopeTier, IntentResult`.
   - `call_claude_with_tools`, `extract_*`, `generate_bot_response` pozostają (Phase 5 mutation handlers jeszcze ich używają).

2. **History fetch** (l. 168): usunąć — router owns.

3. **Classify call** (l. 171): `intent_data = await classify_intent(...)` → `result = await classify(message_text, telegram_id=telegram_id)`.

4. **Post-classification guards** (l. 174-190):
   - Preliminary recommendation: **usunąć oba guards** (low-confidence reclassify + add_meeting temporal heuristic). Tool-use classifier + scope tier model są stabilniejsze niż JSON-in-text; guards były band-aidem dla kruchego klasyfikatora.
   - Jeśli post-deploy regresja → guards wracają **jako router-internal post-processing**, udokumentowane w komentarzu `router.py`.
   - Decision recorded here żeby review łapał gdyby wracały bez uzasadnienia.

5. **Handler map** (l. 193-213) — restructure for scope tiers.

   **Key migration:** obecna mapa używa **string keys** (`"add_client": handle_add_client`). Phase 3 migruje na `IntentType` enum members. Route lookup staje się `handlers.get(result.intent, handle_general)`.

   ```python
   handlers = {
       # 6 MVP (existing handlers — no signature change)
       IntentType.ADD_CLIENT:       handle_add_client,
       IntentType.SHOW_CLIENT:      handle_search_client,
       IntentType.ADD_NOTE:         handle_add_note,
       IntentType.CHANGE_STATUS:    handle_change_status,
       IntentType.ADD_MEETING:      handle_add_meeting,
       IntentType.SHOW_DAY_PLAN:    handle_show_day_plan,
       # Out-of-scope banners (use result.feature_key to pick reply)
       IntentType.POST_MVP_ROADMAP: handle_post_mvp_banner,
       IntentType.VISION_ONLY:      handle_vision_only_banner,      # NEW (Phase 3)
       IntentType.UNPLANNED:        handle_unplanned_banner,         # NEW (Phase 3)
       # D5 rejection
       IntentType.MULTI_MEETING:    handle_multi_meeting_rejection,  # NEW (Phase 3)
       # Catch-all
       IntentType.GENERAL_QUESTION: handle_general,
   }
   ```

   **Banner handlers lokalizacja:** utworzyć nowy plik `bot/handlers/banners.py` jako konsolidację out-of-scope banner handlerów:

   - Przenieść `handle_post_mvp_banner` z `text.py:394` → `banners.py`.
   - Dodać nowe: `handle_vision_only_banner`, `handle_unplanned_banner`, `handle_multi_meeting_rejection`.
   - Wszystkie = thin wrappery wołające templates z `shared/intent/replies/`. Reply wybierany przez `result.feature_key`.
   - `text.py` importuje z `banners`. Uzasadnienie: `text.py` już ma 1700+ linii; 4 banner handlery warte osobnego pliku i logicznej grupy.

   **Usuwane z handler map:**

   - `"edit_client"`, `"filtruj_klientów"`, `"lejek_sprzedazowy"`, `"assign_photo"` — router klasyfikuje jako `POST_MVP_ROADMAP` z właściwym `feature_key`.
   - `"refresh_columns"` — **nie jest routowane przez NLU**. Migruje na Telegram command `/odswiez_kolumny` rejestrowany w `bot/main.py` (patrz §1 "Separate path"). Handler `handle_refresh_columns` zostaje funkcjonalny, tylko path się zmienia.

   **Pozostają w mapie** (legacy stubs do Phase 4):

   - `"confirm_yes"`, `"confirm_no"`, `"cancel_flow"` — router ich nie zwraca; pending flow (`_route_pending_flow` l. 160-164) przejmuje przed klasyfikacją. Phase 4 cleanup.

6. **`increment_interaction` call** (l. 218+): replace hardcoded `claude-haiku-4-5-20251001` z `result.model` (z `IntentResult`).

---

## 6. Zero-touch in Phase 3 (explicit)

Phase 3 **nie tworzy** i **nie dotyka**:

- `shared/mutations/`, `shared/clients/`, `shared/extraction/` — Phase 5 scope.
- `shared/pending/`, `shared/cards/` — Phase 4 scope.
- `shared/scheduler/`, `format_morning_brief` rewrite — Phase 6 scope (znany drift flagowany, nie fixowany).
- `parse_voice_note`, `shared/whisper_stt.py` — nie wołane z routera; stub per D5 w `bot/main.py` (Phase 4 implementation).
- `claude_ai.py::classify_intent` — **nie usuwamy** w Phase 3. Zostaje jako dead code do cleanup w Phase 4 (razem z legacy handler map sunset).
- `shared/ai/transport.py` split — deferred (patrz §1 KEEP note); Phase 4+ housekeeping backlog.

## 6b. Telegram command registration (Phase 3 scope)

Poza NLU routerem, Phase 3 **rejestruje w `bot/main.py`**:

- `CommandHandler("odswiez_kolumny", handle_refresh_columns)` — główna komenda technical cache refresh (per §1 "Separate path").
- Opcjonalnie alias `CommandHandler("refresh_columns", handle_refresh_columns)` — English alias dla dev wygody.

Handler body (`handle_refresh_columns` w `bot/handlers/text.py:1722`) bez zmian — już funkcjonalny, tylko entry point się zmienia z NLU na CommandHandler.

---

## 7. Tests (before router implementation)

Location: `oze-agent/tests/intent/` (new directory).

| Test | Verifies |
|---|---|
| `test_router_classify_mvp_intents.py` | 6 happy-path scenariuszy — per MVP intent, mock tool-use response, assertion `IntentResult.intent == expected` + `scope_tier=MVP`. |
| `test_router_classify_post_mvp_roadmap.py` | Mock `record_out_of_scope(category=post_mvp_roadmap, feature_key=edit_client)` → `IntentType.POST_MVP_ROADMAP`, `feature_key="edit_client"`. |
| `test_router_classify_vision_only.py` | Message "przełóż spotkanie z Kowalskim" → mock `record_out_of_scope(category=vision_only, feature_key=reschedule_meeting)` → `IntentType.VISION_ONLY`, `feature_key="reschedule_meeting"`. |
| `test_router_classify_unplanned.py` | Message "ustaw przypomnienie 30 min przed spotkaniem" → `record_out_of_scope(category=unplanned, feature_key=pre_meeting_reminders)` → `IntentType.UNPLANNED`. |
| `test_router_refresh_columns_not_an_intent.py` | Message "odśwież kolumny" → router klasyfikuje jako `GENERAL_QUESTION`; router schemas introspection potwierdza że `refresh_columns` **nie jest** w żadnym tool (ani MVP intent, ani out-of-scope `feature_key`, ani `record_out_of_scope.feature_key` enum). |
| `test_refresh_columns_is_telegram_command.py` | `bot/main.py` rejestruje `CommandHandler("odswiez_kolumny", ...)`. Wywołanie komendy przez Telegram dispatch wywołuje `handle_refresh_columns` (z `bot/handlers/text.py:1722`). |
| `test_router_classify_multi_meeting_rejection.py` | Message "spotkanie z Kowalskim jutro 10 i z Nowakiem pojutrze 14" → mock `record_multi_meeting_rejection` → `IntentType.MULTI_MEETING`, `scope_tier=REJECTED`. |
| `test_router_multi_meeting_tool_wins_over_regex.py` | Regex pre-check matches "spotkanie jutro i notatka" (false positive) ale model wybiera `record_add_meeting` (single) → wynik = single add_meeting. Regex nie jest kontraktem. |
| `test_router_uses_30min_history_window.py` | Mock `get_conversation_history`; assertion że router woła z `since=timedelta(minutes=30)` i passes `user_id` z parametru. |
| `test_router_event_type_enum_matches_d4.py` | Schema `record_add_meeting.event_type` enum == `{"in_person", "phone_call", "offer_email", "doc_followup"}`. |
| `test_router_status_enum_matches_intencje.py` | Schema `record_change_status.status` enum == 9 pipeline statuses (canonical set per INTENCJE §6). |
| `test_router_text_fallback_returns_general.py` | Model returns text instead of tool call → `IntentResult(intent=GENERAL_QUESTION, confidence=0.0)`. |
| `test_router_api_error_returns_general.py` | API exception → graceful `GENERAL_QUESTION`, no crash. |
| `test_router_no_voice_photo_tool_schemas.py` | Router tools list nie zawiera żadnego schema dla voice / photo / image-document (introspection check on `schemas.py`). |
| `test_router_intent_result_fields.py` | Każdy `IntentResult` ma `model` wypełniony; `feature_key` wypełniony dla out-of-scope i None dla MVP; `reason` może być None ale nie crashuje. |
| `test_scope_tier_mapping_exhaustive.py` | Każda wartość `IntentType` ma jednoznaczne mapowanie na `ScopeTier` (via table / match statement). |
| `test_out_of_scope_replies_polish.py` | Reply templates w `shared/intent/replies/out_of_scope.py` są w języku polskim; per `feature_key` wybiera różny tone: POST-MVP ("będzie później"), VISION_ONLY ("poza aktualnym zakresem; wymaga osobnej decyzji"), UNPLANNED ("natywna alternatywa w Google Calendar"). |
| `test_multi_meeting_reply_polish.py` | `shared/intent/replies/multi_meeting.py` zwraca PL prośbę o jedno spotkanie naraz. |

Legacy `oze-agent/tests/test_claude_ai.py` (tests 83-115 dla `classify_intent`) — **zostaje** w Phase 3 (stary kod jeszcze żyje jako dead code); Phase 4 cleanup pass usuwa razem z funkcją.

---

## 8. Pre-work (blocker before router code)

One single-file infrastructure change przed kodowaniem routera:

- **`shared/database.py::get_conversation_history`** — add `since: timedelta | None = None` param per D6. Filter implementation: if `since` podane, wrapper wyklucza rekordy starsze niż `now_utc - since`, z UTC-aware comparison (spójnie z D2 / D6 `since` contract). Default `None` = raw behavior (back-compat dla istniejących call-sites).
- One test dodany: `test_get_history_with_since_filter`.
- Osobny mały commit przed Phase 3 router code.

---

## 9. Implementation sequence (po approval tego dokumentu)

1. **Commit: `docs: add phase 3 intent router audit`** — ten dokument.
2. **Commit: `feat: database get_conversation_history since param (D6)`** — pre-work.
3. **Commit: `feat: shared/intent module + unit tests`** — core router per sekcja 2-4 **razem z** tests z sekcja 7. Tests and implementation in one commit → every commit green, main zawsze stabilny.
4. **Commit: `feat: bot/handlers/banners.py + out-of-scope + multi-meeting reply templates`** — `shared/intent/replies/*` + przenieść `handle_post_mvp_banner` z `text.py` + dodać `handle_vision_only_banner`, `handle_unplanned_banner`, `handle_multi_meeting_rejection`.
5. **Commit: `refactor: bot wired to shared.intent.classify + /odswiez_kolumny command`** — `bot/handlers/text.py` integration per sekcja 5 + `bot/main.py` CommandHandler registration per §6b. Legacy `classify_intent` pozostaje dead code (cleanup Phase 4).

Each commit small, testable, independently reviewable. Every commit leaves main green (tests + impl together).

---

## 10. Risks / open questions

- **Polish LLM performance with tool-use:** classifier ma rozpoznać polskie idiomaty i potoczne wyrażenia. W Phase 1 audit `classify_intent` używa Claude Haiku 4.5 (`model_type="simple"`) — ten model bywa zawodny z complex polish semantics. Open question: czy router używa `simple` (tańszy) czy `complex` (Sonnet, precyzyjniejszy). Recommendation: **start with `simple`** (spójnie z obecnym use case), measure false-classification rate po rollout, eskaluj do `complex` jeśli trzeba. Metric capture via `IntentResult.model` + interaction tracking.
- **Multi-meeting edge cases:** "spotkanie z Kowalskim i Nowakiem jutro" (dwóch klientów, jedno spotkanie — carpool / group meeting) vs "spotkanie z Kowalskim jutro i z Nowakiem pojutrze" (dwa osobne). Router powinien poradzić sobie z tool-use selection; regex safety net mógłby false-positive. Test coverage explicit.
- **`feature_key` drift risk:** jeśli SSOT §4 dodaje nowy vision-only item a `feature_key` catalog w schemach routera nie aktualizowany → model nie ma gdzie go przyporządkować i fallback'uje do `general_question`. Mitigation: Phase 4 cleanup pass dodaje `test_feature_key_catalog_matches_ssot.py` (TODO w backlogu).

---

## 11. Summary

- Router rewrite respektuje Phase 2 kontrakty (D1, D4, D5, D6, D9 via DEFAULT_TIMEZONE).
- Zero Python edits w tym dokumencie.
- 5 commits planowane sequentially (audit doc + pre-work + router+tests + banners+replies + integration+command). Every commit green (tests + impl together).
- `refresh_columns` migruje z NLU intent na Telegram command `/odswiez_kolumny` (świadomy split technical vs conversational).
- Legacy `classify_intent` dead code do cleanup w Phase 4.
- Post-classification guards removed by default, documented as router-internal fallback option.
- Świadome odstępstwa od Phase 1 audit zapisane jawnie (transport split defer + `generate_bot_response` keep) z uzasadnieniem pragmatyzmu.

**Deliverable tego dokumentu:** commit `docs: add phase 3 intent router audit` z tym plikiem. Implementacja Phase 3 w kolejnych commitach po approval.
