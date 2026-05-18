import { OwnerSectionPage } from "@/components/owner/owner-section-page";

export default function OwnerCustomersAccountsPage() {
  return (
    <OwnerSectionPage
      title="Klienci i konta"
      description="Przegląd użytkowników Agent-OZE, ich statusów, onboardingu i danych CRM w owner mirror Sheets."
      cards={[
        {
          title: "Aktywne konta",
          metric: "Konta",
          body: "Lista kont płatnych, pending payment, canceled oraz tych, które wymagają dopięcia onboardingu.",
        },
        {
          title: "Snapshot kontaktów",
          metric: "CRM",
          body: "Pełna baza kontaktów zostaje w arkuszu właściciela, z kolumnami identyfikującymi użytkownika.",
        },
        {
          title: "Aktywność użytkowników",
          metric: "Produkt",
          body: "Sygnały użycia Telegrama, liczba kontaktów, pierwsze oferty i postęp w lejku Agent-OZE.",
        },
      ]}
    />
  );
}
