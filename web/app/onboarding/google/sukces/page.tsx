import Link from "next/link";
import { requireCurrentAccount } from "@/lib/api/account";
import { getOnboardingStatus } from "@/lib/api/onboarding";

export default async function GoogleSuccessPage() {
  await requireCurrentAccount("/onboarding/google/sukces");
  const status = await getOnboardingStatus();
  const connected = Boolean(status?.steps.google);

  return (
    <main className="min-h-screen bg-[#050607] px-5 py-8 text-zinc-100">
      <section className="mx-auto max-w-2xl">
        <p className="text-xs font-semibold uppercase text-[#3DFF7A]">Google</p>
        <h1 className="mt-3 text-4xl font-semibold text-white">
          {connected ? "Google jest połączony." : "Sprawdzamy połączenie Google."}
        </h1>
        <p className="mt-4 text-sm leading-6 text-zinc-300">
          {connected
            ? "Teraz utworzymy lub podłączymy zasoby: Sheets, Calendar i Drive."
            : "Nie widzimy jeszcze aktywnego tokenu Google. Wróć do autoryzacji i spróbuj ponownie."}
        </p>
        <Link
          href={connected ? "/onboarding/zasoby" : "/onboarding/google"}
          className="mt-6 inline-flex rounded-full bg-[#3DFF7A] px-5 py-3 text-sm font-semibold text-black"
        >
          {connected ? "Dalej" : "Wróć do Google"}
        </Link>
      </section>
    </main>
  );
}
