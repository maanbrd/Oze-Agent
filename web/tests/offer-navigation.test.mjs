import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

const flatOffersPath = new URL("../app/oferty/page.tsx", import.meta.url);
const groupedOffersPath = new URL("../app/(app)/oferty/page.tsx", import.meta.url);
const previewOffersPath = new URL("../app/oferty-preview/page.tsx", import.meta.url);
const groupedOffersSource = readFileSync(groupedOffersPath, "utf8");
const previewOffersSource = existsSync(previewOffersPath) ? readFileSync(previewOffersPath, "utf8") : "";
const crmLayoutSource = readFileSync(new URL("../app/(app)/layout.tsx", import.meta.url), "utf8");
const crmShellSource = readFileSync(new URL("../components/crm-shell.tsx", import.meta.url), "utf8");
const offerSource = readFileSync(new URL("../components/offers/offer-generator.tsx", import.meta.url), "utf8");
const globalsSource = readFileSync(new URL("../app/globals.css", import.meta.url), "utf8");

test("offers page uses the CRM shell route group", () => {
  assert.equal(existsSync(flatOffersPath), false);
  assert.equal(existsSync(groupedOffersPath), true);
  assert.match(groupedOffersSource, /<OfferGenerator \/>/);
  assert.equal(groupedOffersSource.includes("AppShell"), false);
  assert.match(crmLayoutSource, /<CrmShell account=\{account\} decisionsCount=\{decisionsCount\}>/);
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

test("offer generator uses the quieter CRM color treatment", () => {
  assert.equal(globalsSource.includes("--oze-border: rgba(255, 255, 255, 0.045);"), true);
  assert.equal(globalsSource.includes("--oze-green-soft: #78f59a;"), true);
  assert.equal(globalsSource.includes(".oze-app,\n.oze-offers"), true);
  assert.equal(globalsSource.includes(".oze-offers label.text-\\[\\#3DFF7A\\]"), true);
  assert.equal(globalsSource.includes(".oze-offers th.text-\\[\\#3DFF7A\\]"), true);
  assert.equal(globalsSource.includes("background: rgba(255, 255, 255, 0.025) !important;"), true);
  assert.equal(globalsSource.includes("border-color: var(--oze-border) !important;"), true);
  assert.equal(globalsSource.includes("box-shadow: 0 0 0 2px rgba(61, 255, 122, 0.07);"), true);
});

test("offer generator has a dev-only preview route without local login", () => {
  assert.equal(existsSync(previewOffersPath), true);
  assert.equal(previewOffersSource.includes('dynamic = "force-dynamic"'), true);
  assert.equal(previewOffersSource.includes('process.env.NODE_ENV !== "development"'), true);
  assert.equal(previewOffersSource.includes("notFound()"), true);
  assert.equal(previewOffersSource.includes("CrmShell"), true);
  assert.equal(previewOffersSource.includes("OfferGenerator"), true);
  assert.equal(previewOffersSource.includes("getCurrentAccount"), false);
});
