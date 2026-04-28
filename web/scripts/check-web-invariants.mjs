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

const crmAdapter = read("lib/crm/adapters.ts");
assert.match(crmAdapter, /sheets/i, "CRM adapter must model Sheets as client source.");
assert.match(crmAdapter, /calendar/i, "CRM adapter must model Calendar as event source.");
assert.doesNotMatch(
  crmAdapter,
  /\.insert\(|\.update\(|\.delete\(/,
  "CRM adapter must be read-only.",
);

const crmNotice = read("components/crm-notice.tsx");
assert.match(
  crmNotice,
  /Sheets.*Calendar|Calendar.*Sheets/,
  "CRM notice must say edits happen in Sheets and Calendar.",
);

const appFiles = walk("app").filter((file) => file.endsWith(".tsx"));
const appSource = appFiles.map((file) => read(file)).join("\n");
assert.match(
  appSource,
  /CRM|Sheets|Calendar|Google/,
  "App UI must mention CRM/Google edit boundary.",
);
assert.doesNotMatch(
  appSource,
  /action=\{.*addClient|action=\{.*updateClient|name="status"/s,
  "App UI must not expose CRM mutation forms.",
);

for (const route of [
  "app/(app)/dashboard/page.tsx",
  "app/(app)/klienci/page.tsx",
  "app/(app)/kalendarz/page.tsx",
]) {
  assert.match(
    read(route),
    /getCrmDashboardData|CrmNotice|DataFreshnessBadge/,
    `${route} must use CRM read-only primitives.`,
  );
}

console.log("web invariants passed");
