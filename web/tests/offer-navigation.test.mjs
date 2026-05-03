import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const shellSource = readFileSync(new URL("../components/app-shell.tsx", import.meta.url), "utf8");
const offerSource = readFileSync(new URL("../components/offers/offer-generator.tsx", import.meta.url), "utf8");

test("offers page removes the left sidebar shell and keeps only the top-left brand", () => {
  assert.equal(shellSource.includes("<aside"), false);
  assert.equal(shellSource.includes("lg:grid-cols-[240px_1fr]"), false);
  assert.match(shellSource, /absolute left-5 top-5/);
  assert.equal(shellSource.includes("absolute right-5 top-5"), false);
  assert.equal(shellSource.includes("OZE Agent"), true);
  assert.equal(shellSource.includes("Dashboard"), false);
  assert.equal(shellSource.includes(">Oferty<"), false);
});

test("offer generator uses one clear page title", () => {
  assert.equal(offerSource.includes(">Generator ofert<"), true);
  assert.equal(offerSource.includes(">Generator</p>"), false);
  assert.equal(offerSource.includes(">Oferty</h1>"), false);
});

test("offer generator title is shifted toward the header center", () => {
  assert.equal(offerSource.includes("sm:grid-cols-[1fr_auto_1fr]"), true);
  assert.equal(offerSource.includes("sm:col-start-2"), true);
  assert.equal(offerSource.includes("sm:col-start-3"), true);
});
