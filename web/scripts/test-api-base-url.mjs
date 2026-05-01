import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";
import ts from "typescript";

const source = readFileSync(new URL("../lib/api/base-url.ts", import.meta.url), "utf8");
const { outputText } = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2022,
  },
});

const moduleRef = { exports: {} };
const fakeProcess = { env: {} };
vm.runInNewContext(outputText, {
  exports: moduleRef.exports,
  module: moduleRef,
  process: fakeProcess,
  URL,
});

const { normalizeFastApiBaseUrl, fastApiBaseUrl } = moduleRef.exports;

assert.equal(normalizeFastApiBaseUrl(null), "");
assert.equal(normalizeFastApiBaseUrl(""), "");
assert.equal(
  normalizeFastApiBaseUrl("https://api-staging-staging-7359.up.railway.app"),
  "https://api-staging-staging-7359.up.railway.app",
);
assert.equal(
  normalizeFastApiBaseUrl("https://api-staging-staging-7359.up.railway.app/"),
  "https://api-staging-staging-7359.up.railway.app",
);
assert.equal(
  normalizeFastApiBaseUrl("https://api-staging-staging-7359.up.railway.app/api"),
  "https://api-staging-staging-7359.up.railway.app",
);
assert.equal(
  normalizeFastApiBaseUrl("https://api-staging-staging-7359.up.railway.app/api/"),
  "https://api-staging-staging-7359.up.railway.app",
);
assert.equal(
  normalizeFastApiBaseUrl("https://api-staging-staging-7359.up.railway.app/api?x=1#frag"),
  "https://api-staging-staging-7359.up.railway.app",
);
assert.equal(
  normalizeFastApiBaseUrl("https://api-staging-staging-7359.up.railway.app/internal"),
  "https://api-staging-staging-7359.up.railway.app/internal",
);
assert.equal(normalizeFastApiBaseUrl("not a url/"), "not a url");

fakeProcess.env.FASTAPI_INTERNAL_BASE_URL =
  "https://api-staging-staging-7359.up.railway.app/api/";
fakeProcess.env.NEXT_PUBLIC_API_BASE_URL = "https://ignored.example";
assert.equal(
  fastApiBaseUrl(),
  "https://api-staging-staging-7359.up.railway.app",
);

delete fakeProcess.env.FASTAPI_INTERNAL_BASE_URL;
assert.equal(fastApiBaseUrl(), "https://ignored.example");

console.log("api base-url tests passed");
