import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { test } from "node:test";

const root = new URL("..", import.meta.url).pathname;

function readSource(path) {
  return readFileSync(join(root, path), "utf8");
}

const privacyPageSource = readSource("app/polityka-prywatnosci/page.tsx");
const termsPageSource = readSource("app/regulamin/page.tsx");
const landingSource = readSource("components/landing.tsx");
const registrationPageSource = readSource("app/rejestracja/page.tsx");
const brandSource = readSource("components/brand.tsx");

test("privacy policy is a production Google OAuth disclosure, not a placeholder", () => {
  assert.equal(privacyPageSource.includes("PlaceholderPage"), false);
  assert.equal(privacyPageSource.includes("Dokument roboczy"), false);
  assert.equal(privacyPageSource.includes("placeholder"), false);

  for (const text of [
    "Administrator danych",
    "Google OAuth",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/gmail.send",
    "Limited Use",
    "cofnąć dostęp",
    "usunąć konto",
    "SUPPORT_EMAIL",
  ]) {
    assert.equal(privacyPageSource.includes(text), true, `${text} must be disclosed`);
  }
  assert.equal(brandSource.includes("support@agent-oze.pl"), true);
});

test("privacy policy identifies the temporary GREAT MF LLC controller", () => {
  for (const text of [
    "GREAT MF LLC",
    "36-5120312",
    "810 Pony Express Rd",
    "Cheyenne, WY 82009",
    "tymczasowym operatorem",
    "polski podmiot",
  ]) {
    assert.equal(privacyPageSource.includes(text), true, `${text} must identify the controller path`);
  }
});

test("privacy policy covers GDPR duties and review-safe business benefits", () => {
  for (const text of [
    "RODO",
    "okres przechowywania",
    "odbiorcy",
    "transfer",
    "Prezes UODO",
    "onboarding_survey",
    "conversation_history",
    "admin mirror",
    "user_behavior_profiles",
    "zagregowane benchmarki",
    "profilowanie sposobu pracy",
    "nie wywołuje skutków prawnych",
    "feedback",
    "case studies",
    "osobnej zgody",
  ]) {
    assert.equal(privacyPageSource.includes(text), true, `${text} must be disclosed`);
  }
});

test("privacy policy prohibits unsafe Google data monetization", () => {
  for (const text of [
    "nie używamy danych Google API do reklam",
    "retargetingu",
    "brokerom danych",
    "oceny zdolności kredytowej",
    "Google API Services User Data Policy",
  ]) {
    assert.equal(privacyPageSource.includes(text), true, `${text} must protect Limited Use`);
  }
});

test("terms page is production service terms, not a placeholder", () => {
  assert.equal(termsPageSource.includes("PlaceholderPage"), false);
  assert.equal(termsPageSource.includes("Dokument roboczy"), false);
  assert.equal(termsPageSource.includes("placeholder"), false);

  for (const text of [
    "Zakres usługi",
    "Subskrypcja",
    "Google",
    "Telegram",
    "Gmail",
    "odstąpienie",
    "Rezygnacja",
    "SUPPORT_EMAIL",
  ]) {
    assert.equal(termsPageSource.includes(text), true, `${text} must be present`);
  }
  assert.equal(brandSource.includes("support@agent-oze.pl"), true);
});

test("terms page captures operator rights without weakening consumer rights", () => {
  for (const text of [
    "GREAT MF LLC",
    "36-5120312",
    "świadczenia usługi cyfrowej przed upływem terminu odstąpienia",
    "zawiesić",
    "braku płatności",
    "nadużyć",
    "zmienić cennik",
    "feedback",
    "wersje beta",
    "obowiązkowe prawa konsumenta",
    "użytkowników biznesowych",
  ]) {
    assert.equal(termsPageSource.includes(text), true, `${text} must be present`);
  }
});

test("terms page tracks separate B2B agreement and later Polish operator migration", () => {
  for (const text of [
    "TODO: oddzielna umowa B2B",
    "zespołów sprzedażowych",
    "polski podmiot",
    "aktualizacja regulaminu",
    "B2B",
  ]) {
    assert.equal(termsPageSource.includes(text), true, `${text} must be tracked`);
  }
});

test("public entry points link to privacy policy and terms", () => {
  for (const source of [landingSource, registrationPageSource]) {
    assert.equal(source.includes("/polityka-prywatnosci"), true);
    assert.equal(source.includes("/regulamin"), true);
  }
});
