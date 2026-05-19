import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import { BrandLink } from "@/components/brand";
import { getCurrentAccount } from "@/lib/api/account";
import { reconcileCheckoutSession } from "@/lib/billing/checkout-reconcile";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Płatność przyjęta | Agent OZE",
};

export default async function PaymentSuccessPage({
  searchParams,
}: {
  searchParams: Promise<{ session_id?: string }>;
}) {
  const params = await searchParams;

  if (params.session_id) {
    try {
      await reconcileCheckoutSession(params.session_id);
    } catch (error) {
      console.error("reconcileCheckoutSession failed", error);
    }
  }

  const account = await getCurrentAccount();

  if (!account.authenticated) {
    redirect("/login?next=/onboarding/platnosc");
  }

  const active = isCurrentLivePaid(account.profile);

  return (
    <main className="relative grid min-h-screen place-items-center bg-[#050607] px-5 text-zinc-100">
      <BrandLink
        href="/"
        className="absolute left-5 top-5 text-sm font-semibold text-white sm:left-8 sm:top-6"
      />
      <section className="w-full max-w-2xl rounded-[8px] border border-[#3DFF7A]/30 bg-[#3DFF7A]/10 p-8">
        <p className="text-xs font-semibold uppercase text-[#3DFF7A]">
          Płatność
        </p>
        <h1 className="mt-3 text-3xl font-semibold text-white">
          {active ? "Płatność zaksięgowana." : "Czekamy na potwierdzenie płatności."}
        </h1>
        <p className="mt-4 text-sm leading-7 text-zinc-300">
          {active
            ? "Konto ma aktywną subskrypcję. Następny etap to Google, zasoby Google i Telegram."
            : "Wróciłeś do panelu, ale konto nie ma jeszcze aktywnej subskrypcji. Odśwież za chwilę albo wróć do płatności, jeśli status się nie zmieni."}
        </p>
        <Link
          href={active ? "/onboarding/google" : "/onboarding/platnosc"}
          className="mt-7 inline-flex rounded-full bg-[#3DFF7A] px-5 py-3 text-sm font-semibold text-black"
        >
          {active ? "Przejdź do Google" : "Sprawdź płatność"}
        </Link>
      </section>
    </main>
  );
}

function isCurrentLivePaid(
  profile: Awaited<ReturnType<typeof getCurrentAccount>>["profile"],
) {
  if (!profile) return false;
  if (profile.subscription_status !== "active" || !profile.activation_paid) {
    return false;
  }
  if (profile.stripe_livemode !== true) return false;
  const periodEnd = profile.subscription_current_period_end
    ? Date.parse(profile.subscription_current_period_end)
    : Number.NaN;
  return Number.isFinite(periodEnd) && periodEnd > Date.now();
}
