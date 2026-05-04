import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import { createCheckoutSession } from "@/app/onboarding/actions";
import { getCurrentAccount } from "@/lib/api/account";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Płatność | Agent-OZE",
  description: "Wybór planu i płatność Stripe sandbox.",
};

export default async function PaymentStepPage({
  searchParams,
}: {
  searchParams: Promise<{ message?: string }>;
}) {
  const params = await searchParams;
  const account = await getCurrentAccount();

  if (!account.authenticated) {
    redirect("/login?next=/onboarding/platnosc");
  }

  const isActive = account.profile?.subscription_status === "active";

  return (
    <main className="min-h-screen bg-[#050607] text-zinc-100">
      <div className="mx-auto flex min-h-screen w-full max-w-6xl flex-col px-5 py-6 sm:px-8">
        <header className="flex items-center justify-between border-b border-white/10 pb-5">
          <Link href="/" className="text-sm font-semibold text-white">
            OZE Agent
          </Link>
          <Link
            href="/dashboard"
            className="rounded-full border border-white/12 px-4 py-2 text-sm text-zinc-300 transition hover:border-[#3DFF7A]/60 hover:text-white"
          >
            Dashboard
          </Link>
        </header>

        <section className="grid flex-1 gap-8 py-8 lg:grid-cols-[0.9fr_0.7fr]">
          <div>
            <Stepper />
            <p className="mt-8 text-xs font-semibold uppercase text-[#3DFF7A]">
              Krok 2
            </p>
            <h1 className="mt-3 max-w-3xl text-4xl font-semibold leading-tight text-white sm:text-5xl">
              Wybierz plan i uruchom płatność.
            </h1>
            <p className="mt-5 max-w-2xl text-base leading-7 text-zinc-300">
              Stripe sandbox obsłuży płatność. Aktywacja 199 zł jest doliczana
              do pierwszej faktury, plan działa jako subskrypcja.
            </p>

            {params.message ? (
              <p className="mt-6 rounded-[8px] border border-red-400/20 bg-red-400/10 px-4 py-3 text-sm leading-6 text-zinc-200">
                {params.message}
              </p>
            ) : null}

            {account.error ? (
              <p className="mt-6 rounded-[8px] border border-amber-300/20 bg-amber-300/10 px-4 py-3 text-sm leading-6 text-zinc-200">
                {account.error}
              </p>
            ) : null}

            {!account.profile ? (
              <div className="mt-8 rounded-[8px] border border-amber-300/20 bg-amber-300/10 p-5">
                <p className="text-sm font-semibold text-white">
                  Profil konta nie jest jeszcze gotowy.
                </p>
                <p className="mt-2 text-sm leading-6 text-zinc-300">
                  Odśwież stronę za chwilę. Jeśli komunikat wróci, sprawdź
                  konfigurację API konta przed uruchomieniem płatności.
                </p>
              </div>
            ) : isActive ? (
              <div className="mt-8 rounded-[8px] border border-[#3DFF7A]/30 bg-[#3DFF7A]/10 p-5">
                <p className="text-sm font-semibold text-white">
                  Subskrypcja aktywna.
                </p>
                <p className="mt-2 text-sm leading-6 text-zinc-300">
                  Płatność jest zaksięgowana. Następny etap to Google OAuth,
                  zasoby Google i parowanie Telegrama.
                </p>
                <Link
                  href="/onboarding/google"
                  className="mt-5 inline-flex rounded-full bg-[#3DFF7A] px-5 py-2.5 text-sm font-semibold text-black"
                >
                  Przejdź do Google
                </Link>
              </div>
            ) : (
              <div className="mt-8 grid gap-4 md:grid-cols-2">
                <PlanCard
                  plan="monthly"
                  title="Miesięcznie"
                  price="49 zł"
                  note="Najmniejszy próg wejścia. Rezygnujesz kiedy chcesz."
                />
                <PlanCard
                  plan="yearly"
                  title="Rocznie"
                  price="350 zł"
                  badge="Oszczędzasz 238 zł"
                  note="Jedna płatność za rok pracy agenta."
                />
              </div>
            )}
          </div>

          <aside className="h-fit rounded-[8px] border border-white/10 bg-white/[0.04] p-6">
            <p className="text-sm font-semibold text-white">Koszyk</p>
            <div className="mt-5 space-y-4 text-sm">
              <Row label="Aktywacja" value="199 zł" />
              <Row label="Plan miesięczny" value="49 zł / mies." muted />
              <Row label="Plan roczny" value="350 zł / rok" muted />
            </div>
            <div className="mt-6 border-t border-white/10 pt-5">
              <p className="text-sm leading-6 text-zinc-400">
                Stripe Checkout pobierze płatność i odeśle webhook. Konto
                aktywujemy dopiero po potwierdzeniu opłacenia sesji.
              </p>
            </div>
          </aside>
        </section>
      </div>
    </main>
  );
}

function Stepper() {
  const steps = ["Konto", "Płatność", "Google", "Zasoby", "Telegram"];
  return (
    <div className="grid gap-2 sm:grid-cols-5">
      {steps.map((step, index) => (
        <div
          key={step}
          className={
            index <= 1
              ? "rounded-[8px] border border-[#3DFF7A]/30 bg-[#3DFF7A]/10 px-3 py-2 text-xs font-semibold text-white"
              : "rounded-[8px] border border-white/10 bg-white/[0.03] px-3 py-2 text-xs text-zinc-500"
          }
        >
          {index + 1}. {step}
        </div>
      ))}
    </div>
  );
}

function PlanCard({
  plan,
  title,
  price,
  note,
  badge,
}: {
  plan: "monthly" | "yearly";
  title: string;
  price: string;
  note: string;
  badge?: string;
}) {
  return (
    <form
      action={createCheckoutSession}
      className="rounded-[8px] border border-white/10 bg-black/20 p-5"
    >
      <input type="hidden" name="plan" value={plan} />
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-white">{title}</p>
          <p className="mt-3 text-3xl font-semibold text-white">{price}</p>
        </div>
        {badge ? (
          <span className="rounded-full border border-[#3DFF7A]/30 bg-[#3DFF7A]/10 px-3 py-1 text-xs font-semibold text-[#3DFF7A]">
            {badge}
          </span>
        ) : null}
      </div>
      <p className="mt-4 min-h-12 text-sm leading-6 text-zinc-400">{note}</p>
      <button
        type="submit"
        className="mt-5 inline-flex w-full items-center justify-center rounded-full bg-[#3DFF7A] px-5 py-3 text-sm font-semibold text-black transition hover:bg-[#6DFF98]"
      >
        Zapłać i kontynuuj
      </button>
    </form>
  );
}

function Row({
  label,
  value,
  muted,
}: {
  label: string;
  value: string;
  muted?: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span className={muted ? "text-zinc-500" : "text-zinc-300"}>{label}</span>
      <span className={muted ? "text-zinc-500" : "font-semibold text-white"}>
        {value}
      </span>
    </div>
  );
}
