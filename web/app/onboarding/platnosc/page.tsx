import type { Metadata } from "next";
import Link from "next/link";
import { BrandLink } from "@/components/brand";
import { LogoutLink } from "@/components/auth/logout-link";
import { requireOnboardingStep } from "@/lib/auth/guards";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Płatność | Agent OZE",
  description: "Miesięczna subskrypcja Agent OZE.",
};

export default async function PaymentStepPage({
  searchParams,
}: {
  searchParams: Promise<{ message?: string }>;
}) {
  const params = await searchParams;
  const { account, onboardingStatus } =
    await requireOnboardingStep("/onboarding/platnosc");

  const betaEligible = Boolean(onboardingStatus?.access?.betaEligible);
  const isBetaActive = onboardingStatus?.access?.type === "beta";
  const isPaidActive = Boolean(
    account.profile?.subscription_status === "active" &&
      account.profile?.activation_paid,
  );
  const isActive = Boolean(onboardingStatus?.access?.active || isPaidActive);

  return (
    <main className="min-h-screen bg-[#050607] text-zinc-100">
      <div className="mx-auto flex min-h-screen w-full max-w-6xl flex-col px-5 py-6 sm:px-8">
        <header className="flex items-center justify-between border-b border-white/10 pb-5">
          <BrandLink href="/" className="text-sm font-semibold text-white" />
          <LogoutLink />
        </header>

        <section className="grid flex-1 gap-8 py-8 lg:grid-cols-[0.9fr_0.7fr]">
          <div>
            <Stepper />
            <p className="mt-8 text-xs font-semibold uppercase text-[#3DFF7A]">
              Krok 2
            </p>
            <h1 className="mt-3 max-w-3xl text-4xl font-semibold leading-tight text-white sm:text-5xl">
              Uruchom subskrypcję.
            </h1>
            <p className="mt-5 max-w-2xl text-base leading-7 text-zinc-300">
              Jeden plan miesięczny. Po opłaceniu subskrypcji przejdziesz dalej
              do konfiguracji Google i Telegrama.
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
                  {isBetaActive ? "Dostęp beta aktywny." : "Subskrypcja aktywna."}
                </p>
                <p className="mt-2 text-sm leading-6 text-zinc-300">
                  {isBetaActive
                    ? "Możesz przejść dalej bez płatności. Następny etap to Google, zasoby Google i parowanie Telegrama."
                    : "Płatność jest zaksięgowana. Następny etap to Google, zasoby Google i parowanie Telegrama."}
                </p>
                <Link
                  href="/onboarding/google"
                  className="mt-5 inline-flex rounded-full bg-[#3DFF7A] px-5 py-2.5 text-sm font-semibold text-black"
                >
                  Przejdź do Google
                </Link>
              </div>
            ) : (
              <div className="mt-8 space-y-4">
                {betaEligible ? <BetaAccessCard /> : null}
                <div className="max-w-xl">
                  <PlanCard
                    title="OZE-Agent"
                    price="399 zł / mies."
                    note="Pełny dostęp do agenta, panelu i generatora ofert. Rezygnujesz kiedy chcesz."
                  />
                </div>
              </div>
            )}
          </div>

          <aside className="h-fit rounded-[8px] border border-white/10 bg-white/[0.04] p-6">
            <p className="text-sm font-semibold text-white">Koszyk</p>
            <div className="mt-5 space-y-4 text-sm">
              <Row label="Subskrypcja miesięczna" value="399 zł / mies." />
            </div>
            <div className="mt-6 border-t border-white/10 pt-5">
              <p className="text-sm leading-6 text-zinc-400">
                Po płatności wrócisz do konfiguracji konta. Jeśli płatność nie
                przejdzie, możesz wrócić tutaj i spróbować ponownie.
              </p>
            </div>
          </aside>
        </section>
      </div>
    </main>
  );
}

function BetaAccessCard() {
  return (
    <form
      action="/onboarding/beta-access"
      method="post"
      className="rounded-[8px] border border-[#3DFF7A]/25 bg-[#3DFF7A]/10 p-5"
    >
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-sm font-semibold text-white">Dostęp beta</p>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-300">
            Twój email jest na liście beta testerów. Możesz przejść dalej bez
            płatności i skonfigurować Google oraz Telegram.
          </p>
        </div>
        <button
          type="submit"
          className="inline-flex shrink-0 items-center justify-center rounded-full bg-[#3DFF7A] px-5 py-3 text-sm font-semibold text-black transition hover:bg-[#6DFF98]"
        >
          Kontynuuj jako beta tester
        </button>
      </div>
    </form>
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
  title,
  price,
  note,
}: {
  title: string;
  price: string;
  note: string;
}) {
  return (
    <form
      action="/onboarding/checkout"
      method="post"
      className="rounded-[8px] border border-white/10 bg-black/20 p-5"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-white">{title}</p>
          <p className="mt-3 text-3xl font-semibold text-white">{price}</p>
        </div>
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
