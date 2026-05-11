# Plan — naprawa Supabase user mappingu dla E2E (telegram_id=1690210103)

_Data: 29.04.2026_
_Kontekst: smoke run 29.04 dał 36 blockerów, wszystkie z jednym root cause: `no Supabase user found for telegram_id=1690210103`._

## Diagnoza (z lektury kodu)

`oze-agent/tests_e2e/run_mcp_server.sh` przy starcie ładuje **tylko** `oze-agent/tests_e2e/.env`:

```sh
if [[ -f "tests_e2e/.env" ]]; then
    set -a
    source "tests_e2e/.env"
    set +a
fi
```

`oze-agent/tests_e2e/.env.example` deklaruje **5 zmiennych** (TELEGRAM_E2E_API_ID, TELEGRAM_E2E_API_HASH, TELEGRAM_E2E_BOT_USERNAME, TELEGRAM_E2E_ADMIN_ID, TELEGRAM_E2E_SESSION) plus opcjonalnie TELEGRAM_E2E_SUPABASE_USER_ID. **Nie deklaruje** `SUPABASE_URL` ani `SUPABASE_SERVICE_KEY`.

Lokalny `oze-agent/tests_e2e/.env` (sprawdzony, redacted) ma faktycznie **tylko** te 5 telegramowych zmiennych — bez Supabase.

Stos wywołań przy `e2e_seed_fixtures`:

1. [tests_e2e/fixtures.py:94](oze-agent/tests_e2e/fixtures.py#L94) → `resolve_user_id(telegram_id)`
2. [tests_e2e/sheets_verify.py:49](oze-agent/tests_e2e/sheets_verify.py#L49) → `get_user_by_telegram_id(telegram_id)`
3. [shared/database.py:30](oze-agent/shared/database.py#L30) → tworzy klienta przez `Config.SUPABASE_URL` / `Config.SUPABASE_SERVICE_KEY`
4. [bot/config.py:47-49](oze-agent/bot/config.py#L47-L49) → czyta `os.getenv("SUPABASE_URL", "")` / `os.getenv("SUPABASE_SERVICE_KEY", "")`

Skoro w env MCP-a tych zmiennych nie ma, to `Config.SUPABASE_URL = ""`. Klient Supabase startuje z pustym URL, każde zapytanie pada — i wraca `None`. Stąd `no Supabase user found` dla **każdego** telegram_id, nie tylko 1690210103.

Bot na Railway działa, bo Railway dostarcza Supabase env w runtime — to inny proces, inny env.

To znaczy: **user 1690210103 prawie na pewno istnieje w prod Supabase**. Bot ma do niego dostęp i pisze do jego Sheets/Calendar (widać po replyach `✅ Zapisane`). Tylko warstwa weryfikacji testowej nie czyta z tej samej bazy.

## Trzy opcje naprawy

### Opcja A — `railway run` wrapper (rekomendowane)

Owinąć start MCP-a w `railway run` z prod env. Sekrety prod nie lądują na dysku — zgodnie z [CLAUDE.md → Local Development → secrets](CLAUDE.md):

> Lokalny `oze-agent/.env` został usunięty 26.04.2026 (Phase 0.8 cleanup). Sekrety produkcyjne żyją wyłącznie w Railway env vars.

**Zmiana:** `oze-agent/tests_e2e/run_mcp_server.sh` startuje:

```sh
exec railway run --service bot --environment production -- ".venv/bin/python" -m tests_e2e.mcp_server "$@"
```

`tests_e2e/.env` zostaje jak jest (Telethon-only). Railway dosypuje `SUPABASE_URL` + `SUPABASE_SERVICE_KEY` w runtime.

**Plusy:** spójne z polityką "no prod secrets on disk", action-at-a-distance zero.
**Minusy:** wymaga zalogowanego `railway` CLI w środowisku gdzie odpalany jest MCP. Pierwsze uruchomienie przy braku loginu da błąd. MCP musi mieć dostęp do internetu żeby Railway pobrał env.

### Opcja B — dopisać Supabase do `tests_e2e/.env`

Skopiować `SUPABASE_URL` + `SUPABASE_SERVICE_KEY` z Railway prod do `tests_e2e/.env`.

**Plusy:** jeden plik, brak dependency na `railway` CLI, MCP działa offline.
**Minusy:** sekrety prod siedzą lokalnie (chociaż `tests_e2e/.env` jest gitignored). Łamie zasadę "secrets only in Railway".

### Opcja C — override UUID

Ustawić `TELEGRAM_E2E_SUPABASE_USER_ID=<uuid>` w `tests_e2e/.env`. Kod już to wspiera ([sheets_verify.py:30-40](oze-agent/tests_e2e/sheets_verify.py#L30-L40)).

**Plusy:** zero zmian w infrastrukturze.
**Minusy:** to jednorazowy bypass dla jednego usera — działa tylko gdy znamy UUID. Plus dalej i tak `Config.SUPABASE_URL` jest pusty, więc `add_client` / `get_all_clients` wywołane z UUID i tak padną w sheets/calendar wrapperach przy próbie odczytu profilu klienta. Override tylko skraca pierwszy lookup, nie naprawia całej ścieżki.

## Rekomendacja

**Opcja A.** B i C nie naprawiają w pełni — A jest jedynym rozwiązaniem trwałym i zgodnym z polityką sekretów.

## Plan wykonania

### Krok 1 — potwierdzić, że user 1690210103 istnieje w prod Supabase

```bash
railway run --service bot --environment production python -c \
  "from shared.database import get_user_by_telegram_id; \
   u = get_user_by_telegram_id(1690210103); \
   print(u and {'id': u['id'], 'telegram_id': u['telegram_id']})"
```

Oczekiwane: dict z `id` (UUID) i `telegram_id=1690210103`.

Jeśli `None` — user fizycznie nie istnieje, krok 1b: stworzyć przez normalny flow (handlowiec ręcznie paruje konto przez bota albo przez SQL na Supabase). Bez usera nie ma sensu kontynuować planu.

### Krok 2 — zmodyfikować `run_mcp_server.sh`

Edytuj [oze-agent/tests_e2e/run_mcp_server.sh](oze-agent/tests_e2e/run_mcp_server.sh):

- Po sekcji ładowania `tests_e2e/.env` (która zostaje, bo zawiera Telethon API keys) i wyborze interpretera Pythona, zamień `exec` na wrapper:

```sh
# Wrap with railway run so the MCP server inherits Supabase env
# (SUPABASE_URL, SUPABASE_SERVICE_KEY, GOOGLE_*, etc.) from Railway prod.
# Per CLAUDE.md: production secrets live ONLY in Railway env vars.
exec railway run --service bot --environment production -- "$PY" -m tests_e2e.mcp_server "$@"
```

(Ostatecznie należy zachować logikę wyboru `.venv/bin/python` vs `python3` — zapisać w zmiennej `PY` przed `exec`.)

### Krok 3 — restart MCP servera w Claude Code

MCP load happens at session start. Po edycji `run_mcp_server.sh` trzeba:

```
/mcp
```

i restartować server `oze-e2e`, albo zacząć nową sesję Claude Code.

### Krok 4 — weryfikacja

Sekwencja diagnostyczna:

```
mcp__oze-e2e__e2e_status      → oczekiwane: scenariusze=48, OK
mcp__oze-e2e__e2e_seed_fixtures → oczekiwane: seeded user_id=<uuid>, brak ERROR
mcp__oze-e2e__run_scenario name=show_client_existing_just_created
                              → oczekiwane: PASS, brak BLOCKERa na sheets verify
```

Jeśli krok 4 da BLOCKER ze starym komunikatem — Railway nie wstrzykuje env. Diagnoza:

```bash
railway whoami
railway environment list
railway variables --service bot --environment production | grep -i supabase
```

### Krok 5 — re-run pełnego smoke (110 scenariuszy)

Powtórzyć sekwencję z `test_results_smoke_29.04.2026.md`:

- `e2e_seed_fixtures`
- `run_category` × 8 kategorii (mutating_core, read_only, routing, rules, notes, card_structure, error_path, polish_edge) — 2 rundy
- extra `run_category mutating_core`
- `e2e_cleanup_run`

Oczekiwane: BLOCKERy → 0 (lub ~0). 14 stabilnych FAILi z poprzedniego runu zostają (nie są związane z mappingiem) — wymagają osobnej decyzji.

### Krok 6 — wyczyścić leftover `E2E-Beta-*` z poprzedniego runu

Po naprawie `e2e_cleanup_run` zacznie działać. Można od razu odpalić bez `run_id` (default: skasuje wszystkie per-run, zostawi fixturey):

```
mcp__oze-e2e__e2e_cleanup_run
```

To wyczyści ~110 syntetycznych klientów + eventów z dzisiejszego runu (~01:00-04:00 UTC 29.04.2026).

## Krytyczne pliki

| Plik | Co zmieniamy |
|---|---|
| [oze-agent/tests_e2e/run_mcp_server.sh](oze-agent/tests_e2e/run_mcp_server.sh) | wrap z `railway run` |
| [oze-agent/tests_e2e/.env](oze-agent/tests_e2e/.env) | bez zmian (jest Telethon-only — OK) |
| [oze-agent/tests_e2e/.env.example](oze-agent/tests_e2e/.env.example) | doklejić komentarz o railway run jako preferowanej drodze |
| [oze-agent/tests_e2e/README.md](oze-agent/tests_e2e/README.md) | uaktualnić instrukcję uruchomienia (railway login + railway run) |

## Ryzyka

1. **Railway CLI nie zalogowane.** Pierwszy `run` wywali błąd. Mitigacja: w `run_mcp_server.sh` dodać preflight `railway whoami` z czytelnym komunikatem.
2. **Brak internetu / Railway down.** MCP server nie wystartuje. Akceptujemy — to test infra dla prod, offline mode nie jest wymagany.
3. **Inny telegram_id w teście vs w bazie.** Jeśli użyt w teście Telegram account został zarejestrowany pod innym numerem niż 1690210103, sam railway run nie pomoże. Krok 1 (potwierdzić w bazie) wykluczy ten scenariusz.
4. **MCP w Claude Code odpala wrappera w sandboxie bez `railway`.** Sprawdzić, gdzie shell znajduje `railway` — może wymagać pełnej ścieżki w `run_mcp_server.sh` (np. `/opt/homebrew/bin/railway`).

## Out of scope tego planu

- Naprawa 14 stabilnych FAILi z poprzedniego runu (osobny sprint).
- Uruchomienie 20 kreatywnych scenariuszy z `test_results_creative_20.md` (osobna decyzja: kod vs manual).
- Zmiany w architekturze user mappingu.
- Dodanie nowego usera do Supabase (poza krokiem 1b jeśli się okaże potrzebne).

## Decyzja Maana

Decyzja Maana: 

- [ ] zatwierdzam Opcję A (railway run wrapper) — proceed z krokami 1-6
- [ ] wybieram Opcję B (Supabase env w `tests_e2e/.env`) mimo polityki, bo szybciej
- [ ] wybieram Opcję C (override UUID) jako tymczasowy bypass
- [ ] inne / komentarz: ______________________________
