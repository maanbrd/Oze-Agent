import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const src = readSource("../components/dashboard/decyzje-preview.tsx");

test("decyzje-preview uses sonner-backed helpers", () => {
  assert.match(src, /from\s+['"]@\/lib\/ui\/toast['"]/);
  assert.match(src, /showSuccess|showError|showAction/);
});

test("decyzje-preview no longer maintains its own ToastState", () => {
  // Custom local toast type removed in favor of sonner.
  assert.equal(src.includes("type ToastState"), false);
});
