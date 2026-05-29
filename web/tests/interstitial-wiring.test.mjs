import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const authSrc = readSource("../app/auth/actions.ts");
const onboardingSrc = readSource("../app/onboarding/actions.ts");

test("signup redirects to /onboarding/platnosc (plan choice screen, not interstitial)", () => {
  // Signup lands on the plan-choice screen so the user can pick beta vs paid.
  // The interstitial is triggered by the plan choice itself, not the signup.
  assert.match(authSrc, /redirect\(['"]\/onboarding\/platnosc['"]\)/);
  assert.equal(authSrc.includes("przekierowuje?to=stripe"), false);
});

test("createCheckoutSession redirects via przekierowuje?to=stripe (or directly to Stripe URL)", () => {
  // After interstitial change, checkout action is now hit from interstitial page;
  // it directly redirects to Stripe.
  assert.match(onboardingSrc, /checkout\.stripe\.com|stripe\.checkout/);
});

test("startGoogleOAuthAction redirects via przekierowuje?to=google", () => {
  assert.match(onboardingSrc, /przekierowuje\?to=google/);
});
