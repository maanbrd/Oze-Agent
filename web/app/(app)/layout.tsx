import { redirect } from "next/navigation";
import { CrmShell } from "@/components/crm-shell";
import { getCurrentAccount } from "@/lib/api/account";
import { getOnboardingStatus } from "@/lib/api/onboarding";
import { safeLocalPath } from "@/lib/routes";

export default async function LoggedInLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const account = await getCurrentAccount();
  if (!account.authenticated) {
    redirect("/login?next=/dashboard");
  }

  const onboardingStatus = await getOnboardingStatus();
  const completed = Boolean(
    onboardingStatus?.completed || account.profile?.onboarding_completed,
  );

  if (!completed) {
    redirect(safeLocalPath(onboardingStatus?.nextStep, "/onboarding/platnosc"));
  }

  return (
    <CrmShell account={account}>
      {children}
    </CrmShell>
  );
}
