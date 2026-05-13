import type { CrmClient, CrmEvent } from "@/lib/crm/types";
import { warsawDateKey, warsawDateKeyFromIso } from "@/lib/dates";

type WatchListProps = {
  urgentClients: CrmClient[];
  tomorrowEvents: CrmEvent[];
  offers: CrmClient[];
  now?: Date;
};

type Alert = {
  who: string;
  why: string;
  pill: { kind: "warn" | "live" | "flat"; text: string };
};

const PILL_STYLES: Record<Alert["pill"]["kind"], string> = {
  warn: "bg-amber-400/15 text-amber-300",
  live: "bg-[#3DFF7A]/15 text-[#3DFF7A]",
  flat: "bg-white/10 text-zinc-300",
};

function daysSince(iso: string, now: Date): number {
  const past = new Date(iso);
  if (Number.isNaN(past.getTime())) return 0;
  return Math.max(0, Math.floor((now.getTime() - past.getTime()) / 86_400_000));
}

function formatClientName(client: CrmClient): string {
  return client.city ? `${client.fullName} · ${client.city}` : client.fullName;
}

function buildAlerts(
  urgentClients: CrmClient[],
  tomorrowEvents: CrmEvent[],
  offers: CrmClient[],
  now: Date,
): Alert[] {
  const alerts: Alert[] = [];
  const seenIds = new Set<string>();

  const staleOffers = offers
    .filter((client) => client.lastContactAt)
    .map((client) => ({ client, age: daysSince(client.lastContactAt as string, now) }))
    .filter(({ age }) => age >= 5)
    .sort((a, b) => b.age - a.age);

  for (const { client, age } of staleOffers.slice(0, 2)) {
    seenIds.add(client.id);
    alerts.push({
      who: formatClientName(client),
      why: `Oferta wysłana ${age} ${age === 1 ? "dzień" : "dni"} temu, brak reakcji`,
      pill: { kind: "warn", text: `${age} ${age === 1 ? "dzień" : "dni"}` },
    });
  }

  for (const event of tomorrowEvents.slice(0, 2)) {
    if (event.clientId && seenIds.has(event.clientId)) continue;
    if (event.clientId) seenIds.add(event.clientId);
    alerts.push({
      who: event.city ? `${event.clientName} · ${event.city}` : event.clientName,
      why: event.title,
      pill: { kind: "live", text: "jutro" },
    });
  }

  const todayKey = warsawDateKey(now);
  for (const client of urgentClients) {
    if (seenIds.has(client.id)) continue;
    if (alerts.length >= 5) break;
    seenIds.add(client.id);

    let pillText = "dziś";
    if (client.nextActionAt) {
      const actionDayKey = warsawDateKeyFromIso(client.nextActionAt);
      if (actionDayKey && actionDayKey < todayKey) {
        pillText = "spóźnione";
      }
    }

    alerts.push({
      who: formatClientName(client),
      why: client.nextAction ?? client.status,
      pill: { kind: "live", text: pillText },
    });
  }

  return alerts.slice(0, 5);
}

export function WatchList({ urgentClients, tomorrowEvents, offers, now }: WatchListProps) {
  const ref = now ?? new Date();
  const alerts = buildAlerts(urgentClients, tomorrowEvents, offers, ref);

  return (
    <article className="flex h-full flex-col rounded-2xl border border-white/10 bg-white/[0.04] p-6">
      <p className="flex items-center gap-2 text-xs font-medium uppercase tracking-[0.14em] text-amber-300">
        <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-amber-300 shadow-[0_0_8px_#FACC15]" />
        Wymagają uwagi
        {alerts.length > 0 ? <span className="text-amber-300/70">· {alerts.length}</span> : null}
      </p>
      <h2 className="mt-3 text-xl font-bold tracking-tight leading-tight text-white">
        {alerts.length === 0
          ? "Wszystko pod kontrolą."
          : "Zamknij follow-upy zanim ostygną."}
      </h2>

      {alerts.length === 0 ? (
        <p className="mt-4 text-sm text-zinc-500">
          Brak ofert powyżej 5 dni ciszy, żadnych spotkań jutro.
        </p>
      ) : (
        <ul className="mt-5 space-y-0">
          {alerts.map((alert, idx) => (
            <li
              key={`${alert.who}-${idx}`}
              className="grid grid-cols-[1fr_auto] items-start gap-3 border-t border-white/10 py-3 first:border-t-0 first:pt-0"
            >
              <div>
                <p className="text-sm font-semibold text-white">{alert.who}</p>
                <p className="mt-1 text-xs text-zinc-400">{alert.why}</p>
              </div>
              <span
                className={`shrink-0 rounded-md px-2 py-0.5 text-xs font-mono font-medium ${PILL_STYLES[alert.pill.kind]}`}
              >
                {alert.pill.text}
              </span>
            </li>
          ))}
        </ul>
      )}

      <a
        href="https://t.me/AgentOZE_Bot"
        target="_blank"
        rel="noopener noreferrer"
        className="mt-auto pt-5 text-sm font-mono font-medium tracking-wider text-[#3DFF7A] hover:text-[#6BFFA0]"
      >
        → otwórz kolejkę w Telegramie
      </a>
    </article>
  );
}
