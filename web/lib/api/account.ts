import { redirect } from "next/navigation";
import { fastApiBaseUrl } from "@/lib/api/base-url";
import { createClient } from "@/lib/supabase/server";

export type AccountProfile = {
  id: string;
  auth_user_id: string;
  name: string | null;
  email: string | null;
  phone: string | null;
  subscription_status: string | null;
  subscription_plan: string | null;
  subscription_current_period_end: string | null;
  activation_paid: boolean | null;
  onboarding_completed: boolean | null;
  google_sheets_id: string | null;
  google_calendar_id: string | null;
  google_drive_folder_id: string | null;
  telegram_id: number | null;
};

type AccountResponse = {
  auth_user_id: string;
  email: string | null;
  profile: AccountProfile | null;
};

const FASTAPI_ACCOUNT_TIMEOUT_MS = 8000;
const ACCOUNT_PROFILE_SELECT = [
  "id",
  "auth_user_id",
  "name",
  "email",
  "phone",
  "subscription_status",
  "subscription_plan",
  "subscription_current_period_end",
  "activation_paid",
  "onboarding_completed",
  "google_sheets_id",
  "google_calendar_id",
  "google_drive_folder_id",
  "telegram_id",
].join(", ");

export type CurrentAccount =
  | {
      authenticated: false;
      email: null;
      profile: null;
      accessToken: null;
      error: null;
    }
  | {
      authenticated: true;
      email: string | null;
      profile: AccountProfile | null;
      accessToken: string;
      error: string | null;
    };

async function fetchAccount(url: string, accessToken: string) {
  const controller = new AbortController();
  const timeout = setTimeout(
    () => controller.abort(),
    FASTAPI_ACCOUNT_TIMEOUT_MS,
  );

  try {
    return await fetch(url, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
      cache: "no-store",
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timeout);
  }
}

function safeUrlLogParts(value: string) {
  try {
    const url = new URL(value);
    return {
      origin: url.origin,
      pathname: url.pathname,
    };
  } catch {
    return {
      origin: "invalid",
      pathname: "",
    };
  }
}

async function fetchProfileFromSupabase(
  supabase: Awaited<ReturnType<typeof createClient>>,
  authUserId: string,
) {
  const { data, error } = await supabase
    .from("users")
    .select(ACCOUNT_PROFILE_SELECT)
    .eq("auth_user_id", authUserId)
    .maybeSingle();

  if (error) {
    console.error("getCurrentAccount Supabase profile fallback failed", {
      code: error.code,
    });
    return null;
  }

  return (data ?? null) as AccountProfile | null;
}

export async function getCurrentAccount(): Promise<CurrentAccount> {
  const supabase = await createClient();
  const { data: userData, error: userError } = await supabase.auth.getUser();

  if (userError || !userData.user) {
    return {
      authenticated: false,
      email: null,
      profile: null,
      accessToken: null,
      error: null,
    };
  }

  const { data: sessionData } = await supabase.auth.getSession();
  const accessToken = sessionData.session?.access_token ?? "";
  const authUserId = userData.user.id;
  const authEmail = userData.user.email ?? null;

  if (!accessToken) {
    const fallbackProfile = await fetchProfileFromSupabase(supabase, authUserId);
    return {
      authenticated: true,
      email: fallbackProfile?.email ?? authEmail,
      profile: fallbackProfile,
      accessToken: "",
      error: fallbackProfile
        ? "Brak tokenu sesji. Profil pobrano z Supabase."
        : "Brak tokenu sesji.",
    };
  }

  const baseUrl = fastApiBaseUrl();
  if (!baseUrl) {
    const fallbackProfile = await fetchProfileFromSupabase(supabase, authUserId);
    return {
      authenticated: true,
      email: fallbackProfile?.email ?? authEmail,
      profile: fallbackProfile,
      accessToken,
      error: fallbackProfile
        ? "Brak konfiguracji FASTAPI_INTERNAL_BASE_URL. Profil pobrano z Supabase."
        : "Brak konfiguracji FASTAPI_INTERNAL_BASE_URL.",
    };
  }

  const accountApiUrl = `${baseUrl}/api/me`;
  let response: Response;
  try {
    response = await fetchAccount(accountApiUrl, accessToken);
  } catch {
    const fallbackProfile = await fetchProfileFromSupabase(supabase, authUserId);
    return {
      authenticated: true,
      email: fallbackProfile?.email ?? authEmail,
      profile: fallbackProfile,
      accessToken,
      error: fallbackProfile
        ? "API konta chwilowo niedostępne. Profil pobrano z Supabase."
        : "Nie udało się połączyć z API konta.",
    };
  }

  if (!response.ok) {
    console.error("getCurrentAccount /api/me failed", {
      status: response.status,
      statusText: response.statusText,
      url: safeUrlLogParts(accountApiUrl),
    });
    const fallbackProfile = await fetchProfileFromSupabase(supabase, authUserId);
    return {
      authenticated: true,
      email: fallbackProfile?.email ?? authEmail,
      profile: fallbackProfile,
      accessToken,
      error: fallbackProfile
        ? "API konta chwilowo niedostępne. Profil pobrano z Supabase."
        : "Nie udało się pobrać profilu.",
    };
  }

  let account: AccountResponse;
  try {
    account = (await response.json()) as AccountResponse;
  } catch {
    const fallbackProfile = await fetchProfileFromSupabase(supabase, authUserId);
    return {
      authenticated: true,
      email: fallbackProfile?.email ?? authEmail,
      profile: fallbackProfile,
      accessToken,
      error: fallbackProfile
        ? "API konta zwróciło nieczytelną odpowiedź. Profil pobrano z Supabase."
        : "API konta zwróciło nieczytelną odpowiedź.",
    };
  }

  return {
    authenticated: true,
    email: account.email ?? authEmail,
    profile: account.profile,
    accessToken,
    error: null,
  };
}

export async function requireCurrentAccount(
  nextPath: string,
): Promise<CurrentAccount> {
  const account = await getCurrentAccount();
  if (!account.authenticated) {
    redirect(`/login?next=${encodeURIComponent(nextPath)}`);
  }
  return account;
}
