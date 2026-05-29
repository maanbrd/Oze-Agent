import { RedirectingScreen } from "@/components/ui/redirecting-screen";

export default async function PrzekierowujePage({
  searchParams,
}: {
  searchParams: Promise<{ to?: string; url?: string }>;
}) {
  const { to, url } = await searchParams;

  if (to === "google" && url) {
    return (
      <RedirectingScreen
        steps={[
          { label: "Konto", status: "done" },
          { label: "Google", status: "active" },
          { label: "Uprawnienia", status: "pending" },
        ]}
        statusLabel="Łączę z Google"
        subLabel="Za chwilę poprosimy o zgody na Sheets, Kalendarz i Drive."
        nextUrl={url}
      />
    );
  }

  if (to === "stripe") {
    return (
      <RedirectingScreen
        steps={[
          { label: "Konto", status: "done" },
          { label: "Stripe", status: "active" },
          { label: "Płatność", status: "pending" },
        ]}
        statusLabel="Otwieram Stripe"
        subLabel="Za chwilę przeniesiemy Cię do bezpiecznej płatności."
        nextUrl="/onboarding/checkout"
      />
    );
  }

  if (to === "next") {
    return (
      <RedirectingScreen
        steps={[
          { label: "Google", status: "done" },
          { label: "Sprawdzam", status: "active" },
          { label: "Zasoby", status: "pending" },
        ]}
        statusLabel="Sprawdzam zgody"
        subLabel="Za chwilę utworzymy Twoje zasoby Google."
        nextUrl="/onboarding/zasoby"
      />
    );
  }

  return (
    <RedirectingScreen
      steps={[
        { label: "Konto", status: "active" },
        { label: "Następny krok", status: "pending" },
      ]}
      statusLabel="Przekierowuję"
      subLabel="Za chwilę otworzymy następny krok."
      nextUrl="/onboarding/platnosc"
    />
  );
}
