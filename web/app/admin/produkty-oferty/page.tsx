import { OwnerSectionPage } from "@/components/owner/owner-section-page";

export default function OwnerProductsOffersPage() {
  return (
    <OwnerSectionPage
      title="Produkty i oferty"
      description="Wiedza o tym, jakie oferty powstają, jakie komponenty są najczęstsze i które konfiguracje warto rozwijać."
      cards={[
        {
          title: "Typy ofert",
          metric: "Mix",
          body: "PV, magazyny energii, konfiguracje łączone i udział poszczególnych produktów.",
        },
        {
          title: "Komponenty",
          metric: "Sprzęt",
          body: "Panele, inwertery, magazyny, konstrukcje, zabezpieczenia, monitoring i warunki gwarancji.",
        },
        {
          title: "Wysyłki ofert",
          metric: "Gmail",
          body: "Próby wysłania oferty, statusy, błędy i klient, do którego trafiła oferta po potwierdzeniu.",
        },
      ]}
    />
  );
}
