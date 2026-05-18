import { OwnerSectionPage } from "@/components/owner/owner-section-page";

export default function OwnerSettingsPage() {
  return (
    <OwnerSectionPage
      title="Ustawienia"
      description="Konfiguracja warstwy właściciela: admin emails, owner mirror, linki do arkusza i kalendarza oraz przyszłe role."
      cards={[
        {
          title: "OWNER_ADMIN_EMAILS",
          metric: "Dostęp",
          body: "Lista emaili, które mogą wejść do warstwy właściciela. Zwykły użytkownik nie widzi tych tras.",
        },
        {
          title: "Owner mirror",
          metric: "Dane",
          body: "Konfiguracja arkusza i kalendarza właściciela odbywa się przez env Railway/Vercel.",
        },
        {
          title: "Bezpieczeństwo",
          metric: "Admin",
          body: "Panel pokazuje agregaty, a pełna baza użytkowników żyje w kontrolowanym arkuszu administracyjnym.",
        },
      ]}
    />
  );
}
