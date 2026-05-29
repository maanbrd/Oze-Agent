import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const helpersSrc = readSource("../lib/ui/toast.ts");
const toasterSrc = readSource("../components/ui/brand-toaster.tsx");
const layoutSrc = readSource("../app/layout.tsx");

test("toast.ts exports showSuccess, showError, showAction, showPromise", () => {
  for (const fn of ["showSuccess", "showError", "showAction", "showPromise"]) {
    assert.match(helpersSrc, new RegExp(`export\\s+(const|function)\\s+${fn}`));
  }
});

test("toast helpers import from sonner", () => {
  assert.match(helpersSrc, /from\s+['"]sonner['"]/);
});

test("BrandToaster wraps sonner Toaster with brand theme", () => {
  assert.match(toasterSrc, /from\s+['"]sonner['"]/);
  assert.match(toasterSrc, /#3DFF7A/);
});

test("layout.tsx mounts BrandToaster", () => {
  assert.match(layoutSrc, /BrandToaster/);
});
