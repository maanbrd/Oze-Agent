import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const homePageSource = readSource("../app/page.tsx");
const flatDashboardPath = new URL("../app/dashboard/page.tsx", import.meta.url);
const flatOffersPath = new URL("../app/oferty/page.tsx", import.meta.url);
const crmLayoutSource = readSource("../app/(app)/layout.tsx");
const dashboardPageSource = readSource("../app/(app)/dashboard/page.tsx");
const offersPageSource = readSource("../app/(app)/oferty/page.tsx");
const crmShellSource = readSource("../components/crm-shell.tsx");
const guardSource = readSource("../lib/auth/guards.ts");
const loginPageSource = readSource("../app/login/page.tsx");
const onboardingActionsSource = readSource("../app/onboarding/actions.ts");
const onboardingApiSource = readSource("../lib/api/onboarding.ts");
const apiBaseUrlSource = readSource("../lib/api/base-url.ts");
const paymentPageSource = readSource("../app/onboarding/platnosc/page.tsx");
const googlePageSource = readSource("../app/onboarding/google/page.tsx");
const resourcesPageSource = readSource("../app/onboarding/zasoby/page.tsx");
const telegramPageSource = readSource("../app/onboarding/telegram/page.tsx");
const stripeServerSource = readSource("../lib/stripe/server.ts");
const stripeWebhookRouteSource = readSource("../app/api/webhooks/stripe/route.ts");
const checkoutRouteSource = readSource("../app/onboarding/checkout/route.ts");
const paymentSuccessPageSource = readSource("../app/onboarding/sukces/page.tsx");
const checkoutReconcileSource = readSource("../lib/billing/checkout-reconcile.ts");
const stripeEventForwardSource = readSource("../lib/billing/stripe-events.ts");
const logoutRouteSource = readSource("../app/logout/route.ts");
const accountSource = readSource("../lib/api/account.ts");
const packageJsonSource = readSource("../package.json");
const envPullScriptSource = readSource("../scripts/pull-vercel-env-safe.mjs");
const proxySource = readSource("../proxy.ts");
const supabaseProxySource = readSource("../lib/supabase/proxy.ts");

test("private app pages require completed onboarding", () => {
  assert.equal(existsSync(flatDashboardPath), false);
  assert.match(crmLayoutSource, /getCurrentAccount/);
  assert.match(crmLayoutSource, /redirect\("\/login\?next=\/dashboard"\)/);
  assert.match(crmLayoutSource, /getOnboardingStatus/);
  assert.match(crmLayoutSource, /account\.profile\?\.onboarding_completed/);
  assert.match(crmLayoutSource, /safeLocalPath\(onboardingStatus\?\.nextStep, "\/onboarding\/platnosc"\)/);
  assert.match(dashboardPageSource, /getCrmDashboardData/);
  assert.equal(existsSync(flatOffersPath), false);
  assert.match(offersPageSource, /<OfferGenerator \/>/);
});

test("offer generator route is inside the CRM shell", () => {
  assert.match(crmShellSource, /\["Oferty", "\/oferty"\]/);
  assert.match(crmLayoutSource, /<CrmShell account=\{account\}>/);
  assert.equal(offersPageSource.includes("AppShell"), false);
  assert.equal(offersPageSource.includes("requireCompletedOnboarding"), false);
});

test("landing page remains public and does not use the private app gate", () => {
  assert.equal(homePageSource.includes("requireCompletedOnboarding"), false);
  assert.equal(homePageSource.includes("getCurrentAccount"), false);
  assert.match(homePageSource, /<Landing \/>/);
});

test("central gate redirects unauthenticated and incomplete accounts correctly", () => {
  assert.match(guardSource, /redirect\(`\/login\?next=\$\{encodeURIComponent\(currentPath\)\}`\)/);
  assert.match(guardSource, /getOnboardingStatus/);
  assert.match(guardSource, /safeLocalPath\(status\?\.nextStep, "\/onboarding\/platnosc"\)/);
  assert.match(guardSource, /account\.profile\?\.onboarding_completed/);
});

test("login preserves next path without bypassing onboarding gate", () => {
  assert.match(loginPageSource, /safeLocalPath\(params\.next\)/);
  assert.match(loginPageSource, /name="next"/);
  assert.equal(loginPageSource.includes('"/oferty"'), false);
});

test("account auth uses the Supabase user as the source of truth", () => {
  const getUserIndex = accountSource.indexOf("auth.getUser()");
  const getSessionIndex = accountSource.indexOf("auth.getSession()");

  assert.notEqual(getUserIndex, -1);
  assert.notEqual(getSessionIndex, -1);
  assert.ok(getUserIndex < getSessionIndex);
  assert.equal(accountSource.includes("auth.getClaims()"), false);
  assert.match(accountSource, /const authUserId = userData\.user\.id/);
  assert.match(accountSource, /const authEmail = userData\.user\.email \?\? null/);
  assert.match(accountSource, /fetchProfileFromSupabase\(supabase, authUserId\)/);
  assert.match(accountSource, /authenticated: true/);
});

test("full onboarding routes exist", () => {
  for (const path of [
    "../app/onboarding/platnosc/page.tsx",
    "../app/onboarding/sukces/page.tsx",
    "../app/onboarding/anulowano/page.tsx",
    "../app/onboarding/google/page.tsx",
    "../app/onboarding/google/sukces/page.tsx",
    "../app/onboarding/zasoby/page.tsx",
    "../app/onboarding/telegram/page.tsx",
  ]) {
    assert.equal(existsSync(new URL(path, import.meta.url)), true, path);
  }
});

test("onboarding steps enforce sequence and cannot be opened through a stale next param", () => {
  assert.match(guardSource, /requireOnboardingStep/);
  assert.match(guardSource, /status\?\.nextStep/);
  assert.match(guardSource, /redirect\(resolvedNextStep\)/);
  assert.match(paymentPageSource, /requireOnboardingStep\("\/onboarding\/platnosc"\)/);
  assert.match(googlePageSource, /requireOnboardingStep\("\/onboarding\/google"\)/);
  assert.match(resourcesPageSource, /requireOnboardingStep\("\/onboarding\/zasoby"\)/);
  assert.match(telegramPageSource, /requireOnboardingStep\("\/onboarding\/telegram"\)/);
});

test("Google OAuth starts with the current preview success URL", () => {
  assert.match(onboardingActionsSource, /resolveCheckoutReturnBaseUrl/);
  assert.match(onboardingActionsSource, /startGoogleOAuth\(`\$\{returnBaseUrl\}\/onboarding\/google\/sukces`\)/);
  assert.match(onboardingApiSource, /returnUrl\?: string/);
  assert.match(onboardingApiSource, /body: JSON\.stringify\(\{ returnUrl \}\)/);
});

test("stripe checkout returns to the current request origin, not a stale preview URL", () => {
  assert.match(onboardingActionsSource, /import \{ headers \} from "next\/headers"/);
  assert.match(onboardingActionsSource, /resolveCheckoutReturnBaseUrl/);
  assert.match(onboardingActionsSource, /hostname\.endsWith\("\.vercel\.app"\)/);
  assert.match(onboardingActionsSource, /success_url: `\$\{returnBaseUrl\}\/onboarding\/sukces/);
  assert.match(onboardingActionsSource, /cancel_url: `\$\{returnBaseUrl\}\/onboarding\/anulowano`/);
  assert.equal(onboardingActionsSource.includes("success_url: `${appUrl}/"), false);
  assert.match(stripeServerSource, /envValue\("NEXT_PUBLIC_APP_URL"\)/);
});

test("payment plans use a route handler post so checkout keeps browser cookies", () => {
  assert.equal(paymentPageSource.includes("action={createCheckoutSession}"), false);
  assert.match(paymentPageSource, /action="\/onboarding\/checkout"/);
  assert.match(paymentPageSource, /method="post"/);
  assert.match(checkoutRouteSource, /export async function POST/);
  assert.match(checkoutRouteSource, /getCurrentAccount/);
  assert.match(checkoutRouteSource, /NextResponse\.redirect/);
});

test("stripe checkout reports actionable configuration failures", () => {
  assert.match(stripeServerSource, /envValue\("STRIPE_SECRET_KEY"\)/);
  assert.match(stripeServerSource, /export function envValue/);
  assert.match(stripeServerSource, /value === `""`/);
  assert.match(stripeServerSource, /checkoutConfigErrorMessage/);
  assert.match(stripeServerSource, /Missing STRIPE_SECRET_KEY/);
  assert.match(stripeServerSource, /web\/\.env\.local mógł zostać nadpisany/);
  assert.match(stripeServerSource, /No active Stripe price found for lookup key/);
  assert.match(onboardingActionsSource, /checkoutConfigErrorMessage\(error\)/);
});

test("stripe webhook treats blank env values as missing configuration", () => {
  assert.match(stripeWebhookRouteSource, /envValue\("STRIPE_WEBHOOK_SECRET"\)/);
  assert.match(stripeEventForwardSource, /envValue\("BILLING_INTERNAL_SECRET"\)/);
  assert.match(stripeEventForwardSource, /envValue\("FASTAPI_INTERNAL_BASE_URL"\)/);
  assert.equal(stripeWebhookRouteSource.includes("process.env.STRIPE_WEBHOOK_SECRET"), false);
  assert.match(stripeWebhookRouteSource, /Webhook not configured/);
});

test("payment success reconciles a paid Checkout session before waiting for webhook", () => {
  assert.match(paymentSuccessPageSource, /searchParams: Promise<\{ session_id\?: string \}>/);
  assert.match(paymentSuccessPageSource, /reconcileCheckoutSession\(params\.session_id\)/);
  assert.match(checkoutReconcileSource, /stripe\.checkout\.sessions\.retrieve\(sessionId\)/);
  assert.match(checkoutReconcileSource, /session\.status === "complete"/);
  assert.match(checkoutReconcileSource, /session\.payment_status === "paid"/);
  assert.match(checkoutReconcileSource, /session\.client_reference_id === profile\.id/);
  assert.match(checkoutReconcileSource, /session\.metadata\?\.auth_user_id === profile\.auth_user_id/);
  assert.match(checkoutReconcileSource, /type: "checkout\.session\.completed"/);
  assert.match(checkoutReconcileSource, /forwardStripeEventToFastApi/);
});

test("FastAPI base URL ignores blank quoted env values before using fallback", () => {
  assert.match(apiBaseUrlSource, /trimmed === `""`/);
  assert.match(apiBaseUrlSource, /normalizeFastApiBaseUrl\(process\.env\.FASTAPI_INTERNAL_BASE_URL\) \|\|/);
  assert.match(apiBaseUrlSource, /normalizeFastApiBaseUrl\(process\.env\.NEXT_PUBLIC_API_BASE_URL\)/);
});

test("local Vercel env pull protects the existing env file first", () => {
  assert.match(packageJsonSource, /"env:pull": "node scripts\/pull-vercel-env-safe\.mjs"/);
  assert.match(envPullScriptSource, /copyFileSync\(targetPath, backupPath\)/);
  assert.match(envPullScriptSource, /\/tmp\/agent-oze-env-backups/);
  assert.match(envPullScriptSource, /"env", "pull"/);
  assert.match(envPullScriptSource, /removedBlankLines/);
  assert.match(envPullScriptSource, /return !isBlank/);
});

test("onboarding has a direct logout route for stuck browser sessions", () => {
  assert.match(logoutRouteSource, /auth\.signOut\(\)/);
  assert.match(logoutRouteSource, /NextResponse\.redirect\(url\)/);
  assert.match(paymentPageSource, /<LogoutLink \/>/);
  assert.match(googlePageSource, /<LogoutLink \/>/);
  assert.match(resourcesPageSource, /<LogoutLink \/>/);
  assert.match(telegramPageSource, /<LogoutLink \/>/);
});

test("Supabase SSR proxy persists auth cookies across server actions", () => {
  assert.match(proxySource, /export async function proxy/);
  assert.match(proxySource, /updateSession\(request\)/);
  assert.match(proxySource, /matcher/);
  assert.match(supabaseProxySource, /createServerClient/);
  assert.match(supabaseProxySource, /request\.cookies\.set/);
  assert.match(supabaseProxySource, /response\.cookies\.set/);
  assert.match(supabaseProxySource, /auth\.getClaims\(\)/);
});
