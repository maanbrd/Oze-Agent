"use server";

import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";

function value(formData: FormData, key: string) {
  return String(formData.get(key) ?? "").trim();
}

function encoded(path: string, message: string) {
  const params = new URLSearchParams({ message });
  return `${path}?${params.toString()}`;
}

export async function login(formData: FormData) {
  const email = value(formData, "email").toLowerCase();
  const password = value(formData, "password");
  const next = value(formData, "next") || "/dashboard";

  const supabase = await createClient();
  const { error } = await supabase.auth.signInWithPassword({ email, password });

  if (error) {
    redirect(encoded("/login", "Nie udało się zalogować. Sprawdź email i hasło."));
  }

  redirect(next.startsWith("/") ? next : "/dashboard");
}

export async function signup(formData: FormData) {
  const firstName = value(formData, "firstName");
  const lastName = value(formData, "lastName");
  const phone = value(formData, "phone");
  const email = value(formData, "email").toLowerCase();
  const password = value(formData, "password");
  const terms = formData.get("terms") === "on";
  const onboardingSurvey = {
    region: value(formData, "region"),
    specialty: value(formData, "specialty"),
    referral_source: value(formData, "referralSource"),
    experience: value(formData, "experience"),
  };

  if (!terms) {
    redirect(encoded("/rejestracja", "Regulamin jest wymagany."));
  }

  const name = `${firstName} ${lastName}`.trim();
  const supabase = await createClient();
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: {
        first_name: firstName,
        last_name: lastName,
        name,
        phone,
        consent_terms: true,
        consent_marketing: formData.get("marketing") === "on",
        consent_phone_contact: formData.get("phoneContact") === "on",
        onboarding_survey: onboardingSurvey,
        region: onboardingSurvey.region,
        specialty: onboardingSurvey.specialty,
        referral_source: onboardingSurvey.referral_source,
        experience: onboardingSurvey.experience,
      },
    },
  });

  if (error) {
    redirect(encoded("/rejestracja", "Nie udało się założyć konta. Spróbuj ponownie."));
  }

  if (!data.session) {
    redirect(encoded("/login", "Konto utworzone. Sprawdź email i zaloguj się."));
  }

  redirect("/onboarding/platnosc");
}

export async function logout() {
  const supabase = await createClient();
  await supabase.auth.signOut();
  redirect("/login");
}
