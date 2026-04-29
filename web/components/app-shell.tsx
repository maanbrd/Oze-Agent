import Link from "next/link";
import { OnboardingGate } from "@/components/onboarding-gate";
import type { CurrentAccount } from "@/lib/api/account";
import type { OnboardingStatus } from "@/lib/api/onboarding";

const navItems = [
  ["Dashboard", "/dashboard"],
  ["Klienci", "/klienci"],
  ["Kalendarz", "/kalendarz"],
  ["Płatności", "/platnosci"],
  ["Ustawienia", "/ustawienia"],
  ["Import", "/import"],
  ["Instrukcja", "/instrukcja"],
  ["FAQ", "/faq"],
] as const;

function googleLinks(account: CurrentAccount) {
  const profile = account.profile;
  return {
    sheets: profile?.google_sheets_id
      ? `https://docs.google.com/spreadsheets/d/${profile.google_sheets_id}`
      : null,
    calendar: profile?.google_calendar_id
      ? `https://calendar.google.com/calendar/u/0/r?cid=${encodeURIComponent(
          profile.google_calendar_id,
        )}`
      : null,
    drive: profile?.google_drive_folder_id
      ? `https://drive.google.com/drive/folders/${profile.google_drive_folder_id}`
      : null,
  };
}

export function AppShell({
  account,
  onboardingStatus,
  children,
}: {
  account: CurrentAccount;
  onboardingStatus: OnboardingStatus | null;
  children: React.ReactNode;
}) {
  const links = googleLinks(account);
  const email = account.profile?.email ?? account.email ?? "Konto";

  return (
    <main className="min-h-screen bg-[#050607] text-zinc-100">
      <div className="grid min-h-screen lg:grid-cols-[248px_1fr]">
        <aside className="border-b border-white/10 bg-[#090b0f] px-5 py-5 lg:border-b-0 lg:border-r">
          <Link href="/dashboard" className="flex items-center gap-3 text-sm font-semibold text-white">
            <span className="grid h-8 w-8 place-items-center rounded-full border border-[#3DFF7A]/40 bg-[#3DFF7A]/10">
              <span className="h-2.5 w-2.5 rounded-full bg-[#3DFF7A]" />
            </span>
            Agent-OZE
          </Link>
          <nav className="mt-7 grid gap-1">
            {navItems.map(([label, href]) => (
              <Link
                key={href}
                href={href}
                className="rounded-[8px] px-3 py-2 text-sm text-zinc-400 transition hover:bg-white/[0.05] hover:text-white"
              >
                {label}
              </Link>
            ))}
          </nav>
          <div className="mt-7 rounded-[8px] border border-white/10 bg-white/[0.04] p-3 text-xs leading-5 text-zinc-400">
            CRM read-only. Edycja: Sheets i Calendar.
          </div>
        </aside>

        <section className="min-w-0">
          <header className="sticky top-0 z-20 border-b border-white/10 bg-[#050607]/90 px-5 py-4 backdrop-blur lg:px-8">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <label className="w-full max-w-xl text-xs font-medium uppercase text-zinc-500">
                Szukaj klienta
                <input
                  type="search"
                  placeholder="Nazwisko, miasto, telefon"
                  className="mt-2 w-full rounded-[8px] border border-white/10 bg-black/30 px-4 py-2.5 text-sm normal-case text-white outline-none focus:border-[#3DFF7A]/70"
                />
              </label>
              <div className="text-sm text-zinc-400">{email}</div>
            </div>
          </header>
          <div className="px-5 py-6 lg:px-8">
            <OnboardingGate status={onboardingStatus} />
            {children}
          </div>
        </section>
      </div>

      <div className="fixed bottom-5 right-5 z-30 grid gap-2">
        <GoogleFab label="Sheets" href={links.sheets} />
        <GoogleFab label="Calendar" href={links.calendar} />
        <GoogleFab label="Drive" href={links.drive} />
      </div>
    </main>
  );
}

function GoogleFab({ label, href }: { label: string; href: string | null }) {
  if (!href) {
    return (
      <span className="rounded-full border border-white/10 bg-zinc-900 px-4 py-2 text-xs text-zinc-500">
        {label}: brak
      </span>
    );
  }

  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="rounded-full border border-[#3DFF7A]/30 bg-[#3DFF7A]/15 px-4 py-2 text-xs font-semibold text-[#3DFF7A] shadow-[0_0_24px_rgba(61,255,122,0.14)]"
    >
      {label}
    </a>
  );
}
