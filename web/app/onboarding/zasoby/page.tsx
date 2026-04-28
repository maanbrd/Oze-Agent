import { createGoogleResourcesAction } from "@/app/onboarding/actions";
import { getOnboardingStatus } from "@/lib/api/onboarding";

export default async function ResourcesPage() {
  const status = await getOnboardingStatus();
  const profile = status?.profile;
  const defaultName = String(
    profile?.name ?? profile?.email ?? "Agent-OZE",
  );

  return (
    <main className="min-h-screen bg-[#050607] px-5 py-8 text-zinc-100">
      <section className="mx-auto max-w-3xl">
        <p className="text-xs font-semibold uppercase text-[#3DFF7A]">Krok 4</p>
        <h1 className="mt-3 text-4xl font-semibold text-white">
          Zasoby Google.
        </h1>
        <p className="mt-4 text-sm leading-6 text-zinc-300">
          Tworzymy brakujące zasoby systemowe. Dane CRM nadal edytujesz w Sheets
          i Calendar.
        </p>
        <form action={createGoogleResourcesAction} className="mt-6 grid gap-4">
          <label className="text-sm text-zinc-300">
            Nazwa arkusza Sheets
            <input
              name="sheetsName"
              defaultValue={`Agent-OZE CRM - ${defaultName}`}
              className="mt-2 w-full rounded-[8px] border border-white/10 bg-black/30 px-4 py-3 text-white"
            />
          </label>
          <label className="text-sm text-zinc-300">
            Nazwa kalendarza
            <input
              name="calendarName"
              defaultValue={`Agent-OZE - ${defaultName}`}
              className="mt-2 w-full rounded-[8px] border border-white/10 bg-black/30 px-4 py-3 text-white"
            />
          </label>
          <button className="w-fit rounded-full bg-[#3DFF7A] px-5 py-3 text-sm font-semibold text-black">
            Utwórz brakujące zasoby
          </button>
        </form>
      </section>
    </main>
  );
}
