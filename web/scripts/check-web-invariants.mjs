import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import assert from "node:assert/strict";

const root = new URL("..", import.meta.url).pathname;

function read(path) {
  return readFileSync(join(root, path), "utf8");
}

function walk(dir) {
  const entries = readdirSync(join(root, dir));
  return entries.flatMap((entry) => {
    const relative = join(dir, entry);
    const absolute = join(root, relative);
    if (statSync(absolute).isDirectory()) return walk(relative);
    return relative;
  });
}

const stripeWebhook = read("app/api/webhooks/stripe/route.ts");
assert.match(stripeWebhook, /livemode/, "Stripe webhook must inspect livemode.");
assert.match(
  stripeWebhook,
  /Live Stripe events are disabled|live mode/i,
  "Stripe webhook must reject live-mode events.",
);

console.log("web invariants passed");
