import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const src = readSource("../components/dashboard/decyzje-preview.tsx");

test("decyzje-preview is read-only and routes decisions to Telegram", () => {
  assert.equal(src.includes("/decyzje-preview/actions"), false);
  assert.equal(src.includes("changeClientStatusAction"), false);
  assert.equal(src.includes("scheduleClientCallAction"), false);
  assert.match(src, /https:\/\/t\.me\/AgentOZE_Bot/);
});

test("decyzje-preview no longer maintains its own ToastState", () => {
  // Custom local toast type removed in favor of sonner.
  assert.equal(src.includes("type ToastState"), false);
});
