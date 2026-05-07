import type { CrmClient, CrmEvent, FunnelStatus } from "@/lib/crm/types";
import { formatWarsawTime, warsawDateKey, warsawDateKeyFromIso } from "@/lib/dates";

export const OPEN_STATUSES = new Set<FunnelStatus>([
  "Nowy lead",
  "Spotkanie umówione",
  "Spotkanie odbyte",
  "Oferta wysłana",
  "Podpisane",
]);

const MONTH_LOCATIVE_PL = [
  "styczniu",
  "lutym",
  "marcu",
  "kwietniu",
  "maju",
  "czerwcu",
  "lipcu",
  "sierpniu",
  "wrześniu",
  "październiku",
  "listopadzie",
  "grudniu",
];

export function countActiveClients(clients: CrmClient[]): number {
  return clients.filter((client) => OPEN_STATUSES.has(client.status)).length;
}

function daysSince(iso: string, now: Date): number {
  const past = new Date(iso);
  if (Number.isNaN(past.getTime())) return 0;
  const diffMs = now.getTime() - past.getTime();
  return Math.max(0, Math.floor(diffMs / 86_400_000));
}

export function oldestOfferStaleDays(clients: CrmClient[], now = new Date()): number | null {
  const offers = clients.filter((client) => client.status === "Oferta wysłana");
  if (offers.length === 0) return null;
  let max = 0;
  let seen = false;
  for (const client of offers) {
    if (!client.lastContactAt) continue;
    const days = daysSince(client.lastContactAt, now);
    if (days > max) max = days;
    seen = true;
  }
  return seen ? max : null;
}

function warsawYearMonthFromIso(iso: string): string | null {
  const key = warsawDateKeyFromIso(iso);
  return key ? key.slice(0, 7) : null;
}

function warsawYearMonth(now = new Date()): string {
  return warsawDateKey(now).slice(0, 7);
}

function previousWarsawYearMonth(now = new Date()): { ym: string; monthIndex: number } {
  const todayKey = warsawDateKey(now);
  const [yStr, mStr] = todayKey.split("-");
  const year = parseInt(yStr, 10);
  const month = parseInt(mStr, 10);
  const prevMonth = month === 1 ? 12 : month - 1;
  const prevYear = month === 1 ? year - 1 : year;
  const ym = `${prevYear}-${String(prevMonth).padStart(2, "0")}`;
  return { ym, monthIndex: prevMonth - 1 };
}

export function signedInMonth(clients: CrmClient[], yearMonth: string): number {
  return clients.filter((client) => {
    if (client.status !== "Podpisane") return false;
    if (!client.lastContactAt) return false;
    return warsawYearMonthFromIso(client.lastContactAt) === yearMonth;
  }).length;
}

export function signedThisMonth(clients: CrmClient[], now = new Date()): number {
  return signedInMonth(clients, warsawYearMonth(now));
}

export function signedPreviousMonth(clients: CrmClient[], now = new Date()): {
  count: number;
  monthLabel: string;
} {
  const { ym, monthIndex } = previousWarsawYearMonth(now);
  return {
    count: signedInMonth(clients, ym),
    monthLabel: MONTH_LOCATIVE_PL[monthIndex] ?? ym,
  };
}

export function formatTodayMeetingTimes(events: CrmEvent[]): string {
  if (events.length === 0) return "—";
  return events
    .slice()
    .sort((a, b) => a.startsAt.localeCompare(b.startsAt))
    .map((event) => formatWarsawTime(event.startsAt))
    .join(" · ");
}

function pad2(n: number): string {
  return String(n).padStart(2, "0");
}

function shiftDateKey(key: string, days: number): string {
  const [y, m, d] = key.split("-").map((s) => parseInt(s, 10));
  if (!y || !m || !d) return key;
  const dt = new Date(Date.UTC(y, m - 1, d, 12));
  dt.setUTCDate(dt.getUTCDate() + days);
  return `${dt.getUTCFullYear()}-${pad2(dt.getUTCMonth() + 1)}-${pad2(dt.getUTCDate())}`;
}

function mondayOffsetFromKey(key: string): number {
  const [y, m, d] = key.split("-").map((s) => parseInt(s, 10));
  if (!y || !m || !d) return 0;
  const dow = new Date(Date.UTC(y, m - 1, d, 12)).getUTCDay();
  return (dow + 6) % 7;
}

export function meetingsThisWeek(
  events: CrmEvent[],
  now = new Date(),
): { total: number; past: number } {
  const todayKey = warsawDateKey(now);
  const fromMon = mondayOffsetFromKey(todayKey);
  const weekStartKey = shiftDateKey(todayKey, -fromMon);
  const weekEndKey = shiftDateKey(todayKey, 6 - fromMon);
  const cutoffMs = now.getTime();

  let total = 0;
  let past = 0;
  for (const event of events) {
    const evKey = warsawDateKeyFromIso(event.startsAt);
    if (!evKey) continue;
    if (evKey < weekStartKey || evKey > weekEndKey) continue;
    total += 1;
    const startMs = new Date(event.startsAt).getTime();
    if (Number.isFinite(startMs) && startMs < cutoffMs) past += 1;
  }
  return { total, past };
}

export function daysLeftInMonth(now = new Date()): number {
  const todayKey = warsawDateKey(now);
  const [y, m, d] = todayKey.split("-").map((s) => parseInt(s, 10));
  if (!y || !m || !d) return 0;
  const lastDayOfMonth = new Date(Date.UTC(y, m, 0)).getUTCDate();
  return Math.max(0, lastDayOfMonth - d);
}
