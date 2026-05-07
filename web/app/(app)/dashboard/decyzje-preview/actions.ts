"use server";

import { revalidatePath } from "next/cache";

import {
  changeClientStatus as apiChangeClientStatus,
  scheduleClientCall as apiScheduleClientCall,
  touchClientContact as apiTouchClientContact,
  type DecisionResult,
  type ScheduleCallResult,
} from "@/lib/api/decisions";
import type { FunnelStatus } from "@/lib/crm/types";

function bumpDashboard() {
  // Sidebar count badge lives in (app)/layout.tsx — invalidating "/" via the
  // "layout" segment is the cheapest way to force the count to re-fetch.
  revalidatePath("/", "layout");
}

export async function changeClientStatusAction(
  row: number,
  newStatus: FunnelStatus,
): Promise<DecisionResult> {
  const result = await apiChangeClientStatus(row, newStatus);
  if (result.ok) bumpDashboard();
  return result;
}

export async function touchClientContactAction(row: number): Promise<DecisionResult> {
  const result = await apiTouchClientContact(row);
  if (result.ok) bumpDashboard();
  return result;
}

export async function scheduleClientCallAction(input: {
  row: number;
  date: string;
  time: string;
  note: string;
  mode: "create" | "overwrite" | "cancel-only";
}): Promise<ScheduleCallResult> {
  const result = await apiScheduleClientCall(input);
  if (result.ok) bumpDashboard();
  return result;
}
