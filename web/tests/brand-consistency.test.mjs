import assert from "node:assert/strict";
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { test } from "node:test";

const root = new URL("..", import.meta.url).pathname;
const repoRoot = join(root, "..");

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

test("shared brand component defines canonical business email addresses", () => {
  const source = readSource("components/brand.tsx");

  for (const email of [
    "admin@agent-oze.pl",
    "kontakt@agent-oze.pl",
    "support@agent-oze.pl",
    "faktury@agent-oze.pl",
  ]) {
    assert.equal(source.includes(email), true, `${email} must be defined in shared brand constants`);
  }
});

test("environment template documents the Workspace owner admin email", () => {
  const envExample = readFileSync(join(repoRoot, "oze-agent/.env.example"), "utf8");

  assert.match(envExample, /^ADMIN_EMAIL=admin@agent-oze\.pl$/m);
  assert.match(envExample, /^OWNER_ADMIN_EMAILS=admin@agent-oze\.pl\s+# comma-separated emails allowed to open \/admin$/m);
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

test("visible user-facing sources do not use the retired public email domain", () => {
  const checkedDirs = [join(root, "app"), join(root, "components"), join(root, "lib")];
  const offenders = [];

  for (const dir of checkedDirs) {
    for (const file of collectSourceFiles(dir)) {
      const relativePath = relative(root, file);
      const source = readFileSync(file, "utf8");
      if (source.includes("@oze-agent.pl")) {
        offenders.push(relativePath);
      }
    }
  }

  assert.deepEqual(offenders, []);
});
