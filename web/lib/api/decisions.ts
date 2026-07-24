import "server-only";

import { fastApiBaseUrl } from "@/lib/api/base-url";
import { getCurrentAccount } from "@/lib/api/account";
import type { FunnelStatus } from "@/lib/crm/types";

const FASTAPI_DECISIONS_TIMEOUT_MS = 8000;

export type PendingClient = {
  id: string;
  row: number;
  fullName: string;
  city: string;
  phone: string | null;
  email: string | null;
  address: string | null;
  product: string | null;
  status: FunnelStatus;
  notes: string | null;
  lastContactAt: string | null;
  nextAction: string | null;
  nextActionAt: string | null;
  calendarEventId: string | null;
  staleDays: number;
};

export type PendingDecisionsResponse = {
  fetchedAt: string;
  today: string;
  count: number;
  clients: PendingClient[];
  source: "live" | "unavailable";
};

async function authedFetch(path: string, init: RequestInit = {}) {
  const account = await getCurrentAccount();
  const baseUrl = fastApiBaseUrl();

  if (!account.authenticated || !account.accessToken) {
    throw new Error("session_missing");
  }
  if (!baseUrl) {
    throw new Error("api_base_missing");
  }

  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer ${account.accessToken}`);
  headers.set("Content-Type", "application/json");

  const controller = new AbortController();
  const timeout = setTimeout(
    () => controller.abort(),
    FASTAPI_DECISIONS_TIMEOUT_MS,
  );

  try {
    return await fetch(`${baseUrl}${path}`, {
      ...init,
      cache: "no-store",
      headers,
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timeout);
  }
}

export async function getPendingDecisions(): Promise<PendingDecisionsResponse> {
  try {
    const response = await authedFetch("/api/decisions/pending");
    if (!response.ok) throw new Error(`status_${response.status}`);
    return (await response.json()) as PendingDecisionsResponse;
  } catch {
    return {
      fetchedAt: new Date().toISOString(),
      today: new Date().toISOString().slice(0, 10),
      count: 0,
      clients: [],
      source: "unavailable",
    };
  }
}

export async function getDecisionsCount(): Promise<number> {
  try {
    const response = await authedFetch("/api/decisions/count");
    if (!response.ok) return 0;
    const payload = (await response.json()) as { count: number };
    return Number(payload.count) || 0;
  } catch {
    return 0;
  }
}
