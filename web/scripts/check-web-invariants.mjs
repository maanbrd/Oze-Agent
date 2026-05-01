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
assert.match(
  stripeWebhook,
  /AbortController/,
  "Stripe webhook forwarding must have a timeout guard.",
);
assert.match(
  stripeWebhook,
  /Billing write unavailable/,
  "Stripe webhook forwarding must return a controlled error when FastAPI is unavailable.",
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
const componentFiles = walk("components").filter((file) => file.endsWith(".tsx"));
const appAndComponentSource = [...appFiles, ...componentFiles]
  .map((file) => read(file))
  .join("\n");
const logoutButton = read("components/logout-button.tsx");
assert.match(
  logoutButton,
  /logout/,
  "Logged-in UI must expose the logout server action.",
);
assert.match(
  read("components/app-shell.tsx"),
  /LogoutButton/,
  "App shell must render a logout button for authenticated pages.",
);
assert.match(
  read("app/onboarding/layout.tsx"),
  /LogoutButton/,
  "Onboarding pages must render a logout button while a user is mid-flow.",
);
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
const blankTargetTags =
  appAndComponentSource.match(/<a\b[^>]*target=["']_blank["'][^>]*>/g) ?? [];
for (const tag of blankTargetTags) {
  assert.match(
    tag,
    /rel=["']noopener noreferrer["']/,
    `External link opening a new tab must use rel="noopener noreferrer": ${tag}`,
  );
}
assert.doesNotMatch(
  appAndComponentSource,
  /href=\{[^}]*\?\?\s*"#"/,
  "App routes must not render missing external URLs as href=\"#\".",
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
const accountHelper = read("lib/api/account.ts");
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
assert.match(
  accountHelper,
  /AbortController/,
  "Account profile fetches must have a timeout guard.",
);
assert.match(
  accountHelper,
  /Nie udało się połączyć z API konta/,
  "Account profile fetch failures must return a controlled Polish error.",
);
assert.match(
  onboardingHelper,
  /AbortController/,
  "Onboarding API fetches must have a timeout guard.",
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

const googleSuccessPage = read("app/onboarding/google/sukces/page.tsx");
assert.match(
  googleSuccessPage,
  /requireCurrentAccount/,
  "Google OAuth success page must require an authenticated account.",
);
assert.match(
  googleSuccessPage,
  /steps\.google/,
  "Google OAuth success page must not claim success before onboarding status confirms Google tokens.",
);

for (const route of [
  "app/onboarding/sukces/page.tsx",
  "app/onboarding/anulowano/page.tsx",
]) {
  assert.match(
    read(route),
    /getCurrentAccount/,
    `${route} must require an authenticated account before showing payment return state.`,
  );
  assert.match(
    read(route),
    /\/login\?next=\/onboarding\/platnosc/,
    `${route} must redirect anonymous users back through payment onboarding.`,
  );
}

const paymentSuccessPage = read("app/onboarding/sukces/page.tsx");
assert.match(
  paymentSuccessPage,
  /subscription_status.*active|active.*subscription_status/s,
  "Payment success page must not claim activation before the webhook marks the subscription active.",
);

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
assert.match(
  crmAdapters,
  /catch/,
  "CRM adapter must catch FastAPI fetch failures and preserve source-state UI.",
);
assert.match(
  crmAdapters,
  /trustedExternalUrl/,
  "CRM adapter must validate Google Workspace links before rendering them.",
);
for (const origin of [
  "https://docs.google.com",
  "https://calendar.google.com",
  "https://drive.google.com",
]) {
  assert.match(
    crmAdapters,
    new RegExp(origin.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")),
    `CRM adapter must allow ${origin} links only through the trusted URL helper.`,
  );
}

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
assert.match(
  settingsPage,
  /params\.message/,
  "Settings must render account update errors from the server action redirect.",
);

const onboardingActions = read("app/onboarding/actions.ts");
assert.match(
  onboardingActions,
  /trustedExternalUrl/,
  "Onboarding server actions must validate external redirect targets.",
);
assert.match(
  onboardingActions,
  /https:\/\/checkout\.stripe\.com/,
  "Stripe Checkout redirects must be limited to checkout.stripe.com.",
);
assert.match(
  onboardingActions,
  /https:\/\/accounts\.google\.com/,
  "Google OAuth redirects must be limited to accounts.google.com.",
);
for (const action of [
  "startGoogleOAuthAction",
  "createGoogleResourcesAction",
  "generateTelegramCodeAction",
  "updateAccountAction",
]) {
  assert.match(
    onboardingActions,
    new RegExp(`export async function ${action}[\\s\\S]*?catch`),
    `${action} must redirect with a user-facing message instead of surfacing a raw Next.js error page.`,
  );
}

for (const route of [
  "app/onboarding/google/page.tsx",
  "app/onboarding/zasoby/page.tsx",
  "app/onboarding/telegram/page.tsx",
]) {
  assert.match(
    read(route),
    /params\.message/,
    `${route} must render onboarding action errors from redirects.`,
  );
}

const onboardingGate = read("components/onboarding-gate.tsx");
const appShell = read("components/app-shell.tsx");
const appLayout = read("app/(app)/layout.tsx");
assert.match(
  onboardingGate,
  /nextStep/,
  "Onboarding gate must link to the next step.",
);
assert.match(
  onboardingGate,
  /safeLocalPath/,
  "Onboarding gate must sanitize the next step returned by the backend.",
);
assert.match(
  appShell,
  /OnboardingGate/,
  "App shell must render onboarding gate.",
);
assert.match(
  appShell,
  /encodeURIComponent/,
  "Google quick links must encode resource IDs before placing them in hrefs.",
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
assert.match(
  telegramPage,
  /Rejestracja ukończona/,
  "Telegram onboarding must explicitly confirm completed registration after pairing.",
);
assert.match(
  telegramPage,
  /\/dashboard\?onboarding=complete/,
  "Telegram onboarding must return completed users to the dashboard with a completion flag.",
);

const dashboardPage = read("app/(app)/dashboard/page.tsx");
assert.match(
  dashboardPage,
  /onboarding.*complete/s,
  "Dashboard must handle the onboarding completion flag.",
);
assert.match(
  dashboardPage,
  /Rejestracja ukończona.*płatność.*Google.*Telegram/s,
  "Dashboard must show a complete onboarding banner after redirecting back.",
);
assert.match(
  dashboardPage,
  /warsawDateKey/,
  "Dashboard must compute today's key in Europe/Warsaw.",
);
assert.match(
  dashboardPage,
  /warsawDateKeyFromIso/,
  "Dashboard must compare CRM event/action dates in Europe/Warsaw.",
);
assert.doesNotMatch(
  dashboardPage,
  /todayKey\s*=\s*"2026-04-29"/,
  "Dashboard must not hardcode the Phase 1B smoke date as today.",
);
assert.doesNotMatch(
  dashboardPage,
  /\+02:00/,
  "Dashboard must not hardcode Warsaw's daylight-saving offset.",
);

const calendarPage = read("app/(app)/kalendarz/page.tsx");
assert.match(
  calendarPage,
  /formatWarsawDayLabel/,
  "Calendar must format day labels in Europe/Warsaw.",
);
assert.match(
  calendarPage,
  /formatWarsawTime/,
  "Calendar must format event times in Europe/Warsaw.",
);
assert.doesNotMatch(
  calendarPage,
  /\+02:00/,
  "Calendar must not hardcode Warsaw's daylight-saving offset.",
);

const routeHelper = read("lib/routes.ts");
const loginPage = read("app/login/page.tsx");
const authActions = read("app/auth/actions.ts");
assert.match(
  routeHelper,
  /safeLocalPath/,
  "Web must centralize safe local redirect sanitization.",
);
assert.match(
  routeHelper,
  /trustedExternalUrl/,
  "Web must centralize trusted external redirect validation.",
);
assert.match(
  routeHelper,
  /startsWith\(\"\/\/\"\)/,
  "Safe local redirect helper must reject protocol-relative URLs.",
);
assert.match(
  routeHelper,
  /\\u0000-\\u001F\\u007F/,
  "Safe local redirect helper must reject control characters.",
);
assert.match(
  routeHelper,
  /parsed\.protocol !== "https:"/,
  "Trusted external redirect helper must require https URLs.",
);
assert.match(
  loginPage,
  /safeLocalPath/,
  "Login page must sanitize next before rendering or redirecting.",
);
assert.match(
  authActions,
  /safeLocalPath/,
  "Login action must sanitize next before redirecting.",
);
assert.match(
  authActions,
  /encodedWithNext/,
  "Login action must preserve safe next target after failed login.",
);
assert.doesNotMatch(
  loginPage + "\n" + authActions,
  /next\.startsWith\("\/"\)/,
  "Login flow must not use broad next.startsWith('/') redirect checks.",
);

const packageJson = JSON.parse(read("package.json"));
const healthRoute = read("app/healthz/route.ts");
assert.match(
  healthRoute,
  /phase:\s*"1B"/,
  "Web health route must identify Phase 1B readiness.",
);
assert.match(
  healthRoute,
  /readiness:\s*"phase1b-web"/,
  "Web health route must identify web readiness scope.",
);

assert.equal(
  packageJson.scripts["test:dates"],
  "node scripts/test-dates.mjs",
  "Web package must expose Warsaw date helper behavior tests.",
);
assert.equal(
  packageJson.scripts["test:routes"],
  "node scripts/test-routes.mjs",
  "Web package must expose route helper behavior tests.",
);
assert.equal(
  packageJson.scripts["test:web-units"],
  "npm run test:routes && npm run test:dates && npm run test:api-base-url",
  "Web package must expose combined web unit tests.",
);
assert.equal(
  packageJson.scripts["test:api-base-url"],
  "node scripts/test-api-base-url.mjs",
  "Web package must expose FastAPI base URL normalization tests.",
);
assert.equal(
  packageJson.scripts["check:phase1b-env"],
  "node scripts/check-phase1b-env.mjs",
  "Web package must expose the Phase 1B env checker.",
);
assert.equal(
  packageJson.scripts["smoke:phase1b-local"],
  "node scripts/smoke-phase1b-local.mjs",
  "Web package must expose the Phase 1B local smoke checker.",
);

const phase1bEnvChecker = read("scripts/check-phase1b-env.mjs");
assert.match(
  phase1bEnvChecker,
  /NEXT_PUBLIC_SUPABASE_URL/,
  "Phase 1B env checker must require Supabase URL.",
);
assert.match(
  phase1bEnvChecker,
  /--env-file/,
  "Phase 1B env checker must support explicit env files for local readiness.",
);
assert.match(
  phase1bEnvChecker,
  /\.env\.local/,
  "Phase 1B env checker must load local dotenv files.",
);
assert.match(
  phase1bEnvChecker,
  /STRIPE_WEBHOOK_SECRET/,
  "Phase 1B env checker must know staging webhook secret requirements.",
);
assert.match(
  phase1bEnvChecker,
  /must use https in staging/,
  "Phase 1B env checker must reject non-HTTPS staging URLs.",
);
assert.match(
  phase1bEnvChecker,
  /must be a valid URL/,
  "Phase 1B env checker must validate URL-shaped environment values.",
);
assert.match(
  phase1bEnvChecker,
  /SUPABASE_SERVICE_KEY must not be configured/,
  "Phase 1B env checker must block Supabase service keys in web env.",
);

const phase1bLocalSmoke = read("scripts/smoke-phase1b-local.mjs");
assert.match(
  phase1bLocalSmoke,
  /\/healthz/,
  "Phase 1B local smoke must check the web health route.",
);
assert.match(
  phase1bLocalSmoke,
  /phase1b-web/,
  "Phase 1B local smoke must verify the health readiness marker.",
);
for (const route of [
  "/dashboard",
  "/klienci",
  "/kalendarz",
  "/platnosci",
  "/ustawienia",
  "/import",
  "/instrukcja",
  "/faq",
]) {
  assert.match(
    phase1bLocalSmoke,
    new RegExp(route.replace("/", "\\/")),
    `Phase 1B local smoke must check anonymous redirect for ${route}.`,
  );
}
for (const route of ["/onboarding/sukces", "/onboarding/anulowano"]) {
  assert.match(
    phase1bLocalSmoke,
    new RegExp(route.replace("/", "\\/")),
    `Phase 1B local smoke must check anonymous payment return redirect for ${route}.`,
  );
}
assert.match(
  phase1bLocalSmoke,
  /\/onboarding\/google\/sukces/,
  "Phase 1B local smoke must check anonymous Google success redirect.",
);
assert.match(
  phase1bLocalSmoke,
  /CRM mutation forms/,
  "Phase 1B local smoke must check the no-CRM-mutation boundary.",
);

console.log("web invariants passed");
