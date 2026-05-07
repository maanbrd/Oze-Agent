import type { LeadSources } from "@/lib/api/insights";

export function TopZrodla({ sources }: { sources: LeadSources }) {
  const offline = sources.source !== "live";
  const rows = sources.rows;
  const maxCount = rows.reduce((max, r) => Math.max(max, r.totalCount), 0);

  return (
    <section className="rounded-[8px] border border-white/10 bg-white/[0.04] p-5">
      <div className="mb-4 flex items-baseline justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-[#3DFF7A]">
            Top 3 źródła leadów
          </p>
          <h2 className="mt-1 text-sm font-semibold text-white">
            Skąd przychodzą klienci i którzy podpisują
          </h2>
        </div>
        {offline ? (
          <span className="rounded-full border border-amber-300/40 bg-amber-300/10 px-2 py-0.5 text-[10px] font-semibold uppercase text-amber-300">
            offline
          </span>
        ) : null}
      </div>

      {rows.length === 0 ? (
        <p className="text-sm text-zinc-500">
          {"Brak danych w kolumnie „Źródło pozyskania”. Uzupełnij Sheets, żeby zobaczyć ranking."}
        </p>
      ) : (
        <div className="space-y-3">
          {rows.map((row) => (
            <SourceBar key={row.source} row={row} maxCount={maxCount} />
          ))}
        </div>
      )}

      <p className="mt-4 text-[11px] text-zinc-500">
        Łącznie {sources.totalClients} {plural(sources.totalClients, "klient", "klientów", "klientów")}
        {" · "}
        {sources.totalSigned} {plural(sources.totalSigned, "podpisany", "podpisanych", "podpisanych")}
      </p>
    </section>
  );
}

function SourceBar({ row, maxCount }: { row: LeadSources["rows"][number]; maxCount: number }) {
  const widthPct = maxCount > 0 ? Math.max(6, (row.totalCount / maxCount) * 100) : 6;
  const ratePct = Math.round(row.conversionRate * 1000) / 10;

  return (
    <div className="grid grid-cols-[1fr_auto] items-center gap-4">
      <div>
        <div className="mb-1 flex items-baseline justify-between gap-3">
          <span className="text-sm font-semibold text-white">{row.source}</span>
          <span className="text-xs text-zinc-400 tabular-nums">
            {row.totalCount} {plural(row.totalCount, "klient", "klientów", "klientów")}
          </span>
        </div>
        <div className="h-2 w-full rounded-full bg-white/10">
          <div
            className="h-2 rounded-full bg-[#3DFF7A]"
            style={{ width: `${widthPct.toFixed(1)}%` }}
          />
        </div>
      </div>
      <div className="min-w-[120px] text-right">
        <span className="text-sm font-semibold tabular-nums text-[#3DFF7A]">
          {ratePct.toFixed(0)}%
        </span>
        <span className="ml-1 text-[11px] text-zinc-500">do Podpisane</span>
      </div>
    </div>
  );
}

function plural(n: number, one: string, few: string, many: string): string {
  if (n === 1) return one;
  const last2 = n % 100;
  if (last2 >= 12 && last2 <= 14) return many;
  const last = n % 10;
  if (last >= 2 && last <= 4) return few;
  return many;
}
