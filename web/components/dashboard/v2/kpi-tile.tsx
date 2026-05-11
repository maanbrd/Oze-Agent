type DeltaKind = "up" | "down" | "warn" | "flat";

type KpiTileProps = {
  label: string;
  value: number | string;
  secondary?: string;
  delta?: { kind: DeltaKind; text: string };
  detail?: string;
};

const DELTA_STYLES: Record<DeltaKind, string> = {
  up: "bg-[#3DFF7A]/15 text-[#3DFF7A]",
  down: "bg-rose-400/15 text-rose-300",
  warn: "bg-amber-400/15 text-amber-300",
  flat: "bg-white/10 text-zinc-300",
};

export function KpiTile({ label, value, secondary, delta, detail }: KpiTileProps) {
  return (
    <article className="flex flex-col gap-3 rounded-2xl border border-white/10 bg-white/[0.04] p-5">
      <div className="flex items-start justify-between gap-3">
        <p className="text-xs font-medium uppercase tracking-wider text-zinc-400">
          {label}
        </p>
        {delta ? (
          <span
            className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium ${DELTA_STYLES[delta.kind]}`}
          >
            {delta.text}
          </span>
        ) : null}
      </div>
      <p className="text-4xl font-bold tracking-tight tabular-nums leading-none text-white">
        {value}
        {secondary ? (
          <span className="ml-1 text-xl font-medium text-zinc-500">{secondary}</span>
        ) : null}
      </p>
      {detail ? (
        <p className="text-xs text-zinc-500">{detail}</p>
      ) : null}
    </article>
  );
}
