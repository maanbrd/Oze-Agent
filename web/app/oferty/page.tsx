import { AppShell } from "@/components/app-shell";
import { OfferGenerator } from "@/components/offers/offer-generator";

export default function OffersPage() {
  return (
    <AppShell active="oferty">
      <OfferGenerator />
    </AppShell>
  );
}
