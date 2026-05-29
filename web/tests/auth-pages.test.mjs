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
const logoutLinkSource = readSource("../components/auth/logout-link.tsx");
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

  for (const label of [
    "Imię",
    "Nazwisko",
    "Telefon",
    "Email",
    "Hasło",
    "Powtórz hasło",
    "Dalej: płatność",
  ]) {
    assert.equal(registrationPageSource.includes(label), true);
  }
});

test("registration form keeps the onboarding content and three consent checkboxes without step tiles", () => {
  for (const text of [
    "Załóż konto i przejdź do onboardingu.",
    "Akceptuję regulamin i politykę prywatności.",
    "Chcę otrzymywać informacje o rozwoju Agent OZE.",
    "Wyrażam zgodę na kontakt telefoniczny.",
  ]) {
    assert.equal(registrationPageSource.includes(text), true);
  }

  assert.equal(registrationPageSource.includes("Możecie zadzwonić, jeśli onboarding utknie."), false);
  assert.equal(registrationPageSource.includes("Auth + RLS"), false);
  assert.equal(registrationPageSource.includes("Google + Telegram"), false);
  assert.equal(registrationPageSource.includes("Ten krok tworzy bezpieczne konto."), false);
  assert.equal(registrationPageSource.includes("parowanie Telegrama będą kolejnymi krokami"), false);
  assert.equal(registrationPageSource.includes("sm:grid-cols-3"), false);
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
    "Pompy ciepła + piece",
    "Czyste powietrze",
    "Wszystkie",
    "Inna",
    "Polecenie",
    "3+ lata",
    "Dalej: płatność",
  ]) {
    assert.equal(registrationPageSource.includes(text), true);
  }

  assert.equal(registrationPageSource.includes('"PV", "Pompy ciepła", "PV + magazyn", "Wszystko"'), false);
  assert.equal(authActionsSource.includes("onboarding_survey"), true);
  assert.equal(authActionsSource.includes("referral_source"), true);
});

test("auth forms provide concrete input placeholders", () => {
  for (const placeholder of [
    "jan@firma.pl",
    "Twoje hasło",
    "Jan",
    "Kowalski",
    "500 600 700",
    "Minimum 8 znaków",
    "Powtórz hasło",
  ]) {
    assert.equal(
      `${loginPageSource}\n${registrationPageSource}`.includes(`placeholder="${placeholder}"`),
      true,
      `${placeholder} placeholder must be present`,
    );
  }
});

test("signup validates repeated password before creating an auth account", () => {
  assert.equal(registrationPageSource.includes('name="repeatPassword"'), true);
  assert.match(registrationPageSource, /label="Powtórz hasło"[\s\S]*name="repeatPassword"/);
  assert.match(authActionsSource, /const repeatPassword = value\(formData, "repeatPassword"\);/);
  assert.match(authActionsSource, /if \(password !== repeatPassword\)/);
  assert.match(authActionsSource, /Hasła nie są takie same\./);

  const mismatchCheckIndex = authActionsSource.indexOf("password !== repeatPassword");
  const signUpIndex = authActionsSource.indexOf("supabase.auth.signUp");
  assert.ok(mismatchCheckIndex > -1);
  assert.ok(signUpIndex > -1);
  assert.ok(mismatchCheckIndex < signUpIndex);
});

test("signup creates a real auth account and sends the seller to payment onboarding", () => {
  assert.equal(authActionsSource.includes('"use server"'), true);
  assert.equal(authActionsSource.includes("signUp"), true);
  assert.equal(authActionsSource.includes("name,"), false);
  assert.equal(authActionsSource.includes('redirect("/onboarding/przekierowuje?to=stripe")'), true);
  assert.equal(authActionsSource.includes('router.push("/oferty")'), false);
  assert.equal(authActionsSource.includes('redirect("/oferty")'), false);
  assert.equal(authActionsSource.includes("localStorage.setItem"), false);
});

test("auth mutations invalidate the router cache before redirecting", () => {
  assert.match(authActionsSource, /import \{ revalidatePath \} from "next\/cache";/);

  for (const actionName of ["login", "signup", "logout"]) {
    const actionStart = authActionsSource.indexOf(`export async function ${actionName}`);
    const nextActionStart = authActionsSource.indexOf(
      "export async function",
      actionStart + 1,
    );
    const actionSource = authActionsSource.slice(
      actionStart,
      nextActionStart === -1 ? undefined : nextActionStart,
    );

    assert.match(actionSource, /revalidatePath\("\/", "layout"\);/);
  }
});

test("logout link does not prefetch the logout side effect", () => {
  assert.equal(logoutLinkSource.includes("next/link"), false);
  assert.match(logoutLinkSource, /action="\/logout"/);
  assert.match(logoutLinkSource, /SubmitButton/);
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
