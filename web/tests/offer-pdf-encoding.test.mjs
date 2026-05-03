import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const source = readFileSync(new URL("../components/offers/offer-generator.tsx", import.meta.url), "utf8");

test("browser PDF fallback does not write UTF-16 BOM strings into page text", () => {
  assert.equal(source.includes("FEFF"), false);
  assert.equal(source.includes("pdfUtf16Hex"), false);
});

test("browser PDF fallback does not render product type as a tiny header artifact", () => {
  assert.equal(source.includes("text(offer.productType"), false);
});

test("test PDF is generated from the live preview state, not stale backend profile data", () => {
  assert.equal(source.includes("/test-pdf"), false);
});

test("browser PDF fallback embeds the selected logo image", () => {
  assert.equal(source.includes("embedPng"), true);
  assert.equal(source.includes("embedJpg"), true);
});

test("browser PDF fallback clears the accent bar behind transparent logos", () => {
  assert.equal(source.includes("logoClearArea"), true);
});

test("offer PDF does not render the informational eyebrow near the logo", () => {
  assert.equal(source.includes("Oferta informacyjna"), false);
});

test("offer PDF and preview use the short price label", () => {
  assert.equal(source.includes("Cena klienta"), false);
  assert.equal(source.includes("CENA KLIENTA"), false);
});

test("active wizard tabs expose state for high-contrast black text", () => {
  assert.equal(source.includes("data-active"), true);
});

test("browser PDF fallback uses the generated PV and storage watermark subtly", () => {
  assert.equal(source.includes("pv-storage-watermark.png"), true);
  assert.equal(source.includes("watermarkOpacity"), true);
});

test("browser PDF fallback does not render the top-right price box", () => {
  assert.equal(source.includes("priceBoxY"), false);
  assert.equal(source.includes("po szacowanym dofinansowaniu"), false);
});

test("browser PDF fallback uses the dark preview-style palette", () => {
  assert.equal(source.includes("pdfDarkBackground"), true);
  assert.equal(source.includes("pdfTextWhite"), true);
  assert.equal(source.includes("fill(0, 0, 595, 842, rgb(1, 1, 1))"), false);
});

test("offer profile editor does not expose the accent control", () => {
  assert.equal(source.includes('type="color"'), false);
  assert.equal(source.includes(">Akcent"), false);
});

test("browser PDF fallback does not use the seller accent color", () => {
  assert.equal(source.includes("hexToRgb01(profile.accentColor)"), false);
  assert.equal(source.includes("boldFont, accent"), false);
});
