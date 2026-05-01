# Web App Onboarding And Phase 1 Design

_Date: 29.04.2026_
_Track: Web app Phase 0D, 0E, 0F, Phase 1_
_Branch: `feat/web-phase-0c`_

## Decision

Status 29.04.2026: this design has been implemented on `feat/web-phase-0c` /
PR #5. Phase 0C/0D/0E/0F/Phase 1 are code-complete on the branch, but rollout
is still gated by Phase 1B sandbox/deployment smokes.

Phase 0C created the Stripe sandbox foundation, protected app shell, read-only
CRM adapter boundary, initial CRM pages, secondary app routes, and a FastAPI
read-only CRM endpoint. The follow-up implementation pass turned the web app
into a usable onboarding and dashboard product.

The recommended Phase 1 definition is accepted:

- real onboarding status endpoints,
- Google OAuth initiated from the web app but completed by FastAPI,
- resource creation or connection for Google Sheets, Calendar, and Drive,
- Telegram pairing by short-lived code,
- dashboard data read from real Google resources through FastAPI,
- billing/account/settings made more functional,
- no web forms that mutate CRM data.

The Telegram bot is not the active focus of this pass. It remains the only CRM
mutation surface. The web app can change system/account/onboarding data, but CRM
source-of-truth records stay in Google.

## Current Baseline

Phase 0D and 0E are implemented in the current branch:

- logged-in app shell exists,
- `/dashboard`, `/klienci`, `/kalendarz`, `/platnosci`, `/ustawienia`,
  `/import`, `/instrukcja`, `/faq` exist,
- CRM pages call a read-only adapter and expose source states,
- FastAPI exposes `/api/dashboard/crm` with source metadata,
- Stripe Checkout and webhook forwarding exist,
- FastAPI exposes `/api/onboarding/*` authenticated by Supabase JWT,
- Google OAuth state is signed and redirects back to web onboarding,
- resource creation is exposed as a controlled onboarding operation,
- partial Google resource creation persists successful IDs before later failure,
- Telegram pairing has a web/API flow and shows `/start <code>`,
- completed accounts see live or unavailable CRM state rather than silent demo,
- settings/account pages mutate only system account fields.

The main missing part is Phase 1B rollout/readiness: real sandbox env, deployed
webhook, Supabase migrations, Stripe smoke/replay, Google OAuth/resource smoke,
Telegram pairing smoke, and browser smoke.

## Product Rules

The web app must clearly show that CRM edits happen in Google:

- clients are edited in Google Sheets,
- meetings and actions are edited in Google Calendar,
- photos live in Google Drive,
- the web app renders CRM data read-only and provides direct Google links.

The web app must not render forms or server actions that create, update, delete,
or reorder CRM clients/events/notes/statuses. It may render filters, search,
view preferences, onboarding controls, account settings, and billing actions.

User-facing UI text stays Polish and concise. Copy can be rough because product
copy is expected to change later; functionality and boundaries matter more.

## Phase 0D Completion

Phase 0D completes the logged-in app shell by adding route-level gates and a
single onboarding state model.

The app should compute an onboarding step from the authenticated account:

1. no active subscription -> `/onboarding/platnosc`,
2. no Google tokens -> `/onboarding/google`,
3. missing Sheets/Calendar/Drive resources -> `/onboarding/zasoby`,
4. no Telegram pairing -> `/onboarding/telegram`,
5. complete -> `/dashboard`.

Dashboard routes should remain accessible enough to show account state, but the
primary CTA should send users to the next missing onboarding step. Paid but
incomplete users should not see mock CRM as if it were live CRM data.

## Phase 0E Completion

Phase 0E hardens the read-only CRM experience:

- CRM adapter should distinguish live, mock, and unavailable data states.
- Paid/onboarded users should see live Google-backed data or a clear connection
  error, not silent demo data.
- Unpaid or incomplete users may see sample/demo data only when labelled as demo.
- Dashboard, clients, and calendar pages should expose source state and direct
  Google links consistently.
- FastAPI mapping should return stable DTOs even when Sheets rows or Calendar
  events are sparse.

This phase does not add CRM mutation features to the web app.

## Phase 0F Onboarding Completion

Phase 0F adds the remaining onboarding screens and backend boundaries.

### Google OAuth

Next.js calls a FastAPI endpoint with the Supabase access token. FastAPI resolves
the user from the verified JWT and returns a Google OAuth URL. The OAuth `state`
must not trust a public path `user_id`; it should encode a short-lived signed
state or at minimum bind the state to the authenticated Supabase user.

FastAPI handles the Google callback, stores encrypted tokens through the existing
Google auth helper, and redirects to a web success/failure route such as
`/onboarding/google/sukces` or `/onboarding/google?error=...`.

### Google Resources

After OAuth, the user chooses or accepts default resource names:

- Sheets: `Agent-OZE CRM - <name/email>`,
- Calendar: `Agent-OZE - <name/email>`,
- Drive: `Agent-OZE Klienci - <name/email>`.

The backend creates missing resources using existing wrappers:

- `shared.google_sheets.create_spreadsheet`,
- `shared.google_calendar.create_calendar`,
- `shared.google_drive.create_root_folder`.

Resource IDs are stored in `public.users`. This is system setup data, not CRM
content. The screen shows progress and links to created resources.

### Telegram Pairing

The web app creates a short-lived pairing code stored on the user row:

- `telegram_link_code`,
- `telegram_link_code_expires`.

The screen shows the code, expiry, regenerate action, and polling status. The
bot-side command that consumes this code can be implemented later if it is not
already available, but the web/API contract should be ready. Until the bot flow
lands, the UI must label pairing as waiting for Telegram confirmation.

When `telegram_id` is present and Google resources exist, FastAPI can mark
`onboarding_completed = true`.

## Phase 1 Web App

Phase 1 turns the app from a route skeleton into a reliable operational panel.

### Account State API

FastAPI should expose authenticated endpoints for:

- current account/profile,
- onboarding status and next step,
- Google OAuth URL generation,
- Google resource creation/status,
- Telegram pairing code generation/status,
- optional account profile updates that do not touch CRM.

Next.js should call these endpoints through server-side helpers using the
Supabase access token. Browser-accessible Supabase remains Auth/session only.

### Live CRM Data Path

For completed accounts, CRM pages read only from Google-backed FastAPI endpoints.
Mock CRM data remains isolated for demo/empty-state use and must not be silently
shown as live data. The UI should display source state:

- live Google data,
- demo data,
- Google not connected,
- Google fetch failed.

### Billing And Access

Stripe remains the payment provider. Phase 1 should add better account-facing
billing state and a safe route toward Stripe Billing Portal only if the needed
Stripe configuration is available. Otherwise the page should show subscription
state from FastAPI/Supabase and the existing Checkout retry path.

### Settings

Settings may update account/system fields such as display name, phone, onboarding
resource preferences, and notification preferences if those fields already exist
or are added through a scoped migration. Settings must not update CRM statuses,
client rows, notes, meetings, or Calendar event content.

## Backend Boundaries

FastAPI owns trusted service-role Supabase writes. Next.js must never receive
`SUPABASE_SERVICE_KEY`.

Authenticated web endpoints should use Supabase JWT validation through
`api.auth.get_current_auth_user`, then resolve `public.users.auth_user_id`.

Internal-only endpoints, such as Stripe webhook forwarding, keep the existing
HMAC boundary.

Google token storage stays encrypted in Supabase through `shared.google_auth`.
Logs must not print raw tokens, OAuth codes, pairing codes after consumption, or
Stripe secrets.

## Data Model

Existing columns support most of the flow:

- `auth_user_id`,
- `subscription_status`,
- `subscription_plan`,
- `activation_paid`,
- `google_access_token`,
- `google_refresh_token`,
- `google_token_expiry`,
- `google_sheets_id`,
- `google_sheets_name`,
- `google_calendar_id`,
- `google_calendar_name`,
- `google_drive_folder_id`,
- `telegram_id`,
- `telegram_link_code`,
- `telegram_link_code_expires`,
- `onboarding_completed`,
- `onboarding_survey`.

If needed, a migration may add non-CRM setup fields such as
`onboarding_google_connected_at`, `onboarding_resources_created_at`, or
`telegram_link_code_attempts`. The first implementation should avoid unnecessary
schema growth unless tests reveal the current columns are insufficient.

## Error Handling

OAuth failures return the user to the Google onboarding step with a short Polish
message and a retry button. Resource creation should be partial-result safe:
creating Sheets should not be repeated if it already succeeded but Calendar
failed. Retrying should create only missing resources.

Dashboard data fetch failures should not fall back to unlabelled mock data for
completed users. They should show a live-data error and preserve the direct
Google links that are available.

Telegram pairing code expiry should be visible in the UI. Regeneration should
invalidate or overwrite the prior code for that user.

## Testing

Automated coverage should include:

- account/onboarding status endpoint,
- authenticated Google OAuth URL endpoint rejects unauthenticated access,
- OAuth URL generation does not accept arbitrary path user IDs,
- resource creation is idempotent for already-created Sheets/Calendar/Drive IDs,
- Telegram pairing code generation, expiry, and status polling,
- CRM adapter does not silently use demo data for completed accounts when the
  backend returns an error,
- invariants for no CRM mutation forms in web routes,
- Next.js build and lint,
- focused FastAPI pytest plus full suite when feasible.

Manual verification should include:

1. signup/login,
2. Stripe sandbox payment,
3. Google OAuth redirect round trip in a test environment,
4. resource creation retry after a forced partial failure,
5. Telegram pairing screen generation/regeneration,
6. dashboard/client/calendar pages showing Google source state and direct links.

## Out Of Scope

- Live Stripe mode.
- Przelewy24.
- CRM mutations in the web app.
- Web chat with the agent.
- CSV import that writes clients.
- Bot-side pairing-code consumption if it requires a behavior-layer detour; the
  web/API pairing contract can land first.
- Final marketing copy polish.
- Product-vision-only bot features such as reschedule/cancel/free-slots/delete.

## Open Implementation Choices

1. OAuth state format: signed JSON state is preferred; a server-stored nonce is
   acceptable if it stays short-lived and bound to the authenticated user.
2. Telegram code format: six digits is easiest for users; alphanumeric is safer
   but less convenient. Six digits plus short expiry and per-user overwrite is
   enough for MVP.
3. Billing Portal: add only if Stripe env/config can support it cleanly; do not
   block Phase 1 on it.
