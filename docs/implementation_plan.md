# OZE-Agent — Implementation Plan (Complete)

> **Document version:** 1.1 (post-review)  
> **Created:** 2026-04-05  
> **Last updated:** 2026-04-05  
> **Target executor:** Claude Code (VS Code extension, macOS)  
> **Source of truth:** OZE_Agent_Brief_v5_FINAL.md + poznaj_swojego_agenta_v5_FINAL.md  
> **Repo:** github.com/[maan]/oze-agent (private)

---

## How to read this plan

Each step is tagged:

| Tag | Meaning |
|-----|---------|
| **CLAUDE CODE** | Claude Code executes autonomously |
| **MAAN** | You (Maan) do this manually — login, key generation, UI clicks |
| **CLAUDE COWORK** | Claude Computer Use can assist (browser automation) |

Each step has:
- **What:** What to do
- **Why:** Why this order
- **Files:** Files created or modified
- **Depends on:** Previous steps required
- **Definition of Done (DoD):** How to verify success before moving on

**Critical rule:** Never proceed to the next step until DoD is confirmed.

---

## MVP Cutline — What MUST work for v1.0

These 10 capabilities define the minimum viable product. Phase A core = MVP. Everything else is expansion.

1. Linked Telegram user (manual beta account in Supabase + Google OAuth)
2. Text messages → intent classification → action
3. Voice transcription (Whisper) → parsed client data
4. Add / search / edit / delete client in Google Sheets
5. Add / view / reschedule / cancel meeting in Google Calendar
6. Photo upload → assigned to client in Google Drive
7. Pending flow system (confirmations, multi-step operations)
8. Post-meeting follow-up prompt + bulk response parsing
9. Morning brief + pre-meeting reminder
10. Deployed on Railway (webhook mode)

**NOT MVP** (build only after Phase A is stable and tested):
- Dashboard, admin panel, payments, CSV import, broadcasts, legal docs, backup export, advanced habits, health alert emails, Sentry, email sending

---

## Known Tradeoffs (accepted for MVP)

| Decision | Tradeoff | Why accepted |
|----------|----------|--------------|
| Scheduler in bot process | Restart = lost in-memory state (reminder dedup) | Simpler deployment. Fix: persist dedup flags to Supabase. |
| No auto-retry on Google API failure | User must retry manually | Brief explicitly says "no retry queue on MVP" |
| Supabase free tier | 500MB DB, no daily backups | Sufficient for beta (<10 users) |
| Google OAuth in "testing" mode | Max 100 test users | Fine for beta |
| APScheduler reminder dedup in memory | May re-send after bot restart | Low impact, can persist to DB if needed |
| conversation_history cleanup at 24h | Only affects storage, not bot memory (bot uses last 10 msg / 30 min window) | Per brief design |

---

## Execution Strategy for Claude Code

This is a single master plan, NOT a set of independent packs. Claude Code should:

1. **Work phase by phase.** Focus on the current phase. Don't pre-optimize for future phases.
2. **If a step is too large** (e.g., a module with 8+ functions), split it internally into substeps. Report the split before coding. This is expected and encouraged.
3. **Prefer working code over perfect code.** Get it running, then refine.
4. **When implementation reality conflicts with the plan** (e.g., a library API changed, a pattern doesn't work as described), STOP and explain the conflict. Don't force the plan.
5. **Commit after each step** with message: `"Step X.Y: [description]"`
6. **Phase A is the priority.** Do not start Phase B until Phase A passes ALL 25 acceptance tests.

---

## Phase 0: Infrastructure & Repository Setup

### Step 0.1: Initialize Git repository
- **Tag:** CLAUDE CODE
- **What:** Create the `oze-agent` repo structure with `.gitignore`, initial `README.md`, and branch strategy
- **Files:**
  - `README.md` (placeholder with project name)
  - `.gitignore` (Python + Node.js + .env + __pycache__ + node_modules + .next + .vercel)
  - `.env.example` (all env vars from brief, empty values)
- **Commands:**
  ```bash
  mkdir oze-agent && cd oze-agent
  git init
  git checkout -b main
  # create files
  git add . && git commit -m "Initial commit: project structure"
  git checkout -b develop
  ```
- **DoD:** Repo exists locally with `main` and `develop` branches. `.env.example` contains ALL env vars listed in brief (27 variables).

---

### Step 0.2: Create full directory structure
- **Tag:** CLAUDE CODE
- **What:** Create all directories and empty `__init__.py` files as defined in brief's file structure
- **Depends on:** 0.1
- **Files:**
  ```
  oze-agent/
  ├── bot/
  │   ├── __init__.py
  │   ├── handlers/
  │   │   └── __init__.py
  │   ├── scheduler/
  │   │   └── __init__.py
  │   └── utils/
  │       └── __init__.py
  ├── api/
  │   ├── __init__.py
  │   └── routes/
  │       └── __init__.py
  ├── shared/
  │   └── __init__.py
  ├── tests/
  │   └── __init__.py
  ├── docs/
  ├── dashboard/        (empty for now — Phase B)
  └── admin/            (empty for now — Phase C)
  ```
- **DoD:** `find . -type d` shows all directories. Every Python package has `__init__.py`.

---

### Step 0.3: Create Procfile and railway.toml
- **Tag:** CLAUDE CODE
- **What:** Railway deployment config for 2 processes
- **Depends on:** 0.2
- **Files:**
  - `Procfile`:
    ```
    bot: python -m bot.main
    api: uvicorn api.main:app --host 0.0.0.0 --port $PORT
    ```
  - `railway.toml`:
    ```toml
    [build]
    builder = "nixpacks"
    
    [deploy]
    restartPolicyType = "ON_FAILURE"
    restartPolicyMaxRetries = 10
    ```
- **DoD:** Both files exist and are syntactically correct.

---

### Step 0.4: Create requirements.txt
- **Tag:** CLAUDE CODE
- **What:** All Python dependencies with pinned versions
- **Depends on:** 0.2
- **Files:**
  - `requirements.txt`:
    ```
    # Telegram
    python-telegram-bot>=21.0,<22.0
    
    # API
    fastapi>=0.115.0,<1.0
    uvicorn>=0.30.0,<1.0
    
    # AI
    anthropic>=0.40.0,<1.0
    openai>=1.50.0,<2.0
    
    # Database
    supabase>=2.0.0,<3.0
    
    # Google APIs
    google-api-python-client>=2.100.0,<3.0
    google-auth-oauthlib>=1.2.0,<2.0
    google-auth-httplib2>=0.2.0,<1.0
    
    # Security
    cryptography>=42.0.0,<45.0
    PyJWT>=2.8.0,<3.0
    
    # Scheduler
    APScheduler>=3.10.0,<4.0
    
    # Utilities
    python-dotenv>=1.0.0,<2.0
    httpx>=0.27.0,<1.0
    python-multipart>=0.0.9,<1.0
    
    # Monitoring
    sentry-sdk[fastapi]>=2.0.0,<3.0
    
    # Testing
    pytest>=8.0.0,<9.0
    pytest-asyncio>=0.23.0,<1.0
    pytest-httpx>=0.30.0,<1.0
    ```
  - **Note:** Version ranges instead of pinned versions. Claude Code should run `pip install` and resolve the best compatible set. If conflicts arise, adjust ranges — don't fight the resolver.
- **DoD:** `pip install -r requirements.txt` completes without errors (test in venv).

---

### Step 0.5: Create config module
- **Tag:** CLAUDE CODE
- **What:** Central configuration that reads all env vars with validation
- **Depends on:** 0.4
- **Files:**
  - `bot/config.py`:
    ```python
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    class Config:
        # Core
        ENV = os.getenv("ENV", "dev")
        TIMEZONE = os.getenv("TIMEZONE", "Europe/Warsaw")
        
        # Telegram
        TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
        
        # AI
        ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        
        # Google OAuth
        GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
        GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
        GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "")
        
        # Supabase
        SUPABASE_URL = os.getenv("SUPABASE_URL", "")
        SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
        SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
        SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")
        
        # Security
        ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")
        
        # Payments
        PRZELEWY24_MERCHANT_ID = os.getenv("PRZELEWY24_MERCHANT_ID", "")
        PRZELEWY24_API_KEY = os.getenv("PRZELEWY24_API_KEY", "")
        PRZELEWY24_CRC = os.getenv("PRZELEWY24_CRC", "")
        
        # Pricing
        ACTIVATION_FEE_PLN = int(os.getenv("ACTIVATION_FEE_PLN", "199"))
        MONTHLY_SUBSCRIPTION_PLN = int(os.getenv("MONTHLY_SUBSCRIPTION_PLN", "49"))
        YEARLY_SUBSCRIPTION_PLN = int(os.getenv("YEARLY_SUBSCRIPTION_PLN", "350"))
        
        # Monitoring
        SENTRY_DSN = os.getenv("SENTRY_DSN", "")
        ADMIN_TELEGRAM_ID = os.getenv("ADMIN_TELEGRAM_ID", "")
        ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")
        
        # URLs
        BASE_URL = os.getenv("BASE_URL", "")
        DASHBOARD_URL = os.getenv("DASHBOARD_URL", "")
        ADMIN_URL = os.getenv("ADMIN_URL", "")
        
        # Email
        GMAIL_SMTP_USER = os.getenv("GMAIL_SMTP_USER", "")
        GMAIL_SMTP_PASSWORD = os.getenv("GMAIL_SMTP_PASSWORD", "")
        
        @classmethod
        def validate_phase_a(cls) -> list[str]:
            """Return list of missing env vars required for Phase A (bot)."""
            required = {
                "TELEGRAM_BOT_TOKEN": cls.TELEGRAM_BOT_TOKEN,
                "ANTHROPIC_API_KEY": cls.ANTHROPIC_API_KEY,
                "OPENAI_API_KEY": cls.OPENAI_API_KEY,
                "SUPABASE_URL": cls.SUPABASE_URL,
                "SUPABASE_KEY": cls.SUPABASE_KEY,
                "SUPABASE_SERVICE_KEY": cls.SUPABASE_SERVICE_KEY,
                "ENCRYPTION_KEY": cls.ENCRYPTION_KEY,
                "GOOGLE_CLIENT_ID": cls.GOOGLE_CLIENT_ID,
                "GOOGLE_CLIENT_SECRET": cls.GOOGLE_CLIENT_SECRET,
                "BASE_URL": cls.BASE_URL,
            }
            return [k for k, v in required.items() if not v]
    ```
- **DoD:** `python -c "from bot.config import Config; print(Config.validate_phase_a())"` runs without import errors.

---

### Step 0.6: Create Supabase project and schema
- **Tag:** MAAN + CLAUDE CODE
- **What:**
  1. **MAAN:** Create new Supabase project (free tier), note URL + anon key + service key + JWT secret
  2. **CLAUDE CODE:** Create `supabase_schema.sql` with ALL tables from brief
- **Depends on:** 0.5
- **Files:**
  - `supabase_schema.sql` — contains exact SQL from brief:
    - `users` table (all columns including google tokens, subscription fields, onboarding, admin flags)
    - `promo_codes` table
    - `conversation_history` table
    - `pending_followups` table
    - `pending_flows` table
    - `interaction_log` table
    - `user_habits` table
    - `payment_history` table
    - `webhook_log` table
    - `admin_broadcasts` table
    - `daily_interaction_counts` table
  - Add indexes:
    ```sql
    CREATE INDEX idx_conv_history_telegram ON conversation_history(telegram_id, created_at DESC);
    CREATE INDEX idx_interaction_log_telegram ON interaction_log(telegram_id, created_at DESC);
    CREATE INDEX idx_pending_followups_status ON pending_followups(status, telegram_id);
    CREATE INDEX idx_users_telegram ON users(telegram_id);
    CREATE INDEX idx_users_email ON users(email);
    CREATE INDEX idx_payment_history_user ON payment_history(user_id, created_at DESC);
    CREATE INDEX idx_daily_counts_date ON daily_interaction_counts(telegram_id, date);
    CREATE INDEX idx_webhook_log_source ON webhook_log(source, created_at DESC);
    CREATE INDEX idx_admin_broadcasts_status ON admin_broadcasts(status);
    ```
  - Add RLS policies (basic — service key bypasses):
    ```sql
    ALTER TABLE users ENABLE ROW LEVEL SECURITY;
    -- Service key has full access; anon key blocked from sensitive tables
    ```
- **MAAN action:** Run the SQL in Supabase SQL Editor
- **DoD:** All 11 tables visible in Supabase Table Editor. `SELECT count(*) FROM users` returns 0.

---

### Step 0.7: Create shared/database.py — Supabase connection
- **Tag:** CLAUDE CODE
- **What:** Supabase client wrapper (HTTP client, not SQL pool) with error handling
- **Depends on:** 0.6
- **Files:**
  - `shared/database.py`:
    - `get_supabase_client()` → returns initialized Supabase client (service key for backend)
    - `get_user_by_telegram_id(telegram_id: int) -> dict | None`
    - `get_user_by_id(user_id: str) -> dict | None`
    - `create_user(data: dict) -> dict`
    - `update_user(user_id: str, data: dict) -> dict`
    - `log_interaction(telegram_id, interaction_type, model, tokens_in, tokens_out, cost)`
    - `get_daily_interaction_count(telegram_id, date) -> int`
    - `increment_daily_interaction_count(telegram_id, date) -> int`
    - `save_conversation_message(telegram_id, role, content, message_type)`
    - `get_conversation_history(telegram_id, limit=10) -> list`
    - `save_pending_flow(telegram_id, flow_type, flow_data)`
    - `get_pending_flow(telegram_id) -> dict | None`
    - `delete_pending_flow(telegram_id)`
    - `save_pending_followup(telegram_id, event_id, event_title, event_end_time, client_name, client_location)`
    - `get_pending_followups(telegram_id, status="pending") -> list`
    - `update_pending_followup(followup_id, status)`
    - All functions: try/except with logging, return None on failure
- **DoD:** `python -c "from shared.database import get_supabase_client"` imports clean. Unit test file created (Step 0.7b).

---

### Step 0.7b: Unit test for database module
- **Tag:** CLAUDE CODE
- **What:** Test database functions with mocked Supabase client
- **Depends on:** 0.7
- **Files:**
  - `tests/test_database.py`:
    - Test `get_user_by_telegram_id` returns None for missing user
    - Test `create_user` returns created user dict
    - Test `log_interaction` doesn't raise
    - Test `get_daily_interaction_count` returns 0 for new day
    - Mock Supabase client using `unittest.mock`
- **DoD:** `pytest tests/test_database.py -v` — all tests pass.

---

### Step 0.8: Create shared/encryption.py
- **Tag:** CLAUDE CODE
- **What:** Fernet encryption for Google OAuth tokens
- **Depends on:** 0.5
- **Files:**
  - `shared/encryption.py`:
    ```python
    from cryptography.fernet import Fernet
    from bot.config import Config
    
    def get_fernet() -> Fernet:
        return Fernet(Config.ENCRYPTION_KEY.encode())
    
    def encrypt_token(token: str) -> str:
        return get_fernet().encrypt(token.encode()).decode()
    
    def decrypt_token(encrypted: str) -> str:
        return get_fernet().decrypt(encrypted.encode()).decode()
    
    def generate_encryption_key() -> str:
        """Run once to generate ENCRYPTION_KEY for .env"""
        return Fernet.generate_key().decode()
    ```
- **DoD:** `python -c "from shared.encryption import generate_encryption_key; print(generate_encryption_key())"` prints a valid Fernet key.

---

### Step 0.9: Generate encryption key and setup .env
- **Tag:** MAAN
- **What:** Create local `.env` file with real values
- **Depends on:** 0.8
- **Actions:**
  1. Copy `.env.example` to `.env`
  2. Run `python -c "from shared.encryption import generate_encryption_key; print(generate_encryption_key())"` → paste result into `ENCRYPTION_KEY`
  3. Fill in: `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_KEY`, `SUPABASE_JWT_SECRET` (from Supabase dashboard)
  4. Fill in: `ANTHROPIC_API_KEY` (from Anthropic console)
  5. Fill in: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` (from Google Cloud Console)
  6. Set `ENV=dev`
  7. Set `TIMEZONE=Europe/Warsaw`
  8. Leave payment/email/sentry fields empty for now
- **DoD:** `python -c "from bot.config import Config; missing = Config.validate_phase_a(); print(f'Missing: {missing}')"` — only `TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY`, `BASE_URL` should be missing (filled in later steps).

---

### Step 0.10: Create Telegram bots via BotFather
- **Tag:** MAAN
- **What:** Create two bots in Telegram
- **Actions:**
  1. Open @BotFather in Telegram
  2. `/newbot` → name: `OZE-Agent` → username: `OZEAgentBot` (or similar if taken)
  3. Copy token → paste into `.env` as `TELEGRAM_BOT_TOKEN`
  4. `/newbot` → name: `OZE-Agent Dev` → username: `OZEAgentDevBot` (or similar if taken)
  5. Save dev bot token separately (for staging)
  6. For each bot: `/setdescription` → "Twój osobisty asystent sprzedażowy OZE"
  7. For each bot: `/setabouttext` → "Asystent AI dla handlowców OZE w Polsce"
  8. For each bot: `/setcommands` → leave empty (agent uses natural language, no slash commands except /start)
- **DoD:** Both bot tokens work. Test: `curl https://api.telegram.org/bot<TOKEN>/getMe` returns bot info.

---

### Step 0.11: Create OpenAI API key
- **Tag:** MAAN
- **What:** Generate OpenAI API key for Whisper
- **Actions:**
  1. Go to platform.openai.com → API keys
  2. Create new key (name: "OZE-Agent Whisper")
  3. Paste into `.env` as `OPENAI_API_KEY`
- **DoD:** Key is in `.env`. Verification will happen when Whisper module is built.

---

### Step 0.12: Configure Google Cloud OAuth consent screen
- **Tag:** MAAN
- **What:** Setup OAuth consent screen for the Google Cloud project
- **Depends on:** 0.9 (need Google Client ID already)
- **Actions:**
  1. Google Cloud Console → APIs & Services → OAuth consent screen
  2. User type: External
  3. App name: OZE-Agent
  4. User support email: your email
  5. Scopes: add `https://www.googleapis.com/auth/spreadsheets`, `https://www.googleapis.com/auth/calendar`, `https://www.googleapis.com/auth/drive.file`
  6. Test users: add your own email
  7. App status: Testing (max 100 users — fine for beta)
  8. Create OAuth 2.0 Client ID (Web application type)
  9. Authorized redirect URI: `http://localhost:8000/auth/google/callback` (dev) — will add production URI later
  10. Copy Client ID and Client Secret to `.env`
- **DoD:** OAuth consent screen configured. Client ID and Secret in `.env`.

---

### Step 0.13: Verify all Phase 0 env vars
- **Tag:** CLAUDE CODE
- **What:** Run validation script
- **Depends on:** 0.9, 0.10, 0.11, 0.12
- **Files:**
  - `scripts/verify_env.py`:
    ```python
    from bot.config import Config
    missing = Config.validate_phase_a()
    if missing:
        print(f"❌ Missing: {missing}")
    else:
        print("✅ All Phase A env vars are set")
    ```
- **DoD:** Script prints ✅. All required env vars present. (BASE_URL can be placeholder for now — will be Railway URL)

---

## Phase A: Working Bot with Manual Beta Accounts

> **Goal:** A Telegram bot that can receive text and voice messages, parse client data via Claude, write to Google Sheets, manage Google Calendar, handle photos via Google Drive, do follow-ups, morning briefs, and reminders. Beta accounts created manually in Supabase.

---

### A-0: Shared Services Layer (business logic)

> All business logic lives here. Bot, API, and scheduler import these modules. Zero duplication.

---

#### Step A.1: shared/google_auth.py — OAuth token management
- **Tag:** CLAUDE CODE
- **What:** Google OAuth token storage, retrieval, refresh, and initial authorization
- **Depends on:** 0.7, 0.8
- **Files:**
  - `shared/google_auth.py`:
    - `get_google_credentials(user_id: str) -> google.oauth2.credentials.Credentials | None`
      - Reads encrypted tokens from Supabase `users` table
      - Decrypts access_token and refresh_token
      - If access_token expired → auto-refresh using refresh_token
      - If refresh fails → return None (caller handles re-auth flow)
      - On successful refresh → update encrypted tokens in Supabase
    - `store_google_tokens(user_id: str, credentials: Credentials)`
      - Encrypt access_token and refresh_token
      - Store in Supabase users table with expiry timestamp
    - `build_oauth_url(user_id: str) -> str`
      - Generate OAuth URL with state=user_id
      - Scopes: spreadsheets, calendar, drive.file
      - Access type: offline (for refresh token)
      - Prompt: consent (force refresh token)
    - `handle_oauth_callback(code: str, state: str) -> dict`
      - Exchange code for tokens
      - Store tokens via `store_google_tokens`
      - Return user info
    - `revoke_google_tokens(user_id: str) -> bool`
- **DoD:** Import succeeds. `build_oauth_url` returns a valid Google OAuth URL.

---

#### Step A.2: shared/google_sheets.py — CRM operations
- **Tag:** CLAUDE CODE
- **What:** All Google Sheets operations for CRM
- **Depends on:** A.1
- **Files:**
  - `shared/google_sheets.py`:
    - `get_sheets_service(user_id: str) -> Resource | None`
      - Uses `get_google_credentials` → builds Sheets API service
      - Returns None if credentials invalid (caller handles)
    - `get_sheet_headers(user_id: str) -> list[str]`
      - Read row 1 from user's spreadsheet
      - Cache in Supabase `users.sheet_columns` (JSONB)
    - `get_all_clients(user_id: str) -> list[dict]`
      - Read all rows, return as list of dicts (header: value)
    - `search_clients(user_id: str, query: str) -> list[dict]`
      - Fuzzy search across name, city, phone columns
      - Case-insensitive, typo-tolerant (Levenshtein distance ≤ 2)
      - Returns matching rows as dicts
    - `get_client_by_name_and_city(user_id: str, name: str, city: str) -> dict | None`
      - Exact-ish match for duplicate detection
    - `add_client(user_id: str, client_data: dict) -> int`
      - Append row to sheet
      - Returns row number
      - Sets "Data pierwszego kontaktu" to today if not provided
    - `update_client(user_id: str, row_number: int, updates: dict) -> bool`
      - Update specific cells in a row
      - Sets "Data ostatniego kontaktu" to today
    - `delete_client(user_id: str, row_number: int) -> bool`
      - Delete entire row
    - `create_spreadsheet(user_id: str, name: str) -> str`
      - Create new spreadsheet with default 17 columns
      - Set header formatting (bold, frozen row)
      - Return spreadsheet ID
    - `get_pipeline_stats(user_id: str) -> dict`
      - Count clients per status
      - Return {"Nowy lead": 5, "Spotkanie umówione": 3, ...}
    - Error handling: every function catches Google API errors, logs them, returns None/False/empty
    - If 401/403: return special error indicating re-auth needed
- **DoD:** Import succeeds. Functions have correct signatures and docstrings. `python -c "from shared.google_sheets import get_sheet_headers, add_client, search_clients, get_pipeline_stats"` runs without error.

---

#### Step A.2b: Unit tests for google_sheets.py
- **Tag:** CLAUDE CODE
- **What:** Test Sheets functions with mocked Google API
- **Depends on:** A.2
- **Files:**
  - `tests/test_google_sheets.py`:
    - Test `search_clients` fuzzy matching ("Kowalsky" matches "Kowalski")
    - Test `get_pipeline_stats` correctly counts statuses
    - Test error handling returns None on API failure
    - Mock Google Sheets API responses
- **DoD:** `pytest tests/test_google_sheets.py -v` — all pass.

---

#### Step A.3: shared/google_calendar.py — Calendar operations
- **Tag:** CLAUDE CODE
- **What:** All Google Calendar operations
- **Depends on:** A.1
- **Files:**
  - `shared/google_calendar.py`:
    - `get_calendar_service(user_id: str) -> Resource | None`
    - `create_calendar(user_id: str, name: str) -> str`
      - Create dedicated OZE calendar
      - Return calendar ID
    - `get_events_for_date(user_id: str, date: datetime.date) -> list[dict]`
      - Events for a specific day, sorted by start time
    - `get_events_for_range(user_id: str, start: datetime, end: datetime) -> list[dict]`
      - Events in date range
    - `get_upcoming_events(user_id: str, hours: int = 24) -> list[dict]`
    - `create_event(user_id: str, title: str, start: datetime, end: datetime, location: str = None, description: str = None) -> dict`
      - Create event on user's OZE calendar
      - Return event dict with ID
    - `update_event(user_id: str, event_id: str, updates: dict) -> dict`
      - Update event (title, time, location)
    - `delete_event(user_id: str, event_id: str) -> bool`
    - `check_conflicts(user_id: str, start: datetime, end: datetime) -> list[dict]`
      - Return list of conflicting events
    - `get_free_slots(user_id: str, date: datetime.date, slot_duration: int = 60) -> list[tuple]`
      - Return available time slots (9:00-18:00 default working hours)
    - `get_todays_last_event(user_id: str) -> dict | None`
      - For follow-up engine: when does the last meeting end?
    - Error handling: same pattern as Sheets
- **DoD:** Import succeeds. `python -c "from shared.google_calendar import create_event, check_conflicts, get_free_slots"` runs without error. Functions have correct type hints.

---

#### Step A.3b: Unit tests for google_calendar.py
- **Tag:** CLAUDE CODE
- **Depends on:** A.3
- **Files:**
  - `tests/test_google_calendar.py`:
    - Test `check_conflicts` detects overlapping events
    - Test `get_free_slots` returns correct slots given existing events
    - Mock Google Calendar API
- **DoD:** `pytest tests/test_google_calendar.py -v` — all pass.

---

#### Step A.4: shared/google_drive.py — Photo storage
- **Tag:** CLAUDE CODE
- **What:** Google Drive operations for client photos
- **Depends on:** A.1
- **Files:**
  - `shared/google_drive.py`:
    - `get_drive_service(user_id: str) -> Resource | None`
    - `create_root_folder(user_id: str) -> str`
      - Create "OZE Klienci - [username]" folder
      - Return folder ID
    - `create_client_folder(user_id: str, client_name: str, city: str) -> str`
      - Create "[Klient] - [Miasto]" subfolder
      - Return folder ID
    - `upload_photo(user_id: str, folder_id: str, file_bytes: bytes, filename: str) -> str`
      - Upload photo to client folder
      - Return file web view link
    - `get_client_photos(user_id: str, folder_id: str) -> list[dict]`
      - List photos in client folder with links
    - `get_or_create_client_folder(user_id: str, client_name: str, city: str) -> str`
      - Find existing folder or create new one
- **DoD:** Import succeeds. Functions have correct signatures.

---

#### Step A.5: shared/whisper_stt.py — Speech-to-text
- **Tag:** CLAUDE CODE
- **What:** OpenAI Whisper API integration
- **Depends on:** 0.5
- **Files:**
  - `shared/whisper_stt.py`:
    ```python
    import openai
    from bot.config import Config
    
    async def transcribe_voice(audio_bytes: bytes, filename: str = "voice.ogg") -> dict:
        """
        Transcribe audio using Whisper API.
        Returns: {"text": str, "confidence": float}
        Confidence estimated from Whisper's response.
        Cost: $0.006/min
        """
        client = openai.AsyncOpenAI(api_key=Config.OPENAI_API_KEY)
        
        # Whisper expects a file-like object
        import io
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = filename
        
        try:
            response = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="pl",
                response_format="verbose_json"
            )
            
            # Extract confidence from segments
            segments = response.segments if hasattr(response, 'segments') else []
            avg_confidence = 1.0
            if segments:
                confidences = [s.get("avg_logprob", -0.3) for s in segments]
                avg_logprob = sum(confidences) / len(confidences)
                # Convert log prob to 0-1 scale (rough approximation)
                avg_confidence = min(1.0, max(0.0, 1.0 + avg_logprob / 0.5))
            
            return {
                "text": response.text,
                "confidence": avg_confidence,
                "duration_seconds": getattr(response, "duration", 0)
            }
        except Exception as e:
            raise RuntimeError(f"Whisper transcription failed: {e}")
    ```
- **DoD:** Import succeeds. Function signature correct.

---

#### Step A.5b: Unit test for whisper_stt.py
- **Tag:** CLAUDE CODE
- **Depends on:** A.5
- **Files:**
  - `tests/test_whisper.py`:
    - Test with mocked OpenAI client
    - Test error handling raises RuntimeError
- **DoD:** `pytest tests/test_whisper.py -v` — all pass.

---

#### Step A.6: shared/claude_ai.py — AI processing
- **Tag:** CLAUDE CODE
- **What:** Claude API integration with model routing (Sonnet for complex, Haiku for simple)
- **Depends on:** 0.5
- **Files:**
  - `shared/claude_ai.py`:
    - Constants:
      ```python
      MODEL_COMPLEX = "claude-sonnet-4-20250514"
      MODEL_SIMPLE = "claude-haiku-4-5-20251001"
      COST_PER_MTOK_IN = {"complex": 3.0, "simple": 1.0}
      COST_PER_MTOK_OUT = {"complex": 15.0, "simple": 5.0}
      ```
    - `async def call_claude(system_prompt: str, user_message: str, model_type: str = "complex", max_tokens: int = 2048) -> dict`
      - Returns `{"text": str, "tokens_in": int, "tokens_out": int, "cost_usd": float, "model": str}`
    - `async def parse_voice_note(transcription: str, user_columns: list[str], today: str, default_duration: int) -> dict`
      - Uses COMPLEX model
      - System prompt from brief (the Claude system prompt for voice parsing)
      - Returns parsed JSON with client_data, missing_columns, suggested_followup
    - `async def classify_intent(message: str, context: list[dict] = None) -> dict`
      - Uses SIMPLE model
      - Classify user intent: add_client, search_client, edit_client, delete_client, add_meeting, view_meetings, reschedule_meeting, cancel_meeting, show_pipeline, change_status, assign_photo, general_question, confirm_yes, confirm_no, cancel_flow
      - Returns `{"intent": str, "entities": dict, "confidence": float}`
    - `async def extract_client_data(message: str, user_columns: list[str]) -> dict`
      - Uses COMPLEX model
      - Extract structured client data from natural text
      - Same output format as parse_voice_note
    - `async def extract_meeting_data(message: str, today: str) -> dict`
      - Uses COMPLEX model
      - Parse meeting info: client name, date, time, duration, location
      - Understand Polish date/time expressions
    - `async def generate_bot_response(system_context: str, user_message: str, conversation_history: list[dict]) -> dict`
      - Uses SIMPLE model for simple responses (confirmations, pipeline stats)
      - Uses COMPLEX model if conversation_history suggests complex flow
    - `async def parse_followup_response(transcription: str, meetings: list[dict], user_columns: list[str]) -> dict`
      - Uses COMPLEX model
      - Parse bulk follow-up response covering multiple meetings
      - Returns updates per meeting
    - `async def format_morning_brief(events: list, followups: list, pipeline_stats: dict) -> str`
      - Uses SIMPLE model
      - Generate formatted morning brief message
- **DoD:** Import succeeds. All functions have docstrings and correct signatures.

---

#### Step A.6b: Unit tests for claude_ai.py
- **Tag:** CLAUDE CODE
- **Depends on:** A.6
- **Files:**
  - `tests/test_claude_ai.py`:
    - Test `classify_intent` returns valid intent enum
    - Test model routing (complex vs simple)
    - Test cost calculation
    - Mock Anthropic client
- **DoD:** `pytest tests/test_claude_ai.py -v` — all pass.

---

#### Step A.7: shared/search.py — Fuzzy search engine
- **Tag:** CLAUDE CODE
- **What:** Fuzzy, case-insensitive, typo-tolerant search
- **Depends on:** None (pure Python)
- **Files:**
  - `shared/search.py`:
    - `def normalize_polish(text: str) -> str`
      - Lowercase, handle Polish diacritics for comparison
    - `def levenshtein_distance(s1: str, s2: str) -> int`
      - Standard Levenshtein implementation
    - `def fuzzy_match(query: str, candidates: list[str], threshold: int = 2) -> list[tuple[str, int]]`
      - Return matches with distance ≤ threshold, sorted by distance
    - `def search_clients(clients: list[dict], query: str) -> list[dict]`
      - Search across "Imię i nazwisko", "Miejscowość", "Telefon"
      - Return matching clients sorted by relevance
    - `def find_best_match(query: str, candidates: list[str]) -> str | None`
      - Return best single match or None
    - `def detect_potential_duplicate(name: str, city: str, existing_clients: list[dict]) -> dict | None`
      - Check if client with similar name + same city exists
- **DoD:** Import succeeds.

---

#### Step A.7b: Unit tests for search.py
- **Tag:** CLAUDE CODE
- **Depends on:** A.7
- **Files:**
  - `tests/test_search.py`:
    - Test "Kowalsky" matches "Kowalski" (distance ≤ 2)
    - Test Polish diacritics normalization ("Łódź" vs "Lodz")
    - Test duplicate detection
    - Test empty query returns empty
    - Test phone number search
- **DoD:** `pytest tests/test_search.py -v` — all pass.

---

#### Step A.8: shared/formatting.py — Message formatting
- **Tag:** CLAUDE CODE
- **What:** Telegram message formatting helpers (Markdown V2)
- **Depends on:** None
- **Files:**
  - `shared/formatting.py`:
    - `def format_client_card(client: dict) -> str`
      - Telegram MarkdownV2 formatted client card
      - Bold name, city, phone, status, all other fields
    - `def format_meeting(event: dict) -> str`
      - "📅 10:00-11:00 — Jan Kowalski\n📍 Piłsudskiego 12, Warszawa\n📞 600123456"
    - `def format_daily_schedule(events: list) -> str`
      - Full day schedule with all meetings
    - `def format_pipeline_stats(stats: dict) -> str`
      - "📊 Pipeline:\n• Nowy lead: 5\n• Spotkanie umówione: 3\n..."
    - `def format_morning_brief(events: list, followups: list, stats: dict, free_slots: list) -> str`
      - Full morning brief message
    - `def format_meeting_reminder(event: dict, client: dict) -> str`
      - Pre-meeting reminder with client data
    - `def format_confirmation(action: str, details: dict) -> str`
      - Confirmation message for any action
    - `def format_edit_comparison(field: str, old_value: str, new_value: str) -> str`
      - "Telefon: 600111222 → 601234567"
    - `def escape_markdown_v2(text: str) -> str`
      - Escape special characters for Telegram MarkdownV2
    - `def format_error(error_type: str) -> str`
      - User-friendly error messages in Polish
      - Types: google_down, timeout, token_expired, subscription_expired, rate_limit
- **DoD:** Import succeeds. `escape_markdown_v2("test_123")` returns properly escaped string.

---

#### Step A.8b: Unit tests for formatting.py
- **Tag:** CLAUDE CODE
- **Depends on:** A.8
- **Files:**
  - `tests/test_formatting.py`:
    - Test MarkdownV2 escaping
    - Test client card contains all fields
    - Test pipeline stats format
    - Test error messages are in Polish
- **DoD:** `pytest tests/test_formatting.py -v` — all pass.

---

#### Step A.9: shared/followup.py — Follow-up engine logic
- **Tag:** CLAUDE CODE
- **What:** Follow-up detection and management logic
- **Depends on:** A.3, A.6, 0.7
- **Files:**
  - `shared/followup.py`:
    - `async def check_unreported_meetings(user_id: str, telegram_id: int) -> list[dict]`
      - Get today's past events from Calendar
      - Check which have pending_followups with status='pending'
      - Return list of meetings needing reports
    - `async def create_followup_prompts(unreported: list[dict]) -> str`
      - Format message listing unreported meetings
    - `async def process_followup_response(user_id: str, telegram_id: int, response_text: str, meetings: list[dict], user_columns: list[str]) -> dict`
      - Use Claude to parse bulk response
      - Return per-meeting updates (status changes, notes, follow-up dates)
    - `async def schedule_followup_reminder(telegram_id: int, event_id: str, event_title: str, event_end: datetime, client_name: str, client_location: str)`
      - Save to pending_followups table
- **DoD:** Import succeeds. Functions have correct signatures.

---

#### Step A.10: shared/google_auth.py — Google OAuth callback endpoint
- **Tag:** CLAUDE CODE  
- **What:** Minimal FastAPI endpoint for Google OAuth callback (needed even in Phase A for beta accounts to authorize Google)
- **Depends on:** A.1
- **Files:**
  - `api/main.py` (minimal):
    ```python
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from api.routes.google_oauth import router as google_oauth_router
    
    app = FastAPI(title="OZE-Agent API", version="0.1.0")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(google_oauth_router, prefix="/auth")
    
    @app.get("/health")
    async def health():
        return {"status": "ok", "version": "0.1.0"}
    ```
  - `api/routes/google_oauth.py`:
    - `GET /auth/google/callback` — handles OAuth redirect
    - Exchanges code for tokens, stores them, shows success page
    - `GET /auth/google/url/{user_id}` — returns OAuth URL for a user
- **DoD:** `uvicorn api.main:app` starts without errors. `/health` returns 200.

---

### A-1: Telegram Bot — Core Structure

---

#### Step A.11: bot/main.py — Bot application entry point
- **Tag:** CLAUDE CODE
- **What:** Main bot file with webhook setup and handler registration
- **Depends on:** 0.5, A.10
- **Files:**
  - `bot/main.py`:
    ```python
    import logging
    from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
    from bot.config import Config
    from bot.handlers.start import start_command
    from bot.handlers.text import handle_text
    from bot.handlers.voice import handle_voice
    from bot.handlers.photo import handle_photo
    from bot.handlers.buttons import handle_button
    from bot.handlers.fallback import handle_fallback
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    def main():
        missing = Config.validate_phase_a()
        if missing:
            logger.error(f"Missing env vars: {missing}")
            return
        
        app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # Handlers (order matters — first match wins)
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
        app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        app.add_handler(CallbackQueryHandler(handle_button))
        app.add_handler(MessageHandler(filters.ALL, handle_fallback))
        
        # Error handler
        app.add_error_handler(error_handler)
        
        if Config.ENV == "dev":
            # Polling mode for local development
            logger.info("Starting bot in POLLING mode (dev)")
            app.run_polling(drop_pending_updates=True)
        else:
            # Webhook mode for production
            webhook_url = f"{Config.BASE_URL}/webhooks/telegram"
            logger.info(f"Starting bot in WEBHOOK mode: {webhook_url}")
            app.run_webhook(
                listen="0.0.0.0",
                port=8443,
                url_path="/webhooks/telegram",
                webhook_url=webhook_url,
                drop_pending_updates=True
            )
    
    async def error_handler(update, context):
        logger.error(f"Exception: {context.error}", exc_info=context.error)
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "⚠️ Wystąpił nieoczekiwany błąd. Spróbuj ponownie za chwilę."
            )
    
    if __name__ == "__main__":
        main()
    ```
- **DoD:** `python -m bot.main` starts in polling mode without errors (will fail on missing handlers — that's next).

---

#### Step A.12: bot/utils/telegram_helpers.py — Common bot utilities
- **Tag:** CLAUDE CODE
- **What:** Helper functions for common Telegram operations
- **Depends on:** 0.7
- **Files:**
  - `bot/utils/telegram_helpers.py`:
    - `async def send_typing(context, chat_id)`
      - Send typing indicator
    - `async def send_processing_stage(context, chat_id, stage: str)`
      - Send status message: "🎙 Transkrybuję..." or "🔍 Analizuję..."
    - `async def check_user_registered(telegram_id: int) -> dict | None`
      - Check if telegram_id exists in users table
      - Return user dict or None
    - `async def check_subscription_active(user: dict) -> bool`
      - Check subscription_status == 'active'
    - `async def check_interaction_limit(telegram_id: int) -> dict`
      - Check daily count vs 100 limit
      - Return {"allowed": bool, "count": int, "limit": int, "can_borrow": bool}
    - `async def increment_interaction(telegram_id: int, interaction_type: str, model: str, tokens_in: int, tokens_out: int, cost: float)`
      - Log interaction + increment daily count
    - `async def send_unregistered_message(update)`
      - Send link to oze-agent.pl + registration info
    - `async def send_subscription_expired_message(update)`
      - Send expiry message + payment link
    - `async def send_rate_limit_message(update, count: int, can_borrow: bool)`
      - Inform about limit + offer borrowing
    - `def build_confirm_buttons(callback_prefix: str) -> InlineKeyboardMarkup`
      - Returns [Tak] [Nie] inline keyboard
    - `def build_choice_buttons(options: list[tuple[str, str]]) -> InlineKeyboardMarkup`
      - Generic choice buttons
    - `async def is_private_chat(update) -> bool`
      - Return True only for private chats (ignore groups)
- **DoD:** Import succeeds.

---

#### Step A.13: bot/handlers/start.py — /start command
- **Tag:** CLAUDE CODE
- **What:** Handle /start command with Telegram linking code
- **Depends on:** A.12
- **Files:**
  - `bot/handlers/start.py`:
    - `async def start_command(update, context)`
      1. Check if private chat (ignore groups)
      2. Extract args (linking code from deep link)
      3. If linking code provided:
         - Validate code against Supabase (telegram_link_code, check expiry)
         - If valid: update user's telegram_id in Supabase, clear code
         - Send welcome message + link to "Poznaj swojego agenta"
      4. If no code and user already linked:
         - Send "Już jesteś połączony!" message
      5. If no code and user NOT linked:
         - Send registration link to oze-agent.pl
- **DoD:** Import succeeds from bot.main.

---

#### Step A.14: bot/handlers/text.py — Text message handler (main router)
- **Tag:** CLAUDE CODE
- **What:** The main text message handler — routes to appropriate action
- **Depends on:** A.12, A.6, A.2, A.3
- **Files:**
  - `bot/handlers/text.py`:
    - `async def handle_text(update, context)`
      1. Check private chat
      2. Check user registered → if not, send registration link
      3. Check subscription active → if not, send expiry message
      4. Check interaction limit → if exceeded, send limit message
      5. Send typing indicator
      6. Check for pending flow (user responding to confirmation/edit)
         - If pending: route to flow handler
      7. Save message to conversation_history
      8. Get conversation history (last 10 or 30 min)
      9. Call `classify_intent` with message + history
      10. Route by intent:
          - `add_client` → handle_add_client flow
          - `search_client` → handle_search_client
          - `edit_client` → handle_edit_client
          - `delete_client` → handle_delete_client
          - `add_meeting` → handle_add_meeting
          - `view_meetings` → handle_view_meetings
          - `reschedule_meeting` → handle_reschedule_meeting
          - `cancel_meeting` → handle_cancel_meeting
          - `show_pipeline` → handle_show_pipeline
          - `change_status` → handle_change_status
          - `confirm_yes` → handle_confirm (process pending flow)
          - `confirm_no` → handle_cancel_flow
          - `cancel_flow` → handle_cancel_flow
          - `refresh_columns` → handle_refresh_columns
          - `general_question` → handle_general
      11. Log interaction
    
    Sub-handlers (in same file or separate module if too large):
    
    - `handle_add_client(update, context, user, intent_data)`:
      1. Extract client data from message via Claude
      2. Check for duplicates (name + city)
      3. If duplicate found: inform user, ask whether to add anyway
      4. Show extracted data + missing fields (ALL at once)
      5. Save pending_flow with type="add_client"
      6. Show [Tak] [Nie] buttons
    
    - `handle_search_client(update, context, user, intent_data)`:
      1. Search in Sheets
      2. If 0 results: "Nie znalazłem" + suggest similar
      3. If 1 result: show client card
      4. If 2-10 results: show list with cities, ask which
      5. If 50+ results: send link to Sheets
    
    - `handle_edit_client(update, context, user, intent_data)`:
      1. Find client
      2. Show old value vs new value
      3. Ask: "Zostawić stary i dodać drugi, czy usunąć stary?"
      4. Save pending_flow with type="edit_client"
    
    - `handle_add_meeting(update, context, user, intent_data)`:
      1. Extract meeting data via Claude
      2. Check conflicts
      3. If conflict: warn but allow
      4. Show meeting details, ask confirmation
      5. If client exists in Sheets: auto-link
      6. If client NOT in Sheets: after confirmation, ask "Dodać do bazy?"
      7. Save pending_flow with type="add_meeting"
    
    - `handle_view_meetings(update, context, user, intent_data)`:
      1. Parse date from message (today, tomorrow, this week)
      2. Get events from Calendar
      3. Format and send schedule
    
    - `handle_show_pipeline(update, context, user, intent_data)`:
      1. Get pipeline stats from Sheets
      2. Send short numeric summary
      3. Add link to dashboard
    
    - `handle_change_status(update, context, user, intent_data)`:
      1. Find client
      2. Propose status change
      3. Save pending_flow
    
    - `handle_refresh_columns(update, context, user)`:
      1. Re-read sheet headers
      2. Update cache in Supabase
      3. Confirm: "Kolumny odświeżone: [list]"
    
    - `handle_confirm(update, context, user)`:
      1. Get pending_flow
      2. Execute action based on flow_type
      3. Delete pending_flow
      4. Send success message
    
    - `handle_cancel_flow(update, context, user)`:
      1. Ask "Anulować?" if not already asking
      2. If confirmed: delete pending_flow
- **DoD:** Import succeeds. Bot can receive text messages without crashing (intent classification will be key).

---

#### Step A.15: bot/handlers/voice.py — Voice message handler
- **Tag:** CLAUDE CODE
- **What:** Handle voice messages — transcribe and process
- **Depends on:** A.5, A.14
- **Files:**
  - `bot/handlers/voice.py`:
    - `async def handle_voice(update, context)`
      1. Check private, registered, subscription, limit (same guards as text)
      2. Send "🎙 Transkrybuję..."
      3. Download voice file from Telegram
      4. Call `transcribe_voice`
      5. Check confidence:
         - If high (≥ 0.85): proceed directly to processing
         - If low (< 0.85): show transcription, ask for confirmation
      6. If proceeding:
         - Send "🔍 Analizuję..."
         - Treat transcription as text → route through same logic as handle_text
      7. 60-second timeout on Whisper: send error message
      8. Log interaction (whisper cost + claude cost)
- **DoD:** Import succeeds.

---

#### Step A.16: bot/handlers/photo.py — Photo handler
- **Tag:** CLAUDE CODE
- **What:** Handle photos — assign to client in Google Drive
- **Depends on:** A.4, A.12
- **Files:**
  - `bot/handlers/photo.py`:
    - `async def handle_photo(update, context)`
      1. Standard guards (private, registered, subscription, limit)
      2. Download photo from Telegram (highest resolution)
      3. Check if there's a pending photo flow (assigning multiple photos to same client)
      4. If no pending flow:
         - Ask: "Do którego klienta przypisać zdjęcie? (imię i miejscowość)"
         - Save pending_flow type="assign_photo" with photo bytes
      5. If pending flow exists (user already said which client):
         - Upload to Drive
         - Add link to "Zdjęcia" column in Sheets
         - Confirm: "📸 Zdjęcie dodane do [klient]"
      6. Support batch: multiple photos in sequence → same client
- **DoD:** Import succeeds.

---

#### Step A.17: bot/handlers/buttons.py — Inline button callback handler
- **Tag:** CLAUDE CODE
- **What:** Handle inline button presses ([Tak] / [Nie] and other choices)
- **Depends on:** A.14
- **Files:**
  - `bot/handlers/buttons.py`:
    - `async def handle_button(update, context)`
      1. Answer callback query (removes loading indicator)
      2. Parse callback_data (format: "action:value")
      3. Route by action:
         - `confirm:yes` → process pending flow (same as text "Tak")
         - `confirm:no` → cancel flow (same as text "Nie")
         - `borrow:yes` → borrow interactions from tomorrow
         - `borrow:no` → decline borrowing
         - `select_client:row_num` → select from multiple search results
         - `duplicate:add_anyway` → add client despite duplicate
         - `edit:replace` → replace old value
         - `edit:keep_both` → keep both old and new value
         - `cancel_confirm:yes` → confirm cancellation
         - `cancel_confirm:no` → keep data, continue editing
- **DoD:** Import succeeds.

---

#### Step A.18: bot/handlers/fallback.py — Catch-all handler
- **Tag:** CLAUDE CODE
- **What:** Handle any message type not caught by other handlers
- **Depends on:** A.12
- **Files:**
  - `bot/handlers/fallback.py`:
    - `async def handle_fallback(update, context)`
      1. If group chat: ignore silently
      2. If sticker/animation/etc: "Obsługuję tekst, głosówki i zdjęcia."
      3. If forwarded message: treat content as regular text/voice/photo (process normally)
- **DoD:** Import succeeds.

---

### A-2: Integration Testing — Bot Core

---

#### Step A.19: Create manual beta user in Supabase
- **Tag:** MAAN
- **What:** Manually create a test user for beta testing
- **Depends on:** 0.6, 0.10
- **Actions:**
  1. Open Supabase SQL Editor
  2. Insert user:
     ```sql
     INSERT INTO users (
       name, email, telegram_id, 
       subscription_status, subscription_plan, 
       subscription_expires_at,
       onboarding_completed, is_admin,
       pipeline_statuses, working_days,
       morning_brief_hour, reminder_minutes_before,
       default_meeting_duration
     ) VALUES (
       'Maan', 'your@email.com', YOUR_TELEGRAM_ID,
       'active', 'monthly',
       '2027-12-31T00:00:00Z',
       false, true,
       '["Nowy lead","Spotkanie umówione","Spotkanie odbyte","Oferta wysłana","Negocjacje","Podpisane","Odrzucone"]',
       '[1,2,3,4,5]',
       7, 60, 60
     );
     ```
  3. Note: Google tokens not set yet — need OAuth flow
- **DoD:** User row exists in Supabase with `telegram_id` set.

---

#### Step A.20: Google OAuth flow for beta user
- **Tag:** MAAN + CLAUDE COWORK
- **What:** Authorize Google access for the beta user
- **Depends on:** A.10, A.19
- **Actions:**
  1. Start FastAPI locally: `uvicorn api.main:app --reload --port 8000`
  2. Open browser: `http://localhost:8000/auth/google/url/YOUR_USER_ID`
  3. Complete Google OAuth consent
  4. Callback stores tokens in Supabase
  5. Verify: check users table — `google_access_token` should be non-null (encrypted)
- **DoD:** User has encrypted Google tokens in Supabase.

---

#### Step A.21: Create Google Sheets + Calendar for beta user
- **Tag:** CLAUDE CODE
- **What:** Script to create initial Google resources for a user
- **Depends on:** A.20, A.2, A.3
- **Files:**
  - `scripts/setup_beta_user.py`:
    ```python
    import asyncio
    from shared.google_sheets import create_spreadsheet
    from shared.google_calendar import create_calendar
    from shared.google_drive import create_root_folder
    from shared.database import update_user
    
    USER_ID = "paste-user-id-here"
    
    async def setup():
        # Create spreadsheet
        sheet_id = await create_spreadsheet(USER_ID, "OZE Klienci")
        print(f"Spreadsheet: {sheet_id}")
        
        # Create calendar
        cal_id = await create_calendar(USER_ID, "OZE Spotkania")
        print(f"Calendar: {cal_id}")
        
        # Create Drive folder
        folder_id = await create_root_folder(USER_ID)
        print(f"Drive folder: {folder_id}")
        
        # Update user record
        await update_user(USER_ID, {
            "google_sheets_id": sheet_id,
            "google_sheets_name": "OZE Klienci",
            "google_calendar_id": cal_id,
            "google_calendar_name": "OZE Spotkania",
            "google_drive_folder_id": folder_id,
            "onboarding_completed": True,
        })
        print("✅ Beta user setup complete")
    
    asyncio.run(setup())
    ```
- **MAAN action:** Update USER_ID in script, run it
- **DoD:** Google Sheets with 17 default columns visible in user's Google account. Calendar "OZE Spotkania" visible. Drive folder created.

---

#### Step A.22: End-to-end test — Bot receives message
- **Tag:** MAAN
- **What:** First real integration test
- **Depends on:** A.11 through A.21
- **Actions:**
  1. Start bot locally: `python -m bot.main` (polling mode)
  2. Open Telegram, send message to @OZEAgentDevBot
  3. Send: "Cześć"
  4. Expected: Bot responds (even if just "Jak mogę pomóc?")
  5. Send: "Nowy klient Nowak, Leśna 5, Piaseczno, pompa ciepła, tel 601234567"
  6. Expected: Bot shows parsed data, asks for confirmation
  7. Confirm: "Tak"
  8. Expected: Data appears in Google Sheets
  9. Send: "Co mam o Nowaku?"
  10. Expected: Bot shows client card
- **DoD:** All 4 interactions work. Client visible in Google Sheets.

---

#### Step A.23: End-to-end test — Voice message
- **Tag:** MAAN
- **What:** Test voice flow
- **Depends on:** A.22
- **Actions:**
  1. Send voice message to bot: describe a client visit
  2. Expected: "🎙 Transkrybuję..." → "🔍 Analizuję..." → parsed data → confirmation
  3. Confirm → data in Sheets
- **DoD:** Voice-to-Sheets pipeline works end-to-end.

---

#### Step A.24: End-to-end test — Calendar
- **Tag:** MAAN
- **What:** Test calendar operations
- **Depends on:** A.22
- **Actions:**
  1. Send: "Jutro o 10 jadę do Nowaka"
  2. Expected: Bot shows meeting details with address from Sheets, asks confirmation
  3. Confirm → event in Google Calendar with location
  4. Send: "Co mam jutro?"
  5. Expected: Bot shows tomorrow's schedule
  6. Send: "Przełóż Nowaka na piątek o 14"
  7. Expected: Bot shows old/new time, asks confirmation
  8. Confirm → event updated
- **DoD:** Calendar CRUD works through bot.

---

#### Step A.25: End-to-end test — Photos
- **Tag:** MAAN
- **What:** Test photo upload flow
- **Depends on:** A.22
- **Actions:**
  1. Send photo to bot
  2. Expected: Bot asks which client
  3. Reply: "Nowak z Piaseczna"
  4. Expected: Photo uploaded to Drive, link in Sheets
  5. Send another photo without specifying client
  6. Expected: Bot asks again (or assigns to last client if in flow)
- **DoD:** Photo visible in Google Drive in correct client folder.

---

#### Step A.26: End-to-end test — Edge cases
- **Tag:** MAAN
- **What:** Test error handling and edge cases
- **Depends on:** A.22
- **Actions:**
  1. Test duplicate: add client with same name + city as Nowak → expect duplicate warning
  2. Test edit: "Zmień telefon Nowaka na 602000000" → expect old/new comparison
  3. Test delete: "Usuń Nowaka z Piaseczna" → expect confirmation → confirm → row deleted
  4. Test fuzzy search: "Co mam o Novaku?" → expect "Czy chodziło o Nowaka?"
  5. Test pipeline: "Ilu mam klientów?" → expect count per status
  6. Test unknown message: send sticker → expect fallback message
  7. Test "odśwież kolumny" → expect column refresh confirmation
  8. Test status change: "Nowak — wysłałem ofertę" → expect status change proposal
- **DoD:** All edge cases handled gracefully.

---

### A-3: Scheduler — Proactive Features

---

#### Step A.27: Scheduler setup in bot process
- **Tag:** CLAUDE CODE
- **What:** APScheduler integration in bot main process
- **Accepted tradeoff:** Scheduler runs in-process with bot. Restart = lost in-memory state (e.g., reminder dedup). For MVP this is acceptable. Persist dedup flags to Supabase if re-sends become a problem.
- **Depends on:** A.11
- **Files:**
  - Modify `bot/main.py`:
    - Import APScheduler
    - Initialize AsyncIOScheduler with timezone="Europe/Warsaw"
    - Register all scheduler jobs (placeholder functions for now)
    - Start scheduler before bot starts
  - `bot/scheduler/__init__.py` — export all job functions

---

#### Step A.28: bot/scheduler/morning_brief.py
- **Tag:** CLAUDE CODE
- **What:** Daily morning brief on working days
- **Depends on:** A.27, A.3, A.2, A.8
- **Files:**
  - `bot/scheduler/morning_brief.py`:
    - `async def send_morning_briefs(context)`
      1. Get all active users with `onboarding_completed=True`
      2. For each user:
         a. Check if today is a working day (user's `working_days` setting)
         b. Check if current hour matches user's `morning_brief_hour`
         c. Get today's events from Calendar
         d. Get pending follow-ups
         e. Get pipeline stats
         f. Get free slots
         g. Format morning brief message
         h. Send via Telegram
    - Scheduler: runs every minute, checks hour match (simpler than per-user cron)
- **DoD:** Import succeeds. Manual test: trigger function, receive brief in Telegram.

---

#### Step A.29: bot/scheduler/reminders.py
- **Tag:** CLAUDE CODE
- **What:** Pre-meeting reminders
- **Depends on:** A.27, A.3, A.2
- **Files:**
  - `bot/scheduler/reminders.py`:
    - `async def check_upcoming_meetings(context)`
      1. For each active user:
         a. Get events starting within `reminder_minutes_before` minutes
         b. Check if reminder already sent (flag in context or DB)
         c. Get client data from Sheets (matching event title to client name)
         d. Format reminder: name + address + phone + notes
         e. Send via Telegram
    - Scheduler: runs every 1 minute
    - Track sent reminders to avoid duplicates (in-memory set per bot session, or DB flag)
- **DoD:** Import succeeds.

---

#### Step A.30: bot/scheduler/followup_check.py
- **Tag:** CLAUDE CODE
- **What:** Post-meeting follow-up prompts
- **Depends on:** A.27, A.9
- **Files:**
  - `bot/scheduler/followup_check.py`:
    - `async def check_followups(context)`
      1. For each active user:
         a. Get today's last event end time
         b. If last event ended > 30 min ago AND unreported meetings exist:
            - Create follow-up prompt listing unreported meetings
            - Send via Telegram
            - Mark followups as "asked"
      2. Don't re-ask if already asked today
    - Scheduler: runs every 5 minutes
- **DoD:** Import succeeds.

---

#### Step A.31: bot/scheduler/flow_reminder.py
- **Tag:** CLAUDE CODE
- **What:** Remind about incomplete flows
- **Depends on:** A.27
- **Files:**
  - `bot/scheduler/flow_reminder.py`:
    - `async def remind_incomplete_flows(context)`
      1. Get pending_flows older than 30 min where `reminder_sent=False`
      2. Send reminder: "Masz niedokończoną operację: [type]. Kontynuować?"
      3. Mark `reminder_sent=True`
      4. Only remind once
    - Scheduler: runs every 5 minutes
- **DoD:** Import succeeds.

---

#### Step A.32: bot/scheduler/maintenance.py
- **Tag:** CLAUDE CODE
- **What:** Maintenance jobs (cleanup, token refresh, column sync, subscription check, habit calc)
- **Depends on:** A.27
- **Files:**
  - `bot/scheduler/maintenance.py`:
    - `async def cleanup_conversations(context)`
      - Delete conversation_history older than 24h
      - Runs daily at 03:00
    - `async def refresh_google_tokens(context)`
      - For each user with tokens expiring in < 30 min: auto-refresh
      - Runs every 30 minutes
    - `async def sync_sheet_columns(context)`
      - Re-read sheet headers for all active users
      - Update `sheet_columns` in Supabase
      - Runs every 6 hours
    - `async def check_subscriptions(context)`
      - Find users with `subscription_expires_at < now()` and status='active'
      - Change status to 'expired'
      - Runs daily at 00:00
    - `async def send_subscription_reminders(context)`
      - Find users expiring in 3 days → send reminder
      - Find users expiring today → send reminder
      - Runs daily at 09:00
    - `async def recalculate_habits(context)`
      - For each user: calculate default meeting duration from last 20 meetings
      - Update user_habits table
      - Runs daily at 02:00
- **DoD:** Import succeeds. All functions have correct signatures.

---

#### Step A.33: bot/scheduler/health_check.py
- **Tag:** CLAUDE CODE
- **What:** Health check that alerts admin
- **Depends on:** A.27
- **Files:**
  - `bot/scheduler/health_check.py`:
    - `async def run_health_check(context)`
      1. Check Supabase connection
      2. Check Anthropic API (minimal request)
      3. Check OpenAI API (minimal request)
      4. If any fail: send Telegram alert to ADMIN_TELEGRAM_ID
      5. Also send email alert (Gmail SMTP) if configured
    - Scheduler: runs every 5 minutes
    - Rate limit alerts: max 1 alert per service per 30 min
- **DoD:** Import succeeds.

---

#### Step A.34: Register all scheduler jobs in bot/main.py
- **Tag:** CLAUDE CODE
- **What:** Wire up all scheduler jobs with correct intervals
- **Depends on:** A.28 through A.33
- **Files:**
  - Modify `bot/main.py`:
    ```python
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.triggers.cron import CronTrigger
    import pytz
    
    tz = pytz.timezone("Europe/Warsaw")
    scheduler = AsyncIOScheduler(timezone=tz)
    
    # Morning brief — every minute (checks hour match internally)
    scheduler.add_job(send_morning_briefs, IntervalTrigger(minutes=1), args=[app])
    # Reminders — every minute
    scheduler.add_job(check_upcoming_meetings, IntervalTrigger(minutes=1), args=[app])
    # Follow-ups — every 5 min
    scheduler.add_job(check_followups, IntervalTrigger(minutes=5), args=[app])
    # Flow reminders — every 5 min
    scheduler.add_job(remind_incomplete_flows, IntervalTrigger(minutes=5), args=[app])
    # Token refresh — every 30 min
    scheduler.add_job(refresh_google_tokens, IntervalTrigger(minutes=30), args=[app])
    # Column sync — every 6 hours
    scheduler.add_job(sync_sheet_columns, IntervalTrigger(hours=6), args=[app])
    # Subscription check — daily 00:00
    scheduler.add_job(check_subscriptions, CronTrigger(hour=0, minute=0), args=[app])
    # Subscription reminders — daily 09:00
    scheduler.add_job(send_subscription_reminders, CronTrigger(hour=9, minute=0), args=[app])
    # Conversation cleanup — daily 03:00
    scheduler.add_job(cleanup_conversations, CronTrigger(hour=3, minute=0), args=[app])
    # Habit recalc — daily 02:00
    scheduler.add_job(recalculate_habits, CronTrigger(hour=2, minute=0), args=[app])
    # Health check — every 5 min
    scheduler.add_job(run_health_check, IntervalTrigger(minutes=5), args=[app])
    ```
- **DoD:** Bot starts with scheduler. No errors in logs. Jobs are registered.

---

#### Step A.35: End-to-end test — Morning brief
- **Tag:** MAAN
- **What:** Test morning brief manually
- **Depends on:** A.34
- **Actions:**
  1. Temporarily set `morning_brief_hour` to current hour in Supabase
  2. Add a test meeting in Google Calendar for today
  3. Restart bot
  4. Wait for brief to arrive (within 1 min)
  5. Verify: brief contains meeting info, address, pipeline stats
  6. Reset `morning_brief_hour` to normal
- **DoD:** Morning brief received with correct content.

---

#### Step A.36: End-to-end test — Pre-meeting reminder
- **Tag:** MAAN
- **What:** Test pre-meeting reminder
- **Depends on:** A.34
- **Actions:**
  1. Create a meeting in Google Calendar starting in 61 minutes
  2. Wait for reminder (should arrive when meeting is 60 min away)
  3. Verify: reminder contains client name, address, phone, notes
- **DoD:** Reminder received with client data.

---

#### Step A.37: End-to-end test — Follow-up prompt
- **Tag:** MAAN
- **What:** Test post-meeting follow-up
- **Depends on:** A.34
- **Actions:**
  1. Create a meeting in Calendar that already ended 35 min ago
  2. Wait for follow-up check (every 5 min)
  3. Expected: bot lists the meeting and asks how it went
  4. Reply with voice note describing the meeting
  5. Expected: bot parses response, proposes status changes
  6. Confirm
  7. Verify: status updated in Sheets
- **DoD:** Full follow-up flow works.

---

### A-4: Deploy Bot to Railway

---

#### Step A.38: Prepare Railway deployment
- **Tag:** CLAUDE CODE
- **What:** Finalize deployment config
- **Depends on:** A.34
- **Files:**
  - Verify `Procfile` has correct commands
  - Verify `requirements.txt` is complete
  - Verify `railway.toml` is correct
  - Create `bot/main.py` webhook mode works with Railway PORT env var
  - Verify `api/main.py` works with Railway PORT env var
  - Add `runtime.txt` if needed: `python-3.13`
- **DoD:** All deployment files ready.

---

#### Step A.39: Deploy to Railway
- **Tag:** MAAN
- **What:** First deployment
- **Depends on:** A.38
- **Actions:**
  1. Push code to GitHub (`develop` branch)
  2. Connect Railway to GitHub repo
  3. Create 2 services:
     - Service 1: "bot" — Start command: `python -m bot.main`
     - Service 2: "api" — Start command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
  4. Set ALL env vars from `.env` in Railway dashboard for both services
  5. Set `ENV=staging` for develop branch
  6. Set `BASE_URL` to Railway-generated URL for bot service
  7. Add production Google OAuth redirect URI to Google Cloud Console
  8. Wait for deploy
  9. Check logs for both services
- **DoD:** Both services running. `/health` endpoint returns 200. Bot responds to messages.

---

#### Step A.40: Verify webhook mode
- **Tag:** MAAN
- **What:** Confirm bot works in webhook mode on Railway
- **Depends on:** A.39
- **Actions:**
  1. Send message to bot on Telegram
  2. Expected: bot responds (via webhook, not polling)
  3. Check Railway logs for webhook processing
  4. Test all core flows: text, voice, photos, calendar, search
- **DoD:** Bot fully functional in production environment.

---

### A-5: Phase A Acceptance Tests

---

#### Step A.41: Phase A acceptance test suite
- **Tag:** CLAUDE CODE + MAAN
- **What:** Run complete acceptance test checklist
- **Depends on:** A.40
- **Checklist (all must PASS):**

| # | Test | Expected | Pass/Fail |
|---|------|----------|-----------|
| 1 | Send /start to linked bot | Welcome message | |
| 2 | Send text: new client with full data | Parsed data shown, confirmation buttons | |
| 3 | Confirm client add | Data in Google Sheets | |
| 4 | Voice: describe client visit | Transcription → parse → confirm → Sheets | |
| 5 | Search: "Co mam o [name]?" | Client card shown | |
| 6 | Search with typo | "Czy chodziło o...?" suggestion | |
| 7 | Edit: "Zmień telefon [name]" | Old/new comparison, confirm | |
| 8 | Delete: "Usuń [name]" | Confirmation → row deleted | |
| 9 | Duplicate: add same name+city | Duplicate warning | |
| 10 | Add meeting: "Jutro o 10 do [name]" | Event details, confirm | |
| 11 | View schedule: "Co mam jutro?" | Day schedule shown | |
| 12 | Reschedule: "Przełóż [name] na piątek" | Old/new time, confirm | |
| 13 | Cancel meeting | Confirmation → event deleted | |
| 14 | Conflict detection | Warning when time overlaps | |
| 15 | Send photo → assign to client | Photo in Drive, link in Sheets | |
| 16 | Pipeline: "Ilu mam klientów?" | Count per status | |
| 17 | Status change: "[name] podpisał" | Status update proposal | |
| 18 | Morning brief received | Correct time, correct content | |
| 19 | Pre-meeting reminder received | Client data + address | |
| 20 | Follow-up prompt received | Lists unreported meetings | |
| 21 | Follow-up response processed | Statuses updated after confirm | |
| 22 | "odśwież kolumny" | Columns refreshed | |
| 23 | Rate limit at 80% | Warning + borrow offer | |
| 24 | Sticker sent | Fallback message | |
| 25 | Bot in group | Ignores silently | |

- **DoD:** ALL 25 tests pass. Phase A complete.

---

## Phase B: Dashboard + Onboarding + Payments

> **Goal:** Web dashboard at oze-agent.pl with full onboarding flow, payment integration, client/calendar/stats views, settings, and CSV import.

> **Note:** Dashboard frontend will be built using skill.md + nanobanana pro (Maan's preferred approach). This plan covers the FastAPI backend endpoints and the dashboard page specifications.

---

### B-0: FastAPI Backend — Full API

---

#### Step B.1: api/auth.py — JWT validation middleware
- **Tag:** CLAUDE CODE
- **What:** Supabase JWT validation for all authenticated endpoints
- **Depends on:** A.10
- **Files:**
  - `api/auth.py`:
    - `async def get_current_user(authorization: str = Header()) -> dict`
      - Extract Bearer token
      - Validate JWT using SUPABASE_JWT_SECRET (local validation, no round-trip)
      - Extract user_id from JWT
      - Fetch user from Supabase
      - Return user dict
    - `async def get_admin_user(user: dict = Depends(get_current_user)) -> dict`
      - Check `is_admin=True`
      - Raise 403 if not admin
  - `api/middleware.py`:
    - CORS configuration (restrict to dashboard domain in production)
    - Request logging middleware
    - Rate limiting middleware (login, webhooks, write endpoints)
- **DoD:** JWT validation works with Supabase-issued tokens.

---

#### Step B.2: api/routes/users.py — User management endpoints
- **Tag:** CLAUDE CODE
- **What:** CRUD for user data
- **Depends on:** B.1
- **Files:**
  - `api/routes/users.py`:
    - `GET /api/users/me` — current user profile
    - `PUT /api/users/me` — update profile (name, phone, address, age)
    - `PUT /api/users/me/settings` — update settings (morning_brief_hour, reminder_minutes, working_days, default_duration, pipeline_statuses)
    - `DELETE /api/users/me` — soft delete account
    - `POST /api/users/me/change-password` — change password
    - `GET /api/users/me/subscription` — subscription status + expiry
- **DoD:** All endpoints return correct responses with mocked auth.

---

#### Step B.3: api/routes/sheets.py — Sheets data for dashboard
- **Tag:** CLAUDE CODE
- **What:** Endpoints to read CRM data for dashboard display
- **Depends on:** B.1, A.2
- **Files:**
  - `api/routes/sheets.py`:
    - `GET /api/sheets/clients` — all clients (filterable by status, city, searchable)
    - `GET /api/sheets/clients/{row_number}` — single client detail
    - `GET /api/sheets/pipeline` — pipeline stats
    - `GET /api/sheets/columns` — current column headers
    - `PUT /api/sheets/columns` — update column configuration
    - `POST /api/sheets/columns/refresh` — force refresh headers
- **DoD:** Endpoints return Sheets data through FastAPI.

---

#### Step B.4: api/routes/calendar.py — Calendar data for dashboard
- **Tag:** CLAUDE CODE
- **What:** Calendar endpoints for dashboard
- **Depends on:** B.1, A.3
- **Files:**
  - `api/routes/calendar.py`:
    - `GET /api/calendar/events?start=&end=` — events in date range
    - `GET /api/calendar/events/today` — today's events
    - `GET /api/calendar/events/week` — this week's events
- **DoD:** Endpoints return Calendar data.

---

#### Step B.5: api/routes/payments.py — Przelewy24 integration
- **Tag:** CLAUDE CODE
- **What:** Payment flow with Przelewy24
- **Depends on:** B.1
- **Files:**
  - `api/routes/payments.py`:
    - `POST /api/payments/create-session` — create payment session (activation + first period)
    - `POST /webhooks/przelewy24` — handle payment confirmation webhook
      - Verify signature
      - Check idempotency (przelewy24_order_id)
      - Log to webhook_log (including duplicates)
      - Update user subscription_status to 'active'
      - Set subscription_expires_at
      - Log to payment_history
    - `GET /api/payments/history` — user's payment history
    - `POST /api/payments/renew` — create renewal payment session
    - Webhook idempotency: check order_id before processing
- **DoD:** Payment endpoints created. Webhook handler is idempotent.

---

#### Step B.6: api/routes/csv_import.py — CSV/Excel import
- **Tag:** CLAUDE CODE
- **What:** Bulk import leads from CSV/Excel files
- **Depends on:** B.1, A.2
- **Files:**
  - `api/routes/csv_import.py`:
    - `POST /api/import/upload` — upload file, return preview (first 10 rows + detected columns)
    - `POST /api/import/preview` — get column mapping suggestions
    - `POST /api/import/execute` — execute import with confirmed mapping
      1. Validate required fields (at minimum: "Imię i nazwisko")
      2. Check duplicates (name + city)
      3. Set default status "Nowy lead" if not mapped
      4. Append rows to Google Sheets
      5. Return summary: added count, skipped count, reasons
    - Supported formats: .csv, .xlsx, .xls
    - UTF-8 encoding handling (Polish characters)
- **DoD:** Import flow works end-to-end via API.

---

#### Step B.7: api/routes/broadcast.py — Broadcast queue
- **Tag:** CLAUDE CODE
- **What:** Broadcast message management (admin sends, bot delivers)
- **Depends on:** B.1
- **Files:**
  - `api/routes/broadcast.py`:
    - `POST /api/admin/broadcasts` — create broadcast (admin only)
    - `GET /api/admin/broadcasts` — list broadcasts with status
    - `GET /api/admin/broadcasts/{id}` — broadcast detail with delivery status
    - Broadcast saved to `admin_broadcasts` table
    - Bot scheduler picks up pending broadcasts and delivers via Telegram
- **DoD:** Broadcast CRUD works.

---

#### Step B.8: api/routes/admin.py — Admin endpoints
- **Tag:** CLAUDE CODE
- **What:** Admin panel API endpoints
- **Depends on:** B.1
- **Files:**
  - `api/routes/admin.py`:
    - `GET /api/admin/users` — all users with filters (status, plan)
    - `GET /api/admin/users/{id}` — user detail (data, payments, interactions, logs, cost)
    - `PUT /api/admin/users/{id}/suspend` — suspend user
    - `PUT /api/admin/users/{id}/unsuspend` — unsuspend user
    - `PUT /api/admin/users/{id}/extend` — extend subscription
    - `POST /api/admin/users/{id}/reset-oauth` — reset Google OAuth tokens
    - `POST /api/admin/users/create-beta` — create beta account (no payment required)
    - `POST /api/admin/users/{id}/send-message` — send Telegram message to user
    - `GET /api/admin/dashboard` — admin dashboard stats (users, revenue, API costs, margin)
    - `GET /api/admin/finances` — payment history, MRR, revenue/month
    - `GET /api/admin/logs` — API errors, health status
    - `POST /api/admin/impersonate/{id}` — get impersonation token (see user's dashboard)
- **DoD:** All admin endpoints return correct data structure.

---

#### Step B.9: Register all routes in api/main.py
- **Tag:** CLAUDE CODE
- **What:** Wire up all routers
- **Depends on:** B.1 through B.8
- **Files:**
  - Update `api/main.py`:
    ```python
    from api.routes.users import router as users_router
    from api.routes.sheets import router as sheets_router
    from api.routes.calendar import router as calendar_router
    from api.routes.payments import router as payments_router
    from api.routes.csv_import import router as import_router
    from api.routes.broadcast import router as broadcast_router
    from api.routes.admin import router as admin_router
    from api.routes.google_oauth import router as oauth_router
    
    app.include_router(oauth_router, prefix="/auth")
    app.include_router(users_router, prefix="/api")
    app.include_router(sheets_router, prefix="/api")
    app.include_router(calendar_router, prefix="/api")
    app.include_router(payments_router, prefix="/api")
    app.include_router(import_router, prefix="/api")
    app.include_router(broadcast_router, prefix="/api")
    app.include_router(admin_router, prefix="/api")
    ```
- **DoD:** `uvicorn api.main:app` starts. All routes listed in `/docs` (FastAPI auto-generated docs).

---

#### Step B.10: Unit tests for API endpoints
- **Tag:** CLAUDE CODE
- **Depends on:** B.9
- **Files:**
  - `tests/test_auth.py` — JWT validation, admin check
  - `tests/test_payments.py` — webhook idempotency, signature verification
  - `tests/test_csv_import.py` — column mapping, duplicate detection, validation
- **DoD:** `pytest tests/ -v` — all tests pass.

---

### B-1: Dashboard Specifications (for frontend build)

> Maan will build the frontend using skill.md + nanobanana pro. This section defines what each page needs.

---

#### Step B.11: Create dashboard specification document
- **Tag:** CLAUDE CODE
- **What:** Detailed spec for each dashboard page — components, data sources, API calls
- **Depends on:** B.9
- **Files:**
  - `docs/dashboard_spec.md`:
    - Per page:
      - Route, Polish name
      - Public (demo) vs authenticated behavior
      - API endpoints consumed
      - UI components needed (tables, charts, forms, buttons)
      - Data flow
      - Mobile considerations
      - Demo data specification
    - Pages covered:
      - `/` — landing/home
      - `/klienci` — clients table + calendar view
      - `/statystyki` — conversion charts
      - `/instrukcja` — "Poznaj swojego agenta" content
      - `/faq` — Q&A
      - `/platnosci` — subscription management
      - `/ustawienia` — settings
      - `/kontakt` — contact form
      - `/import` — CSV/Excel import
      - `/rejestracja` — registration + survey + payment
      - `/login` — login form
    - Demo data specification (20+ fictional clients)
    - Banner specification for public pages
- **DoD:** Complete spec document covering all pages.

---

#### Step B.12: Create design_system.md
- **Tag:** CLAUDE CODE
- **What:** Visual guidelines for dashboard
- **Depends on:** None
- **Files:**
  - `docs/design_system.md`:
    - Theme: Dark mode only
    - Background: #0A0A0B or similar deep dark
    - Accent color: #00FF88 (neon green)
    - Secondary: muted gray tones
    - Font recommendation: Inter or similar
    - Component styling: shadcn/ui defaults with dark theme
    - Border radius: shadcn defaults
    - Spacing system
    - Table styling
    - Chart color palette
    - Mobile breakpoints
    - Button variants (primary green, secondary outline, danger red)
    - Card styling
    - Navigation (sidebar on desktop, bottom nav on mobile)
    - Icons: Lucide
- **DoD:** Design system document complete.

---

#### Step B.13: Create onboarding flow specification
- **Tag:** CLAUDE CODE
- **What:** Detailed onboarding flow spec
- **Depends on:** B.11
- **Files:**
  - `docs/onboarding_spec.md`:
    - Step 1: Registration form (Google Sign-In OR email/password) + survey (6 fields + 3 checkboxes)
    - Step 2: Payment via Przelewy24 (activation + first period, Blik default)
    - Step 3: Google OAuth ("Zezwól" one click)
    - Step 4: Name resources (spreadsheet name + calendar name)
    - Step 5: Link Telegram (show 6-char code, valid 15 min, instruct /start in @OZEAgentBot)
    - Step 6: Bot welcome (automatic after linking)
    - Progress indicator
    - Error handling per step
    - "Zalecamy oddzielne konto Google" message placement
    - Estimated time: 3-4 minutes
- **DoD:** Onboarding spec complete.

---

#### Step B.14: Create demo data file
- **Tag:** CLAUDE CODE
- **What:** Hardcoded demo data for public dashboard
- **Depends on:** B.11
- **Files:**
  - `dashboard/lib/demo-data.ts` (or similar — for frontend):
    - 20+ fictional clients with Polish names and cities
    - Realistic OZE data (products, roof sizes, power consumption)
    - Full pipeline representation (clients in every status)
    - 1 month of fictional meeting history
    - 3-5 meetings per day in demo calendar
    - Demo statistics with conversion data
- **DoD:** Demo data file complete with realistic Polish data.

---

### B-2: Phase B Integration & Acceptance Tests

---

#### Step B.15: Deploy updated API to Railway
- **Tag:** MAAN
- **What:** Deploy all new API endpoints
- **Depends on:** B.9
- **Actions:**
  1. Push to `develop` branch
  2. Verify Railway deploy succeeds
  3. Test `/api/docs` on Railway URL
  4. Test key endpoints manually
- **DoD:** All API endpoints accessible on Railway.

---

#### Step B.16: Phase B acceptance tests
- **Tag:** MAAN + CLAUDE CODE
- **What:** Full acceptance test for Phase B
- **Depends on:** B.15 + dashboard built by Maan

| # | Test | Expected | Pass/Fail |
|---|------|----------|-----------|
| 1 | Registration flow complete | Account created, survey saved | |
| 2 | Payment via Przelewy24 (sandbox) | Status → active | |
| 3 | Google OAuth in onboarding | Tokens stored | |
| 4 | Telegram linking code | 6-char code generated, expires in 15 min | |
| 5 | /start with code | User linked | |
| 6 | Dashboard login | JWT issued, protected pages accessible | |
| 7 | Clients table loads | Shows data from Sheets | |
| 8 | Client card detail | All fields + photos + meetings | |
| 9 | Calendar view | Meetings displayed, dark theme | |
| 10 | Statistics page | Conversion charts render | |
| 11 | Settings page | Changes saved, reflected in bot behavior | |
| 12 | CSV import | Upload → preview → map → import → data in Sheets | |
| 13 | Contact form | Email sent to admin | |
| 14 | Instruction page | Full "Poznaj swojego agenta" content | |
| 15 | FAQ page | Q&A renders | |
| 16 | Payment page | Subscription management works | |
| 17 | Demo mode | Public pages show demo data + banner | |
| 18 | Mobile responsive | All pages usable on phone | |
| 19 | Session expiry | After 30 days inactivity, re-login required | |
| 20 | Password reset | Email link works | |

- **DoD:** ALL 20 tests pass.

---

## Phase C: Admin Panel

---

#### Step C.1: Admin panel specification
- **Tag:** CLAUDE CODE
- **What:** Detailed spec for admin panel pages
- **Depends on:** B.8
- **Files:**
  - `docs/admin_panel_spec.md`:
    - Dashboard: active/expired/pending users, revenue, API costs, margin, trends
    - Users: list + filters + detail card (data, payments, interactions, logs, cost per user)
    - User actions: block/unblock, reset OAuth, extend subscription, send message, impersonate, create beta
    - Promo codes: CRUD (NOT on MVP — placeholder page)
    - Broadcasts: create, send, history, preview, delivery status
    - Logs: API errors, health status, Sentry link, active alerts
    - Finances: all payments, revenue/month chart, MRR
    - Auth: `is_admin=true` check on every request
    - Impersonation: "login as user" to see user's dashboard view
- **DoD:** Admin panel spec complete.

---

#### Step C.2: Admin panel backend — all endpoints already built in B.8
- **Tag:** N/A — already done
- **Note:** All admin API endpoints were built in Step B.8. This step confirms they're tested.

---

#### Step C.3: Bot scheduler — broadcast queue processor
- **Tag:** CLAUDE CODE
- **What:** Scheduler job to process broadcast queue
- **Depends on:** A.27, B.7
- **Files:**
  - `bot/scheduler/broadcast.py`:
    - `async def process_broadcast_queue(context)`
      1. Get pending broadcasts from Supabase
      2. For each broadcast:
         - Set status to 'processing'
         - Get target users (all active or specific)
         - Send messages in batches (respect Telegram rate limits: 30 msg/sec)
         - Update sent_count, failed_count
         - Set status to 'completed' or 'failed'
      3. Log results
    - Scheduler: runs every 1 minute
- **DoD:** Broadcast queue processor works. Admin can send broadcast → users receive.

---

#### Step C.4: Phase C acceptance tests
- **Tag:** MAAN
- **What:** Admin panel acceptance tests
- **Depends on:** C.1 through C.3

| # | Test | Expected | Pass/Fail |
|---|------|----------|-----------|
| 1 | Admin login | Access granted with is_admin=true | |
| 2 | Non-admin blocked | 403 error | |
| 3 | User list loads | All users with status, plan | |
| 4 | User detail card | Full data, payments, interactions | |
| 5 | Suspend user | User sees expiry message in bot + dashboard | |
| 6 | Unsuspend user | User returns to pre-suspension state | |
| 7 | Create beta account | Account created without payment | |
| 8 | Send broadcast to all | All active users receive message | |
| 9 | Send broadcast to one | Specific user receives | |
| 10 | Broadcast delivery status | Correct sent/failed counts | |
| 11 | Impersonate user | See user's dashboard view | |
| 12 | Finance dashboard | Revenue, MRR, payment history | |
| 13 | Reset user OAuth | Tokens cleared, user prompted to re-auth | |
| 14 | Extend subscription | Expiry date updated | |
| 15 | Logs page | API errors visible, health status | |

- **DoD:** ALL 15 tests pass.

---

## Phase D: Monitoring, Recovery, Polish

---

#### Step D.1: Sentry integration
- **Tag:** MAAN + CLAUDE CODE
- **What:** Setup Sentry error tracking
- **Actions (MAAN):**
  1. Create Sentry account (free tier)
  2. Create project (Python, FastAPI)
  3. Copy DSN to `.env` and Railway env vars
- **Files (CLAUDE CODE):**
  - Update `bot/main.py`: initialize Sentry SDK
  - Update `api/main.py`: initialize Sentry SDK with FastAPI integration
  - Add Sentry breadcrumbs to key functions (API calls, DB operations)
- **DoD:** Errors appear in Sentry dashboard.

---

#### Step D.2: Gmail SMTP setup
- **Tag:** MAAN
- **What:** Configure Gmail for sending emails
- **Actions:**
  1. Go to Google Account → Security → 2-Step Verification (enable if not)
  2. Generate App Password (name: "OZE-Agent SMTP")
  3. Copy to `.env` as `GMAIL_SMTP_PASSWORD`
  4. Set `GMAIL_SMTP_USER` to your Gmail address
- **DoD:** App Password generated and in `.env`.

---

#### Step D.3: shared/email.py — Email sending
- **Tag:** CLAUDE CODE
- **What:** Gmail SMTP email sending
- **Depends on:** D.2
- **Files:**
  - `shared/email.py`:
    - `async def send_email(to: str, subject: str, body_html: str) -> bool`
      - Gmail SMTP with TLS
      - Polish email templates
    - `async def send_welcome_email(user_email: str, user_name: str)`
    - `async def send_subscription_reminder_email(user_email: str, days_remaining: int)`
    - `async def send_payment_confirmation_email(user_email: str, amount: float, plan: str)`
    - `async def send_admin_alert_email(subject: str, body: str)`
- **DoD:** Test email sends successfully.

---

#### Step D.4: bot/scheduler/backup_export.py
- **Tag:** CLAUDE CODE
- **What:** Weekly backup of critical tables to admin's Google Drive
- **Depends on:** A.4, A.27
- **Files:**
  - `bot/scheduler/backup_export.py`:
    - `async def export_backup(context)`
      1. Export tables to JSON: users, payment_history, promo_codes
      2. Upload to admin's Google Drive
      3. Filename: `backup_YYYY-MM-DD.json`
    - Scheduler: weekly, Sunday 04:00
- **DoD:** Backup JSON appears in admin's Drive.

---

#### Step D.5: Create legal documents
- **Tag:** CLAUDE CODE
- **What:** Regulamin (terms) and privacy policy templates
- **Depends on:** None
- **Files:**
  - `docs/regulamin.md`:
    - Polish language
    - Covers: service description, subscription terms, payment terms, data handling, cancellation, liability
    - Maximum legally permissible flexibility for admin regarding user data and client data collected by users
    - RODO/GDPR compliance basics
    - Admin access to ALL data explicitly documented
    - No refunds policy
    - Account deletion = soft delete, data retained
  - `docs/polityka_prywatnosci.md`:
    - Polish language
    - Data collected: user personal data, Google account data, CRM data (client data)
    - Data processing purposes
    - Admin access rights explicitly stated
    - Data retention policy
    - Third parties: Google, Anthropic (AI processing), OpenAI (transcription), Przelewy24 (payments), Supabase (database)
    - User rights under RODO
    - Contact information
- **DoD:** Both documents created. Maan reviews and approves.

---

#### Step D.6: Update README.md
- **Tag:** CLAUDE CODE
- **What:** Complete README with setup instructions
- **Depends on:** All previous steps
- **Files:**
  - `README.md`:
    - Project description
    - Architecture diagram (ASCII)
    - Tech stack
    - Prerequisites (accounts needed)
    - Setup instructions:
      1. Clone repo
      2. Create virtual environment
      3. Install dependencies
      4. Create Supabase project + run schema
      5. Create Google Cloud project + OAuth
      6. Create Telegram bots
      7. Configure `.env`
      8. Run locally
      9. Deploy to Railway
    - Environment variables reference
    - Directory structure
    - Development workflow (branches, PRs)
    - Deployment instructions
- **DoD:** New developer can set up the project following README.

---

#### Step D.7: Final acceptance_criteria.md
- **Tag:** CLAUDE CODE
- **What:** Complete acceptance criteria document
- **Depends on:** All previous steps
- **Files:**
  - `docs/acceptance_criteria.md`:
    - All acceptance tests from Phases A, B, C combined
    - 15 critical flow areas from brief
    - Pass/Fail checklist format
    - Edge cases documented
    - Error scenarios documented
- **DoD:** Document complete.

---

#### Step D.8: Production deployment
- **Tag:** MAAN
- **What:** Deploy to production
- **Actions:**
  1. Merge `develop` → `main`
  2. Railway auto-deploys production
  3. Set `ENV=prod`
  4. Set production `BASE_URL`
  5. Configure custom domain (when domain decided)
  6. Update Google OAuth redirect URIs for production
  7. Update Przelewy24 webhook URL for production
  8. Switch Telegram bot from dev to production token
  9. Verify all services running
  10. Run full acceptance test suite on production
- **DoD:** Production environment fully functional.

---

#### Step D.9: Final integration test — Full user journey
- **Tag:** MAAN
- **What:** Complete end-to-end test simulating real user
- **Actions:**
  1. Register new account via dashboard
  2. Complete payment
  3. Authorize Google
  4. Name resources
  5. Link Telegram with code
  6. Receive welcome message
  7. Add 3 clients via voice
  8. Add 5 clients via text
  9. Import 10 clients via CSV
  10. Schedule meetings for tomorrow
  11. Wait for morning brief next day
  12. Go to meetings, receive reminders
  13. After meetings, respond to follow-up
  14. Check dashboard: clients, calendar, stats
  15. Change settings
  16. Check admin panel: user visible, finance data correct
  17. Send broadcast from admin
  18. Suspend user, verify blocking works
  19. Unsuspend, verify recovery
  20. Renew subscription
- **DoD:** Full user journey works without issues. OZE-Agent MVP is complete.

---

## Summary — Step Count by Phase

| Phase | Steps | Focus |
|-------|-------|-------|
| Phase 0 | 0.1 — 0.13 | Infrastructure, repo, env, accounts |
| Phase A | A.1 — A.41 | Working bot with all features |
| Phase B | B.1 — B.16 | Dashboard backend + specs + payments |
| Phase C | C.1 — C.4 | Admin panel |
| Phase D | D.1 — D.9 | Monitoring, email, backups, legal, deploy |
| **Total** | **~83 steps** | |

---

## Dependency Graph (Critical Path)

```
0.1 → 0.2 → 0.3/0.4/0.5 → 0.6 → 0.7 → 0.8/0.9
                                      ↓
                              A.1 → A.2/A.3/A.4 → A.5/A.6/A.7/A.8/A.9
                                                          ↓
                                              A.10 → A.11 → A.12 → A.13/A.14/A.15/A.16/A.17/A.18
                                                                              ↓
                                                              A.19 → A.20 → A.21 → A.22-A.26 (E2E tests)
                                                                                          ↓
                                                                              A.27-A.34 (Scheduler)
                                                                                          ↓
                                                                              A.35-A.37 (Scheduler tests)
                                                                                          ↓
                                                                              A.38-A.40 (Deploy)
                                                                                          ↓
                                                                              A.41 (Acceptance)
                                                                                          ↓
                                                                    B.1-B.10 (API) → B.11-B.14 (Specs)
                                                                                          ↓
                                                                              B.15-B.16 (Deploy + Accept)
                                                                                          ↓
                                                                              C.1-C.4 (Admin)
                                                                                          ↓
                                                                              D.1-D.9 (Polish + Prod)
```

---

## CLAUDE.md — Instructions for Claude Code

When starting work on this project, Claude Code should:

### Execution Rules
1. **Read this entire plan** before writing any code
2. **Execute steps in exact order** — never skip ahead
3. **Phase A is the priority.** Do not start Phase B until Phase A passes ALL 25 acceptance tests.
4. **Verify DoD after each step** before proceeding
5. **Commit after each step** with message: `"Step X.Y: [description]"`
6. **If a step is too large** (e.g., a module with 8+ functions), split it into smaller internal substeps. Report the split to Maan before coding. This is expected and encouraged.
7. **If a step fails:** Stop, report the error, wait for Maan's guidance
8. **If something is unclear:** Ask Maan before guessing
9. **When implementation reality conflicts with the plan** (library API changed, pattern doesn't work), STOP and explain the conflict clearly. Don't force the plan — adapt it.
10. **Prefer working code over overengineered code.** Get it running, then refine.

### Code Standards
11. **All Python code:** Type hints, docstrings, try/except with logging on external calls
12. **All user-facing text:** Polish language
13. **All AI prompts:** Polish language (as specified in brief)
14. **Async pattern:** Use `async` for Telegram handlers, Anthropic, OpenAI. Use `asyncio.to_thread()` for synchronous Google API calls where needed.

### Architectural Rules (non-negotiable)
15. **Shared services rule:** ALL business logic in `shared/`. Bot and API import only. Zero duplication.
16. **Source of truth rule:** CRM data → Google. System data → Supabase. Never mix.
17. **No temporary CRM storage:** If Google is down, inform user and wait. Never cache CRM data in Supabase.
18. **Confirmation rule:** Agent NEVER writes to Sheets/Calendar/Drive without user confirmation.
19. **Error messages:** Always in Polish, always user-friendly, always identify the source of the problem.

---

*End of Implementation Plan v1.1*
