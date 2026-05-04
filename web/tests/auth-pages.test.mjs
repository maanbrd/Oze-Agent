import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const loginPageSource = readSource("../app/login/page.tsx");
const registrationPageSource = readSource("../app/rejestracja/page.tsx");
const authPageSource = readSource("../components/auth/auth-page.tsx");

test("login page renders a real auth form instead of the placeholder", () => {
  assert.equal(loginPageSource.includes("PlaceholderPage"), false);
  assert.equal(loginPageSource.includes("Panel handlowca będzie dostępny"), false);
  assert.equal(loginPageSource.includes("Brak formularza jest celowy"), false);
  assert.match(loginPageSource, /AuthPage/);

  for (const label of ["Email", "Hasło", "Zaloguj się"]) {
    assert.equal(authPageSource.includes(label), true);
  }
});

test("registration page renders a real onboarding form instead of the placeholder", () => {
  assert.equal(registrationPageSource.includes("PlaceholderPage"), false);
  assert.equal(registrationPageSource.includes("Onboarding jest już w przygotowaniu"), false);
  assert.match(registrationPageSource, /AuthPage/);

  for (const label of ["Imię", "Nazwisko", "Telefon", "Email", "Hasło", "Załóż konto"]) {
    assert.equal(authPageSource.includes(label), true);
  }
});

test("auth form creates a local web session and returns the seller to the app", () => {
  assert.equal(authPageSource.includes('"use client"'), true);
  assert.equal(authPageSource.includes("localStorage.setItem"), true);
  assert.equal(authPageSource.includes("oze-agent-session"), true);
  assert.equal(authPageSource.includes('router.push("/oferty")'), true);
});
