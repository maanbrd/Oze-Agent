# Web App Functional Roadmap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the functional Agent-OZE web app spine: Stripe billing, protected app shell, read-only CRM pages backed by Sheets/Calendar adapters, and onboarding screens.

**Architecture:** Next.js owns browser sessions, hosted Stripe Checkout creation, and the logged-in UI. FastAPI owns service-role Supabase writes and read-only dashboard endpoints that read Google Sheets and Calendar. CRM source-of-truth stays in Google; the web app shows direct Google links and never renders CRM mutation forms.

**Tech Stack:** Next.js 16 App Router, React 19, TypeScript, Tailwind CSS v4, Supabase Auth/SSR, Stripe hosted Checkout, FastAPI, pytest.

---

## File Structure

- Modify: `web/app/api/webhooks/stripe/route.ts` — verify Stripe webhooks, reject live-mode payloads, forward only signed sandbox events to FastAPI.
- Modify: `web/app/onboarding/actions.ts` — create hosted Stripe Checkout sessions using stable lookup keys.
- Modify: `web/app/onboarding/platnosc/page.tsx` — payment step and subscription state.
- Modify: `web/app/onboarding/sukces/page.tsx` — post-checkout polling/status CTA.
- Modify: `web/app/onboarding/anulowano/page.tsx` — retry path.
- Modify: `web/app/dashboard/page.tsx` — replace status-only page with functional dashboard shell.
- Create: `web/app/(app)/layout.tsx` — logged-in shell with sidebar/topbar/floating Google links.
- Create: `web/app/(app)/dashboard/page.tsx` — dashboard route using the shared shell.
- Create: `web/app/(app)/klienci/page.tsx` — read-only clients table and side panel.
- Create: `web/app/(app)/kalendarz/page.tsx` — read-only calendar list/week view.
- Create: `web/app/(app)/platnosci/page.tsx` — subscription and payment history view.
- Create: `web/app/(app)/ustawienia/page.tsx` — account/integration settings, CRM editing disabled.
- Create: `web/app/(app)/import/page.tsx` — non-mutating import interest screen.
- Create: `web/app/(app)/instrukcja/page.tsx` — practical instruction route.
- Create: `web/app/(app)/faq/page.tsx` — FAQ route.
- Create: `web/components/app-shell.tsx` — sidebar, topbar, route frame, floating Google buttons.
- Create: `web/components/crm-notice.tsx` — reusable notice that CRM edits happen in Sheets/Calendar.
- Create: `web/components/data-freshness-badge.tsx` — freshness display beside CRM-derived data.
- Create: `web/lib/crm/types.ts` — shared CRM DTOs.
- Create: `web/lib/crm/mock-data.ts` — demo/empty-state data only.
- Create: `web/lib/crm/adapters.ts` — read-only CRM adapter boundary that targets FastAPI, with explicit fallback rules.
- Create: `web/scripts/check-web-invariants.mjs` — static invariants for no CRM mutation forms and required Google-link notice.
- Modify: `web/package.json` — add `test:invariants`.
- Modify: `oze-agent/api/routes/billing.py` — reject `livemode: true`, strengthen idempotency.
- Modify: `oze-agent/api/routes/dashboard.py` — add read-only dashboard CRM endpoints.
- Modify: `oze-agent/tests/test_billing.py` — billing RED/GREEN tests.
- Create: `oze-agent/tests/test_dashboard_api.py` — dashboard endpoint tests using mocked Google wrappers.
- Modify: `oze-agent/supabase_migrations/20260428_billing_stripe_0c.sql` — ensure Stripe fields/tables match code.
- Modify: `docs/STRIPE_PHASE_0C_ROLLOUT.md` — update only if implementation changes rollout commands or env names.

---

### Task 1: Billing Safety And Idempotency

**Files:**
- Modify: `oze-agent/tests/test_billing.py`
- Modify: `oze-agent/api/routes/billing.py`
- Modify: `web/app/api/webhooks/stripe/route.ts`

- [ ] **Step 1: Write failing FastAPI test for live-mode rejection**

Add to `oze-agent/tests/test_billing.py`:

```python
def test_process_stripe_event_rejects_live_mode(monkeypatch):
    from api.routes import billing

    monkeypatch.setattr(billing, "_get_existing_log", lambda event_id: None)

    with pytest.raises(HTTPException) as exc:
        billing.process_stripe_event(
            {
                "id": "evt_live",
                "type": "checkout.session.completed",
                "livemode": True,
                "object": {"object": "checkout.session", "payment_status": "paid"},
            }
        )

    assert exc.value.status_code == 400
    assert "Live Stripe events are disabled" in exc.value.detail
```

- [ ] **Step 2: Verify RED**

Run:

```bash
cd oze-agent && PYTHONPATH=. pytest tests/test_billing.py::test_process_stripe_event_rejects_live_mode -q
```

Expected: FAIL because `process_stripe_event` currently accepts payloads without checking `livemode`.

- [ ] **Step 3: Implement minimal live-mode guard**

In `oze-agent/api/routes/billing.py`, add this check near the start of `process_stripe_event`, after payload ID/type validation and before inserting webhook logs:

```python
    if payload.get("livemode") is True:
        raise HTTPException(status_code=400, detail="Live Stripe events are disabled in Phase 0C.")
```

- [ ] **Step 4: Verify GREEN**

Run:

```bash
cd oze-agent && PYTHONPATH=. pytest tests/test_billing.py::test_process_stripe_event_rejects_live_mode -q
```

Expected: PASS.

- [ ] **Step 5: Add static web invariant for live-mode rejection**

Create `web/scripts/check-web-invariants.mjs` with this initial content:

```javascript
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import assert from "node:assert/strict";

const root = new URL("..", import.meta.url).pathname;

function read(path) {
  return readFileSync(join(root, path), "utf8");
}

function walk(dir) {
  const entries = readdirSync(join(root, dir));
  return entries.flatMap((entry) => {
    const relative = join(dir, entry);
    const absolute = join(root, relative);
    if (statSync(absolute).isDirectory()) return walk(relative);
    return relative;
  });
}

const stripeWebhook = read("app/api/webhooks/stripe/route.ts");
assert.match(stripeWebhook, /livemode/, "Stripe webhook must inspect livemode.");
assert.match(stripeWebhook, /Live Stripe events are disabled|live mode/i, "Stripe webhook must reject live-mode events.");

console.log("web invariants passed");
```

- [ ] **Step 6: Add script and verify RED**

Modify `web/package.json` scripts:

```json
"test:invariants": "node scripts/check-web-invariants.mjs"
```

Run:

```bash
cd web && npm run test:invariants
```

Expected: FAIL because `web/app/api/webhooks/stripe/route.ts` has no live-mode rejection.

- [ ] **Step 7: Implement minimal Next webhook live-mode guard**

In `web/app/api/webhooks/stripe/route.ts`, after `constructEvent` succeeds and before forwarding:

```typescript
  if (event.livemode) {
    console.error("Live Stripe webhook rejected in Phase 0C", event.id);
    return NextResponse.json(
      { error: "Live Stripe events are disabled in Phase 0C" },
      { status: 400 },
    );
  }
```

- [ ] **Step 8: Verify billing safety**

Run:

```bash
cd web && npm run test:invariants
cd ../oze-agent && PYTHONPATH=. pytest tests/test_billing.py -q
```

Expected: web invariant PASS, billing tests PASS.

- [ ] **Step 9: Commit**

```bash
git add web/package.json web/scripts/check-web-invariants.mjs web/app/api/webhooks/stripe/route.ts oze-agent/api/routes/billing.py oze-agent/tests/test_billing.py
git commit -m "fix(billing): reject live stripe events"
```

---

### Task 2: Read-Only CRM Adapter Boundary

**Files:**
- Create: `web/lib/crm/types.ts`
- Create: `web/lib/crm/mock-data.ts`
- Create: `web/lib/crm/adapters.ts`
- Modify: `web/scripts/check-web-invariants.mjs`

- [ ] **Step 1: Write failing invariant for CRM source boundary**

Append to `web/scripts/check-web-invariants.mjs`:

```javascript
const crmAdapter = read("lib/crm/adapters.ts");
assert.match(crmAdapter, /sheets/i, "CRM adapter must model Sheets as client source.");
assert.match(crmAdapter, /calendar/i, "CRM adapter must model Calendar as event source.");
assert.doesNotMatch(crmAdapter, /\.insert\(|\.update\(|\.delete\(/, "CRM adapter must be read-only.");
```

- [ ] **Step 2: Verify RED**

Run:

```bash
cd web && npm run test:invariants
```

Expected: FAIL because `web/lib/crm/adapters.ts` does not exist.

- [ ] **Step 3: Add CRM types**

Create `web/lib/crm/types.ts`:

```typescript
export type FunnelStatus =
  | "Nowy lead"
  | "Spotkanie umówione"
  | "Spotkanie odbyte"
  | "Oferta wysłana"
  | "Podpisane"
  | "Zamontowana"
  | "Rezygnacja z umowy"
  | "Nieaktywny"
  | "Odrzucone";

export type CrmClient = {
  id: string;
  fullName: string;
  city: string;
  phone: string | null;
  email: string | null;
  address: string | null;
  product: string | null;
  status: FunnelStatus;
  notes: string | null;
  lastContactAt: string | null;
  nextAction: string | null;
  nextActionAt: string | null;
  sheetsUrl: string | null;
  calendarUrl: string | null;
  driveUrl: string | null;
};

export type CrmEventType = "in_person" | "phone_call" | "offer_email" | "doc_followup";

export type CrmEvent = {
  id: string;
  clientId: string | null;
  title: string;
  clientName: string;
  city: string | null;
  startsAt: string;
  endsAt: string;
  type: CrmEventType;
  location: string | null;
  calendarUrl: string | null;
};

export type CrmDashboardData = {
  fetchedAt: string;
  clients: CrmClient[];
  events: CrmEvent[];
};
```

- [ ] **Step 4: Add mock data isolated behind adapter**

Create `web/lib/crm/mock-data.ts` with at least five realistic Polish clients and four events. Each client must include `sheetsUrl`; each event must include `calendarUrl`.

- [ ] **Step 5: Add read-only adapter**

Create `web/lib/crm/adapters.ts`:

```typescript
import "server-only";

import { getCurrentAccount } from "@/lib/api/account";
import { mockCrmDashboardData } from "@/lib/crm/mock-data";
import type { CrmDashboardData } from "@/lib/crm/types";

function apiBaseUrl() {
  return (
    process.env.FASTAPI_INTERNAL_BASE_URL ??
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    ""
  ).replace(/\/$/, "");
}

export async function getCrmDashboardData(): Promise<CrmDashboardData> {
  const account = await getCurrentAccount();
  const baseUrl = apiBaseUrl();

  if (!account.authenticated || !account.accessToken || !baseUrl) {
    return mockCrmDashboardData;
  }

  const response = await fetch(`${baseUrl}/api/dashboard/crm`, {
    headers: { Authorization: `Bearer ${account.accessToken}` },
    cache: "no-store",
  });

  if (!response.ok) {
    return mockCrmDashboardData;
  }

  return (await response.json()) as CrmDashboardData;
}
```

- [ ] **Step 6: Verify GREEN**

Run:

```bash
cd web && npm run test:invariants && npm run lint
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add web/lib/crm web/scripts/check-web-invariants.mjs
git commit -m "feat(web): add read-only crm adapter boundary"
```

---

### Task 3: App Shell And CRM Mutation Guardrails

**Files:**
- Create: `web/components/app-shell.tsx`
- Create: `web/components/crm-notice.tsx`
- Create: `web/components/data-freshness-badge.tsx`
- Create: `web/app/(app)/layout.tsx`
- Modify: `web/scripts/check-web-invariants.mjs`

- [ ] **Step 1: Write failing invariant for CRM edit messaging and no mutation forms**

Append to `web/scripts/check-web-invariants.mjs`:

```javascript
const appFiles = walk("app").filter((file) => file.endsWith(".tsx"));
const appSource = appFiles.map((file) => read(file)).join("\n");
assert.match(appSource, /CRM|Sheets|Calendar|Google/, "App UI must mention CRM/Google edit boundary.");
assert.doesNotMatch(appSource, /action=\{.*addClient|action=\{.*updateClient|name=\"status\"/s, "App UI must not expose CRM mutation forms.");
```

- [ ] **Step 2: Verify RED**

Run:

```bash
cd web && npm run test:invariants
```

Expected: FAIL because the shell and notice do not exist yet.

- [ ] **Step 3: Create CRM notice**

Create `web/components/crm-notice.tsx`:

```tsx
export function CrmNotice() {
  return (
    <section className="rounded-[8px] border border-amber-300/20 bg-amber-300/10 px-4 py-3 text-sm leading-6 text-amber-100">
      CRM edytujesz w Google: klienty w Sheets, spotkania i akcje w Calendar.
      Ten panel pokazuje dane read-only i daje bezpośrednie linki do Google.
    </section>
  );
}
```

- [ ] **Step 4: Create freshness badge**

Create `web/components/data-freshness-badge.tsx`:

```tsx
export function DataFreshnessBadge({ fetchedAt }: { fetchedAt: string }) {
  const date = new Date(fetchedAt);
  const label = Number.isNaN(date.getTime())
    ? "odświeżenie nieznane"
    : `odświeżone ${date.toLocaleString("pl-PL", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })}`;

  return (
    <span className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-xs text-zinc-400">
      {label}
    </span>
  );
}
```

- [ ] **Step 5: Create app shell**

Create `web/components/app-shell.tsx` with:

- sidebar links for Dashboard, Klienci, Kalendarz, Płatności, Ustawienia, Import, Instrukcja, FAQ
- topbar search input as non-mutating client search
- floating links labelled Sheets, Calendar, Drive
- fallback disabled labels when Google URLs are missing

- [ ] **Step 6: Create logged-in layout**

Create `web/app/(app)/layout.tsx`:

```tsx
import { redirect } from "next/navigation";
import { AppShell } from "@/components/app-shell";
import { getCurrentAccount } from "@/lib/api/account";

export default async function LoggedInLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const account = await getCurrentAccount();
  if (!account.authenticated) {
    redirect("/login?next=/dashboard");
  }

  return <AppShell account={account}>{children}</AppShell>;
}
```

- [ ] **Step 7: Verify GREEN**

Run:

```bash
cd web && npm run test:invariants && npm run lint
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add web/components/app-shell.tsx web/components/crm-notice.tsx web/components/data-freshness-badge.tsx 'web/app/(app)/layout.tsx' web/scripts/check-web-invariants.mjs
git commit -m "feat(web): add protected app shell"
```

---

### Task 4: Functional Dashboard, Clients, And Calendar Pages

**Files:**
- Create: `web/app/(app)/dashboard/page.tsx`
- Create: `web/app/(app)/klienci/page.tsx`
- Create: `web/app/(app)/kalendarz/page.tsx`
- Modify: `web/app/dashboard/page.tsx`

- [ ] **Step 1: Write failing invariant for required app routes**

Append to `web/scripts/check-web-invariants.mjs`:

```javascript
for (const route of [
  "app/(app)/dashboard/page.tsx",
  "app/(app)/klienci/page.tsx",
  "app/(app)/kalendarz/page.tsx",
]) {
  assert.match(read(route), /getCrmDashboardData|CrmNotice|DataFreshnessBadge/, `${route} must use CRM read-only primitives.`);
}
```

- [ ] **Step 2: Verify RED**

Run:

```bash
cd web && npm run test:invariants
```

Expected: FAIL because the app routes do not exist.

- [ ] **Step 3: Build `/dashboard` inside app group**

Create `web/app/(app)/dashboard/page.tsx` that:

- calls `getCrmDashboardData()`
- renders `CrmNotice`
- renders `DataFreshnessBadge`
- shows four KPI cards from clients/events
- shows status funnel counts
- shows today events from Calendar data
- shows urgent clients from Sheets rows with `nextActionAt`

- [ ] **Step 4: Redirect legacy dashboard route**

Replace `web/app/dashboard/page.tsx` content with:

```tsx
import { redirect } from "next/navigation";

export default function DashboardRedirect() {
  redirect("/dashboard");
}
```

If Next route grouping conflicts with the existing path, delete the legacy route instead and keep only `web/app/(app)/dashboard/page.tsx`.

- [ ] **Step 5: Build `/klienci`**

Create `web/app/(app)/klienci/page.tsx` that:

- calls `getCrmDashboardData()`
- renders `CrmNotice`
- renders filters/search UI without server actions that mutate CRM
- renders a table of Sheets-backed clients
- renders direct `Otwórz w Sheets`, `Pokaż w Calendar`, `Folder Drive` links when present

- [ ] **Step 6: Build `/kalendarz`**

Create `web/app/(app)/kalendarz/page.tsx` that:

- calls `getCrmDashboardData()`
- renders `CrmNotice`
- renders Calendar-backed event cards grouped by date
- renders direct Google Calendar links
- does not render add/edit event forms

- [ ] **Step 7: Verify GREEN**

Run:

```bash
cd web && npm run test:invariants && npm run lint && npm run build
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add 'web/app/(app)/dashboard/page.tsx' 'web/app/(app)/klienci/page.tsx' 'web/app/(app)/kalendarz/page.tsx' web/app/dashboard/page.tsx web/scripts/check-web-invariants.mjs
git commit -m "feat(web): add read-only crm dashboard pages"
```

---

### Task 5: Payments, Settings, Import, Instruction, FAQ Routes

**Files:**
- Create: `web/app/(app)/platnosci/page.tsx`
- Create: `web/app/(app)/ustawienia/page.tsx`
- Create: `web/app/(app)/import/page.tsx`
- Create: `web/app/(app)/instrukcja/page.tsx`
- Create: `web/app/(app)/faq/page.tsx`

- [ ] **Step 1: Write failing invariant for secondary routes**

Append to `web/scripts/check-web-invariants.mjs`:

```javascript
for (const route of [
  "app/(app)/platnosci/page.tsx",
  "app/(app)/ustawienia/page.tsx",
  "app/(app)/import/page.tsx",
  "app/(app)/instrukcja/page.tsx",
  "app/(app)/faq/page.tsx",
]) {
  assert.ok(read(route).length > 200, `${route} must be implemented.`);
}
```

- [ ] **Step 2: Verify RED**

Run:

```bash
cd web && npm run test:invariants
```

Expected: FAIL because the routes do not exist.

- [ ] **Step 3: Build `/platnosci`**

Create a page that reads `getCurrentAccount()`, shows subscription status, plan, current period end, activation paid state, and a CTA back to `/onboarding/platnosc` when unpaid.

- [ ] **Step 4: Build `/ustawienia`**

Create a page that shows profile, Google integration state, Telegram pairing state, and disabled CRM settings with text: `Statusy i kolumny zmieniasz w Google. Panel nie zapisuje zmian CRM.`

- [ ] **Step 5: Build `/import`**

Create a non-mutating route that explains CSV import is not active and has no upload form that writes CRM data.

- [ ] **Step 6: Build `/instrukcja` and `/faq`**

Create concise functional routes with sections for using Telegram, reading dashboard data, opening Google links, and billing.

- [ ] **Step 7: Verify GREEN**

Run:

```bash
cd web && npm run test:invariants && npm run lint && npm run build
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add 'web/app/(app)/platnosci/page.tsx' 'web/app/(app)/ustawienia/page.tsx' 'web/app/(app)/import/page.tsx' 'web/app/(app)/instrukcja/page.tsx' 'web/app/(app)/faq/page.tsx' web/scripts/check-web-invariants.mjs
git commit -m "feat(web): add functional secondary app routes"
```

---

### Task 6: FastAPI Read-Only Dashboard Endpoints

**Files:**
- Create: `oze-agent/tests/test_dashboard_api.py`
- Modify: `oze-agent/api/routes/dashboard.py`

- [ ] **Step 1: Write failing endpoint test**

Create `oze-agent/tests/test_dashboard_api.py`:

```python
from types import SimpleNamespace

import pytest


class _FakeQuery:
    def __init__(self, data):
        self.data = data

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def execute(self):
        return SimpleNamespace(data=self.data)


class _FakeSupabase:
    def __init__(self, users):
        self.users = users

    def table(self, name):
        assert name == "users"
        return _FakeQuery(self.users)


@pytest.mark.asyncio
async def test_dashboard_crm_uses_google_resource_ids(monkeypatch):
    from api.auth import AuthUser
    from api.routes import dashboard

    user = {
        "id": "user-1",
        "auth_user_id": "auth-1",
        "google_sheets_id": "sheet-1",
        "google_calendar_id": "cal-1",
        "google_drive_folder_id": "drive-1",
    }
    monkeypatch.setattr(dashboard, "get_supabase_client", lambda: _FakeSupabase([user]))
    monkeypatch.setattr(
        dashboard,
        "_fetch_sheet_clients",
        lambda user_id, sheet_id: [
            {
                "id": "sheet-row-1",
                "fullName": "Jan Testowy",
                "city": "Marki",
                "status": "Nowy lead",
                "sheetsUrl": "https://docs.google.com/spreadsheets/d/sheet-1",
            }
        ],
    )
    monkeypatch.setattr(
        dashboard,
        "_fetch_calendar_events",
        lambda user_id, calendar_id: [
            {
                "id": "event-1",
                "clientName": "Jan Testowy",
                "startsAt": "2026-04-30T10:00:00+02:00",
                "calendarUrl": "https://calendar.google.com/calendar",
            }
        ],
    )

    result = await dashboard.get_dashboard_crm(
        AuthUser(user_id="auth-1", email="jan@example.pl")
    )

    assert result["clients"][0]["sheetsUrl"].startswith("https://docs.google.com")
    assert result["events"][0]["calendarUrl"].startswith("https://calendar.google.com")
```

- [ ] **Step 2: Verify RED**

Run:

```bash
cd oze-agent && PYTHONPATH=. pytest tests/test_dashboard_api.py -q
```

Expected: FAIL because `/api/dashboard/crm` and helper functions do not exist.

- [ ] **Step 3: Implement minimal endpoint**

In `oze-agent/api/routes/dashboard.py`, add:

```python
from datetime import datetime, timezone
from typing import Any


def _fetch_sheet_clients(user_id: str, sheet_id: str) -> list[dict[str, Any]]:
    return []


def _fetch_calendar_events(user_id: str, calendar_id: str) -> list[dict[str, Any]]:
    return []


@router.get("/dashboard/crm")
async def get_dashboard_crm(auth_user: AuthUser = Depends(get_current_auth_user)):
    user_result = (
        get_supabase_client()
        .table("users")
        .select("id, auth_user_id, google_sheets_id, google_calendar_id, google_drive_folder_id")
        .eq("auth_user_id", auth_user.user_id)
        .limit(1)
        .execute()
    )
    if not user_result.data:
        return {"fetchedAt": datetime.now(tz=timezone.utc).isoformat(), "clients": [], "events": []}

    user = user_result.data[0]
    clients = []
    events = []
    if user.get("google_sheets_id"):
        clients = _fetch_sheet_clients(user["id"], user["google_sheets_id"])
    if user.get("google_calendar_id"):
        events = _fetch_calendar_events(user["id"], user["google_calendar_id"])

    return {
        "fetchedAt": datetime.now(tz=timezone.utc).isoformat(),
        "clients": clients,
        "events": events,
    }
```

- [ ] **Step 4: Verify GREEN**

Run:

```bash
cd oze-agent && PYTHONPATH=. pytest tests/test_dashboard_api.py tests/test_api_auth.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add oze-agent/api/routes/dashboard.py oze-agent/tests/test_dashboard_api.py
git commit -m "feat(api): add read-only dashboard crm endpoint"
```

---

### Task 7: Final Verification And Development Commit Hygiene

**Files:**
- Review all changed files.

- [ ] **Step 1: Run web verification**

```bash
cd web && npm run test:invariants && npm run lint && npm run build
```

Expected: all commands exit 0.

- [ ] **Step 2: Run Python verification**

```bash
cd oze-agent && PYTHONPATH=. pytest tests/test_billing.py tests/test_dashboard_api.py tests/test_api_auth.py -q
```

Expected: all selected tests pass.

- [ ] **Step 3: Run broader Python baseline if local env allows**

```bash
cd oze-agent && PYTHONPATH=. pytest -q
```

Expected: pass, or report exact failures if unrelated environment dependencies block the run.

- [ ] **Step 4: Inspect diff**

```bash
git status --short
git diff --stat HEAD
```

Expected: only planned files are modified/untracked.

- [ ] **Step 5: Use finishing-a-development-branch**

Invoke `superpowers:finishing-a-development-branch` and follow its workflow for final branch handling.
