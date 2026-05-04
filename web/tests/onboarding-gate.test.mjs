import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const homePageSource = readSource("../app/page.tsx");
const dashboardPageSource = readSource("../app/dashboard/page.tsx");
const offersPageSource = readSource("../app/oferty/page.tsx");
const guardSource = readSource("../lib/auth/guards.ts");
const loginPageSource = readSource("../app/login/page.tsx");
const paymentPageSource = readSource("../app/onboarding/platnosc/page.tsx");
const googlePageSource = readSource("../app/onboarding/google/page.tsx");
const resourcesPageSource = readSource("../app/onboarding/zasoby/page.tsx");
const telegramPageSource = readSource("../app/onboarding/telegram/page.tsx");

test("private app pages require completed onboarding", () => {
  assert.match(dashboardPageSource, /requireCompletedOnboarding\("\/dashboard"\)/);
  assert.match(offersPageSource, /requireCompletedOnboarding\("\/oferty"\)/);
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
