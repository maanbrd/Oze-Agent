import { OwnerSectionPage } from "@/components/owner/owner-section-page";

export default function OwnerIntegrationsPage() {
  return (
    <OwnerSectionPage
      title="Integracje"
      description="Google Sheets, Google Calendar, Drive, Telegram, Stripe, Supabase oraz stan połączeń potrzebnych do pracy Agent-OZE."
      cards={[
        {
          title: "Google",
          metric: "Źródło CRM",
          body: "Stan arkuszy, kalendarzy, folderów Drive oraz tokenów, na których działa mirror właściciela.",
        },
        {
          title: "Telegram i AI",
          metric: "Agent",
          body: "Aktywność botów, zużycie modeli oraz konta, które jeszcze nie podłączyły Telegrama.",
        },
        {
          title: "Płatności",
          metric: "Stripe",
          body: "Status webhooków, subskrypcji i danych rozliczeniowych, które zasilają widok właściciela.",
        },
      ]}
    />
  );
}
