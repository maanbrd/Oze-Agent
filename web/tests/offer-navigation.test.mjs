import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

const flatOffersPath = new URL("../app/oferty/page.tsx", import.meta.url);
const groupedOffersPath = new URL("../app/(app)/oferty/page.tsx", import.meta.url);
const groupedOffersSource = readFileSync(groupedOffersPath, "utf8");
const crmLayoutSource = readFileSync(new URL("../app/(app)/layout.tsx", import.meta.url), "utf8");
const crmShellSource = readFileSync(new URL("../components/crm-shell.tsx", import.meta.url), "utf8");
const offerSource = readFileSync(new URL("../components/offers/offer-generator.tsx", import.meta.url), "utf8");

test("offers page uses the CRM shell route group", () => {
  assert.equal(existsSync(flatOffersPath), false);
  assert.equal(existsSync(groupedOffersPath), true);
  assert.match(groupedOffersSource, /<OfferGenerator \/>/);
  assert.equal(groupedOffersSource.includes("AppShell"), false);
  assert.match(crmLayoutSource, /<CrmShell account=\{account\}>/);
  assert.match(crmShellSource, /\["Oferty", "\/oferty"\]/);
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
