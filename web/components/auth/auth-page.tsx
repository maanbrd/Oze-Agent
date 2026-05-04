"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useMemo, useState } from "react";

type AuthMode = "login" | "register";

type AuthPageProps = {
  mode: AuthMode;
};

type FormState = {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  password: string;
  region: string;
  specialty: string;
  referralSource: string;
  experience: string;
  consentTerms: boolean;
  consentMarketing: boolean;
  consentPhoneContact: boolean;
};

const initialState: FormState = {
  firstName: "",
  lastName: "",
  email: "",
  phone: "",
  password: "",
  region: "",
  specialty: "",
  referralSource: "",
  experience: "",
  consentTerms: false,
  consentMarketing: false,
  consentPhoneContact: false,
};

const regions = [
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
];

const specialties = ["PV", "Pompy ciepła", "PV + magazyn", "Wszystko"];
const referralSources = ["Facebook", "Polecenie", "Google", "Inne"];
const experiences = ["do 1 roku", "1-3 lata", "3+ lata"];

const fieldClass =
  "mt-2 h-12 w-full rounded-[8px] border border-white/10 bg-black/28 px-4 text-sm text-white outline-none transition placeholder:text-zinc-600 focus:border-[#3DFF7A]/50 focus:ring-4 focus:ring-[#3DFF7A]/10";

const labelClass = "text-xs font-semibold uppercase tracking-[0] text-[#6DFF98]";

const secondaryButtonClass =
  "inline-flex h-12 items-center justify-center rounded-full border border-white/14 px-6 text-sm font-semibold text-zinc-200 transition hover:border-[#3DFF7A]/60 hover:text-white";

export function AuthPage({ mode }: AuthPageProps) {
  const router = useRouter();
  const [form, setForm] = useState<FormState>(initialState);
  const [error, setError] = useState("");
  const isRegister = mode === "register";

  const copy = useMemo(
    () =>
      isRegister
        ? {
            eyebrow: "Rejestracja",
            title: "Załóż konto i przejdź do onboardingu.",
            body: "Ten krok tworzy bezpieczne konto. Płatność, Google OAuth i parowanie Telegrama będą kolejnymi krokami tego samego flow.",
            highlights: ["Auth + RLS", "Płatność", "Google + Telegram"],
            cta: "Dalej: płatność",
            formTitle: "Załóż konto",
            switchLabel: "Masz już konto?",
            switchCta: "Zaloguj się",
            switchHref: "/login",
          }
        : {
            eyebrow: "Logowanie",
            title: "Wejdź do panelu handlowca",
            body: "Zaloguj się i wróć do generatora ofert oraz ustawień sprzedażowych.",
            highlights: ["Generator ofert", "Gmail handlowca", "Google Sheets"],
            cta: "Zaloguj się",
            formTitle: "Zaloguj się",
            switchLabel: "Nie masz konta?",
            switchCta: "Załóż konto",
            switchHref: "/rejestracja",
          },
    [isRegister],
  );

  function updateField<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((current) => ({ ...current, [key]: value }));
    setError("");
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const email = form.email.trim();
    const password = form.password.trim();
    const firstName = form.firstName.trim();
    const lastName = form.lastName.trim();
    const phone = form.phone.trim();
    const onboardingSurvey = {
      region: form.region,
      specialty: form.specialty,
      referral_source: form.referralSource,
      experience: form.experience,
    };

    if (!email || !password) {
      setError("Uzupełnij email i hasło.");
      return;
    }

    if (!email.includes("@")) {
      setError("Wpisz poprawny adres email.");
      return;
    }

    const minimumPasswordLength = isRegister ? 8 : 6;

    if (password.length < minimumPasswordLength) {
      setError(`Hasło musi mieć co najmniej ${minimumPasswordLength} znaków.`);
      return;
    }

    if (isRegister && (!firstName || !lastName || !phone)) {
      setError("Uzupełnij imię, nazwisko i telefon.");
      return;
    }

    if (
      isRegister &&
      (!onboardingSurvey.region ||
        !onboardingSurvey.specialty ||
        !onboardingSurvey.referral_source ||
        !onboardingSurvey.experience)
    ) {
      setError("Uzupełnij krótką ankietę onboardingową.");
      return;
    }

    if (isRegister && !form.consentTerms) {
      setError("Regulamin i polityka prywatności są wymagane.");
      return;
    }

    const displayName = [firstName, lastName].filter(Boolean).join(" ") || email;
    const session = {
      email,
      displayName,
      firstName,
      lastName,
      phone,
      consent_terms: form.consentTerms,
      consent_marketing: form.consentMarketing,
      consent_phone_contact: form.consentPhoneContact,
      onboarding_survey: onboardingSurvey,
      region: onboardingSurvey.region,
      specialty: onboardingSurvey.specialty,
      referral_source: onboardingSurvey.referral_source,
      experience: onboardingSurvey.experience,
      createdAt: new Date().toISOString(),
      source: mode,
    };

    localStorage.setItem("oze-agent-session", JSON.stringify(session));
    router.push("/oferty");
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#050607] text-zinc-100">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_22%_8%,rgba(61,255,122,0.16),transparent_32%),radial-gradient(circle_at_82%_18%,rgba(20,184,166,0.12),transparent_30%),linear-gradient(180deg,#0b0d10_0%,#050607_72%)]" />
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[#3DFF7A]/60 to-transparent" />

      <div className="relative mx-auto flex min-h-screen w-full max-w-6xl flex-col px-5 py-6 sm:px-8">
        <header className="flex items-center justify-between">
          <Link
            href="/"
            className="flex items-center gap-3 text-sm font-semibold tracking-[0] text-white"
          >
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

        <section className="grid flex-1 items-center gap-10 py-14 lg:grid-cols-[0.9fr_0.8fr] lg:items-start lg:py-20">
          <div className="max-w-3xl">
            <p className="mb-5 text-xs font-semibold uppercase tracking-[0] text-[#3DFF7A]">
              {copy.eyebrow}
            </p>
            <h1 className="max-w-3xl text-5xl font-semibold leading-[0.98] tracking-[0] text-white sm:text-6xl lg:text-7xl">
              {copy.title}
            </h1>
            <p className="mt-7 max-w-2xl text-lg leading-8 text-zinc-300 sm:text-xl">
              {copy.body}
            </p>

            <div className="mt-9 grid gap-3 sm:grid-cols-3">
              {copy.highlights.map((item) => (
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
            onSubmit={submit}
            className="rounded-[8px] border border-white/10 bg-white/[0.04] p-5 shadow-[0_24px_80px_rgba(0,0,0,0.36)] backdrop-blur sm:p-6"
          >
            <div className="mb-6">
              <h2 className="text-2xl font-semibold tracking-[0] text-white">
                {copy.formTitle}
              </h2>
              <p className="mt-2 text-sm leading-6 text-zinc-400">
                {copy.switchLabel}{" "}
                <Link href={copy.switchHref} className="font-semibold text-[#6DFF98]">
                  {copy.switchCta}
                </Link>
              </p>
            </div>

            <div className="space-y-4">
              {isRegister ? (
                <div className="grid gap-4 sm:grid-cols-2">
                  <label>
                    <span className={labelClass}>Imię</span>
                    <input
                      className={fieldClass}
                      autoComplete="given-name"
                      value={form.firstName}
                      onChange={(event) => updateField("firstName", event.target.value)}
                    />
                  </label>
                  <label>
                    <span className={labelClass}>Nazwisko</span>
                    <input
                      className={fieldClass}
                      autoComplete="family-name"
                      value={form.lastName}
                      onChange={(event) => updateField("lastName", event.target.value)}
                    />
                  </label>
                </div>
              ) : null}

              <label className="block">
                <span className={labelClass}>Email</span>
                <input
                  className={fieldClass}
                  type="email"
                  autoComplete={isRegister ? "email" : "username"}
                  inputMode="email"
                  value={form.email}
                  onChange={(event) => updateField("email", event.target.value)}
                />
              </label>

              {isRegister ? (
                <label className="block">
                  <span className={labelClass}>Telefon</span>
                  <input
                    className={fieldClass}
                    type="tel"
                    autoComplete="tel"
                    inputMode="tel"
                    value={form.phone}
                    onChange={(event) => updateField("phone", event.target.value)}
                  />
                </label>
              ) : null}

              <label className="block">
                <span className={labelClass}>Hasło</span>
                <input
                  className={fieldClass}
                  type="password"
                  autoComplete={isRegister ? "new-password" : "current-password"}
                  minLength={isRegister ? 8 : 6}
                  value={form.password}
                  onChange={(event) => updateField("password", event.target.value)}
                />
              </label>

              {isRegister ? (
                <div className="space-y-3">
                  <div className="border-t border-white/10 pt-5">
                    <p className="text-sm font-semibold text-white">Krótka ankieta</p>
                    <p className="mt-1 text-xs leading-5 text-zinc-500">
                      Pomaga ustawić onboarding pod teren, w którym pracujesz.
                    </p>
                    <SelectField
                      label="Region działania"
                      value={form.region}
                      options={regions}
                      onChange={(value) => updateField("region", value)}
                    />
                    <SelectField
                      label="Branża"
                      value={form.specialty}
                      options={specialties}
                      onChange={(value) => updateField("specialty", value)}
                    />
                    <SelectField
                      label="Skąd nas znasz"
                      value={form.referralSource}
                      options={referralSources}
                      onChange={(value) => updateField("referralSource", value)}
                    />
                    <SelectField
                      label="Doświadczenie w OZE"
                      value={form.experience}
                      options={experiences}
                      onChange={(value) => updateField("experience", value)}
                    />
                  </div>
                  <label className="flex items-start gap-3 rounded-[8px] border border-white/10 bg-black/20 p-3 text-sm leading-6 text-zinc-300">
                    <input
                      required
                      name="terms"
                      className="mt-1 h-4 w-4 accent-[#3DFF7A]"
                      type="checkbox"
                      checked={form.consentTerms}
                      onChange={(event) => updateField("consentTerms", event.target.checked)}
                    />
                    <span>Akceptuję regulamin i politykę prywatności.</span>
                  </label>
                  <label className="flex items-start gap-3 rounded-[8px] border border-white/10 bg-black/20 p-3 text-sm leading-6 text-zinc-400">
                    <input
                      name="marketing"
                      className="mt-1 h-4 w-4 accent-[#3DFF7A]"
                      type="checkbox"
                      checked={form.consentMarketing}
                      onChange={(event) =>
                        updateField("consentMarketing", event.target.checked)
                      }
                    />
                    <span>Chcę otrzymywać informacje o rozwoju Agent-OZE.</span>
                  </label>
                  <label className="flex items-start gap-3 rounded-[8px] border border-white/10 bg-black/20 p-3 text-sm leading-6 text-zinc-400">
                    <input
                      name="phoneContact"
                      className="mt-1 h-4 w-4 accent-[#3DFF7A]"
                      type="checkbox"
                      checked={form.consentPhoneContact}
                      onChange={(event) =>
                        updateField("consentPhoneContact", event.target.checked)
                      }
                    />
                    <span>Możecie zadzwonić, jeśli onboarding utknie.</span>
                  </label>
                </div>
              ) : null}
            </div>

            {error ? (
              <p className="mt-4 rounded-[8px] border border-red-400/20 bg-red-950/20 px-4 py-3 text-sm text-red-200">
                {error}
              </p>
            ) : null}

            <div className="mt-6 flex flex-col gap-3 sm:flex-row">
              <button
                type="submit"
                className="inline-flex h-12 flex-1 items-center justify-center rounded-full bg-[#3DFF7A] px-6 text-sm font-semibold text-black shadow-[0_0_36px_rgba(61,255,122,0.22)] transition hover:translate-y-[-1px] hover:bg-[#6DFF98]"
              >
                {copy.cta}
              </button>
              <Link href="/" className={secondaryButtonClass}>
                Landing
              </Link>
            </div>
          </form>
        </section>
      </div>
    </main>
  );
}

function SelectField({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
}) {
  return (
    <label className="mt-4 block text-sm font-medium text-zinc-200">
      {label}
      <select
        required
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="mt-2 h-12 w-full rounded-[8px] border border-white/10 bg-black/28 px-4 text-sm text-white outline-none transition focus:border-[#3DFF7A]/50 focus:ring-4 focus:ring-[#3DFF7A]/10"
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
