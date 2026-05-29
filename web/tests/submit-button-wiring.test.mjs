import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const expectations = [
  { file: "../app/rejestracja/page.tsx", pendingLabel: "Rejestruję konto…", variant: "solid", fullWidth: true },
  { file: "../app/login/page.tsx", pendingLabel: "Loguję…", variant: "solid", fullWidth: true },
  { file: "../app/onboarding/platnosc/page.tsx", pendingLabel: "Przygotowuję płatność…", variant: "solid", fullWidth: false },
  { file: "../app/onboarding/platnosc/page.tsx", pendingLabel: "Aktywuję dostęp…", variant: "outline", fullWidth: false },
  { file: "../app/onboarding/google/page.tsx", pendingLabel: "Łączę z Google…", variant: "solid", fullWidth: true },
  { file: "../app/(app)/ustawienia/page.tsx", pendingLabel: "Zapisuję…", variant: "outline", fullWidth: false },
  { file: "../app/(app)/platnosci/page.tsx", pendingLabel: "Anuluję trial…", variant: "outline", fullWidth: false },
  { file: "../components/auth/logout-link.tsx", pendingLabel: "Wylogowuję…", variant: "outline", fullWidth: false },
];

for (const { file, pendingLabel, variant, fullWidth } of expectations) {
  test(`${file} wires SubmitButton with pendingLabel "${pendingLabel}"`, () => {
    const src = readSource(file);
    assert.match(src, /SubmitButton/, `expected SubmitButton import/usage in ${file}`);
    assert.ok(
      src.includes(`pendingLabel="${pendingLabel}"`),
      `expected pendingLabel="${pendingLabel}" in ${file}`
    );
    assert.ok(
      src.includes(`variant="${variant}"`),
      `expected variant="${variant}" in ${file}`
    );
    if (fullWidth) {
      assert.match(src, /fullWidth/, `expected fullWidth prop in ${file}`);
    }
  });
}

// telegram-pairing-card uses dynamic variant — assert only pendingLabel.
test("telegram-pairing-card wires SubmitButton for the 'Wygeneruj nowy kod' button", () => {
  const src = readSource("../components/onboarding/telegram-pairing-card.tsx");
  assert.match(src, /SubmitButton/);
  assert.ok(src.includes(`pendingLabel="Generuję nowy kod…"`));
  // Dynamic variant is intentional — both literals must appear.
  assert.match(src, /variant=\{expired \? "solid" : "outline"\}/);
});
