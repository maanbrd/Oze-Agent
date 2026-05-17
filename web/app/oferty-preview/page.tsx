import { notFound } from "next/navigation";
import { CrmShell } from "@/components/crm-shell";
import { OfferGenerator } from "@/components/offers/offer-generator";
import type { CurrentAccount } from "@/lib/api/account";

export const dynamic = "force-dynamic";

const previewAccount = {
  authenticated: true,
  email: "preview@agent-oze.pl",
  accessToken: "preview",
  error: null,
  profile: {
    id: "preview",
    auth_user_id: "preview",
    name: "Podgląd lokalny",
    email: "preview@agent-oze.pl",
    phone: "+48 000 000 000",
    subscription_status: "active",
    subscription_plan: "preview",
    subscription_current_period_end: null,
    activation_paid: true,
    onboarding_completed: true,
    google_sheets_id: null,
    google_calendar_id: null,
    google_drive_folder_id: null,
    telegram_id: null,
  },
} satisfies CurrentAccount;

export default function OffersPreviewPage() {
  if (process.env.NODE_ENV !== "development") {
    notFound();
  }

  return (
    <CrmShell account={previewAccount} decisionsCount={14}>
      <OfferGenerator />
    </CrmShell>
  );
}
