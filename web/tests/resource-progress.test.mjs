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
