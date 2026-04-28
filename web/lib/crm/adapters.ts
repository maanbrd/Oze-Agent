import "server-only";

import { getCurrentAccount } from "@/lib/api/account";
import { mockCrmDashboardData } from "@/lib/crm/mock-data";
import type { CrmDashboardData } from "@/lib/crm/types";

const CRM_SOURCES = {
  clients: "sheets",
  events: "calendar",
} as const;

function apiBaseUrl() {
  return (
    process.env.FASTAPI_INTERNAL_BASE_URL ??
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    ""
  ).replace(/\/$/, "");
}

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

export async function getCrmDashboardData(): Promise<CrmDashboardData> {
  const account = await getCurrentAccount();
  const baseUrl = apiBaseUrl();

  if (!account.authenticated || !account.accessToken || !baseUrl) {
    return demoData();
  }

  const completed = Boolean(account.profile?.onboarding_completed);

  const response = await fetch(`${baseUrl}/api/dashboard/crm`, {
    headers: {
      Authorization: `Bearer ${account.accessToken}`,
      "X-OZE-CRM-Sources": `${CRM_SOURCES.clients},${CRM_SOURCES.events}`,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    return completed
      ? unavailableData(
          "Nie udało się pobrać danych z Google. Otwórz Sheets lub Calendar bezpośrednio.",
        )
      : demoData();
  }

  const data = (await response.json()) as CrmDashboardData;
  return {
    ...data,
    source: data.source ?? "live",
    sourceMessage: data.sourceMessage ?? "Dane z Google Sheets i Calendar.",
  };
}
