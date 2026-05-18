import assert from "node:assert/strict";
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { test } from "node:test";

const root = new URL("..", import.meta.url).pathname;

function readSource(path) {
  return readFileSync(join(root, path), "utf8");
}

function collectSourceFiles(dir) {
  const files = [];
  for (const entry of readdirSync(dir)) {
    const fullPath = join(dir, entry);
    const stat = statSync(fullPath);
    if (stat.isDirectory()) {
      files.push(...collectSourceFiles(fullPath));
    } else if (/\.(tsx?|jsx?)$/.test(entry)) {
      files.push(fullPath);
    }
  }
  return files;
}

test("shared brand component defines the canonical Agent OZE identity", () => {
  const brandPath = join(root, "components/brand.tsx");
  assert.equal(existsSync(brandPath), true);

  const source = readSource("components/brand.tsx");
  assert.match(source, /BRAND_NAME\s*=\s*"Agent OZE"/);
  assert.match(source, /function BrandMark/);
  assert.match(source, /function BrandLink/);
  assert.match(source, /#3DFF7A/);
});

test("primary shells use the shared brand link", () => {
  for (const file of [
    "components/landing.tsx",
    "components/crm-shell.tsx",
    "components/owner/owner-admin-shell.tsx",
  ]) {
    const source = readSource(file);
    assert.match(source, /@\/components\/brand/, `${file} must import the shared brand component`);
    assert.match(source, /<BrandLink\b/, `${file} must render BrandLink`);
  }
});

test("visible user-facing sources do not use retired brand spellings", () => {
  const checkedDirs = [join(root, "app"), join(root, "components"), join(root, "lib")];
  const offenders = [];

  for (const dir of checkedDirs) {
    for (const file of collectSourceFiles(dir)) {
      const relativePath = relative(root, file);
      const source = readFileSync(file, "utf8");
      if (source.includes("OZE Agent") || source.includes("Agent-OZE")) {
        offenders.push(relativePath);
      }
    }
  }

  assert.deepEqual(offenders, []);
});
