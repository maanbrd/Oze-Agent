import Link from "next/link";
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
    subscription_status: "inactive",
    subscription_plan: null,
    subscription_current_period_end: null,
    activation_paid: false,
    onboarding_completed: true,
    google_sheets_id: null,
    google_calendar_id: null,
    google_drive_folder_id: null,
    telegram_id: null,
  },
} satisfies CurrentAccount;

const planItems = [
  "Agent w Telegramie",
  "Panel CRM",
  "Klienci i kalendarz z Google",
  "Generator ofert",
  "Zdjęcia i pliki na Dysku Google",
];

export default function PaymentsPreviewPage() {
  if (process.env.NODE_ENV !== "development") {
    notFound();
  }

  return (
    <CrmShell account={previewAccount} decisionsCount={14}>
      <div className="mx-auto max-w-6xl space-y-6">
        <header>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#3DFF7A]">
            Płatności
          </p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-white">
            Konto i rozliczenia
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-zinc-400">
            Tutaj sprawdzasz, czy konto jest aktywne, jaki plan masz przypisany
            i gdzie wrócić do płatności, jeśli subskrypcja nie została jeszcze opłacona.
          </p>
        </header>

        <section className="rounded-2xl border border-white/10 bg-[radial-gradient(circle_at_86%_18%,rgba(61,255,122,0.14),transparent_32%),rgba(255,255,255,0.035)] p-6 shadow-[0_0_30px_rgba(61,255,122,0.04)]">
          <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
            <div>
              <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-[#3DFF7A]">
                <span className="h-2 w-2 rounded-full bg-amber-300 shadow-[0_0_12px_rgba(251,191,36,0.8)]" />
                Konto czeka na płatność
              </p>
              <h2 className="mt-4 max-w-2xl text-3xl font-bold tracking-tight text-white">
                Aktywuj subskrypcję, żeby korzystać z Agent OZE.
              </h2>
              <p className="mt-3 max-w-2xl text-sm leading-6 text-zinc-400">
                Po opłaceniu planu konto przejdzie dalej do konfiguracji Google
                i Telegrama. Dane rozliczeniowe zostaną przypisane do adresu email z konta.
              </p>
            </div>
            <Link
              href="/onboarding/platnosc"
              className="inline-flex h-11 items-center justify-center rounded-full bg-[#3DFF7A] px-5 text-sm font-semibold text-black shadow-[0_0_24px_rgba(61,255,122,0.14)] transition hover:bg-[#6DFF98]"
            >
              Przejdź do płatności
            </Link>
          </div>

          <div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <BillingState label="Status" value="Nieaktywna" tone="warn" />
            <BillingState label="Plan" value="OZE-Agent" />
            <BillingState label="Cena" value="399 zł / mies." />
            <BillingState label="Okres" value="brak aktywnego okresu" />
          </div>
        </section>

        <section className="grid gap-5 lg:grid-cols-[0.9fr_1.1fr]">
          <article className="rounded-[8px] border border-white/10 bg-white/[0.04] p-5">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#3DFF7A]">
              Co obejmuje plan
            </p>
            <div className="mt-5 grid gap-3">
              {planItems.map((item) => (
                <div
                  key={item}
                  className="flex items-center gap-3 rounded-[8px] border border-white/10 bg-black/20 px-4 py-3 text-sm text-zinc-200"
                >
                  <span className="h-2 w-2 rounded-full bg-[#3DFF7A]" />
                  {item}
                </div>
              ))}
            </div>
          </article>

          <article className="rounded-[8px] border border-white/10 bg-white/[0.04] p-5">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#3DFF7A]">
              Faktury i historia
            </p>
            <h2 className="mt-3 text-xl font-semibold tracking-tight text-white">
              Historia płatności pojawi się po pierwszej opłaconej subskrypcji.
            </h2>
            <p className="mt-3 text-sm leading-6 text-zinc-400">
              Faktury są wysyłane na email użyty przy płatności. Po aktywacji
              pokażemy tutaj ostatnią płatność, datę kolejnego odnowienia i
              link do zarządzania rozliczeniem.
            </p>

            <div className="mt-6 rounded-[8px] border border-white/10 bg-black/20 p-4">
              <p className="text-sm font-semibold text-white">Po aktywacji zobaczysz tutaj:</p>
              <div className="mt-4 grid gap-3 text-sm text-zinc-400 sm:grid-cols-3">
                <div>Następna płatność</div>
                <div>Ostatnia faktura</div>
                <div>Status odnowienia</div>
              </div>
            </div>
          </article>
        </section>
      </div>
    </CrmShell>
  );
}

function BillingState({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: string;
  tone?: "default" | "warn";
}) {
  return (
    <div className="rounded-[8px] border border-white/10 bg-black/20 p-4">
      <p className="text-xs font-semibold uppercase tracking-[0.12em] text-zinc-500">
        {label}
      </p>
      <p
        className={
          tone === "warn"
            ? "mt-2 font-semibold text-amber-200"
            : "mt-2 font-semibold text-white"
        }
      >
        {value}
      </p>
    </div>
  );
}
