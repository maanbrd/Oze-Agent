import Link from "next/link";
import type {
  OwnerCounterRow,
  OwnerDashboardData,
  OwnerIntegrationRow,
} from "@/lib/api/admin-dashboard";
import { OwnerPanel } from "@/components/owner/owner-dashboard";

export function OwnerAnalyticsDashboard({ data }: { data: OwnerDashboardData }) {
  return (
    <OwnerPanel
      title="Analityka danych OZE"
      description="Rynek, komponenty, miasta, ceny i konfiguracje ofert z administracyjnej kopii danych."
    >
      <DashboardError error={data.error} />
      <KpiGrid
        items={[
          ["Oferty", formatNumber(data.oze.offers_total), "wszystkie szablony w systemie"],
          ["Śr. cena", formatPln(data.oze.average_offer_price_pln), "netto z ofert"],
          ["Łączna moc", `${formatNumber(data.oze.total_pv_kwp)} kWp`, "suma mocy PV"],
          ["Magazyny", `${formatNumber(data.oze.total_storage_kwh)} kWh`, "suma pojemności"],
        ]}
      />
      <div className="grid gap-3 xl:grid-cols-[1fr_1fr_0.8fr]">
        <Panel title="Najczęstsze komponenty ofert" subtitle="udział w ofertach">
          <BarList rows={data.oze.components} empty="Brak komponentów ofert." />
        </Panel>
        <Panel title="Struktura ofert wg typu" subtitle="mix produktowy">
          <DonutSummary rows={data.oze.popular_offer_types} center={formatNumber(data.oze.offers_total)} label="ofert" />
        </Panel>
        <Panel title="Najczęstsze miasta" subtitle="wg kontaktów">
          <RankedList rows={data.oze.top_cities} empty="Brak danych miast." />
        </Panel>
      </div>
      <div className="grid gap-3 xl:grid-cols-[1.1fr_0.9fr]">
        <Panel title="Średnia cena ofert" subtitle="wartość i skala">
          <PriceBand value={data.oze.average_offer_price_pln} />
        </Panel>
        <Panel title="Statusy CRM" subtitle="z owner mirror Sheets">
          <CounterTable rows={data.oze.crm_statuses} empty="Brak kontaktów w mirrorze." />
        </Panel>
      </div>
    </OwnerPanel>
  );
}

export function OwnerOperationsDashboard({ data }: { data: OwnerDashboardData }) {
  const riskyIntegrations = data.operations.integrations.filter((item) => item.ok < item.total);
  return (
    <OwnerPanel
      title="Operacje i zdrowie"
      description="Stan integracji, tokenów Google, synchronizacji mirroru i alertów, które mogą blokować pracę użytkowników."
    >
      <DashboardError error={data.error} />
      <KpiGrid
        items={[
          ["Status systemu", data.operations.system_status, "ogólny stan administracyjny"],
          ["Integracje z uwagą", formatNumber(riskyIntegrations.length), "źródła wymagające sprawdzenia"],
          ["Alerty", formatNumber(data.operations.attention.reduce((sum, item) => sum + item.count, 0)), "łączna liczba sygnałów"],
          ["Aktywni 7 dni", formatNumber(data.business.active_7d_accounts), "użytkownicy z aktywnością"],
        ]}
      />
      <div className="grid gap-3 xl:grid-cols-[0.9fr_1fr_0.8fr]">
        <Panel title="Status integracji" subtitle="podpięte konta">
          <IntegrationGrid rows={data.operations.integrations} />
        </Panel>
        <Panel title="Błędy i zadania" subtitle="priorytety właściciela">
          <AttentionList data={data} />
        </Panel>
        <Panel title="Zdrowie synchronizacji" subtitle="owner mirror">
          <HealthStack rows={data.operations.integrations} />
        </Panel>
      </div>
      <div className="grid gap-3 xl:grid-cols-[1fr_1fr]">
        <Panel title="Aktywność produktu" subtitle="sygnały użycia">
          <MiniTimeline
            items={[
              ["Aktywne konta", data.business.active_paid_accounts],
              ["Aktywni 7 dni", data.business.active_7d_accounts],
              ["Oferty", data.oze.offers_total],
              ["Pending payment", data.business.pending_payment_accounts],
            ]}
          />
        </Panel>
        <Panel title="Kalendarz zbiorczy" subtitle="zaplecze spotkań">
          <OwnerLinks data={data} />
        </Panel>
      </div>
    </OwnerPanel>
  );
}

export function OwnerAccountsDashboard({ data }: { data: OwnerDashboardData }) {
  return (
    <OwnerPanel
      title="Klienci i konta"
      description="Przegląd użytkowników Agent OZE, ich statusów, onboardingu i danych CRM w owner mirror Sheets."
    >
      <DashboardError error={data.error} />
      <KpiGrid
        items={[
          ["Aktywne konta", formatNumber(data.business.active_paid_accounts), "płatne konta"],
          ["Pending payment", formatNumber(data.business.pending_payment_accounts), "konta do odzyskania"],
          ["Canceled", formatNumber(data.business.canceled_accounts), "ostatni snapshot zostaje"],
          ["Pierwsza oferta", formatNumber(lastFunnelCount(data, "Pierwsza oferta")), "użytkownicy po aktywacji oferty"],
        ]}
      />
      <div className="grid gap-3 xl:grid-cols-[1.35fr_0.65fr]">
        <Panel title="Lejek kont" subtitle="od rejestracji do pierwszej oferty">
          <FunnelStrip data={data} />
        </Panel>
        <Panel title="Snapshot CRM" subtitle="owner Google Sheets">
          <OwnerLinks data={data} />
        </Panel>
      </div>
      <div className="grid gap-3 xl:grid-cols-3">
        <Panel title="Statusy CRM użytkowników" subtitle="kontakty w mirrorze">
          <CounterTable rows={data.oze.crm_statuses} empty="Brak kontaktów w mirrorze." />
        </Panel>
        <Panel title="Najczęstsze miasta" subtitle="gdzie pracują użytkownicy">
          <RankedList rows={data.oze.top_cities} empty="Brak danych miast." />
        </Panel>
        <Panel title="Aktywność użytkowników" subtitle="produkt">
          <MiniTimeline
            items={[
              ["Telegram aktywny", funnelCount(data, "Telegram aktywny")],
              ["Pierwsze kontakty", funnelCount(data, "Pierwsze kontakty")],
              ["Pierwsza oferta", funnelCount(data, "Pierwsza oferta")],
            ]}
          />
        </Panel>
      </div>
    </OwnerPanel>
  );
}

export function OwnerBillingDashboard({ data }: { data: OwnerDashboardData }) {
  return (
    <OwnerPanel
      title="Płatności i subskrypcje"
      description="MRR, konta aktywne, pending payment, churn i historia rozliczeń z Supabase/Stripe."
    >
      <DashboardError error={data.error} />
      <KpiGrid
        items={[
          ["MRR", formatPln(data.business.mrr_pln), "aktywny przychód miesięczny"],
          ["Marża brutto", formatPln(data.business.estimated_gross_margin_pln), "bez kosztów poza AI"],
          ["Pending payment", formatPln(data.business.pending_payment_pln), "wartość do odzyskania"],
          ["Churn/canceled", formatNumber(data.business.canceled_accounts), "konta anulowane"],
        ]}
      />
      <div className="grid gap-3 xl:grid-cols-[1.1fr_0.9fr]">
        <Panel title="Przychód vs koszt AI" subtitle="kontrola marży">
          <RevenueVsAi data={data} />
        </Panel>
        <Panel title="Pipeline płatności" subtitle="status kont">
          <PaymentBars data={data} />
        </Panel>
      </div>
      <div className="grid gap-3 xl:grid-cols-3">
        <Panel title="Aktywne konta" subtitle="płatne">
          <BigNumber value={data.business.active_paid_accounts} detail="kont aktywnych" />
        </Panel>
        <Panel title="Pending payment" subtitle="do działania">
          <BigNumber value={data.business.pending_payment_accounts} detail="kont oczekujących" warn />
        </Panel>
        <Panel title="Koszt AI" subtitle="miesięcznie">
          <BigNumber value={data.business.ai_cost_usd_month} detail="USD z interaction_log" money="usd" />
        </Panel>
      </div>
    </OwnerPanel>
  );
}

export function OwnerProductsDashboard({ data }: { data: OwnerDashboardData }) {
  return (
    <OwnerPanel
      title="Produkty i oferty"
      description="Wiedza o tym, jakie oferty powstają, jakie komponenty są najczęstsze i które konfiguracje warto rozwijać."
    >
      <DashboardError error={data.error} />
      <KpiGrid
        items={[
          ["Oferty", formatNumber(data.oze.offers_total), "szablony ofert"],
          ["Śr. cena", formatPln(data.oze.average_offer_price_pln), "średnia oferta"],
          ["PV", `${formatNumber(data.oze.total_pv_kwp)} kWp`, "łączna moc"],
          ["Magazyny", `${formatNumber(data.oze.total_storage_kwh)} kWh`, "łączna pojemność"],
        ]}
      />
      <div className="grid gap-3 xl:grid-cols-[0.8fr_1fr_1fr]">
        <Panel title="Mix produktów" subtitle="typy ofert">
          <DonutSummary rows={data.oze.popular_offer_types} center={formatNumber(data.oze.offers_total)} label="ofert" />
        </Panel>
        <Panel title="Komponenty" subtitle="sprzęt i zakres">
          <BarList rows={data.oze.components} empty="Brak komponentów ofert." />
        </Panel>
        <Panel title="Ceny i moc" subtitle="skala produktów">
          <ProductScale data={data} />
        </Panel>
      </div>
      <div className="grid gap-3 xl:grid-cols-[1fr_1fr]">
        <Panel title="Popularne konfiguracje" subtitle="udział">
          <CounterTable rows={data.oze.popular_offer_types} empty="Brak ofert w mirrorze." />
        </Panel>
        <Panel title="Wysyłki ofert" subtitle="źródło: Supabase">
          <MiniTimeline
            items={[
              ["Wszystkie oferty", data.oze.offers_total],
              ["Użytkownicy z pierwszą ofertą", funnelCount(data, "Pierwsza oferta")],
              ["Kontakty po ofercie", statusCount(data, "Oferta wysłana")],
            ]}
          />
        </Panel>
      </div>
    </OwnerPanel>
  );
}

export function OwnerIntegrationsDashboard({ data }: { data: OwnerDashboardData }) {
  return (
    <OwnerPanel
      title="Integracje"
      description="Google Sheets, Google Calendar, Drive, Telegram, Stripe, Supabase oraz stan połączeń potrzebnych do pracy Agent OZE."
    >
      <DashboardError error={data.error} />
      <KpiGrid
        items={[
          ["System", data.operations.system_status, "status administracyjny"],
          ["Google Sheets", integrationRatio(data.operations.integrations, "Google Sheets"), "arkusze użytkowników"],
          ["Calendar", integrationRatio(data.operations.integrations, "Google Calendar"), "kalendarze użytkowników"],
          ["Telegram", integrationRatio(data.operations.integrations, "Telegram"), "połączone konta"],
        ]}
      />
      <div className="grid gap-3 xl:grid-cols-[1fr_0.9fr_0.9fr]">
        <Panel title="Status integracji" subtitle="wszystkie źródła">
          <IntegrationGrid rows={data.operations.integrations} />
        </Panel>
        <Panel title="Owner mirror" subtitle="Sheets i Calendar">
          <OwnerLinks data={data} />
        </Panel>
        <Panel title="Ryzyka integracji" subtitle="gdzie patrzeć">
          <HealthStack rows={data.operations.integrations} />
        </Panel>
      </div>
      <Panel title="Sygnały operacyjne" subtitle="z backendu admin API">
        <AttentionList data={data} compact />
      </Panel>
    </OwnerPanel>
  );
}

export function OwnerReportsDashboard({ data }: { data: OwnerDashboardData }) {
  return (
    <OwnerPanel
      title="Raporty"
      description="Cykliczne raporty z owner mirror, eksporty i szybkie linki do arkusza oraz kalendarza właściciela."
    >
      <DashboardError error={data.error} />
      <KpiGrid
        items={[
          ["MRR", formatPln(data.business.mrr_pln), "raport biznesowy"],
          ["Oferty", formatNumber(data.oze.offers_total), "raport produktowy"],
          ["Konta aktywne", formatNumber(data.business.active_paid_accounts), "raport operacyjny"],
          ["Alerty", formatNumber(data.operations.attention.length), "raport ryzyk"],
        ]}
      />
      <div className="grid gap-3 xl:grid-cols-3">
        <ReportCard title="Raport dzienny" rows={[
          ["Aktywne konta", formatNumber(data.business.active_paid_accounts)],
          ["Pending payment", formatNumber(data.business.pending_payment_accounts)],
          ["Aktywni 7 dni", formatNumber(data.business.active_7d_accounts)],
        ]} />
        <ReportCard title="Raport miesięczny" rows={[
          ["MRR", formatPln(data.business.mrr_pln)],
          ["Koszt AI", formatUsd(data.business.ai_cost_usd_month)],
          ["Marża brutto", formatPln(data.business.estimated_gross_margin_pln)],
        ]} />
        <ReportCard title="Raport OZE" rows={[
          ["Oferty", formatNumber(data.oze.offers_total)],
          ["Śr. cena", formatPln(data.oze.average_offer_price_pln)],
          ["Moc PV", `${formatNumber(data.oze.total_pv_kwp)} kWp`],
        ]} />
      </div>
      <Panel title="Eksport danych" subtitle="pełna kopia administracyjna">
        <OwnerLinks data={data} />
      </Panel>
    </OwnerPanel>
  );
}

export function OwnerSettingsDashboard({ data }: { data: OwnerDashboardData }) {
  return (
    <OwnerPanel
      title="Ustawienia"
      description="Konfiguracja warstwy właściciela: admin emails, owner mirror, linki do arkusza i kalendarza oraz przyszłe role."
    >
      <DashboardError error={data.error} />
      <div className="grid gap-3 xl:grid-cols-3">
        <Panel title="Dostęp admina" subtitle="OWNER_ADMIN_EMAILS">
          <SettingsStatus label="Aktualny admin" value="lukaszfathioze@gmail.com" ok />
          <p className="mt-4 text-sm leading-6 text-zinc-400">
            Tylko email z listy owner admin może wejść na `/admin`. Zwykły
            użytkownik dostaje ukrytą stronę zamiast panelu właściciela.
          </p>
        </Panel>
        <Panel title="Owner mirror" subtitle="zaplecze danych">
          <SettingsStatus label="Google Sheets" value={data.links.sheets_url ? "skonfigurowany" : "brak linku"} ok={Boolean(data.links.sheets_url)} />
          <SettingsStatus label="Google Calendar" value={data.links.calendar_url ? "skonfigurowany" : "brak linku"} ok={Boolean(data.links.calendar_url)} />
        </Panel>
        <Panel title="Bezpieczeństwo" subtitle="warstwy danych">
          <SettingsStatus label="CRM shell admina" value="wyłączony" ok />
          <SettingsStatus label="API admina" value="chronione tokenem" ok />
        </Panel>
      </div>
      <div className="grid gap-3 xl:grid-cols-[1fr_1fr]">
        <Panel title="Linki administracyjne" subtitle="szybki dostęp">
          <OwnerLinks data={data} />
        </Panel>
        <Panel title="Kontrola danych" subtitle="co widzi właściciel">
          <MiniTimeline
            items={[
              ["Agregaty w dashboardzie", 1],
              ["Pełny CRM w owner Sheets", data.oze.crm_statuses.reduce((sum, item) => sum + item.count, 0)],
              ["Przyszłe spotkania w Calendar", data.operations.attention.find((item) => item.label === "Przyszłe spotkania")?.count ?? 0],
            ]}
          />
        </Panel>
      </div>
    </OwnerPanel>
  );
}

function Panel({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  return (
    <article className="rounded-[8px] border border-white/10 bg-white/[0.025] p-4">
      <div className="flex items-baseline justify-between gap-3">
        <h2 className="text-sm font-semibold text-white">{title}</h2>
        <p className="text-[11px] text-zinc-500">{subtitle}</p>
      </div>
      {children}
    </article>
  );
}

function KpiGrid({
  items,
}: {
  items: Array<[label: string, value: string, detail: string]>;
}) {
  return (
    <section className="rounded-[8px] border border-white/10 bg-white/[0.025]">
      <div className="grid divide-y divide-white/10 md:grid-cols-2 md:divide-x md:divide-y-0 xl:grid-cols-4">
        {items.map(([label, value, detail]) => (
          <div key={label} className="p-4">
            <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-zinc-500">{label}</p>
            <p className="mt-2 text-3xl font-semibold text-[#3DFF7A]">{value}</p>
            <p className="mt-2 text-xs leading-5 text-zinc-500">{detail}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function CounterTable({ rows, empty }: { rows: OwnerCounterRow[]; empty: string }) {
  if (rows.length === 0) return <EmptyLine>{empty}</EmptyLine>;
  return (
    <table className="mt-3 w-full text-xs">
      <thead className="text-left text-zinc-500">
        <tr>
          <th className="py-2">Nazwa</th>
          <th className="py-2 text-right">Liczba</th>
          <th className="py-2 text-right">Udział</th>
        </tr>
      </thead>
      <tbody className="text-zinc-300">
        {rows.map((row) => (
          <tr key={row.label} className="border-t border-white/5">
            <td className="py-2 text-white">{row.label}</td>
            <td className="py-2 text-right">{formatNumber(row.count)}</td>
            <td className="py-2 text-right text-[#3DFF7A]">
              {formatPercent(row.share_pct ?? row.conversion_pct ?? 0)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function RankedList({ rows, empty }: { rows: OwnerCounterRow[]; empty: string }) {
  if (rows.length === 0) return <EmptyLine>{empty}</EmptyLine>;
  return (
    <div className="mt-3 grid gap-2">
      {rows.map((row, index) => (
        <div key={row.label} className="grid grid-cols-[24px_1fr_auto_auto] items-center gap-2 text-xs">
          <span className="text-zinc-500">{index + 1}</span>
          <span className="font-medium text-white">{row.label}</span>
          <span className="text-zinc-300">{formatNumber(row.count)}</span>
          <span className="text-[#3DFF7A]">{formatPercent(row.share_pct ?? 0)}</span>
        </div>
      ))}
    </div>
  );
}

function BarList({ rows, empty }: { rows: OwnerCounterRow[]; empty: string }) {
  if (rows.length === 0) return <EmptyLine>{empty}</EmptyLine>;
  return (
    <div className="mt-4 grid gap-3">
      {rows.map((row) => (
        <div key={row.label} className="grid grid-cols-[minmax(140px,190px)_1fr_52px] items-center gap-3 text-xs">
          <span className="text-zinc-300">{row.label}</span>
          <span className="h-2 rounded-full bg-white/10">
            <span
              className="block h-2 rounded-full bg-[#3DFF7A]"
              style={{ width: `${Math.max(0, Math.min(100, row.share_pct ?? 0))}%` }}
            />
          </span>
          <span className="text-right text-zinc-400">{formatPercent(row.share_pct ?? 0)}</span>
        </div>
      ))}
    </div>
  );
}

function DonutSummary({
  rows,
  center,
  label,
}: {
  rows: OwnerCounterRow[];
  center: string;
  label: string;
}) {
  if (rows.length === 0) return <EmptyLine>Brak danych do wykresu.</EmptyLine>;
  const primary = Math.max(0, Math.min(100, rows[0]?.share_pct ?? 0));
  const secondary = Math.max(primary, Math.min(100, primary + (rows[1]?.share_pct ?? 0)));
  return (
    <div className="mt-5 grid items-center gap-5 md:grid-cols-[170px_1fr]">
      <div
        className="grid h-40 w-40 place-items-center rounded-full"
        style={{
          background: `conic-gradient(#3DFF7A 0 ${primary}%, #78f59a ${primary}% ${secondary}%, rgba(255,255,255,0.18) ${secondary}% 100%)`,
        }}
      >
        <div className="grid h-24 w-24 place-items-center rounded-full bg-[#080a0d] text-center">
          <div>
            <p className="text-2xl font-bold text-white">{center}</p>
            <p className="text-[10px] uppercase tracking-[0.18em] text-zinc-500">{label}</p>
          </div>
        </div>
      </div>
      <div className="grid gap-2 text-xs">
        {rows.slice(0, 5).map((row) => (
          <p key={row.label} className="flex justify-between gap-4 text-zinc-300">
            <span>{row.label}</span>
            <span className="font-semibold text-[#3DFF7A]">{formatPercent(row.share_pct ?? 0)}</span>
          </p>
        ))}
      </div>
    </div>
  );
}

function FunnelStrip({ data }: { data: OwnerDashboardData }) {
  return (
    <div className="mt-4 grid gap-2 md:grid-cols-4 xl:grid-cols-7">
      {data.funnel.map((step, index) => (
        <div
          key={step.label}
          className={index < 4 ? "rounded-[8px] border border-[#3DFF7A]/10 bg-[#3DFF7A]/10 p-3" : "rounded-[8px] border border-white/10 bg-black/25 p-3"}
        >
          <p className="min-h-10 text-xs font-semibold text-zinc-300">{step.label}</p>
          <p className="mt-3 text-2xl font-semibold text-white">{formatNumber(step.count)}</p>
          <p className="mt-2 text-xs text-[#3DFF7A]">{formatPercent(step.conversion_pct)}</p>
        </div>
      ))}
    </div>
  );
}

function IntegrationGrid({ rows }: { rows: OwnerIntegrationRow[] }) {
  if (rows.length === 0) return <EmptyLine>Brak danych integracji.</EmptyLine>;
  return (
    <div className="mt-4 grid gap-2">
      {rows.map((row) => (
        <div key={row.label} className="rounded-[8px] border border-white/10 bg-black/25 p-3">
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm font-semibold text-white">{row.label}</p>
            <p className={row.ok === row.total ? "text-sm font-semibold text-[#3DFF7A]" : "text-sm font-semibold text-amber-300"}>
              {row.ok}/{row.total}
            </p>
          </div>
          <div className="mt-3 h-2 rounded-full bg-white/10">
            <div
              className="h-2 rounded-full bg-[#3DFF7A]"
              style={{ width: `${row.total > 0 ? (row.ok / row.total) * 100 : 0}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

function HealthStack({ rows }: { rows: OwnerIntegrationRow[] }) {
  if (rows.length === 0) return <EmptyLine>Brak danych zdrowia systemu.</EmptyLine>;
  return (
    <div className="mt-4 grid gap-2">
      {rows.map((row) => {
        const missing = Math.max(row.total - row.ok, 0);
        return (
          <div key={row.label} className="grid grid-cols-[1fr_auto] gap-3 rounded-[8px] border border-white/10 bg-black/25 p-3 text-sm">
            <span className="text-zinc-300">{row.label}</span>
            <span className={missing === 0 ? "font-semibold text-[#3DFF7A]" : "font-semibold text-amber-300"}>
              {missing === 0 ? "OK" : `${missing} do sprawdzenia`}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function AttentionList({ data, compact = false }: { data: OwnerDashboardData; compact?: boolean }) {
  if (data.operations.attention.length === 0) return <EmptyLine>Brak alertów operacyjnych.</EmptyLine>;
  return (
    <div className={compact ? "mt-4 grid gap-2 xl:grid-cols-4" : "mt-4 grid gap-2"}>
      {data.operations.attention.map((item) => (
        <div key={item.label} className="rounded-[8px] border border-white/10 bg-black/25 p-3">
          <div className="flex items-start justify-between gap-3">
            <p className="text-sm font-semibold text-white">{item.label}</p>
            <span className="text-lg font-semibold text-amber-300">{formatNumber(item.count)}</span>
          </div>
          <p className="mt-1 text-xs text-zinc-500">{item.detail}</p>
        </div>
      ))}
    </div>
  );
}

function RevenueVsAi({ data }: { data: OwnerDashboardData }) {
  const revenueHeight = data.business.mrr_pln > 0 ? 78 : 8;
  const aiHeight = data.business.ai_cost_usd_month > 0 ? 28 : 8;
  return (
    <div className="mt-5 grid h-64 grid-cols-[80px_1fr] rounded-[8px] border border-white/10 bg-[linear-gradient(rgba(255,255,255,0.045)_1px,transparent_1px)] bg-[length:100%_25%] p-4">
      <div className="flex flex-col justify-between text-[11px] text-zinc-600">
        <span>max</span>
        <span>śr.</span>
        <span>0</span>
      </div>
      <div className="grid grid-cols-2 items-end gap-8">
        <ChartBar label="Przychód" value={formatPln(data.business.mrr_pln)} height={revenueHeight} />
        <ChartBar label="Koszt AI" value={formatUsd(data.business.ai_cost_usd_month)} height={aiHeight} muted />
      </div>
    </div>
  );
}

function ChartBar({
  label,
  value,
  height,
  muted = false,
}: {
  label: string;
  value: string;
  height: number;
  muted?: boolean;
}) {
  return (
    <div className="grid h-full items-end gap-2">
      <div className={muted ? "rounded-t-[8px] bg-white/35" : "rounded-t-[8px] bg-[#3DFF7A] shadow-[0_0_24px_rgba(61,255,122,0.18)]"} style={{ height: `${height}%` }} />
      <div>
        <p className="text-sm font-semibold text-white">{value}</p>
        <p className="text-[11px] text-zinc-500">{label}</p>
      </div>
    </div>
  );
}

function PaymentBars({ data }: { data: OwnerDashboardData }) {
  const total = data.business.active_paid_accounts + data.business.pending_payment_accounts + data.business.canceled_accounts;
  const rows: OwnerCounterRow[] = [
    { label: "Aktywne", count: data.business.active_paid_accounts, share_pct: pct(data.business.active_paid_accounts, total) },
    { label: "Pending payment", count: data.business.pending_payment_accounts, share_pct: pct(data.business.pending_payment_accounts, total) },
    { label: "Canceled", count: data.business.canceled_accounts, share_pct: pct(data.business.canceled_accounts, total) },
  ];
  return <BarList rows={rows} empty="Brak danych płatności." />;
}

function PriceBand({ value }: { value: number }) {
  const marker = Math.max(4, Math.min(96, value > 0 ? 58 : 4));
  return (
    <div className="mt-6">
      <p className="text-4xl font-semibold text-white">{formatPln(value)}</p>
      <p className="mt-2 text-sm text-zinc-500">średnia cena oferty w danych właściciela</p>
      <div className="relative mt-8 h-3 rounded-full bg-white/10">
        <div className="h-3 rounded-full bg-[#3DFF7A]" style={{ width: `${marker}%` }} />
        <div className="absolute top-1/2 h-7 w-1 -translate-y-1/2 rounded-full bg-white" style={{ left: `${marker}%` }} />
      </div>
      <div className="mt-3 flex justify-between text-[11px] text-zinc-600">
        <span>niska</span>
        <span>średnia</span>
        <span>wysoka</span>
      </div>
    </div>
  );
}

function ProductScale({ data }: { data: OwnerDashboardData }) {
  return (
    <div className="mt-4 grid gap-3">
      <ScaleRow label="Łączna moc PV" value={data.oze.total_pv_kwp} suffix="kWp" />
      <ScaleRow label="Magazyny energii" value={data.oze.total_storage_kwh} suffix="kWh" />
      <ScaleRow label="Średnia cena" value={data.oze.average_offer_price_pln} suffix="zł" />
    </div>
  );
}

function ScaleRow({ label, value, suffix }: { label: string; value: number; suffix: string }) {
  return (
    <div className="rounded-[8px] border border-white/10 bg-black/25 p-3">
      <div className="flex justify-between gap-3 text-sm">
        <span className="text-zinc-400">{label}</span>
        <span className="font-semibold text-white">{formatNumber(value)} {suffix}</span>
      </div>
      <div className="mt-3 h-2 rounded-full bg-white/10">
        <div className="h-2 rounded-full bg-[#3DFF7A]" style={{ width: `${value > 0 ? 62 : 4}%` }} />
      </div>
    </div>
  );
}

function MiniTimeline({ items }: { items: Array<[string, number]> }) {
  const max = Math.max(1, ...items.map(([, value]) => value));
  return (
    <div className="mt-4 grid gap-3">
      {items.map(([label, value]) => (
        <div key={label} className="grid grid-cols-[170px_1fr_72px] items-center gap-3 text-xs">
          <span className="text-zinc-300">{label}</span>
          <span className="h-2 rounded-full bg-white/10">
            <span className="block h-2 rounded-full bg-[#3DFF7A]" style={{ width: `${(value / max) * 100}%` }} />
          </span>
          <span className="text-right font-semibold text-white">{formatNumber(value)}</span>
        </div>
      ))}
    </div>
  );
}

function BigNumber({
  value,
  detail,
  warn = false,
  money,
}: {
  value: number;
  detail: string;
  warn?: boolean;
  money?: "usd";
}) {
  return (
    <div className="mt-6">
      <p className={warn ? "text-5xl font-semibold text-amber-300" : "text-5xl font-semibold text-[#3DFF7A]"}>
        {money === "usd" ? formatUsd(value) : formatNumber(value)}
      </p>
      <p className="mt-3 text-sm text-zinc-500">{detail}</p>
    </div>
  );
}

function ReportCard({ title, rows }: { title: string; rows: Array<[string, string]> }) {
  return (
    <Panel title={title} subtitle="podsumowanie">
      <div className="mt-4 grid gap-2">
        {rows.map(([label, value]) => (
          <div key={label} className="flex justify-between gap-3 border-t border-white/5 py-2 text-sm">
            <span className="text-zinc-400">{label}</span>
            <span className="font-semibold text-white">{value}</span>
          </div>
        ))}
      </div>
    </Panel>
  );
}

function SettingsStatus({ label, value, ok }: { label: string; value: string; ok: boolean }) {
  return (
    <div className="mt-4 rounded-[8px] border border-white/10 bg-black/25 p-3">
      <div className="flex items-center justify-between gap-3">
        <span className="text-sm text-zinc-400">{label}</span>
        <span className={ok ? "text-sm font-semibold text-[#3DFF7A]" : "text-sm font-semibold text-amber-300"}>
          {ok ? "OK" : "uwaga"}
        </span>
      </div>
      <p className="mt-2 text-sm font-semibold text-white">{value}</p>
    </div>
  );
}

function OwnerLinks({ data }: { data: OwnerDashboardData }) {
  return (
    <div className="mt-4 grid gap-2 text-sm">
      <OwnerLink href={data.links.sheets_url} label="Otwórz owner Google Sheets" />
      <OwnerLink href={data.links.calendar_url} label="Otwórz owner Google Calendar" />
    </div>
  );
}

function OwnerLink({ href, label }: { href: string | null; label: string }) {
  if (!href) {
    return (
      <span className="rounded-[8px] border border-white/10 bg-black/20 px-3 py-2 text-zinc-500">
        {label}: brak konfiguracji
      </span>
    );
  }

  return (
    <Link
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="rounded-[8px] border border-[#3DFF7A]/25 bg-[#3DFF7A]/10 px-3 py-2 font-semibold text-[#3DFF7A]"
    >
      {label} →
    </Link>
  );
}

function DashboardError({ error }: { error?: string | null }) {
  if (!error) return null;
  return (
    <div className="rounded-[8px] border border-amber-300/25 bg-amber-300/10 px-4 py-3 text-sm text-amber-100">
      {error}
    </div>
  );
}

function EmptyLine({ children }: { children: React.ReactNode }) {
  return (
    <p className="mt-4 rounded-[8px] border border-white/10 bg-black/20 px-3 py-3 text-sm text-zinc-500">
      {children}
    </p>
  );
}

function integrationRatio(rows: OwnerIntegrationRow[], label: string) {
  const row = rows.find((item) => item.label === label);
  if (!row) return "0/0";
  return `${row.ok}/${row.total}`;
}

function funnelCount(data: OwnerDashboardData, label: string) {
  return data.funnel.find((step) => step.label === label)?.count ?? 0;
}

function lastFunnelCount(data: OwnerDashboardData, label: string) {
  return funnelCount(data, label);
}

function statusCount(data: OwnerDashboardData, label: string) {
  return data.oze.crm_statuses.find((row) => row.label === label)?.count ?? 0;
}

function pct(value: number, total: number) {
  if (total <= 0) return 0;
  return Math.round((value / total) * 1000) / 10;
}

function formatNumber(value: number) {
  return new Intl.NumberFormat("pl-PL", { maximumFractionDigits: 2 }).format(value || 0);
}

function formatPln(value: number) {
  return `${formatNumber(Math.round(value || 0))} zł`;
}

function formatUsd(value: number) {
  return `$${formatNumber(value || 0)}`;
}

function formatPercent(value: number) {
  return `${formatNumber(value || 0)}%`;
}
