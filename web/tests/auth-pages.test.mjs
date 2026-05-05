import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const loginPageSource = readSource("../app/login/page.tsx");
const registrationPageSource = readSource("../app/rejestracja/page.tsx");
const authActionsSource = readSource("../app/auth/actions.ts");
const supabaseServerSource = readSource("../lib/supabase/server.ts");
const authConfigErrorSource = readSource(
  "../components/auth/auth-config-error.tsx",
);

test("login page renders a real Supabase auth form instead of the placeholder", () => {
  assert.equal(loginPageSource.includes("PlaceholderPage"), false);
  assert.equal(loginPageSource.includes("Panel handlowca będzie dostępny"), false);
  assert.equal(loginPageSource.includes("Brak formularza jest celowy"), false);
  assert.match(loginPageSource, /action=\{login\}/);

  for (const label of ["Email", "Hasło", "Zaloguj się"]) {
    assert.equal(loginPageSource.includes(label), true);
  }
});

test("registration page renders a real server-action onboarding form instead of the placeholder", () => {
  assert.equal(registrationPageSource.includes("PlaceholderPage"), false);
  assert.equal(registrationPageSource.includes("Onboarding jest już w przygotowaniu"), false);
  assert.match(registrationPageSource, /action=\{signup\}/);

  for (const label of ["Imię", "Nazwisko", "Telefon", "Email", "Hasło", "Dalej: płatność"]) {
    assert.equal(registrationPageSource.includes(label), true);
  }
});

test("registration form keeps the fuller onboarding content and three consent checkboxes", () => {
  for (const text of [
    "Załóż konto i przejdź do onboardingu.",
    "Auth + RLS",
    "Płatność",
    "Google + Telegram",
    "Akceptuję regulamin i politykę prywatności.",
    "Chcę otrzymywać informacje o rozwoju Agent-OZE.",
    "Możecie zadzwonić, jeśli onboarding utknie.",
  ]) {
    assert.equal(registrationPageSource.includes(text), true);
  }

  assert.equal((registrationPageSource.match(/type="checkbox"/g) ?? []).length, 3);
  assert.equal(authActionsSource.includes("consent_terms"), true);
  assert.equal(authActionsSource.includes("consent_marketing"), true);
  assert.equal(authActionsSource.includes("consent_phone_contact"), true);
});

test("registration form keeps the onboarding survey before consent", () => {
  for (const text of [
    "Krótka ankieta",
    "Pomaga ustawić onboarding pod teren, w którym pracujesz.",
    "Region działania",
    "Branża",
    "Skąd nas znasz",
    "Doświadczenie w OZE",
    "cała Polska",
    "PV + magazyn",
    "Polecenie",
    "3+ lata",
    "Dalej: płatność",
  ]) {
    assert.equal(registrationPageSource.includes(text), true);
  }

  assert.equal(authActionsSource.includes("onboarding_survey"), true);
  assert.equal(authActionsSource.includes("referral_source"), true);
});

test("signup creates a real auth account and sends the seller to payment onboarding", () => {
  assert.equal(authActionsSource.includes('"use server"'), true);
  assert.equal(authActionsSource.includes("signUp"), true);
  assert.equal(authActionsSource.includes('redirect("/onboarding/platnosc")'), true);
  assert.equal(authActionsSource.includes('router.push("/oferty")'), false);
  assert.equal(authActionsSource.includes('redirect("/oferty")'), false);
  assert.equal(authActionsSource.includes("localStorage.setItem"), false);
});

test("auth pages show a controlled Supabase config error instead of crashing", () => {
  assert.match(supabaseServerSource, /getSupabaseEnvStatus/);
  assert.match(supabaseServerSource, /envValue/);
  assert.match(supabaseServerSource, /value !== `""`/);
  assert.equal(supabaseServerSource.includes('"SUPABASE_URL"'), true);
  assert.equal(supabaseServerSource.includes('"SUPABASE_KEY"'), true);
  assert.match(supabaseServerSource, /missingSupabaseEnvMessage/);
  assert.match(supabaseServerSource, /missingSupabaseEnvRedirectMessage/);
  assert.match(loginPageSource, /missingSupabaseEnvMessage\(\)/);
  assert.match(registrationPageSource, /missingSupabaseEnvMessage\(\)/);
  assert.match(authActionsSource, /missingSupabaseEnvRedirectMessage\(\)/);
  assert.equal(authConfigErrorSource.includes("Logowanie wymaga konfiguracji Supabase."), true);
  assert.equal(authConfigErrorSource.includes("web/.env.local"), true);
  assert.equal(
    authConfigErrorSource.includes("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY"),
    true,
  );
  assert.equal(authConfigErrorSource.includes("NEXT_PUBLIC_SUPABASE_ANON_KEY"), true);
  assert.equal(authConfigErrorSource.includes("SUPABASE_URL"), true);
  assert.equal(authConfigErrorSource.includes("SUPABASE_KEY"), true);
});
