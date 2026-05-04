import Link from "next/link";
import { generateTelegramCodeAction } from "@/app/onboarding/actions";
import { requireCurrentAccount } from "@/lib/api/account";
import {
  getOnboardingStatus,
  getTelegramStatus,
} from "@/lib/api/onboarding";

export const dynamic = "force-dynamic";

export default async function TelegramOnboardingPage({
  searchParams,
}: {
  searchParams: Promise<{ message?: string }>;
}) {
  const params = await searchParams;
  await requireCurrentAccount("/onboarding/telegram");
  const [status, pairing] = await Promise.all([
    getOnboardingStatus(),
    getTelegramStatus(),
  ]);
  const paired = pairing?.paired || status?.steps.telegram;

  return (
    <main className="min-h-screen bg-[#050607] px-5 py-8 text-zinc-100">
      <section className="mx-auto max-w-3xl">
        <p className="text-xs font-semibold uppercase text-[#3DFF7A]">Krok 5</p>
        <h1 className="mt-3 text-4xl font-semibold text-white">
          Połącz Telegrama.
        </h1>
        <p className="mt-4 text-sm leading-6 text-zinc-300">
          Telegram paruje konto z botem. CRM edytujesz w Google Sheets i
          Calendar przez bezpośrednie linki z panelu.
        </p>
        {params.message ? (
          <p className="mt-5 rounded-[8px] border border-red-400/20 bg-red-400/10 px-4 py-3 text-sm">
            {params.message}
          </p>
        ) : null}
        {paired ? (
          <div className="mt-6 rounded-[8px] border border-[#3DFF7A]/30 bg-[#3DFF7A]/10 p-5">
            <meta httpEquiv="refresh" content="4;url=/dashboard?onboarding=complete" />
            <p className="text-sm font-semibold uppercase text-[#3DFF7A]">
              Rejestracja ukończona
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-white">
              Telegram połączony.
            </h2>
            <p className="mt-3 max-w-xl text-sm leading-6 text-zinc-200">
              Konto, płatność, Google i Telegram są gotowe. Za chwilę
              przeniesiemy Cię do głównego panelu.
            </p>
            <Link
              href="/dashboard?onboarding=complete"
              className="mt-4 inline-flex rounded-full bg-[#3DFF7A] px-5 py-3 text-sm font-semibold text-black"
            >
              Przejdź do panelu
            </Link>
          </div>
        ) : (
          <div className="mt-6 rounded-[8px] border border-white/10 bg-white/[0.04] p-5">
            <p className="text-sm text-zinc-300">Kod parowania</p>
            <p className="mt-3 text-5xl font-semibold tracking-[0.2em] text-white">
              {pairing?.code ?? "------"}
            </p>
            <p className="mt-5 text-sm text-zinc-300">
              Wyślij do bota w Telegramie:
            </p>
            <code className="mt-2 block rounded-[8px] bg-black/40 px-4 py-3 text-lg text-white">
              /start {pairing?.code ?? "KOD"}
            </code>
            <p className="mt-3 text-sm text-zinc-400">
              Kod jest krótkotrwały. Po wpisaniu w Telegramie ta strona pokaże
              status po odświeżeniu.
            </p>
            <form action={generateTelegramCodeAction} className="mt-5">
              <button className="rounded-full border border-[#3DFF7A]/40 px-5 py-3 text-sm font-semibold text-[#3DFF7A]">
                Wygeneruj nowy kod
              </button>
            </form>
          </div>
        )}
      </section>
    </main>
  );
}
