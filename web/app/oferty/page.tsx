import { AppShell } from "@/components/app-shell";
import { OfferGenerator } from "@/components/offers/offer-generator";
import { requireCompletedOnboarding } from "@/lib/auth/guards";

export const dynamic = "force-dynamic";

export default async function OffersPage() {
  await requireCompletedOnboarding("/oferty");

  return (
    <AppShell active="oferty">
      <OfferGenerator />
    </AppShell>
  );
}
