import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { test } from "node:test";

const root = new URL("..", import.meta.url).pathname;

function readSource(path) {
  return readFileSync(join(root, path), "utf8");
}

function parseStringArray(source, constantName) {
  const match = source.match(new RegExp(`const ${constantName} = \\[(?<body>[\\s\\S]*?)\\] as const;`));
  assert.ok(match?.groups?.body, `${constantName} must be defined as a string tuple`);

  return Array.from(match.groups.body.matchAll(/"([^"]+)"/g), (item) => item[1]);
}

test("landing hero has short mobile headline lines that fit narrow phones", () => {
  const source = readSource("components/landing.tsx");
  const lines = parseStringArray(source, "MOBILE_HERO_TITLE_LINES");

  assert.ok(lines.length >= 5);

  for (const line of lines) {
    assert.ok(line.length <= 18, `"${line}" is too long for the 390px mobile hero`);
  }
});

test("landing mobile shell clips only horizontal decorative overflow", () => {
  const source = readSource("components/landing.tsx");

  assert.match(source, /overflowX:\s*"clip"/);
  assert.match(source, /minWidth:\s*0/);
  assert.match(source, /Firmy OZE\? Agent dla zespołu/);
  assert.match(source, /compact \? \(\s*MOBILE_HERO_TITLE_LINES\.map/);
});

test("registration page allows auth content to shrink on mobile", () => {
  const source = readSource("app/rejestracja/page.tsx");
  const lines = parseStringArray(source, "REGISTRATION_MOBILE_TITLE_LINES");

  assert.match(source, /overflow-x-clip/);
  assert.equal(source.includes("min-h-screen overflow-hidden"), false);
  assert.ok(lines.length >= 3);
  for (const line of lines) {
    assert.ok(line.length <= 16, `"${line}" is too long for the 390px registration headline`);
  }
  assert.match(source, /max-w-\[330px\]/);
  assert.match(source, /grid w-full min-w-0/);
  assert.match(source, /<div className="min-w-0 pt-2">/);
  assert.match(source, /className="min-w-0 rounded-\[8px\]/);
  assert.match(source, /text-4xl/);
});

test("login page keeps its form within a narrow mobile viewport", () => {
  const source = readSource("app/login/page.tsx");

  assert.match(source, /overflow-x-clip/);
  assert.equal(source.includes("min-h-screen overflow-hidden"), false);
  assert.match(source, /max-w-\[330px\]/);
  assert.match(source, /justify-start[^"]*sm:justify-center/);
  assert.match(source, /min-w-0/);
  assert.match(source, /<span className="sm:hidden">Start<\/span>/);
});

test("shared web shells avoid full-page overflow-hidden on mobile", () => {
  for (const path of [
    "components/app-shell.tsx",
    "components/auth/auth-config-error.tsx",
    "components/placeholder-page.tsx",
  ]) {
    const source = readSource(path);
    assert.match(source, /overflow-x-clip/, `${path} should only clip horizontal overflow`);
    assert.equal(source.includes("min-h-screen overflow-hidden"), false, path);
  }

  assert.match(readSource("app/firma/page.tsx"), /overflowX:\s*"clip"/);
});
