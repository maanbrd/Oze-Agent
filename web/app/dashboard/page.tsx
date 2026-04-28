import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { logout } from "@/app/auth/actions";
import { createClient } from "@/lib/supabase/server";

export const metadata: Metadata = {
  title: "Dashboard | Agent-OZE",
  description: "Panel Agent-OZE.",
};

export default async function DashboardPage() {
  const supabase = await createClient();
  const { data: claimsData } = await supabase.auth.getClaims();

  if (!claimsData?.claims) {
    redirect("/login?next=/dashboard");
  }

  return (
    <main className="min-h-screen bg-[#050607] text-zinc-100">
      <div className="mx-auto flex min-h-screen w-full max-w-7xl flex-col px-5 py-6 sm:px-8">
        <header className="flex items-center justify-between border-b border-white/10 pb-5">
          <div>
            <p className="text-xs font-semibold uppercase text-[#3DFF7A]">
              Dashboard
            </p>
            <h1 className="mt-2 text-2xl font-semibold text-white">
              {claimsData.claims.email || "Konto Agent-OZE"}
            </h1>
          </div>
          <form action={logout}>
            <button
              type="submit"
              className="rounded-full border border-white/12 px-4 py-2 text-sm font-semibold text-zinc-300 transition hover:border-[#3DFF7A]/60 hover:text-white"
            >
              Wyloguj
            </button>
          </form>
        </header>

        <section className="grid flex-1 gap-5 py-8 lg:grid-cols-[0.75fr_1.25fr]">
          <div className="rounded-[8px] border border-white/10 bg-white/[0.04] p-6">
            <h2 className="text-lg font-semibold text-white">Status konta</h2>
            <div className="mt-5 space-y-3">
              <StatusRow label="Auth + RLS" done />
              <StatusRow
                label="Subskrypcja"
                done={false}
                value="następny etap"
              />
              <StatusRow label="Google" done={false} />
              <StatusRow label="Telegram" done={false} />
              <StatusRow label="Onboarding" done={false} />
            </div>
          </div>

          <div className="rounded-[8px] border border-white/10 bg-white/[0.04] p-6">
            <h2 className="text-lg font-semibold text-white">
              Następny krok: onboarding
            </h2>
            <p className="mt-4 max-w-2xl text-sm leading-7 text-zinc-300">
              Fundament sesji jest gotowy. Kolejne etapy podepną płatność,
              Google OAuth, tworzenie arkusza/kalendarza/folderu i parowanie
              Telegrama. Dane klientów nadal będą czytane z Google, a mutacje
              CRM zostają po stronie agenta w Telegramie.
            </p>
            <p className="mt-4 max-w-2xl text-sm leading-7 text-zinc-500">
              Next.js używa Supabase tylko do sesji. Dane profilu i dashboardu
              będą pobierane przez FastAPI po weryfikacji JWT.
            </p>
            <div className="mt-6 grid gap-3 sm:grid-cols-3">
              {["Płatność", "Google OAuth", "Telegram pairing"].map((item) => (
                <div
                  key={item}
                  className="rounded-[8px] border border-white/10 bg-black/20 px-4 py-3 text-sm text-zinc-300"
                >
                  {item}
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

function StatusRow({
  label,
  done,
  value,
}: {
  label: string;
  done: boolean;
  value?: string;
}) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-[8px] border border-white/10 bg-black/20 px-4 py-3 text-sm">
      <span className="text-zinc-300">{label}</span>
      <span className={done ? "text-[#3DFF7A]" : "text-zinc-500"}>
        {value ?? (done ? "gotowe" : "czeka")}
      </span>
    </div>
  );
}
