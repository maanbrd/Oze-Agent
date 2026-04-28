import { readFileSync } from "node:fs";
import { join } from "node:path";
import assert from "node:assert/strict";

const root = new URL("..", import.meta.url).pathname;

function read(path) {
  return readFileSync(join(root, path), "utf8");
}

const stripeWebhook = read("app/api/webhooks/stripe/route.ts");
assert.match(stripeWebhook, /livemode/, "Stripe webhook must inspect livemode.");
assert.match(
  stripeWebhook,
  /Live Stripe events are disabled|live mode/i,
  "Stripe webhook must reject live-mode events.",
);

const crmAdapter = read("lib/crm/adapters.ts");
assert.match(crmAdapter, /sheets/i, "CRM adapter must model Sheets as client source.");
assert.match(crmAdapter, /calendar/i, "CRM adapter must model Calendar as event source.");
assert.doesNotMatch(
  crmAdapter,
  /\.insert\(|\.update\(|\.delete\(/,
  "CRM adapter must be read-only.",
);

console.log("web invariants passed");
