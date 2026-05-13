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

test("telegram pairing page resolves the configured bot handle and exact command", () => {
  assert.equal(telegramPageSource.includes("DEFAULT_TELEGRAM_BOT_HANDLE"), true);
  assert.equal(telegramPageSource.includes("@OzeAgentBot"), true);
  assert.equal(telegramPageSource.includes("NEXT_PUBLIC_TELEGRAM_BOT_USERNAME"), true);
  assert.equal(pairingCardSource.includes("botHandle"), true);
  assert.equal(pairingCardSource.includes("@OZEAGENTBot"), false);
  assert.equal(pairingCardSource.includes('/start ${code ?? "KOD"}'), false);
  assert.equal(pairingCardSource.includes("/start KOD"), false);
  assert.match(pairingCardSource, /\/start \$\{code\}/);
});

test("telegram pairing card makes QR and deep link the primary path", () => {
  assert.equal(pairingCardSource.includes('import { QRCodeSVG } from "qrcode.react"'), true);
  assert.match(pairingCardSource, /https:\/\/t\.me\/\$\{botUsername\}\?start=\$\{encodeURIComponent\(code\)\}/);
  assert.equal(pairingCardSource.includes("telegramDeepLink"), true);
  assert.equal(pairingCardSource.includes("QRCodeSVG"), true);
  assert.equal(pairingCardSource.includes("Zeskanuj QR telefonem."), true);
  assert.equal(pairingCardSource.includes("Otwórz Telegrama"), true);
  assert.equal(pairingCardSource.includes("Kopiuj komendę"), true);
});

test("telegram pairing card exposes a real 90 second countdown and expired state", () => {
  assert.match(pairingCardSource, /PAIRING_TTL_SECONDS\s*=\s*90/);
  assert.equal(pairingCardSource.includes("90 sekund"), true);
  assert.equal(pairingCardSource.includes("Kod wygasł. Wygeneruj nowy kod."), true);
  assert.match(pairingCardSource, /Math\.min\(PAIRING_TTL_SECONDS/);
});

test("telegram pairing card gives cross-device steps in plain language", () => {
  for (const text of [
    "Zeskanuj QR telefonem albo kliknij Otwórz Telegrama.",
    "Telegram otworzy czat z botem ${botHandle}.",
    "Kliknij Start, jeśli Telegram pokaże taki przycisk.",
    "Jeśli kod nie wklei się sam, skopiuj komendę z tej strony.",
    "Awaryjnie wyślij w Telegramie komendę",
    "Wróć tutaj. Panel sam sprawdzi, czy konto jest połączone.",
  ]) {
    assert.equal(pairingCardSource.includes(text), true);
  }
});

test("telegram pairing card uses the live command in the visual process representation", () => {
  assert.equal(pairingCardSource.includes("telegram-pairing-flow.png"), false);
  assert.equal(pairingCardSource.includes("commandLabel"), true);
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

test("telegram pairing card shows status failures instead of silently hanging", () => {
  assert.equal(
    pairingCardSource.includes(
      "Nie udało się sprawdzić statusu. Spróbujemy ponownie.",
    ),
    true,
  );
  assert.match(pairingCardSource, /const \[statusError, setStatusError\]/);
  assert.equal(pairingCardSource.includes("onClick={pollStatus}"), true);
  assert.equal(pairingCardSource.includes("window.location.reload()"), false);
});

test("telegram status API route exposes current pairing state to the polling UI", () => {
  assert.equal(telegramStatusRouteSource.includes("getTelegramStatus"), true);
  assert.equal(telegramStatusRouteSource.includes("NextResponse.json"), true);
  assert.equal(telegramStatusRouteSource.includes("ok: true"), true);
  assert.equal(telegramStatusRouteSource.includes("ok: false"), true);
  assert.equal(telegramStatusRouteSource.includes("status ??"), false);
  assert.equal(telegramStatusRouteSource.includes("no-store"), true);
});
