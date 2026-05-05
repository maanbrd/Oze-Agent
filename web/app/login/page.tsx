import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import { login } from "@/app/auth/actions";
import { AuthConfigError } from "@/components/auth/auth-config-error";
import { safeLocalPath } from "@/lib/routes";
import { createClient, missingSupabaseEnvMessage } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Logowanie | Agent-OZE",
  description: "Logowanie do panelu Agent-OZE.",
};

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ message?: string; next?: string }>;
}) {
  const params = await searchParams;
  const supabaseEnvError = missingSupabaseEnvMessage();
  if (supabaseEnvError) {
    return <AuthConfigError detail={supabaseEnvError} />;
  }

  const supabase = await createClient();
  const { data } = await supabase.auth.getClaims();
  const nextPath = safeLocalPath(params.next);

  if (data?.claims) {
    redirect(nextPath);
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#050607] text-zinc-100">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_24%_12%,rgba(61,255,122,0.2),transparent_34%),radial-gradient(circle_at_78%_22%,rgba(20,184,166,0.14),transparent_32%),linear-gradient(180deg,#0b0d10_0%,#050607_72%)]" />
      <div className="relative mx-auto flex min-h-screen w-full max-w-6xl flex-col px-5 py-6 sm:px-8">
        <Header />
        <section className="flex flex-1 items-center py-16">
          <div className="grid w-full gap-10 lg:grid-cols-[0.95fr_0.75fr] lg:items-center">
            <div>
              <p className="mb-5 text-xs font-semibold uppercase text-[#3DFF7A]">
                Logowanie
              </p>
              <h1 className="max-w-3xl text-5xl font-semibold leading-[0.98] text-white sm:text-6xl">
                Wejdź do panelu przy biurku.
              </h1>
              <p className="mt-7 max-w-2xl text-lg leading-8 text-zinc-300">
                Telegram zostaje miejscem pracy w terenie. Panel pokazuje konto,
                onboarding i docelowo read-only widoki danych z Google.
              </p>
            </div>

            <form
              action={login}
              className="rounded-[8px] border border-white/10 bg-white/[0.04] p-6 shadow-2xl shadow-black/30"
            >
              {params.message ? (
                <p className="mb-5 rounded-[8px] border border-[#3DFF7A]/20 bg-[#3DFF7A]/10 px-4 py-3 text-sm leading-6 text-zinc-200">
                  {params.message}
                </p>
              ) : null}
              <input type="hidden" name="next" value={nextPath} />
              <label className="block text-sm font-medium text-zinc-200">
                Email
                <input
                  required
                  type="email"
                  name="email"
                  autoComplete="email"
                  className="mt-2 w-full rounded-[8px] border border-white/10 bg-black/30 px-4 py-3 text-base text-white outline-none transition focus:border-[#3DFF7A]/70"
                />
              </label>
              <label className="mt-5 block text-sm font-medium text-zinc-200">
                Hasło
                <input
                  required
                  type="password"
                  name="password"
                  autoComplete="current-password"
                  className="mt-2 w-full rounded-[8px] border border-white/10 bg-black/30 px-4 py-3 text-base text-white outline-none transition focus:border-[#3DFF7A]/70"
                />
              </label>
              <button
                type="submit"
                className="mt-7 inline-flex w-full items-center justify-center rounded-full bg-[#3DFF7A] px-6 py-3 text-sm font-semibold text-black shadow-[0_0_36px_rgba(61,255,122,0.22)] transition hover:bg-[#6DFF98]"
              >
                Zaloguj się
              </button>
              <p className="mt-5 text-sm leading-6 text-zinc-400">
                Nie masz konta?{" "}
                <Link href="/rejestracja" className="font-semibold text-[#3DFF7A]">
                  Załóż konto
                </Link>
              </p>
            </form>
          </div>
        </section>
      </div>
    </main>
  );
}

function Header() {
  return (
    <header className="flex items-center justify-between">
      <Link href="/" className="flex items-center gap-3 text-sm font-semibold text-white">
        <span className="grid h-8 w-8 place-items-center rounded-full border border-[#3DFF7A]/40 bg-[#3DFF7A]/10 shadow-[0_0_24px_rgba(61,255,122,0.18)]">
          <span className="h-2.5 w-2.5 rounded-full bg-[#3DFF7A]" />
        </span>
        OZE Agent
      </Link>
      <Link
        href="/"
        className="rounded-full border border-white/12 px-4 py-2 text-sm text-zinc-300 transition hover:border-[#3DFF7A]/60 hover:text-white"
      >
        Landing
      </Link>
    </header>
  );
}
