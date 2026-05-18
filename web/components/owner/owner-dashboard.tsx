import Link from "next/link";
import type { OwnerCounterRow, OwnerDashboardData } from "@/lib/api/admin-dashboard";

export function OwnerDashboard({ data }: { data: OwnerDashboardData }) {
  const kpis = [
    {
      label: "MRR",
      value: formatPln(data.business.mrr_pln),
      detail: "miesięczny przychód z aktywnych kont",
    },
    {
      label: "Aktywne konta",
      value: formatNumber(data.business.active_paid_accounts),
      detail: "płatne konta w systemie",
    },
    {
      label: "Koszt AI",
      value: `${formatUsd(data.business.ai_cost_usd_month)}`,
      detail: "suma kosztów z interaction_log",
    },
    {
      label: "Marża brutto",
      value: formatPln(data.business.estimated_gross_margin_pln),
      detail: "bez estymacji kosztów poza AI",
    },
    {
      label: "Aktywni 7 dni",
      value: formatNumber(data.business.active_7d_accounts),
      detail: "konta z aktywnością w logu",
    },
    {
      label: "Pending payment",
      value: formatNumber(data.business.pending_payment_accounts),
      detail: `${formatPln(data.business.pending_payment_pln)} do odzyskania`,
      warn: true,
    },
  ];

  return (
    <div className="space-y-3">
      {data.error ? (
        <div className="rounded-[8px] border border-amber-300/25 bg-amber-300/10 px-4 py-3 text-sm text-amber-100">
          {data.error}
        </div>
      ) : null}

      <section className="rounded-[8px] border border-white/10 bg-white/[0.025]">
        <div className="grid divide-y divide-white/10 md:grid-cols-2 md:divide-x md:divide-y-0 xl:grid-cols-6">
          {kpis.map((kpi) => (
            <Kpi key={kpi.label} {...kpi} />
          ))}
        </div>
      </section>

      <section className="grid gap-3 xl:grid-cols-[1.1fr_1fr_0.55fr]">
        <Panel title="Przychód vs koszt AI" subtitle="bieżący miesiąc">
          <RevenueCostChart
            revenue={data.business.mrr_pln}
            aiCost={data.business.ai_cost_usd_month}
          />
        </Panel>

        <Panel title="Lejek Agent OZE" subtitle="od rejestracji do pierwszej oferty">
          <div className="mt-4 grid gap-2 sm:grid-cols-2 xl:grid-cols-7">
            {data.funnel.map((step, index) => (
              <div
                key={step.label}
                className={
                  index < 4
                    ? "rounded-[8px] border border-[#3DFF7A]/10 bg-[#3DFF7A]/10 p-3"
                    : "rounded-[8px] border border-white/10 bg-black/25 p-3"
                }
              >
                <p className="min-h-10 text-xs font-semibold text-zinc-300">{step.label}</p>
                <p className="mt-3 text-2xl font-semibold text-white">{formatNumber(step.count)}</p>
                <p className="mt-2 text-xs text-[#3DFF7A]">
                  {formatPercent(step.conversion_pct)}
                </p>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Wymaga uwagi" subtitle="priorytety właściciela">
          <div className="mt-4 grid gap-2">
            {data.operations.attention.length > 0 ? (
              data.operations.attention.map((item) => (
                <div key={item.label} className="rounded-[8px] border border-white/10 bg-black/25 p-3">
                  <div className="flex items-start justify-between gap-3">
                    <p className="text-sm font-semibold text-white">{item.label}</p>
                    <span className="text-lg font-semibold text-amber-300">
                      {formatNumber(item.count)}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-zinc-500">{item.detail}</p>
                </div>
              ))
            ) : (
              <EmptyLine>Brak alertów operacyjnych.</EmptyLine>
            )}
          </div>
        </Panel>
      </section>

      <section className="grid gap-3 xl:grid-cols-[0.8fr_1fr_0.6fr_0.5fr]">
        <Panel title="Dane z rynku OZE" subtitle="oferty i komponenty">
          <div className="mt-4 grid grid-cols-2 gap-2">
            <Metric label="Oferty" value={formatNumber(data.oze.offers_total)} />
            <Metric label="Śr. cena" value={formatPln(data.oze.average_offer_price_pln)} />
            <Metric label="Łączna moc" value={`${formatNumber(data.oze.total_pv_kwp)} kWp`} />
            <Metric label="Magazyny" value={`${formatNumber(data.oze.total_storage_kwh)} kWh`} />
          </div>
        </Panel>

        <Panel title="Popularne konfiguracje ofert" subtitle="typy i udział">
          <CounterTable rows={data.oze.popular_offer_types} empty="Brak ofert w mirrorze." />
        </Panel>

        <Panel title="Najczęstsze miasta" subtitle="wg kontaktów">
          <RankedList rows={data.oze.top_cities} empty="Brak danych miast." />
        </Panel>

        <Panel title="Integracje" subtitle="status kont">
          <div className="mt-4 grid gap-2">
            {data.operations.integrations.length > 0 ? (
              data.operations.integrations.map((item) => (
                <div key={item.label} className="grid grid-cols-[1fr_auto_auto] items-center gap-2 text-xs">
                  <span className="text-zinc-300">{item.label}</span>
                  <span className="text-zinc-500">
                    {formatNumber(item.ok)} / {formatNumber(item.total)}
                  </span>
                  <span className={item.ok === item.total ? "font-semibold text-[#3DFF7A]" : "font-semibold text-amber-300"}>
                    {item.ok === item.total ? "OK" : "uwaga"}
                  </span>
                </div>
              ))
            ) : (
              <EmptyLine>Brak danych integracji.</EmptyLine>
            )}
          </div>
        </Panel>
      </section>

      <section className="grid gap-3 xl:grid-cols-[0.9fr_0.9fr_1fr]">
        <Panel title="Najczęstsze komponenty" subtitle="udział w ofertach">
          <div className="mt-4 grid gap-3">
            {data.oze.components.length > 0 ? (
              data.oze.components.map((row) => (
                <Bar key={row.label} label={row.label} value={row.share_pct ?? 0} />
              ))
            ) : (
              <EmptyLine>Brak komponentów ofert.</EmptyLine>
            )}
          </div>
        </Panel>

        <Panel title="Statusy CRM" subtitle="z owner mirror Sheets">
          <CounterTable rows={data.oze.crm_statuses} empty="Brak kontaktów w mirrorze." />
        </Panel>

        <Panel title="Zaplecze danych" subtitle="Sheets i Calendar właściciela">
          <div className="mt-4 grid gap-2 text-sm">
            <OwnerLink href={data.links.sheets_url} label="Otwórz owner Google Sheets" />
            <OwnerLink href={data.links.calendar_url} label="Otwórz owner Google Calendar" />
          </div>
          <p className="mt-4 text-xs leading-5 text-zinc-500">
            Arkusz i kalendarz są kopią administracyjną. Źródłem prawdy CRM
            pozostają Google Sheets, Calendar i Drive użytkownika.
          </p>
        </Panel>
      </section>
    </div>
  );
}

function Kpi({
  label,
  value,
  detail,
  warn = false,
}: {
  label: string;
  value: string;
  detail: string;
  warn?: boolean;
}) {
  return (
    <div className="p-4">
      <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-zinc-500">{label}</p>
      <p className={warn ? "mt-2 text-3xl font-semibold text-amber-300" : "mt-2 text-3xl font-semibold text-[#3DFF7A]"}>
        {value}
      </p>
      <p className="mt-2 text-xs leading-5 text-zinc-500">{detail}</p>
    </div>
  );
}

export function OwnerPanel({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-4">
      <div>
        <p className="text-xs font-bold uppercase tracking-[0.22em] text-[#3DFF7A]">Agent OZE Admin</p>
        <h1 className="mt-3 text-3xl font-semibold text-white">{title}</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-zinc-400">{description}</p>
      </div>
      {children}
    </div>
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

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[8px] border border-white/10 bg-black/20 p-3">
      <p className="text-[11px] text-zinc-500">{label}</p>
      <p className="mt-2 text-xl font-semibold text-white">{value}</p>
    </div>
  );
}

function RevenueCostChart({ revenue, aiCost }: { revenue: number; aiCost: number }) {
  const revenueHeight = Math.min(82, Math.max(8, revenue > 0 ? 68 : 8));
  const costHeight = Math.min(82, Math.max(8, aiCost > 0 ? 28 : 8));

  return (
    <div className="mt-5">
      <div className="grid h-56 grid-cols-[72px_1fr] rounded-[8px] border border-white/10 bg-[linear-gradient(rgba(255,255,255,0.045)_1px,transparent_1px)] bg-[length:100%_25%] p-4">
        <div className="flex flex-col justify-between text-[11px] text-zinc-600">
          <span>max</span>
          <span>śr.</span>
          <span>0</span>
        </div>
        <div className="grid grid-cols-2 items-end gap-8">
          <ChartBar label="Przychód" value={formatPln(revenue)} height={revenueHeight} tone="green" />
          <ChartBar label="Koszt AI" value={formatUsd(aiCost)} height={costHeight} tone="muted" />
        </div>
      </div>
    </div>
  );
}

function ChartBar({
  label,
  value,
  height,
  tone,
}: {
  label: string;
  value: string;
  height: number;
  tone: "green" | "muted";
}) {
  return (
    <div className="grid h-full items-end gap-2">
      <div
        className={
          tone === "green"
            ? "rounded-t-[8px] bg-[#3DFF7A] shadow-[0_0_24px_rgba(61,255,122,0.18)]"
            : "rounded-t-[8px] bg-white/35"
        }
        style={{ height: `${height}%` }}
      />
      <div>
        <p className="text-sm font-semibold text-white">{value}</p>
        <p className="text-[11px] text-zinc-500">{label}</p>
      </div>
    </div>
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

function Bar({ label, value }: { label: string; value: number }) {
  return (
    <div className="grid grid-cols-[minmax(130px,180px)_1fr_48px] items-center gap-3 text-xs">
      <span className="text-zinc-300">{label}</span>
      <span className="h-2 rounded-full bg-white/10">
        <span
          className="block h-2 rounded-full bg-[#3DFF7A]"
          style={{ width: `${Math.max(0, Math.min(100, value))}%` }}
        />
      </span>
      <span className="text-right text-zinc-400">{formatPercent(value)}</span>
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

function EmptyLine({ children }: { children: React.ReactNode }) {
  return (
    <p className="mt-4 rounded-[8px] border border-white/10 bg-black/20 px-3 py-3 text-sm text-zinc-500">
      {children}
    </p>
  );
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
