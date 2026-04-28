import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import { signup } from "@/app/auth/actions";
import { createClient } from "@/lib/supabase/server";

export const metadata: Metadata = {
  title: "Rejestracja | Agent-OZE",
  description: "Założenie konta Agent-OZE.",
};

export default async function RegistrationPage({
  searchParams,
}: {
  searchParams: Promise<{ message?: string }>;
}) {
  const params = await searchParams;
  const supabase = await createClient();
  const { data } = await supabase.auth.getClaims();

  if (data?.claims) {
    redirect("/dashboard");
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#050607] text-zinc-100">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_24%_12%,rgba(61,255,122,0.2),transparent_34%),radial-gradient(circle_at_78%_22%,rgba(20,184,166,0.14),transparent_32%),linear-gradient(180deg,#0b0d10_0%,#050607_72%)]" />
      <div className="relative mx-auto flex min-h-screen w-full max-w-6xl flex-col px-5 py-6 sm:px-8">
        <Header />
        <section className="flex flex-1 items-center py-16">
          <div className="grid w-full gap-10 lg:grid-cols-[0.9fr_0.8fr] lg:items-start">
            <div className="pt-2">
              <p className="mb-5 text-xs font-semibold uppercase text-[#3DFF7A]">
                Rejestracja
              </p>
              <h1 className="max-w-3xl text-5xl font-semibold leading-[0.98] text-white sm:text-6xl">
                Załóż konto i przejdź do onboardingu.
              </h1>
              <p className="mt-7 max-w-2xl text-lg leading-8 text-zinc-300">
                Ten krok tworzy bezpieczne konto. Płatność, Google OAuth i
                parowanie Telegrama będą kolejnymi krokami tego samego flow.
              </p>
              <div className="mt-9 grid gap-3 sm:grid-cols-3">
                {["Auth + RLS", "Płatność", "Google + Telegram"].map((item) => (
                  <div
                    key={item}
                    className="rounded-[8px] border border-white/10 bg-white/[0.04] px-4 py-3 text-sm leading-6 text-zinc-300"
                  >
                    <span className="mr-2 inline-block h-2 w-2 rounded-full bg-[#3DFF7A]" />
                    {item}
                  </div>
                ))}
              </div>
            </div>

            <form
              action={signup}
              className="rounded-[8px] border border-white/10 bg-white/[0.04] p-6 shadow-2xl shadow-black/30"
            >
              {params.message ? (
                <p className="mb-5 rounded-[8px] border border-red-400/20 bg-red-400/10 px-4 py-3 text-sm leading-6 text-zinc-200">
                  {params.message}
                </p>
              ) : null}
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Imię" name="firstName" autoComplete="given-name" />
                <Field label="Nazwisko" name="lastName" autoComplete="family-name" />
              </div>
              <Field label="Email" name="email" type="email" autoComplete="email" />
              <Field label="Telefon" name="phone" type="tel" autoComplete="tel" />
              <Field
                label="Hasło"
                name="password"
                type="password"
                autoComplete="new-password"
                minLength={8}
              />
              <label className="mt-5 flex gap-3 text-sm leading-6 text-zinc-300">
                <input required name="terms" type="checkbox" className="mt-1 h-4 w-4" />
                <span>Akceptuję regulamin i politykę prywatności.</span>
              </label>
              <label className="mt-3 flex gap-3 text-sm leading-6 text-zinc-400">
                <input name="marketing" type="checkbox" className="mt-1 h-4 w-4" />
                <span>Chcę otrzymywać informacje o rozwoju Agent-OZE.</span>
              </label>
              <label className="mt-3 flex gap-3 text-sm leading-6 text-zinc-400">
                <input name="phoneContact" type="checkbox" className="mt-1 h-4 w-4" />
                <span>Możecie zadzwonić, jeśli onboarding utknie.</span>
              </label>
              <button
                type="submit"
                className="mt-7 inline-flex w-full items-center justify-center rounded-full bg-[#3DFF7A] px-6 py-3 text-sm font-semibold text-black shadow-[0_0_36px_rgba(61,255,122,0.22)] transition hover:bg-[#6DFF98]"
              >
                Utwórz konto
              </button>
              <p className="mt-5 text-sm leading-6 text-zinc-400">
                Masz konto?{" "}
                <Link href="/login" className="font-semibold text-[#3DFF7A]">
                  Zaloguj się
                </Link>
              </p>
            </form>
          </div>
        </section>
      </div>
    </main>
  );
}

function Field({
  label,
  name,
  type = "text",
  autoComplete,
  minLength,
}: {
  label: string;
  name: string;
  type?: string;
  autoComplete?: string;
  minLength?: number;
}) {
  return (
    <label className="mt-5 block text-sm font-medium text-zinc-200 first:mt-0">
      {label}
      <input
        required
        type={type}
        name={name}
        autoComplete={autoComplete}
        minLength={minLength}
        className="mt-2 w-full rounded-[8px] border border-white/10 bg-black/30 px-4 py-3 text-base text-white outline-none transition focus:border-[#3DFF7A]/70"
      />
    </label>
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
