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

export async function getCrmDashboardData(): Promise<CrmDashboardData> {
  const account = await getCurrentAccount();
  const baseUrl = apiBaseUrl();

  if (!account.authenticated || !account.accessToken || !baseUrl) {
    return mockCrmDashboardData;
  }

  const response = await fetch(`${baseUrl}/api/dashboard/crm`, {
    headers: {
      Authorization: `Bearer ${account.accessToken}`,
      "X-OZE-CRM-Sources": `${CRM_SOURCES.clients},${CRM_SOURCES.events}`,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    return mockCrmDashboardData;
  }

  return (await response.json()) as CrmDashboardData;
}
