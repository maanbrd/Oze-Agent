import { CrmNotice } from "@/components/crm-notice";
import { DataFreshnessBadge } from "@/components/data-freshness-badge";
import { getCrmDashboardData } from "@/lib/crm/adapters";
import type { CrmEvent } from "@/lib/crm/types";

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
                <a
                  key={event.id}
                  href={event.calendarUrl ?? "#"}
                  target="_blank"
                  rel="noreferrer"
                  className="rounded-[8px] border border-white/10 bg-black/20 p-4 hover:border-[#3DFF7A]/40"
                >
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
                </a>
              ))}
            </div>
          </div>
        ))}
      </section>
    </div>
  );
}

function groupByDay(events: CrmEvent[]) {
  return events.reduce<Record<string, CrmEvent[]>>((groups, event) => {
    const day = event.startsAt.slice(0, 10);
    groups[day] = [...(groups[day] ?? []), event];
    return groups;
  }, {});
}

function formatDay(day: string) {
  return new Date(`${day}T12:00:00+02:00`).toLocaleDateString("pl-PL", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    weekday: "long",
  });
}

function formatTime(value: string) {
  return new Date(value).toLocaleTimeString("pl-PL", {
    hour: "2-digit",
    minute: "2-digit",
  });
}
