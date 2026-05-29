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
