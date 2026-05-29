import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const src = readSource("../app/api/onboarding/resources-progress/route.ts");

test("route handler is a GET handler", () => {
  assert.match(src, /export\s+async\s+function\s+GET/);
});

test("response uses SSE content-type or JSON polling shape", () => {
  assert.ok(
    src.includes("text/event-stream") || src.includes("application/json"),
    "expected SSE or JSON response",
  );
});

test("payload includes step, elapsed_ms fields", () => {
  assert.match(src, /step/);
  assert.match(src, /elapsed_ms/);
});

test("route reads authoritative progress from FastAPI proxy", () => {
  assert.match(src, /fastApiBaseUrl|FASTAPI_BASE_URL/);
});
