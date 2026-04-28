import type { Metadata } from "next";
import { PlaceholderPage } from "@/components/placeholder-page";

export const metadata: Metadata = {
  title: "Polityka prywatności | Agent-OZE",
  description: "Polityka prywatności Agent-OZE - wersja robocza.",
};

export default function PrivacyPage() {
  return (
    <PlaceholderPage
      eyebrow="Dokument roboczy"
      title="Polityka prywatności będzie gotowa przed onboardingiem."
      body="Przed startem kont opiszemy jasno, jakie dane przetwarza Agent-OZE, gdzie mieszkają dane klientów, jak działa integracja z Google oraz jak użytkownik może cofnąć dostęp i usunąć konto."
      highlights={["Dane w Google", "Dostępy OAuth", "Usunięcie konta"]}
      primaryLabel="Wróć na landing"
      primaryHref="/"
      note="To placeholder techniczny dla preview. Finalna wersja dokumentu powstanie przed uruchomieniem rejestracji."
    />
  );
}
