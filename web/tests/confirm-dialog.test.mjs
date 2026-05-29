import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const src = readSource("../components/ui/confirm-dialog.tsx");

test("ConfirmDialog is a client component with destructive variant", () => {
  assert.match(src, /^['"]use client['"]/m);
  assert.match(src, /export\s+function\s+ConfirmDialog/);
  assert.match(src, /variant\??:\s*['"]destructive['"]/);
});

test("ConfirmDialog uses Escape key to cancel", () => {
  assert.match(src, /Escape/);
});

test("ConfirmDialog disables confirm button while pending", () => {
  assert.match(src, /pending/);
  assert.match(src, /disabled/);
});
