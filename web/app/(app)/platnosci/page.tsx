import Link from "next/link";
import { getCurrentAccount } from "@/lib/api/account";

export default async function PaymentsPage() {
  const account = await getCurrentAccount();
  const profile = account.profile;
  const active = profile?.subscription_status === "active";

  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase text-[#3DFF7A]">Płatności</p>
        <h1 className="mt-2 text-3xl font-semibold text-white">
          Stripe i subskrypcja
        </h1>
      </div>

      <section className="rounded-[8px] border border-white/10 bg-white/[0.04] p-5">
        <div className="grid gap-4 md:grid-cols-4">
          <State label="Status" value={profile?.subscription_status ?? "brak"} hot={active} />
          <State label="Plan" value={profile?.subscription_plan ?? "nie wybrano"} />
          <State label="Aktywacja" value={profile?.activation_paid ? "opłacona" : "czeka"} />
          <State
            label="Okres do"
            value={formatDate(profile?.subscription_current_period_end)}
          />
        </div>
        {!active ? (
          <Link
            href="/onboarding/platnosc"
            className="mt-6 inline-flex rounded-full bg-[#3DFF7A] px-5 py-3 text-sm font-semibold text-black"
          >
            Przejdź do płatności
          </Link>
        ) : null}
      </section>

      <section className="rounded-[8px] border border-white/10 bg-white/[0.04] p-5">
        <h2 className="text-sm font-semibold text-white">Historia płatności</h2>
        <p className="mt-3 text-sm leading-6 text-zinc-400">
          Historia pojawi się po podpięciu endpointu `payment_history`. Źródłem
          rozliczeń pozostaje Stripe, a FastAPI zapisuje zdarzenia webhooków w
          Supabase.
        </p>
      </section>
    </div>
  );
}

function State({
  label,
  value,
  hot,
}: {
  label: string;
  value: string;
  hot?: boolean;
}) {
  return (
    <div className="rounded-[8px] border border-white/10 bg-black/20 p-4">
      <p className="text-xs uppercase text-zinc-500">{label}</p>
      <p className={hot ? "mt-2 font-semibold text-[#3DFF7A]" : "mt-2 font-semibold text-white"}>
        {value}
      </p>
    </div>
  );
}

function formatDate(value: string | null | undefined) {
  if (!value) return "brak";
  return new Date(value).toLocaleDateString("pl-PL", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}
