import { redirect } from "next/navigation";
import { requireCurrentAccount } from "@/lib/api/account";
import { getOnboardingStatus } from "@/lib/api/onboarding";

export const dynamic = "force-dynamic";

export default async function GoogleSuccessPage() {
  await requireCurrentAccount("/onboarding/google/sukces");
  const status = await getOnboardingStatus();
  const connected = Boolean(status?.steps.google);

  if (connected) {
    redirect("/onboarding/przekierowuje?to=next");
  }

  redirect("/onboarding/google?error=brak_zgody");
}
