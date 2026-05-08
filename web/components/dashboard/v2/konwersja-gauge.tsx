import type { CrmClient } from "@/lib/crm/types";

type KonwersjaGaugeProps = {
  clients: CrmClient[];
};

export function KonwersjaGauge({ clients }: KonwersjaGaugeProps) {
  const wyslane = clients.filter((c) => c.status === "Oferta wysłana").length;
  const podpisane = clients.filter((c) => c.status === "Podpisane").length;
  const odrzucone = clients.filter((c) => c.status === "Odrzucone").length;
  const rezygnacja = clients.filter((c) => c.status === "Rezygnacja z umowy").length;
  const zamontowana = clients.filter((c) => c.status === "Zamontowana").length;

  // Closed-loop pool: offers that already converted (signed/installed) + offers
  // that didn't convert (rejected/canceled) + offers still in flight (Oferta wysłana).
  const closedSigned = podpisane + zamontowana;
  const closedLost = odrzucone + rezygnacja;
  const closedTotal = closedSigned + closedLost;
  const conversionRate = closedTotal > 0 ? closedSigned / closedTotal : 0;
  const conversionPct = Math.round(conversionRate * 100);

  const radius = 62;
  const strokeWidth = 14;
  const circumference = 2 * Math.PI * radius;
  const filledArc = (conversionPct / 100) * circumference;

  return (
    <article className="rounded-2xl border border-white/10 bg-white/[0.04] p-6">
      <header className="flex items-baseline justify-between gap-3">
        <h2 className="text-base font-semibold tracking-tight text-white">
          Konwersja <span className="font-normal text-zinc-400">· oferta → podpis</span>
        </h2>
      </header>

      <div className="mt-5 flex flex-col items-center gap-5 sm:flex-row sm:items-center">
        <div className="relative h-[160px] w-[160px] shrink-0">
          <svg viewBox="0 0 160 160" className="h-full w-full">
            <circle
              cx="80"
              cy="80"
              r={radius}
              fill="none"
              stroke="rgba(255,255,255,0.06)"
              strokeWidth={strokeWidth}
            />
            <circle
              cx="80"
              cy="80"
              r={radius}
              fill="none"
              stroke="#3DFF7A"
              strokeWidth={strokeWidth}
              strokeLinecap="round"
              strokeDasharray={`${filledArc} ${circumference}`}
              transform="rotate(-90 80 80)"
              style={{ filter: "drop-shadow(0 0 8px rgba(61,255,122,0.5))" }}
            />
          </svg>
          <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center text-center">
            <p className="text-4xl font-bold tracking-tight tabular-nums leading-none text-white">
              {conversionPct}
              <span className="text-2xl font-medium text-zinc-500">%</span>
            </p>
            <p className="mt-1 text-[10px] font-mono uppercase tracking-[0.12em] text-zinc-500">
              z domkniętych
            </p>
          </div>
        </div>
        <ul className="flex-1 space-y-0 text-sm">
          <li className="grid grid-cols-[1fr_auto] items-baseline gap-3 border-t border-white/10 py-2 first:border-t-0 first:pt-0">
            <span className="text-zinc-400">Wysłane</span>
            <span className="font-mono font-semibold text-white tabular-nums">{wyslane}</span>
          </li>
          <li className="grid grid-cols-[1fr_auto] items-baseline gap-3 border-t border-white/10 py-2">
            <span className="text-zinc-400">Podpisane</span>
            <span className="font-mono font-semibold text-[#3DFF7A] tabular-nums">{podpisane}</span>
          </li>
          <li className="grid grid-cols-[1fr_auto] items-baseline gap-3 border-t border-white/10 py-2">
            <span className="text-zinc-400">Zamontowane</span>
            <span className="font-mono font-semibold text-[#3DFF7A] tabular-nums">{zamontowana}</span>
          </li>
          <li className="grid grid-cols-[1fr_auto] items-baseline gap-3 border-t border-white/10 py-2">
            <span className="text-zinc-400">Odrzucone</span>
            <span className="font-mono font-semibold text-amber-300 tabular-nums">{odrzucone}</span>
          </li>
          <li className="grid grid-cols-[1fr_auto] items-baseline gap-3 border-t border-white/10 py-2">
            <span className="text-zinc-400">Rezygnacja</span>
            <span className="font-mono font-semibold text-rose-300 tabular-nums">{rezygnacja}</span>
          </li>
        </ul>
      </div>
    </article>
  );
}
