import type { Metadata } from "next";
import { PlaceholderPage } from "@/components/placeholder-page";

export const metadata: Metadata = {
  title: "Regulamin | Agent-OZE",
  description: "Regulamin Agent-OZE - wersja robocza.",
};

export default function TermsPage() {
  return (
    <PlaceholderPage
      eyebrow="Dokument roboczy"
      title="Regulamin pojawi się przed startem rejestracji."
      body="Pełne zasady korzystania z Agent-OZE opublikujemy przed uruchomieniem płatności i onboardingu. Dokument będzie obejmował konto, subskrypcję, zakres działania bota i odpowiedzialność za dane w Google Workspace użytkownika."
      highlights={["Subskrypcja", "Konto użytkownika", "Zakres usługi"]}
      primaryLabel="Wróć na landing"
      primaryHref="/"
      note="To placeholder techniczny dla preview. Nie jest jeszcze finalnym regulaminem usługi."
    />
  );
}
