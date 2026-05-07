import { Sparkline } from "@/components/dashboard/sparkline";
import type { Trend6mo } from "@/lib/api/insights";

type SeriesKey = "newClients" | "meetingsDone" | "offersSent" | "signed";

const SERIES_LABELS: Record<SeriesKey, string> = {
  newClients: "Nowi klienci",
  meetingsDone: "Spotkania odbyte",
  offersSent: "Oferty wysłane",
  signed: "Podpisani",
};

const POLISH_MONTH_SHORT: Record<string, string> = {
  "01": "sty",
  "02": "lut",
  "03": "mar",
  "04": "kwi",
  "05": "maj",
  "06": "cze",
  "07": "lip",
  "08": "sie",
  "09": "wrz",
  "10": "paź",
  "11": "lis",
  "12": "gru",
};

export function Trend6mo({ trend }: { trend: Trend6mo }) {
  const offline = trend.source !== "live";
  const months = trend.months;
  const lastMonthLabel = months.length > 0 ? polishMonthLabel(months[months.length - 1]) : "";
  const prevMonthLabel = months.length > 1 ? polishMonthLabel(months[months.length - 2]) : "";

  const series: SeriesKey[] = ["newClients", "meetingsDone", "offersSent", "signed"];

  return (
    <section className="rounded-[8px] border border-white/10 bg-white/[0.04] p-5">
      <div className="mb-4 flex items-baseline justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-[#3DFF7A]">
            Trend 6 miesięcy
          </p>
          <h2 className="mt-1 text-sm font-semibold text-white">
            Jak idzie miesiąc do miesiąca
          </h2>
        </div>
        {offline ? (
          <span className="rounded-full border border-amber-300/40 bg-amber-300/10 px-2 py-0.5 text-[10px] font-semibold uppercase text-amber-300">
            offline
          </span>
        ) : null}
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {series.map((key) => (
          <SeriesCard
            key={key}
            label={SERIES_LABELS[key]}
            data={trend.series[key]}
            lastMonthLabel={lastMonthLabel}
            prevMonthLabel={prevMonthLabel}
          />
        ))}
      </div>

      {months.length > 0 ? (
        <p className="mt-3 text-[11px] uppercase tracking-wider text-zinc-500">
          {polishMonthLabel(months[0])} → {lastMonthLabel}
        </p>
      ) : null}
    </section>
  );
}

function SeriesCard({
  label,
  data,
  lastMonthLabel,
  prevMonthLabel,
}: {
  label: string;
  data: number[];
  lastMonthLabel: string;
  prevMonthLabel: string;
}) {
  const last = data.length > 0 ? data[data.length - 1] : 0;
  const prev = data.length > 1 ? data[data.length - 2] : 0;
  const delta = last - prev;
  const arrow = delta > 0 ? "↑" : delta < 0 ? "↓" : "→";
  const arrowColor =
    delta > 0 ? "text-[#3DFF7A]" : delta < 0 ? "text-amber-300" : "text-zinc-500";

  const deltaText = (() => {
    if (data.length < 2) return "—";
    if (delta === 0) return `bez zmian vs ${prevMonthLabel}`;
    const sign = delta > 0 ? "+" : "";
    return `${sign}${delta} vs ${prevMonthLabel}`;
  })();

  return (
    <article className="rounded-[8px] border border-white/10 bg-black/20 p-4">
      <p className="text-xs text-zinc-400">{label}</p>
      <div className="mt-2 flex items-baseline gap-2">
        <p className="text-2xl font-semibold tabular-nums text-white">{last}</p>
        <span className={`text-xs font-semibold tabular-nums ${arrowColor}`} aria-hidden="true">
          {arrow}
        </span>
        <span className="text-[11px] text-zinc-500">{lastMonthLabel}</span>
      </div>
      <div className="mt-3">
        <Sparkline data={data} ariaLabel={`${label}: ${data.join(", ")}`} />
      </div>
      <p className="mt-2 text-[11px] text-zinc-500">{deltaText}</p>
    </article>
  );
}

function polishMonthLabel(ym: string): string {
  const [yearStr, monthStr] = ym.split("-");
  const month = POLISH_MONTH_SHORT[monthStr] ?? monthStr;
  const year = (yearStr ?? "").slice(2);
  return year ? `${month} '${year}` : month;
}
