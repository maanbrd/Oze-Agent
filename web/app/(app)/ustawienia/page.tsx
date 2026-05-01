import Link from "next/link";
import { updateAccountAction } from "@/app/onboarding/actions";
import { CrmNotice } from "@/components/crm-notice";
import { getCurrentAccount } from "@/lib/api/account";

export default async function SettingsPage({
  searchParams,
}: {
  searchParams: Promise<{ message?: string; saved?: string }>;
}) {
  const params = await searchParams;
  const account = await getCurrentAccount();
  const profile = account.profile;

  return (
    <div className="space-y-6">
      <section>
        <p className="text-xs font-semibold uppercase text-[#3DFF7A]">
          Ustawienia
        </p>
        <h1 className="mt-2 text-3xl font-semibold text-white">
          Konto i integracje.
        </h1>
        <p className="mt-3 text-sm leading-6 text-zinc-400">
          Statusy, notatki, klienci i spotkania zostają w Google Sheets i
          Calendar. Ten formularz zapisuje tylko dane konta.
        </p>
      </section>

      <CrmNotice />

      {params.message ? (
        <p className="max-w-xl rounded-[8px] border border-red-400/20 bg-red-400/10 px-4 py-3 text-sm leading-6 text-zinc-200">
          {params.message}
        </p>
      ) : null}
      {params.saved ? (
        <p className="max-w-xl rounded-[8px] border border-[#3DFF7A]/20 bg-[#3DFF7A]/10 px-4 py-3 text-sm leading-6 text-zinc-200">
          Ustawienia konta zapisane.
        </p>
      ) : null}

      <form
        action={updateAccountAction}
        className="grid max-w-xl gap-4 rounded-[8px] border border-white/10 bg-white/[0.04] p-5"
      >
        <label className="text-sm text-zinc-300">
          Nazwa konta
          <input
            name="name"
            defaultValue={profile?.name ?? ""}
            className="mt-2 w-full rounded-[8px] border border-white/10 bg-black/30 px-4 py-3 text-white"
          />
        </label>
        <label className="text-sm text-zinc-300">
          Telefon kontaktowy
          <input
            name="phone"
            defaultValue={profile?.phone ?? ""}
            className="mt-2 w-full rounded-[8px] border border-white/10 bg-black/30 px-4 py-3 text-white"
          />
        </label>
        <button className="w-fit rounded-full bg-[#3DFF7A] px-5 py-3 text-sm font-semibold text-black">
          Zapisz ustawienia konta
        </button>
      </form>

      <section className="rounded-[8px] border border-white/10 bg-white/[0.04] p-5">
        <h2 className="text-sm font-semibold text-white">Profil</h2>
        <div className="mt-4 space-y-3">
          <Line label="Email" value={profile?.email ?? account.email ?? "brak"} />
          <Line label="Nazwa" value={profile?.name ?? "brak"} />
          <Line label="Telefon" value={profile?.phone ?? "brak"} />
        </div>
      </section>

      <section className="rounded-[8px] border border-white/10 bg-white/[0.04] p-5">
        <h2 className="text-sm font-semibold text-white">CRM i onboarding</h2>
        <p className="mt-3 text-sm leading-6 text-zinc-400">
          Statusy i kolumny zmieniasz w Google. Panel nie zapisuje zmian CRM.
          Połączenie Google i Telegrama przechodzi przez onboarding.
        </p>
        <Link
          href="/onboarding/google"
          className="mt-4 inline-flex rounded-full border border-[#3DFF7A]/40 px-4 py-2 text-sm font-semibold text-[#3DFF7A]"
        >
          Przejdź do onboardingu
        </Link>
      </section>
    </div>
  );
}

function Line({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4 text-sm">
      <span className="text-zinc-500">{label}</span>
      <span className="text-zinc-200">{value}</span>
    </div>
  );
}
