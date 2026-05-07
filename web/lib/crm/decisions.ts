import type { FunnelStatus } from "@/lib/crm/types";

export type TransitionTone = "happy" | "stay" | "out";

export type Transition = {
  next: FunnelStatus;
  label: string;
  tone: TransitionTone;
};

export const STALENESS_DAYS = 7;

/**
 * Same canonical mapping as oze-agent/api/routes/decisions.py NEXT_STEP_AFTER_STATUS.
 * Mirrors live there too (Python is source of truth) — keep in sync.
 */
export const TRANSITIONS: Partial<Record<FunnelStatus, Transition[]>> = {
  "Nowy lead": [
    { next: "Spotkanie umówione", label: "✓ Umówione", tone: "happy" },
    { next: "Nowy lead", label: "Czeka na kontakt", tone: "stay" },
    { next: "Odrzucone", label: "✗ Odrzucone", tone: "out" },
  ],
  "Spotkanie umówione": [
    { next: "Spotkanie odbyte", label: "✓ Odbyte", tone: "happy" },
    { next: "Spotkanie umówione", label: "Nadal czeka", tone: "stay" },
    { next: "Nieaktywny", label: "✗ Nieaktywny", tone: "out" },
  ],
  "Spotkanie odbyte": [
    { next: "Oferta wysłana", label: "✓ Wysłałem ofertę", tone: "happy" },
    { next: "Spotkanie odbyte", label: "Jeszcze przygotowuję", tone: "stay" },
    { next: "Nieaktywny", label: "✗ Nieaktywny", tone: "out" },
  ],
  "Oferta wysłana": [
    { next: "Podpisane", label: "✓ Podpisane", tone: "happy" },
    { next: "Oferta wysłana", label: "Czekam na decyzję", tone: "stay" },
    { next: "Rezygnacja z umowy", label: "✗ Rezygnacja", tone: "out" },
  ],
  Podpisane: [
    { next: "Zamontowana", label: "✓ Zamontowana", tone: "happy" },
    { next: "Podpisane", label: "Czeka na montaż", tone: "stay" },
    { next: "Rezygnacja z umowy", label: "✗ Rezygnacja", tone: "out" },
  ],
};

export function transitionsForStatus(s: FunnelStatus): Transition[] {
  return TRANSITIONS[s] ?? [];
}

export function pad2(n: number): string {
  return String(n).padStart(2, "0");
}

export function tomorrowDateString(): string {
  const dt = new Date();
  dt.setDate(dt.getDate() + 1);
  return `${dt.getFullYear()}-${pad2(dt.getMonth() + 1)}-${pad2(dt.getDate())}`;
}

const POLISH_DAY_SHORT = ["niedz.", "pn.", "wt.", "śr.", "czw.", "pt.", "sob."];

export function formatScheduleLabel(dateIso: string, timeHHMM: string): string {
  if (!dateIso || !timeHHMM) return "";
  const [y, m, d] = dateIso.split("-").map((s) => parseInt(s, 10));
  if (!y || !m || !d) return `${dateIso} ${timeHHMM}`;
  const dt = new Date(y, m - 1, d);
  const dayName = POLISH_DAY_SHORT[dt.getDay()] ?? "";
  return `${pad2(d)}.${pad2(m)} (${dayName}) ${timeHHMM}`;
}

/**
 * Returns CSS-friendly color tokens for the staleness pill on each card.
 * 0–6 days = neon green, 7–9 days = amber warning, 10+ days = red urgency.
 */
export function stalenessColor(days: number): string {
  if (days >= 10) return "#EF4444";
  if (days >= 7) return "#FBBF24";
  return "#3DFF7A";
}

/**
 * Returns Tailwind-style classes for the sidebar "Wymagają decyzji" badge.
 * Matches the prototype convention: 1–7 green, 8–15 amber, 16+ red, 0 hidden.
 */
export function decisionsBadgeClasses(count: number): string {
  if (count <= 0) return "text-zinc-500 border-white/10 bg-white/5";
  if (count <= 7) return "text-[#3DFF7A] border-[#3DFF7A]/40 bg-[#3DFF7A]/10";
  if (count <= 15) return "text-amber-300 border-amber-300/40 bg-amber-300/10";
  return "text-red-400 border-red-400/40 bg-red-400/10";
}
