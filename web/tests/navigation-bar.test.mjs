import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const src = readSource("../components/ui/navigation-bar.tsx");

test("NavigationBar is a client component", () => {
  assert.match(src, /^['"]use client['"]/m);
});

test("NavigationBar exposes manual show() via context or props", () => {
  assert.match(src, /useNavigationProgress|NavigationProgressProvider/);
});

test("NavigationBar uses brand green and slides on top of viewport", () => {
  assert.match(src, /#3DFF7A/);
  // JSX style object uses quoted string values: position: "fixed"
  assert.match(src, /position:\s*["']?fixed["']?/);
  assert.match(src, /top:\s*0/);
});

test("NavigationBar respects prefers-reduced-motion", () => {
  assert.match(src, /prefers-reduced-motion:\s*reduce/);
});
