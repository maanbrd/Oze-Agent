import { OwnerSectionPage } from "@/components/owner/owner-section-page";

export default function OwnerBillingPage() {
  return (
    <OwnerSectionPage
      title="Płatności i subskrypcje"
      description="MRR, konta aktywne, pending payment, churn i historia rozliczeń z Supabase/Stripe."
      cards={[
        {
          title: "MRR i aktywne konta",
          metric: "Przychód",
          body: "Podstawowy widok przychodu miesięcznego oraz liczby aktywnie płacących kont.",
        },
        {
          title: "Pending payment",
          metric: "Odzysk",
          body: "Konta, które rozpoczęły płatność albo mają problem z opłaceniem subskrypcji.",
        },
        {
          title: "Churn i canceled",
          metric: "Retencja",
          body: "Konta anulowane zostają w snapshotach, ale nie są dalej odświeżane w kalendarzu mirror.",
        },
      ]}
    />
  );
}
