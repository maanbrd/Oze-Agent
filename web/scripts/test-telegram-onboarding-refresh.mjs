import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const root = new URL("..", import.meta.url).pathname;

function read(path) {
  return readFileSync(join(root, path), "utf8");
}

const poller = read("components/onboarding/telegram-pairing-card.tsx");
assert.match(
  poller,
  /^"use client";/m,
  "Telegram pairing card must be a client component.",
);
assert.match(
  poller,
  /\/api\/onboarding\/telegram-status/,
  "Telegram pairing card must poll the Telegram status API.",
);
assert.match(
  poller,
  /window\.setInterval\(pollStatus/,
  "Telegram pairing card must poll for updated pairing state.",
);
assert.match(
  poller,
  /window\.location\.assign\("\/dashboard\?onboarding=complete"\)/,
  "Telegram pairing card must send paired users to the dashboard completion URL.",
);

const telegramPage = read("app/onboarding/telegram/page.tsx");
assert.match(
  telegramPage,
  /import\s+\{\s*TelegramPairingCard\s*\}\s+from\s+"@\/components\/onboarding\/telegram-pairing-card"/,
  "Telegram onboarding page must use the shared pairing card.",
);
assert.match(
  telegramPage,
  /<TelegramPairingCard/,
  "Telegram onboarding page must mount the pairing card while waiting for pairing.",
);
