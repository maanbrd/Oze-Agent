import { redirect } from "next/navigation";
import { CrmShell } from "@/components/crm-shell";
import { getCurrentAccount } from "@/lib/api/account";
import { getDecisionsCount } from "@/lib/api/decisions";
import { getOnboardingStatus } from "@/lib/api/onboarding";
import { isOwnerAdminAccount } from "@/lib/admin/owner-admin";
import { fallbackOnboardingProgress } from "@/lib/onboarding/fallback";
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

  if (isOwnerAdminAccount(account)) {
    redirect("/admin");
  }

  const onboardingStatus = await getOnboardingStatus();
  const fallback = fallbackOnboardingProgress(account.profile);
  const completed = onboardingStatus ? onboardingStatus.completed : fallback.completed;

  if (!completed) {
    redirect(
      safeLocalPath(
        onboardingStatus?.nextStep ?? fallback.nextStep,
        "/onboarding/platnosc",
      ),
    );
  }

  const decisionsCount = await getDecisionsCount();

  return (
    <CrmShell account={account} decisionsCount={decisionsCount}>
      {children}
    </CrmShell>
  );
}
