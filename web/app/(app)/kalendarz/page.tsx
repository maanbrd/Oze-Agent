import { CrmNotice } from "@/components/crm-notice";
import { DataFreshnessBadge } from "@/components/data-freshness-badge";
import { getCrmDashboardData } from "@/lib/crm/adapters";
import type { CrmEvent } from "@/lib/crm/types";
import {
  formatWarsawDayLabel,
  formatWarsawTime,
  warsawDateKeyFromIso,
} from "@/lib/dates";

export default async function CalendarPage() {
  const data = await getCrmDashboardData();
  const grouped = groupByDay(data.events);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase text-[#3DFF7A]">Kalendarz</p>
          <h1 className="mt-2 text-3xl font-semibold text-white">
            Spotkania i akcje z Calendar
          </h1>
        </div>
        <DataFreshnessBadge fetchedAt={data.fetchedAt} />
      </div>

      <CrmNotice />
      <p className="rounded-[8px] border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-zinc-300">
        {data.source === "live"
          ? "Źródło: Google Sheets i Calendar."
          : data.sourceMessage}
      </p>

      <section className="grid gap-4">
        {Object.entries(grouped).map(([day, events]) => (
          <div key={day} className="rounded-[8px] border border-white/10 bg-white/[0.04] p-5">
            <h2 className="text-sm font-semibold text-white">{formatDay(day)}</h2>
            <div className="mt-4 grid gap-3">
              {events.map((event) => (
                <CalendarEventItem key={event.id} event={event} />
              ))}
            </div>
          </div>
        ))}
      </section>
    </div>
  );
}

function CalendarEventItem({ event }: { event: CrmEvent }) {
  const content = (
    <>
      <span className="text-sm font-semibold text-white">
        {formatTime(event.startsAt)} · {event.clientName}
      </span>
      <span className="mt-1 block text-sm text-zinc-400">
        {event.title}
      </span>
      {event.location ? (
        <span className="mt-2 block text-xs text-zinc-500">
          {event.location}
        </span>
      ) : null}
    </>
  );
  const className = "rounded-[8px] border border-white/10 bg-black/20 p-4";

  if (!event.calendarUrl) {
    return <div className={className}>{content}</div>;
  }

  return (
    <a
      href={event.calendarUrl}
      target="_blank"
      rel="noopener noreferrer"
      className={`${className} hover:border-[#3DFF7A]/40`}
    >
      {content}
    </a>
  );
}

function groupByDay(events: CrmEvent[]) {
  return events.reduce<Record<string, CrmEvent[]>>((groups, event) => {
    const day = warsawDateKeyFromIso(event.startsAt) ?? event.startsAt.slice(0, 10);
    groups[day] = [...(groups[day] ?? []), event];
    return groups;
  }, {});
}

function formatDay(day: string) {
  return formatWarsawDayLabel(day);
}

function formatTime(value: string) {
  return formatWarsawTime(value);
}
