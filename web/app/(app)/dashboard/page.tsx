import { CrmNotice } from "@/components/crm-notice";
import { DataFreshnessBadge } from "@/components/data-freshness-badge";
import { HeroDay } from "@/components/dashboard/v2/hero-day";
import { KonwersjaGauge } from "@/components/dashboard/v2/konwersja-gauge";
import { KpiTile } from "@/components/dashboard/v2/kpi-tile";
import { LejekBars } from "@/components/dashboard/v2/lejek-bars";
import { SourcesDonut } from "@/components/dashboard/v2/sources-donut";
import { TrendArea6mo } from "@/components/dashboard/v2/trend-area-6mo";
import { WatchList } from "@/components/dashboard/v2/watch-list";
import { getLeadSources, getTrend6mo } from "@/lib/api/insights";
import { getCrmDashboardData } from "@/lib/crm/adapters";
import {
  countActiveClients,
  formatTodayMeetingTimes,
  oldestOfferStaleDays,
  signedPreviousMonth,
  signedThisMonth,
} from "@/lib/crm/dashboard-stats";
import { warsawDateKey, warsawDateKeyFromIso } from "@/lib/dates";

export default async function DashboardPage({
  searchParams,
}: {
  searchParams?: Promise<{ onboarding?: string }>;
}) {
  const params = await searchParams;
  const onboardingComplete = params?.onboarding === "complete";

  const [data, trend, sources] = await Promise.all([
    getCrmDashboardData(),
    getTrend6mo(),
    getLeadSources(),
  ]);

  const now = new Date();
  const todayKey = warsawDateKey();
  const tomorrowDate = new Date(now);
  tomorrowDate.setDate(tomorrowDate.getDate() + 1);
  const tomorrowKey = warsawDateKey(tomorrowDate);

  const todayEvents = data.events.filter(
    (event) => warsawDateKeyFromIso(event.startsAt) === todayKey,
  );
  const tomorrowEvents = data.events.filter(
    (event) => warsawDateKeyFromIso(event.startsAt) === tomorrowKey,
  );
  const urgentClients = data.clients
    .filter((client) => {
      if (!client.nextActionAt) return false;
      const nextActionDay = warsawDateKeyFromIso(client.nextActionAt);
      return Boolean(nextActionDay && nextActionDay <= todayKey);
    })
    .slice(0, 5);

  const offers = data.clients.filter((client) => client.status === "Oferta wysłana");
  const activeClients = countActiveClients(data.clients);
  const totalClients = data.clients.length;
  const oldestOfferDays = oldestOfferStaleDays(data.clients, now);
  const todayTimesLabel = formatTodayMeetingTimes(todayEvents);
  const signedThis = signedThisMonth(data.clients, now);
  const signedPrev = signedPreviousMonth(data.clients, now);

  const signedDelta =
    signedPrev.count > 0
      ? Math.round(((signedThis - signedPrev.count) / signedPrev.count) * 100)
      : null;

  const activeRatio =
    totalClients > 0 ? Math.round((activeClients / totalClients) * 100) : null;

  return (
    <div className="space-y-6">
      {onboardingComplete ? (
        <p className="rounded-2xl border border-[#3DFF7A]/30 bg-[#3DFF7A]/10 px-4 py-3 text-sm font-semibold text-white">
          Rejestracja ukończona. Konto, płatność, Google i Telegram są połączone.
        </p>
      ) : null}

      <CrmNotice />

      <header className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#3DFF7A]">
            Dashboard
          </p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-white">
            Centrum dowodzenia
          </h1>
        </div>
        <DataFreshnessBadge fetchedAt={data.fetchedAt} />
      </header>

      {data.source !== "live" ? (
        <p className="rounded-2xl border border-amber-300/30 bg-amber-300/10 px-4 py-3 text-sm text-amber-200">
          {data.sourceMessage}
        </p>
      ) : null}

      <section className="grid gap-5 lg:grid-cols-12">
        <div className="lg:col-span-8">
          <HeroDay
            todayEvents={todayEvents}
            tomorrowEventsCount={tomorrowEvents.length}
            activeClients={activeClients}
            totalClients={totalClients}
            pendingOffersCount={offers.length}
            now={now}
          />
        </div>
        <div className="lg:col-span-4">
          <WatchList
            urgentClients={urgentClients}
            tomorrowEvents={tomorrowEvents}
            offers={offers}
            now={now}
          />
        </div>
      </section>

      <section className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <KpiTile
          label="Aktywni"
          value={activeClients}
          secondary={`/${totalClients}`}
          delta={
            activeRatio !== null
              ? { kind: "up", text: `${activeRatio}% bazy` }
              : undefined
          }
          detail={
            totalClients > 0
              ? `${totalClients - activeClients} poza lejkiem`
              : "brak klientów"
          }
        />
        <KpiTile
          label="Spotkania dziś"
          value={todayEvents.length}
          delta={todayEvents.length > 0 ? { kind: "up", text: "live" } : undefined}
          detail={todayTimesLabel}
        />
        <KpiTile
          label="Oferty czekają"
          value={offers.length}
          delta={
            oldestOfferDays !== null && oldestOfferDays >= 5
              ? { kind: "warn", text: `⚠ ${oldestOfferDays}d` }
              : undefined
          }
          detail={
            oldestOfferDays === null
              ? "brak"
              : `najstarsza ${oldestOfferDays} ${oldestOfferDays === 1 ? "dzień" : "dni"}`
          }
        />
        <KpiTile
          label="Podpisane (ten miesiąc)"
          value={signedThis}
          delta={
            signedDelta !== null
              ? signedDelta > 0
                ? { kind: "up", text: `▲ +${signedDelta}%` }
                : signedDelta < 0
                  ? { kind: "down", text: `▼ ${signedDelta}%` }
                  : { kind: "flat", text: "±0" }
              : undefined
          }
          detail={
            signedPrev.count === 0
              ? "brak danych z poprzedniego miesiąca"
              : `vs ${signedPrev.count} w ${signedPrev.monthLabel}`
          }
        />
      </section>

      <TrendArea6mo trend={trend} />

      <section className="grid gap-5 lg:grid-cols-3">
        <LejekBars clients={data.clients} />
        <SourcesDonut sources={sources} />
        <KonwersjaGauge clients={data.clients} />
      </section>
    </div>
  );
}
