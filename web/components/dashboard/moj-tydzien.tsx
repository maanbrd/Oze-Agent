import type { ActivityWeek } from "@/lib/api/insights";

export function MojTydzien({ activity }: { activity: ActivityWeek }) {
  const offline = activity.source !== "live";

  return (
    <section className="rounded-[8px] border border-white/10 bg-white/[0.04] p-5">
      <div className="mb-4 flex items-baseline justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-[#3DFF7A]">
            Mój tydzień
          </p>
          <h2 className="mt-1 text-sm font-semibold text-white">
            Twoja aktywność od poniedziałku
          </h2>
        </div>
        {offline ? (
          <span className="rounded-full border border-amber-300/40 bg-amber-300/10 px-2 py-0.5 text-[10px] font-semibold uppercase text-amber-300">
            offline
          </span>
        ) : null}
      </div>
      <div className="grid gap-3 md:grid-cols-4">
        <Cell
          label="Nowi klienci"
          value={activity.newClients}
          detail={newClientsDetail(activity.newClients)}
        />
        <Cell
          label="Spotkania odbyte"
          value={activity.meetingsDone}
          detail={meetingsDetail(activity.meetingsDone)}
        />
        <Cell
          label="Oferty wysłane"
          value={activity.offersSent}
          detail={offersDetail(activity.offersSent)}
        />
        <Cell
          label="Streak"
          value={activity.streak}
          detail={streakDetail(activity.streak)}
        />
      </div>
    </section>
  );
}

function newClientsDetail(n: number): string {
  if (n === 0) return "ten tydzień bez nowych";
  return n === 1 ? "1 nowy lead" : `${n} nowych leadów`;
}

function meetingsDetail(n: number): string {
  if (n === 0) return "zero w Calendar";
  return n === 1 ? "1 spotkanie odbyte" : "z Calendar do dziś";
}

function offersDetail(n: number): string {
  if (n === 0) return "zero w tym tygodniu";
  return n === 1 ? "1 oferta z eventu offer_email" : "z eventów offer_email";
}

function streakDetail(streak: number): string {
  if (streak === 0) return "dzisiaj nic — czas zacząć";
  if (streak === 1) return "1 dzień z ruchem";
  if (streak >= 30) return "30+ dni z rzędu";
  return `${streak} dni z rzędu`;
}

function Cell({
  label,
  value,
  detail,
}: {
  label: string;
  value: number;
  detail: string;
}) {
  return (
    <article className="rounded-[8px] border border-white/10 bg-black/20 p-4">
      <p className="text-sm text-zinc-400">{label}</p>
      <p className="mt-3 text-3xl font-semibold tabular-nums text-white">{value}</p>
      <p className="mt-2 text-xs text-zinc-500">{detail}</p>
    </article>
  );
}
