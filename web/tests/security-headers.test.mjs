import assert from "node:assert/strict";
import { test } from "node:test";

import {
  buildCsp,
  buildHsts,
  buildSecurityHeaders,
} from "../lib/security-headers.mjs";

function headerMap(headers) {
  return Object.fromEntries(headers.map((h) => [h.key, h.value]));
}

test("CSP ships as Report-Only by default (safe rollout)", () => {
  const map = headerMap(buildSecurityHeaders({ enforceCsp: false }));
  assert.ok(map["Content-Security-Policy-Report-Only"]);
  assert.equal(map["Content-Security-Policy"], undefined);
});

test("CSP is enforced when enforceCsp is true", () => {
  const map = headerMap(buildSecurityHeaders({ enforceCsp: true }));
  assert.ok(map["Content-Security-Policy"]);
  assert.equal(map["Content-Security-Policy-Report-Only"], undefined);
});

test("CSP locks framing, base-uri and object-src", () => {
  const csp = buildCsp();
  assert.match(csp, /default-src 'self'/);
  assert.match(csp, /frame-ancestors 'none'/);
  assert.match(csp, /object-src 'none'/);
  assert.match(csp, /base-uri 'self'/);
});

test("CSP allows the real redirect + data origins the app needs", () => {
  const csp = buildCsp();
  assert.match(csp, /form-action[^;]*https:\/\/checkout\.stripe\.com/);
  assert.match(csp, /form-action[^;]*https:\/\/accounts\.google\.com/);
  assert.match(csp, /connect-src[^;]*https:\/\/\*\.supabase\.co/);
});

test("CSP never weakens script-src with unsafe-eval", () => {
  assert.doesNotMatch(buildCsp(), /unsafe-eval/);
});

test("static security headers are present and strict", () => {
  const map = headerMap(buildSecurityHeaders());
  assert.equal(map["X-Content-Type-Options"], "nosniff");
  assert.equal(map["X-Frame-Options"], "DENY");
  assert.equal(map["Referrer-Policy"], "strict-origin-when-cross-origin");
  assert.match(map["Permissions-Policy"], /geolocation=\(\)/);
});

test("HSTS starts conservative and ramps via flags", () => {
  // Default: 1 day, no includeSubDomains/preload (staged rollout).
  assert.equal(buildHsts({ maxAge: 86400 }), "max-age=86400");
  // Fully ramped.
  assert.equal(
    buildHsts({ maxAge: 15552000, includeSubDomains: true, preload: true }),
    "max-age=15552000; includeSubDomains; preload",
  );
});
