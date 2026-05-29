import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const globalsCss = readSource("../app/globals.css");
const packageJson = readSource("../package.json");

test("globals.css defines brand loading-ux tokens", () => {
  assert.match(globalsCss, /--brand-green:\s*#3dff7a/i);
  assert.match(globalsCss, /--brand-bg:\s*#0b0d10/i);
  assert.match(globalsCss, /--brand-bg-deep:\s*#050607/i);
  assert.match(globalsCss, /--ui-border-dim:\s*#1f242b/i);
  assert.match(globalsCss, /--state-error:\s*#ff6464/i);
  assert.match(globalsCss, /--brand-bg-inset:\s*#060709/i);
  assert.match(globalsCss, /--ui-text-primary:\s*#f5f7fa/i);
  assert.match(globalsCss, /--ui-text-muted:\s*#6b7280/i);
  assert.match(globalsCss, /--ui-text-deep:\s*#4a5460/i);
  assert.match(globalsCss, /--state-neutral:\s*#9aa5b1/i);
});

test("globals.css respects prefers-reduced-motion globally", () => {
  assert.match(globalsCss, /@media\s*\(prefers-reduced-motion:\s*reduce\)/);
  assert.match(globalsCss, /\.motion-safe-only/);
  assert.match(globalsCss, /animation:\s*none\s*!important/);
});

test("sonner is installed as a dependency", () => {
  const pkg = JSON.parse(packageJson);
  assert.ok(pkg.dependencies.sonner, "expected sonner in dependencies");
});
