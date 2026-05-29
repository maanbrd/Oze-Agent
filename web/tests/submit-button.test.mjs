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
