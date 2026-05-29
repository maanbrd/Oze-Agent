import { RedirectingScreen } from "@/components/ui/redirecting-screen";

type StepStatus = "done" | "active" | "pending";

type RouteConfig = {
  steps: { label: string; status: StepStatus }[];
  statusLabel: string;
  subLabel: string;
  nextUrl: string;
};

const ROUTES: Record<string, RouteConfig> = {
  stripe: {
    steps: [
      { label: "Konto", status: "done" },
      { label: "Stripe", status: "active" },
      { label: "Płatność", status: "pending" },
    ],
    statusLabel: "Otwieram Stripe",
    subLabel: "Za chwilę przeniesiemy Cię do bezpiecznej płatności.",
    nextUrl: "/onboarding/checkout",
  },
  google: {
    steps: [
      { label: "Konto", status: "done" },
      { label: "Google", status: "active" },
      { label: "Uprawnienia", status: "pending" },
    ],
    statusLabel: "Łączę z Google",
    subLabel: "Za chwilę poprosimy o zgody na Sheets, Kalendarz i Drive.",
    nextUrl: "/onboarding/google/oauth-start",
  },
  next: {
    steps: [
      { label: "Google", status: "done" },
      { label: "Sprawdzam", status: "active" },
      { label: "Zasoby", status: "pending" },
    ],
    statusLabel: "Sprawdzam zgody",
    subLabel: "Za chwilę utworzymy Twoje zasoby Google.",
    nextUrl: "/onboarding/zasoby",
  },
};

export default async function PrzekierowujePage({
  searchParams,
}: {
  searchParams: Promise<{ to?: string }>;
}) {
  const { to } = await searchParams;
  const cfg = (to && ROUTES[to]) || ROUTES.stripe;
  return <RedirectingScreen {...cfg} />;
}
