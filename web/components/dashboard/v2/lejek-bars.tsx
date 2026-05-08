import type { CrmClient, FunnelStatus } from "@/lib/crm/types";

type LejekBarsProps = {
  clients: CrmClient[];
};

const STATUSES: FunnelStatus[] = [
  "Nowy lead",
  "Spotkanie umówione",
  "Spotkanie odbyte",
  "Oferta wysłana",
  "Podpisane",
  "Zamontowana",
  "Rezygnacja z umowy",
  "Nieaktywny",
  "Odrzucone",
];

const SIGNED_STATUSES = new Set<FunnelStatus>(["Podpisane", "Zamontowana"]);

export function LejekBars({ clients }: LejekBarsProps) {
  const counts: Record<FunnelStatus, number> = STATUSES.reduce(
    (acc, status) => ({ ...acc, [status]: 0 }),
    {} as Record<FunnelStatus, number>,
  );
  for (const client of clients) {
    if (client.status in counts) {
      counts[client.status as FunnelStatus] += 1;
    }
  }
  const max = Math.max(...Object.values(counts), 1);

  return (
    <article className="rounded-2xl border border-white/10 bg-white/[0.04] p-6">
      <header className="flex items-baseline justify-between gap-3">
        <h2 className="text-base font-semibold tracking-tight text-white">Lejek</h2>
        <p className="text-xs font-mono text-zinc-500">{clients.length} klientów</p>
      </header>

      <ul className="mt-5 space-y-2.5">
        {STATUSES.map((status) => {
          const count = counts[status];
          const widthPct = max > 0 ? Math.max(2, (count / max) * 100) : 2;
          const isSigned = SIGNED_STATUSES.has(status);
          return (
            <li key={status} className="grid grid-cols-[1fr_auto] items-baseline gap-3">
              <div className="grid grid-cols-1 gap-1">
                <div className="grid grid-cols-[1fr_auto] items-baseline gap-3">
                  <span className="text-sm text-zinc-300">{status}</span>
                  <span
                    className={`font-mono text-sm font-semibold tabular-nums tracking-tight ${
                      isSigned ? "text-[#3DFF7A]" : "text-white"
                    }`}
                  >
                    {count}
                  </span>
                </div>
                <div className="h-1 overflow-hidden rounded-full bg-white/[0.06]">
                  <div
                    className={`h-full rounded-full ${
                      isSigned
                        ? "bg-[#3DFF7A] shadow-[0_0_8px_rgba(61,255,122,0.5)]"
                        : "bg-white"
                    }`}
                    style={{ width: `${widthPct}%` }}
                  />
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </article>
  );
}
