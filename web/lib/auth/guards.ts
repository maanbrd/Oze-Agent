import "server-only";

import { redirect } from "next/navigation";
import { getCurrentAccount } from "@/lib/api/account";
import { getOnboardingStatus } from "@/lib/api/onboarding";
import { fallbackOnboardingProgress } from "@/lib/onboarding/fallback";
import { safeLocalPath } from "@/lib/routes";

export async function requireCompletedOnboarding(currentPath: string) {
  const account = await getCurrentAccount();

  if (!account.authenticated) {
    redirect(`/login?next=${encodeURIComponent(currentPath)}`);
  }

  const status = await getOnboardingStatus();
  const fallback = fallbackOnboardingProgress(account.profile);
  const completed = status ? status.completed : fallback.completed;

  if (!completed) {
    redirect(safeLocalPath(status?.nextStep ?? fallback.nextStep, "/onboarding/platnosc"));
  }

  return { account, onboardingStatus: status };
}

export async function requireOnboardingStep(currentPath: string) {
  const account = await getCurrentAccount();

  if (!account.authenticated) {
    redirect(`/login?next=${encodeURIComponent(currentPath)}`);
  }

  const status = await getOnboardingStatus();
  const fallback = fallbackOnboardingProgress(account.profile);
  const completed = status ? status.completed : fallback.completed;

  if (completed) {
    redirect("/dashboard");
  }

  const resolvedNextStep = safeLocalPath(
    status?.nextStep ?? fallback.nextStep,
    "/onboarding/platnosc",
  );
  const canShowPaidFallbackPaymentStep =
    !status &&
    currentPath === "/onboarding/platnosc" &&
    fallback.access.active &&
    fallback.nextStep === "/onboarding/google";

  if (resolvedNextStep !== currentPath && !canShowPaidFallbackPaymentStep) {
    redirect(resolvedNextStep);
  }

  return { account, onboardingStatus: status };
}
