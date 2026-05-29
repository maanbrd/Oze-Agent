import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const src = readSource("../components/ui/breadcrumb-arrow.tsx");

test("BreadcrumbArrow renders SVG with crawling dash animation", () => {
  assert.match(src, /export\s+function\s+BreadcrumbArrow/);
  assert.match(src, /stroke-dasharray|strokeDasharray/);
  assert.match(src, /@keyframes\s+breadcrumb-crawl/);
});

test("BreadcrumbArrow uses brand green", () => {
  assert.match(src, /#3DFF7A/);
});

test("BreadcrumbArrow respects reduced-motion", () => {
  assert.match(src, /prefers-reduced-motion:\s*reduce/);
});
