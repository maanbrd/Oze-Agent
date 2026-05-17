import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

const faqSource = readFileSync(
  new URL("../app/(app)/faq/page.tsx", import.meta.url),
  "utf8",
);
const faqPreviewPath = new URL("../app/faq-preview/page.tsx", import.meta.url);
const faqPreviewSource = existsSync(faqPreviewPath)
  ? readFileSync(faqPreviewPath, "utf8")
  : "";

test("FAQ is grouped into three practical help sections", () => {
  for (const section of ["Dane i Google", "Praca z agentem", "Panel, oferty i konto"]) {
    assert.equal(faqSource.includes(section), true, section);
  }
});

test("FAQ contains the approved practical question set", () => {
  const questions = [
    "Gdzie są dane klientów?",
    "Czy muszę zakładać nowe konto Google?",
    "Czy mogę edytować dane ręcznie w Google?",
    "Co się dzieje z danymi, gdy rezygnuję?",
    "Po co Telegram, skoro jest panel web?",
    "Czy agent zapisuje coś od razu?",
    "Jak pisać do agenta, żeby dobrze zrozumiał?",
    "Co jeśli agent pomyli dane albo nie wie, o kogo chodzi?",
    "Do czego służy panel web?",
    "Czy webapp edytuje CRM?",
    "Jak działają oferty?",
    "Gdzie sprawdzę płatność i fakturę?",
  ];

  for (const question of questions) {
    assert.equal(faqSource.includes(question), true, question);
  }
});

test("FAQ recommends a separate Google account and Google Workspace without making it mandatory", () => {
  assert.equal(faqSource.includes("osobne konto Google"), true);
  assert.equal(faqSource.includes("Google Workspace"), true);
  assert.equal(faqSource.includes("nie jest wymagane"), true);
});

test("FAQ avoids technical implementation wording", () => {
  for (const forbidden of ["webhook", "backend", "Stripe Checkout", "read-only"]) {
    assert.equal(faqSource.includes(forbidden), false, forbidden);
  }
});

test("FAQ uses the Agent-OZE help layout style", () => {
  assert.equal(faqSource.includes("faqSections.reduce"), true);
  assert.equal(faqSource.includes("faqSections.length"), false);
  assert.equal(faqSource.includes("sekcje"), false);
  assert.equal(faqSource.includes("sectionIndex"), true);
  assert.equal(faqSource.includes('padStart(2, "0")'), true);
  assert.equal(faqSource.includes("lg:grid-cols-[0.72fr_1.28fr]"), true);
  assert.equal(faqSource.includes("shadow-[0_0_30px_rgba(61,255,122,0.06)]"), true);
});

test("FAQ has a dev-only preview route without local login", () => {
  assert.equal(existsSync(faqPreviewPath), true);
  assert.equal(faqPreviewSource.includes('dynamic = "force-dynamic"'), true);
  assert.equal(faqPreviewSource.includes('process.env.NODE_ENV !== "development"'), true);
  assert.equal(faqPreviewSource.includes("notFound()"), true);
  assert.equal(faqPreviewSource.includes("FaqPage"), true);
  assert.equal(faqPreviewSource.includes("getCurrentAccount"), false);
});
