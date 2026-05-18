import Link from "next/link";
import { getCurrentAccount } from "@/lib/api/account";

const planItems = [
  "Agent w Telegramie",
  "Panel CRM",
  "Klienci i kalendarz z Google",
  "Generator ofert",
  "Zdjęcia i pliki na Dysku Google",
];

export default async function PaymentsPage() {
  const account = await getCurrentAccount();
  const profile = account.profile;
  const status = profile?.subscription_status ?? null;
  const active = status === "active";
  const statusLabel = active ? "Aktywna" : billingStatusLabel(status);
  const periodLabel = active
    ? formatDate(profile?.subscription_current_period_end)
    : "brak aktywnego okresu";

  return (
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
              <span
                className={
                  active
                    ? "h-2 w-2 rounded-full bg-[#3DFF7A] shadow-[0_0_12px_rgba(61,255,122,0.8)]"
                    : "h-2 w-2 rounded-full bg-amber-300 shadow-[0_0_12px_rgba(251,191,36,0.8)]"
                }
              />
              {active ? "Konto aktywne" : "Konto czeka na płatność"}
            </p>
            <h2 className="mt-4 max-w-2xl text-3xl font-bold tracking-tight text-white">
              {active
                ? "Subskrypcja działa. Możesz korzystać z Agent OZE."
                : "Aktywuj subskrypcję, żeby korzystać z Agent OZE."}
            </h2>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-zinc-400">
              {active
                ? "Dane rozliczeniowe są przypisane do adresu email z konta. Gdy odnowienie będzie wymagało uwagi, pokażemy to tutaj."
                : "Po opłaceniu planu konto przejdzie dalej do konfiguracji Google i Telegrama. Dane rozliczeniowe zostaną przypisane do adresu email z konta."}
            </p>
          </div>

          {!active ? (
            <Link
              href="/onboarding/platnosc"
              className="inline-flex h-11 items-center justify-center rounded-full bg-[#3DFF7A] px-5 text-sm font-semibold text-black shadow-[0_0_24px_rgba(61,255,122,0.14)] transition hover:bg-[#6DFF98]"
            >
              Przejdź do płatności
            </Link>
          ) : null}
        </div>

        <div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <BillingState label="Status" value={statusLabel} tone={active ? "ok" : "warn"} />
          <BillingState label="Plan" value={profile?.subscription_plan ?? "OZE-Agent"} />
          <BillingState label="Cena" value="399 zł / mies." />
          <BillingState label="Okres" value={periodLabel} />
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
            <p className="text-sm font-semibold text-white">
              Po aktywacji zobaczysz tutaj:
            </p>
            <div className="mt-4 grid gap-3 text-sm text-zinc-400 sm:grid-cols-3">
              <div>Następna płatność</div>
              <div>Ostatnia faktura</div>
              <div>Status odnowienia</div>
            </div>
          </div>
        </article>
      </section>
    </div>
  );
}

function BillingState({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: string;
  tone?: "default" | "ok" | "warn";
}) {
  const valueClass =
    tone === "ok"
      ? "mt-2 font-semibold text-[#3DFF7A]"
      : tone === "warn"
        ? "mt-2 font-semibold text-amber-200"
        : "mt-2 font-semibold text-white";

  return (
    <div className="rounded-[8px] border border-white/10 bg-black/20 p-4">
      <p className="text-xs font-semibold uppercase tracking-[0.12em] text-zinc-500">
        {label}
      </p>
      <p className={valueClass}>{value}</p>
    </div>
  );
}

function billingStatusLabel(value: string | null | undefined) {
  switch (value) {
    case "active":
      return "Aktywna";
    case "trialing":
      return "Okres próbny";
    case "past_due":
      return "Wymaga płatności";
    case "canceled":
    case "cancelled":
      return "Anulowana";
    case "pending_payment":
    case "incomplete":
      return "Czeka na płatność";
    case "unpaid":
      return "Nieopłacona";
    default:
      return "Nieaktywna";
  }
}

function formatDate(value: string | null | undefined) {
  if (!value) return "brak aktywnego okresu";
  return new Date(value).toLocaleDateString("pl-PL", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}
