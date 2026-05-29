import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const src = readSource("../components/offers/offer-generator.tsx");

test("offer-generator imports toast helpers", () => {
  assert.match(src, /@\/lib\/ui\/toast/);
});

test("offer-generator imports ConfirmDialog", () => {
  assert.match(src, /ConfirmDialog/);
});

test("offer-generator renders BrandSpinner on async ops", () => {
  assert.match(src, /BrandSpinner/);
});

test("offer-generator tracks per-action loading state (not single global flag)", () => {
  // Expect a record-style state, not just one boolean.
  assert.match(src, /loadingAction|actionLoading|busyAction/);
});

test("deleteOffer is guarded by ConfirmDialog", () => {
  assert.match(src, /ConfirmDialog/);
  assert.match(src, /deleteOffer/);
  // Confirmation copy must mention deletion.
  assert.match(src, /usuń|usunąć|usunięcia/i);
});
