import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";
import ts from "typescript";

const source = readFileSync(new URL("../lib/routes.ts", import.meta.url), "utf8");
const { outputText } = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2022,
  },
});

const routeModule = { exports: {} };
vm.runInNewContext(outputText, {
  exports: routeModule.exports,
  module: routeModule,
  URL,
});

const { safeLocalPath, trustedExternalUrl } = routeModule.exports;

assert.equal(safeLocalPath(null), "/dashboard");
assert.equal(safeLocalPath(undefined, "/login"), "/login");
assert.equal(safeLocalPath(""), "/dashboard");
assert.equal(safeLocalPath("dashboard"), "/dashboard");
assert.equal(safeLocalPath("/onboarding/telegram"), "/onboarding/telegram");
assert.equal(safeLocalPath("/dashboard"), "/dashboard");
assert.equal(
  safeLocalPath("/login?next=/onboarding/telegram#retry"),
  "/login?next=/onboarding/telegram#retry",
);
assert.equal(safeLocalPath("//example.com/phish"), "/dashboard");
assert.equal(safeLocalPath("///example.com/phish"), "/dashboard");
assert.equal(safeLocalPath("https://example.com/phish"), "/dashboard");
assert.equal(safeLocalPath("http://example.com/phish"), "/dashboard");
assert.equal(safeLocalPath("javascript:alert(1)"), "/dashboard");
assert.equal(safeLocalPath("mailto:test@example.com"), "/dashboard");
assert.equal(safeLocalPath("\\evil"), "/dashboard");
assert.equal(safeLocalPath("/dashboard\r\nLocation: https://evil.test"), "/dashboard");

assert.equal(
  trustedExternalUrl("https://checkout.stripe.com/c/pay", [
    "https://checkout.stripe.com",
  ]),
  "https://checkout.stripe.com/c/pay",
);
assert.equal(
  trustedExternalUrl("https://accounts.google.com/o/oauth2/v2/auth", [
    "https://accounts.google.com",
  ]),
  "https://accounts.google.com/o/oauth2/v2/auth",
);
assert.equal(
  trustedExternalUrl("https://docs.google.com/spreadsheets/d/demo", [
    "https://docs.google.com",
    "https://calendar.google.com",
    "https://drive.google.com",
  ]),
  "https://docs.google.com/spreadsheets/d/demo",
);
assert.equal(
  trustedExternalUrl("http://checkout.stripe.com/c/pay", [
    "https://checkout.stripe.com",
  ]),
  null,
);
assert.equal(
  trustedExternalUrl("https://checkout.stripe.com.evil.test/c/pay", [
    "https://checkout.stripe.com",
  ]),
  null,
);
assert.equal(
  trustedExternalUrl("https://accounts.google.com.attacker.tld/o/oauth2", [
    "https://accounts.google.com",
  ]),
  null,
);
assert.equal(
  trustedExternalUrl("https://attacker.tld/?next=https://accounts.google.com", [
    "https://accounts.google.com",
  ]),
  null,
);
assert.equal(
  trustedExternalUrl("javascript:alert(1)", ["https://accounts.google.com"]),
  null,
);
assert.equal(trustedExternalUrl("not a url", ["https://accounts.google.com"]), null);
assert.equal(trustedExternalUrl("", ["https://accounts.google.com"]), null);
assert.equal(trustedExternalUrl(null, ["https://accounts.google.com"]), null);

console.log("route helper tests passed");
