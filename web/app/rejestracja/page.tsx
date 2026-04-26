import type { Metadata } from "next";
import { PlaceholderPage } from "@/components/placeholder-page";

export const metadata: Metadata = {
  title: "Rejestracja | Agent-OZE",
  description: "Onboarding Agent-OZE jest przygotowywany.",
};

export default function RegistrationPage() {
  return (
    <PlaceholderPage
      eyebrow="Rejestracja"
      title="Onboarding jest już w przygotowaniu."
      body="Tutaj pojawi się krótki proces założenia konta: płatność, połączenie Google i sparowanie Telegrama. Na razie pokazujemy landing i domykamy fundament pod MVP."
      highlights={[
        "Konto indywidualne",
        "Google Sheets i Calendar",
        "Telegram jako miejsce pracy",
      ]}
      primaryLabel="Wróć na landing"
      primaryHref="/"
      secondaryLabel="Zaloguj się"
      secondaryHref="/login"
      note="Ta strona nie uruchamia jeszcze płatności ani autoryzacji. Realny onboarding wejdzie w kolejnych etapach Phase 0."
    />
  );
}
