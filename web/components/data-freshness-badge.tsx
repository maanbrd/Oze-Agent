export function DataFreshnessBadge({ fetchedAt }: { fetchedAt: string }) {
  const date = new Date(fetchedAt);
  const label = Number.isNaN(date.getTime())
    ? "odświeżenie nieznane"
    : `odświeżone ${date.toLocaleString("pl-PL", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })}`;

  return (
    <span className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-xs text-zinc-400">
      {label}
    </span>
  );
}
