import type { CrmEvent } from "@/lib/crm/types";
import { formatWarsawTime } from "@/lib/dates";

type HeroDayProps = {
  todayEvents: CrmEvent[];
  tomorrowEventsCount: number;
  activeClients: number;
  totalClients: number;
  pendingOffersCount: number;
  now?: Date;
};

const WEEKDAY_PL = [
  "niedziela",
  "poniedziałek",
  "wtorek",
  "środa",
  "czwartek",
  "piątek",
  "sobota",
] as const;

const MONTH_PL = [
  "stycznia",
  "lutego",
  "marca",
  "kwietnia",
  "maja",
  "czerwca",
  "lipca",
  "sierpnia",
  "września",
  "października",
  "listopada",
  "grudnia",
] as const;

function formatDateLong(d: Date): string {
  return `${WEEKDAY_PL[d.getDay()]}, ${d.getDate()} ${MONTH_PL[d.getMonth()]} ${d.getFullYear()}`;
}

function buildHeadline(meetings: number, pendingOffers: number): string {
  const parts: string[] = [];
  if (meetings > 0) {
    parts.push(`${meetings} ${meetings === 1 ? "spotkanie" : meetings >= 2 && meetings <= 4 ? "spotkania" : "spotkań"}`);
  }
  if (pendingOffers > 0) {
    parts.push(`${pendingOffers} ${pendingOffers === 1 ? "oferta czeka" : pendingOffers >= 2 && pendingOffers <= 4 ? "oferty czekają" : "ofert czeka"}`);
  }
  if (parts.length === 0) {
    return "Pusty grafik. Dobry moment, żeby ruszyć stare leady.";
  }
  if (parts.length === 1) {
    return `${parts[0]} dziś.`;
  }
  return `${parts.join(", ")} dziś.`;
}

function findNextEvent(events: CrmEvent[], now: Date): CrmEvent | null {
  const future = events.filter((event) => new Date(event.startsAt).getTime() > now.getTime());
  if (future.length === 0) return null;
  return future.reduce((soonest, candidate) =>
    new Date(candidate.startsAt).getTime() < new Date(soonest.startsAt).getTime()
      ? candidate
      : soonest,
  );
}

function formatRelativeTime(targetIso: string, now: Date): string {
  const diffMs = new Date(targetIso).getTime() - now.getTime();
  if (diffMs < 0) return "zaraz";
  const minutes = Math.round(diffMs / 60_000);
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const restMin = minutes % 60;
  return restMin > 0 ? `${hours}h ${restMin}min` : `${hours}h`;
}

export function HeroDay({
  todayEvents,
  tomorrowEventsCount,
  activeClients,
  totalClients,
  pendingOffersCount,
  now,
}: HeroDayProps) {
  const ref = now ?? new Date();
  const sortedEvents = [...todayEvents].sort((a, b) => a.startsAt.localeCompare(b.startsAt));
  const nextEvent = findNextEvent(sortedEvents, ref);
  const headline = buildHeadline(sortedEvents.length, pendingOffersCount);

  return (
    <article className="relative h-full overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-[#0c1612] via-[#0a0c0f] to-[#0a0c0f] p-8">
      <div
        className="pointer-events-none absolute right-[-80px] top-[-80px] h-[280px] w-[280px] rounded-full"
        style={{
          background: "radial-gradient(circle, rgba(61,255,122,0.18) 0%, transparent 70%)",
        }}
      />
      <div className="relative">
        <p className="flex items-center gap-2 text-xs font-medium uppercase tracking-[0.16em] text-[#3DFF7A]">
          <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-[#3DFF7A] shadow-[0_0_8px_#3DFF7A]" />
          Twój dzień · {formatDateLong(ref)}
        </p>
        <h1 className="mt-4 text-3xl font-bold tracking-tight leading-tight text-white sm:text-4xl">
          {headline}
        </h1>
        <div className="mt-5 flex flex-wrap gap-x-7 gap-y-2 text-sm text-zinc-400">
          <span>
            aktywni · <b className="font-semibold text-white">{activeClients}</b> z {totalClients}
          </span>
          {tomorrowEventsCount > 0 ? (
            <span>
              jutro ·{" "}
              <b className="font-semibold text-white">
                {tomorrowEventsCount}{" "}
                {tomorrowEventsCount === 1
                  ? "spotkanie"
                  : tomorrowEventsCount >= 2 && tomorrowEventsCount <= 4
                    ? "spotkania"
                    : "spotkań"}
              </b>
            </span>
          ) : (
            <span>jutro · <b className="font-semibold text-white">brak spotkań</b></span>
          )}
          {nextEvent ? (
            <span>
              najbliższe za <b className="font-semibold text-white">{formatRelativeTime(nextEvent.startsAt, ref)}</b>
            </span>
          ) : null}
        </div>

        {sortedEvents.length > 0 ? (
          <div className="mt-7 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {sortedEvents.slice(0, 3).map((event) => {
              const isNext = nextEvent?.id === event.id;
              return (
                <div
                  key={event.id}
                  className={
                    isNext
                      ? "rounded-xl border border-[#3DFF7A] bg-black/40 p-4 shadow-[0_0_24px_rgba(61,255,122,0.20)] backdrop-blur"
                      : "rounded-xl border border-white/10 bg-black/40 p-4 backdrop-blur"
                  }
                >
                  <p className={`font-mono text-xl font-medium tracking-tight ${isNext ? "text-[#3DFF7A]" : "text-white"}`}>
                    {formatWarsawTime(event.startsAt)}
                  </p>
                  <p className="mt-1 text-sm font-semibold text-white">{event.clientName}</p>
                  {event.city ? (
                    <p className="mt-0.5 text-xs text-zinc-400">{event.city}</p>
                  ) : null}
                </div>
              );
            })}
          </div>
        ) : null}
      </div>
    </article>
  );
}
