import Link from "next/link";
import { startGoogleOAuthAction } from "@/app/onboarding/actions";
import { LogoutLink } from "@/components/auth/logout-link";
import { requireOnboardingStep } from "@/lib/auth/guards";

export const dynamic = "force-dynamic";

export default async function GoogleOnboardingPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string; message?: string }>;
}) {
  const params = await searchParams;
  const { onboardingStatus: status } =
    await requireOnboardingStep("/onboarding/google");
  const connected = status?.steps.google;

  return (
    <main className="min-h-screen bg-[#050607] px-5 py-8 text-zinc-100">
      <section className="mx-auto max-w-3xl">
        <div className="mb-8 flex justify-end">
          <LogoutLink />
        </div>
        <p className="text-xs font-semibold uppercase text-[#3DFF7A]">Krok 3</p>
        <h1 className="mt-3 text-4xl font-semibold text-white">
          Połącz Google.
        </h1>
        <p className="mt-4 text-sm leading-6 text-zinc-300">
          Web app czyta CRM z Google Sheets i Calendar. Edycja klientów i
          spotkań zostaje w Google.
        </p>
        {params.error ? (
          <p className="mt-5 rounded-[8px] border border-red-400/20 bg-red-400/10 px-4 py-3 text-sm">
            Autoryzacja Google nie powiodła się. Spróbuj ponownie.
          </p>
        ) : null}
        {params.message ? (
          <p className="mt-5 rounded-[8px] border border-red-400/20 bg-red-400/10 px-4 py-3 text-sm">
            {params.message}
          </p>
        ) : null}
        {connected ? (
          <Link
            href="/onboarding/zasoby"
            className="mt-6 inline-flex rounded-full bg-[#3DFF7A] px-5 py-3 text-sm font-semibold text-black"
          >
            Przejdź do zasobów
          </Link>
        ) : (
          <form action={startGoogleOAuthAction} className="mt-6">
            <button className="rounded-full bg-[#3DFF7A] px-5 py-3 text-sm font-semibold text-black">
              Połącz konto Google
            </button>
          </form>
        )}
      </section>
    </main>
  );
}
