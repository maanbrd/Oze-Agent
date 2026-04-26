import type { Metadata } from "next";
import { PlaceholderPage } from "@/components/placeholder-page";

export const metadata: Metadata = {
  title: "Logowanie | Agent-OZE",
  description: "Panel Agent-OZE jest przygotowywany.",
};

export default function LoginPage() {
  return (
    <PlaceholderPage
      eyebrow="Logowanie"
      title="Panel handlowca będzie dostępny po uruchomieniu kont."
      body="Logowanie podepniemy po konfiguracji Supabase Auth i RLS. Do tego momentu bot Telegram pozostaje aktywnym miejscem pracy, a web jest przygotowywany jako czytelny panel przy biurku."
      highlights={["Supabase Auth", "Bezpieczne sesje", "Dostęp tylko do swoich danych"]}
      primaryLabel="Wróć na landing"
      primaryHref="/"
      secondaryLabel="Załóż konto"
      secondaryHref="/rejestracja"
      note="Brak formularza jest celowy: nie zbieramy jeszcze danych logowania zanim auth i polityki RLS będą gotowe."
    />
  );
}
