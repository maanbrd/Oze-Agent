import type { Metadata } from "next";
import { DecyzjePreview } from "@/components/dashboard/decyzje-preview";
import { getPendingDecisions } from "@/lib/api/decisions";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Wymagają decyzji | Agent OZE",
  description:
    "Klienci wymagający uwagi — podgląd w dashboardzie, potwierdzenie decyzji w Telegramie.",
};

export default async function DecyzjePreviewPage() {
  const data = await getPendingDecisions();
  return (
    <DecyzjePreview
      key={data.fetchedAt}
      initialClients={data.clients}
      fetchedAt={data.fetchedAt}
      sourceState={data.source}
    />
  );
}
