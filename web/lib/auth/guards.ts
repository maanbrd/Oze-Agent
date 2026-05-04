import "server-only";

import { redirect } from "next/navigation";
import { getCurrentAccount } from "@/lib/api/account";
import { getOnboardingStatus } from "@/lib/api/onboarding";
import { safeLocalPath } from "@/lib/routes";

export async function requireCompletedOnboarding(currentPath: string) {
  const account = await getCurrentAccount();

  if (!account.authenticated) {
    redirect(`/login?next=${encodeURIComponent(currentPath)}`);
  }

  const status = await getOnboardingStatus();
  const completed = Boolean(
    status?.completed || account.profile?.onboarding_completed,
  );

  if (!completed) {
    redirect(safeLocalPath(status?.nextStep, "/onboarding/platnosc"));
  }

  return { account, onboardingStatus: status };
}

export async function requireOnboardingStep(currentPath: string) {
  const account = await getCurrentAccount();

  if (!account.authenticated) {
    redirect(`/login?next=${encodeURIComponent(currentPath)}`);
  }

  const status = await getOnboardingStatus();
  const completed = Boolean(
    status?.completed || account.profile?.onboarding_completed,
  );

  if (completed) {
    redirect("/dashboard");
  }

  const resolvedNextStep = safeLocalPath(
    status?.nextStep,
    "/onboarding/platnosc",
  );

  if (resolvedNextStep !== currentPath) {
    redirect(resolvedNextStep);
  }

  return { account, onboardingStatus: status };
}
