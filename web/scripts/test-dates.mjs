import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";
import ts from "typescript";

const source = readFileSync(new URL("../lib/dates.ts", import.meta.url), "utf8");
const { outputText } = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2022,
  },
});

const dateModule = { exports: {} };
vm.runInNewContext(outputText, {
  exports: dateModule.exports,
  module: dateModule,
  Intl,
  Date,
  Number,
});

const {
  formatWarsawDayLabel,
  formatWarsawTime,
  warsawDateKey,
  warsawDateKeyFromIso,
} = dateModule.exports;

assert.equal(
  warsawDateKey(new Date("2026-01-15T22:30:00.000Z")),
  "2026-01-15",
);
assert.equal(
  warsawDateKey(new Date("2026-01-15T23:30:00.000Z")),
  "2026-01-16",
);
assert.equal(
  warsawDateKeyFromIso("2026-03-29T00:30:00.000Z"),
  "2026-03-29",
);
assert.equal(
  warsawDateKeyFromIso("2026-05-01T23:30:00.000Z"),
  "2026-05-02",
);
assert.equal(
  warsawDateKeyFromIso("2026-10-25T22:30:00.000Z"),
  "2026-10-25",
);
assert.equal(warsawDateKeyFromIso("2026-05-01"), "2026-05-01");
assert.equal(warsawDateKeyFromIso("not-a-date"), null);

assert.match(formatWarsawDayLabel("2026-05-01"), /01\.05\.2026/);
assert.match(formatWarsawDayLabel("invalid"), /invalid/);
assert.match(formatWarsawTime("2026-01-15T23:30:00.000Z"), /^00:30$/);
assert.match(formatWarsawTime("2026-03-29T01:30:00.000Z"), /^03:30$/);
assert.match(formatWarsawTime("2026-10-25T01:30:00.000Z"), /^02:30$/);

console.log("date helper tests passed");
