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
