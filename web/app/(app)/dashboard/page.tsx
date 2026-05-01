import { CrmNotice } from "@/components/crm-notice";
import { DataFreshnessBadge } from "@/components/data-freshness-badge";
import { getCrmDashboardData } from "@/lib/crm/adapters";
import type { CrmClient, CrmEvent, FunnelStatus } from "@/lib/crm/types";
import { formatWarsawTime, warsawDateKey, warsawDateKeyFromIso } from "@/lib/dates";

const statuses: FunnelStatus[] = [
  "Nowy lead",
  "Spotkanie umówione",
  "Spotkanie odbyte",
  "Oferta wysłana",
  "Podpisane",
  "Zamontowana",
  "Rezygnacja z umowy",
  "Nieaktywny",
  "Odrzucone",
];

export default async function DashboardPage({
  searchParams,
}: {
  searchParams?: Promise<{ onboarding?: string }>;
}) {
  const params = await searchParams;
  const onboardingComplete = params?.onboarding === "complete";
  const data = await getCrmDashboardData();
  const todayKey = warsawDateKey();
  const todayEvents = data.events.filter((event) =>
    warsawDateKeyFromIso(event.startsAt) === todayKey,
  );
  const urgentClients = data.clients
    .filter((client) => {
      if (!client.nextActionAt) return false;
      const nextActionDay = warsawDateKeyFromIso(client.nextActionAt);
      return Boolean(nextActionDay && nextActionDay <= todayKey);
    })
    .slice(0, 5);
  const signed = data.clients.filter((client) => client.status === "Podpisane");
  const offers = data.clients.filter((client) => client.status === "Oferta wysłana");

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase text-[#3DFF7A]">
            Dashboard
          </p>
          <h1 className="mt-2 text-3xl font-semibold text-white">
            Centrum dowodzenia
          </h1>
        </div>
        <DataFreshnessBadge fetchedAt={data.fetchedAt} />
      </div>

      {onboardingComplete ? (
        <p className="rounded-[8px] border border-[#3DFF7A]/30 bg-[#3DFF7A]/10 px-4 py-3 text-sm font-semibold text-white">
          Rejestracja ukończona. Konto, płatność, Google i Telegram są połączone.
        </p>
      ) : null}

      <CrmNotice />
      <p className="rounded-[8px] border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-zinc-300">
        {data.source === "live"
          ? "Źródło: Google Sheets i Calendar."
          : data.sourceMessage}
      </p>

      <section className="grid gap-4 md:grid-cols-4">
        <Metric label="Klienci" value={data.clients.length} detail="z Google Sheets" />
        <Metric label="Spotkania dziś" value={todayEvents.length} detail="z Google Calendar" />
        <Metric label="Oferty wysłane" value={offers.length} detail="czekają na decyzję" />
        <Metric label="Podpisane" value={signed.length} detail="aktywny miesiąc" />
      </section>

      <section className="grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
        <Panel title="Lejek z Sheets">
          <div className="space-y-3">
            {statuses.map((status) => {
              const count = data.clients.filter((client) => client.status === status).length;
              return (
                <div key={status} className="grid grid-cols-[160px_1fr_32px] items-center gap-3 text-sm">
                  <span className="text-zinc-300">{status}</span>
                  <span className="h-2 rounded-full bg-white/10">
                    <span
                      className="block h-2 rounded-full bg-[#3DFF7A]"
                      style={{ width: `${Math.max(10, count * 18)}%` }}
                    />
                  </span>
                  <span className="text-right text-zinc-400">{count}</span>
                </div>
              );
            })}
          </div>
        </Panel>

        <Panel title="Dziś z Calendar">
          <div className="space-y-3">
            {todayEvents.length ? (
              todayEvents.map((event) => <TodayEvent key={event.id} event={event} />)
            ) : (
              <p className="text-sm text-zinc-500">Dziś bez spotkań w Calendar.</p>
            )}
          </div>
        </Panel>
      </section>

      <Panel title="Wymagają uwagi">
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {urgentClients.map((client) => (
            <ClientAction key={client.id} client={client} />
          ))}
        </div>
      </Panel>
    </div>
  );
}

function TodayEvent({ event }: { event: CrmEvent }) {
  const content = (
    <>
      <span className="font-semibold text-white">
        {formatTime(event.startsAt)} · {event.clientName}
      </span>
      <span className="mt-1 block text-zinc-400">{event.title}</span>
    </>
  );
  const className = "block rounded-[8px] border border-white/10 bg-black/20 p-4 text-sm";

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

function Metric({
  label,
  value,
  detail,
}: {
  label: string;
  value: number;
  detail: string;
}) {
  return (
    <article className="rounded-[8px] border border-white/10 bg-white/[0.04] p-4">
      <p className="text-sm text-zinc-400">{label}</p>
      <p className="mt-3 text-3xl font-semibold tabular-nums text-white">{value}</p>
      <p className="mt-2 text-xs text-zinc-500">{detail}</p>
    </article>
  );
}

function Panel({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-[8px] border border-white/10 bg-white/[0.04] p-5">
      <h2 className="text-sm font-semibold text-white">{title}</h2>
      <div className="mt-4">{children}</div>
    </section>
  );
}

function ClientAction({ client }: { client: CrmClient }) {
  return (
    <article className="rounded-[8px] border border-white/10 bg-black/20 p-4">
      <p className="font-semibold text-white">{client.fullName}</p>
      <p className="mt-1 text-sm text-zinc-400">
        {client.city} · {client.status}
      </p>
      <p className="mt-3 text-sm text-amber-100">{client.nextAction}</p>
      <div className="mt-4 flex flex-wrap gap-2 text-xs">
        {client.sheetsUrl ? <ExternalLink href={client.sheetsUrl}>Sheets</ExternalLink> : null}
        {client.calendarUrl ? <ExternalLink href={client.calendarUrl}>Calendar</ExternalLink> : null}
      </div>
    </article>
  );
}

function ExternalLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="rounded-full border border-[#3DFF7A]/30 px-3 py-1 font-semibold text-[#3DFF7A]"
    >
      {children}
    </a>
  );
}

function formatTime(value: string) {
  return formatWarsawTime(value);
}
