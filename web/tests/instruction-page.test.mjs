import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

const privatePageSource = readFileSync(
  new URL("../app/(app)/instrukcja/page.tsx", import.meta.url),
  "utf8",
);
const previewPagePath = new URL("../app/instrukcja-preview/page.tsx", import.meta.url);
const previewPageSource = existsSync(previewPagePath)
  ? readFileSync(previewPagePath, "utf8")
  : "";
const guidePath = new URL("../components/instruction-guide.tsx", import.meta.url);
const guideSource = existsSync(guidePath) ? readFileSync(guidePath, "utf8") : "";

test("instruction page explains the agent as a full user guide", () => {
  for (const text of [
    "Instrukcja użytkowa Agent-OZE",
    "Najważniejsza zasada: agent nic nie zapisuje od razu",
    "✅ Zapisać",
    "➕ Dopisać",
    "❌ Anulować",
    "Dodaj klienta Jan Kowalski",
    "Jutro o 10 spotkanie",
    "co mam jutro?",
    "Wyślij ofertę",
    "Samo nazwisko to za mało",
    "Czego agent teraz nie robi",
  ]) {
    assert.equal(guideSource.includes(text), true, text);
  }
});

test("instruction page covers the web app sections in plain language", () => {
  for (const text of [
    "Dashboard",
    "Wymagają decyzji",
    "Klienci",
    "Kalendarz",
    "Oferty",
    "Płatności",
    "Arkusz Google",
    "Kalendarz Google",
    "Dysk Google",
  ]) {
    assert.equal(guideSource.includes(text), true, text);
  }

  assert.equal(guideSource.includes("Ustawienia"), false);
  assert.equal(guideSource.includes("Import"), false);
});

test("instruction note example explains short follow-up notes without sounding rigid", () => {
  assert.equal(guideSource.includes("Notatka po rozmowie"), true);
  assert.equal(guideSource.includes("dopisz, że żona chce magazyn"), true);
  assert.equal(guideSource.includes("musi wiedzieć, którego klienta dotyczy notatka"), false);
});

test("instruction sections are visually separated into clear chapters", () => {
  for (const marker of [
    'number="01"',
    'number="02"',
    'number="03"',
    'number="04"',
    'number="05"',
  ]) {
    assert.equal(guideSource.includes(marker), true, marker);
  }

  assert.equal(guideSource.includes("Podstawowe wpisy"), true);
  assert.equal(guideSource.includes("Odczyt, oferty i załączniki"), true);
  assert.equal(guideSource.includes("border-t border-white/10"), true);
});

test("instruction page avoids implementation jargon", () => {
  for (const forbidden of [
    "Supabase",
    "FastAPI",
    "endpoint",
    "webhook",
    "record_add_meeting",
    "ID wydarzenia",
    "_row",
    "row number",
    "ISO",
  ]) {
    assert.equal(guideSource.includes(forbidden), false, forbidden);
  }
});

test("instruction guide has a dev-only public preview route", () => {
  assert.equal(privatePageSource.includes("InstructionGuide"), true);
  assert.equal(existsSync(previewPagePath), true);
  assert.equal(previewPageSource.includes('dynamic = "force-dynamic"'), true);
  assert.equal(previewPageSource.includes("InstructionGuide"), true);
  assert.equal(previewPageSource.includes('process.env.NODE_ENV !== "development"'), true);
  assert.equal(previewPageSource.includes("notFound()"), true);
});
