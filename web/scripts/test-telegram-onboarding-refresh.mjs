import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const root = new URL("..", import.meta.url).pathname;

function read(path) {
  return readFileSync(join(root, path), "utf8");
}

assert.ok(
  existsSync(join(root, "components/telegram-status-poller.tsx")),
  "Telegram onboarding must include a dedicated status poller component.",
);

const poller = read("components/telegram-status-poller.tsx");
assert.match(
  poller,
  /^"use client";/m,
  "Telegram status poller must be a client component.",
);
assert.match(
  poller,
  /router\.refresh\(\)/,
  "Telegram status poller must refresh the onboarding page.",
);
assert.match(
  poller,
  /setInterval\(/,
  "Telegram status poller must poll for updated pairing state.",
);

const telegramPage = read("app/onboarding/telegram/page.tsx");
assert.match(
  telegramPage,
  /import\s+\{\s*TelegramStatusPoller\s*\}\s+from\s+"@\/components\/telegram-status-poller"/,
  "Telegram onboarding page must use the shared status poller.",
);
assert.match(
  telegramPage,
  /<TelegramStatusPoller\s*\/>/,
  "Telegram onboarding page must mount the status poller while waiting for pairing.",
);
