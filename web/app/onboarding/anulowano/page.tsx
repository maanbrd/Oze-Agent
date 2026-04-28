import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Płatność anulowana | Agent-OZE",
};

export default function PaymentCanceledPage() {
  return (
    <main className="grid min-h-screen place-items-center bg-[#050607] px-5 text-zinc-100">
      <section className="w-full max-w-2xl rounded-[8px] border border-white/10 bg-white/[0.04] p-8">
        <p className="text-xs font-semibold uppercase text-zinc-500">
          Płatność
        </p>
        <h1 className="mt-3 text-3xl font-semibold text-white">
          Płatność anulowana.
        </h1>
        <p className="mt-4 text-sm leading-7 text-zinc-300">
          Konto zostało utworzone, ale subskrypcja nadal czeka. Możesz wrócić do
          wyboru planu i uruchomić checkout jeszcze raz.
        </p>
        <Link
          href="/onboarding/platnosc"
          className="mt-7 inline-flex rounded-full bg-[#3DFF7A] px-5 py-3 text-sm font-semibold text-black"
        >
          Wróć do płatności
        </Link>
      </section>
    </main>
  );
}
