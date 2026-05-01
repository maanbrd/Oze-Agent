# Web App Phase 1 Continuation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking. All checklist items below are now complete.

_Status 29.04.2026: COMPLETED on `feat/web-phase-0c` and pushed to PR #5._

Verification evidence:

- `cd oze-agent && PYTHONPATH=. pytest tests/test_onboarding_api.py tests/test_dashboard_api.py tests/test_api_auth.py -q` -> 11 passed.
- `cd oze-agent && PYTHONPATH=. pytest -q` -> 840 passed.
- `cd web && npm run test:invariants && npm run lint && npm run build` -> pass.

**Goal:** Continue the approved Phase 1 web app work by hardening onboarding gates, Google resource retries, live CRM metadata, and Telegram pairing instructions.

**Architecture:** FastAPI remains the trusted service boundary for Supabase service-role writes and Google operations. Next.js renders authenticated app UI and reads onboarding/CRM status through server-side helpers. Telegram remains the CRM mutation surface; the web app only helps pair Telegram via the existing `/start <code>` linking flow.

**Tech Stack:** FastAPI, pytest, Next.js 16 App Router, TypeScript, static web invariants, Tailwind CSS v4.

---

## File Structure

- Modify: `oze-agent/tests/test_onboarding_api.py` — add partial-resource retry test.
- Modify: `oze-agent/api/routes/onboarding.py` — persist each created Google resource immediately.
- Modify: `oze-agent/tests/test_dashboard_api.py` — require CRM source metadata.
- Modify: `oze-agent/api/routes/dashboard.py` — return `source` and `sourceMessage`.
- Create: `web/components/onboarding-gate.tsx` — reusable app-shell banner for incomplete onboarding.
- Modify: `web/components/app-shell.tsx` — accept and render onboarding status.
- Modify: `web/app/(app)/layout.tsx` — fetch onboarding status and pass it to the shell.
- Modify: `web/app/onboarding/telegram/page.tsx` — show `/start <code>` command instructions.
- Modify: `web/scripts/check-web-invariants.mjs` — enforce onboarding gate and Telegram command guidance.

---

### Task 1: Partial-Safe Google Resource Creation

**Files:**
- Modify: `oze-agent/tests/test_onboarding_api.py`
- Modify: `oze-agent/api/routes/onboarding.py`

- [x] **Step 1: Write failing test**

Add this test:

```python
@pytest.mark.asyncio
async def test_create_google_resources_persists_partial_success_before_later_failure(monkeypatch):
    from fastapi import HTTPException
    from api.auth import AuthUser
    from api.routes import onboarding

    fake = _FakeSupabase([
        {
            "id": "user-1",
            "auth_user_id": "auth-1",
            "email": "jan@example.pl",
            "name": "Jan Test",
            "subscription_status": "active",
            "activation_paid": True,
            "google_refresh_token": "encrypted",
            "google_sheets_id": "existing-sheet",
            "google_calendar_id": None,
            "google_drive_folder_id": None,
        }
    ])
    monkeypatch.setattr(onboarding, "get_supabase_client", lambda: fake)
    monkeypatch.setattr(onboarding, "create_calendar", lambda user_id, name: "calendar-1")
    monkeypatch.setattr(onboarding, "create_root_folder", lambda user_id: None)

    with pytest.raises(HTTPException):
        await onboarding.create_google_resources(
            {"calendarName": "Agent-OZE Calendar"},
            AuthUser(user_id="auth-1", email="jan@example.pl", claims={}),
        )

    assert fake.rows[0]["google_calendar_id"] == "calendar-1"
```

- [x] **Step 2: Verify RED**

Run:

```bash
cd oze-agent && PYTHONPATH=. pytest tests/test_onboarding_api.py::test_create_google_resources_persists_partial_success_before_later_failure -q
```

Expected: FAIL because the endpoint stores updates only after all resources are created.

- [x] **Step 3: Implement incremental persistence**

In `oze-agent/api/routes/onboarding.py`, add:

```python
def _persist_user_update(user: dict[str, Any], update_data: dict[str, Any]) -> None:
    if not update_data:
        return
    payload = {**update_data, "updated_at": _now_iso()}
    get_supabase_client().table("users").update(payload).eq("id", user["id"]).execute()
    user.update(payload)
```

Then call `_persist_user_update(user, {...})` immediately after each successful
Sheets, Calendar, and Drive creation.

- [x] **Step 4: Verify GREEN**

Run:

```bash
cd oze-agent && PYTHONPATH=. pytest tests/test_onboarding_api.py -q
```

Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add oze-agent/tests/test_onboarding_api.py oze-agent/api/routes/onboarding.py
git commit -m "fix(api): persist partial google onboarding resources"
```

---

### Task 2: CRM Source Metadata From FastAPI

**Files:**
- Modify: `oze-agent/tests/test_dashboard_api.py`
- Modify: `oze-agent/api/routes/dashboard.py`

- [x] **Step 1: Write failing test assertion**

In `test_dashboard_crm_uses_google_resource_ids`, add:

```python
assert result["source"] == "live"
assert "Google" in result["sourceMessage"]
```

- [x] **Step 2: Verify RED**

Run:

```bash
cd oze-agent && PYTHONPATH=. pytest tests/test_dashboard_api.py::test_dashboard_crm_uses_google_resource_ids -q
```

Expected: FAIL with missing `source`.

- [x] **Step 3: Implement source metadata**

In every return from `get_dashboard_crm`, include:

```python
"source": "live",
"sourceMessage": "Dane z Google Sheets i Calendar.",
```

- [x] **Step 4: Verify GREEN**

Run:

```bash
cd oze-agent && PYTHONPATH=. pytest tests/test_dashboard_api.py tests/test_onboarding_api.py -q
```

Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add oze-agent/tests/test_dashboard_api.py oze-agent/api/routes/dashboard.py
git commit -m "feat(api): return crm source metadata"
```

---

### Task 3: App-Wide Onboarding Gate

**Files:**
- Create: `web/components/onboarding-gate.tsx`
- Modify: `web/components/app-shell.tsx`
- Modify: `web/app/(app)/layout.tsx`
- Modify: `web/scripts/check-web-invariants.mjs`

- [x] **Step 1: Add failing invariant**

Append:

```javascript
const onboardingGate = read("components/onboarding-gate.tsx");
const appShell = read("components/app-shell.tsx");
const appLayout = read("app/(app)/layout.tsx");
assert.match(onboardingGate, /nextStep/, "Onboarding gate must link to the next step.");
assert.match(appShell, /OnboardingGate/, "App shell must render onboarding gate.");
assert.match(appLayout, /getOnboardingStatus/, "Logged-in layout must fetch onboarding status.");
```

- [x] **Step 2: Verify RED**

Run:

```bash
cd web && npm run test:invariants
```

Expected: FAIL because `components/onboarding-gate.tsx` is missing.

- [x] **Step 3: Add gate component**

Create `web/components/onboarding-gate.tsx`:

```tsx
import Link from "next/link";
import type { OnboardingStatus } from "@/lib/api/onboarding";

export function OnboardingGate({ status }: { status: OnboardingStatus | null }) {
  if (!status || status.completed) return null;
  return (
    <section className="mb-5 rounded-[8px] border border-[#3DFF7A]/25 bg-[#3DFF7A]/10 px-4 py-3 text-sm text-zinc-200">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <p>Dokończ onboarding, żeby panel czytał live dane z Google.</p>
        <Link href={status.nextStep} className="w-fit rounded-full bg-[#3DFF7A] px-4 py-2 text-xs font-semibold text-black">
          Kontynuuj
        </Link>
      </div>
    </section>
  );
}
```

- [x] **Step 4: Render gate in app shell**

Update `AppShell` props to accept `onboardingStatus` and render:

```tsx
<OnboardingGate status={onboardingStatus} />
```

above `{children}`.

- [x] **Step 5: Fetch status in layout**

In `web/app/(app)/layout.tsx`, import `getOnboardingStatus`, fetch it after
auth, and pass it to `AppShell`.

- [x] **Step 6: Verify GREEN**

Run:

```bash
cd web && npm run test:invariants && npm run lint && npm run build
```

Expected: PASS.

- [x] **Step 7: Commit**

```bash
git add web/components/onboarding-gate.tsx web/components/app-shell.tsx web/app/'(app)'/layout.tsx web/scripts/check-web-invariants.mjs
git commit -m "feat(web): add app onboarding gate"
```

---

### Task 4: Telegram Pairing Instructions

**Files:**
- Modify: `web/app/onboarding/telegram/page.tsx`
- Modify: `web/scripts/check-web-invariants.mjs`

- [x] **Step 1: Add failing invariant**

Append:

```javascript
const telegramPage = read("app/onboarding/telegram/page.tsx");
assert.match(telegramPage, /\\/start/, "Telegram onboarding must show /start code command.");
```

- [x] **Step 2: Verify RED**

Run:

```bash
cd web && npm run test:invariants
```

Expected: FAIL because the screen shows the code but not the exact command.

- [x] **Step 3: Update Telegram page**

Render the command:

```tsx
<code className="mt-4 block rounded-[8px] bg-black/40 px-4 py-3 text-lg text-white">
  /start {pairing?.code ?? "KOD"}
</code>
```

- [x] **Step 4: Verify GREEN**

Run:

```bash
cd web && npm run test:invariants && npm run lint && npm run build
```

Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add web/app/onboarding/telegram/page.tsx web/scripts/check-web-invariants.mjs
git commit -m "feat(web): clarify telegram pairing command"
```

---

### Task 5: Final Verification And Push

**Files:**
- Review all changed files.

- [x] **Step 1: Focused backend**

Run:

```bash
cd oze-agent && PYTHONPATH=. pytest tests/test_onboarding_api.py tests/test_dashboard_api.py tests/test_api_auth.py -q
```

Expected: PASS.

- [x] **Step 2: Full backend**

Run:

```bash
cd oze-agent && PYTHONPATH=. pytest -q
```

Expected: PASS.

- [x] **Step 3: Full web**

Run:

```bash
cd web && npm run test:invariants && npm run lint && npm run build
```

Expected: PASS.

- [x] **Step 4: Push**

Run:

```bash
git status --short --branch
git push
```

Expected: clean branch pushed to `origin/feat/web-phase-0c`.

---

## Self-Review

Spec coverage:

- Partial retry safety for Google resources: Task 1.
- Live CRM source state from backend, not only frontend fallback: Task 2.
- Route/app gate toward next onboarding step: Task 3.
- Telegram screen actually tells user how to pair with existing `/start <code>` flow: Task 4.

Placeholder scan:

- No placeholder markers or unspecified implementation steps remain.

Type consistency:

- `OnboardingStatus` is imported from existing `web/lib/api/onboarding.ts`.
- Existing bot `/start <code>` handler already consumes `telegram_link_code`; the web task only exposes the command clearly.
