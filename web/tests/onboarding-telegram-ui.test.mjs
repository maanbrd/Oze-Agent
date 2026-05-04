import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const telegramPageSource = readSource("../app/onboarding/telegram/page.tsx");
const pairingCardSource = readSource("../components/onboarding/telegram-pairing-card.tsx");
const telegramStatusRouteSource = readSource(
  "../app/api/onboarding/telegram-status/route.ts",
);

test("telegram onboarding uses a dedicated pairing card and keeps completed redirect", () => {
  assert.match(telegramPageSource, /TelegramPairingCard/);
  assert.match(telegramPageSource, /\/dashboard\?onboarding=complete/);
});

test("telegram pairing card names the production bot and the exact command", () => {
  assert.equal(pairingCardSource.includes("@OZEAGENTBot"), true);
  assert.match(pairingCardSource, /\/start \$\{code \?\? "KOD"\}/);
});

test("telegram pairing card exposes a real 90 second countdown and expired state", () => {
  assert.match(pairingCardSource, /PAIRING_TTL_SECONDS\s*=\s*90/);
  assert.equal(pairingCardSource.includes("90 sekund"), true);
  assert.equal(pairingCardSource.includes("Kod wygasł. Wygeneruj nowy kod."), true);
  assert.match(pairingCardSource, /Math\.min\(PAIRING_TTL_SECONDS/);
});

test("telegram pairing card gives every small step in plain language", () => {
  for (const text of [
    "Otwórz Telegram.",
    "Kliknij wyszukiwarkę u góry ekranu.",
    "Wpisz @OZEAGENTBot.",
    "Otwórz czat z botem.",
    "Jeśli widzisz przycisk Start, kliknij go.",
    "Skopiuj komendę z tej strony.",
    "Wklej w Telegramie komendę",
    "Wyślij wiadomość do bota.",
    "Wróć tutaj i odśwież stronę, jeśli status nie zmieni się sam.",
  ]) {
    assert.equal(pairingCardSource.includes(text), true);
  }
});

test("telegram pairing card includes the generated visual process representation", () => {
  assert.equal(
    existsSync(new URL("../public/media/telegram-pairing-flow.png", import.meta.url)),
    true,
  );
  assert.equal(pairingCardSource.includes("telegram-pairing-flow.png"), true);
  for (const text of ["Telegram", "Komenda", "Połączenie", "Panel"]) {
    assert.equal(pairingCardSource.includes(text), true);
  }
});

test("telegram pairing card polls status and redirects after successful pairing", () => {
  assert.match(pairingCardSource, /POLL_INTERVAL_MS\s*=\s*3000/);
  assert.equal(
    pairingCardSource.includes('fetch("/api/onboarding/telegram-status"'),
    true,
  );
  assert.equal(
    pairingCardSource.includes(
      'window.location.assign("/dashboard?onboarding=complete")',
    ),
    true,
  );
  assert.equal(pairingCardSource.includes("if (!code || expired)"), true);
});

test("telegram status API route exposes current pairing state to the polling UI", () => {
  assert.equal(telegramStatusRouteSource.includes("getTelegramStatus"), true);
  assert.equal(telegramStatusRouteSource.includes("NextResponse.json"), true);
  assert.equal(telegramStatusRouteSource.includes("no-store"), true);
});
