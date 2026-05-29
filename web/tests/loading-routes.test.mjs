import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

const paths = [
  "../app/onboarding/platnosc/loading.tsx",
  "../app/onboarding/google/loading.tsx",
  "../app/onboarding/zasoby/loading.tsx",
  "../app/(app)/dashboard/loading.tsx",
  "../app/(app)/klienci/loading.tsx",
  "../app/(app)/kalendarz/loading.tsx",
];

for (const p of paths) {
  test(`${p} exists and renders Skeleton primitives`, () => {
    const url = new URL(p, import.meta.url);
    assert.ok(existsSync(url), `expected file at ${p}`);
    const src = readFileSync(url, "utf8");
    assert.match(src, /Skeleton(Card|Line|Cta)/);
    assert.match(src, /export default/);
  });
}
