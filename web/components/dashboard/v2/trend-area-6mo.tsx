import type { Trend6mo } from "@/lib/api/insights";

type TrendArea6moProps = {
  trend: Trend6mo;
};

const POLISH_MONTH_SHORT: Record<string, string> = {
  "01": "STY",
  "02": "LUT",
  "03": "MAR",
  "04": "KWI",
  "05": "MAJ",
  "06": "CZE",
  "07": "LIP",
  "08": "SIE",
  "09": "WRZ",
  "10": "PAŹ",
  "11": "LIS",
  "12": "GRU",
};

function shortMonthLabel(ym: string): string {
  const [, monthStr] = ym.split("-");
  return POLISH_MONTH_SHORT[monthStr] ?? monthStr;
}

function buildSmoothPath(points: { x: number; y: number }[]): string {
  if (points.length === 0) return "";
  if (points.length === 1) return `M ${points[0].x} ${points[0].y}`;

  let d = `M ${points[0].x} ${points[0].y}`;
  for (let i = 0; i < points.length - 1; i++) {
    const p0 = i === 0 ? points[0] : points[i - 1];
    const p1 = points[i];
    const p2 = points[i + 1];
    const p3 = i + 2 < points.length ? points[i + 2] : p2;
    const tension = 0.5;
    const cp1x = p1.x + (p2.x - p0.x) * (tension / 3);
    const cp1y = p1.y + (p2.y - p0.y) * (tension / 3);
    const cp2x = p2.x - (p3.x - p1.x) * (tension / 3);
    const cp2y = p2.y - (p3.y - p1.y) * (tension / 3);
    d += ` C ${cp1x.toFixed(2)} ${cp1y.toFixed(2)}, ${cp2x.toFixed(2)} ${cp2y.toFixed(2)}, ${p2.x} ${p2.y}`;
  }
  return d;
}

export function TrendArea6mo({ trend }: TrendArea6moProps) {
  const offline = trend.source !== "live";
  const data = trend.series.signed;
  const months = trend.months;

  if (data.length === 0 || months.length === 0) {
    return (
      <article className="rounded-2xl border border-white/10 bg-white/[0.04] p-6">
        <h2 className="text-base font-semibold tracking-tight text-white">
          Trend 6 miesięcy <span className="font-normal text-zinc-400">· podpisane</span>
        </h2>
        <p className="mt-4 text-sm text-zinc-500">Brak danych do wyświetlenia.</p>
      </article>
    );
  }

  const max = Math.max(...data, 1);
  const min = Math.min(...data, 0);
  const range = Math.max(max - min, 1);
  const total = data.reduce((sum, n) => sum + n, 0);
  const avg = data.length > 0 ? total / data.length : 0;
  const last = data[data.length - 1];
  const prev = data.length > 1 ? data[data.length - 2] : 0;
  const monthOverMonth =
    prev > 0 ? Math.round(((last - prev) / prev) * 100) : last > 0 ? null : null;
  const peakIdx = data.indexOf(max);

  const W = 600;
  const H = 200;
  const padTop = 20;
  const padBottom = 20;
  const padLeft = 30;
  const padRight = 20;
  const innerW = W - padLeft - padRight;
  const innerH = H - padTop - padBottom;

  const stepX = data.length > 1 ? innerW / (data.length - 1) : 0;
  const points = data.map((value, i) => ({
    x: padLeft + i * stepX,
    y: padTop + innerH - ((value - min) / range) * innerH,
  }));

  const linePath = buildSmoothPath(points);
  const areaPath = `${linePath} L ${points[points.length - 1].x} ${padTop + innerH} L ${points[0].x} ${padTop + innerH} Z`;

  return (
    <article className="rounded-2xl border border-white/10 bg-white/[0.04] p-6">
      <header className="flex flex-wrap items-baseline justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold tracking-tight text-white">
            Trend 6 miesięcy <span className="font-normal text-zinc-400">· podpisane / mc</span>
          </h2>
          <p className="mt-1 text-xs font-mono text-zinc-500">
            Σ {total} · avg {avg.toFixed(1)}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {monthOverMonth !== null ? (
            <span
              className={`rounded-md px-2 py-0.5 text-xs font-medium ${
                monthOverMonth > 0
                  ? "bg-[#3DFF7A]/15 text-[#3DFF7A]"
                  : monthOverMonth < 0
                    ? "bg-rose-400/15 text-rose-300"
                    : "bg-white/10 text-zinc-300"
              }`}
            >
              {monthOverMonth > 0 ? "▲" : monthOverMonth < 0 ? "▼" : "±"} {Math.abs(monthOverMonth)}% m/m
            </span>
          ) : null}
          {offline ? (
            <span className="rounded-full border border-amber-300/40 bg-amber-300/10 px-2 py-0.5 text-[10px] font-semibold uppercase text-amber-300">
              offline
            </span>
          ) : null}
        </div>
      </header>

      <div className="mt-5 overflow-hidden">
        <svg
          viewBox={`0 0 ${W} ${H}`}
          preserveAspectRatio="none"
          className="block w-full"
          style={{ height: 200 }}
        >
          <defs>
            <linearGradient id="trendArea" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#3DFF7A" stopOpacity="0.4" />
              <stop offset="100%" stopColor="#3DFF7A" stopOpacity="0" />
            </linearGradient>
          </defs>
          <line x1="0" y1={padTop + innerH * 0.25} x2={W} y2={padTop + innerH * 0.25} stroke="#ffffff10" strokeDasharray="2 4" />
          <line x1="0" y1={padTop + innerH * 0.5} x2={W} y2={padTop + innerH * 0.5} stroke="#ffffff10" strokeDasharray="2 4" />
          <line x1="0" y1={padTop + innerH * 0.75} x2={W} y2={padTop + innerH * 0.75} stroke="#ffffff10" strokeDasharray="2 4" />
          <text x={6} y={padTop + 4} fontFamily="Geist Mono, ui-monospace, monospace" fontSize="10" fill="#71717a">
            {max}
          </text>
          <text x={6} y={padTop + innerH + 4} fontFamily="Geist Mono, ui-monospace, monospace" fontSize="10" fill="#71717a">
            {min}
          </text>

          <path d={areaPath} fill="url(#trendArea)" />
          <path
            d={linePath}
            fill="none"
            stroke="#3DFF7A"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            style={{ filter: "drop-shadow(0 0 6px rgba(61,255,122,0.5))" }}
          />
          {points.map((p, i) => {
            const isPeak = i === peakIdx;
            const isLast = i === points.length - 1;
            return (
              <circle
                key={i}
                cx={p.x}
                cy={p.y}
                r={isPeak ? 5 : isLast ? 4 : 3}
                fill="#3DFF7A"
                stroke={isPeak || isLast ? "#000" : undefined}
                strokeWidth={isPeak || isLast ? 2 : 0}
              />
            );
          })}
        </svg>
      </div>

      <div className="mt-3 grid grid-cols-6 border-t border-white/10 pt-3">
        {months.map((month, i) => {
          const isPeak = i === peakIdx;
          return (
            <div key={month} className="text-center">
              <p
                className={`text-2xl font-bold tabular-nums tracking-tight leading-none ${
                  isPeak ? "text-[#3DFF7A]" : "text-white"
                }`}
              >
                {data[i]}
              </p>
              <p className="mt-1.5 text-[10px] font-mono uppercase tracking-wider text-zinc-500">
                {shortMonthLabel(month)}
              </p>
              {isPeak ? (
                <p className="text-[9px] font-mono uppercase tracking-wider text-[#3DFF7A]">
                  peak
                </p>
              ) : null}
            </div>
          );
        })}
      </div>
    </article>
  );
}
