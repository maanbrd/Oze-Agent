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

function apiBaseUrl() {
  return (
    process.env.FASTAPI_INTERNAL_BASE_URL ??
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    ""
  ).replace(/\/$/, "");
}

export async function getCurrentAccount(): Promise<CurrentAccount> {
  const supabase = await createClient();
  const { data: claimsData } = await supabase.auth.getClaims();

  if (!claimsData?.claims) {
    return {
      authenticated: false,
      email: null,
      profile: null,
      accessToken: null,
      error: null,
    };
  }

  const { data: sessionData } = await supabase.auth.getSession();
  const accessToken = sessionData.session?.access_token;

  if (!accessToken) {
    return {
      authenticated: true,
      email: String(claimsData.claims.email ?? ""),
      profile: null,
      accessToken: "",
      error: "Brak tokenu sesji.",
    };
  }

  const baseUrl = apiBaseUrl();
  if (!baseUrl) {
    return {
      authenticated: true,
      email: String(claimsData.claims.email ?? ""),
      profile: null,
      accessToken,
      error: "Brak konfiguracji FASTAPI_INTERNAL_BASE_URL.",
    };
  }

  const response = await fetch(`${baseUrl}/api/me`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    return {
      authenticated: true,
      email: String(claimsData.claims.email ?? ""),
      profile: null,
      accessToken,
      error: "Nie udało się pobrać profilu.",
    };
  }

  const account = (await response.json()) as AccountResponse;

  return {
    authenticated: true,
    email: account.email,
    profile: account.profile,
    accessToken,
    error: null,
  };
}
