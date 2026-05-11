import type { LeadSources } from "@/lib/api/insights";

type SourcesDonutProps = {
  sources: LeadSources;
};

const PALETTE = ["#3DFF7A", "#ffffff", "#71717a", "#3a3a3a"] as const;

type Segment = {
  label: string;
  count: number;
  color: string;
};

function buildSegments(sources: LeadSources): Segment[] {
  const sorted = [...sources.rows].sort((a, b) => b.totalCount - a.totalCount);
  const top3 = sorted.slice(0, 3);
  const restCount = sorted.slice(3).reduce((sum, row) => sum + row.totalCount, 0);

  const segments: Segment[] = top3.map((row, i) => ({
    label: row.source,
    count: row.totalCount,
    color: PALETTE[i],
  }));

  if (restCount > 0) {
    segments.push({ label: "Inne", count: restCount, color: PALETTE[3] });
  }
  return segments;
}

export function SourcesDonut({ sources }: SourcesDonutProps) {
  const offline = sources.source !== "live";
  const segments = buildSegments(sources);
  const total = segments.reduce((sum, seg) => sum + seg.count, 0);

  const radius = 60;
  const strokeWidth = 16;
  const circumference = 2 * Math.PI * radius;
  const segmentArcs: { dasharray: string; dashoffset: number; color: string }[] = [];
  let cumulativeOffset = 0;
  for (const seg of segments) {
    if (total === 0) break;
    const arcLength = (seg.count / total) * circumference;
    segmentArcs.push({
      dasharray: `${arcLength} ${circumference}`,
      dashoffset: -cumulativeOffset,
      color: seg.color,
    });
    cumulativeOffset += arcLength;
  }

  return (
    <article className="rounded-2xl border border-white/10 bg-white/[0.04] p-6">
      <header className="flex items-baseline justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold tracking-tight text-white">Skąd leady</h2>
          <p className="mt-1 text-xs font-mono text-zinc-500">30 dni · {total} nowych</p>
        </div>
        {offline ? (
          <span className="rounded-full border border-amber-300/40 bg-amber-300/10 px-2 py-0.5 text-[10px] font-semibold uppercase text-amber-300">
            offline
          </span>
        ) : null}
      </header>

      {total === 0 ? (
        <p className="mt-5 text-sm text-zinc-500">
          Brak danych w kolumnie „Źródło pozyskania”.
        </p>
      ) : (
        <div className="mt-5 grid grid-cols-[150px_1fr] gap-5 items-center">
          <div className="relative h-[150px] w-[150px]">
            <svg viewBox="0 0 150 150" className="h-full w-full">
              <circle
                cx="75"
                cy="75"
                r={radius}
                fill="none"
                stroke="rgba(255,255,255,0.05)"
                strokeWidth={strokeWidth}
              />
              {segmentArcs.map((arc, i) => (
                <circle
                  key={i}
                  cx="75"
                  cy="75"
                  r={radius}
                  fill="none"
                  stroke={arc.color}
                  strokeWidth={strokeWidth}
                  strokeDasharray={arc.dasharray}
                  strokeDashoffset={arc.dashoffset}
                  transform="rotate(-90 75 75)"
                  style={
                    i === 0
                      ? { filter: "drop-shadow(0 0 6px rgba(61,255,122,0.5))" }
                      : undefined
                  }
                />
              ))}
            </svg>
            <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center text-center">
              <p className="text-3xl font-bold tracking-tight tabular-nums leading-none text-white">
                {total}
              </p>
              <p className="mt-1 text-[10px] font-mono uppercase tracking-[0.12em] text-zinc-500">
                LEADÓW
              </p>
            </div>
          </div>
          <ul className="space-y-0">
            {segments.map((seg, i) => (
              <li
                key={`${seg.label}-${i}`}
                className="grid grid-cols-[12px_1fr_auto] items-baseline gap-3 border-t border-white/10 py-2 text-sm first:border-t-0 first:pt-0"
              >
                <span
                  className="h-2.5 w-2.5 rounded-full"
                  style={{ background: seg.color }}
                />
                <span className="truncate text-zinc-300">{seg.label}</span>
                <span className="font-mono text-xs text-zinc-500">
                  {Math.round((seg.count / total) * 100)}%
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </article>
  );
}
