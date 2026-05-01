import "server-only";

import { fastApiBaseUrl } from "@/lib/api/base-url";
import { getCurrentAccount } from "@/lib/api/account";
import { mockCrmDashboardData } from "@/lib/crm/mock-data";
import type { CrmDashboardData } from "@/lib/crm/types";
import { trustedExternalUrl } from "@/lib/routes";

const CRM_SOURCES = {
  clients: "sheets",
  events: "calendar",
} as const;

const GOOGLE_WORKSPACE_ORIGINS = [
  "https://docs.google.com",
  "https://calendar.google.com",
  "https://drive.google.com",
];
const CRM_FETCH_TIMEOUT_MS = 8000;

function unavailableData(message: string): CrmDashboardData {
  return {
    fetchedAt: new Date().toISOString(),
    source: "unavailable",
    sourceMessage: message,
    clients: [],
    events: [],
  };
}

function demoData(): CrmDashboardData {
  return {
    ...mockCrmDashboardData,
    source: "demo",
    sourceMessage:
      "Dane demo. Po onboardingu panel czyta CRM z Google Sheets i Calendar.",
  };
}

function googleWorkspaceUrl(value: string | null) {
  if (!value) return null;
  return trustedExternalUrl(value, GOOGLE_WORKSPACE_ORIGINS);
}

function sanitizeGoogleLinks(data: CrmDashboardData): CrmDashboardData {
  return {
    ...data,
    clients: data.clients.map((client) => ({
      ...client,
      sheetsUrl: googleWorkspaceUrl(client.sheetsUrl),
      calendarUrl: googleWorkspaceUrl(client.calendarUrl),
      driveUrl: googleWorkspaceUrl(client.driveUrl),
    })),
    events: data.events.map((event) => ({
      ...event,
      calendarUrl: googleWorkspaceUrl(event.calendarUrl),
    })),
  };
}

async function fetchCrm(url: string, accessToken: string) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), CRM_FETCH_TIMEOUT_MS);

  try {
    return await fetch(url, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "X-OZE-CRM-Sources": `${CRM_SOURCES.clients},${CRM_SOURCES.events}`,
      },
      cache: "no-store",
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timeout);
  }
}

export async function getCrmDashboardData(): Promise<CrmDashboardData> {
  const account = await getCurrentAccount();
  const baseUrl = fastApiBaseUrl();

  if (!account.authenticated || !account.accessToken || !baseUrl) {
    return demoData();
  }

  const completed = Boolean(account.profile?.onboarding_completed);

  let response: Response;
  try {
    response = await fetchCrm(
      `${baseUrl}/api/dashboard/crm`,
      account.accessToken,
    );
  } catch {
    return completed
      ? unavailableData(
          "Nie udało się połączyć z API Google. Otwórz Sheets lub Calendar bezpośrednio.",
        )
      : demoData();
  }

  if (!response.ok) {
    return completed
      ? unavailableData(
          "Nie udało się pobrać danych z Google. Otwórz Sheets lub Calendar bezpośrednio.",
        )
      : demoData();
  }

  const data = (await response.json()) as CrmDashboardData;
  return sanitizeGoogleLinks({
    ...data,
    source: data.source ?? "live",
    sourceMessage: data.sourceMessage ?? "Dane z Google Sheets i Calendar.",
  });
}
