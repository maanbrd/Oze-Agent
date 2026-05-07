import {
  daysLeftInMonth,
  meetingsThisWeek,
  oldestOfferStaleDays,
  signedThisMonth,
} from "@/lib/crm/dashboard-stats";
import type { CrmClient, CrmEvent } from "@/lib/crm/types";

export function Nastepne30Dni({
  clients,
  events,
  now,
}: {
  clients: CrmClient[];
  events: CrmEvent[];
  now?: Date;
}) {
  const ref = now ?? new Date();
  const week = meetingsThisWeek(events, ref);
  const offersCount = clients.filter((client) => client.status === "Oferta wysłana").length;
  const oldestOffer = oldestOfferStaleDays(clients, ref);
  const signedMtd = signedThisMonth(clients, ref);
  const monthDaysLeft = daysLeftInMonth(ref);

  return (
    <section className="rounded-[8px] border border-white/10 bg-white/[0.04] p-5">
      <div className="mb-4 flex items-baseline justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-[#3DFF7A]">
            Następne 30 dni
          </p>
          <h2 className="mt-1 text-sm font-semibold text-white">
            Pipeline na horyzont
          </h2>
        </div>
      </div>
      <div className="grid gap-3 md:grid-cols-3">
        <Cell
          label="Spotkania ten tydzień"
          value={week.total}
          detail={weekDetail(week.total, week.past)}
        />
        <Cell
          label="Oferty czekają"
          value={offersCount}
          detail={offerDetail(oldestOffer)}
        />
        <Cell
          label="Podpisane (ten miesiąc)"
          value={signedMtd}
          detail={`do końca miesiąca: ${monthDaysLeft} ${monthDaysLeft === 1 ? "dzień" : "dni"}`}
        />
      </div>
    </section>
  );
}

function weekDetail(total: number, past: number): string {
  if (total === 0) return "brak";
  if (past === 0) return "wszystkie przed nami";
  if (past === total) return "wszystkie odbyte";
  return `${past} z ${total} odbytych`;
}

function offerDetail(days: number | null): string {
  if (days === null) return "brak";
  return `najstarsza ${days} ${days === 1 ? "dzień" : "dni"} temu`;
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
