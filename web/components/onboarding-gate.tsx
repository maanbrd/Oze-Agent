import Link from "next/link";
import type { OnboardingStatus } from "@/lib/api/onboarding";

export function OnboardingGate({ status }: { status: OnboardingStatus | null }) {
  if (!status || status.completed) return null;

  return (
    <section className="mb-5 rounded-[8px] border border-[#3DFF7A]/25 bg-[#3DFF7A]/10 px-4 py-3 text-sm text-zinc-200">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <p>Dokończ onboarding, żeby panel czytał live dane z Google Sheets i Calendar.</p>
        <Link
          href={status.nextStep}
          className="w-fit rounded-full bg-[#3DFF7A] px-4 py-2 text-xs font-semibold text-black"
        >
          Kontynuuj
        </Link>
      </div>
    </section>
  );
}
