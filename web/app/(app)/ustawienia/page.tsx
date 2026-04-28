import { CrmNotice } from "@/components/crm-notice";
import { getCurrentAccount } from "@/lib/api/account";

export default async function SettingsPage() {
  const account = await getCurrentAccount();
  const profile = account.profile;

  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase text-[#3DFF7A]">Ustawienia</p>
        <h1 className="mt-2 text-3xl font-semibold text-white">Konto i integracje</h1>
      </div>

      <CrmNotice />

      <section className="grid gap-4 md:grid-cols-2">
        <Panel title="Profil">
          <Line label="Email" value={profile?.email ?? account.email ?? "brak"} />
          <Line label="Telefon" value={profile?.phone ?? "brak"} />
          <Line label="Nazwa" value={profile?.name ?? "brak"} />
        </Panel>

        <Panel title="Integracje">
          <Line label="Sheets" value={profile?.google_sheets_id ? "połączone" : "czeka"} />
          <Line label="Calendar" value={profile?.google_calendar_id ? "połączone" : "czeka"} />
          <Line label="Drive" value={profile?.google_drive_folder_id ? "połączone" : "czeka"} />
          <Line label="Telegram" value={profile?.telegram_id ? "sparowany" : "czeka"} />
        </Panel>
      </section>

      <section className="rounded-[8px] border border-white/10 bg-white/[0.04] p-5">
        <h2 className="text-sm font-semibold text-white">CRM</h2>
        <p className="mt-3 text-sm leading-6 text-zinc-400">
          Statusy i kolumny zmieniasz w Google. Panel nie zapisuje zmian CRM.
          Ta sekcja pokaże konfigurację po podpięciu odczytu z Sheets i Calendar.
        </p>
      </section>
    </div>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-[8px] border border-white/10 bg-white/[0.04] p-5">
      <h2 className="text-sm font-semibold text-white">{title}</h2>
      <div className="mt-4 space-y-3">{children}</div>
    </section>
  );
}

function Line({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4 text-sm">
      <span className="text-zinc-500">{label}</span>
      <span className="text-zinc-200">{value}</span>
    </div>
  );
}
