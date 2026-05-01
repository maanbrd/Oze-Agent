import "server-only";

import { fastApiBaseUrl } from "@/lib/api/base-url";
import { getCurrentAccount } from "@/lib/api/account";

export type OnboardingStatus = {
  fetchedAt: string;
  nextStep: string;
  completed: boolean;
  steps: {
    payment: boolean;
    google: boolean;
    resources: boolean;
    telegram: boolean;
  };
  profile: Record<string, unknown> | null;
};

export type TelegramPairingStatus = {
  paired: boolean;
  telegramId: number | null;
  code: string | null;
  expiresAt: string | null;
};

const FASTAPI_ONBOARDING_TIMEOUT_MS = 8000;

async function fetchOnboarding(url: string, init: RequestInit) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), FASTAPI_ONBOARDING_TIMEOUT_MS);

  try {
    return await fetch(url, {
      ...init,
      cache: "no-store",
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timeout);
  }
}

async function authedFetch(path: string, init: RequestInit = {}) {
  const account = await getCurrentAccount();
  const baseUrl = fastApiBaseUrl();

  if (!account.authenticated || !account.accessToken) {
    throw new Error("Brak aktywnej sesji.");
  }

  if (!baseUrl) {
    throw new Error("Brak konfiguracji FASTAPI_INTERNAL_BASE_URL.");
  }

  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer ${account.accessToken}`);
  headers.set("Content-Type", "application/json");

  const response = await fetchOnboarding(`${baseUrl}${path}`, {
    ...init,
    headers,
  });

  if (!response.ok) {
    throw new Error(`API error ${response.status}`);
  }

  return response;
}

export async function getOnboardingStatus(): Promise<OnboardingStatus | null> {
  try {
    const response = await authedFetch("/api/onboarding/status");
    return (await response.json()) as OnboardingStatus;
  } catch {
    return null;
  }
}

export async function startGoogleOAuth(): Promise<string> {
  const response = await authedFetch("/api/onboarding/google/oauth-url", {
    method: "POST",
    body: "{}",
  });
  const payload = (await response.json()) as { url: string };
  return payload.url;
}

export async function createGoogleResources(input: {
  sheetsName?: string;
  calendarName?: string;
}) {
  const response = await authedFetch("/api/onboarding/resources", {
    method: "POST",
    body: JSON.stringify(input),
  });
  return response.json();
}

export async function generateTelegramCode(): Promise<TelegramPairingStatus> {
  const response = await authedFetch("/api/onboarding/telegram-code", {
    method: "POST",
    body: "{}",
  });
  return (await response.json()) as TelegramPairingStatus;
}

export async function getTelegramStatus(): Promise<TelegramPairingStatus | null> {
  try {
    const response = await authedFetch("/api/onboarding/telegram-status");
    return (await response.json()) as TelegramPairingStatus;
  } catch {
    return null;
  }
}

export async function updateAccount(input: { name?: string; phone?: string }) {
  const response = await authedFetch("/api/onboarding/account", {
    method: "PATCH",
    body: JSON.stringify(input),
  });
  return response.json();
}
