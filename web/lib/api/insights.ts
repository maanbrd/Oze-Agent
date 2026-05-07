import "server-only";

import { fastApiBaseUrl } from "@/lib/api/base-url";
import { getCurrentAccount } from "@/lib/api/account";

const FASTAPI_INSIGHTS_TIMEOUT_MS = 8000;

export type ActivityWeek = {
  fetchedAt: string;
  today: string;
  weekStart: string;
  weekEnd: string;
  newClients: number;
  meetingsDone: number;
  offersSent: number;
  streak: number;
  source: "live" | "unavailable";
};

export type Trend6mo = {
  fetchedAt: string;
  today: string;
  months: string[];
  series: {
    newClients: number[];
    meetingsDone: number[];
    offersSent: number[];
    signed: number[];
  };
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
    FASTAPI_INSIGHTS_TIMEOUT_MS,
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

function emptyActivityWeek(): ActivityWeek {
  const today = new Date().toISOString().slice(0, 10);
  return {
    fetchedAt: new Date().toISOString(),
    today,
    weekStart: today,
    weekEnd: today,
    newClients: 0,
    meetingsDone: 0,
    offersSent: 0,
    streak: 0,
    source: "unavailable",
  };
}

export async function getActivityWeek(): Promise<ActivityWeek> {
  try {
    const response = await authedFetch("/api/insights/activity-week");
    if (!response.ok) return emptyActivityWeek();
    return (await response.json()) as ActivityWeek;
  } catch {
    return emptyActivityWeek();
  }
}

function emptyTrend6mo(): Trend6mo {
  const today = new Date();
  const months: string[] = [];
  let year = today.getFullYear();
  let month = today.getMonth() + 1;
  for (let i = 0; i < 6; i += 1) {
    months.unshift(`${year}-${String(month).padStart(2, "0")}`);
    month -= 1;
    if (month === 0) {
      month = 12;
      year -= 1;
    }
  }
  return {
    fetchedAt: new Date().toISOString(),
    today: today.toISOString().slice(0, 10),
    months,
    series: {
      newClients: new Array(6).fill(0),
      meetingsDone: new Array(6).fill(0),
      offersSent: new Array(6).fill(0),
      signed: new Array(6).fill(0),
    },
    source: "unavailable",
  };
}

export async function getTrend6mo(): Promise<Trend6mo> {
  try {
    const response = await authedFetch("/api/insights/trend-6mo");
    if (!response.ok) return emptyTrend6mo();
    return (await response.json()) as Trend6mo;
  } catch {
    return emptyTrend6mo();
  }
}
