# Audit Risk Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the eight confirmed audit risks without replacing the existing manager profile or breaking legacy pending records.

**Architecture:** Introduce stable client references that resolve current Sheets rows at execution time, database-backed operation claims for Telegram and Gmail, and monotonic event handling for Stripe. Keep legacy row-only payloads readable, but make every newly created operation carry identity data and fail closed on mismatch. The manager/owner UI remains intact; only the seller Decisions surface becomes read-only.

**Tech Stack:** Python 3.11+/FastAPI/python-telegram-bot/Supabase/Postgres/Google APIs, Next.js 16/React 19, pytest and Node test runner.

---

### Task 1: Stable client references

**Files:**
- Create: `oze-agent/shared/clients/identity.py`
- Modify: `oze-agent/shared/clients/__init__.py`
- Test: `oze-agent/tests/clients/test_identity.py`

- [ ] Write failing tests proving a reference resolves after row movement and rejects missing/ambiguous identities.
- [ ] Run `pytest tests/clients/test_identity.py -q` and verify the new tests fail because the API is missing.
- [ ] Implement `build_client_ref(row)` and `resolve_client_ref(user_id, ref)` using normalized name, city, phone and email plus a row hint.
- [ ] Run `pytest tests/clients/test_identity.py -q` and verify pass.

### Task 2: Safe pending and note writes

**Files:**
- Modify: `oze-agent/shared/pending/payloads.py`
- Modify: `oze-agent/bot/handlers/text.py`
- Modify: `oze-agent/bot/handlers/buttons.py`
- Modify: `oze-agent/shared/mutations/add_note.py`
- Test: `oze-agent/tests/handlers/test_add_note_confirm.py`
- Test: `oze-agent/tests/handlers/test_change_status_confirm.py`
- Test: `oze-agent/tests/handlers/test_add_meeting_confirm.py`

- [ ] Add failing tests for moved rows and for a note appended after card creation.
- [ ] Run the targeted handler tests and verify the failures are identity/snapshot related.
- [ ] Store `client_ref` in new pending payloads, resolve it immediately before mutation, and re-read current notes before append.
- [ ] Keep row-only legacy payloads compatible while failing closed when a new reference mismatches.
- [ ] Re-run targeted handler and mutation tests.

### Task 3: Telegram callback serialization

**Files:**
- Modify: `oze-agent/shared/database.py`
- Modify: `oze-agent/bot/handlers/buttons.py`
- Modify: `oze-agent/bot/handlers/text.py`
- Create: `oze-agent/supabase_migrations/20260724_pending_flow_claims.sql`
- Test: `oze-agent/tests/handlers/test_button_security.py`
- Test: `oze-agent/tests/test_database.py`

- [ ] Add failing tests that two save callbacks cannot both acquire a flow.
- [ ] Add an atomic Supabase RPC claim keyed by telegram id and flow version.
- [ ] Claim before `handle_confirm`; release only for retryable pre-effect failures and consume after terminal outcomes.
- [ ] Re-run button/database tests.

### Task 4: Gmail outbox recovery and stable offer recipient

**Files:**
- Modify: `oze-agent/shared/offers/repository.py`
- Modify: `oze-agent/shared/offers/queue_worker.py`
- Modify: `oze-agent/shared/offers/pipeline.py`
- Modify: `oze-agent/bot/handlers/text.py`
- Create: `oze-agent/supabase_migrations/20260724_offer_send_recovery.sql`
- Test: `oze-agent/tests/offers/test_queue_worker.py`
- Test: `oze-agent/tests/offers/test_pipeline.py`
- Test: `oze-agent/tests/handlers/test_offer_send_background.py`

- [ ] Add failing tests for a moved client, a stale `sending` attempt and a DB failure after Gmail success.
- [ ] Persist client reference and immutable confirmed recipients at enqueue time.
- [ ] Resolve and validate identity before rendering/sending; never recompute recipients from a different row.
- [ ] Recover stale `sending` as `reconcile_required`, never blind-retry an ambiguous Gmail outcome.
- [ ] Store a deterministic RFC Message-ID derived from idempotency key and add repository reconciliation transitions.
- [ ] Re-run offer tests.

### Task 5: Stripe webhook idempotency and ordering

**Files:**
- Modify: `oze-agent/api/routes/billing.py`
- Create: `oze-agent/supabase_migrations/20260724_stripe_event_ordering.sql`
- Test: `oze-agent/tests/test_billing_stripe_event.py`

- [ ] Add failing tests for retry of an unprocessed log and for an older event arriving after a newer event.
- [ ] Upsert/claim one webhook row per Stripe event and retry that row rather than insert again.
- [ ] Persist Stripe event `created` on users and ignore state regressions older than the last applied event.
- [ ] Mark unsupported events processed so retries remain idempotent.
- [ ] Re-run billing tests.

### Task 6: API subscription enforcement

**Files:**
- Modify: `oze-agent/api/auth.py`
- Modify: `oze-agent/api/routes/dashboard.py`
- Modify: `oze-agent/api/routes/decisions.py`
- Modify: `oze-agent/api/routes/insights.py`
- Modify: `oze-agent/api/routes/offers.py`
- Test: `oze-agent/tests/test_api_auth.py`
- Test: `oze-agent/tests/test_dashboard_api.py`
- Test: `oze-agent/tests/test_offers_api_security.py`

- [ ] Add failing direct-API tests for canceled/unpaid accounts and passing tests for active/trial/beta access.
- [ ] Implement `require_active_account` as a shared FastAPI dependency.
- [ ] Attach it to paid product routes while leaving onboarding, billing webhooks, account and owner admin access intact.
- [ ] Re-run API security tests.

### Task 7: Warsaw calendar boundaries

**Files:**
- Modify: `oze-agent/shared/google_calendar.py`
- Modify: `oze-agent/shared/google_sheets.py`
- Test: `oze-agent/tests/test_google_calendar.py`
- Test: `oze-agent/tests/test_google_sheets.py`

- [ ] Add failing DST-aware tests for Warsaw midnight bounds and host-timezone-independent contact dates.
- [ ] Query `[Warsaw midnight, next Warsaw midnight)` and use a shared Warsaw date helper for Sheets writes.
- [ ] Re-run Google wrapper and day-plan tests.

### Task 8: Read-only Decisions panel

**Files:**
- Modify: `web/components/dashboard/decyzje-preview.tsx`
- Delete: `web/app/(app)/dashboard/decyzje-preview/actions.ts`
- Modify: `oze-agent/api/routes/decisions.py`
- Modify: `web/tests/decyzje-preview-toast.test.mjs`
- Create: `web/tests/decyzje-read-only.test.mjs`
- Modify: `oze-agent/tests/test_dashboard_api.py`

- [ ] Add failing source/API tests asserting no CRM mutation actions or POST decision routes remain.
- [ ] Remove action buttons/modals/server actions and replace them with read-only context plus Telegram/Google deep links.
- [ ] Keep pending decision reads and existing manager/owner pages unchanged.
- [ ] Re-run Node tests and API tests.

### Task 9: Integrated verification

**Files:**
- Modify only when a regression test proves a compatibility problem.

- [ ] Run targeted tests after every task.
- [ ] Run `pytest -q` from `oze-agent/`.
- [ ] Run `node --test tests/*.test.mjs` from `web/`.
- [ ] Run `npm run lint` and `npm run build` when dependencies are available.
- [ ] Run `python3 scripts/security_scan.py` from repository root.
- [ ] Review `git diff --check`, `git status --short` and the complete diff; do not commit.
