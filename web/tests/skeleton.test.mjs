import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const src = readSource("../components/ui/skeleton.tsx");

test("Skeleton primitives export SkeletonLine, SkeletonCard, SkeletonCta", () => {
  assert.match(src, /export\s+function\s+SkeletonLine/);
  assert.match(src, /export\s+function\s+SkeletonCard/);
  assert.match(src, /export\s+function\s+SkeletonCta/);
});

test("SkeletonLine variants cover title | sub | body", () => {
  assert.match(src, /variant\??:\s*['"]title['"]\s*\|\s*['"]sub['"]\s*\|\s*['"]body['"]/);
});

test("Skeleton uses outline pulse with brand green, not gray blocks", () => {
  assert.match(src, /#3DFF7A/);
  assert.match(src, /border:/);
});

test("Skeleton respects prefers-reduced-motion", () => {
  assert.match(src, /prefers-reduced-motion:\s*reduce/);
});
