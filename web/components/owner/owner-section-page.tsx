import type { OwnerDashboardData } from "@/lib/api/admin-dashboard";
import { OwnerPanel } from "@/components/owner/owner-dashboard";

type OwnerSectionPageProps = {
  title: string;
  description: string;
  cards: Array<{
    title: string;
    body: string;
    metric?: string;
  }>;
  data?: OwnerDashboardData;
};

export function OwnerSectionPage({
  title,
  description,
  cards,
  data,
}: OwnerSectionPageProps) {
  return (
    <OwnerPanel title={title} description={description}>
      <div className="grid gap-3 lg:grid-cols-3">
        {cards.map((card) => (
          <article key={card.title} className="rounded-[8px] border border-white/10 bg-white/[0.025] p-4">
            <p className="text-xs font-bold uppercase tracking-[0.18em] text-[#3DFF7A]">
              {card.metric ?? "Widok"}
            </p>
            <h2 className="mt-3 text-xl font-semibold text-white">{card.title}</h2>
            <p className="mt-3 text-sm leading-6 text-zinc-400">{card.body}</p>
          </article>
        ))}
      </div>

      {data?.error ? (
        <div className="rounded-[8px] border border-amber-300/25 bg-amber-300/10 px-4 py-3 text-sm text-amber-100">
          {data.error}
        </div>
      ) : null}
    </OwnerPanel>
  );
}
