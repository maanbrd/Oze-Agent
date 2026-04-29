# Web App Onboarding And Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

_Status 29.04.2026: implemented on `feat/web-phase-0c` / PR #5, then hardened
by `2026-04-29-web-app-phase1-continuation.md`. Remaining work is Phase 1B
rollout/readiness smoke._

**Goal:** Complete Phase 0D/0E/0F and Phase 1 for the web app: real onboarding state, Google OAuth/resource setup, Telegram pairing, safer live CRM data handling, and functional account settings without web CRM mutations.

Historical note: the task checklist below is preserved as the original execution
plan. The branch has since implemented and hardened this scope; see the status
header above and the continuation plan for final verification evidence.

**Architecture:** FastAPI owns trusted Supabase service-role writes and Google integration operations. Next.js owns server-rendered UI and calls FastAPI with the Supabase access token. CRM data remains read-only in the web app; Google Sheets/Calendar/Drive remain the CRM source of truth.

**Tech Stack:** FastAPI, pytest, Supabase service client, Google wrappers, Next.js 16 App Router, React 19, TypeScript, Tailwind CSS v4, Supabase SSR.

---

## File Structure

- Create: `oze-agent/api/routes/onboarding.py` — authenticated onboarding status, resource creation, Telegram pairing, account update endpoints.
- Modify: `oze-agent/api/main.py` — mount onboarding router under `/api/onboarding`.
- Modify: `oze-agent/api/routes/google_oauth.py` — consume signed OAuth state and redirect back to web onboarding routes.
- Modify: `oze-agent/bot/config.py` — add `GOOGLE_OAUTH_STATE_SECRET` to secret config, defaulting to `BILLING_INTERNAL_SECRET` at call sites when unset.
- Create: `oze-agent/tests/test_onboarding_api.py` — backend tests for status, resources, pairing, account update, OAuth state.
- Modify: `web/lib/api/account.ts` — include onboarding/account fields needed by UI.
- Create: `web/lib/api/onboarding.ts` — server-only FastAPI client helpers for onboarding endpoints.
- Modify: `web/app/onboarding/actions.ts` — add server actions for Google OAuth, resource creation, Telegram code, and account settings.
- Create: `web/app/onboarding/google/page.tsx` — Google connection step.
- Create: `web/app/onboarding/google/sukces/page.tsx` — Google OAuth success landing.
- Create: `web/app/onboarding/zasoby/page.tsx` — Google resource creation step.
- Create: `web/app/onboarding/telegram/page.tsx` — Telegram pairing step.
- Modify: `web/app/onboarding/sukces/page.tsx` — after Stripe success, route toward Google onboarding.
- Modify: `web/app/(app)/dashboard/page.tsx` — show onboarding gate and live/demo/unavailable CRM source.
- Modify: `web/app/(app)/klienci/page.tsx` — show CRM source state and avoid silent demo data.
- Modify: `web/app/(app)/kalendarz/page.tsx` — show CRM source state and avoid silent demo data.
- Modify: `web/app/(app)/ustawienia/page.tsx` — add system account settings form only.
- Modify: `web/lib/crm/types.ts` — add CRM source metadata.
- Modify: `web/lib/crm/mock-data.ts` — mark mock data as demo.
- Modify: `web/lib/crm/adapters.ts` — completed accounts fail visibly instead of silently showing mock CRM.
- Modify: `web/components/crm-notice.tsx` — keep explicit Google edit boundary.
- Modify: `web/scripts/check-web-invariants.mjs` — assert onboarding routes exist, no CRM mutation forms, and no Przelewy24 copy.
- Modify: `web/.env.example` and `web/README.md` — document onboarding env names and routes.

---

### Task 1: FastAPI Onboarding Status And Account Update

**Files:**
- Create: `oze-agent/api/routes/onboarding.py`
- Modify: `oze-agent/api/main.py`
- Create: `oze-agent/tests/test_onboarding_api.py`

- [ ] **Step 1: Write failing tests for onboarding status and account update**

Add to `oze-agent/tests/test_onboarding_api.py`:

```python
from types import SimpleNamespace

import pytest


class _FakeQuery:
    def __init__(self, rows):
        self.rows = rows
        self.updated = None

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def update(self, data):
        self.updated = data
        for row in self.rows:
            row.update(data)
        return self

    def execute(self):
        return SimpleNamespace(data=self.rows)


class _FakeSupabase:
    def __init__(self, rows):
        self.rows = rows
        self.last_query = None

    def table(self, name):
        assert name == "users"
        self.last_query = _FakeQuery(self.rows)
        return self.last_query


@pytest.mark.asyncio
async def test_onboarding_status_next_step_payment(monkeypatch):
    from api.auth import AuthUser
    from api.routes import onboarding

    fake = _FakeSupabase([
        {
            "id": "user-1",
            "auth_user_id": "auth-1",
            "email": "jan@example.pl",
            "name": "Jan",
            "phone": None,
            "subscription_status": "pending_payment",
            "activation_paid": False,
            "google_access_token": None,
            "google_refresh_token": None,
            "google_sheets_id": None,
            "google_calendar_id": None,
            "google_drive_folder_id": None,
            "telegram_id": None,
            "telegram_link_code": None,
            "telegram_link_code_expires": None,
            "onboarding_completed": False,
        }
    ])
    monkeypatch.setattr(onboarding, "get_supabase_client", lambda: fake)

    result = await onboarding.get_onboarding_status(
        AuthUser(user_id="auth-1", email="jan@example.pl", claims={})
    )

    assert result["nextStep"] == "/onboarding/platnosc"
    assert result["steps"]["payment"] is False
    assert result["steps"]["google"] is False
    assert result["profile"]["id"] == "user-1"


@pytest.mark.asyncio
async def test_update_account_allows_only_system_fields(monkeypatch):
    from api.auth import AuthUser
    from api.routes import onboarding

    fake = _FakeSupabase([
        {
            "id": "user-1",
            "auth_user_id": "auth-1",
            "email": "jan@example.pl",
            "name": "Jan",
            "phone": None,
        }
    ])
    monkeypatch.setattr(onboarding, "get_supabase_client", lambda: fake)

    result = await onboarding.update_account(
        {"name": "Jan Test", "phone": "600100200", "google_sheets_id": "blocked"},
        AuthUser(user_id="auth-1", email="jan@example.pl", claims={}),
    )

    assert result["profile"]["name"] == "Jan Test"
    assert result["profile"]["phone"] == "600100200"
    assert "google_sheets_id" not in fake.last_query.updated
```

- [ ] **Step 2: Verify RED**

Run:

```bash
cd oze-agent && PYTHONPATH=. pytest tests/test_onboarding_api.py::test_onboarding_status_next_step_payment tests/test_onboarding_api.py::test_update_account_allows_only_system_fields -q
```

Expected: FAIL with `ImportError` or missing `api.routes.onboarding`.

- [ ] **Step 3: Implement onboarding route**

Create `oze-agent/api/routes/onboarding.py`:

```python
"""Authenticated web onboarding routes."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from api.auth import AuthUser, get_current_auth_user
from shared.database import get_supabase_client

router = APIRouter()

USER_SELECT = (
    "id, auth_user_id, email, name, phone, subscription_status, "
    "subscription_plan, subscription_current_period_end, activation_paid, "
    "google_access_token, google_refresh_token, google_token_expiry, "
    "google_sheets_id, google_sheets_name, google_calendar_id, "
    "google_calendar_name, google_drive_folder_id, telegram_id, "
    "telegram_link_code, telegram_link_code_expires, onboarding_completed"
)


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _get_user_for_auth(auth_user: AuthUser) -> dict[str, Any]:
    result = (
        get_supabase_client()
        .table("users")
        .select(USER_SELECT)
        .eq("auth_user_id", auth_user.user_id)
        .limit(1)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return result.data[0]


def _has_google_tokens(user: dict[str, Any]) -> bool:
    return bool(user.get("google_refresh_token"))


def _has_resources(user: dict[str, Any]) -> bool:
    return bool(
        user.get("google_sheets_id")
        and user.get("google_calendar_id")
        and user.get("google_drive_folder_id")
    )


def _has_payment(user: dict[str, Any]) -> bool:
    return user.get("subscription_status") == "active" and bool(user.get("activation_paid"))


def _has_telegram(user: dict[str, Any]) -> bool:
    return bool(user.get("telegram_id"))


def _next_step(user: dict[str, Any]) -> str:
    if not _has_payment(user):
        return "/onboarding/platnosc"
    if not _has_google_tokens(user):
        return "/onboarding/google"
    if not _has_resources(user):
        return "/onboarding/zasoby"
    if not _has_telegram(user):
        return "/onboarding/telegram"
    return "/dashboard"


def _status_payload(user: dict[str, Any]) -> dict[str, Any]:
    steps = {
        "payment": _has_payment(user),
        "google": _has_google_tokens(user),
        "resources": _has_resources(user),
        "telegram": _has_telegram(user),
    }
    completed = all(steps.values())
    return {
        "fetchedAt": _now_iso(),
        "nextStep": "/dashboard" if completed else _next_step(user),
        "completed": completed,
        "steps": steps,
        "profile": {
            "id": user.get("id"),
            "auth_user_id": user.get("auth_user_id"),
            "email": user.get("email"),
            "name": user.get("name"),
            "phone": user.get("phone"),
            "subscription_status": user.get("subscription_status"),
            "subscription_plan": user.get("subscription_plan"),
            "subscription_current_period_end": user.get("subscription_current_period_end"),
            "activation_paid": user.get("activation_paid"),
            "google_sheets_id": user.get("google_sheets_id"),
            "google_sheets_name": user.get("google_sheets_name"),
            "google_calendar_id": user.get("google_calendar_id"),
            "google_calendar_name": user.get("google_calendar_name"),
            "google_drive_folder_id": user.get("google_drive_folder_id"),
            "telegram_id": user.get("telegram_id"),
            "onboarding_completed": user.get("onboarding_completed"),
        },
    }


@router.get("/status")
async def get_onboarding_status(auth_user: AuthUser = Depends(get_current_auth_user)):
    user = _get_user_for_auth(auth_user)
    payload = _status_payload(user)
    if payload["completed"] and not user.get("onboarding_completed"):
        get_supabase_client().table("users").update(
            {"onboarding_completed": True, "updated_at": _now_iso()}
        ).eq("id", user["id"]).execute()
        user["onboarding_completed"] = True
        payload = _status_payload(user)
    return payload


@router.patch("/account")
async def update_account(
    payload: dict[str, Any],
    auth_user: AuthUser = Depends(get_current_auth_user),
):
    user = _get_user_for_auth(auth_user)
    update_data: dict[str, Any] = {}
    if "name" in payload:
        update_data["name"] = str(payload.get("name") or "").strip()[:120] or None
    if "phone" in payload:
        update_data["phone"] = str(payload.get("phone") or "").strip()[:40] or None

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No supported account fields provided.",
        )

    update_data["updated_at"] = _now_iso()
    result = (
        get_supabase_client()
        .table("users")
        .update(update_data)
        .eq("id", user["id"])
        .execute()
    )
    updated = result.data[0] if result.data else {**user, **update_data}
    return {"profile": updated}
```

- [ ] **Step 4: Mount the router**

Modify `oze-agent/api/main.py`:

```python
from api.routes.onboarding import router as onboarding_router
```

and add after dashboard router:

```python
app.include_router(onboarding_router, prefix="/api/onboarding")
```

- [ ] **Step 5: Verify GREEN**

Run:

```bash
cd oze-agent && PYTHONPATH=. pytest tests/test_onboarding_api.py::test_onboarding_status_next_step_payment tests/test_onboarding_api.py::test_update_account_allows_only_system_fields tests/test_api_auth.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add oze-agent/api/routes/onboarding.py oze-agent/api/main.py oze-agent/tests/test_onboarding_api.py
git commit -m "feat(api): add web onboarding status"
```

---

### Task 2: Authenticated Google OAuth Boundary

**Files:**
- Modify: `oze-agent/api/routes/onboarding.py`
- Modify: `oze-agent/api/routes/google_oauth.py`
- Modify: `oze-agent/bot/config.py`
- Modify: `oze-agent/tests/test_onboarding_api.py`

- [ ] **Step 1: Add failing tests for signed OAuth state**

Append to `oze-agent/tests/test_onboarding_api.py`:

```python
@pytest.mark.asyncio
async def test_google_oauth_url_uses_authenticated_user(monkeypatch):
    from api.auth import AuthUser
    from api.routes import onboarding

    fake = _FakeSupabase([
        {
            "id": "user-1",
            "auth_user_id": "auth-1",
            "email": "jan@example.pl",
            "subscription_status": "active",
            "activation_paid": True,
        }
    ])
    monkeypatch.setattr(onboarding, "get_supabase_client", lambda: fake)
    monkeypatch.setattr(onboarding, "build_oauth_url", lambda user_id, state=None: f"https://google.test?state={state}&user={user_id}")

    result = await onboarding.start_google_oauth(
        AuthUser(user_id="auth-1", email="jan@example.pl", claims={})
    )

    assert result["url"].startswith("https://google.test")
    assert "user=user-1" in result["url"]
    assert "auth-1" not in result["url"]


def test_oauth_state_roundtrip(monkeypatch):
    from api.routes import onboarding

    monkeypatch.setattr(onboarding.Config, "GOOGLE_OAUTH_STATE_SECRET", "state-secret", raising=False)
    state = onboarding.encode_oauth_state("user-1")

    assert onboarding.decode_oauth_state(state) == "user-1"
```

- [ ] **Step 2: Verify RED**

Run:

```bash
cd oze-agent && PYTHONPATH=. pytest tests/test_onboarding_api.py::test_google_oauth_url_uses_authenticated_user tests/test_onboarding_api.py::test_oauth_state_roundtrip -q
```

Expected: FAIL because `start_google_oauth` and state helpers do not exist.

- [ ] **Step 3: Add config field**

Modify `oze-agent/bot/config.py`:

```python
SECRET_ENV_NAMES = (
    ...
    "GOOGLE_OAUTH_STATE_SECRET",
    ...
)
```

and inside `Config` security section:

```python
    GOOGLE_OAUTH_STATE_SECRET = _clean_env("GOOGLE_OAUTH_STATE_SECRET")
```

- [ ] **Step 4: Add state helpers and OAuth URL endpoint**

Modify `oze-agent/api/routes/onboarding.py` imports:

```python
import base64
import hashlib
import hmac
import json

from bot.config import Config
from shared.google_auth import build_oauth_url
```

Add helpers:

```python
def _oauth_state_secret() -> str:
    secret = Config.GOOGLE_OAUTH_STATE_SECRET or Config.BILLING_INTERNAL_SECRET
    if not secret:
        raise HTTPException(status_code=500, detail="OAuth state secret is not configured.")
    return secret


def encode_oauth_state(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "iat": int(datetime.now(tz=timezone.utc).timestamp()),
    }
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    body = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    sig = hmac.new(_oauth_state_secret().encode("utf-8"), body.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def decode_oauth_state(state: str, max_age_seconds: int = 900) -> str:
    try:
        body, sig = state.split(".", 1)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid OAuth state.") from exc
    expected = hmac.new(_oauth_state_secret().encode("utf-8"), body.encode("ascii"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        raise HTTPException(status_code=400, detail="Invalid OAuth state signature.")
    padded = body + "=" * (-len(body) % 4)
    payload = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")))
    iat = int(payload.get("iat", 0))
    now = int(datetime.now(tz=timezone.utc).timestamp())
    if now - iat > max_age_seconds:
        raise HTTPException(status_code=400, detail="OAuth state expired.")
    user_id = payload.get("user_id")
    if not isinstance(user_id, str) or not user_id:
        raise HTTPException(status_code=400, detail="OAuth state missing user.")
    return user_id
```

Add endpoint:

```python
@router.post("/google/oauth-url")
async def start_google_oauth(auth_user: AuthUser = Depends(get_current_auth_user)):
    user = _get_user_for_auth(auth_user)
    if not _has_payment(user):
        raise HTTPException(status_code=402, detail="Payment is required before Google OAuth.")
    state = encode_oauth_state(user["id"])
    return {"url": build_oauth_url(user["id"], state=state)}
```

- [ ] **Step 5: Let Google auth helper accept state override**

Modify `oze-agent/shared/google_auth.py` signature and state:

```python
def build_oauth_url(user_id: str, state: str | None = None) -> str:
```

and inside `OAuth2Session(...)`:

```python
        state=state or user_id,
```

- [ ] **Step 6: Decode state in callback and redirect to web**

Modify `oze-agent/api/routes/google_oauth.py` imports:

```python
from fastapi.responses import RedirectResponse
from api.routes.onboarding import decode_oauth_state
from bot.config import Config
```

Replace `google_callback` body with:

```python
@router.get("/google/callback")
async def google_callback(code: str, state: str):
    try:
        user_id = decode_oauth_state(state)
        user = handle_oauth_callback(code=code, state=user_id)
        target = (Config.DASHBOARD_URL or "http://localhost:3000").rstrip("/")
        if not user:
            logger.error("google_callback: handle_oauth_callback returned None for user=%s", user_id)
            return RedirectResponse(f"{target}/onboarding/google?error=oauth_failed", status_code=302)
        return RedirectResponse(f"{target}/onboarding/google/sukces", status_code=302)
    except Exception as e:
        logger.error("google_callback: %s", e)
        target = (Config.DASHBOARD_URL or "http://localhost:3000").rstrip("/")
        return RedirectResponse(f"{target}/onboarding/google?error=oauth_failed", status_code=302)
```

- [ ] **Step 7: Verify GREEN**

Run:

```bash
cd oze-agent && PYTHONPATH=. pytest tests/test_onboarding_api.py::test_google_oauth_url_uses_authenticated_user tests/test_onboarding_api.py::test_oauth_state_roundtrip tests/test_api_auth.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add oze-agent/api/routes/onboarding.py oze-agent/api/routes/google_oauth.py oze-agent/shared/google_auth.py oze-agent/bot/config.py oze-agent/tests/test_onboarding_api.py
git commit -m "feat(api): add authenticated google oauth start"
```

---

### Task 3: Google Resource Creation Endpoint

**Files:**
- Modify: `oze-agent/api/routes/onboarding.py`
- Modify: `oze-agent/tests/test_onboarding_api.py`

- [ ] **Step 1: Add failing test for idempotent resource creation**

Append to `oze-agent/tests/test_onboarding_api.py`:

```python
@pytest.mark.asyncio
async def test_create_google_resources_only_creates_missing(monkeypatch):
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
            "google_sheets_name": "Existing Sheet",
            "google_calendar_id": None,
            "google_calendar_name": None,
            "google_drive_folder_id": None,
        }
    ])
    monkeypatch.setattr(onboarding, "get_supabase_client", lambda: fake)
    monkeypatch.setattr(onboarding, "create_spreadsheet", pytest.fail, raising=False)
    monkeypatch.setattr(onboarding, "create_calendar", lambda user_id, name: "calendar-1", raising=False)
    monkeypatch.setattr(onboarding, "create_root_folder", lambda user_id: "drive-1", raising=False)

    result = await onboarding.create_google_resources(
        {"calendarName": "Agent-OZE Calendar"},
        AuthUser(user_id="auth-1", email="jan@example.pl", claims={}),
    )

    assert result["resources"]["sheetsId"] == "existing-sheet"
    assert result["resources"]["calendarId"] == "calendar-1"
    assert result["resources"]["driveFolderId"] == "drive-1"
    assert fake.last_query.updated["google_calendar_id"] == "calendar-1"
```

- [ ] **Step 2: Verify RED**

Run:

```bash
cd oze-agent && PYTHONPATH=. pytest tests/test_onboarding_api.py::test_create_google_resources_only_creates_missing -q
```

Expected: FAIL because `create_google_resources` does not exist.

- [ ] **Step 3: Add imports and helper**

Modify `oze-agent/api/routes/onboarding.py` imports:

```python
from shared.google_calendar import create_calendar
from shared.google_drive import create_root_folder
from shared.google_sheets import create_spreadsheet
```

Add helper:

```python
def _resource_name(payload: dict[str, Any], key: str, fallback: str) -> str:
    value = str(payload.get(key) or "").strip()
    return value[:120] if value else fallback
```

- [ ] **Step 4: Add resource endpoint**

Add to `oze-agent/api/routes/onboarding.py`:

```python
@router.post("/resources")
async def create_google_resources(
    payload: dict[str, Any],
    auth_user: AuthUser = Depends(get_current_auth_user),
):
    user = _get_user_for_auth(auth_user)
    if not _has_payment(user):
        raise HTTPException(status_code=402, detail="Payment is required before resource creation.")
    if not _has_google_tokens(user):
        raise HTTPException(status_code=409, detail="Google OAuth is required before resource creation.")

    label = user.get("name") or user.get("email") or user["id"]
    update_data: dict[str, Any] = {}
    sheets_id = user.get("google_sheets_id")
    calendar_id = user.get("google_calendar_id")
    drive_folder_id = user.get("google_drive_folder_id")

    if not sheets_id:
        sheets_name = _resource_name(payload, "sheetsName", f"Agent-OZE CRM - {label}")
        maybe_sheets_id = create_spreadsheet(user["id"], sheets_name)
        sheets_id = await maybe_sheets_id if hasattr(maybe_sheets_id, "__await__") else maybe_sheets_id
        if not sheets_id:
            raise HTTPException(status_code=502, detail="Could not create Google Sheets resource.")
        update_data["google_sheets_id"] = sheets_id
        update_data["google_sheets_name"] = sheets_name

    if not calendar_id:
        calendar_name = _resource_name(payload, "calendarName", f"Agent-OZE - {label}")
        maybe_calendar_id = create_calendar(user["id"], calendar_name)
        calendar_id = await maybe_calendar_id if hasattr(maybe_calendar_id, "__await__") else maybe_calendar_id
        if not calendar_id:
            raise HTTPException(status_code=502, detail="Could not create Google Calendar resource.")
        update_data["google_calendar_id"] = calendar_id
        update_data["google_calendar_name"] = calendar_name

    if not drive_folder_id:
        maybe_drive_id = create_root_folder(user["id"])
        drive_folder_id = await maybe_drive_id if hasattr(maybe_drive_id, "__await__") else maybe_drive_id
        if not drive_folder_id:
            raise HTTPException(status_code=502, detail="Could not create Google Drive resource.")
        update_data["google_drive_folder_id"] = drive_folder_id

    if update_data:
        update_data["updated_at"] = _now_iso()
        get_supabase_client().table("users").update(update_data).eq("id", user["id"]).execute()
        user.update(update_data)

    return {
        "resources": {
            "sheetsId": sheets_id,
            "calendarId": calendar_id,
            "driveFolderId": drive_folder_id,
        },
        "nextStep": _next_step(user),
    }
```

- [ ] **Step 5: Verify GREEN**

Run:

```bash
cd oze-agent && PYTHONPATH=. pytest tests/test_onboarding_api.py::test_create_google_resources_only_creates_missing -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add oze-agent/api/routes/onboarding.py oze-agent/tests/test_onboarding_api.py
git commit -m "feat(api): add google resource onboarding"
```

---

### Task 4: Telegram Pairing API

**Files:**
- Modify: `oze-agent/api/routes/onboarding.py`
- Modify: `oze-agent/tests/test_onboarding_api.py`

- [ ] **Step 1: Add failing tests for pairing code and status**

Append to `oze-agent/tests/test_onboarding_api.py`:

```python
@pytest.mark.asyncio
async def test_generate_telegram_code_sets_expiry(monkeypatch):
    from api.auth import AuthUser
    from api.routes import onboarding

    fake = _FakeSupabase([
        {
            "id": "user-1",
            "auth_user_id": "auth-1",
            "email": "jan@example.pl",
            "subscription_status": "active",
            "activation_paid": True,
            "google_refresh_token": "encrypted",
            "google_sheets_id": "sheet-1",
            "google_calendar_id": "cal-1",
            "google_drive_folder_id": "drive-1",
            "telegram_id": None,
        }
    ])
    monkeypatch.setattr(onboarding, "get_supabase_client", lambda: fake)
    monkeypatch.setattr(onboarding.secrets, "randbelow", lambda upper: 12345)

    result = await onboarding.generate_telegram_code(
        AuthUser(user_id="auth-1", email="jan@example.pl", claims={})
    )

    assert result["code"] == "112345"
    assert result["paired"] is False
    assert fake.last_query.updated["telegram_link_code"] == "112345"
    assert fake.last_query.updated["telegram_link_code_expires"] is not None


@pytest.mark.asyncio
async def test_telegram_status_completed_when_telegram_id_exists(monkeypatch):
    from api.auth import AuthUser
    from api.routes import onboarding

    fake = _FakeSupabase([
        {
            "id": "user-1",
            "auth_user_id": "auth-1",
            "telegram_id": 123456,
            "telegram_link_code": None,
            "telegram_link_code_expires": None,
        }
    ])
    monkeypatch.setattr(onboarding, "get_supabase_client", lambda: fake)

    result = await onboarding.get_telegram_status(
        AuthUser(user_id="auth-1", email="jan@example.pl", claims={})
    )

    assert result["paired"] is True
    assert result["telegramId"] == 123456
```

- [ ] **Step 2: Verify RED**

Run:

```bash
cd oze-agent && PYTHONPATH=. pytest tests/test_onboarding_api.py::test_generate_telegram_code_sets_expiry tests/test_onboarding_api.py::test_telegram_status_completed_when_telegram_id_exists -q
```

Expected: FAIL because pairing endpoints do not exist.

- [ ] **Step 3: Add import**

Modify `oze-agent/api/routes/onboarding.py`:

```python
import secrets
```

- [ ] **Step 4: Add pairing endpoints**

Add to `oze-agent/api/routes/onboarding.py`:

```python
def _telegram_code() -> str:
    return f"{100000 + secrets.randbelow(900000):06d}"


@router.post("/telegram-code")
async def generate_telegram_code(auth_user: AuthUser = Depends(get_current_auth_user)):
    user = _get_user_for_auth(auth_user)
    if not _has_payment(user) or not _has_google_tokens(user) or not _has_resources(user):
        raise HTTPException(status_code=409, detail="Complete payment and Google setup before Telegram pairing.")
    if user.get("telegram_id"):
        return {"paired": True, "telegramId": user["telegram_id"], "code": None, "expiresAt": None}

    code = _telegram_code()
    expires_at = datetime.now(tz=timezone.utc) + timedelta(minutes=15)
    get_supabase_client().table("users").update(
        {
            "telegram_link_code": code,
            "telegram_link_code_expires": expires_at.isoformat(),
            "updated_at": _now_iso(),
        }
    ).eq("id", user["id"]).execute()
    return {"paired": False, "telegramId": None, "code": code, "expiresAt": expires_at.isoformat()}


@router.get("/telegram-status")
async def get_telegram_status(auth_user: AuthUser = Depends(get_current_auth_user)):
    user = _get_user_for_auth(auth_user)
    return {
        "paired": bool(user.get("telegram_id")),
        "telegramId": user.get("telegram_id"),
        "code": None if user.get("telegram_id") else user.get("telegram_link_code"),
        "expiresAt": None if user.get("telegram_id") else user.get("telegram_link_code_expires"),
    }
```

- [ ] **Step 5: Verify GREEN**

Run:

```bash
cd oze-agent && PYTHONPATH=. pytest tests/test_onboarding_api.py::test_generate_telegram_code_sets_expiry tests/test_onboarding_api.py::test_telegram_status_completed_when_telegram_id_exists -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add oze-agent/api/routes/onboarding.py oze-agent/tests/test_onboarding_api.py
git commit -m "feat(api): add telegram pairing endpoints"
```

---

### Task 5: Next.js Onboarding API Helpers And Actions

**Files:**
- Create: `web/lib/api/onboarding.ts`
- Modify: `web/app/onboarding/actions.ts`
- Modify: `web/scripts/check-web-invariants.mjs`

- [ ] **Step 1: Add failing web invariant for onboarding helper and no Przelewy24**

Append to `web/scripts/check-web-invariants.mjs`:

```javascript
const onboardingHelper = read("lib/api/onboarding.ts");
assert.match(onboardingHelper, /getOnboardingStatus/, "Web must have onboarding status helper.");
assert.match(onboardingHelper, /startGoogleOAuth/, "Web must have Google OAuth helper.");
assert.match(onboardingHelper, /createGoogleResources/, "Web must have resource creation helper.");
assert.match(onboardingHelper, /generateTelegramCode/, "Web must have Telegram code helper.");
assert.doesNotMatch(appSource, /Przelewy24/i, "Web UI must not mention Przelewy24.");
```

- [ ] **Step 2: Verify RED**

Run:

```bash
cd web && npm run test:invariants
```

Expected: FAIL because `web/lib/api/onboarding.ts` does not exist.

- [ ] **Step 3: Create onboarding helper**

Create `web/lib/api/onboarding.ts`:

```typescript
import "server-only";

import { getCurrentAccount } from "@/lib/api/account";

export type OnboardingStatus = {
  fetchedAt: string;
  nextStep: string;
  completed: boolean;
  steps: {
    payment: boolean;
    google: boolean;
    resources: boolean;
    telegram: boolean;
  };
  profile: Record<string, unknown> | null;
};

export type TelegramPairingStatus = {
  paired: boolean;
  telegramId: number | null;
  code: string | null;
  expiresAt: string | null;
};

function apiBaseUrl() {
  return (
    process.env.FASTAPI_INTERNAL_BASE_URL ??
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    ""
  ).replace(/\/$/, "");
}

async function authedFetch(path: string, init: RequestInit = {}) {
  const account = await getCurrentAccount();
  const baseUrl = apiBaseUrl();
  if (!account.authenticated || !account.accessToken) {
    throw new Error("Brak aktywnej sesji.");
  }
  if (!baseUrl) {
    throw new Error("Brak konfiguracji FASTAPI_INTERNAL_BASE_URL.");
  }
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${account.accessToken}`,
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`API error ${response.status}`);
  }
  return response;
}

export async function getOnboardingStatus(): Promise<OnboardingStatus | null> {
  try {
    const response = await authedFetch("/api/onboarding/status");
    return (await response.json()) as OnboardingStatus;
  } catch {
    return null;
  }
}

export async function startGoogleOAuth(): Promise<string> {
  const response = await authedFetch("/api/onboarding/google/oauth-url", {
    method: "POST",
    body: "{}",
  });
  const payload = (await response.json()) as { url: string };
  return payload.url;
}

export async function createGoogleResources(input: {
  sheetsName?: string;
  calendarName?: string;
}) {
  const response = await authedFetch("/api/onboarding/resources", {
    method: "POST",
    body: JSON.stringify(input),
  });
  return response.json();
}

export async function generateTelegramCode(): Promise<TelegramPairingStatus> {
  const response = await authedFetch("/api/onboarding/telegram-code", {
    method: "POST",
    body: "{}",
  });
  return (await response.json()) as TelegramPairingStatus;
}

export async function getTelegramStatus(): Promise<TelegramPairingStatus | null> {
  try {
    const response = await authedFetch("/api/onboarding/telegram-status");
    return (await response.json()) as TelegramPairingStatus;
  } catch {
    return null;
  }
}

export async function updateAccount(input: { name?: string; phone?: string }) {
  const response = await authedFetch("/api/onboarding/account", {
    method: "PATCH",
    body: JSON.stringify(input),
  });
  return response.json();
}
```

- [ ] **Step 4: Add server actions**

Modify `web/app/onboarding/actions.ts` imports:

```typescript
import {
  createGoogleResources,
  generateTelegramCode,
  startGoogleOAuth,
  updateAccount,
} from "@/lib/api/onboarding";
```

Append actions:

```typescript
export async function startGoogleOAuthAction() {
  const url = await startGoogleOAuth();
  redirect(url);
}

export async function createGoogleResourcesAction(formData: FormData) {
  await createGoogleResources({
    sheetsName: String(formData.get("sheetsName") ?? ""),
    calendarName: String(formData.get("calendarName") ?? ""),
  });
  redirect("/onboarding/telegram");
}

export async function generateTelegramCodeAction() {
  await generateTelegramCode();
  redirect("/onboarding/telegram");
}

export async function updateAccountAction(formData: FormData) {
  await updateAccount({
    name: String(formData.get("name") ?? ""),
    phone: String(formData.get("phone") ?? ""),
  });
  redirect("/ustawienia?saved=1");
}
```

- [ ] **Step 5: Verify GREEN**

Run:

```bash
cd web && npm run test:invariants && npm run lint
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add web/lib/api/onboarding.ts web/app/onboarding/actions.ts web/scripts/check-web-invariants.mjs
git commit -m "feat(web): add onboarding api helpers"
```

---

### Task 6: Onboarding Screens For Google, Resources, And Telegram

**Files:**
- Create: `web/app/onboarding/google/page.tsx`
- Create: `web/app/onboarding/google/sukces/page.tsx`
- Create: `web/app/onboarding/zasoby/page.tsx`
- Create: `web/app/onboarding/telegram/page.tsx`
- Modify: `web/app/onboarding/sukces/page.tsx`
- Modify: `web/scripts/check-web-invariants.mjs`

- [ ] **Step 1: Add failing invariant for onboarding routes**

Append to `web/scripts/check-web-invariants.mjs`:

```javascript
for (const route of [
  "app/onboarding/google/page.tsx",
  "app/onboarding/google/sukces/page.tsx",
  "app/onboarding/zasoby/page.tsx",
  "app/onboarding/telegram/page.tsx",
]) {
  assert.match(read(route), /onboarding|Google|Telegram|Sheets|Calendar|Drive/i, `${route} must implement onboarding UI.`);
}
```

- [ ] **Step 2: Verify RED**

Run:

```bash
cd web && npm run test:invariants
```

Expected: FAIL because onboarding routes are missing.

- [ ] **Step 3: Create Google step**

Create `web/app/onboarding/google/page.tsx`:

```tsx
import Link from "next/link";
import { startGoogleOAuthAction } from "@/app/onboarding/actions";
import { getOnboardingStatus } from "@/lib/api/onboarding";

export default async function GoogleOnboardingPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const params = await searchParams;
  const status = await getOnboardingStatus();
  const connected = status?.steps.google;

  return (
    <main className="min-h-screen bg-[#050607] px-5 py-8 text-zinc-100">
      <section className="mx-auto max-w-3xl">
        <p className="text-xs font-semibold uppercase text-[#3DFF7A]">Krok 3</p>
        <h1 className="mt-3 text-4xl font-semibold text-white">Połącz Google.</h1>
        <p className="mt-4 text-sm leading-6 text-zinc-300">
          Web app czyta CRM z Google Sheets i Calendar. Edycja klientów i spotkań zostaje w Google.
        </p>
        {params.error ? (
          <p className="mt-5 rounded-[8px] border border-red-400/20 bg-red-400/10 px-4 py-3 text-sm">
            Autoryzacja Google nie powiodła się. Spróbuj ponownie.
          </p>
        ) : null}
        {connected ? (
          <Link href="/onboarding/zasoby" className="mt-6 inline-flex rounded-full bg-[#3DFF7A] px-5 py-3 text-sm font-semibold text-black">
            Przejdź do zasobów
          </Link>
        ) : (
          <form action={startGoogleOAuthAction} className="mt-6">
            <button className="rounded-full bg-[#3DFF7A] px-5 py-3 text-sm font-semibold text-black">
              Połącz konto Google
            </button>
          </form>
        )}
      </section>
    </main>
  );
}
```

- [ ] **Step 4: Create Google success page**

Create `web/app/onboarding/google/sukces/page.tsx`:

```tsx
import Link from "next/link";

export default function GoogleSuccessPage() {
  return (
    <main className="min-h-screen bg-[#050607] px-5 py-8 text-zinc-100">
      <section className="mx-auto max-w-2xl">
        <p className="text-xs font-semibold uppercase text-[#3DFF7A]">Google</p>
        <h1 className="mt-3 text-4xl font-semibold text-white">Google jest połączony.</h1>
        <p className="mt-4 text-sm leading-6 text-zinc-300">
          Teraz utworzymy lub podłączymy zasoby: Sheets, Calendar i Drive.
        </p>
        <Link href="/onboarding/zasoby" className="mt-6 inline-flex rounded-full bg-[#3DFF7A] px-5 py-3 text-sm font-semibold text-black">
          Dalej
        </Link>
      </section>
    </main>
  );
}
```

- [ ] **Step 5: Create resources page**

Create `web/app/onboarding/zasoby/page.tsx`:

```tsx
import { createGoogleResourcesAction } from "@/app/onboarding/actions";
import { getOnboardingStatus } from "@/lib/api/onboarding";

export default async function ResourcesPage() {
  const status = await getOnboardingStatus();
  const profile = status?.profile as Record<string, string | null> | null;
  const defaultName = String(profile?.name ?? profile?.email ?? "Agent-OZE");

  return (
    <main className="min-h-screen bg-[#050607] px-5 py-8 text-zinc-100">
      <section className="mx-auto max-w-3xl">
        <p className="text-xs font-semibold uppercase text-[#3DFF7A]">Krok 4</p>
        <h1 className="mt-3 text-4xl font-semibold text-white">Zasoby Google.</h1>
        <p className="mt-4 text-sm leading-6 text-zinc-300">
          Tworzymy brakujące zasoby systemowe. Dane CRM nadal edytujesz w Sheets i Calendar.
        </p>
        <form action={createGoogleResourcesAction} className="mt-6 grid gap-4">
          <label className="text-sm text-zinc-300">
            Nazwa arkusza Sheets
            <input name="sheetsName" defaultValue={`Agent-OZE CRM - ${defaultName}`} className="mt-2 w-full rounded-[8px] border border-white/10 bg-black/30 px-4 py-3 text-white" />
          </label>
          <label className="text-sm text-zinc-300">
            Nazwa kalendarza
            <input name="calendarName" defaultValue={`Agent-OZE - ${defaultName}`} className="mt-2 w-full rounded-[8px] border border-white/10 bg-black/30 px-4 py-3 text-white" />
          </label>
          <button className="w-fit rounded-full bg-[#3DFF7A] px-5 py-3 text-sm font-semibold text-black">
            Utwórz brakujące zasoby
          </button>
        </form>
      </section>
    </main>
  );
}
```

- [ ] **Step 6: Create Telegram pairing page**

Create `web/app/onboarding/telegram/page.tsx`:

```tsx
import Link from "next/link";
import { generateTelegramCodeAction } from "@/app/onboarding/actions";
import { getOnboardingStatus, getTelegramStatus } from "@/lib/api/onboarding";

export default async function TelegramOnboardingPage() {
  const [status, pairing] = await Promise.all([
    getOnboardingStatus(),
    getTelegramStatus(),
  ]);
  const paired = pairing?.paired || status?.steps.telegram;

  return (
    <main className="min-h-screen bg-[#050607] px-5 py-8 text-zinc-100">
      <section className="mx-auto max-w-3xl">
        <p className="text-xs font-semibold uppercase text-[#3DFF7A]">Krok 5</p>
        <h1 className="mt-3 text-4xl font-semibold text-white">Połącz Telegrama.</h1>
        <p className="mt-4 text-sm leading-6 text-zinc-300">
          CRM dalej zmieniasz przez Telegrama po potwierdzeniu albo bezpośrednio w Google.
        </p>
        {paired ? (
          <div className="mt-6 rounded-[8px] border border-[#3DFF7A]/30 bg-[#3DFF7A]/10 p-5">
            <p className="text-sm font-semibold text-white">Telegram połączony.</p>
            <Link href="/dashboard" className="mt-4 inline-flex rounded-full bg-[#3DFF7A] px-5 py-3 text-sm font-semibold text-black">
              Przejdź do dashboardu
            </Link>
          </div>
        ) : (
          <div className="mt-6 rounded-[8px] border border-white/10 bg-white/[0.04] p-5">
            <p className="text-sm text-zinc-300">Kod parowania</p>
            <p className="mt-3 text-5xl font-semibold tracking-[0.2em] text-white">{pairing?.code ?? "------"}</p>
            <p className="mt-3 text-sm text-zinc-400">Kod jest krótkotrwały. Po wpisaniu w Telegramie ta strona pokaże status po odświeżeniu.</p>
            <form action={generateTelegramCodeAction} className="mt-5">
              <button className="rounded-full border border-[#3DFF7A]/40 px-5 py-3 text-sm font-semibold text-[#3DFF7A]">
                Wygeneruj nowy kod
              </button>
            </form>
          </div>
        )}
      </section>
    </main>
  );
}
```

- [ ] **Step 7: Update Stripe success CTA**

Modify `web/app/onboarding/sukces/page.tsx` so the primary link points to `/onboarding/google` and the page mentions the next step is Google.

- [ ] **Step 8: Verify GREEN**

Run:

```bash
cd web && npm run test:invariants && npm run lint && npm run build
```

Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add web/app/onboarding web/scripts/check-web-invariants.mjs
git commit -m "feat(web): add onboarding completion screens"
```

---

### Task 7: Live CRM Source States

**Files:**
- Modify: `web/lib/crm/types.ts`
- Modify: `web/lib/crm/mock-data.ts`
- Modify: `web/lib/crm/adapters.ts`
- Modify: `web/app/(app)/dashboard/page.tsx`
- Modify: `web/app/(app)/klienci/page.tsx`
- Modify: `web/app/(app)/kalendarz/page.tsx`
- Modify: `web/scripts/check-web-invariants.mjs`

- [ ] **Step 1: Add failing invariant for CRM source states**

Append to `web/scripts/check-web-invariants.mjs`:

```javascript
const crmTypes = read("lib/crm/types.ts");
const crmAdapters = read("lib/crm/adapters.ts");
assert.match(crmTypes, /CrmSourceState/, "CRM DTOs must include source state.");
assert.match(crmAdapters, /unavailable/, "CRM adapter must expose unavailable state.");
assert.match(crmAdapters, /demo/, "CRM adapter must expose demo state.");
assert.match(crmAdapters, /completed/, "CRM adapter must consider onboarding completion before demo fallback.");
```

- [ ] **Step 2: Verify RED**

Run:

```bash
cd web && npm run test:invariants
```

Expected: FAIL because CRM source state is not modeled.

- [ ] **Step 3: Add CRM source type**

Modify `web/lib/crm/types.ts`:

```typescript
export type CrmSourceState = "live" | "demo" | "unavailable";
```

and update `CrmDashboardData`:

```typescript
export type CrmDashboardData = {
  fetchedAt: string;
  source: CrmSourceState;
  sourceMessage: string;
  clients: CrmClient[];
  events: CrmEvent[];
};
```

- [ ] **Step 4: Mark mock data as demo**

Modify `web/lib/crm/mock-data.ts` returned object:

```typescript
export const mockCrmDashboardData: CrmDashboardData = {
  fetchedAt: new Date().toISOString(),
  source: "demo",
  sourceMessage: "Dane demo. Po onboardingu panel czyta CRM z Google Sheets i Calendar.",
  clients: [...],
  events: [...],
};
```

- [ ] **Step 5: Change adapter fallback rules**

Modify `web/lib/crm/adapters.ts`:

```typescript
function unavailableData(message: string): CrmDashboardData {
  return {
    fetchedAt: new Date().toISOString(),
    source: "unavailable",
    sourceMessage: message,
    clients: [],
    events: [],
  };
}
```

and in `getCrmDashboardData()` replace fallback behavior:

```typescript
  if (!account.authenticated || !account.accessToken || !baseUrl) {
    return mockCrmDashboardData;
  }

  const completed = Boolean(account.profile?.onboarding_completed);

  const response = await fetch(`${baseUrl}/api/dashboard/crm`, {
    headers: {
      Authorization: `Bearer ${account.accessToken}`,
      "X-OZE-CRM-Sources": `${CRM_SOURCES.clients},${CRM_SOURCES.events}`,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    return completed
      ? unavailableData("Nie udało się pobrać danych z Google. Otwórz Sheets lub Calendar bezpośrednio.")
      : mockCrmDashboardData;
  }

  const data = (await response.json()) as CrmDashboardData;
  return {
    ...data,
    source: data.source ?? "live",
    sourceMessage: data.sourceMessage ?? "Dane z Google Sheets i Calendar.",
  };
```

- [ ] **Step 6: Render source state in CRM pages**

In each of `web/app/(app)/dashboard/page.tsx`, `web/app/(app)/klienci/page.tsx`, and `web/app/(app)/kalendarz/page.tsx`, render this near the top:

```tsx
<p className="mt-3 rounded-[8px] border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-zinc-300">
  {data.source === "live" ? "Źródło: Google Sheets i Calendar." : data.sourceMessage}
</p>
```

- [ ] **Step 7: Verify GREEN**

Run:

```bash
cd web && npm run test:invariants && npm run lint && npm run build
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add web/lib/crm web/app/'(app)'/dashboard/page.tsx web/app/'(app)'/klienci/page.tsx web/app/'(app)'/kalendarz/page.tsx web/scripts/check-web-invariants.mjs
git commit -m "feat(web): expose crm source states"
```

---

### Task 8: Functional Settings Page For Account Data Only

**Files:**
- Modify: `web/app/(app)/ustawienia/page.tsx`
- Modify: `web/app/onboarding/actions.ts`
- Modify: `web/scripts/check-web-invariants.mjs`

- [ ] **Step 1: Add failing invariant for account-only settings**

Append to `web/scripts/check-web-invariants.mjs`:

```javascript
const settingsPage = read("app/(app)/ustawienia/page.tsx");
assert.match(settingsPage, /updateAccountAction/, "Settings must use account-only update action.");
assert.doesNotMatch(settingsPage, /google_sheets_id|google_calendar_id|Status klienta|Notatki klienta/, "Settings must not edit CRM fields.");
```

- [ ] **Step 2: Verify RED**

Run:

```bash
cd web && npm run test:invariants
```

Expected: FAIL because settings page does not use account update action.

- [ ] **Step 3: Update settings page**

Modify `web/app/(app)/ustawienia/page.tsx` to include this system-account form:

```tsx
import { updateAccountAction } from "@/app/onboarding/actions";
import { getCurrentAccount } from "@/lib/api/account";

export default async function SettingsPage() {
  const account = await getCurrentAccount();
  const profile = account.profile;

  return (
    <div className="space-y-6">
      <section>
        <p className="text-xs font-semibold uppercase text-[#3DFF7A]">Ustawienia</p>
        <h1 className="mt-2 text-3xl font-semibold text-white">Konto i integracje.</h1>
        <p className="mt-3 text-sm leading-6 text-zinc-400">
          Statusy, notatki, klienci i spotkania zostają w Google Sheets i Calendar. Ten formularz zapisuje tylko dane konta.
        </p>
      </section>

      <form action={updateAccountAction} className="grid max-w-xl gap-4 rounded-[8px] border border-white/10 bg-white/[0.04] p-5">
        <label className="text-sm text-zinc-300">
          Nazwa konta
          <input name="name" defaultValue={profile?.name ?? ""} className="mt-2 w-full rounded-[8px] border border-white/10 bg-black/30 px-4 py-3 text-white" />
        </label>
        <label className="text-sm text-zinc-300">
          Telefon kontaktowy
          <input name="phone" defaultValue={profile?.phone ?? ""} className="mt-2 w-full rounded-[8px] border border-white/10 bg-black/30 px-4 py-3 text-white" />
        </label>
        <button className="w-fit rounded-full bg-[#3DFF7A] px-5 py-3 text-sm font-semibold text-black">
          Zapisz ustawienia konta
        </button>
      </form>
    </div>
  );
}
```

- [ ] **Step 4: Verify GREEN**

Run:

```bash
cd web && npm run test:invariants && npm run lint && npm run build
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add web/app/'(app)'/ustawienia/page.tsx web/app/onboarding/actions.ts web/scripts/check-web-invariants.mjs
git commit -m "feat(web): add account-only settings form"
```

---

### Task 9: Documentation And Environment Sync

**Files:**
- Modify: `web/.env.example`
- Modify: `web/README.md`
- Modify: `docs/CURRENT_STATUS.md`
- Modify: `docs/IMPLEMENTATION_PLAN.md`

- [ ] **Step 1: Update env example**

Add to `web/.env.example` if missing:

```bash
FASTAPI_INTERNAL_BASE_URL=http://localhost:8000
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000
BILLING_INTERNAL_SECRET=
```

- [ ] **Step 2: Update web README routes**

Add to `web/README.md` route list:

```markdown
- `http://localhost:3000/onboarding/google` — Google OAuth step
- `http://localhost:3000/onboarding/zasoby` — Sheets/Calendar/Drive setup
- `http://localhost:3000/onboarding/telegram` — Telegram pairing code
```

Add backend note:

```markdown
Phase 0F/1 onboarding calls FastAPI `/api/onboarding/*` with the Supabase access token. FastAPI resolves `auth_user_id`, writes system setup fields with the service key, and keeps CRM data in Google.
```

- [ ] **Step 3: Update project status docs**

In `docs/CURRENT_STATUS.md`, update the web app track bullet for Phase 0F/Phase 1 to say implementation is now on `feat/web-phase-0c`.

In `docs/IMPLEMENTATION_PLAN.md`, update the web app snapshot table so Phase 0F/Phase 1 are named explicitly:

```markdown
| **0F** Onboarding completion | ✅ code-complete on PR #5, smoke pending | Google OAuth, resource setup, Telegram pairing |
| **Phase 1** Operational web panel | ✅ code-complete on PR #5, rollout pending | live CRM source states, account settings, read-only dashboard hardening |
```

- [ ] **Step 4: Verify docs do not reintroduce Przelewy24**

Run:

```bash
rg -n "Przelewy24" web docs/CURRENT_STATUS.md docs/IMPLEMENTATION_PLAN.md
```

Expected: no web/current-plan references except historical source-of-truth or explicit "out of scope" references outside touched docs.

- [ ] **Step 5: Commit**

```bash
git add web/.env.example web/README.md docs/CURRENT_STATUS.md docs/IMPLEMENTATION_PLAN.md
git commit -m "docs: sync web onboarding phase status"
```

---

### Task 10: Final Verification

**Files:**
- Review all changed files.

- [ ] **Step 1: Run focused backend tests**

Run:

```bash
cd oze-agent && PYTHONPATH=. pytest tests/test_onboarding_api.py tests/test_dashboard_api.py tests/test_billing.py tests/test_api_auth.py -q
```

Expected: PASS.

- [ ] **Step 2: Run full backend suite**

Run:

```bash
cd oze-agent && PYTHONPATH=. pytest -q
```

Expected: PASS. If environment-only failures occur, capture exact test names and error output.

- [ ] **Step 3: Run web checks**

Run:

```bash
cd web && npm run test:invariants && npm run lint && npm run build
```

Expected: PASS.

- [ ] **Step 4: Inspect worktree**

Run:

```bash
git status --short
git log --oneline -12
```

Expected: only intentional commits on `feat/web-phase-0c`; no untracked implementation files.

- [ ] **Step 5: Use verification-before-completion**

Invoke `superpowers:verification-before-completion` before saying the implementation is complete.

- [ ] **Step 6: Use finishing-a-development-branch**

Invoke `superpowers:finishing-a-development-branch` to push the branch and update the draft PR.

---

## Self-Review

Spec coverage:

- Phase 0D route gates and onboarding model: Task 1 and Task 6.
- Phase 0E live/demo/unavailable CRM states: Task 7.
- Phase 0F Google OAuth/resource setup/Telegram pairing: Tasks 2, 3, 4, 6.
- Phase 1 account state API and settings: Tasks 1, 5, 8.
- Billing continuity: existing Phase 0C remains; Task 6 routes post-Stripe users forward.
- CRM read-only boundary: Tasks 7 and 8 plus invariants in Tasks 5, 7, 8.
- Docs/env sync: Task 9.

Placeholder scan:

- No placeholder markers or unspecified implementation steps remain.
- Each task has a failing test or invariant, a verification command, implementation content, and a commit.

Type consistency:

- Backend route names match frontend helper paths.
- `OnboardingStatus`, `TelegramPairingStatus`, and CRM source fields are introduced before use.
- Account update accepts only `name` and `phone`; no CRM fields are sent from web settings.
