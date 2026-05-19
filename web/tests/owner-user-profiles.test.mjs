import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const ownerShellSource = readSource("../components/owner/owner-admin-shell.tsx");
const pageSource = readSource("../app/admin/profile-uzytkownikow/page.tsx");
const componentSource = readSource("../components/owner/owner-user-profiles.tsx");
const apiSource = readSource("../lib/api/admin-user-profiles.ts");

test("owner admin shell links to user profiles panel", () => {
  assert.match(ownerShellSource, /\/admin\/profile-uzytkownikow/);
  assert.match(ownerShellSource, /Profile użytkowników/);
});

test("user profiles admin page fetches profile data and renders dedicated view", () => {
  assert.match(pageSource, /dynamic = "force-dynamic"/);
  assert.match(pageSource, /getOwnerUserProfiles/);
  assert.match(pageSource, /OwnerUserProfilesDashboard/);
});

test("user profiles API client calls protected Admin API endpoints", () => {
  assert.match(apiSource, /\/api\/admin\/user-profiles/);
  assert.match(apiSource, /Authorization: `Bearer \$\{account\.accessToken\}`/);
  assert.match(apiSource, /profile_markdown/);
  assert.match(apiSource, /insights_json/);
});

test("user profiles view has a thin admin reader structure", () => {
  assert.match(componentSource, /Profile użytkowników/);
  assert.match(componentSource, /Markdown profilu/);
  assert.match(componentSource, /Wnioski/);
  assert.match(componentSource, /Ostatnia analiza/);
  assert.match(componentSource, /whitespace-pre-wrap/);
  assert.equal(componentSource.includes("contentEditable"), false);
});
