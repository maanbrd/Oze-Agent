"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { safeLocalPath } from "@/lib/routes";
import {
  createClient,
  missingSupabaseEnvRedirectMessage,
} from "@/lib/supabase/server";

function value(formData: FormData, key: string) {
  return String(formData.get(key) ?? "").trim();
}

function encoded(path: string, message: string) {
  const params = new URLSearchParams({ message });
  return `${path}?${params.toString()}`;
}

function encodedWithNext(path: string, message: string, next: string) {
  const params = new URLSearchParams({ message, next });
  return `${path}?${params.toString()}`;
}

export async function login(formData: FormData) {
  const email = value(formData, "email").toLowerCase();
  const password = value(formData, "password");
  const next = safeLocalPath(value(formData, "next"));
  const configError = missingSupabaseEnvRedirectMessage();

  if (configError) {
    redirect(encodedWithNext("/login", configError, next));
  }

  const supabase = await createClient();
  const { error } = await supabase.auth.signInWithPassword({ email, password });

  if (error) {
    redirect(
      encodedWithNext(
        "/login",
        "Nie udało się zalogować. Sprawdź email i hasło.",
        next,
      ),
    );
  }

  revalidatePath("/", "layout");
  redirect(next);
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

  const configError = missingSupabaseEnvRedirectMessage();
  if (configError) {
    redirect(encoded("/rejestracja", configError));
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
    redirect(
      encoded("/rejestracja", "Nie udało się założyć konta. Spróbuj ponownie."),
    );
  }

  if (!data.session) {
    redirect(encoded("/login", "Konto utworzone. Sprawdź email i zaloguj się."));
  }

  revalidatePath("/", "layout");
  redirect("/onboarding/platnosc");
}

export async function logout() {
  const configError = missingSupabaseEnvRedirectMessage();
  if (configError) {
    redirect(encoded("/login", configError));
  }

  const supabase = await createClient();
  await supabase.auth.signOut();
  revalidatePath("/", "layout");
  redirect("/login");
}
