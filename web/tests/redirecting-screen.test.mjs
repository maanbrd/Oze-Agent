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
