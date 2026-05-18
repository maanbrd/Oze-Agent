import { OwnerSectionPage } from "@/components/owner/owner-section-page";

export default function OwnerOperationsPage() {
  return (
    <OwnerSectionPage
      title="Operacje i zdrowie"
      description="Stan integracji, tokenów Google, synchronizacji mirroru i alertów, które mogą blokować pracę użytkowników."
      cards={[
        {
          title: "Status integracji",
          metric: "Google",
          body: "Ile kont ma podpięty arkusz, kalendarz, Drive i Telegram oraz gdzie trzeba zareagować.",
        },
        {
          title: "Błędy synchronizacji",
          metric: "Sync",
          body: "Miejsce na logi owner mirror, nieudane odczyty i konta wymagające ponownego połączenia Google.",
        },
        {
          title: "Alerty krytyczne",
          metric: "Ryzyko",
          body: "Kolejka spraw, które wpływają na dostęp, płatności albo poprawność danych w panelu właściciela.",
        },
      ]}
    />
  );
}
