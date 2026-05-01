import { redirect } from "next/navigation";
import { AppShell } from "@/components/app-shell";
import { getCurrentAccount } from "@/lib/api/account";
import { getOnboardingStatus } from "@/lib/api/onboarding";

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

  return (
    <AppShell account={account} onboardingStatus={onboardingStatus}>
      {children}
    </AppShell>
  );
}
