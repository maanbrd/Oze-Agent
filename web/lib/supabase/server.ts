import { cookies } from "next/headers";
import { createServerClient } from "@supabase/ssr";

type SupabaseEnvStatus =
  | {
      configured: true;
      url: string;
      key: string;
      missing: [];
    }
  | {
      configured: false;
      url: null;
      key: null;
      missing: string[];
    };

function envValue(...names: string[]) {
  for (const name of names) {
    const value = process.env[name]?.trim();

    if (value && value !== `""` && value !== "''") {
      return value;
    }
  }

  return null;
}

export function getSupabaseEnvStatus(): SupabaseEnvStatus {
  const url = envValue("NEXT_PUBLIC_SUPABASE_URL", "SUPABASE_URL");
  const key = envValue(
    "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY",
    "NEXT_PUBLIC_SUPABASE_ANON_KEY",
    "SUPABASE_KEY",
  );

  if (!url || !key) {
    const missing: string[] = [];
    if (!url) {
      missing.push("NEXT_PUBLIC_SUPABASE_URL albo SUPABASE_URL");
    }
    if (!key) {
      missing.push(
        "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY, NEXT_PUBLIC_SUPABASE_ANON_KEY albo SUPABASE_KEY",
      );
    }

    return {
      configured: false,
      url: null,
      key: null,
      missing,
    };
  }

  return { configured: true, url, key, missing: [] };
}

function requireSupabaseEnv() {
  const status = getSupabaseEnvStatus();

  if (!status.configured) {
    throw new Error(`Missing ${status.missing.join(" and ")}`);
  }

  return { url: status.url, key: status.key };
}

export function missingSupabaseEnvMessage() {
  const status = getSupabaseEnvStatus();

  if (status.configured) {
    return null;
  }

  return `Brak konfiguracji Supabase: ${status.missing.join(", ")}.`;
}

export function missingSupabaseEnvRedirectMessage() {
  const status = getSupabaseEnvStatus();

  if (status.configured) {
    return null;
  }

  return "Brak konfiguracji Supabase dla web appu. Ustaw zmienne środowiskowe i zrestartuj serwer.";
}

export async function createClient() {
  const cookieStore = await cookies();
  const { url, key } = requireSupabaseEnv();

  return createServerClient(url, key, {
    cookies: {
      getAll() {
        return cookieStore.getAll();
      },
      setAll(cookiesToSet) {
        try {
          cookiesToSet.forEach(({ name, value, options }) => {
            cookieStore.set(name, value, options);
          });
        } catch {
          // Server Components cannot write cookies. Server Actions and middleware can.
        }
      },
    },
  });
}
