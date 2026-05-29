import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const expectations = [
  { file: "../app/rejestracja/page.tsx", pendingLabel: "Rejestruję konto" },
  { file: "../app/login/page.tsx", pendingLabel: "Loguję" },
  { file: "../app/onboarding/platnosc/page.tsx", pendingLabel: "Przygotowuję płatność" },
  { file: "../app/onboarding/platnosc/page.tsx", pendingLabel: "Aktywuję dostęp" },
  { file: "../app/onboarding/google/page.tsx", pendingLabel: "Łączę z Google" },
  { file: "../app/(app)/ustawienia/page.tsx", pendingLabel: "Zapisuję" },
  { file: "../app/(app)/platnosci/page.tsx", pendingLabel: "Anuluję trial" },
  { file: "../components/auth/logout-link.tsx", pendingLabel: "Wylogowuję" },
  { file: "../components/onboarding/telegram-pairing-card.tsx", pendingLabel: "Generuję nowy kod" },
];

for (const { file, pendingLabel } of expectations) {
  test(`${file} wires SubmitButton with pendingLabel "${pendingLabel}"`, () => {
    const src = readSource(file);
    assert.match(src, /SubmitButton/);
    assert.ok(
      src.includes(`pendingLabel="${pendingLabel}"`) ||
        src.includes(`pendingLabel={\`${pendingLabel}`),
      `expected pendingLabel="${pendingLabel}" in ${file}`
    );
  });
}
