# Web App Functional Roadmap Design

_Date: 29.04.2026_
_Track: Phase 0C onward_
_Worktree: `/Users/mansoniasty/workflows/Agent-OZE-phase0c`_

## Decision

The active implementation track is now the web app. The Telegram agent is no
longer the blocker for this phase after the recent memory fix made the agent
substantially more usable. Remaining agent polish stays as a later lane and
must not derail the web app buildout.

The web app follows the existing active docs:

- `docs/WEB_APP_BRIEF_FOR_CLAUDE_DESIGN.md`
- `web/CLAUDE.md`
- `docs/STRIPE_PHASE_0C_ROLLOUT.md`
- `docs/SOURCE_OF_TRUTH.md`, with this spec recording the updated user decision
  that web work is allowed to proceed now.

Przelewy24 is replaced by Stripe. Any remaining Przelewy24 copy in web docs or
UI should be treated as stale and changed to Stripe while touching the related
screen.

## Product Scope

The first goal is a functional web app, not final marketing copy. Copy should be
plain Polish and easy to replace later. Engineering should prioritize working
flows, route structure, data boundaries, and payment/onboarding mechanics.

The web app is not a chat surface and must not mutate CRM data. Telegram remains
the place for adding clients, notes, meetings, and status changes. The web app
can mutate system/account data: auth profile, billing state, onboarding state,
Google connection metadata, Telegram pairing state, and user settings.

The first usable version should let a real user:

1. Create an account.
2. Pay through Stripe sandbox.
3. Reach a gated dashboard that reflects account/subscription/onboarding state.
4. Move through the Google and Telegram onboarding screens, with safe placeholder
   or mock-backed behavior where live integrations are not ready.
5. Use a read-only dashboard shell with CRM-oriented pages built around mock data
   first, then replace the adapters with Google/FastAPI-backed data.

## Architecture

The web app remains a Next.js app under `web/`, deployed separately from the
Python backend. Supabase Auth owns browser sessions and RLS-facing user identity.
FastAPI owns trusted service-role operations and durable billing writes.

Stripe is integrated with hosted Checkout. The browser never handles Stripe
secrets. Next.js creates Checkout Sessions server-side, receives Stripe webhooks,
verifies them, then forwards a signed internal payload to FastAPI. FastAPI
validates the HMAC, writes billing state to Supabase with the service key, and
deduplicates by Stripe event ID.

Read-only CRM pages should use a local adapter boundary. In early phases the
adapter returns realistic Polish mock data. Later the same boundary calls FastAPI
dashboard endpoints that read Google Sheets and Calendar. This keeps UI work
moving without storing CRM source-of-truth data in Supabase.

## Phase Roadmap

### Phase 0C — Stripe Billing Foundation

Finish the existing Phase 0C worktree:

- Supabase profile lookup and protected routes.
- `/rejestracja` account creation flow.
- `/onboarding/platnosc` plan selection and Stripe Checkout launch.
- `/api/webhooks/stripe` webhook verification and forwarding.
- FastAPI `/internal/billing/stripe-event` HMAC verification, event processing,
  idempotent `payment_history`, `webhook_log`, and `billing_outbox` writes.
- Supabase migration for Stripe fields/tables.
- Dashboard subscription gating.

This phase stays sandbox-only until `docs/STRIPE_PHASE_0C_ROLLOUT.md` passes.
Stop immediately if any Stripe response says `livemode: true`.

### Phase 0D — Functional App Shell

Build the logged-in product shell:

- Persistent sidebar and topbar after login.
- Routes: `/dashboard`, `/klienci`, `/kalendarz`, `/platnosci`, `/ustawienia`,
  `/instrukcja`, `/faq`, `/import`.
- Protected route behavior using Supabase session checks.
- Subscription/onboarding gates that send unpaid users to payment and incomplete
  users to the correct onboarding step.
- Floating Google action buttons on logged-in screens, disabled or explanatory
  until Google resources exist.

### Phase 0E — Read-Only CRM Experience

Build functional CRM pages with mock-backed adapters:

- Dashboard KPIs, funnel, day plan, urgent clients, and data freshness badge.
- Clients table with search, filters, sortable columns, and read-only side panel.
- Calendar week/day/list view with event details and client links.
- Payments page that reads local account/billing state.
- Settings page for account and onboarding state, with CRM-editing features
  disabled if they are POST-MVP.

The UI must make it clear that CRM edits happen through Telegram or Google
direct links, not through web forms.

### Phase 0F — Onboarding Completion

Add the remaining onboarding screens as functional flows:

- Google OAuth status and connection entry point.
- Resource naming step for Sheets, Calendar, and Drive.
- Resource creation progress screen. It may use mocked progress until backend
  creation is wired, but the route/state model should match the real flow.
- Telegram pairing code screen with timer, regenerate action, and polling/mock
  status boundary.
- Final redirect to dashboard once required setup is complete.

### Later Agent Polish

Keep a separate agent polish backlog. Known direction: the memory fix improved
the agent heavily, but there is still behavior work left. That work should be
planned separately after the web app has its functional spine.

## Data Boundaries

System data may live in Supabase:

- user profile
- auth mapping
- subscription fields
- onboarding status
- Google resource IDs and encrypted tokens
- Telegram pairing state
- billing logs/outbox

CRM source-of-truth data stays in Google:

- clients in Sheets
- meetings/actions in Calendar
- photos in Drive

Mock CRM data in the frontend is acceptable during UI buildout, but it must be
clearly isolated in mock/adapters so it can be replaced by FastAPI reads.

## Error Handling

Stripe failures return the user to `/onboarding/platnosc` with a short message.
Webhook forwarding failures must leave enough log state for replay and must not
mark events as processed unless FastAPI accepts them.

FastAPI billing ingestion must be duplicate-safe. Replayed events should not
duplicate `payment_history` rows or `billing_outbox` messages.

Dashboard routes must fail closed for auth. If profile data cannot load, show a
short account-state panel instead of exposing protected app screens.

## Testing

Phase 0C needs automated tests for:

- Stripe webhook verification and forwarding in Next.js.
- Stripe lookup-key and direct price ID resolution.
- FastAPI billing HMAC verification.
- Billing event idempotency.
- Account gating for registration, payment, and dashboard routes where practical.

Frontend shell and CRM pages need tests or build-time verification focused on:

- route rendering
- protected redirects
- no CRM mutation forms
- payment CTA visibility
- mock adapter data shape

Manual verification must include the sandbox Stripe smoke from
`docs/STRIPE_PHASE_0C_ROLLOUT.md` before treating billing as complete.

## Out Of Scope

These are not part of this implementation pass:

- Live Stripe mode.
- Production price creation.
- Przelewy24 integration.
- CRM mutations from the web app.
- Company/workspace extension.
- CSV import implementation beyond a placeholder or non-mutating screen.
- Final marketing copy polish.
- Full agent behavior rewrite.

## Open Decisions

1. Exact final copy and pricing presentation can change later.
2. Whether Google resource creation is wired live in Phase 0F or mocked behind
   the route boundary depends on backend readiness after Phase 0C.
3. Agent polish items need their own spec/plan after the web app functional
   spine is working.
