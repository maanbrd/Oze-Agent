import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const crmShellSource = readSource("../components/crm-shell.tsx");
const privateSettingsPath = new URL("../app/(app)/ustawienia/page.tsx", import.meta.url);
const privateImportPath = new URL("../app/(app)/import/page.tsx", import.meta.url);
const settingsPreviewPath = new URL("../app/ustawienia-preview/page.tsx", import.meta.url);
const settingsPreviewComponentPath = new URL(
  "../components/settings-preview.tsx",
  import.meta.url,
);
const panelPreviewPath = new URL("../app/panel-preview/page.tsx", import.meta.url);
const panelPreviewSource = readSource("../app/panel-preview/page.tsx");

test("settings and import stay hidden from the main CRM navigation", () => {
  assert.equal(existsSync(privateSettingsPath), true);
  assert.equal(existsSync(privateImportPath), true);
  assert.equal(crmShellSource.includes('["Ustawienia", "/ustawienia"]'), false);
  assert.equal(crmShellSource.includes("/ustawienia"), false);
  assert.equal(crmShellSource.includes('["Import", "/import"]'), false);
  assert.equal(crmShellSource.includes("/import"), false);
});

test("rejected settings concept preview is removed", () => {
  assert.equal(existsSync(settingsPreviewPath), false);
  assert.equal(existsSync(settingsPreviewComponentPath), false);
});

test("panel preview renders the CRM shell without requiring login in development", () => {
  assert.equal(existsSync(panelPreviewPath), true);
  assert.equal(panelPreviewSource.includes("CrmShell"), true);
  assert.equal(panelPreviewSource.includes('dynamic = "force-dynamic"'), true);
  assert.equal(panelPreviewSource.includes('process.env.NODE_ENV !== "development"'), true);
  assert.equal(panelPreviewSource.includes("notFound()"), true);
  assert.equal(panelPreviewSource.includes("getCurrentAccount"), false);
  assert.equal(panelPreviewSource.includes("Płatności, import"), false);
});
