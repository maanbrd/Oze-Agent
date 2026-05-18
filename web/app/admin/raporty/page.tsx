import { OwnerSectionPage } from "@/components/owner/owner-section-page";

export default function OwnerReportsPage() {
  return (
    <OwnerSectionPage
      title="Raporty"
      description="Miejsce na cykliczne raporty z owner mirror, eksporty i szybkie linki do arkusza oraz kalendarza właściciela."
      cards={[
        {
          title: "Raport dzienny",
          metric: "Daily",
          body: "Podsumowanie nowych kont, kosztów AI, ofert, błędów i przyszłych spotkań.",
        },
        {
          title: "Raport miesięczny",
          metric: "MRR",
          body: "Przychód, churn, aktywność kont i zmiany w popularności konfiguracji OZE.",
        },
        {
          title: "Eksport danych",
          metric: "Sheets",
          body: "Owner Google Sheets pozostaje pełnym źródłem administracyjnej kopii danych.",
        },
      ]}
    />
  );
}
