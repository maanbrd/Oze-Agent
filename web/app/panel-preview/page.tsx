import { notFound } from "next/navigation";
import { CrmShell } from "@/components/crm-shell";
import type { CurrentAccount } from "@/lib/api/account";

export const dynamic = "force-dynamic";

const previewAccount = {
  authenticated: true,
  email: "preview@agent-oze.pl",
  accessToken: "preview",
  error: null,
  profile: {
    id: "preview",
    auth_user_id: "preview",
    name: "Podgląd lokalny",
    email: "preview@agent-oze.pl",
    phone: "+48 000 000 000",
    subscription_status: "active",
    subscription_plan: "preview",
    subscription_current_period_end: null,
    activation_paid: true,
    onboarding_completed: true,
    google_sheets_id: null,
    google_calendar_id: null,
    google_drive_folder_id: null,
    telegram_id: null,
  },
} satisfies CurrentAccount;

export default function PanelPreviewPage() {
  if (process.env.NODE_ENV !== "development") {
    notFound();
  }

  return (
    <CrmShell account={previewAccount} decisionsCount={14}>
      <section className="mx-auto max-w-5xl space-y-6">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[#3DFF7A]">
            Podgląd panelu
          </p>
          <h1 className="mt-3 text-3xl font-semibold text-white">
            Nawigacja po usunięciu zbędnej zakładki
          </h1>
          <p className="mt-4 max-w-2xl text-sm leading-6 text-zinc-400">
            Ten widok pokazuje realny shell aplikacji bez logowania. W menu
            zostają tylko sekcje, które mają jasną rolę w pracy handlowca.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <PreviewCard title="Praca codzienna">
            Dashboard, decyzje, klienci i kalendarz prowadzą użytkownika przez
            bieżący dzień.
          </PreviewCard>
          <PreviewCard title="Rzeczy pomocnicze">
            Płatności, import, instrukcja i FAQ zostają dostępne tam, gdzie mają
            konkretny cel.
          </PreviewCard>
          <PreviewCard title="Sprzedaż">
            Oferty zostają osobnym, zatwierdzonym flow do szablonów i testowych
            PDF-ów.
          </PreviewCard>
        </div>
      </section>
    </CrmShell>
  );
}

function PreviewCard({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <article className="rounded-[8px] border border-white/10 bg-white/[0.04] p-5">
      <h2 className="text-base font-semibold text-white">{title}</h2>
      <p className="mt-3 text-sm leading-6 text-zinc-400">{children}</p>
    </article>
  );
}
