import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const previewPath = new URL("../app/oferty-preview/page.tsx", import.meta.url);
const previewSource = readSource("../app/oferty-preview/page.tsx");
test("offer generator preview is available locally without login", () => {
  assert.equal(existsSync(previewPath), true);
  assert.equal(previewSource.includes("CrmShell"), true);
  assert.equal(previewSource.includes("OfferGenerator"), true);
  assert.equal(previewSource.includes('dynamic = "force-dynamic"'), true);
  assert.equal(previewSource.includes('process.env.NODE_ENV !== "development"'), true);
  assert.equal(previewSource.includes("notFound()"), true);
  assert.equal(previewSource.includes("getCurrentAccount"), false);
});

test("offer generator preview uses the selected variant A production component", () => {
  assert.equal(previewSource.includes("OfferDesignPreview"), false);
  assert.equal(previewSource.includes("Wariant B"), false);
  assert.equal(previewSource.includes("Wariant C"), false);
});
