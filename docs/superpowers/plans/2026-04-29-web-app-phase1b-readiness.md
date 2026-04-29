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
- [ ] Commit the completed Phase 1B readiness tooling/docs.
