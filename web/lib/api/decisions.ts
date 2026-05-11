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

export type DecisionResult =
  | { ok: true }
  | { ok: false; code: string };

export type ScheduleCallResult =
  | { ok: true; eventId: string | null; sheetsSynced: boolean }
  | { ok: false; code: string };

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

export async function changeClientStatus(
  row: number,
  newStatus: FunnelStatus,
): Promise<DecisionResult> {
  try {
    const response = await authedFetch("/api/decisions/change-status", {
      method: "POST",
      body: JSON.stringify({ row, new_status: newStatus }),
    });
    if (!response.ok) {
      return { ok: false, code: `http_${response.status}` };
    }
    const payload = (await response.json()) as { success: boolean; error_code?: string };
    if (!payload.success) return { ok: false, code: payload.error_code ?? "unknown" };
    return { ok: true };
  } catch (e) {
    return { ok: false, code: e instanceof Error ? e.message : "fetch_failed" };
  }
}

export async function touchClientContact(row: number): Promise<DecisionResult> {
  try {
    const response = await authedFetch("/api/decisions/touch-contact", {
      method: "POST",
      body: JSON.stringify({ row }),
    });
    if (!response.ok) return { ok: false, code: `http_${response.status}` };
    const payload = (await response.json()) as { success: boolean; error_code?: string };
    if (!payload.success) return { ok: false, code: payload.error_code ?? "unknown" };
    return { ok: true };
  } catch (e) {
    return { ok: false, code: e instanceof Error ? e.message : "fetch_failed" };
  }
}

export async function scheduleClientCall(input: {
  row: number;
  date: string;
  time: string;
  note: string;
  mode: "create" | "overwrite" | "cancel-only";
}): Promise<ScheduleCallResult> {
  try {
    const response = await authedFetch("/api/decisions/schedule-call", {
      method: "POST",
      body: JSON.stringify(input),
    });
    if (!response.ok) return { ok: false, code: `http_${response.status}` };
    const payload = (await response.json()) as {
      success: boolean;
      error_code?: string;
      event_id?: string | null;
      sheets_synced?: boolean;
    };
    if (!payload.success) return { ok: false, code: payload.error_code ?? "unknown" };
    return {
      ok: true,
      eventId: payload.event_id ?? null,
      sheetsSynced: Boolean(payload.sheets_synced),
    };
  } catch (e) {
    return { ok: false, code: e instanceof Error ? e.message : "fetch_failed" };
  }
}
