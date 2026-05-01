import { CrmNotice } from "@/components/crm-notice";
import { DataFreshnessBadge } from "@/components/data-freshness-badge";
import { getCrmDashboardData } from "@/lib/crm/adapters";

export default async function ClientsPage() {
  const data = await getCrmDashboardData();

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase text-[#3DFF7A]">Klienci</p>
          <h1 className="mt-2 text-3xl font-semibold text-white">Baza z Sheets</h1>
        </div>
        <DataFreshnessBadge fetchedAt={data.fetchedAt} />
      </div>

      <CrmNotice />
      <p className="rounded-[8px] border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-zinc-300">
        {data.source === "live"
          ? "Źródło: Google Sheets i Calendar."
          : data.sourceMessage}
      </p>

      <section className="rounded-[8px] border border-white/10 bg-white/[0.04] p-4">
        <div className="grid gap-3 md:grid-cols-4">
          {["Status", "Miasto", "Produkt", "Źródło"].map((label) => (
            <label key={label} className="text-xs font-semibold uppercase text-zinc-500">
              {label}
              <select className="mt-2 w-full rounded-[8px] border border-white/10 bg-black/30 px-3 py-2 text-sm normal-case text-zinc-300">
                <option>Wszystkie</option>
              </select>
            </label>
          ))}
        </div>
      </section>

      <section className="overflow-hidden rounded-[8px] border border-white/10 bg-white/[0.04]">
        <table className="w-full border-collapse text-left text-sm">
          <thead className="bg-white/[0.04] text-xs uppercase text-zinc-500">
            <tr>
              <th className="px-4 py-3">Klient</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Produkt</th>
              <th className="px-4 py-3">Następny krok</th>
              <th className="px-4 py-3">Google</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/10">
            {data.clients.map((client) => (
              <tr key={client.id}>
                <td className="px-4 py-4">
                  <span className="font-semibold text-white">{client.fullName}</span>
                  <span className="block text-zinc-500">{client.city}</span>
                </td>
                <td className="px-4 py-4 text-zinc-300">{client.status}</td>
                <td className="px-4 py-4 text-zinc-300">{client.product ?? "brak"}</td>
                <td className="px-4 py-4 text-zinc-300">{client.nextAction ?? "brak"}</td>
                <td className="px-4 py-4">
                  <div className="flex flex-wrap gap-2">
                    {client.sheetsUrl ? <ExternalLink href={client.sheetsUrl}>Sheets</ExternalLink> : null}
                    {client.calendarUrl ? <ExternalLink href={client.calendarUrl}>Calendar</ExternalLink> : null}
                    {client.driveUrl ? <ExternalLink href={client.driveUrl}>Drive</ExternalLink> : null}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

function ExternalLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="rounded-full border border-[#3DFF7A]/30 px-3 py-1 text-xs font-semibold text-[#3DFF7A]"
    >
      {children}
    </a>
  );
}
