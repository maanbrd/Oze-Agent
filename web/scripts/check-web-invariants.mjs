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
assert.match(
  stripeWebhook,
  /Live Stripe events are disabled|live mode/i,
  "Stripe webhook must reject live-mode events.",
);

const crmAdapter = read("lib/crm/adapters.ts");
assert.match(crmAdapter, /sheets/i, "CRM adapter must model Sheets as client source.");
assert.match(crmAdapter, /calendar/i, "CRM adapter must model Calendar as event source.");
assert.doesNotMatch(
  crmAdapter,
  /\.insert\(|\.update\(|\.delete\(/,
  "CRM adapter must be read-only.",
);

const crmNotice = read("components/crm-notice.tsx");
assert.match(
  crmNotice,
  /Sheets.*Calendar|Calendar.*Sheets/,
  "CRM notice must say edits happen in Sheets and Calendar.",
);

const appFiles = walk("app").filter((file) => file.endsWith(".tsx"));
const appSource = appFiles.map((file) => read(file)).join("\n");
assert.match(
  appSource,
  /CRM|Sheets|Calendar|Google/,
  "App UI must mention CRM/Google edit boundary.",
);
assert.doesNotMatch(
  appSource,
  /action=\{.*addClient|action=\{.*updateClient|name="status"/s,
  "App UI must not expose CRM mutation forms.",
);

for (const route of [
  "app/(app)/dashboard/page.tsx",
  "app/(app)/klienci/page.tsx",
  "app/(app)/kalendarz/page.tsx",
]) {
  assert.match(
    read(route),
    /getCrmDashboardData|CrmNotice|DataFreshnessBadge/,
    `${route} must use CRM read-only primitives.`,
  );
}

for (const route of [
  "app/(app)/platnosci/page.tsx",
  "app/(app)/ustawienia/page.tsx",
  "app/(app)/import/page.tsx",
  "app/(app)/instrukcja/page.tsx",
  "app/(app)/faq/page.tsx",
]) {
  assert.ok(read(route).length > 200, `${route} must be implemented.`);
}

const onboardingHelper = read("lib/api/onboarding.ts");
assert.match(
  onboardingHelper,
  /getOnboardingStatus/,
  "Web must have onboarding status helper.",
);
assert.match(
  onboardingHelper,
  /startGoogleOAuth/,
  "Web must have Google OAuth helper.",
);
assert.match(
  onboardingHelper,
  /createGoogleResources/,
  "Web must have resource creation helper.",
);
assert.match(
  onboardingHelper,
  /generateTelegramCode/,
  "Web must have Telegram code helper.",
);
assert.doesNotMatch(
  appSource,
  new RegExp("Przelewy" + "24", "i"),
  "Web UI must not mention the retired payment provider.",
);

for (const route of [
  "app/onboarding/google/page.tsx",
  "app/onboarding/google/sukces/page.tsx",
  "app/onboarding/zasoby/page.tsx",
  "app/onboarding/telegram/page.tsx",
]) {
  assert.match(
    read(route),
    /onboarding|Google|Telegram|Sheets|Calendar|Drive/i,
    `${route} must implement onboarding UI.`,
  );
}

const crmTypes = read("lib/crm/types.ts");
const crmAdapters = read("lib/crm/adapters.ts");
assert.match(crmTypes, /CrmSourceState/, "CRM DTOs must include source state.");
assert.match(crmAdapters, /unavailable/, "CRM adapter must expose unavailable state.");
assert.match(crmAdapters, /demo/, "CRM adapter must expose demo state.");
assert.match(
  crmAdapters,
  /completed/,
  "CRM adapter must consider onboarding completion before demo fallback.",
);

const settingsPage = read("app/(app)/ustawienia/page.tsx");
assert.match(
  settingsPage,
  /updateAccountAction/,
  "Settings must use account-only update action.",
);
assert.doesNotMatch(
  settingsPage,
  /google_sheets_id|google_calendar_id|Status klienta|Notatki klienta/,
  "Settings must not edit CRM fields.",
);

const onboardingGate = read("components/onboarding-gate.tsx");
const appShell = read("components/app-shell.tsx");
const appLayout = read("app/(app)/layout.tsx");
assert.match(
  onboardingGate,
  /nextStep/,
  "Onboarding gate must link to the next step.",
);
assert.match(
  appShell,
  /OnboardingGate/,
  "App shell must render onboarding gate.",
);
assert.match(
  appLayout,
  /getOnboardingStatus/,
  "Logged-in layout must fetch onboarding status.",
);

const telegramPage = read("app/onboarding/telegram/page.tsx");
assert.match(
  telegramPage,
  /\/start/,
  "Telegram onboarding must show /start code command.",
);

const packageJson = JSON.parse(read("package.json"));
assert.equal(
  packageJson.scripts["check:phase1b-env"],
  "node scripts/check-phase1b-env.mjs",
  "Web package must expose the Phase 1B env checker.",
);

const phase1bEnvChecker = read("scripts/check-phase1b-env.mjs");
assert.match(
  phase1bEnvChecker,
  /NEXT_PUBLIC_SUPABASE_URL/,
  "Phase 1B env checker must require Supabase URL.",
);
assert.match(
  phase1bEnvChecker,
  /STRIPE_WEBHOOK_SECRET/,
  "Phase 1B env checker must know staging webhook secret requirements.",
);

console.log("web invariants passed");
