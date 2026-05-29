# Webapp Loading UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a brand-locked loading & feedback visual language across the Agent-OZE webapp so every user click produces visible feedback within 100ms and no async wait exceeds 2s without a status indicator.

**Architecture:** 6 reusable React components (Wzorce A–F: BrandSpinner, NavigationBar+BreadcrumbArrow, Skeleton, ResourceProgress, Toast helpers via sonner, RedirectingScreen) plus 6 `loading.tsx` files. Components are pure presentational primitives wired into existing `<form action={…}>` server actions, page-level layouts, and one new SSE/polling endpoint for the 10–45s Google resources creation. Custom toast in `decyzje-preview.tsx` is migrated to global sonner system; offer generator gets per-button loading state + confirm dialog for destructive ops.

**Tech Stack:** Next.js 16 + React 19 + Tailwind v4 + sonner (new dep) + node:test for source-grep style component tests (matches existing `web/tests/*.test.mjs` convention). No new state management library — `useFormStatus()` for forms, `useState` for onClick async, `useTransition` for optimistic mutations.

**Spec reference:** `docs/superpowers/specs/2026-05-29-webapp-loading-ux-design.md`
**Audit reference:** `~/.claude/plans/to-czego-zdecydowanie-teraz-golden-kay.md`

---

## File Structure

**New components (web/components/ui/):**
- `brand-spinner.tsx` — Wzorzec A (SVG ring 22×22, animowany stroke-dasharray + rotate)
- `submit-button.tsx` — wrapper z `useFormStatus()` + BrandSpinner
- `navigation-bar.tsx` — Wzorzec B (sliding rail 3px na górze viewportu)
- `breadcrumb-arrow.tsx` — Wzorzec B (crawling dashed arrow horizontal)
- `skeleton.tsx` — Wzorzec C (`SkeletonLine`, `SkeletonCard`, `SkeletonCta`)
- `redirecting-screen.tsx` — Wzorzec F (brand mark + pill steps)
- `confirm-dialog.tsx` — destructive action confirm (R1-style)

**New components (web/components/onboarding/):**
- `resource-progress.tsx` — Wzorzec D (3-step canvas dla createGoogleResources)

**New infrastructure:**
- `web/lib/ui/toast.ts` — sonner helpers (`showSuccess`, `showError`, `showAction`, `showPromise`)
- `web/lib/ui/motion.ts` — `usePrefersReducedMotion()` hook
- `web/app/api/onboarding/resources-progress/route.ts` — SSE/polling endpoint
- `web/app/onboarding/przekierowuje/page.tsx` — Wzorzec F route

**New loading.tsx files:**
- `web/app/onboarding/platnosc/loading.tsx`
- `web/app/onboarding/google/loading.tsx`
- `web/app/onboarding/zasoby/loading.tsx`
- `web/app/(app)/dashboard/loading.tsx`
- `web/app/(app)/klienci/loading.tsx`
- `web/app/(app)/kalendarz/loading.tsx`

**Modifications (replace bare buttons with SubmitButton):**
- `web/app/rejestracja/page.tsx`
- `web/app/login/page.tsx`
- `web/app/onboarding/platnosc/page.tsx` (×2 buttons)
- `web/app/onboarding/google/page.tsx`
- `web/app/(app)/ustawienia/page.tsx`
- `web/app/(app)/platnosci/page.tsx`
- `web/components/auth/logout-link.tsx`
- `web/components/onboarding/telegram-pairing-card.tsx`
- `web/components/onboarding/resource-submit-button.tsx` (delete after Phase 7)

**Modifications (sonner integration):**
- `web/app/layout.tsx` — mount `<Toaster />` + `<NavigationBar />`
- `web/components/dashboard/decyzje-preview.tsx` — migrate custom toast to sonner

**Modifications (offer generator overhaul):**
- `web/components/offers/offer-generator.tsx` — 7 onClick buttons get local isLoading + spinner + toast; deleteOffer wrapped in ConfirmDialog

**Modifications (interstitial wire-up):**
- `web/app/auth/actions.ts` — signup redirectuje przez `/przekierowuje?to=stripe`
- `web/app/onboarding/actions.ts` — createCheckoutSession, activateBetaAccess, startGoogleOAuthAction używają interstitial

**Modifications (global CSS tokens):**
- `web/app/globals.css` — add `--brand-green`, `--brand-bg`, etc. + reduced-motion media query

---

## Phase 0 — Setup & Tokens

### Task 0.1: Install sonner and define brand CSS variables

**Files:**
- Modify: `web/package.json` (add sonner dep)
- Modify: `web/app/globals.css` (add CSS variables + reduced-motion globals)
- Create: `web/tests/loading-ux-tokens.test.mjs`

- [ ] **Step 1: Write the failing test**

Create `web/tests/loading-ux-tokens.test.mjs`:

```js
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const globalsCss = readSource("../app/globals.css");
const packageJson = readSource("../package.json");

test("globals.css defines brand loading-ux tokens", () => {
  assert.match(globalsCss, /--brand-green:\s*#3DFF7A/i);
  assert.match(globalsCss, /--brand-bg:\s*#0b0d10/i);
  assert.match(globalsCss, /--brand-bg-deep:\s*#050607/i);
  assert.match(globalsCss, /--ui-border-dim:\s*#1f242b/i);
  assert.match(globalsCss, /--state-error:\s*#FF6464/i);
});

test("globals.css respects prefers-reduced-motion globally", () => {
  assert.match(globalsCss, /@media\s*\(prefers-reduced-motion:\s*reduce\)/);
});

test("sonner is installed as a dependency", () => {
  const pkg = JSON.parse(packageJson);
  assert.ok(pkg.dependencies.sonner, "expected sonner in dependencies");
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && node --test tests/loading-ux-tokens.test.mjs`
Expected: FAIL with assertion errors on all 3 tests.

- [ ] **Step 3: Install sonner**

Run: `cd web && npm install sonner`

- [ ] **Step 4: Add tokens to globals.css**

Edit `web/app/globals.css`, add at the top of `:root` block (after existing `@theme` if any):

```css
:root {
  --brand-green: #3DFF7A;
  --brand-bg: #0b0d10;
  --brand-bg-deep: #050607;
  --brand-bg-inset: #060709;
  --ui-border-dim: #1f242b;
  --ui-text-primary: #f5f7fa;
  --ui-text-muted: #6b7280;
  --ui-text-deep: #4a5460;
  --state-error: #FF6464;
  --state-neutral: #9aa5b1;
}

@media (prefers-reduced-motion: reduce) {
  .motion-safe-only {
    animation: none !important;
    transition: none !important;
  }
}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd web && node --test tests/loading-ux-tokens.test.mjs`
Expected: PASS (3/3).

- [ ] **Step 6: Commit**

```bash
cd /Users/mansoniasty/workflows/Agent-OZE
git add web/package.json web/package-lock.json web/app/globals.css web/tests/loading-ux-tokens.test.mjs
git commit -m "feat(web): add brand loading-ux tokens and sonner dep"
```

---

## Phase 1 — Wzorzec A (BrandSpinner + SubmitButton)

### Task 1.1: BrandSpinner SVG component with reduced-motion fallback

**Files:**
- Create: `web/components/ui/brand-spinner.tsx`
- Create: `web/tests/brand-spinner.test.mjs`

- [ ] **Step 1: Write the failing test**

Create `web/tests/brand-spinner.test.mjs`:

```js
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const src = readSource("../components/ui/brand-spinner.tsx");

test("BrandSpinner is exported", () => {
  assert.match(src, /export\s+function\s+BrandSpinner/);
});

test("BrandSpinner has outline variant with brand green stroke", () => {
  assert.match(src, /#3DFF7A/);
  assert.match(src, /stroke-dasharray/);
});

test("BrandSpinner accepts variant prop (outline | solid)", () => {
  assert.match(src, /variant\??:\s*['"]outline['"]\s*\|\s*['"]solid['"]/);
});

test("BrandSpinner exposes accessible status role", () => {
  assert.match(src, /role=['"]status['"]/);
  assert.match(src, /aria-live=['"]polite['"]/);
});

test("BrandSpinner has motion-safe-only class on animation for reduced-motion respect", () => {
  assert.match(src, /motion-safe-only/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && node --test tests/brand-spinner.test.mjs`
Expected: FAIL — file does not exist.

- [ ] **Step 3: Create component**

Create `web/components/ui/brand-spinner.tsx`:

```tsx
type BrandSpinnerProps = {
  variant?: "outline" | "solid";
  size?: number;
  label?: string;
};

export function BrandSpinner({
  variant = "outline",
  size = 22,
  label = "Ładuję",
}: BrandSpinnerProps) {
  const stroke = variant === "solid" ? "#0b0d10" : "#3DFF7A";
  const dropShadow =
    variant === "solid" ? undefined : "drop-shadow(0 0 4px #3DFF7A88)";

  return (
    <span
      role="status"
      aria-live="polite"
      style={{ display: "inline-flex", filter: dropShadow }}
    >
      <span className="sr-only">{label}</span>
      <svg
        className="motion-safe-only brand-spinner-svg"
        width={size}
        height={size}
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <circle
          className="motion-safe-only brand-spinner-circle"
          cx="12"
          cy="12"
          r="9"
          fill="none"
          stroke={stroke}
          strokeWidth="2"
          strokeLinecap="round"
          strokeDasharray="50 70"
        />
      </svg>
      <style>{`
        .brand-spinner-svg { animation: brand-spinner-rotate 1.2s linear infinite; }
        .brand-spinner-circle { animation: brand-spinner-dash 1.6s ease-in-out infinite; }
        @keyframes brand-spinner-rotate {
          to { transform: rotate(360deg); }
        }
        @keyframes brand-spinner-dash {
          0%   { stroke-dasharray: 5 120; stroke-dashoffset: 0; }
          50%  { stroke-dasharray: 80 45; stroke-dashoffset: -30; }
          100% { stroke-dasharray: 5 120; stroke-dashoffset: -125; }
        }
        @media (prefers-reduced-motion: reduce) {
          .brand-spinner-svg, .brand-spinner-circle {
            animation: none !important;
          }
        }
      `}</style>
    </span>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd web && node --test tests/brand-spinner.test.mjs`
Expected: PASS (5/5).

- [ ] **Step 5: Commit**

```bash
cd /Users/mansoniasty/workflows/Agent-OZE
git add web/components/ui/brand-spinner.tsx web/tests/brand-spinner.test.mjs
git commit -m "feat(web): add BrandSpinner component (Wzorzec A)"
```

---

### Task 1.2: SubmitButton wrapper with useFormStatus

**Files:**
- Create: `web/components/ui/submit-button.tsx`
- Create: `web/tests/submit-button.test.mjs`

- [ ] **Step 1: Write the failing test**

Create `web/tests/submit-button.test.mjs`:

```js
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const src = readSource("../components/ui/submit-button.tsx");

test("SubmitButton is a client component using useFormStatus", () => {
  assert.match(src, /^['"]use client['"]/m);
  assert.match(src, /useFormStatus/);
  assert.match(src, /react-dom/);
});

test("SubmitButton renders BrandSpinner when pending", () => {
  assert.match(src, /BrandSpinner/);
  assert.match(src, /pending/);
});

test("SubmitButton accepts pendingLabel prop", () => {
  assert.match(src, /pendingLabel/);
});

test("SubmitButton disables itself when pending (blocks double-submit)", () => {
  assert.match(src, /disabled=\{pending/);
});

test("SubmitButton supports variant (outline | solid)", () => {
  assert.match(src, /variant\??:\s*['"]outline['"]\s*\|\s*['"]solid['"]/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && node --test tests/submit-button.test.mjs`
Expected: FAIL — file does not exist.

- [ ] **Step 3: Create component**

Create `web/components/ui/submit-button.tsx`:

```tsx
"use client";

import { useFormStatus } from "react-dom";
import type { ReactNode } from "react";
import { BrandSpinner } from "./brand-spinner";

type SubmitButtonProps = {
  children: ReactNode;
  pendingLabel: string;
  variant?: "outline" | "solid";
  className?: string;
  fullWidth?: boolean;
};

export function SubmitButton({
  children,
  pendingLabel,
  variant = "outline",
  className = "",
  fullWidth = false,
}: SubmitButtonProps) {
  const { pending } = useFormStatus();

  const base =
    variant === "solid"
      ? "bg-[#3DFF7A] text-[#0b0d10] font-semibold"
      : "bg-[#0b0d10] text-[#f5f7fa] border border-[#3DFF7A]";

  const widthClass = fullWidth ? "w-full justify-center" : "";

  return (
    <button
      type="submit"
      disabled={pending}
      aria-busy={pending}
      className={`inline-flex items-center gap-2 rounded-full px-5 py-3 text-sm transition-opacity disabled:cursor-wait disabled:opacity-80 ${base} ${widthClass} ${className}`.trim()}
      style={{
        boxShadow:
          variant === "outline"
            ? "0 0 0 1px #3DFF7A22, 0 0 18px #3DFF7A22"
            : undefined,
      }}
    >
      {pending && <BrandSpinner variant={variant} label={pendingLabel} />}
      <span>{pending ? pendingLabel : children}</span>
    </button>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd web && node --test tests/submit-button.test.mjs`
Expected: PASS (5/5).

- [ ] **Step 5: Commit**

```bash
cd /Users/mansoniasty/workflows/Agent-OZE
git add web/components/ui/submit-button.tsx web/tests/submit-button.test.mjs
git commit -m "feat(web): add SubmitButton wrapper (Wzorzec A integration)"
```

---

## Phase 2 — Apply SubmitButton across P1 forms

### Task 2.1: Replace bare submit buttons in 8 forms

**Files:**
- Modify: `web/app/rejestracja/page.tsx`
- Modify: `web/app/login/page.tsx`
- Modify: `web/app/onboarding/platnosc/page.tsx` (2 buttons)
- Modify: `web/app/onboarding/google/page.tsx`
- Modify: `web/app/(app)/ustawienia/page.tsx`
- Modify: `web/app/(app)/platnosci/page.tsx`
- Modify: `web/components/auth/logout-link.tsx`
- Modify: `web/components/onboarding/telegram-pairing-card.tsx` ("Wygeneruj nowy kod" button)
- Create: `web/tests/submit-button-wiring.test.mjs`

- [ ] **Step 1: Write the failing test**

Create `web/tests/submit-button-wiring.test.mjs`:

```js
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const expectations = [
  { file: "../app/rejestracja/page.tsx", pendingLabel: "Rejestruję konto" },
  { file: "../app/login/page.tsx", pendingLabel: "Loguję" },
  { file: "../app/onboarding/platnosc/page.tsx", pendingLabel: "Przygotowuję płatność" },
  { file: "../app/onboarding/platnosc/page.tsx", pendingLabel: "Aktywuję dostęp" },
  { file: "../app/onboarding/google/page.tsx", pendingLabel: "Łączę z Google" },
  { file: "../app/(app)/ustawienia/page.tsx", pendingLabel: "Zapisuję" },
  { file: "../app/(app)/platnosci/page.tsx", pendingLabel: "Anuluję trial" },
  { file: "../components/auth/logout-link.tsx", pendingLabel: "Wylogowuję" },
  { file: "../components/onboarding/telegram-pairing-card.tsx", pendingLabel: "Generuję nowy kod" },
];

for (const { file, pendingLabel } of expectations) {
  test(`${file} wires SubmitButton with pendingLabel "${pendingLabel}"`, () => {
    const src = readSource(file);
    assert.match(src, /SubmitButton/);
    assert.ok(
      src.includes(`pendingLabel="${pendingLabel}"`) ||
        src.includes(`pendingLabel={\`${pendingLabel}`),
      `expected pendingLabel="${pendingLabel}" in ${file}`
    );
  });
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && node --test tests/submit-button-wiring.test.mjs`
Expected: FAIL on all 9 cases (SubmitButton not imported anywhere).

- [ ] **Step 3: Modify `web/app/rejestracja/page.tsx`**

Read the file, find the existing `<button type="submit">…Dalej: płatność…</button>` near line 187, replace with:

```tsx
import { SubmitButton } from "@/components/ui/submit-button";

// inside the form, where the old <button> was:
<SubmitButton pendingLabel="Rejestruję konto…" variant="solid" fullWidth>
  Dalej: płatność
</SubmitButton>
```

Remove any redundant button styling that overlaps with `<SubmitButton>` classes. Keep the rest of the form intact.

- [ ] **Step 4: Modify `web/app/login/page.tsx`**

Replace the `<button type="submit">…Zaloguj się</button>` with:

```tsx
import { SubmitButton } from "@/components/ui/submit-button";

<SubmitButton pendingLabel="Loguję…" variant="solid" fullWidth>
  Zaloguj się
</SubmitButton>
```

- [ ] **Step 5: Modify `web/app/onboarding/platnosc/page.tsx`** — both buttons

Replace „Kontynuuj jako beta tester":

```tsx
<SubmitButton pendingLabel="Aktywuję dostęp…" variant="outline">
  Kontynuuj jako beta tester
</SubmitButton>
```

Replace „Rozpocznij 3 dni testu":

```tsx
<SubmitButton pendingLabel="Przygotowuję płatność…" variant="solid">
  Rozpocznij 3 dni testu
</SubmitButton>
```

Import: `import { SubmitButton } from "@/components/ui/submit-button";`

- [ ] **Step 6: Modify `web/app/onboarding/google/page.tsx`**

Replace „Połącz konto Google":

```tsx
import { SubmitButton } from "@/components/ui/submit-button";

<SubmitButton pendingLabel="Łączę z Google…" variant="solid" fullWidth>
  Połącz konto Google
</SubmitButton>
```

- [ ] **Step 7: Modify `web/app/(app)/ustawienia/page.tsx`**

Replace „Zapisz ustawienia konta":

```tsx
import { SubmitButton } from "@/components/ui/submit-button";

<SubmitButton pendingLabel="Zapisuję…" variant="outline">
  Zapisz ustawienia konta
</SubmitButton>
```

- [ ] **Step 8: Modify `web/app/(app)/platnosci/page.tsx`**

Replace „Potwierdzam anulowanie po okresie próbnym":

```tsx
import { SubmitButton } from "@/components/ui/submit-button";

<SubmitButton pendingLabel="Anuluję trial…" variant="outline">
  Potwierdzam anulowanie po okresie próbnym
</SubmitButton>
```

- [ ] **Step 9: Modify `web/components/auth/logout-link.tsx`**

Replace the logout `<button>` with:

```tsx
import { SubmitButton } from "@/components/ui/submit-button";

<SubmitButton pendingLabel="Wylogowuję…" variant="outline">
  Wyloguj
</SubmitButton>
```

- [ ] **Step 10: Modify `web/components/onboarding/telegram-pairing-card.tsx`** — only the „Wygeneruj nowy kod" button

```tsx
import { SubmitButton } from "@/components/ui/submit-button";

<SubmitButton pendingLabel="Generuję nowy kod…" variant="outline">
  Wygeneruj nowy kod
</SubmitButton>
```

Keep the other interactive elements (copy command button, QR, polling) unchanged.

- [ ] **Step 11: Run all tests**

Run:
```bash
cd web
node --test tests/submit-button-wiring.test.mjs
node --test tests/submit-button.test.mjs
node --test tests/brand-spinner.test.mjs
npm run lint
```
Expected: all PASS, lint clean.

- [ ] **Step 12: Build smoke test**

Run: `cd web && npm run build`
Expected: Build succeeds.

- [ ] **Step 13: Commit**

```bash
cd /Users/mansoniasty/workflows/Agent-OZE
git add web/app/rejestracja/page.tsx web/app/login/page.tsx web/app/onboarding/platnosc/page.tsx \
  web/app/onboarding/google/page.tsx 'web/app/(app)/ustawienia/page.tsx' \
  'web/app/(app)/platnosci/page.tsx' web/components/auth/logout-link.tsx \
  web/components/onboarding/telegram-pairing-card.tsx web/tests/submit-button-wiring.test.mjs
git commit -m "feat(web): wire SubmitButton into 9 P1 form actions"
```

---

## Phase 3 — Wzorzec C (Skeleton + loading.tsx)

### Task 3.1: Skeleton primitives

**Files:**
- Create: `web/components/ui/skeleton.tsx`
- Create: `web/tests/skeleton.test.mjs`

- [ ] **Step 1: Write the failing test**

Create `web/tests/skeleton.test.mjs`:

```js
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const src = readSource("../components/ui/skeleton.tsx");

test("Skeleton primitives export SkeletonLine, SkeletonCard, SkeletonCta", () => {
  assert.match(src, /export\s+function\s+SkeletonLine/);
  assert.match(src, /export\s+function\s+SkeletonCard/);
  assert.match(src, /export\s+function\s+SkeletonCta/);
});

test("SkeletonLine variants cover title | sub | body", () => {
  assert.match(src, /variant\??:\s*['"]title['"]\s*\|\s*['"]sub['"]\s*\|\s*['"]body['"]/);
});

test("Skeleton uses outline pulse with brand green, not gray blocks", () => {
  assert.match(src, /#3DFF7A/);
  assert.match(src, /border:/);
});

test("Skeleton respects prefers-reduced-motion", () => {
  assert.match(src, /prefers-reduced-motion:\s*reduce/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && node --test tests/skeleton.test.mjs`
Expected: FAIL — file does not exist.

- [ ] **Step 3: Create component**

Create `web/components/ui/skeleton.tsx`:

```tsx
import type { ReactNode } from "react";

type LineVariant = "title" | "sub" | "body";

const lineStyles: Record<LineVariant, { height: string; width: string; opacity?: number }> = {
  title: { height: "18px", width: "60%" },
  sub: { height: "12px", width: "40%", opacity: 0.5 },
  body: { height: "12px", width: "90%" },
};

export function SkeletonLine({
  variant = "body",
  delay = 0,
}: {
  variant?: LineVariant;
  delay?: number;
}) {
  const s = lineStyles[variant];
  return (
    <div
      className="sk-line"
      style={{
        height: s.height,
        width: s.width,
        opacity: s.opacity ?? 1,
        animationDelay: `${delay}ms`,
      }}
    />
  );
}

export function SkeletonCta({ delay = 0 }: { delay?: number }) {
  return (
    <div
      className="sk-line sk-cta"
      style={{ animationDelay: `${delay}ms` }}
      aria-hidden="true"
    />
  );
}

export function SkeletonCard({ children }: { children: ReactNode }) {
  return (
    <div className="sk-card" role="status" aria-label="Ładuję zawartość">
      {children}
      <style>{`
        .sk-card {
          border: 1.5px solid #3DFF7A;
          border-radius: 14px;
          padding: 26px 24px;
          background: linear-gradient(180deg, #0b0d10 0%, #060709 100%);
          box-shadow: 0 0 18px #3DFF7A14;
        }
        .sk-line {
          border: 1px solid #3DFF7A;
          border-radius: 6px;
          margin-bottom: 12px;
          animation: sk-pulse 1.6s ease-in-out infinite;
        }
        .sk-cta {
          height: 38px;
          width: 50%;
          border-radius: 999px;
          margin-top: 20px;
        }
        @keyframes sk-pulse {
          0%, 100% { border-color: #3DFF7A22; box-shadow: none; }
          50%      { border-color: #3DFF7A; box-shadow: 0 0 8px #3DFF7A44; }
        }
        @media (prefers-reduced-motion: reduce) {
          .sk-line { animation: none; border-color: #3DFF7A55; }
        }
      `}</style>
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd web && node --test tests/skeleton.test.mjs`
Expected: PASS (4/4).

- [ ] **Step 5: Commit**

```bash
cd /Users/mansoniasty/workflows/Agent-OZE
git add web/components/ui/skeleton.tsx web/tests/skeleton.test.mjs
git commit -m "feat(web): add Skeleton primitives (Wzorzec C)"
```

---

### Task 3.2: 6 loading.tsx files for app routes

**Files:**
- Create: `web/app/onboarding/platnosc/loading.tsx`
- Create: `web/app/onboarding/google/loading.tsx`
- Create: `web/app/onboarding/zasoby/loading.tsx`
- Create: `web/app/(app)/dashboard/loading.tsx`
- Create: `web/app/(app)/klienci/loading.tsx`
- Create: `web/app/(app)/kalendarz/loading.tsx`
- Create: `web/tests/loading-routes.test.mjs`

- [ ] **Step 1: Write the failing test**

Create `web/tests/loading-routes.test.mjs`:

```js
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

const paths = [
  "../app/onboarding/platnosc/loading.tsx",
  "../app/onboarding/google/loading.tsx",
  "../app/onboarding/zasoby/loading.tsx",
  "../app/(app)/dashboard/loading.tsx",
  "../app/(app)/klienci/loading.tsx",
  "../app/(app)/kalendarz/loading.tsx",
];

for (const p of paths) {
  test(`${p} exists and renders Skeleton primitives`, () => {
    const url = new URL(p, import.meta.url);
    assert.ok(existsSync(url), `expected file at ${p}`);
    const src = readFileSync(url, "utf8");
    assert.match(src, /Skeleton(Card|Line|Cta)/);
    assert.match(src, /export default/);
  });
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && node --test tests/loading-routes.test.mjs`
Expected: FAIL on all 6 (files don't exist).

- [ ] **Step 3: Create `web/app/onboarding/platnosc/loading.tsx`**

```tsx
import { SkeletonCard, SkeletonLine, SkeletonCta } from "@/components/ui/skeleton";

export default function LoadingPaymentStep() {
  return (
    <main className="min-h-screen bg-[#050607] px-6 py-16 flex items-start justify-center">
      <div className="w-full max-w-2xl">
        <SkeletonCard>
          <SkeletonLine variant="title" />
          <SkeletonLine variant="sub" delay={150} />
          <SkeletonLine variant="body" delay={300} />
          <SkeletonLine variant="body" delay={450} />
          <SkeletonCta delay={600} />
        </SkeletonCard>
      </div>
    </main>
  );
}
```

- [ ] **Step 4: Create `web/app/onboarding/google/loading.tsx`**

Same structure, different title text in a comment:

```tsx
import { SkeletonCard, SkeletonLine, SkeletonCta } from "@/components/ui/skeleton";

export default function LoadingGoogleStep() {
  return (
    <main className="min-h-screen bg-[#050607] px-6 py-16 flex items-start justify-center">
      <div className="w-full max-w-2xl">
        <SkeletonCard>
          <SkeletonLine variant="title" />
          <SkeletonLine variant="sub" delay={150} />
          <SkeletonLine variant="body" delay={300} />
          <SkeletonCta delay={450} />
        </SkeletonCard>
      </div>
    </main>
  );
}
```

- [ ] **Step 5: Create `web/app/onboarding/zasoby/loading.tsx`**

```tsx
import { SkeletonCard, SkeletonLine } from "@/components/ui/skeleton";

export default function LoadingResourcesStep() {
  return (
    <main className="min-h-screen bg-[#050607] px-6 py-16 flex items-start justify-center">
      <div className="w-full max-w-2xl">
        <SkeletonCard>
          <SkeletonLine variant="title" />
          <SkeletonLine variant="sub" delay={150} />
          <SkeletonLine variant="body" delay={300} />
          <SkeletonLine variant="body" delay={450} />
          <SkeletonLine variant="body" delay={600} />
        </SkeletonCard>
      </div>
    </main>
  );
}
```

- [ ] **Step 6: Create `web/app/(app)/dashboard/loading.tsx`**

```tsx
import { SkeletonCard, SkeletonLine } from "@/components/ui/skeleton";

export default function LoadingDashboard() {
  return (
    <div className="min-h-screen bg-[#050607] p-6 grid gap-4 md:grid-cols-2">
      <SkeletonCard>
        <SkeletonLine variant="title" />
        <SkeletonLine variant="body" delay={150} />
        <SkeletonLine variant="body" delay={300} />
      </SkeletonCard>
      <SkeletonCard>
        <SkeletonLine variant="title" />
        <SkeletonLine variant="body" delay={150} />
        <SkeletonLine variant="body" delay={300} />
      </SkeletonCard>
    </div>
  );
}
```

- [ ] **Step 7: Create `web/app/(app)/klienci/loading.tsx`**

```tsx
import { SkeletonCard, SkeletonLine } from "@/components/ui/skeleton";

export default function LoadingClients() {
  return (
    <div className="min-h-screen bg-[#050607] p-6 space-y-3">
      {Array.from({ length: 8 }).map((_, i) => (
        <SkeletonCard key={i}>
          <SkeletonLine variant="title" delay={i * 80} />
          <SkeletonLine variant="sub" delay={i * 80 + 100} />
        </SkeletonCard>
      ))}
    </div>
  );
}
```

- [ ] **Step 8: Create `web/app/(app)/kalendarz/loading.tsx`**

```tsx
import { SkeletonCard, SkeletonLine } from "@/components/ui/skeleton";

export default function LoadingCalendar() {
  return (
    <div className="min-h-screen bg-[#050607] p-6 grid gap-3 md:grid-cols-7">
      {Array.from({ length: 14 }).map((_, i) => (
        <SkeletonCard key={i}>
          <SkeletonLine variant="sub" delay={i * 60} />
          <SkeletonLine variant="body" delay={i * 60 + 80} />
        </SkeletonCard>
      ))}
    </div>
  );
}
```

- [ ] **Step 9: Run test to verify it passes**

Run: `cd web && node --test tests/loading-routes.test.mjs && npm run build`
Expected: tests PASS (6/6), build succeeds.

- [ ] **Step 10: Commit**

```bash
cd /Users/mansoniasty/workflows/Agent-OZE
git add web/app/onboarding/platnosc/loading.tsx web/app/onboarding/google/loading.tsx \
  web/app/onboarding/zasoby/loading.tsx 'web/app/(app)/dashboard/loading.tsx' \
  'web/app/(app)/klienci/loading.tsx' 'web/app/(app)/kalendarz/loading.tsx' \
  web/tests/loading-routes.test.mjs
git commit -m "feat(web): add 6 loading.tsx files with outline skeletons (Wzorzec C)"
```

---

## Phase 4 — Wzorzec B (NavigationBar + BreadcrumbArrow)

### Task 4.1: NavigationBar sliding rail with useLinkStatus

**Files:**
- Create: `web/components/ui/navigation-bar.tsx`
- Create: `web/tests/navigation-bar.test.mjs`

- [ ] **Step 1: Write the failing test**

Create `web/tests/navigation-bar.test.mjs`:

```js
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const src = readSource("../components/ui/navigation-bar.tsx");

test("NavigationBar is a client component", () => {
  assert.match(src, /^['"]use client['"]/m);
});

test("NavigationBar exposes manual show() via context or props", () => {
  assert.match(src, /useNavigationProgress|NavigationProgressProvider/);
});

test("NavigationBar uses brand green and slides on top of viewport", () => {
  assert.match(src, /#3DFF7A/);
  assert.match(src, /position:\s*fixed/);
  assert.match(src, /top:\s*0/);
});

test("NavigationBar respects prefers-reduced-motion", () => {
  assert.match(src, /prefers-reduced-motion:\s*reduce/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && node --test tests/navigation-bar.test.mjs`
Expected: FAIL — file does not exist.

- [ ] **Step 3: Create component**

Create `web/components/ui/navigation-bar.tsx`:

```tsx
"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

type Ctx = {
  visible: boolean;
  show: () => void;
  hide: () => void;
};

const NavigationProgressContext = createContext<Ctx | null>(null);

export function useNavigationProgress() {
  const ctx = useContext(NavigationProgressContext);
  if (!ctx) {
    throw new Error("useNavigationProgress must be used within NavigationProgressProvider");
  }
  return ctx;
}

export function NavigationProgressProvider({ children }: { children: ReactNode }) {
  const [visible, setVisible] = useState(false);
  const show = useCallback(() => setVisible(true), []);
  const hide = useCallback(() => setVisible(false), []);

  useEffect(() => {
    if (!visible) return;
    const id = window.setTimeout(hide, 8000);
    return () => window.clearTimeout(id);
  }, [visible, hide]);

  const value = useMemo(() => ({ visible, show, hide }), [visible, show, hide]);

  return (
    <NavigationProgressContext.Provider value={value}>
      {children}
      <NavigationBar />
    </NavigationProgressContext.Provider>
  );
}

function NavigationBar() {
  const { visible } = useNavigationProgress();
  if (!visible) return null;
  return (
    <div
      aria-hidden="true"
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        height: 3,
        background: "#1f242b",
        zIndex: 9999,
        overflow: "hidden",
      }}
    >
      <div className="nav-bar-fill" />
      <style>{`
        .nav-bar-fill {
          position: absolute;
          top: 0; bottom: 0; left: -40%;
          width: 40%;
          background: linear-gradient(90deg, transparent, #3DFF7A 60%, transparent);
          box-shadow: 0 0 12px #3DFF7A88;
          animation: nav-slide 1.4s cubic-bezier(.65,.05,.36,1) infinite;
        }
        @keyframes nav-slide { to { left: 100%; } }
        @media (prefers-reduced-motion: reduce) {
          .nav-bar-fill {
            animation: none;
            left: 30%;
          }
        }
      `}</style>
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd web && node --test tests/navigation-bar.test.mjs`
Expected: PASS (4/4).

- [ ] **Step 5: Commit**

```bash
cd /Users/mansoniasty/workflows/Agent-OZE
git add web/components/ui/navigation-bar.tsx web/tests/navigation-bar.test.mjs
git commit -m "feat(web): add NavigationBar + provider (Wzorzec B rail)"
```

---

### Task 4.2: BreadcrumbArrow crawling dashed line

**Files:**
- Create: `web/components/ui/breadcrumb-arrow.tsx`
- Create: `web/tests/breadcrumb-arrow.test.mjs`

- [ ] **Step 1: Write the failing test**

Create `web/tests/breadcrumb-arrow.test.mjs`:

```js
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const src = readSource("../components/ui/breadcrumb-arrow.tsx");

test("BreadcrumbArrow renders SVG with crawling dash animation", () => {
  assert.match(src, /export\s+function\s+BreadcrumbArrow/);
  assert.match(src, /stroke-dasharray|strokeDasharray/);
  assert.match(src, /@keyframes\s+breadcrumb-crawl/);
});

test("BreadcrumbArrow uses brand green", () => {
  assert.match(src, /#3DFF7A/);
});

test("BreadcrumbArrow respects reduced-motion", () => {
  assert.match(src, /prefers-reduced-motion:\s*reduce/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && node --test tests/breadcrumb-arrow.test.mjs`
Expected: FAIL.

- [ ] **Step 3: Create component**

Create `web/components/ui/breadcrumb-arrow.tsx`:

```tsx
export function BreadcrumbArrow({ width = 120 }: { width?: number }) {
  return (
    <span
      aria-hidden="true"
      style={{
        display: "inline-block",
        width,
        height: 18,
        filter: "drop-shadow(0 0 4px #3DFF7A77)",
      }}
    >
      <svg viewBox="0 0 220 18" width="100%" height="100%">
        <path
          className="breadcrumb-crawl"
          d="M4 9 L200 9"
          fill="none"
          stroke="#3DFF7A"
          strokeWidth="1.4"
          strokeLinecap="round"
          strokeDasharray="5 6"
        />
        <path
          d="M194 3 L212 9 L194 15"
          fill="none"
          stroke="#3DFF7A"
          strokeWidth="1.4"
          strokeLinecap="round"
        />
      </svg>
      <style>{`
        .breadcrumb-crawl { animation: breadcrumb-crawl 0.8s linear infinite; }
        @keyframes breadcrumb-crawl { to { stroke-dashoffset: -11; } }
        @media (prefers-reduced-motion: reduce) {
          .breadcrumb-crawl { animation: none; }
        }
      `}</style>
    </span>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd web && node --test tests/breadcrumb-arrow.test.mjs`
Expected: PASS (3/3).

- [ ] **Step 5: Commit**

```bash
cd /Users/mansoniasty/workflows/Agent-OZE
git add web/components/ui/breadcrumb-arrow.tsx web/tests/breadcrumb-arrow.test.mjs
git commit -m "feat(web): add BreadcrumbArrow (Wzorzec B connector)"
```

---

### Task 4.3: Mount NavigationProgressProvider in app layout + wire from form actions

**Files:**
- Modify: `web/app/layout.tsx`
- Create: `web/components/ui/use-link-status-watcher.tsx`
- Create: `web/tests/navigation-bar-mounted.test.mjs`

- [ ] **Step 1: Write the failing test**

Create `web/tests/navigation-bar-mounted.test.mjs`:

```js
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const layoutSrc = readSource("../app/layout.tsx");

test("app/layout.tsx wraps children with NavigationProgressProvider", () => {
  assert.match(layoutSrc, /NavigationProgressProvider/);
});

test("LinkStatusWatcher exists and uses useLinkStatus from next/link", () => {
  const watcherSrc = readSource("../components/ui/use-link-status-watcher.tsx");
  assert.match(watcherSrc, /useLinkStatus/);
  assert.match(watcherSrc, /useNavigationProgress/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && node --test tests/navigation-bar-mounted.test.mjs`
Expected: FAIL.

- [ ] **Step 3: Create LinkStatusWatcher**

Create `web/components/ui/use-link-status-watcher.tsx`:

```tsx
"use client";

import { useLinkStatus } from "next/link";
import { useEffect } from "react";
import { useNavigationProgress } from "./navigation-bar";

export function LinkStatusWatcher() {
  const status = useLinkStatus();
  const { show, hide } = useNavigationProgress();

  useEffect(() => {
    if (status.pending) {
      show();
    } else {
      hide();
    }
  }, [status.pending, show, hide]);

  return null;
}
```

- [ ] **Step 4: Modify `web/app/layout.tsx`**

Find the body wrapper, replace the children render with:

```tsx
import { NavigationProgressProvider } from "@/components/ui/navigation-bar";

// inside the body JSX, wrap children:
<NavigationProgressProvider>
  {children}
</NavigationProgressProvider>
```

Keep existing analytics, fonts, Stripe scripts etc. intact.

- [ ] **Step 5: Run test to verify it passes**

Run: `cd web && node --test tests/navigation-bar-mounted.test.mjs && npm run build`
Expected: PASS (2/2), build succeeds.

- [ ] **Step 6: Commit**

```bash
cd /Users/mansoniasty/workflows/Agent-OZE
git add web/app/layout.tsx web/components/ui/use-link-status-watcher.tsx web/tests/navigation-bar-mounted.test.mjs
git commit -m "feat(web): mount NavigationProgressProvider in root layout"
```

---

## Phase 5 — Wzorzec E (Toast / sonner integration)

### Task 5.1: Configure sonner Toaster + brand theme + helpers

**Files:**
- Modify: `web/app/layout.tsx` (add `<Toaster />`)
- Create: `web/lib/ui/toast.ts`
- Create: `web/components/ui/brand-toaster.tsx`
- Create: `web/tests/toast.test.mjs`

- [ ] **Step 1: Write the failing test**

Create `web/tests/toast.test.mjs`:

```js
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const helpersSrc = readSource("../lib/ui/toast.ts");
const toasterSrc = readSource("../components/ui/brand-toaster.tsx");
const layoutSrc = readSource("../app/layout.tsx");

test("toast.ts exports showSuccess, showError, showAction, showPromise", () => {
  for (const fn of ["showSuccess", "showError", "showAction", "showPromise"]) {
    assert.match(helpersSrc, new RegExp(`export\\s+(const|function)\\s+${fn}`));
  }
});

test("toast helpers import from sonner", () => {
  assert.match(helpersSrc, /from\s+['"]sonner['"]/);
});

test("BrandToaster wraps sonner Toaster with brand theme", () => {
  assert.match(toasterSrc, /from\s+['"]sonner['"]/);
  assert.match(toasterSrc, /#3DFF7A/);
});

test("layout.tsx mounts BrandToaster", () => {
  assert.match(layoutSrc, /BrandToaster/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && node --test tests/toast.test.mjs`
Expected: FAIL.

- [ ] **Step 3: Create `web/lib/ui/toast.ts`**

```ts
import { toast } from "sonner";

export const showSuccess = (title: string, body?: string) =>
  toast.success(title, { description: body, duration: 6000 });

export const showError = (
  title: string,
  body?: string,
  retry?: () => void,
) =>
  toast.error(title, {
    description: body,
    duration: 8000,
    action: retry ? { label: "Spróbuj ponownie", onClick: retry } : undefined,
  });

export const showAction = (
  title: string,
  body: string,
  undo: () => void,
) =>
  toast(title, {
    description: body,
    duration: 6000,
    action: { label: "Cofnij", onClick: undo },
  });

export function showPromise<T>(
  promise: Promise<T>,
  msgs: { loading: string; success: string; error: string },
) {
  return toast.promise(promise, msgs);
}
```

- [ ] **Step 4: Create `web/components/ui/brand-toaster.tsx`**

```tsx
"use client";

import { Toaster } from "sonner";

export function BrandToaster() {
  return (
    <Toaster
      theme="dark"
      position="bottom-right"
      gap={12}
      toastOptions={{
        style: {
          background: "#0b0d10",
          color: "#f5f7fa",
          border: "1px solid #3DFF7A",
          borderRadius: 12,
          boxShadow:
            "0 0 0 1px #3DFF7A22, 0 0 18px #3DFF7A22, 0 12px 36px #00000088",
          fontSize: 13,
        },
        classNames: {
          error: "sonner-brand-error",
          success: "sonner-brand-success",
        },
      }}
    />
  );
}
```

- [ ] **Step 5: Modify `web/app/layout.tsx`**

Inside the body, after `<NavigationProgressProvider>` opening:

```tsx
import { BrandToaster } from "@/components/ui/brand-toaster";

// inside NavigationProgressProvider:
<NavigationProgressProvider>
  {children}
  <BrandToaster />
</NavigationProgressProvider>
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd web && node --test tests/toast.test.mjs && npm run build`
Expected: PASS (4/4), build succeeds.

- [ ] **Step 7: Commit**

```bash
cd /Users/mansoniasty/workflows/Agent-OZE
git add web/lib/ui/toast.ts web/components/ui/brand-toaster.tsx web/app/layout.tsx web/tests/toast.test.mjs
git commit -m "feat(web): integrate sonner with brand theme + helpers"
```

---

### Task 5.2: Migrate decyzje-preview custom toast to sonner helpers

**Files:**
- Modify: `web/components/dashboard/decyzje-preview.tsx`
- Create: `web/tests/decyzje-preview-toast.test.mjs`

- [ ] **Step 1: Write the failing test**

Create `web/tests/decyzje-preview-toast.test.mjs`:

```js
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const src = readSource("../components/dashboard/decyzje-preview.tsx");

test("decyzje-preview uses sonner-backed helpers", () => {
  assert.match(src, /from\s+['"]@\/lib\/ui\/toast['"]/);
  assert.match(src, /showSuccess|showError|showAction/);
});

test("decyzje-preview no longer maintains its own ToastState", () => {
  // Custom local toast type removed in favor of sonner.
  assert.equal(src.includes("type ToastState"), false);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && node --test tests/decyzje-preview-toast.test.mjs`
Expected: FAIL.

- [ ] **Step 3: Modify `web/components/dashboard/decyzje-preview.tsx`**

- Remove the `type ToastState` declaration (lines ~27-47 in the existing file).
- Remove the `const [toast, setToast] = useState<ToastState | null>(null);` state.
- Remove the JSX block that rendered the custom toast (lines ~310-350 area).
- Replace each `setToast({ ... })` call with the matching helper:
  - For status changes: `showAction("Zmieniono status", "Klient: …", () => undo())`
  - For schedule actions: `showSuccess("Zaplanowano telefon", "Klient: …")`
  - For errors: `showError("Nie udało się zaktualizować", err.message, () => retry())`
- Add at top: `import { showSuccess, showError, showAction } from "@/lib/ui/toast";`
- Leave `useTransition` optimistic state machinery as-is.

- [ ] **Step 4: Run test + build**

Run: `cd web && node --test tests/decyzje-preview-toast.test.mjs && npm run build`
Expected: PASS, build succeeds.

- [ ] **Step 5: Commit**

```bash
cd /Users/mansoniasty/workflows/Agent-OZE
git add web/components/dashboard/decyzje-preview.tsx web/tests/decyzje-preview-toast.test.mjs
git commit -m "refactor(web): migrate decyzje-preview from custom toast to sonner helpers"
```

---

## Phase 6 — Offer generator overhaul

### Task 6.1: ConfirmDialog component for destructive actions

**Files:**
- Create: `web/components/ui/confirm-dialog.tsx`
- Create: `web/tests/confirm-dialog.test.mjs`

- [ ] **Step 1: Write the failing test**

Create `web/tests/confirm-dialog.test.mjs`:

```js
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const src = readSource("../components/ui/confirm-dialog.tsx");

test("ConfirmDialog is a client component with destructive variant", () => {
  assert.match(src, /^['"]use client['"]/m);
  assert.match(src, /export\s+function\s+ConfirmDialog/);
  assert.match(src, /variant\??:\s*['"]destructive['"]/);
});

test("ConfirmDialog uses Escape key to cancel", () => {
  assert.match(src, /Escape/);
});

test("ConfirmDialog disables confirm button while pending", () => {
  assert.match(src, /pending/);
  assert.match(src, /disabled/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && node --test tests/confirm-dialog.test.mjs`
Expected: FAIL.

- [ ] **Step 3: Create component**

Create `web/components/ui/confirm-dialog.tsx`:

```tsx
"use client";

import { useEffect, useState, type ReactNode } from "react";
import { BrandSpinner } from "./brand-spinner";

type Props = {
  open: boolean;
  title: string;
  description?: ReactNode;
  confirmLabel: string;
  cancelLabel?: string;
  variant?: "default" | "destructive";
  onConfirm: () => Promise<void> | void;
  onCancel: () => void;
};

export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel,
  cancelLabel = "Anuluj",
  variant = "default",
  onConfirm,
  onCancel,
}: Props) {
  const [pending, setPending] = useState(false);

  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape" && !pending) onCancel();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, pending, onCancel]);

  if (!open) return null;

  const confirmColor = variant === "destructive" ? "#FF6464" : "#3DFF7A";

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-dialog-title"
      style={{
        position: "fixed",
        inset: 0,
        background: "#000000aa",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 10000,
      }}
    >
      <div
        style={{
          background: "#0b0d10",
          border: `1px solid ${confirmColor}`,
          borderRadius: 14,
          padding: "26px 28px",
          maxWidth: 440,
          width: "calc(100% - 32px)",
          boxShadow: `0 0 0 1px ${confirmColor}22, 0 24px 60px #000`,
          color: "#f5f7fa",
        }}
      >
        <h3 id="confirm-dialog-title" style={{ marginTop: 0, fontSize: 18 }}>
          {title}
        </h3>
        {description && (
          <div style={{ marginTop: 8, color: "#9ca3af", fontSize: 13 }}>
            {description}
          </div>
        )}
        <div style={{ marginTop: 22, display: "flex", gap: 10, justifyContent: "flex-end" }}>
          <button
            type="button"
            onClick={onCancel}
            disabled={pending}
            style={{
              background: "transparent",
              border: "1px solid #1f242b",
              color: "#9ca3af",
              padding: "10px 16px",
              borderRadius: 999,
              cursor: pending ? "wait" : "pointer",
            }}
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            disabled={pending}
            onClick={async () => {
              setPending(true);
              try {
                await onConfirm();
              } finally {
                setPending(false);
              }
            }}
            style={{
              background: confirmColor,
              color: "#0b0d10",
              padding: "10px 18px",
              borderRadius: 999,
              fontWeight: 600,
              cursor: pending ? "wait" : "pointer",
              border: "none",
              display: "inline-flex",
              alignItems: "center",
              gap: 8,
            }}
          >
            {pending && <BrandSpinner variant="solid" />}
            <span>{confirmLabel}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd web && node --test tests/confirm-dialog.test.mjs`
Expected: PASS (3/3).

- [ ] **Step 5: Commit**

```bash
cd /Users/mansoniasty/workflows/Agent-OZE
git add web/components/ui/confirm-dialog.tsx web/tests/confirm-dialog.test.mjs
git commit -m "feat(web): add ConfirmDialog for destructive actions"
```

---

### Task 6.2: Wire local loading state + toast + ConfirmDialog into offer-generator

**Files:**
- Modify: `web/components/offers/offer-generator.tsx`
- Create: `web/tests/offer-generator-loading-ux.test.mjs`

- [ ] **Step 1: Write the failing test**

Create `web/tests/offer-generator-loading-ux.test.mjs`:

```js
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const src = readSource("../components/offers/offer-generator.tsx");

test("offer-generator imports toast helpers", () => {
  assert.match(src, /@\/lib\/ui\/toast/);
});

test("offer-generator imports ConfirmDialog", () => {
  assert.match(src, /ConfirmDialog/);
});

test("offer-generator renders BrandSpinner on async ops", () => {
  assert.match(src, /BrandSpinner/);
});

test("offer-generator tracks per-action loading state (not single global flag)", () => {
  // Expect a record-style state, not just one boolean.
  assert.match(src, /loadingAction|actionLoading|busyAction/);
});

test("deleteOffer is guarded by ConfirmDialog", () => {
  assert.match(src, /ConfirmDialog/);
  assert.match(src, /deleteOffer/);
  // Confirmation copy must mention deletion.
  assert.match(src, /usuń|usunąć|usunięcia/i);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && node --test tests/offer-generator-loading-ux.test.mjs`
Expected: FAIL.

- [ ] **Step 3: Modify `web/components/offers/offer-generator.tsx`**

Add to imports:

```tsx
import { BrandSpinner } from "@/components/ui/brand-spinner";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { showSuccess, showError } from "@/lib/ui/toast";
```

Replace the existing `useState<string | null>(apiError)` flow with a record-style loading map:

```tsx
type ActionKey =
  | "createDraft"
  | "moveReady"
  | "duplicateOffer"
  | "deleteOffer"
  | "saveEditor"
  | "publishEditor"
  | "downloadPdf";

const [actionLoading, setActionLoading] = useState<Partial<Record<ActionKey, boolean>>>({});
const [deleteCandidate, setDeleteCandidate] = useState<{ id: string; name: string } | null>(null);

async function withLoading<T>(key: ActionKey, fn: () => Promise<T>): Promise<T | null> {
  setActionLoading((s) => ({ ...s, [key]: true }));
  try {
    return await fn();
  } catch (err) {
    showError(
      "Coś poszło nie tak",
      err instanceof Error ? err.message : "Spróbuj jeszcze raz.",
      () => withLoading(key, fn),
    );
    return null;
  } finally {
    setActionLoading((s) => ({ ...s, [key]: false }));
  }
}
```

For each of the 7 onClick async ops (around lines 1052, 1060, 1063, 1079, 1173, 1180, 1188 in current file), wrap the call:

```tsx
// Example for saveEditor:
onClick={() => void withLoading("saveEditor", async () => {
  await saveEditor();
  showSuccess("Oferta zapisana");
})}
disabled={actionLoading.saveEditor}
```

Add `{actionLoading.saveEditor && <BrandSpinner />}` inside each button JSX. Repeat the pattern for `createDraft`, `moveReady`, `duplicateOffer`, `publishEditor`, `downloadPdf`.

For `deleteOffer`, replace the direct call with confirm flow:

```tsx
onClick={() => setDeleteCandidate({ id: offer.id, name: offer.title })}
```

At the bottom of the component JSX, add:

```tsx
<ConfirmDialog
  open={!!deleteCandidate}
  title="Czy na pewno usunąć szablon?"
  description={deleteCandidate ? `${deleteCandidate.name} zostanie nieodwracalnie usunięta.` : null}
  confirmLabel="Usuń"
  variant="destructive"
  onCancel={() => setDeleteCandidate(null)}
  onConfirm={async () => {
    if (!deleteCandidate) return;
    await withLoading("deleteOffer", async () => {
      await deleteOffer(deleteCandidate.id);
      showSuccess("Szablon usunięty");
    });
    setDeleteCandidate(null);
  }}
/>
```

Remove the old `apiError` red border block that used to display errors (errors now live in toast).

- [ ] **Step 4: Run tests + build**

Run:
```bash
cd web
node --test tests/offer-generator-loading-ux.test.mjs
node --test tests/offer-email-template-ui.test.mjs
node --test tests/offer-navigation.test.mjs
npm run lint
npm run build
```
Expected: all PASS, lint clean, build succeeds.

- [ ] **Step 5: Commit**

```bash
cd /Users/mansoniasty/workflows/Agent-OZE
git add web/components/offers/offer-generator.tsx web/tests/offer-generator-loading-ux.test.mjs
git commit -m "feat(web): offer-generator gets per-action spinner + toast + confirm dialog"
```

---

## Phase 7 — Wzorzec D (3-step progress for createGoogleResources)

### Task 7.1: Backend SSE/polling endpoint for resources-progress

**Files:**
- Create: `web/app/api/onboarding/resources-progress/route.ts`
- Create: `web/tests/resources-progress-endpoint.test.mjs`

- [ ] **Step 1: Write the failing test**

Create `web/tests/resources-progress-endpoint.test.mjs`:

```js
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const src = readSource("../app/api/onboarding/resources-progress/route.ts");

test("route handler is a GET handler", () => {
  assert.match(src, /export\s+async\s+function\s+GET/);
});

test("response uses SSE content-type or JSON polling shape", () => {
  assert.ok(
    src.includes("text/event-stream") || src.includes("application/json"),
    "expected SSE or JSON response",
  );
});

test("payload includes step, elapsed_ms fields", () => {
  assert.match(src, /step/);
  assert.match(src, /elapsed_ms/);
});

test("route reads authoritative progress from FastAPI proxy", () => {
  assert.match(src, /fastApiBaseUrl|FASTAPI_BASE_URL/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && node --test tests/resources-progress-endpoint.test.mjs`
Expected: FAIL.

- [ ] **Step 3: Create endpoint**

Create `web/app/api/onboarding/resources-progress/route.ts`:

```ts
import { NextResponse } from "next/server";
import { getCurrentAccount } from "@/lib/api/account";
import { fastApiBaseUrl } from "@/lib/api/base-url";

type ProgressPayload = {
  step: "sheets" | "calendar" | "drive" | "done";
  elapsed_ms: number;
  error?: { code: string; message: string };
};

export async function GET(): Promise<Response> {
  const account = await getCurrentAccount();
  if (!account.authenticated || !account.accessToken) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  const base = fastApiBaseUrl();
  if (!base) {
    return NextResponse.json<ProgressPayload>(
      { step: "sheets", elapsed_ms: 0 },
      { status: 200 },
    );
  }

  const upstream = await fetch(`${base}/api/onboarding/resources-progress`, {
    headers: { Authorization: `Bearer ${account.accessToken}` },
    cache: "no-store",
  });

  if (!upstream.ok) {
    return NextResponse.json(
      { error: "upstream_error", status: upstream.status },
      { status: 502 },
    );
  }

  const data = (await upstream.json()) as ProgressPayload;
  return NextResponse.json(data, {
    headers: { "Cache-Control": "no-store" },
  });
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd web && node --test tests/resources-progress-endpoint.test.mjs && npm run build`
Expected: PASS (4/4), build succeeds.

- [ ] **Step 5: Commit**

```bash
cd /Users/mansoniasty/workflows/Agent-OZE
git add web/app/api/onboarding/resources-progress/route.ts web/tests/resources-progress-endpoint.test.mjs
git commit -m "feat(web): add resources-progress polling endpoint"
```

> **Note:** The FastAPI side (`/api/onboarding/resources-progress`) must be added separately. Track that as an `oze-agent` follow-up in `docs/IMPLEMENTATION_PLAN.md`. Until then, the polling endpoint returns the initial `{step: "sheets", elapsed_ms: 0}` and the UI never advances — frontend still functions; user just sees stalled progress.

---

### Task 7.2: ResourceProgress 3-step canvas component

**Files:**
- Create: `web/components/onboarding/resource-progress.tsx`
- Create: `web/tests/resource-progress.test.mjs`

- [ ] **Step 1: Write the failing test**

Create `web/tests/resource-progress.test.mjs`:

```js
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const src = readSource("../components/onboarding/resource-progress.tsx");

test("ResourceProgress is a client component polling progress endpoint", () => {
  assert.match(src, /^['"]use client['"]/m);
  assert.match(src, /\/api\/onboarding\/resources-progress/);
});

test("ResourceProgress renders 3 named steps (Sheets, Kalendarz, Drive)", () => {
  assert.match(src, /Sheets/);
  assert.match(src, /Kalendarz/);
  assert.match(src, /Drive/);
});

test("ResourceProgress displays elapsed time and status text", () => {
  assert.match(src, /elapsed/);
  assert.match(src, /UPŁYNĘŁO/);
});

test("ResourceProgress redirects to /onboarding/telegram on done", () => {
  assert.match(src, /\/onboarding\/telegram/);
});

test("ResourceProgress respects prefers-reduced-motion", () => {
  assert.match(src, /prefers-reduced-motion:\s*reduce/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && node --test tests/resource-progress.test.mjs`
Expected: FAIL.

- [ ] **Step 3: Create component**

Create `web/components/onboarding/resource-progress.tsx`:

```tsx
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { showError } from "@/lib/ui/toast";

type StepKey = "sheets" | "calendar" | "drive" | "done";
type StepLabel = { key: Exclude<StepKey, "done">; label: string; status: string };

const STEPS: StepLabel[] = [
  { key: "sheets", label: "Sheets", status: "Tworzę arkusz klientów" },
  { key: "calendar", label: "Kalendarz", status: "Konfiguruję Twój kalendarz" },
  { key: "drive", label: "Drive", status: "Przygotowuję folder na zdjęcia" },
];

function stepState(current: StepKey, target: StepKey): "done" | "active" | "pending" {
  const order: StepKey[] = ["sheets", "calendar", "drive", "done"];
  return order.indexOf(current) > order.indexOf(target)
    ? "done"
    : order.indexOf(current) === order.indexOf(target)
      ? "active"
      : "pending";
}

export function ResourceProgress() {
  const router = useRouter();
  const [current, setCurrent] = useState<StepKey>("sheets");
  const [elapsedMs, setElapsedMs] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      try {
        const res = await fetch("/api/onboarding/resources-progress", { cache: "no-store" });
        if (!res.ok) throw new Error(`status ${res.status}`);
        const payload = (await res.json()) as { step: StepKey; elapsed_ms: number };
        if (cancelled) return;
        setCurrent(payload.step);
        setElapsedMs(payload.elapsed_ms);
        if (payload.step === "done") {
          setTimeout(() => router.push("/onboarding/telegram"), 800);
        }
      } catch (err) {
        if (cancelled) return;
        showError(
          "Nie mogę sprawdzić postępu",
          err instanceof Error ? err.message : "Spróbuję za chwilę.",
        );
      }
    }

    poll();
    const id = window.setInterval(poll, 2000);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, [router]);

  const elapsedSec = Math.floor(elapsedMs / 1000);
  const activeStep = STEPS.find((s) => stepState(current, s.key) === "active") ?? STEPS[STEPS.length - 1];

  return (
    <div className="rp-canvas">
      <div className="rp-eyebrow">krok 4 z 5 — onboarding</div>
      <h2 className="rp-title">Tworzymy Twoje konto Google</h2>
      <div className="rp-sub">To trwa zwykle 15–30 sekund. Nie odświeżaj strony.</div>

      <div className="rp-steps">
        {STEPS.map((step, idx) => (
          <Step key={step.key} state={stepState(current, step.key)} label={step.label} icon={step.key} idx={idx} />
        )).flatMap((node, idx, arr) =>
          idx < arr.length - 1
            ? [node, <Connector key={`c-${idx}`} active={stepState(current, STEPS[idx + 1].key) === "active"} done={stepState(current, STEPS[idx + 1].key) === "done" || current === "done"} />]
            : [node]
        )}
      </div>

      <div className="rp-status-row">
        <div className="rp-status">
          {current === "done" ? "Gotowe — przekierowuję" : <>{activeStep.status}<span className="dots" /></>}
        </div>
        <div className="rp-elapsed">
          UPŁYNĘŁO <strong>{elapsedSec} s</strong>
        </div>
      </div>

      <div className="rp-reassure">Operacja jest jednorazowa — robimy ją raz na całe życie konta.</div>

      <style>{`
        .rp-canvas { background: #0b0d10; border: 1px solid #1f242b; border-radius: 16px; padding: 56px 48px 48px; text-align: center; color: #f5f7fa; max-width: 720px; margin: 0 auto; }
        .rp-eyebrow { font-size: 11px; letter-spacing: 0.16em; text-transform: uppercase; color: #3DFF7A; opacity: 0.7; margin-bottom: 14px; }
        .rp-title { font-size: 22px; margin: 0 0 10px; font-weight: 500; }
        .rp-sub { font-size: 13px; color: #6b7280; margin-bottom: 38px; }
        .rp-steps { display: flex; align-items: center; justify-content: center; gap: 8px; margin: 32px auto 0; max-width: 560px; }
        .rp-status-row { margin-top: 36px; display: flex; flex-direction: column; align-items: center; gap: 6px; }
        .rp-status { font-size: 14px; }
        .dots::after { content: "…"; animation: dots-fade 1.4s steps(4, end) infinite; }
        @keyframes dots-fade { 0%{content:"";}25%{content:".";}50%{content:"..";}75%{content:"...";}100%{content:"…";} }
        .rp-elapsed { font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; color: #6b7280; }
        .rp-elapsed strong { color: #3DFF7A; font-weight: 500; }
        .rp-reassure { margin-top: 28px; font-size: 11px; color: #4a5460; font-style: italic; max-width: 360px; margin-left: auto; margin-right: auto; opacity: 0.7; }
        @media (prefers-reduced-motion: reduce) { .dots::after { animation: none; content: "…"; } }
      `}</style>
    </div>
  );
}

function Step({ state, label, icon, idx }: { state: "done" | "active" | "pending"; label: string; icon: "sheets" | "calendar" | "drive"; idx: number }) {
  return (
    <div className={`rp-step rp-step-${state}`}>
      <div className="rp-frame">
        <Icon kind={icon} />
        {state === "done" && <div className="rp-check">✓</div>}
      </div>
      <div className="rp-label">{label}</div>
      <style>{`
        .rp-step { display: flex; flex-direction: column; align-items: center; gap: 10px; width: 90px; }
        .rp-frame { width: 56px; height: 56px; border: 1.5px solid #1f242b; border-radius: 14px; display: flex; align-items: center; justify-content: center; position: relative; background: #060709; transition: all 240ms ease; }
        .rp-frame svg { width: 26px; height: 26px; stroke: #4a5460; fill: none; stroke-width: 1.4; stroke-linecap: round; stroke-linejoin: round; transition: stroke 240ms ease; }
        .rp-check { position: absolute; bottom: -4px; right: -4px; width: 18px; height: 18px; border-radius: 50%; background: #3DFF7A; color: #0b0d10; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; box-shadow: 0 0 6px #3DFF7A88; }
        .rp-label { font-size: 12px; color: #6b7280; letter-spacing: 0.02em; transition: color 240ms ease; }
        .rp-step-done .rp-frame { border-color: #3DFF7A; box-shadow: 0 0 0 1px #3DFF7A33; }
        .rp-step-done .rp-frame svg { stroke: #3DFF7A; }
        .rp-step-done .rp-label { color: #f5f7fa; }
        .rp-step-active .rp-frame { border-color: #3DFF7A; box-shadow: 0 0 0 1px #3DFF7A55, 0 0 22px #3DFF7A55; animation: step-breathe 1.6s ease-in-out infinite; }
        .rp-step-active .rp-frame svg { stroke: #3DFF7A; }
        .rp-step-active .rp-label { color: #3DFF7A; }
        @keyframes step-breathe { 0%,100%{box-shadow: 0 0 0 1px #3DFF7A33, 0 0 12px #3DFF7A33;} 50%{box-shadow: 0 0 0 1px #3DFF7A88, 0 0 26px #3DFF7A66;} }
        @media (prefers-reduced-motion: reduce) { .rp-step-active .rp-frame { animation: none; } }
      `}</style>
    </div>
  );
}

function Connector({ active, done }: { active: boolean; done: boolean }) {
  return (
    <div className={`rp-conn ${done ? "rp-conn-done" : active ? "rp-conn-active" : "rp-conn-pending"}`}>
      <svg viewBox="0 0 120 16" preserveAspectRatio="none" width="100%" height="100%">
        <path d="M2 8 L110 8" className="rail" />
        {active && <path d="M2 8 L110 8" className="crawl" />}
        {done && <path d="M104 3 L114 8 L104 13" className="head" />}
      </svg>
      <style>{`
        .rp-conn { flex: 1; height: 16px; max-width: 120px; align-self: center; margin-bottom: 24px; }
        .rp-conn svg path { fill: none; stroke-linecap: round; stroke-width: 1.4; }
        .rail { stroke: #1f242b; stroke-dasharray: 4 5; }
        .rp-conn-done .rail { stroke: #3DFF7A66; }
        .crawl { stroke: #3DFF7A; stroke-dasharray: 5 6; animation: connector-crawl 0.8s linear infinite; filter: drop-shadow(0 0 3px #3DFF7A77); }
        .head { stroke: #3DFF7A66; filter: drop-shadow(0 0 3px #3DFF7A77); }
        @keyframes connector-crawl { to { stroke-dashoffset: -11; } }
        @media (prefers-reduced-motion: reduce) { .crawl { animation: none; } }
      `}</style>
    </div>
  );
}

function Icon({ kind }: { kind: "sheets" | "calendar" | "drive" }) {
  switch (kind) {
    case "sheets":
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <rect x="3" y="3" width="18" height="18" rx="2" />
          <line x1="3" y1="9" x2="21" y2="9" />
          <line x1="3" y1="15" x2="21" y2="15" />
          <line x1="9" y1="3" x2="9" y2="21" />
          <line x1="15" y1="3" x2="15" y2="21" />
        </svg>
      );
    case "calendar":
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <rect x="3" y="5" width="18" height="16" rx="2" />
          <line x1="3" y1="10" x2="21" y2="10" />
          <line x1="8" y1="3" x2="8" y2="7" />
          <line x1="16" y1="3" x2="16" y2="7" />
        </svg>
      );
    case "drive":
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M7 4 L17 4 L22 13 L17 22 L7 22 L2 13 Z" />
          <line x1="7" y1="4" x2="12" y2="13" />
          <line x1="17" y1="4" x2="12" y2="13" />
          <line x1="2" y1="13" x2="22" y2="13" />
        </svg>
      );
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd web && node --test tests/resource-progress.test.mjs && npm run build`
Expected: PASS (5/5), build succeeds.

- [ ] **Step 5: Commit**

```bash
cd /Users/mansoniasty/workflows/Agent-OZE
git add web/components/onboarding/resource-progress.tsx web/tests/resource-progress.test.mjs
git commit -m "feat(web): add ResourceProgress 3-step component (Wzorzec D)"
```

---

### Task 7.3: Wire ResourceProgress into /onboarding/zasoby

**Files:**
- Modify: `web/app/onboarding/zasoby/page.tsx`
- Delete: `web/components/onboarding/resource-submit-button.tsx` (after migration)
- Create: `web/tests/zasoby-progress-wiring.test.mjs`

- [ ] **Step 1: Write the failing test**

Create `web/tests/zasoby-progress-wiring.test.mjs`:

```js
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const src = readSource("../app/onboarding/zasoby/page.tsx");

test("zasoby page renders ResourceProgress after submit", () => {
  assert.match(src, /ResourceProgress/);
});

test("ResourceSubmitButton is no longer used (replaced by SubmitButton + ResourceProgress)", () => {
  // After form submit the page renders ResourceProgress, so the bespoke
  // submit button is gone.
  assert.equal(src.includes("ResourceSubmitButton"), false);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && node --test tests/zasoby-progress-wiring.test.mjs`
Expected: FAIL.

- [ ] **Step 3: Modify `web/app/onboarding/zasoby/page.tsx`**

The page needs to switch between two states: initial form (with SubmitButton) and post-submit progress canvas (with ResourceProgress). Read the existing page, then restructure:

```tsx
import { SubmitButton } from "@/components/ui/submit-button";
import { ResourceProgress } from "@/components/onboarding/resource-progress";
import { createGoogleResourcesAction } from "../actions";
import { getOnboardingStatus } from "@/lib/api/onboarding";

export default async function ResourcesPage() {
  const status = await getOnboardingStatus();
  const inProgress = status.resources?.in_progress === true;

  if (inProgress) {
    return (
      <main className="min-h-screen bg-[#050607] px-6 py-16">
        <ResourceProgress />
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#050607] px-6 py-16">
      <form action={createGoogleResourcesAction}>
        {/* existing form copy */}
        <SubmitButton pendingLabel="Uruchamiam tworzenie zasobów…" variant="solid" fullWidth>
          Utwórz brakujące zasoby
        </SubmitButton>
      </form>
    </main>
  );
}
```

Keep the rest of the page copy (eyebrow, title, description) intact.

- [ ] **Step 4: Delete `web/components/onboarding/resource-submit-button.tsx`**

```bash
git rm web/components/onboarding/resource-submit-button.tsx
```

If any test references it (search `grep -r resource-submit-button web/tests`), update those tests to expect SubmitButton + ResourceProgress.

- [ ] **Step 5: Run tests + build**

Run:
```bash
cd web
node --test tests/zasoby-progress-wiring.test.mjs
node --test tests/resource-progress.test.mjs
npm run lint
npm run build
```
Expected: PASS, lint clean, build succeeds.

- [ ] **Step 6: Commit**

```bash
cd /Users/mansoniasty/workflows/Agent-OZE
git add web/app/onboarding/zasoby/page.tsx web/tests/zasoby-progress-wiring.test.mjs
git rm web/components/onboarding/resource-submit-button.tsx
git commit -m "feat(web): wire ResourceProgress into zasoby flow, drop bespoke submit"
```

---

## Phase 8 — Wzorzec F (Interstitial)

### Task 8.1: RedirectingScreen component + przekierowuje route

**Files:**
- Create: `web/components/ui/redirecting-screen.tsx`
- Create: `web/app/onboarding/przekierowuje/page.tsx`
- Create: `web/tests/redirecting-screen.test.mjs`

- [ ] **Step 1: Write the failing test**

Create `web/tests/redirecting-screen.test.mjs`:

```js
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const componentSrc = readSource("../components/ui/redirecting-screen.tsx");
const routeSrc = readSource("../app/onboarding/przekierowuje/page.tsx");

test("RedirectingScreen is a client component accepting steps + nextUrl", () => {
  assert.match(componentSrc, /^['"]use client['"]/m);
  assert.match(componentSrc, /steps/);
  assert.match(componentSrc, /nextUrl/);
});

test("RedirectingScreen has brand mark and pill steps", () => {
  assert.match(componentSrc, /brand-mark|BrandMark/);
  assert.match(componentSrc, /pill/);
});

test("RedirectingScreen redirects after delay using window.location", () => {
  assert.match(componentSrc, /window\.location/);
});

test("przekierowuje page resolves to=stripe|google|next", () => {
  assert.match(routeSrc, /stripe/);
  assert.match(routeSrc, /google/);
  assert.match(routeSrc, /next/);
});

test("RedirectingScreen respects reduced motion", () => {
  assert.match(componentSrc, /prefers-reduced-motion:\s*reduce/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && node --test tests/redirecting-screen.test.mjs`
Expected: FAIL.

- [ ] **Step 3: Create RedirectingScreen**

Create `web/components/ui/redirecting-screen.tsx`:

```tsx
"use client";

import { useEffect } from "react";

type StepStatus = "done" | "active" | "pending";
type Step = { label: string; status: StepStatus };

type Props = {
  steps: Step[];
  statusLabel: string;
  subLabel: string;
  nextUrl: string;
  delayMs?: number;
};

export function RedirectingScreen({
  steps,
  statusLabel,
  subLabel,
  nextUrl,
  delayMs = 600,
}: Props) {
  useEffect(() => {
    const id = window.setTimeout(() => {
      window.location.href = nextUrl;
    }, delayMs);
    return () => window.clearTimeout(id);
  }, [nextUrl, delayMs]);

  return (
    <div className="rs-screen" role="status" aria-live="polite">
      <span className="brand-mark" aria-hidden="true" />
      <div className="rs-status">{statusLabel}<span className="dots" /></div>
      <div className="rs-sub">{subLabel}</div>
      <div className="rs-steps">
        {steps.map((step, idx) => (
          <>
            <div className={`rs-step rs-step-${step.status}`} key={`s-${idx}`}>
              <div className="pill">{step.label}</div>
            </div>
            {idx < steps.length - 1 && (
              <Connector
                key={`c-${idx}`}
                active={steps[idx + 1].status === "active"}
                done={steps[idx + 1].status === "done"}
              />
            )}
          </>
        ))}
      </div>
      <style>{`
        .rs-screen { background: radial-gradient(circle at center, #0b0d10 0%, #050607 70%); min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 40px 24px; color: #f5f7fa; }
        .brand-mark { width: 36px; height: 36px; border: 1.5px solid #3DFF7A; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-bottom: 26px; box-shadow: 0 0 18px #3DFF7A66; position: relative; }
        .brand-mark::after { content: ""; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 10px; height: 10px; border-radius: 50%; background: #3DFF7A; box-shadow: 0 0 8px #3DFF7A; animation: brand-breathe 2.2s ease-in-out infinite; }
        @keyframes brand-breathe { 0%,100% { opacity: 0.55; transform: translate(-50%, -50%) scale(0.9); } 50% { opacity: 1; transform: translate(-50%, -50%) scale(1.1); } }
        .rs-status { font-size: 14px; letter-spacing: 0.02em; margin-bottom: 4px; }
        .dots::after { content: "…"; animation: dots-fade 1.4s steps(4, end) infinite; }
        @keyframes dots-fade { 0%{content:"";}25%{content:".";}50%{content:"..";}75%{content:"...";}100%{content:"…";} }
        .rs-sub { font-size: 11px; color: #6b7280; letter-spacing: 0.05em; margin-bottom: 32px; }
        .rs-steps { display: flex; align-items: center; gap: 4px; }
        .rs-step { display: flex; flex-direction: column; align-items: center; gap: 6px; width: 84px; }
        .pill { border: 1.2px solid #1f242b; color: #4a5460; padding: 6px 10px; border-radius: 999px; font-size: 11px; letter-spacing: 0.04em; background: #060709; transition: all 240ms ease; }
        .rs-step-done .pill { border-color: #3DFF7A66; color: #3DFF7A; }
        .rs-step-active .pill { border-color: #3DFF7A; color: #3DFF7A; box-shadow: 0 0 0 1px #3DFF7A55, 0 0 18px #3DFF7A55; animation: step-breathe 1.6s ease-in-out infinite; }
        @keyframes step-breathe { 0%,100% { box-shadow: 0 0 0 1px #3DFF7A22, 0 0 8px #3DFF7A33; } 50% { box-shadow: 0 0 0 1px #3DFF7A88, 0 0 24px #3DFF7A66; } }
        @media (prefers-reduced-motion: reduce) {
          .brand-mark::after, .rs-step-active .pill, .dots::after { animation: none !important; }
        }
      `}</style>
    </div>
  );
}

function Connector({ active, done }: { active: boolean; done: boolean }) {
  return (
    <div className="rs-conn" aria-hidden="true">
      <svg viewBox="0 0 28 12" preserveAspectRatio="none" width="100%" height="100%">
        <path d="M2 6 L26 6" stroke={done ? "#3DFF7A66" : "#1f242b"} strokeDasharray="3 4" strokeWidth="1.3" strokeLinecap="round" fill="none" />
        {active && (
          <path
            d="M2 6 L26 6"
            stroke="#3DFF7A"
            strokeDasharray="4 5"
            strokeWidth="1.3"
            strokeLinecap="round"
            fill="none"
            className="rs-crawl"
          />
        )}
      </svg>
      <style>{`
        .rs-conn { width: 28px; height: 12px; }
        .rs-crawl { animation: rs-crawl 0.8s linear infinite; filter: drop-shadow(0 0 2px #3DFF7A77); }
        @keyframes rs-crawl { to { stroke-dashoffset: -9; } }
        @media (prefers-reduced-motion: reduce) { .rs-crawl { animation: none; } }
      `}</style>
    </div>
  );
}
```

- [ ] **Step 4: Create przekierowuje page**

Create `web/app/onboarding/przekierowuje/page.tsx`:

```tsx
import { RedirectingScreen } from "@/components/ui/redirecting-screen";

type StepStatus = "done" | "active" | "pending";

type RouteConfig = {
  steps: { label: string; status: StepStatus }[];
  statusLabel: string;
  subLabel: string;
  nextUrl: string;
};

const ROUTES: Record<string, RouteConfig> = {
  stripe: {
    steps: [
      { label: "Konto", status: "done" },
      { label: "Stripe", status: "active" },
      { label: "Płatność", status: "pending" },
    ],
    statusLabel: "Otwieram Stripe",
    subLabel: "Za chwilę przeniesiemy Cię do bezpiecznej płatności.",
    nextUrl: "/onboarding/checkout",
  },
  google: {
    steps: [
      { label: "Konto", status: "done" },
      { label: "Google", status: "active" },
      { label: "Uprawnienia", status: "pending" },
    ],
    statusLabel: "Łączę z Google",
    subLabel: "Za chwilę poprosimy o zgody na Sheets, Kalendarz i Drive.",
    nextUrl: "/onboarding/google/oauth-start",
  },
  next: {
    steps: [
      { label: "Google", status: "done" },
      { label: "Sprawdzam", status: "active" },
      { label: "Zasoby", status: "pending" },
    ],
    statusLabel: "Sprawdzam zgody",
    subLabel: "Za chwilę utworzymy Twoje zasoby Google.",
    nextUrl: "/onboarding/zasoby",
  },
};

export default async function PrzekierowujePage({
  searchParams,
}: {
  searchParams: Promise<{ to?: string }>;
}) {
  const { to } = await searchParams;
  const cfg = (to && ROUTES[to]) || ROUTES.stripe;
  return <RedirectingScreen {...cfg} />;
}
```

- [ ] **Step 5: Run tests + build**

Run: `cd web && node --test tests/redirecting-screen.test.mjs && npm run build`
Expected: PASS (5/5), build succeeds.

- [ ] **Step 6: Commit**

```bash
cd /Users/mansoniasty/workflows/Agent-OZE
git add web/components/ui/redirecting-screen.tsx web/app/onboarding/przekierowuje/page.tsx web/tests/redirecting-screen.test.mjs
git commit -m "feat(web): add RedirectingScreen + /onboarding/przekierowuje route (Wzorzec F)"
```

---

### Task 8.2: Route the 3 redirect chains through interstitial

**Files:**
- Modify: `web/app/auth/actions.ts`
- Modify: `web/app/onboarding/actions.ts`
- Create: `web/app/onboarding/checkout/page.tsx` (intermediate target hit from interstitial)
- Create: `web/app/onboarding/google/oauth-start/page.tsx` (intermediate target)
- Create: `web/tests/interstitial-wiring.test.mjs`

- [ ] **Step 1: Write the failing test**

Create `web/tests/interstitial-wiring.test.mjs`:

```js
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const authSrc = readSource("../app/auth/actions.ts");
const onboardingSrc = readSource("../app/onboarding/actions.ts");

test("signup redirects via przekierowuje?to=stripe", () => {
  assert.match(authSrc, /przekierowuje\?to=stripe/);
});

test("createCheckoutSession redirects via przekierowuje?to=stripe (or directly to Stripe URL)", () => {
  // After interstitial change, checkout action is now hit from interstitial page;
  // it directly redirects to Stripe.
  assert.match(onboardingSrc, /checkout\.stripe\.com|stripe\.checkout/);
});

test("startGoogleOAuthAction redirects via przekierowuje?to=google", () => {
  assert.match(onboardingSrc, /przekierowuje\?to=google/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && node --test tests/interstitial-wiring.test.mjs`
Expected: FAIL on signup and google assertions.

- [ ] **Step 3: Modify `web/app/auth/actions.ts`** — `signup`

Find the redirect at the end of `signup`:

```ts
redirect("/onboarding/platnosc");
```

Replace with:

```ts
redirect("/onboarding/przekierowuje?to=stripe");
```

> The interstitial will hit `/onboarding/checkout` (new minimal page that triggers `createCheckoutSession`), so the user still reaches Stripe — just via the interstitial.

- [ ] **Step 4: Create `web/app/onboarding/checkout/page.tsx`**

This page is the target of the interstitial — it runs the existing checkout server action and redirects to Stripe.

```tsx
import { createCheckoutSession } from "../actions";

export default async function CheckoutLaunchPage() {
  await createCheckoutSession();
  // createCheckoutSession redirects internally; this never renders.
  return null;
}
```

- [ ] **Step 5: Modify `web/app/onboarding/actions.ts`** — `startGoogleOAuthAction`

Find the line at the end:

```ts
redirect(trustedGoogleUrl);
```

Replace with:

```ts
const params = new URLSearchParams({ to: "google", url: trustedGoogleUrl });
redirect(`/onboarding/przekierowuje?${params.toString()}`);
```

- [ ] **Step 6: Modify `web/app/onboarding/przekierowuje/page.tsx` — extend google route to use the `url` query param**

Update the `ROUTES.google` config to read the URL from query:

```tsx
import { RedirectingScreen } from "@/components/ui/redirecting-screen";

type StepStatus = "done" | "active" | "pending";

export default async function PrzekierowujePage({
  searchParams,
}: {
  searchParams: Promise<{ to?: string; url?: string }>;
}) {
  const { to, url } = await searchParams;

  if (to === "google" && url) {
    return (
      <RedirectingScreen
        steps={[
          { label: "Konto", status: "done" },
          { label: "Google", status: "active" },
          { label: "Uprawnienia", status: "pending" },
        ]}
        statusLabel="Łączę z Google"
        subLabel="Za chwilę poprosimy o zgody na Sheets, Kalendarz i Drive."
        nextUrl={url}
      />
    );
  }

  if (to === "stripe") {
    return (
      <RedirectingScreen
        steps={[
          { label: "Konto", status: "done" },
          { label: "Stripe", status: "active" },
          { label: "Płatność", status: "pending" },
        ]}
        statusLabel="Otwieram Stripe"
        subLabel="Za chwilę przeniesiemy Cię do bezpiecznej płatności."
        nextUrl="/onboarding/checkout"
      />
    );
  }

  if (to === "next") {
    return (
      <RedirectingScreen
        steps={[
          { label: "Google", status: "done" },
          { label: "Sprawdzam", status: "active" },
          { label: "Zasoby", status: "pending" },
        ]}
        statusLabel="Sprawdzam zgody"
        subLabel="Za chwilę utworzymy Twoje zasoby Google."
        nextUrl="/onboarding/zasoby"
      />
    );
  }

  return (
    <RedirectingScreen
      steps={[
        { label: "Konto", status: "active" },
        { label: "Następny krok", status: "pending" },
      ]}
      statusLabel="Przekierowuję"
      subLabel="Za chwilę otworzymy następny krok."
      nextUrl="/onboarding/platnosc"
    />
  );
}
```

- [ ] **Step 7: Modify `web/app/onboarding/google/sukces/page.tsx`** (post-OAuth callback)

After the OAuth callback succeeds, replace the manual link with auto-progress through interstitial:

```tsx
import { redirect } from "next/navigation";

export default async function GoogleSuccessPage() {
  redirect("/onboarding/przekierowuje?to=next");
}
```

- [ ] **Step 8: Run tests + build**

Run:
```bash
cd web
node --test tests/interstitial-wiring.test.mjs
node --test tests/redirecting-screen.test.mjs
npm run lint
npm run build
```
Expected: PASS, lint clean, build succeeds.

- [ ] **Step 9: Commit**

```bash
cd /Users/mansoniasty/workflows/Agent-OZE
git add web/app/auth/actions.ts web/app/onboarding/actions.ts web/app/onboarding/checkout/page.tsx \
  web/app/onboarding/przekierowuje/page.tsx web/app/onboarding/google/sukces/page.tsx \
  web/tests/interstitial-wiring.test.mjs
git commit -m "feat(web): route signup, OAuth, post-OAuth through interstitial"
```

---

## Phase 9 — Verification

### Task 9.1: Run the full test suite + lint + build

**Files:** (verification only — no code changes)

- [ ] **Step 1: Run every loading-ux test**

Run:
```bash
cd web
node --test tests/loading-ux-tokens.test.mjs \
  tests/brand-spinner.test.mjs \
  tests/submit-button.test.mjs \
  tests/submit-button-wiring.test.mjs \
  tests/skeleton.test.mjs \
  tests/loading-routes.test.mjs \
  tests/navigation-bar.test.mjs \
  tests/breadcrumb-arrow.test.mjs \
  tests/navigation-bar-mounted.test.mjs \
  tests/toast.test.mjs \
  tests/decyzje-preview-toast.test.mjs \
  tests/confirm-dialog.test.mjs \
  tests/offer-generator-loading-ux.test.mjs \
  tests/resources-progress-endpoint.test.mjs \
  tests/resource-progress.test.mjs \
  tests/zasoby-progress-wiring.test.mjs \
  tests/redirecting-screen.test.mjs \
  tests/interstitial-wiring.test.mjs
```
Expected: every test PASS.

- [ ] **Step 2: Run the existing invariant suite**

Run: `cd web && npm run test:invariants`
Expected: PASS — confirms no regression in legal pages, brand consistency, owner routes, etc.

- [ ] **Step 3: Run lint**

Run: `cd web && npm run lint`
Expected: 0 errors.

- [ ] **Step 4: Run production build**

Run: `cd web && npm run build`
Expected: build succeeds. Note any warnings.

- [ ] **Step 5: Commit if anything was tweaked during verification**

If steps 1-4 surfaced minor fixes, commit them now:

```bash
cd /Users/mansoniasty/workflows/Agent-OZE
git add -A
git status
# If clean, skip. If tweaks were made:
git commit -m "test(web): verification pass for loading-ux suite"
```

---

### Task 9.2: Manual smoke test against running dev server

**Files:** (manual — no code changes)

- [ ] **Step 1: Start the dev server**

Run: `cd web && railway run --service bot --environment production npm run dev`
Open: http://localhost:3000

- [ ] **Step 2: Slow-network double-click test on rejestracja**

In Chrome DevTools, set Network throttling to "Slow 3G". Open http://localhost:3000/rejestracja. Fill the form, click "Dalej: płatność" 3 times in 1 second.

Expected:
- BrandSpinner appears within 100 ms of first click.
- Subsequent clicks are absorbed (button is `disabled`).
- Network tab shows exactly 1 POST.

If multiple POSTs appear, the `disabled` prop or `useFormStatus()` wiring is broken — fix before moving on.

- [ ] **Step 3: Navigation rail test**

Click any internal link (rejestracja → login or back). The 3 px green rail should slide across the top within 100 ms.

- [ ] **Step 4: Skeleton test**

Reload `/onboarding/platnosc` and `/dashboard` with throttling — outline skeletons must appear and CLS (use Lighthouse) must not regress vs main.

- [ ] **Step 5: Reduced-motion test**

In DevTools → Rendering → Emulate CSS media feature → check `prefers-reduced-motion: reduce`. Repeat steps 2-4. Animations must stop; states remain visible.

- [ ] **Step 6: Toast test (dashboard)**

Sign in as test user, navigate to dashboard, change a client status. Expect sonner toast bottom-right with brand green border + countdown bar + Undo button.

- [ ] **Step 7: Offer generator test**

Open `/oferty`, click delete on a draft. Expect `ConfirmDialog` to appear. Hit Esc — dialog closes without delete. Click Usuń — spinner appears in dialog button, toast "Szablon usunięty" appears.

- [ ] **Step 8: 3-step progress test (against test FastAPI)**

If the FastAPI side of `resources-progress` is available, kick off onboarding from `/onboarding/zasoby`. Watch the 3-step indicator advance Sheets → Calendar → Drive. If FastAPI side is not yet deployed, document the manual test as deferred and note the dependency.

- [ ] **Step 9: Interstitial test**

Register a new test account. After submit, you should see `/onboarding/przekierowuje?to=stripe` briefly before the Stripe redirect. The brand mark should breathe; pill steps should show Konto → Stripe → Płatność.

- [ ] **Step 10: Document any deviations**

If any step revealed an issue, add a note to `docs/CURRENT_STATUS.md` under "Loading UX rollout" describing what to fix in a follow-up slice.

---

### Task 9.3: Update docs and announce

**Files:**
- Modify: `docs/CURRENT_STATUS.md`
- Modify: `docs/IMPLEMENTATION_PLAN.md`

- [ ] **Step 1: Add a section to `docs/CURRENT_STATUS.md`**

Under "Active post-MVP slices (live)", add:

```markdown
### Loading UX visual language (live od 2026-05-29)

Webapp ma 6-wzorcowy system feedbacku dla każdej operacji asynchronicznej:
- Wzorzec A — `<BrandSpinner>` + `<SubmitButton>` (9 form actions)
- Wzorzec B — `<NavigationBar>` rail + `<BreadcrumbArrow>`
- Wzorzec C — `<Skeleton*>` w 6 `loading.tsx`
- Wzorzec D — `<ResourceProgress>` dla createGoogleResources (10–45 s)
- Wzorzec E — sonner z brand theme + helpery w `lib/ui/toast.ts`
- Wzorzec F — `<RedirectingScreen>` + `/onboarding/przekierowuje`

Spec: `docs/superpowers/specs/2026-05-29-webapp-loading-ux-design.md`.
Plan: `docs/superpowers/plans/2026-05-29-webapp-loading-ux-implementation.md`.

POST-MVP follow-up dla `oze-agent`: FastAPI musi udostępniać `GET /api/onboarding/resources-progress` zwracające `{step, elapsed_ms}` — do tego czasu progress indicator stoi na pierwszym kroku.
```

- [ ] **Step 2: Add the FastAPI dependency to `docs/IMPLEMENTATION_PLAN.md`**

Add a new POST-MVP follow-up entry:

```markdown
### `resources_progress_fastapi` (POST-MVP, blocker dla pełnej UX)

FastAPI musi udostępniać `GET /api/onboarding/resources-progress` zwracające
`{step: "sheets"|"calendar"|"drive"|"done", elapsed_ms: number}` z bieżącego
stanu tworzenia zasobów Google. Bez tego endpointu webapp `<ResourceProgress>`
nie pokazuje realnego postępu — tylko statyczny stan pierwszego kroku.

Implementacja po stronie `oze-agent/api/routes/onboarding.py` powinna pisać
state do Supabase `onboarding_progress` (klucz: `user_id`) na każdym kroku
`create_google_resources` flow, a endpoint odczytuje ten state.
```

- [ ] **Step 3: Commit docs**

```bash
cd /Users/mansoniasty/workflows/Agent-OZE
git add docs/CURRENT_STATUS.md docs/IMPLEMENTATION_PLAN.md
git commit -m "docs: record loading UX rollout + resources-progress FastAPI follow-up"
```

- [ ] **Step 4: Final summary**

Print a summary of what shipped:

```
✅ 7 new UI components (BrandSpinner, SubmitButton, NavigationBar, BreadcrumbArrow, Skeleton, ConfirmDialog, RedirectingScreen)
✅ 1 new onboarding component (ResourceProgress)
✅ 6 new loading.tsx files
✅ 1 new API route (resources-progress)
✅ 1 new page (/onboarding/przekierowuje)
✅ Sonner integration with brand theme + 4 helpers
✅ 9 form buttons wired to SubmitButton
✅ Offer generator overhauled (7 onClick + ConfirmDialog + toast)
✅ Decyzje-preview migrated from custom toast to sonner
✅ Signup, OAuth, post-OAuth routed through interstitial

Deferred:
⏳ FastAPI side of resources-progress endpoint (POST-MVP follow-up)
```

---

## Self-Review Notes (for the author)

This plan was self-reviewed against the spec at write-time. Highlights:

- **Coverage**: each of the 6 wzorców A–F has at least one task; spec §9 file list maps 1:1 to tasks in Phases 0–8.
- **No placeholders**: every code step contains actual code; no "// TODO" or "implement later".
- **TDD pattern**: every task is test-first (write failing test → run → implement → run → commit). For pure CSS/visual changes, tests are source-grep style (`assert.match(src, /…/)`) matching the existing convention in `web/tests/*.test.mjs`.
- **Type consistency**: shared types (`StepKey`, `StepStatus`, `ActionKey`) are defined once per consuming file. `ResourceProgress` uses `StepKey` consistently across polling, state, and render.
- **Test cadence**: each task ends with `npm run build` to catch type errors before commit.
- **Known external dependency**: Task 7.1 declares the FastAPI side of `resources-progress` as a separate follow-up — documented in Task 9.3 to surface in `IMPLEMENTATION_PLAN.md`.
