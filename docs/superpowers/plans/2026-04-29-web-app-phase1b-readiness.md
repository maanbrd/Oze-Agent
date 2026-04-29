# Web App Phase 1B Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Phase 1B readiness tooling and runbook docs without adding new product functionality.

**Architecture:** Keep Next.js as the web/session/Stripe Checkout boundary and FastAPI as the service-role Google/Supabase boundary. Local checks validate configuration and code shape; staging smoke validates external webhook, OAuth, resource, and Telegram flows.

**Tech Stack:** Node.js scripts, npm scripts, Python env verifier, pytest, Markdown runbooks.

---

### Task 1: Web Env Checker

**Files:**
- Modify: `web/scripts/check-web-invariants.mjs`
- Modify: `web/package.json`
- Create: `web/scripts/check-phase1b-env.mjs`

- [x] Write a failing invariant requiring `check:phase1b-env` and `scripts/check-phase1b-env.mjs`.
- [x] Run `cd web && npm run test:invariants`; expected failure for missing script.
- [x] Add `check:phase1b-env` and implement the checker.
- [x] Verify local scope accepts test-mode env and rejects `sk_live_`.

### Task 2: FastAPI Env Checker

**Files:**
- Create: `oze-agent/tests/test_verify_phase1b_env.py`
- Create: `oze-agent/scripts/verify_phase1b_env.py`

- [x] Write failing pytest for `collect_missing_phase1b_env`.
- [x] Run `cd oze-agent && PYTHONPATH=. pytest tests/test_verify_phase1b_env.py -q`; expected import failure.
- [x] Implement the checker with explicit required env vars.
- [x] Verify valid env passes and missing service key fails.

### Task 3: Readiness Docs

**Files:**
- Create: `docs/superpowers/specs/2026-04-29-web-app-phase1b-readiness-design.md`
- Create: `docs/superpowers/plans/2026-04-29-web-app-phase1b-readiness.md`
- Create: `docs/WEB_PHASE_1B_READINESS.md`
- Create: `docs/PHASE1B_SMOKE_REPORT_TEMPLATE.md`
- Modify: `docs/STRIPE_PHASE_0C_ROLLOUT.md`
- Modify: `docs/IMPLEMENTATION_PLAN.md`
- Modify: `web/README.md`
- Modify: `oze-agent/.env.example`

- [x] Document local readiness versus staging webhook readiness.
- [x] Document separate Railway bot/API services.
- [x] Document fresh smoke account format and report fields.
- [x] Document exact local and staging verification commands.

### Task 4: Final Verification

**Files:**
- Review all changed files.

- [x] Run `cd web && npm run test:invariants`.
- [x] Run `cd web && npm run lint && npm run build`.
- [x] Run `cd oze-agent && PYTHONPATH=. pytest tests/test_verify_phase1b_env.py tests/test_billing.py tests/test_onboarding_api.py tests/test_dashboard_api.py tests/test_api_auth.py -q`.
- [x] Run `cd oze-agent && PYTHONPATH=. pytest -q`.
- [x] Commit the completed Phase 1B readiness tooling/docs.

### Task 5: Local Smoke Env File Support

**Files:**
- Modify: `web/scripts/check-phase1b-env.mjs`
- Modify: `web/scripts/check-web-invariants.mjs`
- Modify: `oze-agent/scripts/verify_phase1b_env.py`
- Modify: `oze-agent/tests/test_verify_phase1b_env.py`
- Modify: `docs/WEB_PHASE_1B_READINESS.md`
- Modify: `docs/IMPLEMENTATION_PLAN.md`
- Modify: `docs/superpowers/specs/2026-04-29-web-app-phase1b-readiness-design.md`
- Modify: `web/README.md`

- [x] Prove `web/scripts/check-phase1b-env.mjs --env-file=<path>` fails before implementation.
- [x] Add FastAPI pytest coverage for merging env file values.
- [x] Implement dotenv-style `--env-file` loading and default `.env.local` / `.env` loading for web and FastAPI checkers.
- [x] Update runbook/docs with explicit env-file usage.
- [x] Run focused web/backend verification.
- [x] Commit the local smoke env-file support.

### Task 6: Local Route Smoke Automation

**Files:**
- Modify: `web/package.json`
- Modify: `web/scripts/check-web-invariants.mjs`
- Create: `web/scripts/smoke-phase1b-local.mjs`
- Modify: `docs/WEB_PHASE_1B_READINESS.md`
- Modify: `docs/IMPLEMENTATION_PLAN.md`
- Modify: `docs/superpowers/specs/2026-04-29-web-app-phase1b-readiness-design.md`
- Modify: `web/README.md`

- [x] Add a failing invariant requiring `smoke:phase1b-local`.
- [x] Implement local route smoke checks for `/healthz`, public pages, protected redirects, onboarding gate wiring, and no CRM mutation forms.
- [x] Document how to run local route smoke against a running Next.js server.
- [x] Run invariants and local smoke against a dev server.
- [x] Commit the local route smoke automation.

### Task 7: Local FastAPI Smoke Automation

**Files:**
- Create: `oze-agent/scripts/smoke_phase1b_api.py`
- Create: `oze-agent/tests/test_phase1b_api_smoke.py`
- Modify: `docs/WEB_PHASE_1B_READINESS.md`
- Modify: `docs/IMPLEMENTATION_PLAN.md`
- Modify: `docs/superpowers/specs/2026-04-29-web-app-phase1b-readiness-design.md`

- [x] Add a failing pytest import for the API smoke helper.
- [x] Implement `/health` and protected-route fail-closed smoke checks.
- [x] Document how to run API smoke against a local FastAPI server.
- [x] Run pytest and API smoke against a local FastAPI server.
- [x] Commit the local FastAPI smoke automation.

### Task 8: Supabase Migration Preflight

**Files:**
- Create: `oze-agent/scripts/check_phase1b_migrations.py`
- Create: `oze-agent/tests/test_phase1b_migrations.py`
- Modify: `docs/WEB_PHASE_1B_READINESS.md`
- Modify: `docs/IMPLEMENTATION_PLAN.md`
- Modify: `docs/superpowers/specs/2026-04-29-web-app-phase1b-readiness-design.md`

- [x] Add a failing pytest import for the migration preflight helper.
- [x] Implement static checks for auth/RLS and billing/idempotency migration requirements.
- [x] Document the migration preflight before applying Supabase migrations.
- [x] Run pytest and the migration preflight command.
- [x] Commit the migration preflight automation.

### Task 9: Web Env Service-Key Guard

**Files:**
- Modify: `web/scripts/check-phase1b-env.mjs`
- Modify: `web/scripts/check-web-invariants.mjs`
- Modify: `docs/WEB_PHASE_1B_READINESS.md`

- [x] Prove the web env checker currently accepts `SUPABASE_SERVICE_KEY`.
- [x] Reject `SUPABASE_SERVICE_KEY` in web/Vercel env checks.
- [x] Add invariant coverage for the service-key guard.
- [x] Run web env checker positive and negative checks.
- [x] Commit the service-key guard.

### Task 10: Local Readiness Orchestrator

**Files:**
- Create: `oze-agent/scripts/run_phase1b_local_readiness.py`
- Create: `oze-agent/tests/test_phase1b_local_readiness.py`
- Modify: `docs/WEB_PHASE_1B_READINESS.md`
- Modify: `docs/IMPLEMENTATION_PLAN.md`
- Modify: `docs/superpowers/specs/2026-04-29-web-app-phase1b-readiness-design.md`

- [x] Add failing tests for `build_steps()`, optional smoke skipping, full backend inclusion, absolute env-file paths, and report redaction.
- [x] Implement `build_steps()` separately from `run_steps()` so unit tests do not run real commands.
- [x] Implement orchestrated web env, web invariant/lint/build, API env, migration preflight, focused backend tests, optional web smoke, optional API smoke, and optional full backend suite.
- [x] Treat omitted smoke URLs as `skipped`; treat provided unreachable URLs as command failures.
- [x] Redact env-file paths from commands and output in the Markdown report.
- [x] Document the preferred local readiness command.
- [x] Run orchestrator unit tests and a real orchestrator local preflight with temp env files.
- [x] Commit the local readiness orchestrator.

### Task 11: Staging Manifest Preflight

**Files:**
- Create: `oze-agent/scripts/check_phase1b_staging_manifest.py`
- Create: `oze-agent/tests/test_phase1b_staging_manifest.py`
- Create: `docs/phase1b-staging-manifest.example.json`
- Modify: `docs/WEB_PHASE_1B_READINESS.md`
- Modify: `docs/STRIPE_PHASE_0C_ROLLOUT.md`
- Modify: `docs/superpowers/specs/2026-04-29-web-app-phase1b-readiness-design.md`

- [x] Add failing tests for valid manifest, live mode rejection, HTTPS-only URLs, distinct web/API origins, exact webhook URL, exact Railway start command, secret rejection, smoke domain validation, and deterministic smoke identity.
- [x] Implement staging manifest validation with standard URL parsing and recursive secret detection.
- [x] Add a public-data-only example staging manifest.
- [x] Add `--generate-smoke-id` and deterministic `--now=YYYY-MM-DDTHH:MM` support using Europe/Warsaw.
- [x] Document manifest preflight before Stripe webhook creation and smoke account use.
- [x] Run staging manifest tests, example manifest command, and focused Phase 1B readiness tests.
- [x] Commit the staging manifest preflight.

### Task 12: Smoke Report Initializer

**Files:**
- Create: `oze-agent/scripts/init_phase1b_smoke_report.py`
- Create: `oze-agent/tests/test_phase1b_smoke_report_init.py`
- Modify: `docs/WEB_PHASE_1B_READINESS.md`
- Modify: `docs/STRIPE_PHASE_0C_ROLLOUT.md`
- Modify: `docs/superpowers/specs/2026-04-29-web-app-phase1b-readiness-design.md`

- [x] Add failing tests for report initialization, deterministic smoke identity,
      public manifest fields, git branch/commit, operator fallback, secret
      absence, existing output blocking, and invalid manifest blocking.
- [x] Implement a non-mutating report initializer that validates the staging
      manifest, reads git metadata, renders `docs/PHASE1B_SMOKE_REPORT_TEMPLATE.md`,
      and writes only to explicit `--output`.
- [x] Add `--now`, `--operator`, `--environment`, and `--force` support.
- [x] Document report initialization after manifest preflight and before staging
      smoke.
- [x] Run smoke report initializer tests, example command, and focused staging
      manifest plus smoke report tests.
- [x] Commit the smoke report initializer.
