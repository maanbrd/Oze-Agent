import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const source = readFileSync(new URL("../components/offers/offer-generator.tsx", import.meta.url), "utf8");

test("offer profile editor exposes email body template instead of legacy signature", () => {
  assert.equal(source.includes("Treść emaila"), true);
  assert.equal(source.includes("emailBodyTemplate"), true);
  assert.equal(source.includes("email_body_template"), true);
  assert.equal(source.includes("Podpis maila"), false);
  assert.equal(source.includes("emailSignature"), false);
});

test("offer email editor exposes safe draggable variable chips without a test preview", () => {
  for (const token of [
    "{{Imię i nazwisko}}",
    "{{Miasto}}",
    "{{Email}}",
    "{{Telefon}}",
    "{{Produkt}}",
    "{{Status}}",
    "{{Następny krok}}",
    "{{Data następnego kroku}}",
    "{{Firma}}",
    "{{Nazwa oferty}}",
    "{{Cena}}",
  ]) {
    assert.equal(source.includes(token), true);
  }

  assert.equal(source.includes("draggable"), true);
  assert.equal(source.includes("onDragStart"), true);
  assert.equal(source.includes("onDrop"), true);
  assert.equal(source.includes("Podgląd testowy emaila"), false);
  assert.equal(source.includes("emailPreview"), false);
  assert.equal(source.includes("{{_row}}"), false);
  assert.equal(source.includes("{{ID wydarzenia Kalendarz}}"), false);
  assert.equal(source.includes("{{Zdjęcia}}"), false);
  assert.equal(source.includes("{{Link do zdjęć}}"), false);
});

test("email editor lives in its own content step between terms and preview", () => {
  const stepsStart = source.indexOf("const steps");
  const stepsEnd = source.indexOf("const productTypes");
  const stepsSource = source.slice(stepsStart, stepsEnd);
  const basicsStart = source.indexOf("function BasicsStep");
  const basicsEnd = source.indexOf("function ComponentsStep");
  const basicsSource = source.slice(basicsStart, basicsEnd);
  const emailStart = source.indexOf("function EmailContentStep");
  const emailEnd = source.indexOf("function PreviewStep");
  const emailSource = source.slice(emailStart, emailEnd);

  assert.ok(stepsSource.indexOf('label: "Warunki"') < stepsSource.indexOf('label: "Treść"'));
  assert.ok(stepsSource.indexOf('label: "Treść"') < stepsSource.indexOf('label: "Preview"'));
  assert.ok(basicsStart > 0);
  assert.ok(basicsSource.indexOf('label="Nazwa"') < basicsSource.indexOf('label="Typ zestawu"'));
  assert.equal(basicsSource.includes("Treść emaila"), false);
  assert.ok(emailStart > 0);
  assert.equal(emailSource.includes("Treść emaila"), true);
  assert.equal(emailSource.includes("Podgląd testowy emaila"), false);
});

test("email content step uses inline chips instead of showing raw token braces in a textarea", () => {
  const emailStart = source.indexOf("function EmailContentStep");
  const emailEnd = source.indexOf("function PreviewStep");
  const emailSource = source.slice(emailStart, emailEnd);
  const editorStart = source.indexOf("function EmailTemplateEditor");
  const editorEnd = source.indexOf("function EmailContentStep");
  const editorSource = source.slice(editorStart, editorEnd);

  assert.equal(emailSource.includes("<textarea"), false);
  assert.ok(editorStart > 0);
  assert.equal(editorSource.includes("contentEditable"), true);
  assert.equal(source.includes("data-email-token"), true);
  assert.equal(source.includes("serializeEmailEditor"), true);
  assert.equal(source.includes("emailTokenChipClass"), true);
  assert.equal(editorSource.includes("min-h-[360px]"), true);
});

test("inline email variable chips expose an x control for removal", () => {
  assert.equal(source.includes("data-email-token-remove"), true);
  assert.equal(source.includes("Usuń zmienną"), true);
  assert.equal(source.includes("removeEmailTokenChip"), true);
  assert.equal(source.includes('aria-label="Usuń zmienną'), true);
});
