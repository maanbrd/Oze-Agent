import Link from "next/link";

import { BriefJutraModal } from "@/components/dashboard/brief-jutra-modal";
import type { CrmClient, CrmEvent } from "@/lib/crm/types";

export const TELEGRAM_BOT_URL = "https://t.me/AgentOZE_Bot";

export function QuickActionsStrip({
  tomorrowKey,
  tomorrowEvents,
  urgentClients,
  decisionsCount,
}: {
  tomorrowKey: string;
  tomorrowEvents: CrmEvent[];
  urgentClients: CrmClient[];
  decisionsCount: number;
}) {
  return (
    <section
      aria-label="Szybkie akcje"
      className="grid gap-3 md:grid-cols-3"
    >
      <a
        href={TELEGRAM_BOT_URL}
        target="_blank"
        rel="noopener noreferrer"
        className="group flex h-full flex-col items-start gap-2 rounded-[8px] border border-white/10 bg-white/[0.04] p-4 transition hover:border-[#3DFF7A]/40 hover:bg-white/[0.06]"
      >
        <span className="text-2xl" aria-hidden="true">✈️</span>
        <span className="font-semibold text-white">Otwórz @AgentOZE_Bot</span>
        <span className="text-xs text-zinc-400">
          Telegram w nowej karcie. Dyktuj klienta, notatkę, status.
        </span>
      </a>

      <Link
        href="/oferty"
        className="group flex h-full flex-col items-start gap-2 rounded-[8px] border border-white/10 bg-white/[0.04] p-4 transition hover:border-[#3DFF7A]/40 hover:bg-white/[0.06]"
      >
        <span className="text-2xl" aria-hidden="true">📄</span>
        <span className="font-semibold text-white">Wygeneruj ofertę</span>
        <span className="text-xs text-zinc-400">
          Szablon, profil sprzedawcy, PDF. Wysyłka po Twoim potwierdzeniu.
        </span>
      </Link>

      <BriefJutraModal
        tomorrowKey={tomorrowKey}
        tomorrowEvents={tomorrowEvents}
        urgentClients={urgentClients}
        decisionsCount={decisionsCount}
      />
    </section>
  );
}
