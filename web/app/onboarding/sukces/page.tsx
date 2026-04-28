import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Płatność przyjęta | Agent-OZE",
};

export default function PaymentSuccessPage() {
  return (
    <main className="grid min-h-screen place-items-center bg-[#050607] px-5 text-zinc-100">
      <section className="w-full max-w-2xl rounded-[8px] border border-[#3DFF7A]/30 bg-[#3DFF7A]/10 p-8">
        <p className="text-xs font-semibold uppercase text-[#3DFF7A]">
          Płatność
        </p>
        <h1 className="mt-3 text-3xl font-semibold text-white">
          Płatność przyjęta.
        </h1>
        <p className="mt-4 text-sm leading-7 text-zinc-300">
          Stripe wysłał potwierdzenie. Po zaksięgowaniu konto przejdzie na
          aktywną subskrypcję. Następny etap to Google OAuth, zasoby Google i
          Telegram.
        </p>
        <Link
          href="/onboarding/google"
          className="mt-7 inline-flex rounded-full bg-[#3DFF7A] px-5 py-3 text-sm font-semibold text-black"
        >
          Przejdź do Google
        </Link>
      </section>
    </main>
  );
}
