import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import { signup } from "@/app/auth/actions";
import { BrandLink } from "@/components/brand";
import { AuthConfigError } from "@/components/auth/auth-config-error";
import { createClient, missingSupabaseEnvMessage } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Rejestracja | Agent OZE",
  description: "Założenie konta Agent OZE.",
};

const REGISTRATION_MOBILE_TITLE_LINES = ["Załóż konto", "i przejdź", "do onboardingu."] as const;

export default async function RegistrationPage({
  searchParams,
}: {
  searchParams: Promise<{ message?: string }>;
}) {
  const params = await searchParams;
  const supabaseEnvError = missingSupabaseEnvMessage();
  if (supabaseEnvError) {
    return <AuthConfigError detail={supabaseEnvError} />;
  }

  const supabase = await createClient();
  const { data } = await supabase.auth.getClaims();

  if (data?.claims) {
    redirect("/onboarding/platnosc");
  }

  return (
    <main className="relative min-h-screen overflow-x-clip bg-[#050607] text-zinc-100">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_24%_12%,rgba(61,255,122,0.2),transparent_34%),radial-gradient(circle_at_78%_22%,rgba(20,184,166,0.14),transparent_32%),linear-gradient(180deg,#0b0d10_0%,#050607_72%)]" />
      <div className="relative mx-auto flex min-h-screen w-full max-w-6xl min-w-0 flex-col px-5 py-6 sm:px-8">
        <Header />
        <section className="flex flex-1 items-center py-10 sm:py-16">
          <div className="grid w-full min-w-0 max-w-[330px] gap-10 sm:max-w-none lg:grid-cols-[0.9fr_0.8fr] lg:items-start">
            <div className="min-w-0 pt-2">
              <p className="mb-5 text-xs font-semibold uppercase text-[#3DFF7A]">
                Rejestracja
              </p>
              <h1 className="max-w-3xl text-4xl font-semibold leading-[1.05] text-white sm:text-6xl sm:leading-[0.98]">
                <span className="sm:hidden">
                  {REGISTRATION_MOBILE_TITLE_LINES.map((line) => (
                    <span key={line} className="block">
                      {line}
                    </span>
                  ))}
                </span>
                <span className="hidden sm:block">Załóż konto i przejdź do onboardingu.</span>
              </h1>
              <p className="mt-7 max-w-2xl text-base leading-7 text-zinc-300 sm:text-lg sm:leading-8">
                Ten krok tworzy bezpieczne konto. Płatność, Google i
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
              className="min-w-0 rounded-[8px] border border-white/10 bg-white/[0.04] p-5 shadow-2xl shadow-black/30 sm:p-6"
            >
              {params.message ? (
                <p className="mb-5 rounded-[8px] border border-red-400/20 bg-red-400/10 px-4 py-3 text-sm leading-6 text-zinc-200">
                  {params.message}
                </p>
              ) : null}
              <div className="grid min-w-0 gap-4 sm:grid-cols-2 [&>label]:mt-0">
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
              <div className="mt-6 border-t border-white/10 pt-5">
                <p className="text-sm font-semibold text-white">Krótka ankieta</p>
                <p className="mt-1 text-xs leading-5 text-zinc-500">
                  Pomaga ustawić onboarding pod teren, w którym pracujesz.
                </p>
                <SelectField
                  label="Region działania"
                  name="region"
                  options={[
                    "dolnośląskie",
                    "kujawsko-pomorskie",
                    "lubelskie",
                    "lubuskie",
                    "łódzkie",
                    "małopolskie",
                    "mazowieckie",
                    "opolskie",
                    "podkarpackie",
                    "podlaskie",
                    "pomorskie",
                    "śląskie",
                    "świętokrzyskie",
                    "warmińsko-mazurskie",
                    "wielkopolskie",
                    "zachodniopomorskie",
                    "cała Polska",
                  ]}
                />
                <SelectField
                  label="Branża"
                  name="specialty"
                  options={["PV", "Pompy ciepła", "PV + magazyn", "Wszystko"]}
                />
                <SelectField
                  label="Skąd nas znasz"
                  name="referralSource"
                  options={["Facebook", "Polecenie", "Google", "Inne"]}
                />
                <SelectField
                  label="Doświadczenie w OZE"
                  name="experience"
                  options={["do 1 roku", "1-3 lata", "3+ lata"]}
                />
              </div>
              <label className="mt-5 flex gap-3 text-sm leading-6 text-zinc-300">
                <input required name="terms" type="checkbox" className="mt-1 h-4 w-4" />
                <span>Akceptuję regulamin i politykę prywatności.</span>
              </label>
              <label className="mt-3 flex gap-3 text-sm leading-6 text-zinc-400">
                <input name="marketing" type="checkbox" className="mt-1 h-4 w-4" />
                <span>Chcę otrzymywać informacje o rozwoju Agent OZE.</span>
              </label>
              <label className="mt-3 flex gap-3 text-sm leading-6 text-zinc-400">
                <input name="phoneContact" type="checkbox" className="mt-1 h-4 w-4" />
                <span>Możecie zadzwonić, jeśli onboarding utknie.</span>
              </label>
              <button
                type="submit"
                className="mt-7 inline-flex w-full items-center justify-center rounded-full bg-[#3DFF7A] px-6 py-3 text-sm font-semibold text-black shadow-[0_0_36px_rgba(61,255,122,0.22)] transition hover:bg-[#6DFF98]"
              >
                Dalej: płatność
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

function SelectField({
  label,
  name,
  options,
}: {
  label: string;
  name: string;
  options: string[];
}) {
  return (
    <label className="mt-4 block min-w-0 text-sm font-medium text-zinc-200">
      {label}
      <select
        required
        name={name}
        className="mt-2 w-full min-w-0 rounded-[8px] border border-white/10 bg-black/30 px-4 py-3 text-base text-white outline-none transition focus:border-[#3DFF7A]/70"
      >
        <option value="">Wybierz</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
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
    <label className="mt-5 block min-w-0 text-sm font-medium text-zinc-200 first:mt-0">
      {label}
      <input
        required
        type={type}
        name={name}
        autoComplete={autoComplete}
        minLength={minLength}
        className="mt-2 w-full min-w-0 rounded-[8px] border border-white/10 bg-black/30 px-4 py-3 text-base text-white outline-none transition focus:border-[#3DFF7A]/70"
      />
    </label>
  );
}

function Header() {
  return (
    <header className="flex min-w-0 items-center justify-between gap-4">
      <BrandLink href="/" className="text-sm font-semibold text-white" />
      <Link
        href="/"
        className="shrink-0 rounded-full border border-white/12 px-4 py-2 text-sm text-zinc-300 transition hover:border-[#3DFF7A]/60 hover:text-white"
      >
        <span className="sm:hidden">Start</span>
        <span className="hidden sm:inline">Strona główna</span>
      </Link>
    </header>
  );
}
