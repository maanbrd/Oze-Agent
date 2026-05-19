import type { CurrentAccount } from "@/lib/api/account";
import { fastApiBaseUrl } from "@/lib/api/base-url";

export type OwnerUserProfile = {
  user_id: string;
  telegram_id: number | null;
  name: string;
  email: string;
  subscription_status: string;
  is_suspended: boolean;
  is_deleted: boolean;
  profile_markdown: string;
  insights_json: Record<string, unknown>;
  last_analyzed_message_at: string | null;
  last_run_at: string | null;
  status: string;
  error: string | null;
  model: string | null;
  tokens_in: number;
  tokens_out: number;
  cost_usd: number;
  analyzed_messages_count: number;
};

export type OwnerUserProfilesData = {
  profiles: OwnerUserProfile[];
  error?: string | null;
};

export function emptyOwnerUserProfilesData(error: string | null = null): OwnerUserProfilesData {
  return { profiles: [], error };
}

export async function getOwnerUserProfiles(
  account: CurrentAccount,
): Promise<OwnerUserProfilesData> {
  if (!account.authenticated || !account.accessToken) {
    return emptyOwnerUserProfilesData("Brak aktywnej sesji.");
  }

  const baseUrl = fastApiBaseUrl();
  if (!baseUrl) {
    return emptyOwnerUserProfilesData("Brak konfiguracji FASTAPI_INTERNAL_BASE_URL.");
  }

  try {
    const response = await fetch(`${baseUrl}/api/admin/user-profiles`, {
      headers: {
        Authorization: `Bearer ${account.accessToken}`,
      },
      cache: "no-store",
    });

    if (!response.ok) {
      return emptyOwnerUserProfilesData(`API profili zwróciło status ${response.status}.`);
    }

    const payload = (await response.json()) as Partial<OwnerUserProfilesData>;
    return {
      profiles: Array.isArray(payload.profiles) ? payload.profiles : [],
      error: null,
    };
  } catch {
    return emptyOwnerUserProfilesData("Nie udało się pobrać profili użytkowników.");
  }
}

export async function getOwnerUserProfile(
  account: CurrentAccount,
  userId: string,
): Promise<{ profile: OwnerUserProfile | null; error?: string | null }> {
  if (!account.authenticated || !account.accessToken) {
    return { profile: null, error: "Brak aktywnej sesji." };
  }

  const baseUrl = fastApiBaseUrl();
  if (!baseUrl) {
    return { profile: null, error: "Brak konfiguracji FASTAPI_INTERNAL_BASE_URL." };
  }

  try {
    const response = await fetch(`${baseUrl}/api/admin/user-profiles/${encodeURIComponent(userId)}`, {
      headers: {
        Authorization: `Bearer ${account.accessToken}`,
      },
      cache: "no-store",
    });
    if (!response.ok) {
      return { profile: null, error: `API profilu zwróciło status ${response.status}.` };
    }
    const payload = (await response.json()) as { profile?: OwnerUserProfile };
    return { profile: payload.profile ?? null, error: null };
  } catch {
    return { profile: null, error: "Nie udało się pobrać profilu użytkownika." };
  }
}
