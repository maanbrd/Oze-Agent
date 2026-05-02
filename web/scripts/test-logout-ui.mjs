import { readFileSync } from "node:fs";
import { join } from "node:path";
import assert from "node:assert/strict";

const root = new URL("..", import.meta.url).pathname;

function read(path) {
  return readFileSync(join(root, path), "utf8");
}

const logoutButton = read("components/logout-button.tsx");
assert.match(
  logoutButton,
  /import\s+\{\s*logout\s*\}\s+from\s+"@\/app\/auth\/actions"/,
  "LogoutButton must wire the shared logout server action.",
);
assert.match(
  logoutButton,
  /<form\s+action=\{logout\}>/,
  "LogoutButton must submit through the logout server action.",
);
assert.match(
  logoutButton,
  /type="submit"/,
  "LogoutButton must render a submit button.",
);
assert.match(
  logoutButton,
  />\s*Wyloguj\s*</,
  "LogoutButton must render the visible logout label.",
);
assert.match(
  logoutButton,
  /\$\{className\}/,
  "LogoutButton must preserve caller-supplied styling overrides.",
);

const appShell = read("components/app-shell.tsx");
assert.match(
  appShell,
  /<LogoutButton\s*\/>/,
  "App shell must render the shared logout button for authenticated pages.",
);

const onboardingLayout = read("app/onboarding/layout.tsx");
assert.match(
  onboardingLayout,
  /<LogoutButton\s+className="bg-\[#050607\]\/90 backdrop-blur"\s*\/>/,
  "Onboarding layout must render the styled shared logout button while the user is mid-flow.",
);
