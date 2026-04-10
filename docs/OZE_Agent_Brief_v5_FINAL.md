# OZE-Agent — Technical Brief v5 (FINAL) for Claude Code

## Project overview

Build a complete AI-powered sales assistant called **OZE-Agent** for B2C renewable energy (OZE) salespeople in Poland. The system consists of a Telegram bot (primary interface), a Next.js web dashboard (settings, analytics, payments, demo), and an admin panel. Everything is built from scratch in a new repository (`oze-agent`).

**Target user:** Field salesperson who drives between client homes selling photovoltaics, heat pumps, energy storage, and air conditioning. They have 3-6 meetings daily, need to log data fast (preferably by voice), and forget follow-ups constantly. Many have never used an AI agent before.

**Language:** Polish only — all UI, bot messages, AI prompts, and responses in Polish.

**Branding:** OZE-Agent. Telegram bot: @OZEAgentBot. Dev bot: @OZEAgentDevBot. Dashboard: oze-agent.pl. Admin panel: admin.oze-agent.pl

---

## Architecture overview

```
┌─────────────────────────────────────────────────────────┐
│                    INPUT LAYER                          │
│  Telegram Bot          Web Dashboard       Scheduler    │
│  (text+voice+photos)   (Next.js/Vercel)   (APScheduler)│
│  [webhook mode]        [mobile-first]      [in bot proc]│
└──────────┬─────────────────┬──────────────────┬─────────┘
           │                 │                  │
           ▼                 ▼                  ▼
┌─────────────────────────────────────────────────────────┐
│              SHARED SERVICES LAYER                      │
│  claude_ai.py | whisper_stt.py | google_sheets.py       │
│  google_calendar.py | google_drive.py | google_auth.py  │
│  followup.py | search.py | formatting.py                │
│  (imported by bot, FastAPI, AND scheduler — NO duplication)│
└──────────┬─────────────────┬──────────────────┬─────────┘
           │                 │                  │
           ▼                 ▼                  ▼
┌─────────────────────────────────────────────────────────┐
│                   STORAGE LAYER                         │
│  Supabase            Google Sheets    Google Calendar    │
│  (PostgreSQL)        (CRM per user)   (per user)        │
│                      Google Drive (photos per client)    │
└─────────────────────────────────────────────────────────┘
```

---

## Tech stack

| Component | Technology | Hosting |
|-----------|-----------|---------|
| Telegram bot | Python 3.3 + python-telegram-bot 21.x | Railway (process 1, webhook mode) |
| API for dashboard | FastAPI | Railway (process 2, separate from bot) |
| AI — complex tasks | Claude Sonnet 4.6 | API calls |
| AI — simple tasks | Claude Haiku 4.5 | API calls |
| AI — speech-to-text | Whisper API (OpenAI, $0.006/min) | API calls |
| Database | Supabase (PostgreSQL) | Supabase Cloud |
| CRM data | Google Sheets API v4 | Google Cloud |
| Calendar | Google Calendar API v3 | Google Cloud |
| Photo storage | Google Drive API v3 | Google Cloud |
| Web dashboard | Next.js 14 + shadcn/ui + Tailwind CSS | Vercel |
| Admin panel | Next.js 14 + shadcn/ui + Tailwind CSS | Vercel |
| Payments | Przelewy24 (Blik, card, transfer) | External |
| Scheduler | APScheduler (in bot process) | Railway |
| Error tracking | Sentry (free tier) | Sentry Cloud |
| Analytics | Vercel Analytics (free) | Vercel |
| Emails | Gmail SMTP | Google |
| Auth | Supabase Auth (Google Sign-In + email/password) | Supabase |

---

## Source of truth

| Data | Source of truth | Secondary/cache |
|------|----------------|-----------------|
| Client CRM data | Google Sheets (user's) | — |
| Calendar events | Google Calendar (user's) | — |
| Client photos | Google Drive (user's) | — |
| Sheet column headers | Google Sheets (user's) | Supabase cache (refresh every 6h + manual "odśwież kolumny" command in bot) |
| User accounts | Supabase | — |
| User settings | Supabase | — |
| Google OAuth tokens | Supabase (Fernet encrypted) | — |
| Subscription status | Przelewy24 (source) | Supabase (copy, updated via webhook) |
| Payment history | Supabase | — |
| Interaction logs | Supabase | — |
| Conversation history | Supabase (temporary, cleaned after 24h) | — |
| Pending flows | Supabase (temporary) | — |
| Pending followups | Supabase (temporary) | — |
| User habits | Supabase (calculated from logs) | — |
| Promo codes | Supabase (NOT on MVP) | — |

**Key rule:** CRM data lives in Google. System data lives in Supabase. No CRM data is cached in Supabase. If Google is down, bot informs user and waits — does NOT write to Supabase as temporary storage.

---

## Component boundaries

### BOT (Python, Railway process 1)
**Owns:** Telegram webhook endpoint, message processing, Whisper calls, Claude calls, Google API operations (Sheets/Calendar/Drive), conversation memory, inline buttons, proactive messages (brief/reminder/follow-up)
**Does NOT:** Handle auth, registration, payments, serve dashboard data

### FASTAPI (Python, Railway process 2)
**Owns:** REST API for dashboard + admin panel, Supabase Auth JWT validation, Google OAuth redirect handling, Przelewy24 webhook, CRUD on Supabase, reading Google data for dashboard display (Sheets data + Calendar events), broadcast queue management (saves to Supabase, bot picks up), health check endpoint, CSV import processing
**Does NOT:** Process Telegram messages, call Whisper/Claude, send Telegram messages directly (delegates to bot via broadcast queue or Telegram Bot API for simple sends)

### Auth flow (Supabase Auth + FastAPI)
Dashboard logs user in via Supabase Auth → Supabase issues JWT → dashboard sends JWT in `Authorization: Bearer <token>` header on every FastAPI request → FastAPI validates JWT locally using `SUPABASE_JWT_SECRET` env var (no round-trip to Supabase per request) → extracts `user_id` from JWT → for admin endpoints, additionally checks `is_admin` in Supabase.

### SCHEDULER (APScheduler, in bot process)
**Owns:** Timed jobs (brief, reminders, follow-ups, token refresh, column sync, subscription check, habit calc, cleanup, health check, backup export, broadcast queue processing)
**Does NOT:** Handle user input directly

### DASHBOARD (Next.js, Vercel, oze-agent.pl)
**Owns:** Frontend UI for users, calls FastAPI endpoints only
**Does NOT:** Access Supabase or Google API directly

### ADMIN PANEL (Next.js, Vercel, admin.oze-agent.pl)
**Owns:** Admin frontend, calls FastAPI endpoints (with admin auth)
**Does NOT:** Access Supabase directly

### SHARED SERVICES (Python modules imported by bot, FastAPI, scheduler)
`google_sheets.py`, `google_calendar.py`, `google_drive.py`, `google_auth.py`, `claude_ai.py`, `whisper_stt.py`, `followup.py`, `search.py`, `formatting.py`
**Rule:** ALL business logic lives in shared services. Bot, FastAPI, and scheduler import these — never duplicate logic.

---

## AI model routing

| Task type | Model | Examples |
|-----------|-------|---------|
| Complex | Claude Sonnet 4.6 ($3/$15 per MTok) | Voice parsing, follow-up conversations, multi-step flows, ambiguous requests |
| Simple | Claude Haiku 4.5 ($1/$5 per MTok) | Show plan, find client, confirmations, pipeline summary, formatting |

Estimated cost: ~$2.50/month per user.

---

## Roles and permissions

### MVP: 2 roles

| Role | Access |
|------|--------|
| User (handlowiec) | Bot (full), Dashboard (own data only), own Google resources |
| Admin | Admin panel (ALL users, ALL data, ALL logs), impersonation ("login as user"), bot (same as user for own account) |

**Admin sees EVERYTHING:** client data, conversation logs, Sheets content. This must be documented in privacy policy.

**Admin impersonation:** Admin can "login as user" in admin panel to see exactly what user sees in dashboard — for debugging purposes.

**Role check:** `is_admin=true` in Supabase users table. Admin panel middleware checks this on every request.

---

## Subscription and user lifecycle

### Pricing
| Item | Price |
|------|-------|
| Activation (one-time) | 199 zł |
| Monthly | 49 zł/month |
| Yearly | 350 zł/year |

**No promo codes on MVP.** Beta testers get accounts created manually by admin in admin panel (full access, no payment required).

### Lifecycle states
```
pending_payment → active → [suspended | expired] → [reactivated | deleted_soft]
```

| State | Bot behavior | Dashboard | Trigger |
|-------|-------------|-----------|---------|
| pending_payment | Link to registration | Registration flow | New signup |
| active | Full functionality | Full access | Payment confirmed |
| suspended | "Subskrypcja wygasła, wykup dostęp" + link | Limited (payment page only) | Admin suspends |
| expired | Same as suspended | Same | Subscription period ended |
| reactivated | Full (returns to pre-suspension state) | Full | Admin unblocks OR user pays again |

**Suspension by admin:** One-click in admin panel. User sees same message as expired subscription. No re-activation fee needed when admin unblocks.

**Account deletion:** User clicks "Usuń konto" → account marked as deleted but ALL data kept in Supabase forever (can be reactivated by admin). Google resources remain on user's Google account.

**Plan change:** Monthly→yearly: immediate, pays full yearly. Yearly→monthly: active until end of yearly period, then switches.

**No refunds.**

### Subscription reminders
- 3 days before expiry: Telegram message + link to payment
- Day of expiry: Telegram message + link
- After expiry: bot responds only with expiry message

### Emails (Gmail SMTP)
- Welcome email after registration + payment
- 3 days before subscription expiry
- Payment confirmation after each payment

---

## Onboarding flow

1. **Registration + Survey** (one form on dashboard):
   - Google Sign-In OR email + password
   - 6 survey fields: name, address, age, products, referral source, phone
   - 3 checkboxes: terms (required), marketing (optional), phone contact (optional)
   - Message: "Zalecamy oddzielne konto Google dla OZE-Agent (15 GB)"

2. **Payment:** Przelewy24 (activation + first period, Blik default)

3. **Google OAuth:** One click "Zezwól" (Sheets + Calendar + Drive)

4. **Name resources:** User names their spreadsheet and calendar

5. **Link Telegram:** 6-char code (valid 15 min), /start in @OZEAgentBot

6. **Bot welcome:** Short message + link to "Poznaj swojego agenta"

**Total: ~3-4 minutes.**

---

## Agent behavior

### Communication
- Concrete, brief, no filler. Like a sharp colleague.
- Emoji + Telegram formatting (bold, lists).
- Mobile-optimized — short messages.
- Typing indicator always during processing.
- Processing stages for voice: "🎙️ Transkrybuję..." → "🔍 Analizuję..."

### Confirmations
Agent NEVER writes to Sheets/Calendar/Drive without user confirmation. Inline buttons [Tak] [Nie] for closed questions — but user can always type or record voice instead. Buttons are shortcuts, never the only option.

### Minimize interactions
Extract max from one message. List ALL missing fields at once. User fills in one reply or says "zapisz tak jak jest".

### Cancellation
"Nie" → agent asks "Anulować?" → confirms → data discarded.

### Incomplete flows
Data saved in `pending_flows` (zero cost). Reminder after 30 min (once). Waits indefinitely.

### Voice handling
1. Whisper transcribes → show transcription ONLY if low confidence. Otherwise proceed directly.
2. If shown: user confirms, corrects by text, or re-records.
3. 60-second timeout → "Wystąpił problem, spróbuj ponownie"

### Agent does NOT:
- Suggest actions unprompted
- Contact clients
- Generate quotes
- Give sales advice
- Remind about inactive clients
- Respond in groups (private only)
- Respond when subscription expired/suspended

### Agent DOES proactively:
- Morning brief (working days only)
- Pre-meeting reminder (with client data from Sheets)
- Post-meeting follow-up (after last meeting of the day)

### Forwarded messages
Agent processes forwarded messages from other chats normally — no restrictions on message origin.

### Lejek sprzedażowy (pipeline) in bot
When user asks "ilu mam klientów?" or similar — agent responds with short numeric summary (count per status) + link to dashboard for details. Does NOT list individual clients.

### Admin in bot
Admin does NOT have special commands in the Telegram bot. All admin operations happen exclusively in the admin panel (admin.oze-agent.pl).

### Interaction limits
- 100/day default
- Alert at 80%: user informed + option to borrow max 20 from tomorrow (tomorrow then has 80)
- User informed about borrowing
- Logged in interaction_log with model used, tokens, cost

### Memory
- Last 10 messages OR 30 min (whichever shorter)
- Cleanup: delete conversation_history > 24h (daily 03:00)

### Habits (MVP)
- Only: default meeting duration (calculated from last 10-20 meetings)
- Stored in user_habits table
- Always overridable by user

---

## CRM — Google Sheets

### Protected columns (cannot be deleted):
Imię i nazwisko, Adres, Telefon, Status, Notatki

### Default columns (17):
Imię i nazwisko, Telefon, Adres, Miejscowość, Metraż domu (m²), Metraż dachu (m²), Kierunek dachu, Zużycie prądu (kWh/rok), Produkt, Moc proponowana (kW), Status, Źródło leada, Data pierwszego kontaktu, Data ostatniego kontaktu, Data następnego kontaktu, Notatki, Zdjęcia

Single tab, Status column. Headers cached in Supabase (refresh every 6h + manual "odśwież kolumny" command). Agent adapts to custom columns.

### Pipeline statuses (default, editable in dashboard):
["Nowy lead", "Spotkanie umówione", "Spotkanie odbyte", "Oferta wysłana", "Negocjacje", "Podpisane", "Zamontowana", "Rezygnacja z umowy", "Nieaktywny", "Odrzucone"]

### Search
Fuzzy, case-insensitive, typo-tolerant. "Kowalsky" → "Czy chodziło o Kowalskiego?" Multiple matches → list with cities. 50+ clients → link to Sheets.

### Duplicate detection
Agent checks if client with same name + city exists. If yes: informs user, asks whether to add new one anyway. User decides.

### Editing
Agent asks: "Zostawić stary [numer/adres] i dodać drugi, czy usunąć stary?" Shows old vs new before confirming.

### Addresses
Saved in both Sheets AND Calendar event location field. Duplicate city names → agent asks for postal code.

---

## Calendar

- Dedicated OZE calendar per user (does not see personal calendar)
- Default duration: 60 min (configurable in settings, learns from habits)
- Conflict detection: warns, allows after confirmation
- Rescheduling: shows client + old/new date → confirms → updates Calendar + Sheets
- No recurring events on MVP
- User can browse/delete via native Google Calendar app

### Working days
Configurable in settings (default Mon-Fri). Morning brief only on working days.

---

## Client ↔ Calendar linking

- Meeting with existing client → auto-link, update "Data następnego kontaktu" in Sheets
- Meeting with NEW client → create event, then ask: "Dodać do bazy? Którego tak, którego nie?"
- Multiple meetings in one message → batch create events, then ask about new clients

---

## Photos

- Attachments only (NO OCR)
- Google Drive: `OZE Klienci - [user]/[Klient] - [Miasto]/`
- Link in "Zdjęcia" column in Sheets
- Multiple photos batched to same client

---

## CSV/Excel import (Dashboard)

Dashboard feature for bulk importing leads from external sources (Facebook, old databases, Excel files).

### Flow:
1. User uploads CSV or Excel file on dashboard
2. System shows preview of data (first 10 rows)
3. User maps file columns to CRM columns (dropdown per column)
4. User confirms mapping
5. System validates data and shows summary: "Dodaję 47 klientów. 3 mają brakujące wymagane pola."
6. User confirms → system appends rows to Google Sheets
7. Summary: "Dodano 47 klientów. Pominięto 3 (brakujące dane)."

### Rules:
- Supported formats: .csv, .xlsx, .xls
- UTF-8 encoding (Polish characters)
- Duplicate check: warn if name + city already exists, user decides
- Protected columns must have values (at minimum: Imię i nazwisko)
- Status defaults to "Nowy lead" if not mapped

---

## Follow-up engine

After last meeting of the day → agent lists unreported meetings → user responds (voice/text) covering all at once → Claude parses → updates statuses (with confirmation) → proposes follow-ups.

---

## Claude system prompt (voice parsing)

```
Jesteś asystentem handlowca OZE w Polsce. Użytkownik nagrał notatkę głosową po spotkaniu.
Transkrypcja: "{transcription}"
Kolumny w arkuszu: {user_columns_json}
Dzisiejsza data: {today}
Nawyki użytkownika: domyślna długość spotkania = {default_duration} min

Wyciągnij WSZYSTKIE dane pasujące do kolumn. Zwróć TYLKO JSON:
{
  "client_data": {"kolumna": "wartość", ...},
  "missing_columns": ["kolumna1", "kolumna2"],
  "suggested_followup": {
    "action": "opis",
    "deadline": "data jeśli wspomniano",
    "calendar_event_title": "proponowany tytuł"
  }
}

Zasady:
- Produkty mapuj na: PV, Pompa ciepła, Magazyn energii, Klimatyzacja
- Tytuły po polsku: "Spotkanie z [imię]", "Wycena dla [nazwisko]"
- NIE dodawaj pól których nie ma w transkrypcji
- missing_columns = kolumny z arkusza BEZ wartości w transkrypcji
- Daty: "do środy", "w przyszłym tygodniu", "za 3 dni"
- Bądź zwięzły. Nie dodawaj komentarzy.
- Jeśli wspomniany adres, zapisz go w formacie: ulica numer, miejscowość
```

---

## Automated features

| Feature | When | Content |
|---------|------|---------|
| Morning brief | Daily, user's hour, working days only | Meetings + addresses + client notes + free slots + pending follow-ups + pipeline stats |
| Pre-meeting reminder | X min before (configurable) | Client name + address + phone + notes from Sheets |
| Post-meeting follow-up | After last meeting of day | List unreported meetings, user responds in bulk |

---

## Google API failure handling

**Sheets/Calendar/Drive API down:**
- Bot informs user clearly: "Google Sheets jest chwilowo niedostępny. Twoje dane NIE zostały zapisane. Spróbuj ponownie za kilka minut."
- No temporary storage in Supabase (source of truth = Google)
- No auto-retry queue on MVP
- Message clearly identifies the source of the problem (Google, not OZE-Agent)

**Google OAuth token expired/revoked:**
1. Auto-attempt refresh token
2. If refresh fails → bot sends: "Integracja Google wymaga ponownej autoryzacji" + link to dashboard re-auth page

---

## Idempotency

### Przelewy24 webhooks
- Check order_id before processing — ignore duplicates
- Log EVERY webhook (including duplicates) to audit table
- Idempotent: processing same webhook 2x has same result as processing it once

### Telegram webhooks
- Deduplicate by update_id
- Ignore already-processed update_ids

### Sheets writes
- Agent checks for existing client (name + city) before adding
- Informs user if duplicate found, user decides

---

## User policies

### Suspension (by admin)
- One-click in admin panel
- Bot shows: "Subskrypcja wygasła, wykup dostęp" + payment link
- Dashboard: limited to payment page
- No re-activation fee when admin unblocks
- Unblocking: admin one-click, user returns to pre-suspension state with all data

### Account deletion (by user)
- User clicks "Usuń konto" in settings
- Account soft-deleted: marked as deleted, ALL data kept in Supabase forever
- Google resources remain on user's Google account
- Can be reactivated by admin

### Unregistered user messages bot
- Bot responds with: link to oze-agent.pl + info about buying access

---

## Backup and recovery

### Primary: Supabase built-in backups
- Free tier: every 7 days
- Paid ($25/mo): daily with point-in-time recovery

### Secondary: Periodic export to admin's Google Drive
- Scheduler job: weekly export of critical tables (users, payment_history, promo_codes) as JSON
- Stored on admin's Google Drive

### Recovery plan
1. Admin restores Supabase from backup
2. System auto-detects users needing Google re-authorization (token validation on next interaction)
3. Bot sends re-auth request to affected users automatically

---

## Demo data (public dashboard)

- Hardcoded in frontend code
- 20+ realistic fictional clients with Polish names and cities
- Full pipeline representation (clients in every status)
- 1 month of fictional history (meetings, status changes)
- Realistic OZE data (products, roof sizes, power consumption)
- 3-5 meetings per day in demo calendar
- Demo statistics with conversion charts

---

## Dashboard (oze-agent.pl)

### Design
- Dark theme, minimalist, professional, mobile-first
- shadcn/ui + Tailwind CSS
- Supabase Auth (Google Sign-In + email/password)
- Sessions: expire after 30 days of inactivity
- Password reset: via email link

### Pages

| Route | Polish name | Public (demo) | Auth (real data) |
|-------|------------|---------------|-----------------|
| `/` | Strona główna | Landing page (placeholder on MVP — separate workflow later) | Dashboard home with news + daily summary |
| `/klienci` | Klienci i kalendarz | Demo table + demo calendar | Real client table (filterable by status + city, searchable, click → client card with ALL data from Sheets + photos from Drive + meeting history from Calendar) + own calendar view (list of meetings per day/week, fetched via FastAPI → Google Calendar API, styled in dark theme — NOT iframe) |
| `/statystyki` | Statystyki | Demo charts | Real conversion charts |
| `/instrukcja` | Poznaj swojego agenta | Full instruction (same for all) | Same |
| `/faq` | FAQ | Q&A (same for all) | Same |
| `/platnosci` | Płatności | Pricing + CTA | Subscription management |
| `/ustawienia` | Ustawienia | Demo settings view | Columns, statuses, brief hour, reminders, working days, default duration, Google account, Profile (personal data, password) |
| `/kontakt` | Kontakt | Contact form (works — sends email to admin) | Same |
| `/rejestracja` | Rejestracja | Registration + survey + payment | — |
| `/login` | Logowanie | Login form | — |
| `/import` | Import klientów | — | CSV/Excel upload + column mapping |

**No kanban on MVP** (removed).

Banner on public pages: "To jest wersja demonstracyjna. Załóż konto żeby korzystać z własnego agenta."

---

## Admin panel (admin.oze-agent.pl)

Access: `is_admin=true` only. Separate Next.js app.

| Section | Content |
|---------|---------|
| Dashboard | Users (active/expired/pending), revenue, API costs, margin, trends |
| Users | List + filters + detail card (data, payments, interactions, logs, cost per user). Actions: block/unblock, reset OAuth, extend subscription, send message, impersonate ("login as user"), create beta account (full access, no payment) |
| Promo codes | CRUD promo codes (NOT on MVP — reserved for future use) |
| Broadcasts | Send to all active users OR specific user. FastAPI saves broadcast to Supabase queue → bot scheduler picks up and sends via Telegram in batches. History + preview + delivery status. |
| Logs | API errors, health status, Sentry link, active alerts |
| Finances | All payments, revenue/month chart, MRR |

---

## Monitoring and security

| Aspect | Decision |
|--------|----------|
| Health check | Every 5 min, admin alert (Telegram + email) |
| Sentry | From day 1 (free tier) |
| Google tokens | Fernet encrypted in Supabase |
| CORS | Dashboard domain only |
| Rate limiting | Login, webhooks, write endpoints |
| HTTPS | Automatic (Railway + Vercel) |
| Bot groups | Ignores all |
| User rate limit | 100/day + borrow max 20 from tomorrow |
| Dashboard → Google | Always through FastAPI, never direct |
| Webhook URL | BASE_URL env var, endpoints: /webhooks/telegram, /webhooks/przelewy24, /health |
| Domain migration | Change BASE_URL + DNS, zero code changes |

---

## DevOps

| Aspect | Decision |
|--------|----------|
| Railway | 2 processes: bot (webhook) + FastAPI (separate) |
| Git branches | main (production) + develop (dev/staging) |
| CI/CD | Auto-deploy develop → staging. Manual deploy main → production. |
| Environments | ENV=dev/staging/prod (env var) |
| Dev bot | Separate @OZEAgentDevBot + separate Supabase project |
| Tests | pytest for backend |
| README | Full with setup instructions + .env.example |
| Vercel Analytics | Enabled on dashboard |

---

## Key versions

| Technology | Version |
|------------|---------|
| Python | 3.13 |
| Node.js | 20 |
| Next.js | 14 |
| python-telegram-bot | 21.x |
| Others | Latest stable, compatible |

---

## Environment variables

```
# Core
TELEGRAM_BOT_TOKEN=
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
ENV=dev

# Google OAuth
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=

# Supabase
SUPABASE_URL=
SUPABASE_KEY=
SUPABASE_SERVICE_KEY=
SUPABASE_JWT_SECRET=

# Security
ENCRYPTION_KEY=

# Payments
PRZELEWY24_MERCHANT_ID=
PRZELEWY24_API_KEY=
PRZELEWY24_CRC=

# Pricing
ACTIVATION_FEE_PLN=199
ACTIVATION_FEE_PROMO_PLN=20
MONTHLY_SUBSCRIPTION_PLN=49
YEARLY_SUBSCRIPTION_PLN=350

# Monitoring
SENTRY_DSN=
ADMIN_TELEGRAM_ID=
ADMIN_EMAIL=

# URLs
BASE_URL=
DASHBOARD_URL=
ADMIN_URL=

# Email
GMAIL_SMTP_USER=
GMAIL_SMTP_PASSWORD=

# Misc
TIMEZONE=Europe/Warsaw
```

---

## File structure

```
oze-agent/
├── bot/
│   ├── main.py
│   ├── config.py
│   ├── handlers/
│   │   ├── start.py
│   │   ├── voice.py
│   │   ├── text.py
│   │   ├── photo.py
│   │   ├── buttons.py
│   │   └── fallback.py
│   ├── scheduler/
│   │   ├── morning_brief.py
│   │   ├── reminders.py
│   │   ├── followup_check.py
│   │   ├── flow_reminder.py
│   │   ├── health_check.py
│   │   ├── backup_export.py
│   │   └── maintenance.py
│   └── utils/
│       └── telegram_helpers.py
├── api/
│   ├── main.py
│   ├── auth.py
│   ├── routes/
│   │   ├── users.py
│   │   ├── google_oauth.py
│   │   ├── payments.py
│   │   ├── sheets.py
│   │   ├── calendar.py
│   │   ├── promo.py
│   │   ├── admin.py
│   │   ├── broadcast.py
│   │   └── csv_import.py
│   └── middleware.py
├── shared/
│   ├── database.py             # Supabase connection and queries
│   ├── encryption.py
│   ├── google_auth.py
│   ├── google_sheets.py
│   ├── google_calendar.py
│   ├── google_drive.py
│   ├── claude_ai.py
│   ├── whisper_stt.py
│   ├── followup.py
│   ├── search.py
│   └── formatting.py
├── dashboard/
│   ├── app/
│   │   ├── page.tsx
│   │   ├── klienci/page.tsx
│   │   ├── statystyki/page.tsx
│   │   ├── instrukcja/page.tsx
│   │   ├── faq/page.tsx
│   │   ├── platnosci/page.tsx
│   │   ├── ustawienia/page.tsx
│   │   ├── kontakt/page.tsx
│   │   ├── import/page.tsx
│   │   ├── rejestracja/page.tsx
│   │   └── login/page.tsx
│   └── ...
├── admin/
│   ├── app/
│   │   ├── page.tsx
│   │   ├── users/page.tsx
│   │   ├── promo/page.tsx
│   │   ├── broadcasts/page.tsx
│   │   ├── logs/page.tsx
│   │   └── finances/page.tsx
│   └── ...
├── docs/
│   ├── poznaj_swojego_agenta.md
│   ├── design_system.md
│   ├── regulamin.md
│   ├── polityka_prywatnosci.md
│   └── acceptance_criteria.md
├── tests/
│   ├── test_google_sheets.py
│   ├── test_google_calendar.py
│   ├── test_claude_ai.py
│   ├── test_whisper.py
│   ├── test_payments.py
│   ├── test_auth.py
│   └── test_csv_import.py
├── requirements.txt
├── Procfile
├── railway.toml
├── .env.example
└── README.md
```

---

## Supabase schema

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_id BIGINT UNIQUE,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,
    phone TEXT,
    address TEXT,
    age INTEGER,
    products JSONB DEFAULT '[]',
    referral_source TEXT,
    google_access_token TEXT,
    google_refresh_token TEXT,
    google_token_expiry TIMESTAMPTZ,
    google_sheets_id TEXT,
    google_sheets_name TEXT,
    google_calendar_id TEXT,
    google_calendar_name TEXT,
    google_drive_folder_id TEXT,
    morning_brief_hour INTEGER DEFAULT 7,
    reminder_minutes_before INTEGER DEFAULT 60,
    default_meeting_duration INTEGER DEFAULT 60,
    working_days JSONB DEFAULT '[1,2,3,4,5]',
    pipeline_statuses JSONB DEFAULT '["Nowy lead","Spotkanie umówione","Spotkanie odbyte","Oferta wysłana","Negocjacje","Podpisane","Odrzucone"]',
    sheet_columns JSONB,
    subscription_status TEXT DEFAULT 'pending_payment',
    subscription_plan TEXT,
    subscription_expires_at TIMESTAMPTZ,
    activation_paid BOOLEAN DEFAULT FALSE,
    promo_code_used TEXT,
    consent_terms BOOLEAN DEFAULT FALSE,
    consent_marketing BOOLEAN DEFAULT FALSE,
    consent_phone_contact BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    onboarding_completed BOOLEAN DEFAULT FALSE,
    telegram_link_code TEXT,
    telegram_link_code_expires TIMESTAMPTZ,
    is_admin BOOLEAN DEFAULT FALSE,
    is_suspended BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE
);

CREATE TABLE promo_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL,
    value REAL,
    max_uses INTEGER DEFAULT 1,
    times_used INTEGER DEFAULT 0,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE conversation_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_id BIGINT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    message_type TEXT DEFAULT 'text',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE pending_followups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_id BIGINT NOT NULL,
    event_id TEXT NOT NULL,
    event_title TEXT NOT NULL,
    event_end_time TIMESTAMPTZ NOT NULL,
    client_name TEXT,
    client_location TEXT,
    status TEXT DEFAULT 'pending',
    asked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE pending_flows (
    telegram_id BIGINT PRIMARY KEY,
    flow_type TEXT NOT NULL,
    flow_data JSONB NOT NULL,
    reminder_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE interaction_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_id BIGINT NOT NULL,
    interaction_type TEXT,
    model_used TEXT,
    tokens_in INTEGER,
    tokens_out INTEGER,
    cost_usd REAL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE user_habits (
    telegram_id BIGINT PRIMARY KEY,
    default_meeting_duration INTEGER DEFAULT 60,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE payment_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    amount_pln REAL NOT NULL,
    type TEXT NOT NULL,
    status TEXT NOT NULL,
    przelewy24_order_id TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE webhook_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source TEXT NOT NULL,
    payload JSONB NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    duplicate BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE admin_broadcasts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message TEXT NOT NULL,
    target TEXT NOT NULL,            -- 'all' or specific telegram_id
    status TEXT DEFAULT 'pending',   -- pending, processing, completed, failed
    total_recipients INTEGER DEFAULT 0,
    sent_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    sent_by UUID REFERENCES users(id)
);

CREATE TABLE daily_interaction_counts (
    telegram_id BIGINT NOT NULL,
    date DATE NOT NULL,
    count INTEGER DEFAULT 0,
    borrowed_from_tomorrow INTEGER DEFAULT 0,
    PRIMARY KEY (telegram_id, date)
);
```

---

## Scheduler jobs

| Job | Frequency | Description |
|-----|-----------|-------------|
| Morning brief | Daily at each user's hour | Working days only |
| Event reminders | Every 1 min | With client data from Sheets |
| Follow-up check | Every 5 min | After last meeting of day |
| Flow reminder | Every 5 min | Incomplete flows > 30 min, once |
| Token refresh | Every 30 min | Auto-refresh Google tokens |
| Sheet column sync | Every 6 hours | Re-read headers for all users |
| Subscription check | Daily 00:00 | Deactivate expired |
| Subscription reminder | Daily 09:00 | 3 days before + day of expiry |
| Conversation cleanup | Daily 03:00 | Delete > 24h |
| Habit recalculation | Daily 02:00 | Meeting duration defaults |
| Health check | Every 5 min | All APIs, admin alert (Telegram + email) |
| Backup export | Weekly (Sunday 04:00) | Critical tables → admin Google Drive |
| Broadcast queue | Every 1 min | Pick up pending broadcasts from Supabase, send via Telegram Bot API in batches, log results |

---

## MVP acceptance criteria

Formal checklist with Pass/Fail for each critical flow. To be detailed in separate `acceptance_criteria.md`. Key areas:

1. **Registration + Payment:** User can register, pay, authorize Google, link Telegram — end to end
2. **Voice → CRM:** Record voice → see transcription (if low confidence) → confirm → data in Sheets
3. **Text → CRM:** Type client data → confirm → data in Sheets
4. **Calendar:** Add/view/reschedule/cancel meeting via bot
5. **Client search:** Find by name + city, fuzzy, typo-tolerant
6. **Client edit:** Change data with old/new confirmation
7. **Photo:** Send photo → assign to client → visible in Drive + Sheets link
8. **Follow-up:** Post-last-meeting prompt → user responds → statuses updated
9. **Morning brief:** Arrives at configured hour on working days
10. **Reminder:** Arrives before meeting with client data
11. **Dashboard:** Login, view clients table, view calendar, view stats, change settings
12. **CSV import:** Upload file, map columns, import to Sheets
13. **Payments:** Subscription renewal, expiry blocking, promo codes
14. **Admin panel:** View users, view finances, send broadcast, suspend/unsuspend
15. **Errors:** Google API down → clear message. Timeout → clear message. Token expired → re-auth link.

---

## Documents to create

| File | Status | Description |
|------|--------|-------------|
| OZE_Agent_Brief.md | ✅ This document | Technical brief |
| poznaj_swojego_agenta.md | ✅ Created | Instruction page content |
| design_system.md | ❌ TODO | Visual guidelines (dark theme, shadcn/ui, typography, colors) |
| implementation_plan.md | ❌ TODO | Step-by-step plan for Claude Code |
| acceptance_criteria.md | ❌ TODO | Pass/Fail criteria for each flow |
| regulamin.md | ❌ TODO | Terms of service template |
| polityka_prywatnosci.md | ❌ TODO | Privacy policy template |
| README.md | ❌ TODO | Setup instructions |
| .env.example | ❌ TODO | All environment variables |

---

## Future phases (NOT MVP)

- **Phase 5:** Facebook Lead Ads integration (auto-import leads)
- **Phase 6:** Kanban board on dashboard
- **Phase 7:** Multiple pricing plans
- **Phase 8:** Team/manager view
- **Phase 9:** WhatsApp support
- **Phase 10:** AI-generated quotes/proposals
- **Phase 11:** Route optimization (maps)
- **Phase 12:** Invoice generation
- **Phase 13:** Contract value tracking (pipeline value)
- **Phase 14:** Landing page (separate workflow)
- **Phase 15:** Promo code system

---

## Design system

- **Theme:** Dark mode only
- **Accent color:** Neon green (#00FF88 or similar — energetic, OZE-appropriate)
- **UI framework:** shadcn/ui + Tailwind CSS
- **Font:** Claude Code chooses best fit (readable, modern)
- **Icons:** Lucide (shadcn/ui default)
- **Style:** Minimalist, professional, mobile-first
- **Border radius:** shadcn/ui defaults (slightly rounded)
- **Calendar view:** Own component (list of meetings per day/week), NOT iframe. Styled consistently with dark theme.
- **Landing page:** Placeholder on MVP (separate workflow later)

---

## Key design principles

1. **Speed** — 30-second voice note → data saved in under 10 seconds.
2. **Minimize interactions** — extract max from one message, list all missing fields at once.
3. **Confirm everything** — never write data without user's OK.
4. **Shared services** — ALL business logic in shared modules, imported by bot + API + scheduler. Zero duplication.
5. **Source of truth clarity** — CRM in Google, system data in Supabase, never mix.
6. **No temporary CRM storage** — if Google is down, inform user and wait. Don't cache CRM data in Supabase.
7. **Agent adapts** — reads sheet columns, statuses, working days, habits.
8. **Data belongs to user** — their Google account, their data. Cancel → keep everything.
9. **Agent doesn't suggest** — waits for instructions.
10. **Mobile-first** — bot on phone, dashboard on phone.
11. **Polish-first** — native Polish, not translated.
12. **Idempotent webhooks** — all webhooks safe to receive multiple times.
13. **Clear error messages** — user knows what failed and what to do about it.
