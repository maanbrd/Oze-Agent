import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const paymentsPreviewPath = new URL("../app/platnosci-preview/page.tsx", import.meta.url);
const paymentsPreviewSource = readSource("../app/platnosci-preview/page.tsx");
const paymentsPath = new URL("../app/(app)/platnosci/page.tsx", import.meta.url);
const paymentsSource = readSource("../app/(app)/platnosci/page.tsx");

const userFacingTexts = [
  "Konto i rozliczenia",
  "Konto czeka na płatność",
  "Aktywuj subskrypcję, żeby korzystać z Agent OZE.",
  "OZE-Agent",
  "399 zł / mies.",
  "Co obejmuje plan",
  "Faktury i historia",
  "Historia płatności pojawi się po pierwszej opłaconej subskrypcji.",
];

const technicalWords = [
  "Stripe i subskrypcja",
  "webhook",
  "endpoint",
  "FastAPI",
  "Supabase.",
  "payment_history",
  "nie wybrano",
];

test("payments preview renders a billing page without local login", () => {
  assert.equal(existsSync(paymentsPreviewPath), true);
  assert.equal(paymentsPreviewSource.includes("CrmShell"), true);
  assert.equal(paymentsPreviewSource.includes('dynamic = "force-dynamic"'), true);
  assert.equal(paymentsPreviewSource.includes('process.env.NODE_ENV !== "development"'), true);
  assert.equal(paymentsPreviewSource.includes("notFound()"), true);
  assert.equal(paymentsPreviewSource.includes("getCurrentAccount"), false);
});

test("payments preview uses user-facing billing language", () => {
  for (const text of userFacingTexts) {
    assert.equal(paymentsPreviewSource.includes(text), true, text);
  }
});

test("payments preview hides technical billing implementation words", () => {
  for (const forbidden of technicalWords) {
    assert.equal(paymentsPreviewSource.includes(forbidden), false, forbidden);
  }
});

test("payments page uses the same live billing language", () => {
  assert.equal(existsSync(paymentsPath), true);
  assert.equal(paymentsSource.includes("getCurrentAccount"), true);

  for (const text of userFacingTexts) {
    assert.equal(paymentsSource.includes(text), true, text);
  }
});

test("payments page does not expose implementation details to users", () => {
  for (const forbidden of technicalWords) {
    assert.equal(paymentsSource.includes(forbidden), false, forbidden);
  }
});
