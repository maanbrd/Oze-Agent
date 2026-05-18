import { OwnerSectionPage } from "@/components/owner/owner-section-page";

export default function OwnerAnalyticsPage() {
  return (
    <OwnerSectionPage
      title="Analityka danych OZE"
      description="Rynek, komponenty, miasta, ceny i konfiguracje ofert z administracyjnej kopii danych."
      cards={[
        {
          title: "Konfiguracje ofert",
          metric: "Oferty",
          body: "Analiza tego, jakie typy ofert i komponenty najczęściej pojawiają się u użytkowników Agent-OZE.",
        },
        {
          title: "Miasta i regiony",
          metric: "Rynek",
          body: "Widok miejscowości, z których wpadają kontakty oraz gdzie powstaje najwięcej ofert.",
        },
        {
          title: "Ceny i moc",
          metric: "OZE",
          body: "Średnie ceny, moc PV, magazyny energii i zmiana miksu produktowego w czasie.",
        },
      ]}
    />
  );
}
